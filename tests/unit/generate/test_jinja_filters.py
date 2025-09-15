"""Unit tests for Jinja2 custom filters."""

from src.generate.filters import (
    dedent_filter,
    indent_block_filter,
    indent_filter,
    indent_nested_filter,
)


class TestJinjaFilters:
    """Test custom Jinja2 filters."""

    def test_indent_filter_single_line(self):
        """Test indenting a single line."""
        assert indent_filter("hello", 0) == "hello"
        assert indent_filter("hello", 1) == "    hello"
        assert indent_filter("hello", 2) == "        hello"
        assert indent_filter("hello", 1, width=2) == "  hello"

    def test_indent_filter_multi_line(self):
        """Test indenting multiple lines."""
        text = "line1\nline2\nline3"
        expected = "    line1\n    line2\n    line3"
        assert indent_filter(text, 1) == expected

    def test_indent_filter_empty_lines(self):
        """Test that empty lines are not indented."""
        text = "line1\n\nline3"
        expected = "    line1\n\n    line3"
        assert indent_filter(text, 1) == expected

    def test_indent_filter_list_input(self):
        """Test indenting with list input."""
        lines = ["line1", "line2", "line3"]
        expected = "    line1\n    line2\n    line3"
        assert indent_filter(lines, 1) == expected

    def test_indent_block_filter(self):
        """Test smart block indentation."""
        # Code block with existing indentation
        code = """if x > 0:
    print("positive")
else:
    print("negative")"""

        # Apply base level 1
        expected = """    if x > 0:
        print("positive")
    else:
        print("negative")"""

        assert indent_block_filter(code, 1) == expected

    def test_indent_block_filter_preserves_relative(self):
        """Test that relative indentation is preserved."""
        code = """    def func():
        if True:
            return 1
        else:
            return 0"""

        # Apply base level 1 - should preserve the relative indentation
        expected = """    def func():
        if True:
            return 1
        else:
            return 0"""

        assert indent_block_filter(code, 1) == expected

    def test_indent_nested_filter(self):
        """Test nested indentation helper."""
        assert indent_nested_filter("nested", 0) == "    nested"
        assert indent_nested_filter("nested", 1) == "        nested"
        assert indent_nested_filter("nested", 2) == "            nested"

    def test_dedent_filter(self):
        """Test dedentation."""
        text = """    line1
    line2
        line3
    line4"""

        expected = """line1
line2
    line3
line4"""

        assert dedent_filter(text) == expected

    def test_dedent_filter_mixed_indentation(self):
        """Test dedentation with mixed indentation."""
        text = """        def func():
            if True:
                return 1
            else:
                return 0"""

        expected = """def func():
    if True:
        return 1
    else:
        return 0"""

        assert dedent_filter(text) == expected

    def test_integration_with_jinja2(self):
        """Test filters work with Jinja2 environment."""
        from jinja2 import Environment

        from src.generate.filters import register_filters

        env = Environment()
        register_filters(env)

        # Test that filters are registered
        assert "indent" in env.filters
        assert "indent_block" in env.filters
        assert "indent_nested" in env.filters
        assert "dedent" in env.filters

        # Test using filter in template
        template = env.from_string("{{ text | indent(2) }}")
        result = template.render(text="hello")
        assert result == "        hello"

        # Test chaining filters
        template = env.from_string("{{ text | dedent | indent(1) }}")
        result = template.render(text="    hello")
        assert result == "    hello"
