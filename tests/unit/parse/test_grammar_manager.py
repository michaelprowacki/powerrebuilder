"""Tests for GrammarManager."""

from unittest.mock import Mock, patch

import pytest
from lark import Lark
from lark.exceptions import GrammarError

from src.parse import GrammarManager, get_default_manager
from src.parse.constants import FileType
from src.parse.exceptions import GrammarNotFoundError


class TestGrammarManager:
    """Test suite for GrammarManager."""

    def test_init_default_directory(self):
        """Test initialization with default grammar directory."""
        manager = GrammarManager()
        assert manager.grammar_dir.name == "grammar"
        assert manager.grammar_dir.exists()

    def test_init_custom_directory(self, tmp_path):
        """Test initialization with custom grammar directory."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        manager = GrammarManager(grammar_dir)
        assert manager.grammar_dir == grammar_dir

    def test_init_missing_directory(self, tmp_path):
        """Test initialization with non-existent directory."""
        grammar_dir = tmp_path / "missing"

        with pytest.raises(GrammarNotFoundError, match="Grammar directory not found"):
            GrammarManager(grammar_dir)

    def test_load_grammar_caching(self, tmp_path):
        """Test that grammars are cached after loading."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        # Create a simple grammar file
        grammar_file = grammar_dir / "test.lark"
        grammar_file.write_text('start: "hello" "world"')

        manager = GrammarManager(grammar_dir)

        # Load grammar twice
        parser1 = manager.load_grammar("test")
        parser2 = manager.load_grammar("test")

        # Should return same cached instance
        assert parser1 is parser2

    def test_load_grammar_different_start_rules(self, tmp_path):
        """Test loading same grammar with different start rules."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        # Create grammar with multiple rules
        grammar_file = grammar_dir / "test.lark"
        grammar_file.write_text("""
            start: rule1 | rule2
            rule1: "hello"
            rule2: "world"
        """)

        manager = GrammarManager(grammar_dir)

        # Load with different start rules
        parser1 = manager.load_grammar("test", start="start")
        parser2 = manager.load_grammar("test", start="rule1")

        # Should be different instances
        assert parser1 is not parser2

    def test_load_grammar_not_found(self, tmp_path):
        """Test loading non-existent grammar."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        manager = GrammarManager(grammar_dir)

        with pytest.raises(GrammarNotFoundError, match="Grammar file not found"):
            manager.load_grammar("missing")

    def test_load_grammar_syntax_error(self, tmp_path):
        """Test loading grammar with syntax errors."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        # Create invalid grammar file
        grammar_file = grammar_dir / "invalid.lark"
        grammar_file.write_text("start: invalid syntax here")

        manager = GrammarManager(grammar_dir)

        with pytest.raises(GrammarError):
            manager.load_grammar("invalid")

    def test_register_grammar(self):
        """Test registering grammar directly."""
        manager = GrammarManager()

        grammar_content = 'start: "test"'
        manager.register_grammar("custom", grammar_content)

        # Should be able to load registered grammar
        parser = manager.load_grammar("custom")
        assert isinstance(parser, Lark)

    def test_register_grammar_clears_cache(self, tmp_path):
        """Test that registering grammar clears its cache."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        grammar_file = grammar_dir / "test.lark"
        grammar_file.write_text('start: "original"')

        manager = GrammarManager(grammar_dir)

        # Load original
        parser1 = manager.load_grammar("test")

        # Register new version
        manager.register_grammar("test", 'start: "modified"')

        # Load again - should get new version
        parser2 = manager.load_grammar("test")

        assert parser1 is not parser2

    def test_get_parser_window_type(self):
        """Test getting parser for window file type."""
        manager = GrammarManager()

        # Mock load_grammar to avoid actual file loading
        with patch.object(manager, "load_grammar") as mock_load:
            mock_parser = Mock(spec=Lark)
            mock_load.return_value = mock_parser

            parser = manager.get_parser(FileType.WINDOW)

            mock_load.assert_called_once_with("powerbuilder", start=None)
            assert parser is mock_parser

    def test_get_parser_datawindow_type(self):
        """Test getting parser for datawindow file type."""
        manager = GrammarManager()

        with patch.object(manager, "load_grammar") as mock_load:
            mock_parser = Mock(spec=Lark)
            mock_load.return_value = mock_parser

            parser = manager.get_parser(FileType.DATAWINDOW)

            mock_load.assert_called_once_with("datawindow", start="datawindow")
            assert parser is mock_parser

    def test_get_parser_sql_type(self):
        """Test getting parser for SQL file type."""
        manager = GrammarManager()

        with patch.object(manager, "load_grammar") as mock_load:
            mock_parser = Mock(spec=Lark)
            mock_load.return_value = mock_parser

            parser = manager.get_parser(FileType.QUERY)

            mock_load.assert_called_once_with(
                "sql",
                start="sql_statements",
                lexer="basic",
            )
            assert parser is mock_parser

    def test_get_parser_string_extension(self):
        """Test getting parser with string extension."""
        manager = GrammarManager()

        with patch.object(manager, "load_grammar") as mock_load:
            mock_parser = Mock(spec=Lark)
            mock_load.return_value = mock_parser

            parser = manager.get_parser(".srw")

            mock_load.assert_called_once_with("powerbuilder", start=None)
            assert parser is mock_parser

    def test_get_parser_unsupported_type(self):
        """Test getting parser for unsupported file type."""
        manager = GrammarManager()

        with pytest.raises(ValueError, match="Unsupported file type"):
            manager.get_parser("unknown")

    def test_clear_cache(self, tmp_path):
        """Test clearing all caches."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        grammar_file = grammar_dir / "test.lark"
        grammar_file.write_text('start: "test"')

        manager = GrammarManager(grammar_dir)

        # Load grammar to populate caches
        manager.load_grammar("test")

        # Verify caches are populated
        assert len(manager._cache) > 0
        assert len(manager._grammars) > 0

        # Clear caches
        manager.clear_cache()

        # Verify caches are empty
        assert len(manager._cache) == 0
        assert len(manager._grammars) == 0
        assert len(manager._dependencies) == 0

    def test_extract_imports(self):
        """Test extracting imports from grammar content."""
        manager = GrammarManager()

        grammar_content = """
        %import common.WS
        %import common.NEWLINE
        %import sql.select_statement

        start: WS* select_statement NEWLINE
        """

        imports = manager._extract_imports(grammar_content)

        assert imports == {"common", "sql"}

    def test_check_circular_dependencies(self):
        """Test circular dependency detection."""
        manager = GrammarManager()

        # Set up circular dependencies
        manager._dependencies = {
            "a": {"b"},
            "b": {"c"},
            "c": {"a"},  # Creates cycle: a -> b -> c -> a
            "d": {"e"},
            "e": set(),  # No cycle
        }

        cycles = manager.check_circular_dependencies()

        # Should detect the a -> b -> c -> a cycle
        assert len(cycles) == 1
        cycle = cycles[0]
        assert set(cycle[:-1]) == {"a", "b", "c"}  # Last element repeats first

    def test_get_grammar_info(self, tmp_path):
        """Test getting grammar information."""
        grammar_dir = tmp_path / "grammars"
        grammar_dir.mkdir()

        # Create test grammar
        grammar_file = grammar_dir / "test.lark"
        grammar_file.write_text("%import common.WS\nstart: WS")

        manager = GrammarManager(grammar_dir)

        # Load grammar
        manager.load_grammar("test")

        info = manager.get_grammar_info()

        assert "test" in info
        assert info["test"]["loaded"] is True
        assert info["test"]["cached_parsers"] == 1
        assert info["test"]["dependencies"] == ["common"]
        assert info["test"]["file"].endswith("test.lark")

    def test_get_default_manager_singleton(self):
        """Test that get_default_manager returns singleton."""
        manager1 = get_default_manager()
        manager2 = get_default_manager()

        assert manager1 is manager2
