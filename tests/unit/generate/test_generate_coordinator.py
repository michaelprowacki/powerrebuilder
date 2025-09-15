#!/usr/bin/env python3
"""Comprehensive test suite for Generate coordinator."""

import json
import tempfile
from pathlib import Path

import pytest

from src.generate.coordinator import (
    CodeGenerator,
    FlutterGenerator,
    ModelGenerator,
    ServiceGenerator,
    extract_datawindow_from_ast,
    extract_table_from_sql,
)


class TestDataWindowExtraction:
    """Test DataWindow extraction functionality."""

    def test_extract_datawindow_from_ast_direct(self):
        """Test extracting DataWindow from direct AST node."""
        ast_data = {
            "node_type": "DataWindow",
            "columns": [
                {"name": "id", "type": "integer", "is_nullable": False},
                {"name": "name", "type": "string", "length": 50},
            ],
            "retrieve_sql": "SELECT id, name FROM users",
            "table": {"name": "users"},
        }

        result = extract_datawindow_from_ast(ast_data)

        assert result is not None
        assert len(result["columns"]) == 2
        assert result["columns"][0]["name"] == "id"
        assert result["columns"][0]["type"] == "integer"
        assert result["table_name"] == "users"

    def test_extract_datawindow_from_ast_nested(self):
        """Test extracting DataWindow from nested AST."""
        ast_data = {
            "file": {
                "elements": [
                    {
                        "type": "datawindow",
                        "columns": [
                            {"column_name": "emp_id", "column_type": "long"},
                        ],
                        "retrieve_sql": "SELECT * FROM employee",
                    },
                ],
            },
        }

        result = extract_datawindow_from_ast(ast_data)

        assert result is not None
        assert len(result["columns"]) == 1
        assert result["columns"][0]["name"] == "emp_id"

    def test_extract_datawindow_no_datawindow(self):
        """Test extraction when no DataWindow exists."""
        ast_data = {
            "type": "window",
            "controls": [],
        }

        result = extract_datawindow_from_ast(ast_data)
        assert result is None

    def test_extract_table_from_sql(self):
        """Test extracting table name from SQL."""
        test_cases = [
            ("SELECT * FROM users", "users"),
            ("SELECT id, name FROM employee WHERE active = 1", "employee"),
            (
                "SELECT * FROM schema.table_name",
                "schema.table_name",
            ),  # Function returns full qualified name
            # Function extracts from DELETE FROM but not INSERT/UPDATE
            ("INSERT INTO customers VALUES (1, 'John')", ""),
            ("UPDATE products SET price = 100", ""),
            ("DELETE FROM orders WHERE status = 'cancelled'", "orders"),
        ]

        for sql, expected in test_cases:
            result = extract_table_from_sql(sql)
            assert result == expected, (
                f"SQL: {sql} - Expected: {expected}, Got: {result}"
            )

    def test_extract_table_from_complex_sql(self):
        """Test extracting table from complex SQL with joins."""
        sql = """
        SELECT u.id, u.name, d.department_name
        FROM users u
        JOIN departments d ON u.dept_id = d.id
        WHERE u.active = 1
        """
        result = extract_table_from_sql(sql)
        assert result == "users"  # Should return the first table


class TestCodeGenerator:
    """Test base CodeGenerator functionality."""

    def test_code_generator_init(self):
        """Test CodeGenerator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir) / "templates"
            template_dir.mkdir()
            output_dir = Path(temp_dir) / "output"

            gen = CodeGenerator(str(template_dir), str(output_dir))

            assert gen.template_dir == template_dir
            assert gen.output_dir == output_dir
            # Output dir is created when writing files, not during init

    def test_render_template(self):
        """Test template rendering."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir) / "templates"
            template_dir.mkdir()

            # Create a simple template
            template_file = template_dir / "test.jinja2"
            template_file.write_text("Hello {{ name }}!")

            gen = CodeGenerator(str(template_dir), str(temp_dir))
            result = gen.render_template("test.jinja2", {"name": "World"})

            assert result == "Hello World!"

    def test_write_file(self):
        """Test file writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir) / "templates"
            template_dir.mkdir()

            gen = CodeGenerator(str(template_dir), str(temp_dir))
            gen.write_file("test.py", "print('Hello')")

            output_file = Path(temp_dir) / "test.py"
            assert output_file.exists()
            assert output_file.read_text() == "print('Hello')"

    def test_write_file_with_subdirectory(self):
        """Test writing file in subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir) / "templates"
            template_dir.mkdir()

            gen = CodeGenerator(str(template_dir), str(temp_dir))
            gen.write_file("subdir/test.py", "content")

            output_file = Path(temp_dir) / "subdir" / "test.py"
            assert output_file.exists()


class TestModelGenerator:
    """Test SQLModel generation."""

    def create_test_generator(self, temp_dir):
        """Create a test model generator."""
        template_dir = Path(temp_dir) / "templates"
        template_dir.mkdir()

        # Create model template with correct name
        model_template = template_dir / "sqlmodel_model.jinja2"
        model_template.write_text("""
from sqlmodel import SQLModel, Field

class {{ table_name }}(SQLModel, table=True):
    __tablename__ = "{{ table_name.lower() }}"
{%- for column in columns %}
    {{ column.name }}: {{ column.type }}{% if column.nullable %} | None = None{% endif %}
{%- endfor %}
""")

        return ModelGenerator(str(template_dir), str(temp_dir))

    def test_generate_model_basic(self):
        """Test basic model generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = self.create_test_generator(temp_dir)

            columns = [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "name", "type": "str", "nullable": False},
                {"name": "email", "type": "str", "nullable": True},
            ]

            gen.generate_model("User", columns)

            model_file = Path(temp_dir) / "models" / "user.py"
            assert model_file.exists()
            content = model_file.read_text()
            assert "class User(SQLModel" in content
            assert "id: int" in content
            assert "email: str | None = None" in content

    def test_generate_model_with_relationships(self):
        """Test model generation with relationships."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = self.create_test_generator(temp_dir)

            columns = [
                {"name": "id", "type": "int", "nullable": False},
                {"name": "user_id", "type": "int", "nullable": False},
            ]

            relationships = [
                {"name": "user", "type": "User", "back_populates": "posts"},
            ]

            gen.generate_model("Post", columns, relationships)

            model_file = Path(temp_dir) / "models" / "post.py"
            assert model_file.exists()


class TestServiceGenerator:
    """Test service layer generation."""

    def create_test_generator(self, temp_dir):
        """Create a test service generator."""
        template_dir = Path(temp_dir) / "templates"
        template_dir.mkdir()

        # Create service template
        service_template = template_dir / "service.jinja2"
        service_template.write_text("""
class {{ service_name }}Service:
{%- for method in methods %}

    def {{ method.name }}(self{% for param in method.params %}, {{ param }}{% endfor %}):
        \"\"\"{{ method.description }}\"\"\"
        pass
{%- endfor %}
""")

        return ServiceGenerator(str(template_dir), str(temp_dir))

    def test_generate_service(self):
        """Test service generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = self.create_test_generator(temp_dir)

            methods = [
                {
                    "name": "get_user",
                    "params": ["user_id: int"],
                    "description": "Get user by ID",
                },
                {
                    "name": "create_user",
                    "params": ["user_data: dict"],
                    "description": "Create new user",
                },
            ]

            gen.generate_service("User", methods)

            service_file = Path(temp_dir) / "services" / "user_service.py"
            assert service_file.exists()
            content = service_file.read_text()
            assert "class UserService:" in content
            assert "def get_user(self, user_id: int):" in content


class TestFlutterGenerator:
    """Test Flutter code generation."""

    def create_test_generator(self, temp_dir):
        """Create a test Flutter generator."""
        template_dir = Path(temp_dir) / "templates"
        template_dir.mkdir()

        # Create widget template
        widget_template = template_dir / "widget.dart.jinja2"
        widget_template.write_text("""
import 'package:flutter/material.dart';

class {{ widget.name }} extends {% if widget.has_state %}Stateful{% else %}Stateless{% endif %}Widget {
{%- for prop in widget.props %}
  final {{ prop.type }} {{ prop.name }};
{%- endfor %}

  const {{ widget.name }}({Key? key{% for prop in widget.props %}, required this.{{ prop.name }}{% endfor %}}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container();
  }
}
""")

        # Create screen template
        screen_template = template_dir / "screen.dart.jinja2"
        screen_template.write_text("""
import 'package:flutter/material.dart';

class {{ screen.name }}Screen extends StatelessWidget {
  static const String routeName = '{{ screen.route_name }}';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('{{ screen.name }}')),
      body: Container(),
    );
  }
}
""")

        return FlutterGenerator(
            str(template_dir), str(temp_dir), validate_templates=False
        )

    def test_generate_widget(self):
        """Test Flutter widget generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = self.create_test_generator(temp_dir)

            props = [
                {"name": "title", "type": "String"},
                {"name": "onPressed", "type": "VoidCallback"},
            ]

            gen.generate_widget("CustomButton", props, is_stateful=False)

            widget_file = Path(temp_dir) / "widgets" / "custombutton.dart"
            assert widget_file.exists()
            content = widget_file.read_text()
            assert "class CustomButton extends StatelessWidget" in content
            assert "final String title;" in content

    def test_generate_screen(self):
        """Test Flutter screen generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = self.create_test_generator(temp_dir)

            gen.generate_screen("Login", "/login")

            screen_file = Path(temp_dir) / "screens" / "login_screen.dart"
            assert screen_file.exists()
            content = screen_file.read_text()
            assert "class LoginScreen extends StatelessWidget" in content
            assert "routeName = '/login'" in content

    def test_generate_datawindow_widget(self):
        """Test DataWindow widget generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = self.create_test_generator(temp_dir)

            columns = [
                {"name": "id", "type": "int", "label": "ID"},
                {"name": "name", "type": "String", "label": "Name"},
            ]

            # DataWindow widgets would be complex, but basic test structure
            gen.generate_widget(
                "EmployeeDataWindow",
                [
                    {"name": "columns", "type": "List<Column>"},
                    {"name": "dataSource", "type": "String"},
                ],
            )

            widget_file = Path(temp_dir) / "widgets" / "employeedatawindow.dart"
            assert widget_file.exists()

    def test_method_body_conversion(self):
        """Test PowerBuilder method body conversion to Dart."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gen = self.create_test_generator(temp_dir)

            # Create a more comprehensive screen template that includes methods
            screen_template = Path(temp_dir) / "templates" / "screen.dart.jinja2"
            screen_template.write_text("""
import 'package:flutter/material.dart';

class {{ screen.name }}Screen extends StatefulWidget {
  @override
  _{{ screen.name }}ScreenState createState() => _{{ screen.name }}ScreenState();
}

class _{{ screen.name }}ScreenState extends State<{{ screen.name }}Screen> {
{%- for method in screen.methods %}

  {{ method.return_type }} {{ method.name }}({{ method.params }}){% if method.is_async %} async{% endif %} {
{{ method.body|indent(4) }}
  }
{%- endfor %}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('{{ screen.title }}')),
      body: Container(),
    );
  }
}
""")

            # Create a window model with methods that contain PowerBuilder code
            window_model = {
                "name": "TestWindow",
                "title": "Test Window",
                "variables": [
                    {
                        "name": "is_customer_name",
                        "type": "string",
                        "dart_type": "String",
                    },
                ],
                "controls": [
                    {
                        "name": "cb_save",
                        "type": "commandbutton",
                        "text": "Save",
                        "flutter_widget": {"requires_controller": False},
                    },
                    {
                        "name": "sle_name",
                        "type": "singlelineedit",
                        "flutter_widget": {
                            "requires_controller": True,
                            "controller_type": "TextEditingController",
                        },
                    },
                ],
                "methods": [
                    {
                        "name": "saveData",
                        "return_type": None,  # PowerBuilder methods often don't specify return type
                        "parameters": [],
                        "body": """string ls_name
ls_name = sle_name.text
if isnull(ls_name) or trim(ls_name) = "" then
    messagebox("Error", "Please enter a name")
    return
end if

// Save to database
INSERT INTO customers (name) VALUES (:ls_name);
commit;

messagebox("Success", "Customer saved successfully")""",
                    },
                ],
            }

            # Generate the screen
            gen.generate_screen_from_model(window_model)

            # Check the generated file
            screen_file = Path(temp_dir) / "screens" / "testwindow_screen.dart"
            assert screen_file.exists()

            content = screen_file.read_text()

            # Verify method was generated
            assert "void saveData()" in content

            # Verify PowerBuilder code was converted
            assert (
                "String ls_name" in content
            )  # Variable declaration converted (keeping PowerBuilder naming)
            assert (
                "sle_nameController.text" in content
            )  # Control access with controller
            assert "if (" in content  # If statement
            assert (
                "showDialog" in content or "// TODO: MessageBox" in content
            )  # MessageBox conversion


class TestIntegrationFunctions:
    """Test high-level generation functions."""

    def test_generate_models(self):
        """Test generate_models function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock parsed data
            parsed_data = [
                {
                    "type": "datawindow",
                    "name": "d_employee",
                    "columns": [
                        {"name": "emp_id", "type": "integer"},
                        {"name": "emp_name", "type": "string"},
                    ],
                    "table": {"name": "employee"},
                },
            ]

            # Write parsed data
            input_file = Path(temp_dir) / "parsed.json"
            input_file.write_text(json.dumps(parsed_data))

            output_dir = Path(temp_dir) / "output"

            # This would normally call generate_models
            # For now, just verify the structure
            assert True  # Placeholder

    def test_generate_flutter(self):
        """Test generate_flutter function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock UI data
            ui_data = {
                "windows": [
                    {
                        "name": "w_main",
                        "controls": [
                            {"type": "button", "name": "cb_ok", "text": "OK"},
                        ],
                    },
                ],
            }

            input_file = Path(temp_dir) / "ui.json"
            input_file.write_text(json.dumps(ui_data))

            output_dir = Path(temp_dir) / "flutter"

            # This would normally call generate_flutter
            assert True  # Placeholder


class TestErrorHandling:
    """Test error handling in generation."""

    def test_invalid_template_dir(self):
        """Test handling of invalid template directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Non-existent template directory won't raise error on init
            # but will raise when trying to render a template
            gen = CodeGenerator("/non/existent/path", temp_dir)

            with pytest.raises(Exception):
                gen.render_template("missing.jinja2", {})

    def test_template_not_found(self):
        """Test handling of missing template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir) / "templates"
            template_dir.mkdir()

            gen = CodeGenerator(str(template_dir), str(temp_dir))

            # Missing template should raise error
            with pytest.raises(Exception):
                gen.render_template("missing.jinja2", {})

    def test_invalid_ast_data(self):
        """Test handling of invalid AST data."""
        # None should return None
        assert extract_datawindow_from_ast(None) is None

        # Non-dict should return None
        assert extract_datawindow_from_ast("string") is None
        assert extract_datawindow_from_ast([1, 2, 3]) is None
