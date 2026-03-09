"""Code Generation Templates - Template management and rendering.

This module manages code generation templates for different target languages.
Uses simple string templates for maintainability.
"""

from typing import Any, Dict

# ============================================================================
# FLUTTER TEMPLATES
# ============================================================================

FLUTTER_TEMPLATES = {
    "flutter/screen.dart": """import 'package:flutter/material.dart';

class {{ class_name }}Screen extends StatefulWidget {
  const {{ class_name }}Screen({Key? key}) : super(key: key);

  @override
  State<{{ class_name }}Screen> createState() => _{{ class_name }}ScreenState();
}

class _{{ class_name }}ScreenState extends State<{{ class_name }}Screen> {
  {% for property in properties %}
  {{ property.type }} {{ property.name }};
  {% endfor %}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('{{ title }}'),
      ),
      body: Container(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Add your widgets here
          ],
        ),
      ),
    );
  }

  {% for method in methods %}
  {{ method.return_type or 'void' }} {{ method.name }}() {
    // TODO: Implement
  }
  {% endfor %}
}
""",
    "flutter/model.dart": """import 'package:json_annotation/json_annotation.dart';

part '{{ class_name.lower() }}.g.dart';

@JsonSerializable()
class {{ class_name }} {
  {% for property in properties %}
  final {{ _dart_type(property.type) }} {{ property.name }};
  {% endfor %}

  {{ class_name }}({
    {% for property in properties %}
    required this.{{ property.name }},
    {% endfor %}
  });

  factory {{ class_name }}.fromJson(Map<String, dynamic> json) =>
    _${{ class_name }}FromJson(json);

  Map<String, dynamic> toJson() => _${{ class_name }}ToJson(this);
}
""",
    "flutter/data_grid.dart": """import 'package:flutter/material.dart';
import 'package:syncfusion_flutter_datagrid/datagrid.dart';

class {{ class_name }}Grid extends StatelessWidget {
  final List<Map<String, dynamic>> data;

  const {{ class_name }}Grid({Key? key, required this.data}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SfDataGrid(
      source: {{ class_name }}DataSource(data: data),
      columns: [
        {% for column in columns %}
        GridColumn(
          columnName: '{{ column.name }}',
          label: Container(
            alignment: Alignment.center,
            child: Text('{{ column.label }}'),
          ),
        ),
        {% endfor %}
      ],
    );
  }
}

class {{ class_name }}DataSource extends DataGridSource {
  final List<Map<String, dynamic>> data;

  {{ class_name }}DataSource({required this.data});

  @override
  List<DataGridRow> get rows => data.map((item) =>
    DataGridRow(cells: [
      {% for column in columns %}
      DataGridCell(columnName: '{{ column.name }}', value: item['{{ column.name }}']),
      {% endfor %}
    ])
  ).toList();

  @override
  DataGridRowAdapter? buildRow(DataGridRow row) {
    return DataGridRowAdapter(cells: row.getCells());
  }
}
""",
    "flutter/main.dart": """import 'package:flutter/material.dart';
{% for screen in screens %}
import 'screens/{{ screen.name }}.dart';
{% endfor %}

void main() {
  runApp(const {{ app_name }}App());
}

class {{ app_name }}App extends StatelessWidget {
  const {{ app_name }}App({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '{{ app_name }}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('{{ app_name }}')),
      body: ListView(
        children: [
          {% for screen in screens %}
          ListTile(
            title: Text('{{ screen.name }}'),
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const {{ screen.name }}Screen()),
            ),
          ),
          {% endfor %}
        ],
      ),
    );
  }
}
""",
    "flutter/pubspec.yaml": """name: {{ name }}
description: Generated from PowerBuilder
version: {{ version }}

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  {% for dep, version in dependencies.items() %}
  {{ dep }}: {{ version }}
  {% endfor %}

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.3.0
  json_serializable: ^6.0.0
""",
}

# ============================================================================
# PYTHON TEMPLATES
# ============================================================================

PYTHON_TEMPLATES = {
    "python/class.py": """\"\"\"{{ class_name }} - Generated from PowerBuilder.\"\"\"

{% if parent %}
from .{{ parent.lower() }} import {{ parent }}
{% endif %}


class {{ class_name }}{% if parent %}({{ parent }}){% endif %}:
    \"\"\"{{ class_name }} class.\"\"\"

    def __init__(self):
        \"\"\"Initialize {{ class_name }}.\"\"\"
        {% if parent %}
        super().__init__()
        {% endif %}

        {% for property in properties %}
        self.{{ property.name }}: {{ _python_type(property.type) }} = {{ property.default_value or 'None' }}
        {% endfor %}

    {% for method in methods %}
    def {{ method.name }}(self{% for param in method.parameters %}, {{ param.name }}: {{ _python_type(param.type) }}{% endfor %}) -> {{ _python_type(method.return_type) if method.return_type else 'None' }}:
        \"\"\"{{ method.name }} method.\"\"\"
        # TODO: Implement
        pass

    {% endfor %}
""",
    "python/model.py": """\"\"\"{{ class_name }} Model - Generated from PowerBuilder DataWindow.\"\"\"

from typing import Optional
from sqlmodel import Field, SQLModel


class {{ class_name }}(SQLModel, table=True):
    \"\"\"{{ class_name }} database model.\"\"\"

    __tablename__ = "{{ table_name }}"

    {% for property in properties %}
    {{ property.name }}: {{ _python_type(property.type) }} = Field(
        {% if property.is_required %}
        ...,
        {% else %}
        default={{ property.default_value or 'None' }},
        {% endif %}
        description="{{ property.name }}"
    )
    {% endfor %}
""",
    "python/repository.py": """\"\"\"Repository for {{ model_name }}.\"\"\"

from typing import List, Optional
from sqlmodel import Session, select

from {{ model_import }} import {{ model_name }}


class {{ model_name }}Repository:
    \"\"\"Repository for {{ model_name }} operations.\"\"\"

    def __init__(self, session: Session):
        \"\"\"Initialize repository.

        Args:
            session: Database session
        \"\"\"
        self.session = session

    def get_all(self) -> List[{{ model_name }}]:
        \"\"\"Get all records.

        Returns:
            List of {{ model_name }} records
        \"\"\"
        statement = select({{ model_name }})
        return self.session.exec(statement).all()

    def get_by_id(self, id: int) -> Optional[{{ model_name }}]:
        \"\"\"Get record by ID.

        Args:
            id: Record ID

        Returns:
            {{ model_name }} record or None
        \"\"\"
        return self.session.get({{ model_name }}, id)

    def create(self, item: {{ model_name }}) -> {{ model_name }}:
        \"\"\"Create new record.

        Args:
            item: {{ model_name }} to create

        Returns:
            Created {{ model_name }}
        \"\"\"
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def update(self, item: {{ model_name }}) -> {{ model_name }}:
        \"\"\"Update record.

        Args:
            item: {{ model_name }} to update

        Returns:
            Updated {{ model_name }}
        \"\"\"
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(self, id: int) -> bool:
        \"\"\"Delete record.

        Args:
            id: Record ID to delete

        Returns:
            True if deleted
        \"\"\"
        item = self.get_by_id(id)
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False
""",
    "python/main.py": """\"\"\"Main application entry point.\"\"\"

import uvicorn
from litestar import Litestar, get

from models import *


@get("/")
async def index() -> dict:
    \"\"\"Root endpoint.\"\"\"
    return {"app": "{{ app_name }}", "status": "running"}


app = Litestar(
    route_handlers=[index],
    debug=True,
)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
""",
    "python/pyproject.toml": """[project]
name = "{{ name }}"
version = "{{ version }}"
description = "Generated from PowerBuilder"
dependencies = [
    {% for dep in dependencies %}
    "{{ dep }}",
    {% endfor %}
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"
""",
}

# ============================================================================
# TEMPLATE RENDERING
# ============================================================================

# Combine all templates
ALL_TEMPLATES = {
    **FLUTTER_TEMPLATES,
    **PYTHON_TEMPLATES,
}


def get_template(name: str) -> str:
    """Get a template by name.

    Args:
        name: Template name

    Returns:
        Template string
    """
    return ALL_TEMPLATES.get(name, "")


def render_template(name: str, context: Dict[str, Any]) -> str:
    """Render a template with context.

    Args:
        name: Template name
        context: Template variables

    Returns:
        Rendered template
    """
    template = get_template(name)

    if not template:
        return f"// Template not found: {name}"

    # Simple template rendering (real implementation would use Jinja2)
    # For now, just do basic string replacement
    result = template

    # Replace variables
    for key, value in context.items():
        result = result.replace(f"{{{{ {key} }}}}", str(value))

    # Handle loops (simplified)
    import re

    # Handle for loops
    for_pattern = r"{{% for (\w+) in (\w+) %}}"
    for_matches = re.findall(for_pattern, result)
    for var, collection in for_matches:
        if collection in context:
            items = context[collection]
            # This is simplified - real implementation would be more complex
            pass

    # Remove template tags for now
    result = re.sub(r"{%.*?%}", "", result)
    result = re.sub(r"{{.*?}}", "", result)

    return result


def _dart_type(python_type: str) -> str:
    """Convert Python type to Dart type.

    Args:
        python_type: Python type name

    Returns:
        Dart type name
    """
    type_map = {
        "int": "int",
        "integer": "int",
        "long": "int",
        "float": "double",
        "double": "double",
        "decimal": "double",
        "string": "String",
        "str": "String",
        "bool": "bool",
        "boolean": "bool",
        "date": "DateTime",
        "datetime": "DateTime",
        "time": "DateTime",
        "any": "dynamic",
    }
    return type_map.get(python_type.lower(), "dynamic")


def _python_type(pb_type: str) -> str:
    """Convert PowerBuilder type to Python type.

    Args:
        pb_type: PowerBuilder type name

    Returns:
        Python type name
    """
    type_map = {
        "integer": "int",
        "long": "int",
        "decimal": "float",
        "real": "float",
        "double": "float",
        "string": "str",
        "boolean": "bool",
        "date": "datetime",
        "time": "time",
        "datetime": "datetime",
        "any": "Any",
    }
    return type_map.get(pb_type.lower() if pb_type else "", "Any")
