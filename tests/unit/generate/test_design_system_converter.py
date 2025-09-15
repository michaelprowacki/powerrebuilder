"""Test suite for DesignSystemConverter."""

import pytest

from src.generate.converters.flutter.themes import (
    DesignSystemConverter,
    GlassmorphicStyle,
    IconMapping,
)


class TestGlassmorphicStyle:
    """Test cases for GlassmorphicStyle."""

    def test_default_values(self):
        """Test default glassmorphic style values."""
        style = GlassmorphicStyle()

        assert style.blur == 20.0
        assert style.opacity == 0.1
        assert style.border_opacity == 0.2
        assert style.border_width == 1.5
        assert style.light_intensity == 1.2
        assert style.thickness == 10.0
        assert style.border_radius == 20.0

    def test_custom_values(self):
        """Test custom glassmorphic style values."""
        style = GlassmorphicStyle(
            blur=30.0,
            opacity=0.15,
            border_radius=12.0,
        )

        assert style.blur == 30.0
        assert style.opacity == 0.15
        assert style.border_radius == 12.0

    def test_to_flutter_conversion(self):
        """Test conversion to Flutter properties."""
        style = GlassmorphicStyle(opacity=0.2, border_opacity=0.3)
        flutter_props = style.to_flutter()

        assert flutter_props["blur"] == 20.0
        assert "linearGradient" in flutter_props
        assert "borderGradient" in flutter_props
        assert flutter_props["border"] == 1.5
        assert flutter_props["borderRadius"] == 20.0

        # Check gradient colors
        gradient = flutter_props["linearGradient"]
        assert "withOpacity(0.2)" in gradient["colors"][0]
        assert "withOpacity(0.1)" in gradient["colors"][1]
        assert gradient["stops"] == [0.1, 1.0]


class TestIconMapping:
    """Test cases for IconMapping."""

    def test_material_icon_mapping(self):
        """Test Material icon mapping."""
        mapping = IconMapping(
            pb_name="save",
            modern_icon="save",
            icon_library="material",
            keywords=["save", "disk"],
        )

        assert mapping.to_flutter_code() == "Icons.save"
        assert mapping.to_flutter_import() == "import 'package:flutter/material.dart';"

    def test_cupertino_icon_mapping(self):
        """Test Cupertino icon mapping."""
        mapping = IconMapping(
            pb_name="settings",
            modern_icon="settings",
            icon_library="cupertino",
        )

        assert mapping.to_flutter_code() == "CupertinoIcons.settings"
        assert mapping.to_flutter_import() == "import 'package:flutter/cupertino.dart';"

    def test_sf_symbols_icon_mapping(self):
        """Test SF Symbols icon mapping."""
        mapping = IconMapping(
            pb_name="share",
            modern_icon="sf_square_and_arrow_up",
            icon_library="sf_symbols",
        )

        assert mapping.to_flutter_code() == "SFIcons.sf_square_and_arrow_up"
        assert (
            mapping.to_flutter_import()
            == "import 'package:flutter_sficon/flutter_sficon.dart';"
        )

    def test_custom_icon_mapping(self):
        """Test custom icon mapping."""
        mapping = IconMapping(
            pb_name="logo",
            modern_icon="company_logo",
            icon_library="custom",
        )

        assert mapping.to_flutter_code() == "CustomIcons.company_logo"
        assert mapping.to_flutter_import() is None


class TestDesignSystemConverter:
    """Test cases for DesignSystemConverter."""

    def setup_method(self):
        """Set up test instances."""
        self.converter = DesignSystemConverter(design_theme="liquid_glass")

    def test_initialization(self):
        """Test converter initialization."""
        assert self.converter is not None
        assert self.converter.design_theme == "liquid_glass"
        assert len(self.converter.icon_mappings) > 0
        assert len(self.converter.glass_styles) > 0

    def test_different_themes(self):
        """Test initialization with different themes."""
        material_converter = DesignSystemConverter(design_theme="material")
        assert material_converter.design_theme == "material"

        fluent_converter = DesignSystemConverter(design_theme="fluent")
        assert fluent_converter.design_theme == "fluent"

    def test_glass_styles_for_controls(self):
        """Test predefined glass styles for different controls."""
        assert "window" in self.converter.glass_styles
        assert "button" in self.converter.glass_styles
        assert "panel" in self.converter.glass_styles
        assert "dialog" in self.converter.glass_styles
        assert "datawindow" in self.converter.glass_styles

        # Check window has higher blur
        window_style = self.converter.glass_styles["window"]
        button_style = self.converter.glass_styles["button"]
        assert window_style.blur > button_style.blur

    def test_icon_mappings_loaded(self):
        """Test that common icon mappings are loaded."""
        # Check common file operations
        assert "new" in self.converter.icon_mappings
        assert "open" in self.converter.icon_mappings
        assert "save" in self.converter.icon_mappings

        # Check edit operations
        assert "cut" in self.converter.icon_mappings
        assert "copy" in self.converter.icon_mappings
        assert "paste" in self.converter.icon_mappings

        # Check navigation
        assert "first" in self.converter.icon_mappings
        assert "next" in self.converter.icon_mappings

    def test_extract_icon_key(self):
        """Test icon key extraction."""
        test_cases = [
            ("save.ico", "save"),
            ("pb_save_icon.png", "save"),
            ("btn_save_button.gif", "save"),
            ("icon_save.bmp", "save"),
            ("SAVE", "save"),
            ("C:\\icons\\save.ico", "save"),
            ("/usr/share/icons/save.png", "save"),
        ]

        for icon_name, expected in test_cases:
            result = self.converter._extract_icon_key(icon_name)
            assert result == expected

    def test_extract_keywords(self):
        """Test keyword extraction from icon name and context."""
        # Test without context
        keywords = self.converter._extract_keywords("save_document_icon")
        assert "save" in keywords
        assert "document" in keywords

        # Test with context
        context = {
            "control_type": "CommandButton",
            "action": "SaveFile",
            "tooltip": "Save the current document",
        }
        keywords = self.converter._extract_keywords("btn_save", context)
        assert "save" in keywords
        assert "commandbutton" in keywords
        assert "savefile" in keywords
        assert "current" in keywords

    def test_convert_icon_direct_mapping(self):
        """Test direct icon mapping conversion."""
        mapping = self.converter.convert_icon("save.ico")

        assert mapping is not None
        assert mapping.modern_icon == "save"
        assert mapping.icon_library == "material"
        assert mapping.confidence == 1.0

    def test_convert_icon_keyword_matching(self):
        """Test icon conversion via keyword matching."""
        mapping = self.converter.convert_icon("document_save_button.png")

        assert mapping is not None
        assert mapping.modern_icon == "save"
        assert mapping.confidence == 0.8  # Lower confidence for keyword match

    def test_convert_icon_contextual_fallback(self):
        """Test contextual fallback for unknown icons."""
        context = {"control_type": "DataWindow"}
        mapping = self.converter.convert_icon("unknown_icon.ico", context)

        assert mapping is not None
        assert mapping.modern_icon == "table_chart"
        assert mapping.icon_library == "material"
        assert mapping.confidence == 0.5

    def test_convert_icon_generic_fallback(self):
        """Test generic fallback for completely unknown icons."""
        mapping = self.converter.convert_icon("xyz123.ico")

        assert mapping is not None
        assert mapping.modern_icon == "help_outline"
        assert mapping.confidence == 0.3

    def test_apply_glassmorphism(self):
        """Test applying glassmorphism to controls."""
        properties = {
            "width": 200,
            "height": 100,
            "background_color": "Colors.blue",
        }

        enhanced = self.converter.apply_glassmorphism("button", properties)

        assert "glassmorphic" in enhanced
        assert enhanced["needs_backdrop_filter"] is True
        assert "border" in enhanced
        assert enhanced["border"]["gradient"] is True
        assert "withOpacity(0.1)" in enhanced["background_color"]

    def test_apply_glassmorphism_non_glass_theme(self):
        """Test that glassmorphism is not applied for non-glass themes."""
        material_converter = DesignSystemConverter(design_theme="material")
        properties = {"width": 200}

        enhanced = material_converter.apply_glassmorphism("button", properties)

        assert "glassmorphic" not in enhanced
        assert enhanced == properties  # Should be unchanged

    def test_generate_glass_container(self):
        """Test generating Flutter code for glass container."""
        control = {
            "width": 300,
            "height": 200,
            "glassmorphic": {
                "blur": 20,
                "borderRadius": 12,
                "border": 1.5,
                "linearGradient": {
                    "colors": [
                        "Color(0xFFFFFFFF).withOpacity(0.1)",
                        "Color(0xFFFFFFFF).withOpacity(0.05)",
                    ],
                    "stops": [0.1, 1.0],
                },
                "borderGradient": {
                    "colors": [
                        "Color(0xFFFFFFFF).withOpacity(0.2)",
                        "Color(0xFFFFFFFF).withOpacity(0.1)",
                    ],
                },
            },
        }

        lines = self.converter.generate_glass_container(control, "Text('Hello')")

        assert any("GlassmorphicContainer(" in line for line in lines)
        assert any("width: 300," in line for line in lines)
        assert any("height: 200," in line for line in lines)
        assert any("borderRadius: 12," in line for line in lines)
        assert any("blur: 20," in line for line in lines)
        assert any("child: Text('Hello')," in line for line in lines)

    def test_generate_regular_container(self):
        """Test generating regular container when no glassmorphism."""
        control = {
            "width": 100,
            "height": 50,
        }

        lines = self.converter.generate_glass_container(control, "Icon(Icons.save)")

        assert any("Container(" in line for line in lines)
        assert any("width: 100," in line for line in lines)
        assert any("height: 50," in line for line in lines)
        assert any("child: Icon(Icons.save)," in line for line in lines)

    def test_get_required_packages(self):
        """Test getting required Flutter packages."""
        packages = self.converter.get_required_packages()

        assert "glassmorphism: ^3.0.0" in packages

        # Add SF Symbols icon to mappings to test package detection
        self.converter.icon_mappings["test"] = IconMapping(
            pb_name="test",
            modern_icon="sf_test",
            icon_library="sf_symbols",
        )

        packages = self.converter.get_required_packages()
        assert any("flutter_sficon" in pkg for pkg in packages)

    def test_generate_theme_extensions_glass(self):
        """Test generating theme extensions for glass theme."""
        extensions = self.converter.generate_theme_extensions()

        assert "colors" in extensions
        assert "decorations" in extensions
        assert "animations" in extensions

        # Check glass colors
        assert any("glassBackground" in color for color in extensions["colors"])
        assert any("glassBorder" in color for color in extensions["colors"])

        # Check glass decorations
        assert any("glassDecoration" in dec for dec in extensions["decorations"])

        # Check animations
        assert any(
            "glassAnimationDuration" in anim for anim in extensions["animations"]
        )

    def test_generate_theme_extensions_non_glass(self):
        """Test theme extensions for non-glass themes."""
        material_converter = DesignSystemConverter(design_theme="material")
        extensions = material_converter.generate_theme_extensions()

        # Should have empty or minimal extensions
        assert all(len(values) == 0 for values in extensions.values())

    def test_icon_mapping_case_insensitive(self):
        """Test that icon mapping is case-insensitive."""
        test_cases = ["SAVE", "Save", "save", "SaVe"]

        for icon_name in test_cases:
            mapping = self.converter.convert_icon(icon_name)
            assert mapping.modern_icon == "save"

    def test_multiple_keyword_matches(self):
        """Test handling multiple keyword matches."""
        # Both 'new' and 'create' are keywords for the add_box icon
        mapping = self.converter.convert_icon("create_new_document.png")

        assert mapping is not None
        assert mapping.modern_icon in [
            "add_box",
            "add_circle_outline",
        ]  # Could match either
        assert mapping.confidence == 0.8

    def test_icon_mapping_with_all_contexts(self):
        """Test icon mapping with various control type contexts."""
        control_contexts = [
            ("commandbutton", "touch_app"),
            ("datawindow", "table_chart"),
            ("treeview", "account_tree"),
            ("listbox", "list"),
            ("dropdown", "arrow_drop_down"),
            ("checkbox", "check_box_outline_blank"),
            ("radiobutton", "radio_button_unchecked"),
        ]

        for control_type, expected_icon in control_contexts:
            context = {"control_type": control_type}
            mapping = self.converter.convert_icon("unknown.ico", context)
            assert mapping.modern_icon == expected_icon
            assert mapping.confidence == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
