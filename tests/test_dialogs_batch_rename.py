"""Tests for pathlib_gui.dialogs.batch_rename — pure apply_rename_mode function."""

from __future__ import annotations

from pathlib_gui.dialogs.batch_rename import MODES, apply_rename_mode


class TestApplyRenameModePrefix:
    def test_adds_prefix(self) -> None:
        result = apply_rename_mode("file.txt", "Add prefix", {"prefix": "new_"})
        assert result == "new_file.txt"

    def test_empty_prefix(self) -> None:
        result = apply_rename_mode("file.txt", "Add prefix", {"prefix": ""})
        assert result == "file.txt"


class TestApplyRenameModeSuffix:
    def test_adds_suffix_before_extension(self) -> None:
        result = apply_rename_mode("file.txt", "Add suffix", {"suffix_text": "_v2"})
        assert result == "file_v2.txt"

    def test_no_extension(self) -> None:
        result = apply_rename_mode("Makefile", "Add suffix", {"suffix_text": "_old"})
        assert result == "Makefile_old"


class TestApplyRenameModeReplace:
    def test_replaces_text(self) -> None:
        result = apply_rename_mode("my_file.txt", "Replace text", {"find": "my_", "replace": ""})
        assert result == "file.txt"

    def test_replace_with_new_text(self) -> None:
        result = apply_rename_mode("old_name.py", "Replace text", {"find": "old", "replace": "new"})
        assert result == "new_name.py"

    def test_no_match_unchanged(self) -> None:
        result = apply_rename_mode("unchanged.py", "Replace text", {"find": "xyz", "replace": "abc"})
        assert result == "unchanged.py"


class TestApplyRenameModeRegex:
    def test_regex_replace(self) -> None:
        result = apply_rename_mode("test_001.py", "Regex replace", {"pattern": r"\d+", "replace": "XXX"})
        assert result == "test_XXX.py"

    def test_invalid_regex_returns_original(self) -> None:
        result = apply_rename_mode("file.txt", "Regex replace", {"pattern": "[invalid(", "replace": "x"})
        assert result == "file.txt"

    def test_strip_prefix_with_regex(self) -> None:
        result = apply_rename_mode("prefix_name.txt", "Regex replace", {"pattern": r"^prefix_", "replace": ""})
        assert result == "name.txt"


class TestApplyRenameModeChangeExtension:
    def test_changes_extension(self) -> None:
        result = apply_rename_mode("script.py", "Change extension", {"new_ext": "txt"})
        assert result == "script.txt"

    def test_adds_dot_if_missing(self) -> None:
        result = apply_rename_mode("file.md", "Change extension", {"new_ext": "rst"})
        assert result == "file.rst"

    def test_dot_provided(self) -> None:
        result = apply_rename_mode("file.md", "Change extension", {"new_ext": ".rst"})
        assert result == "file.rst"

    def test_empty_extension_strips_it(self) -> None:
        result = apply_rename_mode("file.txt", "Change extension", {"new_ext": ""})
        assert result == "file"


class TestApplyRenameModeNumberSequence:
    def test_default_numbering(self) -> None:
        result = apply_rename_mode("file.txt", "Number sequence", {"start": "1", "pad": "3"})
        assert result == "001_file.txt"

    def test_custom_start(self) -> None:
        result = apply_rename_mode("file.txt", "Number sequence", {"start": "10", "pad": "3"})
        assert result == "010_file.txt"

    def test_zero_padding(self) -> None:
        result = apply_rename_mode("f.txt", "Number sequence", {"start": "5", "pad": "5"})
        assert result == "00005_f.txt"


class TestApplyRenameModeCasing:
    def test_lowercase(self) -> None:
        assert apply_rename_mode("HELLO.TXT", "Lowercase", {}) == "hello.txt"

    def test_uppercase(self) -> None:
        assert apply_rename_mode("hello.txt", "Uppercase", {}) == "HELLO.TXT"

    def test_title_case(self) -> None:
        assert apply_rename_mode("hello world.txt", "Title case", {}) == "Hello World.Txt"


class TestApplyRenameModeSlugify:
    def test_basic_slugify(self) -> None:
        result = apply_rename_mode("Hello World!.txt", "Slugify", {})
        assert " " not in result
        assert "!" not in result
        assert result.endswith(".txt")

    def test_spaces_become_underscores(self) -> None:
        result = apply_rename_mode("my file name.txt", "Slugify", {})
        assert result == "my_file_name.txt"

    def test_lowercase_output(self) -> None:
        result = apply_rename_mode("UPPER.txt", "Slugify", {})
        assert result == result.lower()


class TestApplyRenameModeUnknown:
    def test_unknown_mode_returns_original(self) -> None:
        result = apply_rename_mode("file.txt", "Unknown Mode", {})
        assert result == "file.txt"


class TestModes:
    def test_all_modes_defined(self) -> None:
        assert len(MODES) == 10

    def test_modes_are_strings(self) -> None:
        assert all(isinstance(m, str) for m in MODES)

    def test_each_mode_produces_a_string(self) -> None:
        params = {
            "prefix": "p_",
            "suffix_text": "_s",
            "find": "a",
            "replace": "b",
            "pattern": r"\d",
            "new_ext": ".txt",
            "start": "1",
            "pad": "3",
        }
        for mode in MODES:
            result = apply_rename_mode("test_file_001.txt", mode, params)
            assert isinstance(result, str)
