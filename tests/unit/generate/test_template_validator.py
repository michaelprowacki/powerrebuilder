#!/usr/bin/env python3
"""Test template validation system."""

import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.generate.templates.engine import (
    TemplateContextValidator,
    TemplateConventionValidator,
    TemplateOutputValidator,
    TemplateSyntaxValidator,
    TemplateValidator,
)


class TestTemplateSyntaxValidator:
    """Test template syntax validation."""

    def test_valid_syntax(self):
        """Test validation of template with valid syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid template
            template_path = Path(tmpdir) / "valid.jinja2"
            template_path.write_text("""
{# Valid template #}
{% for item in items %}
    {{ item.name }}
{% endfor %}
""")

            env = Environment(loader=FileSystemLoader(tmpdir))
            validator = TemplateSyntaxValidator(env)

            is_valid, error = validator.validate("valid.jinja2")
            assert is_valid
            assert error is None

    def test_invalid_syntax(self):
        """Test validation of template with invalid syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid template
            template_path = Path(tmpdir) / "invalid.jinja2"
            template_path.write_text("""
{# Invalid template #}
{% for item in items
    {{ item.name }}
{% endfor %}
""")

            env = Environment(loader=FileSystemLoader(tmpdir))
            validator = TemplateSyntaxValidator(env)

            is_valid, error = validator.validate("invalid.jinja2")
            assert not is_valid
            assert "Syntax error" in error


class TestTemplateContextValidator:
    """Test template context validation."""

    def test_extract_variables(self):
        """Test variable extraction from template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "template.jinja2"
            template_path.write_text("""
{{ name }}
{{ user.email }}
{% for item in items %}
    {{ item.value }}
{% endfor %}
""")

            env = Environment(loader=FileSystemLoader(tmpdir))
            validator = TemplateContextValidator(env)

            variables = validator.extract_variables("template.jinja2")
            assert "name" in variables
            assert "user" in variables
            assert "items" in variables
            # Note: item is not in undeclared variables as it's defined in the for loop

    def test_validate_context_all_defined(self):
        """Test context validation when all variables are defined."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "template.jinja2"
            template_path.write_text("{{ name }} - {{ value }}")

            env = Environment(loader=FileSystemLoader(tmpdir))
            validator = TemplateContextValidator(env)

            expected_vars = {"name", "value"}
            provided_context = {"name": "Test", "value": 42}

            is_valid, issues = validator.validate_context(
                "template.jinja2",
                expected_vars,
                provided_context,
            )
            assert is_valid
            assert len(issues) == 0

    def test_validate_context_undefined_variables(self):
        """Test context validation with undefined variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir) / "template.jinja2"
            template_path.write_text("{{ name }} - {{ value }} - {{ missing }}")

            env = Environment(loader=FileSystemLoader(tmpdir))
            validator = TemplateContextValidator(env)

            expected_vars = {"name", "value"}
            provided_context = {"name": "Test", "value": 42}

            is_valid, issues = validator.validate_context(
                "template.jinja2",
                expected_vars,
                provided_context,
            )
            assert not is_valid
            assert any("Undefined variables: missing" in issue for issue in issues)


class TestTemplateOutputValidator:
    """Test template output validation."""

    def test_validate_python_syntax_valid(self):
        """Test validation of valid Python code."""
        code = """
def hello(name):

    return f"Hello, {name}!"

class MyClass:
    def __init__(self):

        self.value = 42
        """
        is_valid, error = TemplateOutputValidator.validate_python_syntax(code)
        assert is_valid
        assert error is None

    def test_validate_python_syntax_invalid(self):
        """Test validation of invalid Python code."""
        code = """
def hello(name)  # Missing colon
    return f"Hello, {name}!"
"""
        is_valid, error = TemplateOutputValidator.validate_python_syntax(code)
        assert not is_valid
        assert "syntax error" in error.lower()

    def test_validate_dart_syntax_valid(self):
        """Test validation of valid Dart code."""
        code = """
class MyWidget extends StatelessWidget {
  final String name;

  MyWidget({required this.name});

  @override
  Widget build(BuildContext context) {
    return Text(name);
  }
}
"""
        is_valid, error = TemplateOutputValidator.validate_dart_syntax(code)
        assert is_valid
        assert error is None

    def test_validate_dart_syntax_unbalanced_braces(self):
        """Test validation of Dart code with unbalanced braces."""
        code = """
class MyWidget {
  void method() {
    if (true) {
      print("test");
    // Missing closing brace
  }
}
"""
        is_valid, error = TemplateOutputValidator.validate_dart_syntax(code)
        assert not is_valid
        assert "Unbalanced braces" in error


class TestTemplateConventionValidator:
    """Test template convention validation."""

    def test_validate_naming_valid(self):
        """Test validation of properly named template."""
        validator = TemplateConventionValidator(Path("/tmp"))

        is_valid, error = validator.validate_naming("my_template.jinja2")
        assert is_valid
        assert error is None

        is_valid, error = validator.validate_naming("model_generator.j2")
        assert is_valid
        assert error is None

    def test_validate_naming_invalid_extension(self):
        """Test validation of template with wrong extension."""
        validator = TemplateConventionValidator(Path("/tmp"))

        is_valid, error = validator.validate_naming("my_template.txt")
        assert not is_valid
        assert "should have .jinja2 extension" in error

    def test_validate_naming_invalid_pattern(self):
        """Test validation of template with invalid naming pattern."""
        validator = TemplateConventionValidator(Path("/tmp"))

        is_valid, error = validator.validate_naming("MyTemplate.jinja2")
        assert not is_valid
        assert "lowercase_underscore naming" in error

    def test_validate_structure_valid(self):
        """Test validation of template with proper structure."""
        content = """{# Template header comment #}
{% extends "base.jinja2" %}

{% block content %}
    <div>{{ content }}</div>
{% endblock %}
"""
        validator = TemplateConventionValidator(Path("/tmp"))
        is_valid, issues = validator.validate_structure(content)
        assert is_valid
        assert len(issues) == 0

    def test_validate_structure_missing_header(self):
        """Test validation of template without header comment."""
        content = """{% extends "base.jinja2" %}

{% block content %}
    <div>{{ content }}</div>
{% endblock %}
"""
        validator = TemplateConventionValidator(Path("/tmp"))
        is_valid, issues = validator.validate_structure(content)
        assert not is_valid
        assert any("header comment" in issue for issue in issues)

    def test_validate_structure_tabs(self):
        """Test validation of template with tabs."""
        content = """{# Header #}
\tindented with tab
    indented with spaces
"""
        validator = TemplateConventionValidator(Path("/tmp"))
        is_valid, issues = validator.validate_structure(content)
        assert not is_valid
        assert any("use spaces, not tabs" in issue for issue in issues)


class TestTemplateValidator:
    """Test main template validator."""

    def test_validate_template_comprehensive(self):
        """Test comprehensive template validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a Python template
            template_path = Path(tmpdir) / "model.py.jinja2"
            template_path.write_text("""{# Model template #}
class {{ class_name }}:
    def __init__(self, {{ params }}):

        self.value = {{ value }}
        """)

            validator = TemplateValidator(tmpdir)

            # Test with valid context
            result = validator.validate_template(
                "model.py.jinja2",
                expected_context={"class_name": str, "params": str, "value": int},
                sample_context={"class_name": "MyClass", "params": "name", "value": 42},
            )

            assert result["valid"]
            assert result["template"] == "model.py.jinja2"
            assert len(result["errors"]) == 0

    def test_validate_template_with_syntax_error(self):
        """Test validation of template with syntax error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create template with syntax error
            template_path = Path(tmpdir) / "bad.jinja2"
            template_path.write_text("""{# Bad template #}
{% for item in items
{{ item }}
{% endfor %}
""")

            validator = TemplateValidator(tmpdir)
            result = validator.validate_template("bad.jinja2")

            assert not result["valid"]
            assert any("Syntax" in error for error in result["errors"])

    def test_validate_all_templates(self):
        """Test validation of all templates in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple templates
            (Path(tmpdir) / "valid.jinja2").write_text("""{# Valid #}
{{ name }}
""")
            (Path(tmpdir) / "invalid.jinja2").write_text("""{# Invalid #}
{% for item in items
""")
            (Path(tmpdir) / "warning.jinja2").write_text("""Missing header
{{ value }}
""")

            validator = TemplateValidator(tmpdir)
            results = validator.validate_all_templates()

            assert len(results["valid"]) == 1
            assert len(results["invalid"]) == 1
            assert len(results["warnings"]) == 1

            # Check that the right templates are in each category
            valid_names = [r["template"] for r in results["valid"]]
            assert "valid.jinja2" in valid_names

            invalid_names = [r["template"] for r in results["invalid"]]
            assert "invalid.jinja2" in invalid_names
