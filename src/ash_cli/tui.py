import os
import queue
import select
import subprocess
import sys
import termios
import threading
import tty

import pyperclip

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .agent import create_agent
from .buffer import ScrollBuffer
from .config import Config


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


def run(config: Config) -> None:
    console = Console()
    tui_config = config.tui
    session_id = os.urandom(16).hex()

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
                    console.print("[dim]Commands: /quit, /q - exit | /help - show this[/dim]")
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

            agent = create_agent(config.model, config.agent, session_id=session_id)

            def stream_agent() -> None:
                try:
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
                except Exception as e:
                    thinking_queue.put(f"Error: {e}")

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

            console.print(f"[green]Command:[/green] {response[0].strip() or '(none)'}")

            if response[0].strip():
                console.print("[dim][E]xecute / [C]opy / [S]kip:[/dim] ", end="")
                sys.stdout.flush()
                if is_tty:
                    key = sys.stdin.read(1)
                    key = key.lower()
                    if key == "e" or key == "\r":
                        proc = subprocess.Popen(
                            response[0].strip(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                        )
                        stdout, stderr = proc.communicate()
                        if stdout:
                            console.print(f"[cyan]{stdout.decode()}[/cyan]")
                        if stderr:
                            console.print(f"[red]{stderr.decode()}[/red]")
                    elif key == "c":
                        try:
                            pyperclip.copy(response[0].strip())
                            console.print("[green]Copied![/green]")
                        except Exception as e:
                            console.print(f"[red]Copy failed: {e}[/red]")
                else:
                    console.print()

    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
