"""Comprehensive tests for core model functionality.

This file consolidates core model tests from:
- test_attribute.py
- test_behavioral.py
- test_cross_module_resolver.py
- test_datawindow.py
- test_example_model.py
- test_file.py
- test_global_variables.py
- test_security_analyzer.py
- test_specialized_controls.py
- test_symbol_table.py
- test_symbol_table_integration.py
- test_system_events.py
- test_system_functions.py
- test_treeview_control.py
- test_type_inference.py
- test_type_inference_integration.py
- test_type_system.py
- test_ui.py
- test_utils.py
- test_validators.py
"""

from datetime import datetime
from pathlib import Path

import pytest

# Core model imports
from src.model import (
    Model,
)
from src.model.analysis.security import (
    SecurityAnalyzer,
    SecuritySeverity,
    SecurityVulnerability,
)
from src.model.attribute import (
    Attribute,
    AttributeCollection,
    AttributeModifier,
    AttributeType,
)
from src.model.behavioral import (
    BehavioralEntity,
    BehavioralEvent,
    BehavioralMethod,
)
from src.model.datawindow import (
    DataWindow,
    DataWindowBuffer,
    DataWindowColumn,
)
from src.model.file import (
    PBFile,
    PBFileMetadata,
    PBFileParser,
    PBFileType,
)
from src.model.global_variables import (
    GlobalScope,
    GlobalVariable,
    GlobalVariableRegistry,
    VariableAccessMode,
)
from src.model.symbol_table import (
    Symbol,
    SymbolScope,
    SymbolTable,
    SymbolType,
)
from src.model.symbols.resolver import (
    CrossModuleResolver,
    ModuleReference,
    ResolutionContext,
)
from src.model.system_events import (
    EventMapping,
    EventPriority,
    SystemEvent,
    SystemEventHandler,
    SystemEventType,
)
from src.model.type_inference import (
    TypeInferenceEngine,
)
from src.model.type_system import (
    Type,
    TypeCategory,
    TypeChecker,
    TypeRegistry,
)
from src.model.ui import (
    UIControl,
    UILayout,
    UIMenu,
    UIWindow,
)
from src.model.utils import (
    camel_to_snake,
    format_error_message,
    is_valid_identifier,
    normalize_identifier,
    parse_qualified_name,
    snake_to_camel,
)
from src.model.validators import (
    ValidationContext,
    ValidationRule,
    ValidationSeverity,
    Validator,
)


class TestAttributes:
    """Test attribute functionality."""

    def test_attribute_creation(self):
        """Test creating attributes."""
        attr = Attribute(
            name="visible",
            type=AttributeType.BOOLEAN,
            value=True,
            modifier=AttributeModifier.PUBLIC,
            is_static=False,
            is_readonly=False,
        )

        assert attr.name == "visible"
        assert attr.type == AttributeType.BOOLEAN
        assert attr.value is True
        assert attr.modifier == AttributeModifier.PUBLIC

    def test_attribute_types(self):
        """Test different attribute types."""
        # Boolean
        bool_attr = Attribute("enabled", AttributeType.BOOLEAN, True)
        assert bool_attr.type == AttributeType.BOOLEAN

        # String
        str_attr = Attribute("text", AttributeType.STRING, "Hello")
        assert str_attr.type == AttributeType.STRING

        # Number
        num_attr = Attribute("width", AttributeType.NUMBER, 100)
        assert num_attr.type == AttributeType.NUMBER

        # Object
        obj_attr = Attribute("parent", AttributeType.OBJECT, None)
        assert obj_attr.type == AttributeType.OBJECT

    def test_attribute_modifiers(self):
        """Test attribute access modifiers."""
        public = Attribute("public_attr", modifier=AttributeModifier.PUBLIC)
        protected = Attribute("protected_attr", modifier=AttributeModifier.PROTECTED)
        private = Attribute("private_attr", modifier=AttributeModifier.PRIVATE)

        assert public.modifier == AttributeModifier.PUBLIC
        assert protected.modifier == AttributeModifier.PROTECTED
        assert private.modifier == AttributeModifier.PRIVATE

    def test_attribute_collection(self):
        """Test attribute collection management."""
        collection = AttributeCollection()

        # Add attributes
        collection.add(Attribute("name", AttributeType.STRING, "test"))
        collection.add(Attribute("value", AttributeType.NUMBER, 42))
        collection.add(Attribute("active", AttributeType.BOOLEAN, True))

        assert len(collection) == 3
        assert collection.get("name").value == "test"
        assert collection.get("value").value == 42
        assert collection.get("active").value is True

        # Remove attribute
        collection.remove("value")
        assert len(collection) == 2
        assert collection.get("value") is None


class TestBehavioral:
    """Test behavioral entity functionality."""

    def test_behavioral_entity_creation(self):
        """Test creating behavioral entities."""
        entity = BehavioralEntity(
            name="n_calculator",
            type="nonvisualobject",
            parent="n_base",
            library="calculator.pbl",
        )

        assert entity.name == "n_calculator"
        assert entity.type == "nonvisualobject"
        assert entity.parent == "n_base"
        assert entity.library == "calculator.pbl"

    def test_behavioral_methods(self):
        """Test behavioral method handling."""
        entity = BehavioralEntity(name="n_service")

        # Add method
        method = BehavioralMethod(
            name="of_process",
            return_type="integer",
            parameters=[("as_data", "string"), ("ai_mode", "integer")],
            access_modifier="public",
            is_static=False,
        )
        entity.add_method(method)

        assert len(entity.methods) == 1
        assert entity.get_method("of_process") == method
        assert method.return_type == "integer"
        assert len(method.parameters) == 2

    def test_behavioral_events(self):
        """Test behavioral event handling."""
        entity = BehavioralEntity(name="w_main")

        # Add event
        event = BehavioralEvent(
            name="ue_save",
            return_type="long",
            parameters=[],
            event_id="pbm_custom01",
            is_extended=True,
        )
        entity.add_event(event)

        assert len(entity.events) == 1
        assert entity.get_event("ue_save") == event
        assert event.event_id == "pbm_custom01"
        assert event.is_extended is True

    def test_behavioral_inheritance(self):
        """Test behavioral entity inheritance."""
        # Base class
        base = BehavioralEntity(
            name="n_base",
            type="nonvisualobject",
            parent="nonvisualobject",
        )
        base.add_method(BehavioralMethod("of_base_method", "integer"))

        # Derived class
        derived = BehavioralEntity(
            name="n_derived",
            type="nonvisualobject",
            parent="n_base",
        )
        derived.add_method(BehavioralMethod("of_derived_method", "string"))

        # Test inheritance chain
        assert derived.parent == base.name
        assert derived.inherits_from(base.name)


class TestCrossModuleResolver:
    """Test cross-module resolution functionality."""

    def test_module_reference(self):
        """Test module reference creation."""
        ref = ModuleReference(
            source_module="app.pbl",
            target_module="framework.pbl",
            reference_type="inherits",
            source_entity="w_app_window",
            target_entity="w_base_window",
        )

        assert ref.source_module == "app.pbl"
        assert ref.target_module == "framework.pbl"
        assert ref.reference_type == "inherits"
        assert ref.source_entity == "w_app_window"
        assert ref.target_entity == "w_base_window"

    def test_resolution_context(self):
        """Test resolution context."""
        context = ResolutionContext(
            current_module="app.pbl",
            search_path=["app.pbl", "framework.pbl", "common.pbl"],
            imported_modules=["framework.pbl"],
        )

        assert context.current_module == "app.pbl"
        assert len(context.search_path) == 3
        assert "framework.pbl" in context.imported_modules

    def test_cross_module_resolver(self):
        """Test cross-module resolver."""
        resolver = CrossModuleResolver()

        # Add modules
        resolver.add_module("app.pbl", ["w_main", "n_app"])
        resolver.add_module("framework.pbl", ["w_base", "n_base"])

        # Add references
        resolver.add_reference(
            ModuleReference(
                source_module="app.pbl",
                target_module="framework.pbl",
                reference_type="inherits",
                source_entity="w_main",
                target_entity="w_base",
            )
        )

        # Resolve
        context = ResolutionContext(
            current_module="app.pbl",
            search_path=["app.pbl", "framework.pbl"],
        )
        result = resolver.resolve("w_base", context)

        assert result.found is True
        assert result.module == "framework.pbl"
        assert result.entity == "w_base"

    def test_dependency_graph(self):
        """Test dependency graph generation."""
        resolver = CrossModuleResolver()

        # Build dependency graph
        resolver.add_reference(ModuleReference("a.pbl", "b.pbl", "uses", "A", "B"))
        resolver.add_reference(ModuleReference("b.pbl", "c.pbl", "uses", "B", "C"))

        graph = resolver.build_dependency_graph()

        assert "a.pbl" in graph.nodes
        assert "b.pbl" in graph.nodes
        assert "c.pbl" in graph.nodes
        assert graph.has_edge("a.pbl", "b.pbl")
        assert graph.has_edge("b.pbl", "c.pbl")


class TestDataWindow:
    """Test DataWindow functionality."""

    def test_datawindow_creation(self):
        """Test creating a DataWindow."""
        dw = DataWindow(
            name="d_employee",
            dataobject="d_employee_list",
            title="Employee List",
            processing=1,  # Grid
        )

        assert dw.name == "d_employee"
        assert dw.dataobject == "d_employee_list"
        assert dw.title == "Employee List"
        assert dw.processing == 1

    def test_datawindow_columns(self):
        """Test DataWindow column management."""
        dw = DataWindow(name="d_test")

        # Add columns
        col1 = DataWindowColumn(
            name="emp_id",
            datatype="number",
            width=80,
            label="ID",
        )
        col2 = DataWindowColumn(
            name="emp_name",
            datatype="string",
            width=200,
            label="Name",
        )

        dw.add_column(col1)
        dw.add_column(col2)

        assert len(dw.columns) == 2
        assert dw.get_column("emp_id") == col1
        assert dw.get_column("emp_name") == col2

    def test_datawindow_data_manipulation(self):
        """Test DataWindow data manipulation."""
        dw = DataWindow(name="d_test")

        # Add columns
        dw.add_column(DataWindowColumn("id", "number"))
        dw.add_column(DataWindowColumn("name", "string"))

        # Insert rows
        dw.insert_row({"id": 1, "name": "John"})
        dw.insert_row({"id": 2, "name": "Jane"})

        assert dw.row_count() == 2
        assert dw.get_item(1, "name") == "John"
        assert dw.get_item(2, "name") == "Jane"

        # Update row
        dw.set_item(1, "name", "John Doe")
        assert dw.get_item(1, "name") == "John Doe"

        # Delete row
        dw.delete_row(2)
        assert dw.row_count() == 1

    def test_datawindow_buffers(self):
        """Test DataWindow buffer management."""
        dw = DataWindow(name="d_test")

        # Primary buffer
        assert dw.primary_buffer is not None
        assert dw.primary_buffer.type == DataWindowBuffer.PRIMARY

        # Filter buffer
        assert dw.filter_buffer is not None
        assert dw.filter_buffer.type == DataWindowBuffer.FILTER

        # Delete buffer
        assert dw.delete_buffer is not None
        assert dw.delete_buffer.type == DataWindowBuffer.DELETE


class TestFiles:
    """Test file handling functionality."""

    def test_pb_file_creation(self):
        """Test creating PB file objects."""
        file = PBFile(
            path=Path("/src/window.srw"),
            type=PBFileType.WINDOW,
            encoding="utf-16-le",
        )

        assert file.path == Path("/src/window.srw")
        assert file.type == PBFileType.WINDOW
        assert file.encoding == "utf-16-le"

    def test_pb_file_types(self):
        """Test different PB file types."""
        # Window
        window = PBFile("w_main.srw", PBFileType.WINDOW)
        assert window.type == PBFileType.WINDOW
        assert window.extension == ".srw"

        # DataWindow
        dw = PBFile("d_list.srd", PBFileType.DATAWINDOW)
        assert dw.type == PBFileType.DATAWINDOW
        assert dw.extension == ".srd"

        # Library
        lib = PBFile("app.pbl", PBFileType.LIBRARY)
        assert lib.type == PBFileType.LIBRARY
        assert lib.extension == ".pbl"

    def test_pb_file_metadata(self):
        """Test PB file metadata."""
        metadata = PBFileMetadata(
            version="12.5",
            created_date=datetime(2024, 1, 1),
            modified_date=datetime(2024, 6, 29),
            author="Developer",
            comments=["Initial version", "Bug fixes"],
        )

        file = PBFile("test.srw", metadata=metadata)

        assert file.metadata.version == "12.5"
        assert file.metadata.author == "Developer"
        assert len(file.metadata.comments) == 2

    def test_pb_file_content_parsing(self):
        """Test PB file content parsing."""
        parser = PBFileParser()

        content = """
        global type w_main from window
        end type
        type cb_ok from commandbutton within w_main
        end type
        """

        result = parser.parse_content(content, PBFileType.WINDOW)

        assert result.file_type == PBFileType.WINDOW
        assert result.global_type == "w_main"
        assert "cb_ok" in result.controls


class TestGlobalVariables:
    """Test global variable functionality."""

    def test_global_variable_creation(self):
        """Test creating global variables."""
        var = GlobalVariable(
            name="gs_app_name",
            type="string",
            initial_value="My Application",
            scope=GlobalScope.APPLICATION,
            access_mode=VariableAccessMode.READ_WRITE,
        )

        assert var.name == "gs_app_name"
        assert var.type == "string"
        assert var.initial_value == "My Application"
        assert var.scope == GlobalScope.APPLICATION

    def test_global_variable_registry(self):
        """Test global variable registry."""
        registry = GlobalVariableRegistry()

        # Register variables
        registry.register(
            GlobalVariable("gi_count", "integer", 0, GlobalScope.APPLICATION)
        )
        registry.register(GlobalVariable("gs_user", "string", "", GlobalScope.SESSION))
        registry.register(
            GlobalVariable("gb_debug", "boolean", False, GlobalScope.SHARED)
        )

        assert len(registry) == 3
        assert registry.get("gi_count").type == "integer"
        assert registry.get("gs_user").scope == GlobalScope.SESSION
        assert registry.get("gb_debug").initial_value is False

    def test_global_variable_access_modes(self):
        """Test global variable access modes."""
        # Read-write
        rw_var = GlobalVariable("g_rw", access_mode=VariableAccessMode.READ_WRITE)
        assert rw_var.can_read()
        assert rw_var.can_write()

        # Read-only
        ro_var = GlobalVariable("g_ro", access_mode=VariableAccessMode.READ_ONLY)
        assert ro_var.can_read()
        assert not ro_var.can_write()

        # Write-only
        wo_var = GlobalVariable("g_wo", access_mode=VariableAccessMode.WRITE_ONLY)
        assert not wo_var.can_read()
        assert wo_var.can_write()


class TestSecurityAnalyzer:
    """Test security analysis functionality."""

    def test_security_analyzer_creation(self):
        """Test creating security analyzer."""
        analyzer = SecurityAnalyzer()

        assert analyzer is not None
        assert len(analyzer.rules) > 0
        assert analyzer.enabled is True

    def test_security_vulnerability_detection(self):
        """Test detecting security vulnerabilities."""
        analyzer = SecurityAnalyzer()

        # Test SQL injection vulnerability
        code = """
        string ls_sql
        ls_sql = "SELECT * FROM users WHERE name = '" + as_name + "'"
        EXECUTE IMMEDIATE :ls_sql;
        """

        vulnerabilities = analyzer.analyze_code(code)

        assert len(vulnerabilities) > 0
        assert any(v.type == "SQL_INJECTION" for v in vulnerabilities)

    def test_security_severity_levels(self):
        """Test security severity levels."""
        # Critical
        critical = SecurityVulnerability(
            type="SQL_INJECTION",
            severity=SecuritySeverity.CRITICAL,
            message="SQL injection vulnerability detected",
            line_number=10,
        )
        assert critical.severity == SecuritySeverity.CRITICAL

        # High
        high = SecurityVulnerability(
            type="WEAK_CRYPTO",
            severity=SecuritySeverity.HIGH,
            message="Weak cryptography algorithm used",
            line_number=20,
        )
        assert high.severity == SecuritySeverity.HIGH

        # Medium
        medium = SecurityVulnerability(
            type="HARDCODED_PASSWORD",
            severity=SecuritySeverity.MEDIUM,
            message="Hardcoded password found",
            line_number=30,
        )
        assert medium.severity == SecuritySeverity.MEDIUM

    def test_security_report_generation(self):
        """Test security report generation."""
        analyzer = SecurityAnalyzer()

        # Analyze some code
        vulnerabilities = [
            SecurityVulnerability("SQL_INJECTION", SecuritySeverity.CRITICAL),
            SecurityVulnerability("XSS", SecuritySeverity.HIGH),
            SecurityVulnerability("INFO_LEAK", SecuritySeverity.LOW),
        ]

        report = analyzer.generate_report(vulnerabilities)

        assert report.total_count == 3
        assert report.critical_count == 1
        assert report.high_count == 1
        assert report.low_count == 1


class TestSymbolTable:
    """Test symbol table functionality."""

    def test_symbol_creation(self):
        """Test creating symbols."""
        symbol = Symbol(
            name="w_main",
            type=SymbolType.WINDOW,
            scope=SymbolScope.GLOBAL,
            location="app.pbl",
            attributes={"title": "Main Window"},
        )

        assert symbol.name == "w_main"
        assert symbol.type == SymbolType.WINDOW
        assert symbol.scope == SymbolScope.GLOBAL
        assert symbol.location == "app.pbl"

    def test_symbol_table_operations(self):
        """Test symbol table operations."""
        table = SymbolTable()

        # Add symbols
        table.add(Symbol("gi_count", SymbolType.VARIABLE, SymbolScope.GLOBAL))
        table.add(Symbol("w_main", SymbolType.WINDOW, SymbolScope.GLOBAL))
        table.add(Symbol("of_process", SymbolType.FUNCTION, SymbolScope.LOCAL))

        assert len(table) == 3
        assert table.lookup("gi_count").type == SymbolType.VARIABLE
        assert table.lookup("w_main").type == SymbolType.WINDOW

        # Remove symbol
        table.remove("of_process")
        assert len(table) == 2
        assert table.lookup("of_process") is None

    def test_symbol_scope_management(self):
        """Test symbol scope management."""
        table = SymbolTable()

        # Global scope
        table.enter_scope("global")
        table.add(Symbol("g_var", SymbolType.VARIABLE, SymbolScope.GLOBAL))

        # Function scope
        table.enter_scope("function_f1")
        table.add(Symbol("l_var", SymbolType.VARIABLE, SymbolScope.LOCAL))

        # Lookup in current scope
        assert table.lookup("l_var") is not None
        assert table.lookup("g_var") is not None  # Global visible

        # Exit function scope
        table.exit_scope()
        assert table.lookup("l_var") is None  # Local not visible
        assert table.lookup("g_var") is not None  # Global still visible

    def test_symbol_resolution(self):
        """Test symbol resolution."""
        table = SymbolTable()

        # Add symbols with inheritance
        table.add(
            Symbol(
                "w_base",
                SymbolType.WINDOW,
                attributes={"methods": ["of_init", "of_close"]},
            )
        )
        table.add(
            Symbol(
                "w_derived",
                SymbolType.WINDOW,
                attributes={"parent": "w_base", "methods": ["of_process"]},
            )
        )

        # Resolve inherited methods
        resolution = table.resolve_inheritance("w_derived")

        assert "of_init" in resolution.inherited_methods
        assert "of_close" in resolution.inherited_methods
        assert "of_process" in resolution.own_methods


class TestSystemEvents:
    """Test system event functionality."""

    def test_system_event_types(self):
        """Test system event types."""
        # Constructor
        constructor = SystemEvent(
            name="constructor",
            type=SystemEventType.CONSTRUCTOR,
            event_id="pbm_constructor",
            priority=EventPriority.HIGH,
        )
        assert constructor.type == SystemEventType.CONSTRUCTOR

        # Destructor
        destructor = SystemEvent(
            name="destructor",
            type=SystemEventType.DESTRUCTOR,
            event_id="pbm_destructor",
            priority=EventPriority.HIGH,
        )
        assert destructor.type == SystemEventType.DESTRUCTOR

        # Open
        open_event = SystemEvent(
            name="open",
            type=SystemEventType.OPEN,
            event_id="pbm_open",
            priority=EventPriority.NORMAL,
        )
        assert open_event.type == SystemEventType.OPEN

    def test_system_event_handler(self):
        """Test system event handler."""
        handler = SystemEventHandler()

        # Register event handlers
        handler.register("pbm_clicked", lambda: print("Clicked"))
        handler.register("pbm_dwnkey", lambda key: print(f"Key: {key}"))

        assert handler.is_registered("pbm_clicked")
        assert handler.is_registered("pbm_dwnkey")
        assert not handler.is_registered("pbm_custom")

    def test_event_mapping(self):
        """Test event ID to event type mapping."""
        mapping = EventMapping()

        # Standard mappings
        assert mapping.get_event_type("pbm_constructor") == SystemEventType.CONSTRUCTOR
        assert mapping.get_event_type("pbm_clicked") == SystemEventType.CLICKED
        assert mapping.get_event_type("pbm_close") == SystemEventType.CLOSE

        # Custom mapping
        mapping.add_custom("pbm_custom01", SystemEventType.USER_DEFINED)
        assert mapping.get_event_type("pbm_custom01") == SystemEventType.USER_DEFINED


class TestTypeSystem:
    """Test type system functionality."""

    def test_type_creation(self):
        """Test creating types."""
        # Primitive type
        int_type = Type(
            name="integer",
            category=TypeCategory.PRIMITIVE,
            size=4,
            is_nullable=False,
        )
        assert int_type.name == "integer"
        assert int_type.category == TypeCategory.PRIMITIVE
        assert int_type.size == 4

        # Object type
        window_type = Type(
            name="window",
            category=TypeCategory.OBJECT,
            parent="systemobject",
            is_nullable=True,
        )
        assert window_type.category == TypeCategory.OBJECT
        assert window_type.parent == "systemobject"

    def test_type_registry(self):
        """Test type registry."""
        registry = TypeRegistry()

        # Register built-in types
        registry.register_primitive("integer", 4)
        registry.register_primitive("long", 8)
        registry.register_primitive("string", None)  # Variable size
        registry.register_primitive("boolean", 1)

        # Register object types
        registry.register_object("window", "systemobject")
        registry.register_object("datawindow", "systemobject")

        assert registry.is_primitive("integer")
        assert registry.is_object("window")
        assert registry.get_type("string").category == TypeCategory.PRIMITIVE

    def test_type_compatibility(self):
        """Test type compatibility checking."""
        checker = TypeChecker()

        # Numeric compatibility
        assert checker.is_compatible("integer", "long")
        assert checker.is_compatible("integer", "decimal")
        assert not checker.is_compatible("integer", "string")

        # Object compatibility (inheritance)
        assert checker.is_compatible("window", "systemobject")
        assert not checker.is_compatible("window", "datawindow")

        # Null compatibility
        assert checker.is_compatible("null", "string")
        assert checker.is_compatible("null", "window")

    def test_type_inference(self):
        """Test type inference."""
        engine = TypeInferenceEngine()

        # Literal inference
        assert engine.infer_literal_type(42) == "integer"
        assert engine.infer_literal_type(3.14) == "decimal"
        assert engine.infer_literal_type("hello") == "string"
        assert engine.infer_literal_type(True) == "boolean"

        # Expression inference
        expr = "10 + 20"
        result = engine.infer_expression_type(expr)
        assert result.type == "integer"
        assert result.confidence == 1.0


class TestUI:
    """Test UI model functionality."""

    def test_ui_control_creation(self):
        """Test creating UI controls."""
        button = UIControl(
            name="cb_ok",
            type="commandbutton",
            text="OK",
            x=10,
            y=10,
            width=100,
            height=30,
            visible=True,
            enabled=True,
        )

        assert button.name == "cb_ok"
        assert button.type == "commandbutton"
        assert button.text == "OK"
        assert button.visible is True

    def test_ui_window(self):
        """Test UI window model."""
        window = UIWindow(
            name="w_main",
            title="Main Window",
            x=100,
            y=100,
            width=800,
            height=600,
            windowtype="main",
            windowstate="normal",
        )

        # Add controls
        window.add_control(UIControl("cb_ok", "commandbutton"))
        window.add_control(UIControl("cb_cancel", "commandbutton"))
        window.add_control(UIControl("dw_list", "datawindow"))

        assert len(window.controls) == 3
        assert window.get_control("cb_ok").type == "commandbutton"
        assert window.get_control("dw_list").type == "datawindow"

    def test_ui_menu(self):
        """Test UI menu model."""
        menu = UIMenu(
            name="m_main",
            text="File",
        )

        # Add menu items
        menu.add_item("m_new", "New", "Ctrl+N")
        menu.add_item("m_open", "Open", "Ctrl+O")
        menu.add_separator()
        menu.add_item("m_exit", "Exit", "Alt+F4")

        assert len(menu.items) == 4
        assert menu.items[2].is_separator

    def test_ui_layout(self):
        """Test UI layout management."""
        layout = UILayout(type="grid", rows=2, columns=3)

        # Add controls to layout
        layout.add_control(UIControl("c1", "statictext"), 0, 0)
        layout.add_control(UIControl("c2", "singlelineedit"), 0, 1)
        layout.add_control(UIControl("c3", "commandbutton"), 1, 2)

        assert layout.get_control_at(0, 0).name == "c1"
        assert layout.get_control_at(0, 1).name == "c2"
        assert layout.get_control_at(1, 2).name == "c3"


class TestValidators:
    """Test validation functionality."""

    def test_validator_creation(self):
        """Test creating validators."""
        validator = Validator(
            name="identifier_validator",
            description="Validates PowerBuilder identifiers",
        )

        # Add rules
        validator.add_rule(
            ValidationRule(
                name="length_check",
                check=lambda x: len(x) <= 40,
                message="Identifier too long",
                severity=ValidationSeverity.ERROR,
            )
        )
        validator.add_rule(
            ValidationRule(
                name="char_check",
                check=lambda x: x[0].isalpha() if x else False,
                message="Identifier must start with letter",
                severity=ValidationSeverity.ERROR,
            )
        )

        assert len(validator.rules) == 2

    def test_validation_execution(self):
        """Test executing validation."""
        validator = Validator("test_validator")

        # Add rules
        validator.add_rule(
            ValidationRule(
                "not_empty",
                lambda x: bool(x),
                "Value cannot be empty",
                ValidationSeverity.ERROR,
            )
        )
        validator.add_rule(
            ValidationRule(
                "min_length",
                lambda x: len(x) >= 3,
                "Value too short",
                ValidationSeverity.WARNING,
            )
        )

        # Valid value
        result = validator.validate("test")
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

        # Invalid value
        result = validator.validate("ab")
        assert result.is_valid  # Only warning
        assert len(result.warnings) == 1

        # Empty value
        result = validator.validate("")
        assert not result.is_valid
        assert len(result.errors) == 1

    def test_validation_context(self):
        """Test validation with context."""
        context = ValidationContext(
            current_file="test.srw",
            current_line=10,
            current_object="w_main",
            strict_mode=True,
        )

        validator = Validator("context_validator")
        validator.add_rule(
            ValidationRule(
                "context_check",
                lambda x, ctx: ctx.strict_mode,
                "Failed in strict mode",
                ValidationSeverity.ERROR,
            )
        )

        result = validator.validate("test", context)
        assert not result.is_valid  # Fails due to strict mode


class TestUtils:
    """Test utility functions."""

    def test_name_conversions(self):
        """Test name conversion utilities."""
        # Camel to snake
        assert camel_to_snake("CamelCase") == "camel_case"
        assert camel_to_snake("HTTPResponse") == "http_response"
        assert camel_to_snake("getXMLParser") == "get_xml_parser"

        # Snake to camel
        assert snake_to_camel("snake_case") == "SnakeCase"
        assert snake_to_camel("http_response") == "HttpResponse"
        assert snake_to_camel("get_xml_parser") == "GetXmlParser"

    def test_identifier_validation(self):
        """Test identifier validation."""
        # Valid identifiers
        assert is_valid_identifier("valid_name")
        assert is_valid_identifier("_private")
        assert is_valid_identifier("name123")

        # Invalid identifiers
        assert not is_valid_identifier("123invalid")  # Starts with number
        assert not is_valid_identifier("invalid-name")  # Contains hyphen
        assert not is_valid_identifier("invalid name")  # Contains space
        assert not is_valid_identifier("")  # Empty

    def test_identifier_normalization(self):
        """Test identifier normalization."""
        assert normalize_identifier("MyVariable") == "myvariable"
        assert normalize_identifier("some_CONSTANT") == "some_constant"
        assert normalize_identifier("MixedCase123") == "mixedcase123"

    def test_qualified_name_parsing(self):
        """Test parsing qualified names."""
        # Simple name
        parts = parse_qualified_name("identifier")
        assert parts == ["identifier"]

        # Qualified name
        parts = parse_qualified_name("object.property")
        assert parts == ["object", "property"]

        # Fully qualified
        parts = parse_qualified_name("library.object.method")
        assert parts == ["library", "object", "method"]

    def test_error_formatting(self):
        """Test error message formatting."""
        msg = format_error_message(
            "Syntax error",
            file="test.srw",
            line=10,
            column=5,
        )
        assert "Syntax error" in msg
        assert "test.srw" in msg
        assert "line 10" in msg
        assert "column 5" in msg


# Test fixtures
@pytest.fixture
def sample_model():
    """Provide a sample model for testing."""
    model = Model(name="TestApp")

    # Add some entities
    model.add_window("w_main", "Main Window")
    model.add_datawindow("d_list", "List DataWindow")
    model.add_nonvisualobject("n_service", "Service Object")

    return model


@pytest.fixture
def sample_symbol_table():
    """Provide a sample symbol table."""
    table = SymbolTable()

    # Add various symbols
    table.add(Symbol("gi_count", SymbolType.VARIABLE, SymbolScope.GLOBAL))
    table.add(Symbol("gs_name", SymbolType.VARIABLE, SymbolScope.GLOBAL))
    table.add(Symbol("w_main", SymbolType.WINDOW, SymbolScope.GLOBAL))
    table.add(Symbol("of_process", SymbolType.FUNCTION, SymbolScope.LOCAL))

    return table


@pytest.fixture
def sample_type_registry():
    """Provide a sample type registry."""
    registry = TypeRegistry()

    # Register primitive types
    for ptype in ["integer", "long", "string", "boolean", "decimal"]:
        registry.register_primitive(ptype)

    # Register object types
    registry.register_object("window", "systemobject")
    registry.register_object("datawindow", "systemobject")
    registry.register_object("nonvisualobject", "systemobject")

    return registry
