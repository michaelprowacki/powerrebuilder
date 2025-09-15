#!/usr/bin/env python3
"""Test suite for extended UI control type mappings."""

import pytest

from src.generate.converters.flutter.widgets import UIConverter


class TestExtendedControlMappings:
    """Test the newly added UI control type mappings."""

    def test_editmask_control(self):
        """Test editmask control conversion."""
        converter = UIConverter()

        result = converter.convert_control(
            "editmask",
            "em_phone",
            {"mask": "(999) 999-9999", "text": ""},
        )

        assert result["widget"] == "TextField"
        assert result["requires_controller"] is True
        assert result["controller_type"] == "TextEditingController"
        assert "formatter" in converter.control_map["editmask"]

    def test_treeview_control(self):
        """Test treeview control conversion."""
        converter = UIConverter()

        result = converter.convert_control(
            "treeview",
            "tv_navigation",
            {"haslines": "true", "hasbuttons": "true"},
        )

        assert result["widget"] == "TreeView"
        assert result.get("custom") is True
        assert "_treeData" in converter.control_map["treeview"]["properties"]["items"]

    def test_listview_control(self):
        """Test listview control conversion."""
        converter = UIConverter()

        result = converter.convert_control(
            "listview",
            "lv_items",
            {"viewmode": "report", "sorted": "true"},
        )

        assert result["widget"] == "ListView"
        assert result.get("builder_pattern") == "ListView.builder"
        assert (
            "_columnDefinitions"
            in converter.control_map["listview"]["properties"]["columns"]
        )

    def test_graph_control(self):
        """Test graph control conversion."""
        converter = UIConverter()

        result = converter.convert_control(
            "graph",
            "gr_sales",
            {"graphtype": "column", "title": "Sales Chart"},
        )

        assert result["widget"] == "CustomChart"
        assert result.get("custom") is True
        assert "_chartType" in converter.control_map["graph"]["properties"]["graphtype"]

    def test_progressbar_controls(self):
        """Test progress bar control conversions."""
        converter = UIConverter()

        # Standard progressbar
        result = converter.convert_control(
            "progressbar",
            "pb_progress",
            {"position": "50", "maxposition": "100"},
        )
        assert result["widget"] == "LinearProgressIndicator"

        # Horizontal progressbar
        h_result = converter.convert_control(
            "hprogressbar",
            "hpb_progress",
            {"position": "25", "maxposition": "100"},
        )
        assert h_result["widget"] == "LinearProgressIndicator"

        # Vertical progressbar
        v_result = converter.convert_control(
            "vprogressbar",
            "vpb_progress",
            {"position": "75", "maxposition": "100"},
        )
        assert v_result["widget"] == "RotatedBox"
        assert v_result["is_container"] is True
        assert converter.control_map["vprogressbar"]["config"]["quarterTurns"] == 3

    def test_trackbar_controls(self):
        """Test trackbar/slider control conversions."""
        converter = UIConverter()

        # Horizontal trackbar
        h_result = converter.convert_control(
            "htrackbar",
            "htb_volume",
            {"position": "50", "minposition": "0", "maxposition": "100"},
        )
        assert h_result["widget"] == "Slider"

        # Vertical trackbar
        v_result = converter.convert_control(
            "vtrackbar",
            "vtb_volume",
            {"position": "30", "minposition": "0", "maxposition": "100"},
        )
        assert v_result["widget"] == "RotatedBox"
        assert "child_widget" in converter.control_map["vtrackbar"]

    def test_shape_controls(self):
        """Test shape control conversions."""
        converter = UIConverter()

        # Round rectangle
        rr_result = converter.convert_control(
            "roundrectangle",
            "rr_frame",
            {"cornerradius": "10", "fillcolor": "255"},
        )
        assert rr_result["widget"] == "Container"
        assert (
            "_borderRadius"
            in converter.control_map["roundrectangle"]["properties"]["cornerradius"]
        )

        # Oval
        oval_result = converter.convert_control(
            "oval",
            "ov_indicator",
            {"fillcolor": "16711680", "linecolor": "0"},
        )
        assert oval_result["widget"] == "Container"
        assert converter.control_map["oval"]["shape"] == "BoxShape.circle"

    def test_date_controls(self):
        """Test date/time control conversions."""
        converter = UIConverter()

        # Date picker
        dp_result = converter.convert_control(
            "datepicker",
            "dp_birthdate",
            {"value": "2023-01-01", "format": "yyyy-MM-dd"},
        )
        assert dp_result["widget"] == "DatePickerField"
        assert dp_result.get("custom") is True

        # Month calendar
        mc_result = converter.convert_control(
            "monthcalendar",
            "mc_appointments",
            {"selecteddate": "2023-06-15", "showtoday": "true"},
        )
        assert mc_result["widget"] == "TableCalendar"
        assert converter.control_map["monthcalendar"]["package"] == "table_calendar"

    def test_ink_controls(self):
        """Test ink/drawing control conversions."""
        converter = UIConverter()

        # Ink picture
        ip_result = converter.convert_control(
            "inkpicture",
            "ip_signature",
            {"inkcolor": "0", "inkwidth": "2"},
        )
        assert ip_result["widget"] == "CustomInkCanvas"
        assert ip_result.get("custom") is True

        # Ink edit
        ie_result = converter.convert_control(
            "inkedit",
            "ie_notes",
            {"recognitiontimeout": "1000"},
        )
        assert ie_result["widget"] == "CustomInkTextField"
        assert ie_result["requires_controller"] is True

    def test_animation_control(self):
        """Test animation control conversion."""
        converter = UIConverter()

        result = converter.convert_control(
            "animation",
            "ani_loader",
            {"animationfile": "loading.gif", "autoplay": "true"},
        )

        assert result["widget"] == "AnimatedBuilder"
        assert result.get("custom") is True
        assert result["controller_type"] == "AnimationController"

    def test_ole_control(self):
        """Test OLE control conversion."""
        converter = UIConverter()

        result = converter.convert_control(
            "ole",
            "ole_excel",
            {"classname": "Excel.Application", "activation": "inplace"},
        )

        assert result["widget"] == "Container"
        assert result["is_container"] is True
        assert result.get("custom") is True
        assert "placeholder" in converter.control_map["ole"]["config"]

    def test_get_widget_imports_extended(self):
        """Test import generation for extended controls."""
        converter = UIConverter()

        controls = [
            {"type": "editmask", "widget": "TextField", "name": "em_phone"},
            {"type": "monthcalendar", "widget": "TableCalendar", "name": "mc_cal"},
            {
                "type": "treeview",
                "widget": "TreeView",
                "name": "tv_nav",
                "custom": True,
            },
            {
                "type": "graph",
                "widget": "CustomChart",
                "name": "gr_sales",
                "custom": True,
            },
            {
                "type": "inkpicture",
                "widget": "CustomInkCanvas",
                "name": "ip_sig",
                "custom": True,
            },
        ]

        imports = converter.get_widget_imports(controls)

        # Check for expected imports
        assert "import 'package:flutter/material.dart';" in imports
        assert (
            "import 'package:flutter/services.dart';" in imports
        )  # For TextInputFormatter
        assert "import 'package:table_calendar/table_calendar.dart';" in imports
        assert "import '../widgets/tree_view.dart';" in imports
        assert "import '../widgets/custom_chart.dart';" in imports
        assert "import '../widgets/ink_controls.dart';" in imports

    def test_generate_widget_code_extended(self):
        """Test widget code generation for extended controls."""
        converter = UIConverter()

        # Test editmask
        editmask_control = {
            "type": "editmask",
            "widget": "TextField",
            "dart_name": "phone",
            "name": "em_phone",
        }
        code = converter._generate_widget_code(editmask_control)
        assert "inputFormatters: _phoneFormatters" in code

        # Test progress bar
        progress_control = {
            "type": "progressbar",
            "widget": "LinearProgressIndicator",
            "dart_name": "download",
            "name": "pb_download",
        }
        code = converter._generate_widget_code(progress_control)
        assert "LinearProgressIndicator(value: _downloadProgress)" in code

        # Test slider
        slider_control = {
            "type": "htrackbar",
            "widget": "Slider",
            "dart_name": "volume",
            "name": "htb_volume",
        }
        code = converter._generate_widget_code(slider_control)
        assert "Slider(value: _volumeValue, onChanged: _onVolumeChanged" in code

        # Test TreeView
        tree_control = {
            "type": "treeview",
            "widget": "TreeView",
            "dart_name": "navigation",
            "name": "tv_navigation",
        }
        code = converter._generate_widget_code(tree_control)
        assert "TreeView(data: _navigationTreeData)" in code

        # Test shape controls
        oval_control = {
            "type": "oval",
            "widget": "Container",
            "dart_name": "indicator",
            "name": "ov_indicator",
            "properties": {},
        }
        code = converter._generate_widget_code(oval_control)
        assert "BoxShape.circle" in code

    def test_unknown_control_fallback(self):
        """Test that unknown controls still get a reasonable fallback."""
        converter = UIConverter()

        # Test a control type that doesn't exist
        result = converter.convert_control(
            "customcontrol",
            "cc_special",
            {"property1": "value1"},
        )

        assert result["widget"] == "Container"
        assert result.get("unknown") is True
        assert "TODO: Implement customcontrol" in result["flutter_properties"]["child"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
