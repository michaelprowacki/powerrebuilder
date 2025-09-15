"""Tests for custom type and enum handling in PowerBuilder parser."""

import pytest
from lark import Lark

from src.model.ast.nodes.base import VariableDeclaration
from src.model.ast.nodes.declarations import CustomType, TypeCategory
from src.parse.parser.specialized.types import EnumeratedType, StructureType, TypeParser


class TestCustomTypes:
    """Test custom type parsing."""

    @pytest.fixture
    def grammar(self):
        """Load test grammar with type extensions."""
        grammar_text = r"""
        ?start: type_declaration

        type_declaration: global_modifier? TYPE IDENTIFIER enumerated_modifier? from_clause? type_body END TYPE

        global_modifier: GLOBAL
        enumerated_modifier: ENUMERATED
        from_clause: FROM type_ref
        type_ref: IDENTIFIER (DOT IDENTIFIER)*

        type_body: _NL enum_body
                 | _NL structure_body
                 | _NL?          -> empty

        enum_body: enum_values
        structure_body: member_list

        enum_values: enum_value (COMMA _NL? enum_value)* COMMA?
        enum_value: IDENTIFIER (EQUALS INT)?

        member_list: member (_NL member)*
        member: visibility? type_name IDENTIFIER (EQUALS expression)?

        visibility: PUBLIC | PRIVATE | PROTECTED
        type_name: TYPE_KEYWORD | IDENTIFIER
        expression: INT | STRING

        // Tokens
        GLOBAL: "global"i
        TYPE: "type"i
        ENUMERATED: "enumerated"i
        FROM: "from"i
        END: "end"i
        PUBLIC: "public"i
        PRIVATE: "private"i
        PROTECTED: "protected"i
        TYPE_KEYWORD.2: /(string|integer|boolean|long|decimal|real|date|time|datetime)\b/i
        EQUALS: "="
        COMMA: ","
        DOT: "."

        IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
        INT: /[0-9]+/
        STRING: /"[^"]*"/

        _NL: /\r?\n/+

        %import common.WS
        %ignore WS
        """
        return Lark(grammar_text, parser="lalr")

    @pytest.fixture
    def transformer(self):
        """Create transformer instance with test-specific methods."""
        from lark import Transformer

        class TestTransformer(Transformer):
            def __init__(self):
                super().__init__()
                self.type_parser = TypeParser()

            def type_declaration(self, items):
                # Debug: print items to understand structure
                # print(f"\ntype_declaration items: {[repr(item) for item in items]}")
                # print(f"\nFinal body_content: {body_content}")

                # Parse items list
                is_global = False
                is_enumerated = False
                name = None
                parent_type = None
                body_content = {}

                # Items should contain: [global?], TYPE, IDENTIFIER, [enumerated?], [from_clause?], type_body, END, TYPE
                i = 0
                while i < len(items):
                    item = items[i]
                    if item == "global" or (
                        hasattr(item, "value") and str(item.value).lower() == "global"
                    ):
                        is_global = True
                    elif hasattr(item, "data") and str(item.data) == "global_modifier":
                        # It's a Tree object for global_modifier
                        is_global = True
                    elif str(item).lower() == "type" and name is None:
                        # Next item should be the identifier
                        if i + 1 < len(items):
                            name = str(items[i + 1])
                            i += 1  # Skip the identifier we just processed
                    elif str(item).lower() == "enumerated":
                        is_enumerated = True
                    elif (
                        hasattr(item, "data")
                        and str(item.data) == "enumerated_modifier"
                    ):
                        # It's a Tree object for enumerated_modifier
                        is_enumerated = True
                    elif isinstance(item, dict):
                        if item.get("type") == "from_clause":
                            parent_type = item.get("parent")
                        elif item.get("type") in [
                            "enum_body",
                            "structure_body",
                            "enum_values",
                            "member_list",
                            "empty",
                        ]:
                            body_content = item
                    elif hasattr(item, "data") and str(item.data) == "type_body":
                        # It's a Tree object for type_body, extract its content
                        if item.children and len(item.children) > 0:
                            child = item.children[0]
                            if isinstance(child, dict):
                                body_content = child
                    i += 1

                # print(f"\nFinal body_content before creating type: {body_content}")

                # Create appropriate type object
                if is_enumerated or body_content.get("type") in [
                    "enum_values",
                    "enum_body",
                ]:
                    values = body_content.get("values", {})
                    type_obj = EnumeratedType(name, values, parent_type)
                elif body_content.get("type") in ["member_list", "structure_body"]:
                    fields = body_content.get("fields", [])
                    type_obj = StructureType(name, fields, parent_type)
                else:
                    type_obj = CustomType(name=name, category=TypeCategory.CUSTOM)
                    if parent_type:
                        type_obj.parent_type = parent_type

                type_obj.is_global = is_global
                type_obj.is_enumerated = is_enumerated

                # Register and return
                self.type_parser.register_type(type_obj)
                return type_obj

            def from_clause(self, items):
                # items: [FROM, type_ref]
                if len(items) >= 2:
                    return {"type": "from_clause", "parent": items[1]}
                return {"type": "from_clause", "parent": None}

            def type_ref(self, items):
                return ".".join(str(item) for item in items if str(item) != ".")

            def empty(self, items):
                return {"type": "empty"}

            def enum_body(self, items):
                # items should contain enum_values directly
                if (
                    items
                    and isinstance(items[0], dict)
                    and items[0].get("type") == "enum_values"
                ):
                    return {"type": "enum_body", "values": items[0].get("values", {})}
                return {"type": "enum_body", "values": {}}

            def structure_body(self, items):
                # items should contain member_list directly
                if (
                    items
                    and isinstance(items[0], dict)
                    and items[0].get("type") == "member_list"
                ):
                    return {
                        "type": "structure_body",
                        "fields": items[0].get("fields", []),
                    }
                return {"type": "structure_body", "fields": []}

            def enum_values(self, items):
                # print(f"\nenum_values items: {items}")
                values = {}
                next_value = 0

                for item in items:
                    if isinstance(item, dict) and item.get("type") == "enum_value":
                        name = item["name"]
                        value = item.get("value")
                        if value is None:
                            value = next_value
                        values[name] = value
                        next_value = value + 1
                    elif str(item) != ",":
                        # Handle inline enum value
                        if isinstance(item, tuple):
                            name, value = item
                            values[name] = value
                            next_value = value + 1

                return {"type": "enum_values", "values": values}

            def enum_value(self, items):
                # items: IDENTIFIER [EQUALS INT]
                name = None
                value = None

                for item in items:
                    if (
                        hasattr(item, "type")
                        and item.type == "IDENTIFIER"
                        and name is None
                    ):
                        name = str(item)
                    elif hasattr(item, "type") and item.type == "INT":
                        value = int(item)
                    elif isinstance(item, str) and name is None:
                        name = item
                    elif isinstance(item, int):
                        value = item

                return {"type": "enum_value", "name": name, "value": value}

            def member_list(self, items):
                fields = []
                for item in items:
                    if isinstance(item, VariableDeclaration):
                        fields.append(item)
                return {"type": "member_list", "fields": fields}

            def member(self, items):
                visibility = "public"
                type_name = None
                name = None
                initial_value = None

                i = 0
                while i < len(items):
                    item = items[i]
                    if str(item).lower() in ["public", "private", "protected"]:
                        visibility = str(item).lower()
                    elif type_name is None:
                        type_name = str(item)
                    elif name is None:
                        name = str(item)
                    elif str(item) == "=" and i + 1 < len(items):
                        # Next item is the initial value
                        initial_value = items[i + 1]
                        i += 1  # Skip the value we just processed
                    i += 1

                decl = VariableDeclaration(
                    name=name, type=type_name, visibility=visibility
                )
                if initial_value is not None:
                    decl.initial_value = initial_value
                return decl

            def IDENTIFIER(self, token):
                return str(token)

            def INT(self, token):
                return int(token)

            def GLOBAL(self, token):
                return "global"

            def ENUMERATED(self, token):
                return "enumerated"

            def global_modifier(self, items):
                return "global"

            def enumerated_modifier(self, items):
                return "enumerated"

            def type_name(self, items):
                # Extract the actual type name from the items
                if items:
                    item = items[0]
                    if hasattr(item, "type"):
                        if item.type in ["IDENTIFIER", "TYPE_KEYWORD"]:
                            return str(item)
                    elif isinstance(item, str):
                        return item
                return "any"

            def TYPE_KEYWORD(self, token):
                return str(token)

        return TestTransformer()

    def test_simple_custom_type(self, grammar, transformer):
        """Test simple custom type declaration."""
        code = """
type my_type from powerobject
end type
""".strip()

        tree = grammar.parse(code)
        result = transformer.transform(tree)

        assert result.name == "my_type"
        assert result.parent_type == "powerobject"
        assert not result.is_global

    def test_global_custom_type(self, grammar, transformer):
        """Test global custom type."""
        code = """
global type my_global_type from datawindow
        end type
""".strip()

        tree = grammar.parse(code)
        result = transformer.transform(tree)

        assert result.name == "my_global_type"
        assert result.parent_type == "datawindow"
        assert result.is_global

    def test_enumerated_type(self, grammar, transformer):
        """Test enumerated type with values."""
        code = """
type colors enumerated
            red = 1,
            green = 2,
            blue = 3
        end type
""".strip()

        tree = grammar.parse(code)
        result = transformer.transform(tree)

        assert isinstance(result, EnumeratedType)
        assert result.name == "colors"
        assert result.is_enumerated
        assert result.values == {"red": 1, "green": 2, "blue": 3}
        assert result.get_value("red") == 1
        assert result.is_valid_value("green")
        assert not result.is_valid_value("yellow")

    def test_enumerated_type_auto_values(self, grammar, transformer):
        """Test enumerated type with automatic values."""
        code = """
type status enumerated
            pending,
            active = 10,
            completed,
            cancelled
        end type
""".strip()

        tree = grammar.parse(code)
        result = transformer.transform(tree)

        assert isinstance(result, EnumeratedType)
        assert result.values == {
            "pending": 0,
            "active": 10,
            "completed": 11,
            "cancelled": 12,
        }

    def test_structure_type(self, grammar, transformer):
        """Test structure type with fields."""
        code = """
type person_info from structure
            string first_name
            string last_name
            integer age
            private string ssn
        end type
""".strip()

        tree = grammar.parse(code)
        result = transformer.transform(tree)

        assert isinstance(result, StructureType)
        assert result.name == "person_info"
        assert result.parent_type == "structure"
        assert len(result.fields) == 4

        # Check fields
        first_name = result.get_field("first_name")
        assert first_name is not None
        assert first_name.type == "string"
        assert first_name.visibility == "public"

        ssn = result.get_field("ssn")
        assert ssn is not None
        assert ssn.type == "string"
        assert ssn.visibility == "private"

        assert result.has_field("age")
        assert not result.has_field("middle_name")

    def test_structure_with_initial_values(self, grammar, transformer):
        """Test structure with field initial values."""
        code = """
type config from structure
            string app_name = "MyApp"
            integer max_users = 100
            boolean debug_mode
        end type
""".strip()

        tree = grammar.parse(code)
        result = transformer.transform(tree)

        assert isinstance(result, StructureType)
        assert len(result.fields) == 3

        # Check field with initial value
        app_name = result.get_field("app_name")
        assert app_name is not None
        assert app_name.type == "string"
        # Note: Initial values would need expression evaluation

    def test_qualified_parent_type(self, grammar, transformer):
        """Test custom type with qualified parent."""
        code = """
type my_window from pfc.w_master
        end type
""".strip()

        tree = grammar.parse(code)
        result = transformer.transform(tree)

        assert result.name == "my_window"
        assert result.parent_type == "pfc.w_master"

    def test_type_registry(self, transformer):
        """Test type registration and lookup."""
        # Create some types
        enum_type = EnumeratedType("status", {"active": 1, "inactive": 0})
        struct_type = StructureType("point", [])

        # Register them
        transformer.type_parser.register_type(enum_type)
        transformer.type_parser.register_type(struct_type)

        # Look them up
        found_enum = transformer.type_parser.get_type("status")
        assert found_enum is not None
        assert isinstance(found_enum, EnumeratedType)
        assert found_enum.name == "status"

        found_struct = transformer.type_parser.get_type("point")
        assert found_struct is not None
        assert isinstance(found_struct, StructureType)
        assert found_struct.name == "point"

        # Non-existent type
        not_found = transformer.type_parser.get_type("unknown")
        assert not_found is None
