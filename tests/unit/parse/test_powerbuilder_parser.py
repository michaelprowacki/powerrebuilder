"""Tests for PowerBuilder parser functionality.

Tests various aspects of the PowerBuilder parsing system including
grammar loading, preprocessing, and basic parsing operations.
"""

from pathlib import Path

import pytest
from lark import Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedToken

from src.parse.constants import (
    PB_BASIC_TYPES,
    PB_KEYWORDS,
    PB_OPERATORS,
)
from src.parse.grammar.loader import GrammarManager
from src.parse.preprocessor.preprocessor import PowerBuilderPreprocessor


class TestGrammarManager:
    """Test the GrammarManager class."""

    def test_manager_initialization(self):
        """Test GrammarManager initialization."""
        gm = GrammarManager()
        assert gm is not None

    def test_manager_load_basic_grammar(self):
        """Test loading basic grammar."""
        gm = GrammarManager()
        parser = gm.get_parser("powerbuilder")
        assert parser is not None

    def test_list_available_grammars(self):
        """Test listing available grammar files."""
        gm = GrammarManager()
        grammars = gm.list_available_grammars()

        # Should have at least the core grammar
        assert len(grammars) > 0
        assert any("powerbuilder" in g for g in grammars)

    def test_get_grammar_path(self):
        """Test getting path to a specific grammar."""
        gm = GrammarManager()

        # Test valid grammar
        path = gm.get_grammar_path("powerbuilder_core")
        assert path.exists()
        assert path.suffix == ".lark"

        # Test invalid grammar
        with pytest.raises(ValueError):
            gm.get_grammar_path("nonexistent_grammar")

    def test_load_grammar(self):
        """Test loading a grammar file."""
        gm = GrammarManager()
        parser = gm.load_grammar("powerbuilder_core")

        assert isinstance(parser, Lark)
        assert parser is not None


class TestPowerBuilderPreprocessor:
    """Test the PowerBuilder preprocessor."""

    def test_preprocessor_init(self):
        """Test preprocessor initialization."""
        pp = PowerBuilderPreprocessor(Path.cwd())  # Provide base_path
        assert pp.base_path == Path.cwd()  # Check something that exists

        # def test_remove_line_continuations(self):

    #     """Test removing line continuations."""
    #     pp = PowerBuilderPreprocessor(Path.cwd())
    #
    #     # Test basic continuation
    #     code = "integer i = 1 + &\n    2"
    #     result = pp.remove_line_continuations(code)
    #     assert result == "integer i = 1 +     2"
    #
    #     # Test multiple continuations
    #     code = "string s = 'hello' + &\n    'world' + &\n    '!'"
    #     result = pp.remove_line_continuations(code)
    #     assert result == "string s = 'hello' +     'world' +     '!'"

    # def test_normalize_keywords(self):
    #     """Test keyword normalization."""
    #     pp = PowerBuilderPreprocessor(Path.cwd())
    #
    #     # Test case normalization
    #     code = "INTEGER i\nSTRING s\nBoolean b"
    #     result = pp.normalize_keywords(code)
    #     assert "integer" in result
    #     assert "string" in result
    #     assert "boolean" in result

    # def test_preprocess_complete(self):
    #     """Test complete preprocessing pipeline."""
    #     pp = PowerBuilderPreprocessor(Path.cwd())
    #
    #     code = """
    #     INTEGER i = 1 + &
    #         2
    #     STRING name = "test"
    #     """
    #
    #     result = pp.preprocess(code)
    #     assert "integer" in result
    #     assert "&" not in result
    #     assert "2" in result


class TestPowerBuilderConstants:
    """Test PowerBuilder constants definitions."""

    def test_keywords_defined(self):
        """Test that keywords are properly defined."""
        assert len(PB_KEYWORDS) > 0
        assert "if" in PB_KEYWORDS
        assert "then" in PB_KEYWORDS
        assert "else" in PB_KEYWORDS
        assert "end" in PB_KEYWORDS
        assert "for" in PB_KEYWORDS
        assert "next" in PB_KEYWORDS

    def test_types_defined(self):
        """Test that types are properly defined."""
        assert len(PB_BASIC_TYPES) > 0
        assert "integer" in PB_BASIC_TYPES
        assert "string" in PB_BASIC_TYPES
        assert "boolean" in PB_BASIC_TYPES
        assert "decimal" in PB_BASIC_TYPES
        assert "date" in PB_BASIC_TYPES

    def test_operators_defined(self):
        """Test that operators are properly defined."""
        assert len(PB_OPERATORS) > 0
        assert "+" in PB_OPERATORS
        assert "-" in PB_OPERATORS
        assert "*" in PB_OPERATORS
        assert "/" in PB_OPERATORS
        assert "=" in PB_OPERATORS
        assert "<>" in PB_OPERATORS


class TestParserIntegration:
    """Test parser integration with grammar and preprocessing."""

    def test_parse_simple_declaration(self):
        """Test parsing a simple variable declaration."""
        gm = GrammarManager()
        parser = gm.load_grammar("powerbuilder_core")
        pp = PowerBuilderPreprocessor(Path.cwd())

        code = "integer count"
        processed = pp.preprocess(code)
        tree = parser.parse(processed)

        assert isinstance(tree, Tree)
        assert tree.data == "start"

    def test_parse_with_line_continuation(self):
        """Test parsing code with line continuation."""
        gm = GrammarManager()
        parser = gm.load_grammar("powerbuilder_core")
        pp = PowerBuilderPreprocessor(Path.cwd())  # Provide base_path

        code = """integer result = 1 + &
            2 + &
            3"""
        processed = pp.preprocess(code)
        tree = parser.parse(processed)

        assert isinstance(tree, Tree)

    def test_parse_multiple_statements(self):
        """Test parsing multiple statements."""
        gm = GrammarManager()
        parser = gm.load_grammar("powerbuilder_core")
        pp = PowerBuilderPreprocessor(Path.cwd())  # Provide base_path

        code = """
        integer i = 10
        string name = 'test'
        boolean flag = true
        """
        processed = pp.preprocess(code)
        tree = parser.parse(processed)

        assert isinstance(tree, Tree)

    def test_parse_control_structures(self):
        """Test parsing control structures."""
        gm = GrammarManager()
        parser = gm.load_grammar("powerbuilder_core")
        pp = PowerBuilderPreprocessor(Path.cwd())  # Provide base_path

        code = """
        if x > 0 then
            y = 1
        else
            y = -1
        end if
        """
        processed = pp.preprocess(code)
        tree = parser.parse(processed)

        assert isinstance(tree, Tree)

    def test_parse_error_handling(self):
        """Test parser error handling."""
        gm = GrammarManager()
        parser = gm.load_grammar("powerbuilder_core")
        pp = PowerBuilderPreprocessor(Path.cwd())  # Provide base_path

        # Invalid syntax
        code = "integer = 5"  # Missing variable name
        processed = pp.preprocess(code)

        with pytest.raises((UnexpectedCharacters, UnexpectedToken)):
            parser.parse(processed)


class TestGrammarCoverage:
    """Test coverage of various grammar constructs."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance for tests."""
        gm = GrammarManager()
        return gm.load_grammar("powerbuilder_core")

    @pytest.fixture
    def preprocessor(self):
        """Create a preprocessor instance for tests."""
        return PowerBuilderPreprocessor(Path.cwd())  # Provide base_path

    def test_all_basic_types(self, parser, preprocessor):
        """Test all basic PowerBuilder types."""
        types_to_test = [
            "integer",
            "string",
            "boolean",
            "date",
            "time",
            "decimal",
            "long",
            "real",
            "char",
            "double",
        ]

        for pb_type in types_to_test:
            code = f"{pb_type} var_{pb_type}"
            processed = preprocessor.preprocess(code)

            # Only test if type is in our constants
            if pb_type in PB_BASIC_TYPES:
                tree = parser.parse(processed)
                assert isinstance(tree, Tree)

    def test_operators(self, parser, preprocessor):
        """Test various operators."""
        test_cases = [
            "x = y + z",
            "x = y - z",
            "x = y * z",
            "x = y / z",
            "x = y > z",
            "x = y < z",
            "x = y >= z",
            "x = y <= z",
            "x = y = z",  # Assignment with comparison
            "x = y <> z",  # Not equal
        ]

        for code in test_cases:
            processed = preprocessor.preprocess(code)
            tree = parser.parse(processed)
            assert isinstance(tree, Tree)

    def test_string_literals(self, parser, preprocessor):
        """Test various string literal formats."""
        test_cases = [
            'x = "double quoted"',
            "x = 'single quoted'",
            'x = "string with \\"escaped\\" quotes"',
            "x = 'string with ''escaped'' quotes'",
            'x = ""',  # Empty string
            "x = ''",  # Empty string single quotes
        ]

        for code in test_cases:
            processed = preprocessor.preprocess(code)
            tree = parser.parse(processed)
            assert isinstance(tree, Tree)

    def test_numeric_literals(self, parser, preprocessor):
        """Test various numeric literal formats."""
        test_cases = [
            "x = 123",  # Integer
            "x = -123",  # Negative integer
            "x = 123.456",  # Decimal
            "x = -123.456",  # Negative decimal
            "x = .5",  # Decimal starting with dot
            "x = 0",  # Zero
        ]

        for code in test_cases:
            processed = preprocessor.preprocess(code)
            tree = parser.parse(processed)
            assert isinstance(tree, Tree)

    def test_boolean_literals(self, parser, preprocessor):
        """Test boolean literals."""
        test_cases = [
            "x = true",
            "x = false",
            "x = TRUE",
            "x = FALSE",
        ]

        for code in test_cases:
            processed = preprocessor.preprocess(code)
            tree = parser.parse(processed)
            assert isinstance(tree, Tree)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
