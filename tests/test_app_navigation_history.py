"""Tests for pathlib_gui.app.NavigationHistory."""

from __future__ import annotations

from pathlib import Path

from pathlib_gui.app import NavigationHistory


class TestNavigationHistoryInitial:
    def test_cannot_go_back_initially(self) -> None:
        h = NavigationHistory()
        assert h.can_go_back() is False

    def test_cannot_go_forward_initially(self) -> None:
        h = NavigationHistory()
        assert h.can_go_forward() is False

    def test_go_back_returns_none_when_empty(self) -> None:
        h = NavigationHistory()
        assert h.go_back() is None

    def test_go_forward_returns_none_when_empty(self) -> None:
        h = NavigationHistory()
        assert h.go_forward() is None


class TestNavigationHistoryPush:
    def test_push_single_item(self) -> None:
        h = NavigationHistory()
        p = Path("/home")
        h.push(p)
        assert h.can_go_back() is False
        assert h.can_go_forward() is False

    def test_push_two_items_enables_back(self) -> None:
        h = NavigationHistory()
        h.push(Path("/home"))
        h.push(Path("/home/user"))
        assert h.can_go_back() is True

    def test_push_truncates_forward_history(self) -> None:
        h = NavigationHistory()
        h.push(Path("/a"))
        h.push(Path("/b"))
        h.go_back()
        h.push(Path("/c"))
        assert h.can_go_forward() is False

    def test_index_updates_correctly(self) -> None:
        h = NavigationHistory()
        h.push(Path("/a"))
        h.push(Path("/b"))
        h.push(Path("/c"))
        assert h.index == 2


class TestNavigationHistoryBackForward:
    def test_go_back_returns_previous(self) -> None:
        h = NavigationHistory()
        h.push(Path("/a"))
        h.push(Path("/b"))
        result = h.go_back()
        assert result == Path("/a")

    def test_go_forward_returns_next(self) -> None:
        h = NavigationHistory()
        h.push(Path("/a"))
        h.push(Path("/b"))
        h.go_back()
        result = h.go_forward()
        assert result == Path("/b")

    def test_full_navigation_cycle(self) -> None:
        h = NavigationHistory()
        paths = [Path(f"/{x}") for x in "abcde"]
        for p in paths:
            h.push(p)
        assert h.go_back() == Path("/d")
        assert h.go_back() == Path("/c")
        assert h.go_forward() == Path("/d")
        assert h.can_go_forward() is True
        assert h.go_forward() == Path("/e")
        assert h.can_go_forward() is False

    def test_cannot_go_back_past_start(self) -> None:
        h = NavigationHistory()
        h.push(Path("/a"))
        h.push(Path("/b"))
        h.go_back()
        assert h.go_back() is None
        assert h.can_go_back() is False

    def test_cannot_go_forward_past_end(self) -> None:
        h = NavigationHistory()
        h.push(Path("/a"))
        h.push(Path("/b"))
        h.go_back()
        h.go_forward()
        assert h.go_forward() is None
        assert h.can_go_forward() is False

    def test_can_go_forward_after_back(self) -> None:
        h = NavigationHistory()
        h.push(Path("/a"))
        h.push(Path("/b"))
        h.go_back()
        assert h.can_go_forward() is True
