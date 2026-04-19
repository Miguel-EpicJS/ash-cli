class ScrollBuffer:
    def __init__(self, height: int = 20) -> None:
        self.height = height
        self.text = ""
        self._offset = 0

    def add(self, s: str) -> None:
        self.text += s

    def scroll_up(self) -> None:
        if self._offset > 0:
            self._offset -= 1

    def scroll_down(self) -> None:
        lines = self.text.split("\n")
        if self._offset + self.height < len(lines):
            self._offset += 1

    def show(self) -> str:
        lines = self.text.split("\n")
        start = self._offset
        end = min(start + self.height, len(lines))
        return "\n".join(lines[start:end])

    @property
    def offset(self) -> int:
        return self._offset
