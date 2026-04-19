from __future__ import annotations

from ash_cli.buffer import ScrollBuffer


class TestScrollBuffer:
    def test_default_values(self) -> None:
        buf = ScrollBuffer()
        assert buf.height == 0
        assert buf.text == ""
        assert buf.offset == 0

    def test_with_height(self) -> None:
        buf = ScrollBuffer(height=10)
        assert buf.height == 10

    def test_add_text(self) -> None:
        buf = ScrollBuffer()
        buf.add("hello")
        assert buf.text == "hello"

    def test_add_multiple(self) -> None:
        buf = ScrollBuffer()
        buf.add("hello")
        buf.add(" world")
        assert buf.text == "hello world"

    def test_scroll_up(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2\nline3\nline4"
        buf.scroll_up()
        assert buf.offset == 0

    def test_scroll_up_at_zero(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2\nline3"
        buf._offset = 0
        buf.scroll_up()
        assert buf.offset == 0

    def test_scroll_down(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2\nline3\nline4"
        buf.scroll_down()
        assert buf.offset == 1

    def test_scroll_down_at_max(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2"
        buf._offset = 0
        buf.scroll_down()
        assert buf.offset == 0

    def test_scroll_down_no_height(self) -> None:
        buf = ScrollBuffer(height=0)
        buf.text = "line1\nline2\nline3"
        buf.scroll_down()
        assert buf.offset == 0

    def test_show_no_height(self) -> None:
        buf = ScrollBuffer(height=0)
        buf.text = "hello"
        result = buf.show()
        assert result == "hello"

    def test_show_with_height(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2\nline3\nline4"
        result = buf.show()
        assert result == "line1\nline2"

    def test_show_with_offset(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2\nline3\nline4"
        buf._offset = 1
        result = buf.show()
        assert result == "line2\nline3"

    def test_show_at_end(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2"
        buf._offset = 1
        result = buf.show()
        assert result == "line2"

    def test_offset_property(self) -> None:
        buf = ScrollBuffer(height=5)
        buf._offset = 3
        assert buf.offset == 3


class TestScrollBufferEdgeCases:
    def test_empty_text(self) -> None:
        buf = ScrollBuffer(height=10)
        assert buf.show() == ""

    def test_single_line_with_height(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "single"
        result = buf.show()
        assert result == "single"

    def test_exact_height_lines(self) -> None:
        buf = ScrollBuffer(height=3)
        buf.text = "line1\nline2\nline3"
        result = buf.show()
        assert result == "line1\nline2\nline3"

    def test_scroll_up_multiple(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2\nline3\nline4\nline5"
        buf._offset = 2
        buf.scroll_up()
        buf.scroll_up()
        assert buf.offset == 0

    def test_scroll_down_multiple(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.text = "line1\nline2\nline3\nline4\nline5"
        buf.scroll_down()
        buf.scroll_down()
        buf.scroll_down()
        assert buf.offset == 3

    def test_newline_handling(self) -> None:
        buf = ScrollBuffer(height=2)
        buf.add("line1\nline2\nline3")
        result = buf.show()
        assert "line1" in result
        assert "line2" in result
