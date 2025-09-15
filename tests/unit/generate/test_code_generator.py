"""Tests for the code generation module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import GenerateError
from src.generate.coordinator import (
    CodeGenerator,
    FlutterGenerator,
    ModelGenerator,
    ServiceGenerator,
    generate_flutter,
    generate_models,
    generate_services,
)


class TestCodeGenerator:
    """Test the base CodeGenerator class."""

    def test_init(self):
        """Test CodeGenerator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = CodeGenerator("templates", tmpdir)
            assert generator.template_dir == Path("templates")
            assert generator.output_dir == Path(tmpdir)
            assert generator.env is not None

    def test_render_template_success(self):
        """Test successful template rendering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test template
            template_dir = Path(tmpdir) / "templates"
            template_dir.mkdir()
            template_file = template_dir / "test.jinja2"
            template_file.write_text("Hello {{ name }}!")

            generator = CodeGenerator(str(template_dir), tmpdir)
            result = generator.render_template("test.jinja2", {"name": "World"})
            assert result == "Hello World!"

    def test_render_template_missing(self):
        """Test rendering missing template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = CodeGenerator(tmpdir, tmpdir)
            with pytest.raises(GenerateError) as exc_info:
                generator.render_template("missing.jinja2", {})
            assert "Failed to render template missing.jinja2" in str(exc_info.value)

    def test_write_file_success(self):
        """Test successful file writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = CodeGenerator("templates", tmpdir)
            generator.write_file("test/file.py", "print('hello')")

            written_file = Path(tmpdir) / "test" / "file.py"
            assert written_file.exists()
            assert written_file.read_text() == "print('hello')"

    def test_write_file_creates_directories(self):
        """Test file writing creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = CodeGenerator("templates", tmpdir)
            generator.write_file("deep/nested/path/file.py", "content")

            written_file = Path(tmpdir) / "deep" / "nested" / "path" / "file.py"
            assert written_file.exists()
            assert written_file.read_text() == "content"

    def test_write_file_error(self):
        """Test file writing error handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = CodeGenerator("templates", tmpdir)
            # Try to write to a path that's actually a file
            bad_path = Path(tmpdir) / "existing_file"
            bad_path.write_text("exists")

            with pytest.raises(GenerateError) as exc_info:
                generator.write_file("existing_file/subdir/file.py", "content")
            assert "Failed to write file" in str(exc_info.value)


class TestModelGenerator:
    """Test the ModelGenerator class."""

    def test_init(self):
        """Test ModelGenerator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ModelGenerator("templates", tmpdir)
            assert isinstance(generator, CodeGenerator)
            assert generator.template_dir == Path("templates")

    @patch.object(ModelGenerator, "render_template")
    @patch.object(ModelGenerator, "write_file")
    def test_generate_model(self, mock_write, mock_render):
        """Test model generation."""
        mock_render.return_value = "model content"

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ModelGenerator("templates", tmpdir)

            columns = [
                {"name": "id", "type": "Integer"},
                {"name": "name", "type": "String"},
            ]
            relationships = [
                {"name": "orders", "type": "one-to-many"},
            ]

            generator.generate_model("User", columns, relationships)

            mock_render.assert_called_once_with(
                "sqlmodel_model.jinja2",
                {
                    "table_name": "User",
                    "columns": columns,
                    "relationships": relationships,
                },
            )
            mock_write.assert_called_once_with("models/user.py", "model content")

    @patch.object(ModelGenerator, "render_template")
    @patch.object(ModelGenerator, "write_file")
    def test_generate_model_no_relationships(self, mock_write, mock_render):
        """Test model generation without relationships."""
        mock_render.return_value = "model content"

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ModelGenerator("templates", tmpdir)

            columns = [{"name": "id", "type": "Integer"}]
            generator.generate_model("Simple", columns)

            mock_render.assert_called_once()
            args = mock_render.call_args[0]
            context = args[1]
            assert context["relationships"] == []


class TestServiceGenerator:
    """Test the ServiceGenerator class."""

    def test_init(self):
        """Test ServiceGenerator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ServiceGenerator("templates", tmpdir)
            assert isinstance(generator, CodeGenerator)

    @patch.object(ServiceGenerator, "render_template")
    @patch.object(ServiceGenerator, "write_file")
    def test_generate_service(self, mock_write, mock_render):
        """Test service generation."""
        mock_render.return_value = "service content"

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ServiceGenerator("templates", tmpdir)

            methods = [
                {"name": "get_user", "params": ["id"]},
                {"name": "create_user", "params": ["data"]},
            ]

            generator.generate_service("UserService", methods)

            mock_render.assert_called_once_with(
                "service.jinja2",
                {
                    "service_name": "UserService",
                    "methods": methods,
                },
            )
            mock_write.assert_called_once_with(
                "services/userservice_service.py",
                "service content",
            )


class TestFlutterGenerator:
    """Test the FlutterGenerator class."""

    def test_init_default_framework(self):
        """Test FlutterGenerator initialization with default framework."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = FlutterGenerator("templates", tmpdir)
            assert generator.framework == "react"

    def test_init_custom_framework(self):
        """Test FlutterGenerator initialization with custom framework."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = FlutterGenerator("templates", tmpdir, "astro")
            assert generator.framework == "astro"

    @patch.object(FlutterGenerator, "render_template")
    @patch.object(FlutterGenerator, "write_file")
    def test_generate_component_react(self, mock_write, mock_render):
        """Test React component generation."""
        mock_render.return_value = "component content"

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = FlutterGenerator("templates", tmpdir, "react")

            props = [
                {"name": "title", "type": "string"},
                {"name": "onClick", "type": "function"},
            ]
            children = [
                {"name": "Button", "props": {"label": "Click me"}},
            ]

            generator.generate_component("Card", props, children)

            mock_render.assert_called_once_with(
                "react_component.jinja2",
                {
                    "component_name": "Card",
                    "props": props,
                    "children": children,
                },
            )
            mock_write.assert_called_once_with(
                "components/card.tsx",
                "component content",
            )

    @patch.object(FlutterGenerator, "render_template")
    @patch.object(FlutterGenerator, "write_file")
    def test_generate_component_astro(self, mock_write, mock_render):
        """Test Astro component generation."""
        mock_render.return_value = "component content"

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = FlutterGenerator("templates", tmpdir, "astro")

            props = [{"name": "title", "type": "string"}]
            generator.generate_component("Header", props)

            mock_render.assert_called_once()
            mock_write.assert_called_once_with(
                "components/header.astro",
                "component content",
            )


class TestGeneratorFunctions:
    """Test the main generator functions."""

    @patch("generate.code_generator.ModelGenerator")
    def test_generate_models_empty(self, mock_generator_class):
        """Test generate_models with empty schema."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        generate_models()

        mock_generator_class.assert_called_once_with("templates", "output/backend")
        # Should not call generate_model since tables list is empty

    @patch("generate.code_generator.ModelGenerator")
    @patch("generate.code_generator.logger")
    def test_generate_models_error(self, mock_logger, mock_generator_class):
        """Test generate_models error handling."""
        mock_generator_class.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            generate_models()

        mock_logger.error.assert_called_once()

    @patch("generate.code_generator.ServiceGenerator")
    def test_generate_services_empty(self, mock_generator_class):
        """Test generate_services with empty services."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        generate_services()

        mock_generator_class.assert_called_once_with("templates", "output/backend")

    @patch("generate.code_generator.ServiceGenerator")
    @patch("generate.code_generator.logger")
    def test_generate_services_error(self, mock_logger, mock_generator_class):
        """Test generate_services error handling."""
        mock_generator_class.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            generate_services()

        mock_logger.error.assert_called_once()

    @patch("generate.code_generator.FlutterGenerator")
    def test_generate_flutter_empty(self, mock_generator_class):
        """Test generate_flutter with empty components."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        generate_flutter()

        mock_generator_class.assert_called_once_with("templates", "output/frontend")

    @patch("generate.code_generator.FlutterGenerator")
    @patch("generate.code_generator.logger")
    def test_generate_flutter_error(self, mock_logger, mock_generator_class):
        """Test generate_flutter error handling."""
        mock_generator_class.side_effect = Exception("Test error")

        with pytest.raises(Exception):
            generate_flutter()

        mock_logger.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
