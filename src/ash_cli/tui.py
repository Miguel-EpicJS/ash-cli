import queue
import select
import sys
import termios
import threading
import tty

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .agent import create_agent
from .buffer import ScrollBuffer
from .config import Config


def get_user_input(console: Console, is_tty: bool) -> str:
    old_settings = None
    if is_tty:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        console.print("[green]>[/green] ", end="")
        sys.stdout.flush()
        if is_tty:
            user_input = ""
            while True:
                ch = sys.stdin.read(1)
                if ch == "\n" or ch == "\r":
                    console.print()
                    break
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
            return user_input.strip()
        else:
            return input().strip()
    except EOFError:
        return ""
    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def run(config: Config) -> None:
    console = Console()
    tui_config = config.tui

    is_tty = sys.stdin.isatty()
    prompt = get_user_input(console, is_tty)

    console.print(
        Panel(
            Text(f"Prompt: {prompt}"),
            title=tui_config.input_panel_title,
            border_style="green",
            box=box.ROUNDED,
        )
    )

    old_settings = None
    if is_tty:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        thinking_buffer = ScrollBuffer()
        content_buffer = ScrollBuffer()
        thinking_queue: queue.Queue[str] = queue.Queue()
        should_quit = [False]
        response: list[str] = [""]

        agent = create_agent(config.model, config.agent)

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
            if is_tty:
                console.print("[dim]j/k scroll, q quit[/dim]")

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
                    elif key == "j":
                        thinking_buffer.scroll_down()
                        content_buffer.scroll_down()
                    elif key == "k":
                        thinking_buffer.scroll_up()
                        content_buffer.scroll_up()
                    elif key == "\x1b":
                        if sys.stdin.read(1) == "[":
                            arrow = sys.stdin.read(1)
                            if arrow == "A":
                                thinking_buffer.scroll_up()
                                content_buffer.scroll_up()
                            elif arrow == "B":
                                thinking_buffer.scroll_down()
                                content_buffer.scroll_down()

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

    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
