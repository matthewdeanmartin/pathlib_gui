"""Tests for pathlib_gui.models.archive."""

from __future__ import annotations

from pathlib_gui.models.archive import ArchiveMember, compression_ratio, format_size


class TestFormatSize:
    def test_bytes(self) -> None:
        assert format_size(500) == "500.0 B"

    def test_kilobytes(self) -> None:
        assert format_size(1024) == "1.0 KB"

    def test_megabytes(self) -> None:
        assert format_size(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self) -> None:
        assert format_size(1024**3) == "1.0 GB"

    def test_large_terabytes(self) -> None:
        result = format_size(1024**4)
        assert "TB" in result

    def test_zero(self) -> None:
        assert format_size(0) == "0.0 B"


def make_member(size: int, compressed_size: int, is_dir: bool = False) -> ArchiveMember:
    return ArchiveMember(
        name="file.txt",
        size=size,
        compressed_size=compressed_size,
        modified=0.0,
        mode=0,
        crc=0,
        is_dir=is_dir,
        is_symlink=False,
        link_target="",
    )


class TestCompressionRatio:
    def test_perfect_compression(self) -> None:
        member = make_member(size=1000, compressed_size=0)
        assert compression_ratio(member) == "100%"

    def test_no_compression(self) -> None:
        member = make_member(size=1000, compressed_size=1000)
        assert compression_ratio(member) == "0%"

    def test_half_compression(self) -> None:
        member = make_member(size=1000, compressed_size=500)
        assert compression_ratio(member) == "50%"

    def test_directory_returns_empty(self) -> None:
        member = make_member(size=0, compressed_size=0, is_dir=True)
        assert compression_ratio(member) == ""

    def test_zero_size_returns_empty(self) -> None:
        member = make_member(size=0, compressed_size=0)
        assert compression_ratio(member) == ""
