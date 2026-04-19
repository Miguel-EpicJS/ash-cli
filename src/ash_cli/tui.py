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
from .config import Config
from .error import ConnectionError, RetryConfig, TimeoutError
from .session import (
    Message,
    Session,
    export_session,
    import_session,
    list_sessions,
    load_session,
    rename_session,
    save_session,
)
from .session import (
    create_session as create_sess,
)


def get_user_input(console: Console, is_tty: bool, is_multi: bool = False) -> str:
    old_settings = None
    if is_tty:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        if is_tty:
            user_input = ""
            line_num = 0
            while True:
                line_start = line_num == 0
                console.print("[green]>[/green] " if line_start else "... ", end="")
                sys.stdout.flush()
                while True:
                    ch = sys.stdin.read(1)
                    if ch == "\n" or ch == "\r":
                        console.print()
                        if is_multi and user_input.rstrip().endswith("\\"):
                            user_input = user_input[:-1] + "\n"
                            line_num += 1
                            break
                        return user_input.strip()
                    elif ch == "\x7f" or ord(ch) == 127:
                        if user_input:
                            user_input = user_input[:-1]
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                    elif ord(ch) < 32:
                        pass
                    else:
                        user_input += ch
                        sys.stdout.write(ch)
                        sys.stdout.flush()
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


def run(config: Config, session: Session | None = None) -> None:
    console = Console()
    tui_config = config.tui
    use_color = tui_config.color

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
            prompt = get_user_input(console, is_tty)
            if not prompt:
                break
            if prompt.startswith("/"):
                cmd = prompt.split()[0].lower()
                if cmd in ("/quit", "/q", "/exit"):
                    break
                elif cmd == "/help":
                    console.print(
                        "[dim]Commands: /quit, /q - exit | /help - show this[/dim]"
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

            thinking_buffer = ScrollBuffer()
            content_buffer = ScrollBuffer()
            thinking_queue: queue.Queue[str] = queue.Queue()
            should_quit = [False]
            response: list[str] = [""]
            use_fallback = [False]

            retry_config = RetryConfig(max_retries=3, base_delay=1.0)

            def stream_agent() -> None:
                retry_count = 0

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

            with Live(
                Group(
                    Panel(
                        Text("..."),
                        title=tui_config.thinking_panel_title,
                        border_style="blue",
                    ),
                    Panel(
                        Text(""),
                        title=tui_config.response_panel_title,
                        border_style="cyan",
                    ),
                ),
                console=console,
                refresh_per_second=tui_config.refresh_rate,
                transient=False,
            ) as live:
                stream_thread = threading.Thread(target=stream_agent, daemon=True)
                stream_thread.start()

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
                                border_style="blue",
                            ),
                            Panel(
                                Text(content_buffer.show()),
                                title=tui_config.response_panel_title,
                                border_style="cyan",
                            ),
                        )
                    )

                    if is_tty and select.select([sys.stdin], [], [], 0)[0]:
                        key = sys.stdin.read(1)
                        if key == "q":
                            should_quit[0] = True
                            break

                        live.update(
                            Group(
                                Panel(
                                    Text(thinking_buffer.show()),
                                    title=tui_config.thinking_panel_title,
                                    border_style="blue",
                                ),
                                Panel(
                                    Text(content_buffer.show()),
                                    title=tui_config.response_panel_title,
                                    border_style="cyan",
                                ),
                            )
                        )

                if use_fallback[0] and not response[0].strip():
                    response[0] = _run_fallback(prompt)

            console.print(f"[green]Command:[/green] {response[0].strip() or '(none)'}")

            if response[0].strip():
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
