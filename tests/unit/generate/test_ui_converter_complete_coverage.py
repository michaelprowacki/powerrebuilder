#!/usr/bin/env python3
"""Test complete UI control type coverage in UIConverter."""

import pytest

from src.generate.converters.flutter.widgets import UIConverter


class TestCompleteUIControlCoverage:
    """Test all UI control types are properly mapped."""

    @pytest.fixture
    def ui_converter(self):
        """Create UIConverter instance."""
        return UIConverter()

    def test_scrollbar_controls(self, ui_converter):
        """Test vertical and horizontal scrollbar conversion."""
        # Test vertical scrollbar
        result = ui_converter.convert_control(
            "vscrollbar",
            "vsb_main",
            {
                "minposition": 0,
                "maxposition": 100,
                "position": 50,
                "linesize": 5,
                "pagesize": 20,
            },
        )

        assert result["widget"] == "Scrollbar"
        assert result["config"]["axis"] == "Axis.vertical"
        assert result["flutter_properties"]["_minValue"] == 0
        assert result["flutter_properties"]["_maxValue"] == 100

        # Test horizontal scrollbar
        result = ui_converter.convert_control(
            "hscrollbar",
            "hsb_main",
            {"position": 25},
        )

        assert result["widget"] == "Scrollbar"
        assert result["config"]["axis"] == "Axis.horizontal"
        assert result["flutter_properties"]["_currentValue"] == 25

    def test_combobox_control(self, ui_converter):
        """Test ComboBox (editable dropdown) conversion."""
        result = ui_converter.convert_control(
            "combobox",
            "cb_country",
            {
                "text": "United States",
                "items": ["USA", "Canada", "Mexico"],
                "allowedit": True,
                "sorted": True,
            },
        )

        assert result["widget"] == "Autocomplete"
        assert result["flutter_properties"]["_selectedText"] == "United States"
        assert result["flutter_properties"]["_suggestions"] == [
            "USA",
            "Canada",
            "Mexico",
        ]
        assert result["flutter_properties"]["_allowEdit"] is True
        assert result["flutter_properties"]["_isSorted"] is True

    def test_richtextedit_control(self, ui_converter):
        """Test RichTextEdit control conversion."""
        result = ui_converter.convert_control(
            "richtextedit",
            "rte_document",
            {
                "text": "<p>Rich text content</p>",
                "readonly": False,
                "toolbar": True,
            },
        )

        assert result["widget"] == "QuillEditor"
        assert result["custom_widget"] is True
        assert "flutter_quill" in result.get("package", "")
        assert result["flutter_properties"]["_document"] == "<p>Rich text content</p>"
        assert result["flutter_properties"]["_readOnly"] is False
        assert result["flutter_properties"]["_showToolbar"] is True

    def test_mdiclient_control(self, ui_converter):
        """Test MDI Client control conversion."""
        result = ui_converter.convert_control(
            "mdiclient",
            "mdi_workspace",
            {
                "backcolor": "255,255,255",
            },
        )

        assert result["widget"] == "Container"
        assert result["is_container"] is True
        assert result["custom_widget"] is True
        assert result["config"]["placeholder"] == "Text('MDI Client Area')"

    def test_widget_code_generation_new_controls(self, ui_converter):
        """Test widget code generation for new controls."""
        # Test scrollbar
        scrollbar_control = {
            "widget": "Scrollbar",
            "dart_name": "verticalScroll",
            "type": "vscrollbar",
            "config": {"axis": "Axis.vertical"},
        }
        code = ui_converter._generate_widget_code(scrollbar_control)
        assert "Scrollbar" in code
        assert "ScrollController" in code
        assert "Axis.vertical" in code

        # Test Autocomplete
        combo_control = {
            "widget": "Autocomplete",
            "dart_name": "countrySelector",
            "type": "combobox",
        }
        code = ui_converter._generate_widget_code(combo_control)
        assert "Autocomplete<String>" in code
        assert "optionsBuilder" in code
        assert "onSelected" in code

        # Test QuillEditor
        rte_control = {
            "widget": "QuillEditor",
            "dart_name": "documentEditor",
            "type": "richtextedit",
        }
        code = ui_converter._generate_widget_code(rte_control)
        assert "QuillEditor" in code
        assert "QuillController" in code
        assert "FocusNode" in code

        # Test MDI Client
        mdi_control = {
            "widget": "Container",
            "dart_name": "workspace",
            "type": "mdiclient",
        }
        code = ui_converter._generate_widget_code(mdi_control)
        assert "MdiClientArea" in code
        assert "Windows" in code

    def test_imports_for_new_controls(self, ui_converter):
        """Test that proper imports are generated for new controls."""
        controls = [
            {"type": "combobox", "widget": "Autocomplete"},
            {"type": "richtextedit", "widget": "QuillEditor"},
            {"type": "mdiclient", "widget": "Container"},
            {"type": "vscrollbar", "widget": "Scrollbar"},
        ]

        imports = ui_converter.get_widget_imports(controls)

        # Check for QuillEditor import
        assert any("flutter_quill" in imp for imp in imports)
        assert any("rich_text_editor.dart" in imp for imp in imports)

        # Check for MDI client import
        assert any("mdi_client.dart" in imp for imp in imports)

        # Material should always be imported
        assert any("flutter/material.dart" in imp for imp in imports)

    def test_all_pb_control_types_mapped(self, ui_converter):
        """Test that all PowerBuilder control types from constants are mapped."""
        from src.parse.constants import PB_CONTROL_TYPES

        # Controls that have different names or are aliases
        control_aliases = {
            "edit": "singlelineedit",  # 'edit' is an alias for singlelineedit
        }

        unmapped_controls = []

        for pb_control in PB_CONTROL_TYPES:
            # Check if control is mapped directly or through alias
            control_name = control_aliases.get(pb_control, pb_control)

            if control_name not in ui_converter.control_map:
                unmapped_controls.append(pb_control)

        # All controls should be mapped
        assert len(unmapped_controls) == 0, f"Unmapped controls: {unmapped_controls}"

    def test_unknown_control_handling(self, ui_converter):
        """Test handling of unknown control types."""
        result = ui_converter.convert_control(
            "unknowncontrol",
            "unk_test",
            {"someprop": "value"},
        )

        assert result["widget"] == "Container"
        assert result["unknown"] is True
        assert "TODO: Implement unknowncontrol" in result["flutter_properties"]["child"]
