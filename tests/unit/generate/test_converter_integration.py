#!/usr/bin/env python3
"""Test suite for converter integration and custom widget generation."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from lark import Tree

from src.generate.converter_integration import ConversionPipeline


class TestCustomWidgetGeneration:
    """Test custom widget generation functionality."""

    @pytest.fixture
    def mock_flutter_generator(self):
        """Create mock Flutter generator."""
        mock_gen = Mock()
        mock_gen.render_template = Mock(return_value="Generated widget code")
        mock_gen.write_file = Mock()
        return mock_gen

    @pytest.fixture
    def pipeline(self, mock_flutter_generator):
        """Create ConversionPipeline with mocked dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pipeline = ConversionPipeline(Path(temp_dir))
            pipeline.flutter_generator = mock_flutter_generator
            return pipeline

    def test_generate_datawindow_custom_widget(self, pipeline):
        """Test DataWindow custom widget generation."""
        control = {
            "type": "datawindow",
            "widget": "DataWindowWidget",
            "dart_name": "employeeData",
            "properties": {
                "dataobject": "d_employee",
            },
        }

        pipeline._generate_datawindow_custom_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "EmployeeDataDataWindow"
        assert context["datawindow_name"] == "d_employee"
        assert context["dart_name"] == "employeeData"

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/employee_data_data_window.dart"

    def test_generate_tree_view_widget(self, pipeline):
        """Test TreeView custom widget generation."""
        control = {
            "type": "treeview",
            "widget": "TreeView",
            "dart_name": "categoryTree",
            "flutter_properties": {},
            "properties": {
                "haslines": True,
                "hasbuttons": False,
                "sorted": True,
            },
        }

        pipeline._generate_tree_view_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "CategoryTreeTreeView"
        assert context["show_lines"] is True
        assert context["show_expand_buttons"] is False
        assert context["is_sorted"] is True

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/category_tree_tree_view.dart"

    def test_generate_chart_widget(self, pipeline):
        """Test Chart/Graph custom widget generation."""
        control = {
            "type": "graph",
            "widget": "CustomChart",
            "dart_name": "salesChart",
            "flutter_properties": {},
            "properties": {
                "graphtype": "line",
            },
        }

        pipeline._generate_chart_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "SalesChartChart"
        assert context["chart_type"] == "line"

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/sales_chart_chart.dart"

    def test_generate_date_picker_widget(self, pipeline):
        """Test DatePicker custom widget generation."""
        control = {
            "type": "datepicker",
            "widget": "DatePickerField",
            "dart_name": "birthDate",
            "flutter_properties": {},
            "properties": {
                "format": "dd/MM/yyyy",
            },
        }

        pipeline._generate_date_picker_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "BirthDateDatePicker"
        assert context["widget"]["is_stateful"] is False
        assert context["date_format"] == "dd/MM/yyyy"

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/birth_date_date_picker.dart"

    def test_generate_calendar_widget(self, pipeline):
        """Test Calendar custom widget generation."""
        control = {
            "type": "monthcalendar",
            "widget": "TableCalendar",
            "dart_name": "eventCalendar",
            "flutter_properties": {},
            "properties": {
                "showtoday": False,
            },
        }

        pipeline._generate_calendar_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "EventCalendarCalendar"
        assert context["show_today"] is False

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/event_calendar_calendar.dart"

    def test_generate_ink_canvas_widget(self, pipeline):
        """Test Ink canvas custom widget generation."""
        control = {
            "type": "inkpicture",
            "widget": "CustomInkCanvas",
            "dart_name": "signaturePad",
            "flutter_properties": {},
            "properties": {
                "inkcolor": "Colors.blue",
                "inkwidth": 3.0,
            },
        }

        pipeline._generate_ink_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "SignaturePadInkCanvas"
        assert context["is_text_field"] is False
        assert context["stroke_color"] == "Colors.blue"
        assert context["stroke_width"] == 3.0

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/signature_pad_ink_canvas.dart"

    def test_generate_ink_edit_widget(self, pipeline):
        """Test Ink edit custom widget generation."""
        control = {
            "type": "inkedit",
            "widget": "CustomInkTextField",
            "dart_name": "handwritingInput",
            "flutter_properties": {},
            "properties": {
                "inkcolor": "Colors.black",
                "inkwidth": 2.0,
            },
        }

        pipeline._generate_ink_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "HandwritingInputInkEdit"
        assert context["is_text_field"] is True
        assert context["stroke_color"] == "Colors.black"
        assert context["stroke_width"] == 2.0

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/handwriting_input_ink_edit.dart"

    def test_generate_animation_widget(self, pipeline):
        """Test Animation custom widget generation."""
        control = {
            "type": "animation",
            "widget": "AnimatedBuilder",
            "dart_name": "loadingAnimation",
            "flutter_properties": {},
            "properties": {
                "animationfile": "assets/loading.json",
                "autoplay": False,
                "transparent": True,
            },
        }

        pipeline._generate_animation_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "LoadingAnimationAnimation"
        assert context["animation_file"] == "assets/loading.json"
        assert context["auto_play"] is False
        assert context["is_transparent"] is True

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/loading_animation_animation.dart"

    def test_generate_ole_placeholder_widget(self, pipeline):
        """Test OLE placeholder widget generation."""
        control = {
            "type": "ole",
            "widget": "Container",
            "dart_name": "excelViewer",
            "properties": {
                "classname": "Excel.Application",
                "activation": "automatic",
                "displaytype": "icon",
            },
        }

        pipeline._generate_ole_placeholder_widget(control)

        # Verify template was rendered
        pipeline.flutter_generator.render_template.assert_called_once()
        context = pipeline.flutter_generator.render_template.call_args[0][1]
        assert context["widget"]["name"] == "ExcelViewerOleContainer"
        assert context["widget"]["is_stateful"] is False
        assert context["ole_class"] == "Excel.Application"
        assert context["activation_type"] == "automatic"
        assert context["display_mode"] == "icon"

        # Verify file was written
        pipeline.flutter_generator.write_file.assert_called_once()
        filename = pipeline.flutter_generator.write_file.call_args[0][0]
        assert filename == "widgets/excel_viewer_ole_container.dart"

    def test_generate_custom_widget_main_dispatcher(self, pipeline):
        """Test main _generate_custom_widget dispatcher method."""
        # Test DataWindow
        control = {
            "type": "datawindow",
            "widget": "DataWindowWidget",
            "dart_name": "test",
        }
        pipeline._generate_custom_widget(control)
        pipeline.flutter_generator.render_template.assert_called()

        # Test unknown type
        pipeline.flutter_generator.reset_mock()
        control = {
            "type": "unknownwidget",
            "widget": "UnknownWidget",
            "dart_name": "test",
        }

        with patch("generate.converter_integration.logger") as mock_logger:
            pipeline._generate_custom_widget(control)
            mock_logger.warning.assert_called_with(
                "Unknown custom widget type: unknownwidget"
            )
            # No template should be rendered for unknown type
            pipeline.flutter_generator.render_template.assert_not_called()

    def test_convert_window_with_custom_widgets(self, pipeline):
        """Test converting window with custom widgets."""
        # Create mock AST converter
        mock_ast_converter = Mock()
        mock_window_def = Mock()
        mock_window_def.name = "TestWindow"
        mock_window_def.properties = {"title": "Test Window"}
        mock_window_def.controls = [
            {
                "type": "datawindow",
                "widget": "DataWindowWidget",
                "dart_name": "employeeData",
                "custom_widget": True,
                "properties": {"dataobject": "d_employee"},
            },
            {
                "type": "button",
                "widget": "ElevatedButton",
                "dart_name": "saveButton",
                "custom_widget": False,
            },
            {
                "type": "treeview",
                "widget": "TreeView",
                "dart_name": "categoryTree",
                "custom_widget": True,
                "properties": {"haslines": True},
            },
        ]
        mock_window_def.datawindows = ["d_employee"]
        mock_window_def.variables = []
        mock_window_def.methods = []
        mock_window_def.events = []

        mock_ast_converter.convert_window.return_value = mock_window_def
        mock_ast_converter.ui_converter.generate_widget_tree.return_value = (
            "Widget tree"
        )
        mock_ast_converter.ui_converter.get_widget_imports.return_value = []

        pipeline.ast_converter = mock_ast_converter

        # Mock AST
        ast = Tree("window", [])

        # Convert window
        pipeline.convert_window(ast, "TestWindow")

        # Verify custom widgets were generated
        assert (
            pipeline.flutter_generator.render_template.call_count >= 3
        )  # Window + 2 custom widgets

        # Verify write_file was called for window and custom widgets
        assert pipeline.flutter_generator.write_file.call_count >= 3


class TestIntegrationWithUIConverter:
    """Test integration between converter_integration and ui_converter."""

    def test_custom_widget_detection(self):
        """Test that custom widgets are properly detected from UI converter mappings."""
        from src.generate.converters.flutter.widgets import UIConverter

        ui_converter = UIConverter()

        # Check controls marked as custom
        custom_controls = []
        for control_type, mapping in ui_converter.control_map.items():
            if mapping.get("custom", False):
                custom_controls.append(control_type)

        expected_custom = [
            "datawindow",
            "treeview",
            "graph",
            "ole",
            "animation",
            "datepicker",
            "monthcalendar",
            "inkpicture",
            "inkedit",
        ]

        for control in expected_custom:
            assert control in custom_controls

    def test_control_conversion_preserves_custom_flag(self):
        """Test that control conversion preserves custom widget flag."""
        from src.generate.converters.flutter.widgets import UIConverter

        ui_converter = UIConverter()

        # Test DataWindow control
        result = ui_converter.convert_control(
            "datawindow",
            "dw_employee",
            {"dataobject": "d_employee"},
        )

        assert result["custom_widget"] is True
        assert result["widget"] == "DataWindowWidget"

        # Test regular button control
        result = ui_converter.convert_control(
            "commandbutton",
            "cb_save",
            {"text": "Save"},
        )

        assert result["custom_widget"] is False
        assert result["widget"] == "ElevatedButton"
