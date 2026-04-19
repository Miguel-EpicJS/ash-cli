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


def run(config: Config) -> None:
    console = Console()
    tui_config = config.tui
    prompt = config.default_prompt

    console.print(
        Panel(
            Text(f"Prompt: {prompt}"),
            title=tui_config.input_panel_title,
            border_style="green",
            box=box.ROUNDED,
        )
    )

    is_tty = sys.stdin.isatty()
    old_settings = None

    if is_tty:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    try:
        thinking_buffer = ScrollBuffer(height=tui_config.thinking_panel_height)
        content_buffer = ScrollBuffer(height=tui_config.panel_height)
        thinking_queue: queue.Queue[str] = queue.Queue()
        should_quit = [False]
        response: list[str | None] = [None]

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
                        response[0] = content
                        content_buffer.add(content)
            except Exception as e:
                thinking_queue.put(f"Error: {e}")

        with Live(
            Group(
                Panel(
                    Text("..."),
                    title=tui_config.thinking_panel_title,
                    border_style="blue",
                    height=tui_config.thinking_panel_height,
                ),
                Panel(
                    Text(""),
                    title=tui_config.response_panel_title,
                    border_style="cyan",
                    height=tui_config.panel_height,
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
                            height=tui_config.thinking_panel_height,
                        ),
                        Panel(
                            Text(content_buffer.show()),
                            title=tui_config.response_panel_title,
                            border_style="cyan",
                            height=tui_config.panel_height,
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
                                height=tui_config.thinking_panel_height,
                            ),
                            Panel(
                                Text(content_buffer.show()),
                                title=tui_config.response_panel_title,
                                border_style="cyan",
                                height=tui_config.panel_height,
                            ),
                        )
                    )

        console.print(
            Panel(
                Text(response[0] or "(done)"),
                title=tui_config.response_panel_title,
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
        console.print("[green]Done![/green]")

    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
