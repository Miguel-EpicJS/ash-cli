import os
import queue
import re
import select
import shlex
import subprocess
import sys
import termios
import threading
import time as time_module
import tty
from pathlib import Path

import pyperclip
from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .agent import create_agent
from .buffer import ScrollBuffer
from .config import Config, get_available_models, resolve_model
from .error import ConnectionError, RetryConfig, TimeoutError
from .logging import init_logging
from .session import (
    Message,
    Session,
    Usage,
    export_session,
    get_command_history,
    get_total_usage,
    import_session,
    list_sessions,
    load_session,
    rename_session,
    save_session,
)
from .session import (
    create_session as create_sess,
)

THEMES = {
    "dark": {
        "thinking_border": "blue",
        "response_border": "cyan",
        "input_prompt": "[green]>[/green]",
        "input_continue": "... ",
        "panel_bg": "",
    },
    "light": {
        "thinking_border": "blue",
        "response_border": "cyan",
        "input_prompt": "[green]>[/green]",
        "input_continue": "... ",
        "panel_bg": "",
    },
}


def _get_theme(config: Config) -> dict[str, str]:
    theme_name = config.tui.theme
    if theme_name == "system":
        if os.environ.get("NO_COLOR"):
            theme_name = "dark"
        elif hasattr(os, "isatty") and sys.stdout.isatty():
            term = os.environ.get("TERM", "")
            if "light" in term:
                theme_name = "light"
    return THEMES.get(theme_name, THEMES["dark"])


def _get_keypress(is_tty: bool) -> str | None:
    if not is_tty:
        return None
    if select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


def _get_escape_sequence(is_tty: bool) -> str | None:
    if not is_tty:
        return None
    if not select.select([sys.stdin], [], [], 0)[0]:
        return None
    first = sys.stdin.read(1)
    if first != "\x1b":
        return first
    if select.select([sys.stdin], [], [], 0.1)[0]:
        second = sys.stdin.read(1)
        if second == "[":
            if select.select([sys.stdin], [], [], 0.1)[0]:
                third = sys.stdin.read(1)
                if third.isdigit():
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        fourth = sys.stdin.read(1)
                        if fourth == "~":
                            return f"escape_{third}"
                    return f"escape_{third}"
                return f"escape_{third}"
    return "escape"


def _get_completion(history: list[str], current: str) -> str | None:
    if not current or not history:
        return None
    current_lower = current.lower()
    for cmd in history:
        if cmd.lower().startswith(current_lower) and cmd != current:
            return cmd
    return None


def _search_history(history: list[str], query: str) -> list[str]:
    if not query:
        return history
    query_lower = query.lower()
    return [cmd for cmd in history if query_lower in cmd.lower()]


def get_user_input(
    console: Console,
    is_tty: bool,
    is_multi: bool = False,
    history: list[str] | None = None,
) -> str:
    old_settings = None
    if is_tty:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        if is_tty:
            user_input = ""
            line_num = 0
            search_mode = False
            search_query = ""
            search_results: list[str] = []
            search_cursor = 0

            while True:
                prompt_text = (
                    "/: "
                    if search_mode
                    else ("[green]>[/green] " if line_num == 0 else "... ")
                )
                console.print(prompt_text + user_input, end="")
                if search_mode:
                    console.print(f" (search: {search_query})", end="")
                sys.stdout.flush()

                while True:
                    key = _get_escape_sequence(is_tty)
                    if key is None:
                        key = _get_keypress(is_tty)

                    if key is None:
                        continue

                    if key == "escape" or key == "escape":
                        if search_mode:
                            search_mode = False
                            search_query = ""
                            search_results = []
                            user_input = ""
                            search_cursor = 0
                        break
                    elif key == "escape[A":
                        if search_mode and search_results:
                            search_cursor = max(0, search_cursor - 1)
                            user_input = search_results[search_cursor]
                        break
                    elif key == "escape[B":
                        if search_mode and search_results:
                            search_cursor = min(
                                len(search_results) - 1, search_cursor + 1
                            )
                            user_input = search_results[search_cursor]
                        break
                    elif key == "\t":
                        if history:
                            completion = _get_completion(history, user_input)
                            if completion:
                                user_input = completion
                                user_input += " "
                        break
                    elif key == "\n" or key == "\r":
                        console.print()
                        if is_multi and user_input.rstrip().endswith("\\"):
                            user_input = user_input[:-1] + "\n"
                            line_num += 1
                            break
                        if (
                            history
                            and user_input.strip()
                            and not user_input.startswith("/")
                        ):
                            history.insert(0, user_input.strip())
                        return user_input.strip()
                    elif key == "\x7f" or ord(key) == 127:
                        if user_input:
                            user_input = user_input[:-1]
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                            if search_mode:
                                search_results = _search_history(
                                    history or [], search_query
                                )
                                search_cursor = 0
                    elif key == "/":
                        if not search_mode and line_num == 0 and not user_input:
                            search_mode = True
                            search_query = ""
                            search_results = history or []
                            search_cursor = 0
                        else:
                            user_input += key
                            sys.stdout.write(key)
                            sys.stdout.flush()
                    elif ord(key) < 32:
                        pass
                    else:
                        user_input += key
                        sys.stdout.write(key)
                        sys.stdout.flush()
                        if search_mode:
                            search_query = user_input
                            search_results = _search_history(
                                history or [], search_query
                            )
                            search_cursor = 0

                if not is_multi:
                    break
            return user_input.strip()
        else:
            console.print("[green]>[/green] ", end="")
            return input().strip()
    except EOFError:
        return ""
    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def _run_fallback(prompt: str) -> str:
    cmd_match = re.search(r"`?(.+?)`?", prompt)
    if cmd_match:
        return cmd_match.group(1).strip()
    words = prompt.strip().split()
    if words and words[0].lower() in ("ls", "cd", "pwd", "cat", "echo", "grep", "find"):
        return words[0] + " " + " ".join(words[1:])
    return "echo 'API unavailable - please try again later'"


def _clean_command(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:[a-zA-Z]*\n)?(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    if text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text


def run(config: Config, session: Session | None = None) -> None:
    console = Console()
    logger = init_logging(config.logging)
    tui_config = config.tui
    use_color = tui_config.color
    theme = _get_theme(config)
    history = get_command_history()

    if session:
        current_session = session
    else:
        current_session = create_sess(
            name="default",
            model=config.model.id,
            temperature=config.model.temperature,
            max_tokens=config.model.max_tokens,
            base_url=config.model.base_url,
        )
    session_id = current_session.id

    old_settings = None
    is_tty = sys.stdin.isatty()

    if is_tty:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            prompt = get_user_input(console, is_tty, history=history)
            if not prompt:
                break
            if prompt.startswith("/"):
                cmd = prompt.split()[0].lower()
                if cmd in ("/quit", "/q", "/exit"):
                    break
                elif cmd == "/help":
                    console.print(
                        "[dim]Commands: /quit, /q - exit | /help - show this | "
                        "/theme dark|light|system - change theme | /models - list models | "
                        "/model <id> - switch model | /metrics - show session usage | "
                        "/stats - show total usage across all sessions[/dim]"
                    )
                    continue
                elif cmd == "/models":
                    models = get_available_models(config)
                    for model_id, preset in models.items():
                        base_url = preset.get("base_url", "N/A")
                        marker = "[*]" if model_id == config.model.id else "[ ]"
                        console.print(f"{marker} {model_id} | {base_url}")
                    continue
                elif cmd == "/model":
                    parts = prompt.split()
                    if len(parts) < 2:
                        console.print("[dim]Usage: /model <model_id>[/dim]")
                    else:
                        new_model_id = parts[1]
                        new_model = resolve_model(new_model_id, config)
                        if new_model:
                            config.model = new_model
                            console.print(
                                f"[green]Switched to model: {new_model_id}[/green]"
                            )
                        else:
                            console.print(f"[red]Unknown model: {new_model_id}[/red]")
                    continue
                elif cmd == "/theme":
                    parts = prompt.split()
                    if len(parts) < 2:
                        console.print(f"[dim]Current theme: {tui_config.theme}[/dim]")
                        console.print("[dim]Usage: /theme dark|light|system[/dim]")
                    elif parts[1] in ("dark", "light", "system"):
                        tui_config.theme = parts[1]
                        console.print(f"[green]Theme set to: {parts[1]}[/green]")
                    else:
                        console.print("[red]Invalid theme. Use dark/light/system[/red]")
                    continue
                elif cmd == "/metrics":
                    u = current_session.usage
                    console.print(
                        f"[dim]Session Usage: Prompt: {u.prompt_tokens} | "
                        f"Completion: {u.completion_tokens} | Total: {u.total_tokens} | "
                        f"Latency: {u.total_latency:.2f}s | API Calls: {u.api_call_count}[/dim]"
                    )
                    continue
                elif cmd == "/stats":
                    u = get_total_usage()
                    console.print(
                        f"[dim]Total Aggregate Usage: Prompt: {u.prompt_tokens} | "
                        f"Completion: {u.completion_tokens} | Total: {u.total_tokens} | "
                        f"Latency: {u.total_latency:.2f}s | API Calls: {u.api_call_count}[/dim]"
                    )
                    continue
                elif cmd == "/sessions":
                    sessions = list_sessions()
                    if not sessions:
                        console.print("[dim]No sessions found.[/dim]")
                    else:
                        for s in sessions:
                            console.print(f"{s.id} | {s.name} | {s.created_at[:10]}")
                    continue
                elif cmd == "/load":
                    parts = prompt.split()
                    if len(parts) < 2:
                        console.print("[dim]Usage: /load <session_id>[/dim]")
                    else:
                        loaded = load_session(parts[1])
                        if loaded:
                            current_session = loaded
                            session_id = current_session.id
                            console.print(
                                f"[green]Loaded session: {current_session.name}[/green]"
                            )
                        else:
                            console.print(f"[red]Session not found: {parts[1]}[/red]")
                    continue
                elif cmd == "/export":
                    parts = prompt.split()
                    if len(parts) < 2:
                        console.print("[dim]Usage: /export <session_id> [/dim]")
                    else:
                        sess_id = parts[1]
                        file_path = (
                            Path(parts[2])
                            if len(parts) > 2
                            else Path.home() / f"{sess_id}.json"
                        )
                        if export_session(sess_id, file_path):
                            console.print(f"[green]Exported to {file_path}[/green]")
                        else:
                            console.print(f"[red]Session not found: {sess_id}[/red]")
                    continue
                elif cmd == "/import":
                    parts = prompt.split()
                    if len(parts) < 2:
                        console.print("[dim]Usage: /import [/dim]")
                    else:
                        imported = import_session(Path(parts[1]))
                        if imported:
                            current_session = imported
                            session_id = current_session.id
                            console.print(
                                f"[green]Imported: {current_session.name}[/green]"
                            )
                        else:
                            console.print(f"[red]Import failed: {parts[1]}[/red]")
                    continue
                elif cmd == "/rename":
                    parts = prompt.split()
                    if len(parts) < 3:
                        console.print(
                            "[dim]Usage: /rename <session_id> <new_name>[/dim]"
                        )
                    else:
                        sess_id = parts[1]
                        new_name = " ".join(parts[2:])
                        renamed = rename_session(sess_id, new_name)
                        if renamed:
                            if current_session.id == sess_id:
                                current_session = renamed
                            console.print(f"[green]Renamed to: {new_name}[/green]")
                        else:
                            console.print(f"[red]Session not found: {sess_id}[/red]")
                    continue

            console.print(
                Panel(
                    Text(f"Prompt: {prompt}"),
                    title=tui_config.input_panel_title,
                    border_style="green",
                    box=box.ROUNDED,
                )
            )

            thinking_buffer = ScrollBuffer(height=tui_config.thinking_panel_height)
            content_buffer = ScrollBuffer(height=tui_config.panel_height)
            thinking_queue: queue.Queue[str] = queue.Queue()
            should_quit = [False]
            response: list[str] = [""]
            use_fallback = [False]

            retry_config = RetryConfig(max_retries=3, base_delay=1.0)
            logger.debug(f"User Prompt: {prompt}")

            def stream_agent() -> None:
                retry_count = 0
                start_time = time_module.time()

                while retry_count < retry_config.max_retries:
                    try:
                        agent = create_agent(
                            config.model, config.agent, session_id=session_id
                        )
                        for chunk in agent.run(prompt, stream=True):
                            if should_quit[0]:
                                break
                            reasoning = getattr(chunk, "reasoning_content", None)
                            if reasoning:
                                thinking_queue.put(reasoning)
                            content = getattr(chunk, "content", None)
                            if content:
                                response[0] += content
                                content_buffer.add(content)
                            usage = getattr(chunk, "response_usage", None)
                            if usage:
                                current_session.usage.add(
                                    Usage(
                                        prompt_tokens=getattr(
                                            usage, "prompt_tokens", 0
                                        ),
                                        completion_tokens=getattr(
                                            usage, "completion_tokens", 0
                                        ),
                                        total_tokens=getattr(usage, "total_tokens", 0),
                                    )
                                )
                        break
                    except (ConnectionError, TimeoutError) as e:
                        retry_count += 1
                        if retry_count < retry_config.max_retries:
                            delay = retry_config.base_delay * (2 ** (retry_count - 1))
                            thinking_queue.put(
                                f"Retry {retry_count}/{retry_config.max_retries} after {delay}s..."
                            )
                            time_module.sleep(delay)
                        else:
                            use_fallback[0] = True
                            thinking_queue.put(f"Fallback mode: {e}")
                    except Exception as e:
                        thinking_queue.put(f"Error: {e}")
                        break

                latency = time_module.time() - start_time
                current_session.usage.total_latency += latency
                current_session.usage.api_call_count += 1

            with Live(
                Group(
                    Panel(
                        Text("..."),
                        title=tui_config.thinking_panel_title,
                        border_style=theme["thinking_border"],
                    ),
                    Panel(
                        Text(""),
                        title=tui_config.response_panel_title,
                        border_style=theme["response_border"],
                    ),
                ),
                console=console,
                refresh_per_second=tui_config.refresh_rate,
                transient=False,
            ) as live:
                stream_thread = threading.Thread(target=stream_agent, daemon=True)
                stream_thread.start()

                scroll_offset = [0]
                page_size = 10

                while stream_thread.is_alive():
                    while True:
                        try:
                            item = thinking_queue.get_nowait()
                            thinking_buffer.add(item)
                        except queue.Empty:
                            break

                    live.update(
                        Group(
                            Panel(
                                Text(thinking_buffer.show()),
                                title=tui_config.thinking_panel_title,
                                border_style=theme["thinking_border"],
                            ),
                            Panel(
                                Text(content_buffer.show()),
                                title=tui_config.response_panel_title,
                                border_style=theme["response_border"],
                            ),
                        )
                    )

                    if is_tty and select.select([sys.stdin], [], [], 0)[0]:
                        key = _get_escape_sequence(is_tty)
                        if key is None:
                            key = _get_keypress(is_tty)
                        if key is None:
                            continue

                        if key == "q" or key == "escape":
                            should_quit[0] = True
                            break
                        elif key == "j":
                            scroll_offset[0] += 1
                            content_buffer.scroll_down()
                        elif key == "k":
                            scroll_offset[0] = max(0, scroll_offset[0] - 1)
                            content_buffer.scroll_up()
                        elif key == "escape[5":
                            for _ in range(page_size):
                                content_buffer.scroll_down()
                        elif key == "escape[6":
                            for _ in range(page_size):
                                content_buffer.scroll_up()
                        elif key == "escape[A":
                            scroll_offset[0] = max(0, scroll_offset[0] - 1)
                            content_buffer.scroll_up()
                        elif key == "escape[B":
                            scroll_offset[0] += 1
                            content_buffer.scroll_down()

                        live.update(
                            Group(
                                Panel(
                                    Text(thinking_buffer.show()),
                                    title=tui_config.thinking_panel_title,
                                    border_style=theme["thinking_border"],
                                ),
                                Panel(
                                    Text(content_buffer.show()),
                                    title=tui_config.response_panel_title,
                                    border_style=theme["response_border"],
                                ),
                            )
                        )

                if use_fallback[0] and not response[0].strip():
                    response[0] = _run_fallback(prompt)

                response[0] = _clean_command(response[0])

            console.print(f"[green]Command:[/green] {response[0] or '(none)'}")

            if response[0].strip():
                logger.debug(f"Agent Response: {response[0].strip()}")
                console.print("[dim][E]xecute / [C]opy / [S]kip:[/dim] ", end="")
                sys.stdout.flush()
                if is_tty:
                    key = sys.stdin.read(1)
                    key = key.lower()
                    if key == "e" or key == "\r":
                        cmd = (
                            response[0].strip().split()[0]
                            if response[0].strip()
                            else ""
                        )
                        if cmd:
                            check = subprocess.run(
                                f"command -v {shlex.quote(cmd)}",
                                shell=True,
                                capture_output=True,
                            )
                            if check.returncode != 0:
                                err_msg = f"Error: '{cmd}' not found"
                                console.print(
                                    f"[red]{err_msg}[/red]" if use_color else err_msg
                                )
                            else:
                                proc = subprocess.Popen(
                                    response[0].strip(),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True,
                                )
                                stdout, stderr = proc.communicate()
                                returncode = proc.returncode
                                if stdout:
                                    out_text = stdout.decode()
                                    color = "[green]" if returncode == 0 else "[red]"
                                    out_str = (
                                        f"{color}{out_text}[/{color[1:-1]}]"
                                        if use_color
                                        else out_text
                                    )
                                    console.print(out_str)
                                if stderr:
                                    err_text = stderr.decode()
                                    console.print(f"[red]{err_text}[/red]")
                    elif key == "c":
                        try:
                            pyperclip.copy(response[0].strip())
                            console.print("[green]Copied![/green]")
                        except Exception as e:
                            console.print(f"[red]Copy failed: {e}[/red]")
                else:
                    console.print()

            if response[0].strip():
                current_session.messages.append(Message(role="user", content=prompt))
                current_session.messages.append(
                    Message(role="assistant", content=response[0].strip())
                )
                save_session(current_session)

    finally:
        save_session(current_session)
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
