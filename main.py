from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich import box
import shutil
import sys
import threading
import queue

console = Console()

class ScrollBuffer:
    def __init__(self, height=20):
        self.height = height
        self.text = ""
        self.offset = 0
        
    def add(self, s):
        self.text += s
        
    def scroll_up(self):
        if self.offset > 0:
            self.offset -= 1
            
    def scroll_down(self):
        lines = self.text.split("\n")
        if self.offset + self.height < len(lines):
            self.offset += 1
    
    def show(self):
        lines = self.text.split("\n")
        start = self.offset
        end = min(start + self.height, len(lines))
        return "\n".join(lines[start:end])

def run():
    import select
    import tty
    import termios
    
    is_tty = sys.stdin.isatty()
    old_settings = None
    
    if is_tty:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
    
    try:
        prompt = "Explain what 1+1 equals"
        
        console.print(Panel(Text(f"Prompt: {prompt}"), title="Input", border_style="green", box=box.ROUNDED))
        
        buffer = ScrollBuffer(height=15)
        thinking_queue = queue.Queue()
        should_quit = [False]
        response = [None]
        
        agent = Agent(
            model=OpenAILike(
                id="qwen3.5:4b",
                api_key="not-needed",
                base_url="http://localhost:8080/v1",
                temperature=0.6,
                max_tokens=4096,
            ),
            description="You are a helpful AI assistant.",
            instructions=["Think and respond briefly."],
            markdown=True,
        )
        
        content_buffer = ScrollBuffer(height=15)
        
        def stream_agent():
            try:
                for chunk in agent.run(prompt, stream=True):
                    if should_quit[0]:
                        break
                    reasoning = getattr(chunk, 'reasoning_content', None)
                    if reasoning:
                        thinking_queue.put(reasoning)
                    content = getattr(chunk, 'content', None)
                    if content:
                        response[0] = content
                        content_buffer.add(content)
            except Exception as e:
                thinking_queue.put(f"Error: {e}")
        
        response_panel = Panel(Text(""), title="Response", border_style="cyan", height=17)
        with Live(
            Group(
                Panel(Text("..."), title="Thinking", border_style="blue", height=17),
                response_panel
            ),
            console=console,
            refresh_per_second=8,
            transient=False
        ) as live:
            if is_tty:
                console.print("[dim]j/k scroll, q quit[/dim]")
            
            stream_thread = threading.Thread(target=stream_agent, daemon=True)
            stream_thread.start()
            
            while stream_thread.is_alive():
                # Get new reasoning chunks
                try:
                    while True:
                        item = thinking_queue.get_nowait()
                        buffer.add(item)
                except queue.Empty:
                    pass
                
                live.update(
                    Group(
                        Panel(Text(buffer.show()), title="Thinking", border_style="blue", height=17),
                        Panel(Text(content_buffer.show()), title="Response", border_style="cyan", height=17)
                    )
                )
                
                # Handle keys
                if is_tty and select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if key == "q":
                        should_quit[0] = True
                        break
                    elif key == "j":
                        buffer.scroll_down()
                        content_buffer.scroll_down()
                    elif key == "k":
                        buffer.scroll_up()
                        content_buffer.scroll_up()
                    elif key == "\x1b":
                        if sys.stdin.read(1) == "[":
                            arrow = sys.stdin.read(1)
                            if arrow == "A":
                                buffer.scroll_up()
                                content_buffer.scroll_up()
                            elif arrow == "B":
                                buffer.scroll_down()
                                content_buffer.scroll_down()
                    live.update(
                        Group(
                            Panel(Text(buffer.show()), title="Thinking", border_style="blue", height=17),
                            Panel(Text(content_buffer.show()), title="Response", border_style="cyan", height=17)
                        )
                    )
        
        console.print(Panel(Text(response[0] or "(done)"), title="Response", border_style="cyan", box=box.ROUNDED))
        console.print("[green]Done![/green]")
        
    finally:
        if old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    run()
