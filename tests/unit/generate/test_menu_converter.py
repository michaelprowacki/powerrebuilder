"""Test suite for MenuConverter."""

import pytest

from src.generate.converters.flutter.menus import (
    MenuConverter,
    MenuDefinition,
    MenuItem,
)


class TestMenuConverter:
    """Test cases for PowerBuilder to Flutter/Python menu conversion."""

    def setup_method(self):
        """Set up test instances."""
        self.converter = MenuConverter()

    def test_initialization(self):
        """Test converter initialization."""
        assert self.converter is not None

    def test_parse_simple_menu(self):
        """Test parsing a simple menu definition."""
        menu_syntax = """
            forward
            global type m_main from menu
            end type
            end forward

            global type m_main from menu
            m_file m_file
            m_edit m_edit
            m_help m_help
            end type
            global m_main m_main

            type m_file from menu
                m_new m_new
                m_open m_open
                m_save m_save
                m_exit m_exit
            end type

            on m_file.create
                this.text = "&File"
                this.m_new = create m_new
                this.m_open = create m_open
                this.m_save = create m_save
                this.m_exit = create m_exit
            end on
        """

        menu_def = self.converter.parse_menu(menu_syntax, "m_main")

        assert menu_def is not None
        assert menu_def.name == "m_main"
        assert len(menu_def.menu_bar) > 0

        # Find File menu
        file_menu = next((m for m in menu_def.menu_bar if m.name == "m_file"), None)
        assert file_menu is not None
        assert file_menu.text == "&File"

    def test_parse_menu_item_properties(self):
        """Test parsing menu item properties."""
        menu_syntax = """
            type m_save from menu
            end type

            on m_save.create
                this.text = "&Save"
                this.shortcut = "Ctrl+S"
                this.enabled = true
                this.visible = true
                this.checked = false
                this.microhelp = "Save the current document"
            end on

            event clicked()
                // Save action
                save_document()
            end event
        """

        item = self.converter._parse_menu_item(menu_syntax)

        assert item is not None
        assert item.text == "&Save"
        assert item.shortcut == "Ctrl+S"
        assert item.enabled is True
        assert item.visible is True
        assert item.checked is False
        assert item.on_click == "save_document()"

    def test_parse_nested_menu(self):
        """Test parsing nested menu structure."""
        menu_syntax = """
            type m_edit from menu
                m_cut m_cut
                m_copy m_copy
                m_paste m_paste
                m_separator1 m_separator1
                m_find m_find
                m_replace m_replace
            end type

            on m_edit.create
                this.text = "&Edit"
                this.m_cut = create m_cut
                this.m_copy = create m_copy
                this.m_paste = create m_paste
                this.m_separator1 = create m_separator1
                this.m_find = create m_find
                this.m_replace = create m_replace
            end on

            type m_cut from menu
            end type

            on m_cut.create
                this.text = "Cu&t"
                this.shortcut = "Ctrl+X"
            end on
        """

        menu_def = MenuDefinition(name="test")
        self.converter._parse_menu_structure(menu_syntax, menu_def)

        # Should have Edit menu with children
        edit_menu = next((m for m in menu_def.menu_bar if m.name == "m_edit"), None)
        assert edit_menu is not None
        assert len(edit_menu.children) >= 2  # At least cut and copy

    def test_menu_item_to_dict(self):
        """Test MenuItem to_dict conversion."""
        item = MenuItem(
            name="m_save",
            text="&Save",
            shortcut="Ctrl+S",
            enabled=True,
            visible=True,
            on_click="save_file()",
        )

        item_dict = item.to_dict()

        assert item_dict["name"] == "m_save"
        assert item_dict["text"] == "&Save"
        assert item_dict["shortcut"] == "Ctrl+S"
        assert item_dict["enabled"] is True
        assert item_dict["on_click"] == "save_file()"
        assert item_dict["has_children"] is False

        # Check Flutter shortcut conversion
        assert "flutter_shortcut" in item_dict
        flutter_shortcut = item_dict["flutter_shortcut"]
        assert "control" in flutter_shortcut["modifiers"]
        assert flutter_shortcut["key"] == "s"

        # Check Python shortcut conversion
        assert "python_shortcut" in item_dict
        assert item_dict["python_shortcut"] == "<Control-S>"

    def test_shortcut_conversion_flutter(self):
        """Test PowerBuilder to Flutter shortcut conversion."""
        test_cases = [
            ("Ctrl+S", {"modifiers": ["control"], "key": "s"}),
            ("Alt+F", {"modifiers": ["alt"], "key": "f"}),
            ("Shift+F1", {"modifiers": ["shift"], "key": "f1"}),
            ("Ctrl+Shift+N", {"modifiers": ["control", "shift"], "key": "n"}),
            ("F5", {"modifiers": [], "key": "f5"}),
        ]

        for pb_shortcut, expected in test_cases:
            item = MenuItem(name="test", text="Test", shortcut=pb_shortcut)
            result = item._convert_shortcut_to_flutter(pb_shortcut)
            assert result == expected

    def test_shortcut_conversion_python(self):
        """Test PowerBuilder to Python/Tkinter shortcut conversion."""
        test_cases = [
            ("Ctrl+S", "<Control-S>"),
            ("Alt+F", "<Alt-F>"),
            ("Shift+Delete", "<Shift-Delete>"),
            ("F1", "<F1>"),
            ("Ctrl+Alt+D", "<Control-<Alt-D>>"),
        ]

        for pb_shortcut, expected in test_cases:
            item = MenuItem(name="test", text="Test", shortcut=pb_shortcut)
            result = item._convert_shortcut_to_python(pb_shortcut)
            assert result == expected

    def test_convert_to_flutter(self):
        """Test converting menu to Flutter format."""
        menu_def = MenuDefinition(name="m_main")

        # Add File menu
        file_menu = MenuItem(
            name="m_file",
            text="&File",
            children=[
                MenuItem(
                    name="m_new", text="&New", shortcut="Ctrl+N", on_click="new_file()"
                ),
                MenuItem(
                    name="m_open",
                    text="&Open",
                    shortcut="Ctrl+O",
                    on_click="open_file()",
                ),
                MenuItem(
                    name="m_save",
                    text="&Save",
                    shortcut="Ctrl+S",
                    on_click="save_file()",
                ),
                MenuItem(name="m_separator", text="-"),
                MenuItem(name="m_exit", text="E&xit", on_click="exit_app()"),
            ],
        )
        menu_def.menu_bar.append(file_menu)

        flutter_data = self.converter.convert_to_flutter(menu_def)

        assert flutter_data is not None
        assert flutter_data["name"] == "m_main"
        assert flutter_data["has_menu_bar"] is True
        assert len(flutter_data["menu_bar"]) == 1
        assert flutter_data["menu_bar"][0]["has_children"] is True

    def test_convert_to_python(self):
        """Test converting menu to Python format."""
        menu_def = MenuDefinition(name="m_main")

        # Add Edit menu
        edit_menu = MenuItem(
            name="m_edit",
            text="&Edit",
            children=[
                MenuItem(name="m_undo", text="&Undo", shortcut="Ctrl+Z"),
                MenuItem(name="m_redo", text="&Redo", shortcut="Ctrl+Y"),
            ],
        )
        menu_def.menu_bar.append(edit_menu)

        python_data = self.converter.convert_to_python(menu_def)

        assert python_data is not None
        assert python_data["name"] == "m_main"
        assert python_data["has_menu_bar"] is True
        assert len(python_data["menu_bar"]) == 1

    def test_separator_handling(self):
        """Test handling of menu separators."""
        menu_syntax = """
            type m_separator1 from menu
            end type

            on m_separator1.create
                this.text = "-"
            end on
        """

        item = self.converter._parse_menu_item(menu_syntax)

        assert item is not None
        assert item.text == "-"
        assert item.name == "m_separator1"

    def test_menu_with_icons(self):
        """Test parsing menu items with icons."""
        menu_syntax = """
            type m_new from menu
            end type

            on m_new.create
                this.text = "&New"
                this.toolbaritemname = "new!"
                this.toolbaritemicon = "new_document.ico"
            end on
        """

        item = self.converter._parse_menu_item(menu_syntax)

        assert item is not None
        assert item.icon == "new_document.ico"

    def test_context_menu_parsing(self):
        """Test parsing context menus."""
        menu_syntax = """
            global type m_context from menu
            m_cut m_cut
            m_copy m_copy
            m_paste m_paste
            end type

            on m_context.create
                this.text = "Context Menu"
                this.menustyle = contemporary!
            end on
        """

        menu_def = self.converter.parse_menu(menu_syntax, "m_context")

        assert menu_def is not None
        assert menu_def.name == "m_context"

    def test_menu_event_handlers(self):
        """Test parsing menu event handlers."""
        menu_syntax = """
            event clicked()
                MessageBox("Info", "Menu clicked")
                parent.perform_action()
            end event

            event selected()
                // Update status bar
                w_main.set_status("Ready")
            end event
        """

        events = self.converter._parse_menu_events(menu_syntax)

        assert "clicked" in events
        assert "selected" in events
        assert "MessageBox" in events["clicked"]
        assert "w_main.set_status" in events["selected"]

    def test_complex_menu_structure(self):
        """Test parsing complex menu with multiple levels."""
        menu_def = MenuDefinition(name="m_complex")

        # Build complex menu structure
        view_menu = MenuItem(
            name="m_view",
            text="&View",
            children=[
                MenuItem(name="m_toolbar", text="&Toolbar", checked=True),
                MenuItem(name="m_statusbar", text="&Status Bar", checked=True),
                MenuItem(name="m_separator", text="-"),
                MenuItem(
                    name="m_zoom",
                    text="&Zoom",
                    children=[
                        MenuItem(name="m_zoom_in", text="Zoom &In", shortcut="Ctrl++"),
                        MenuItem(
                            name="m_zoom_out", text="Zoom &Out", shortcut="Ctrl+-"
                        ),
                        MenuItem(name="m_zoom_100", text="&100%", shortcut="Ctrl+0"),
                    ],
                ),
            ],
        )
        menu_def.menu_bar.append(view_menu)

        # Convert and verify structure
        flutter_data = self.converter.convert_to_flutter(menu_def)

        view_menu_data = flutter_data["menu_bar"][0]
        assert view_menu_data["has_children"] is True

        # Find zoom submenu
        zoom_menu = next(
            (c for c in view_menu_data["children"] if c["name"] == "m_zoom"), None
        )
        assert zoom_menu is not None
        assert zoom_menu["has_children"] is True
        assert len(zoom_menu["children"]) == 3

    def test_empty_menu(self):
        """Test handling empty menu definition."""
        menu_syntax = """
            global type m_empty from menu
            end type
            global m_empty m_empty
        """

        menu_def = self.converter.parse_menu(menu_syntax, "m_empty")

        assert menu_def is not None
        assert menu_def.name == "m_empty"
        assert len(menu_def.menu_bar) == 0

    def test_menu_text_with_mnemonics(self):
        """Test handling menu text with mnemonics."""
        test_cases = [
            ("&File", "File", "F"),
            ("&Edit", "Edit", "E"),
            ("Sa&ve", "Save", "v"),
            ("E&xit", "Exit", "x"),
            ("&&Escaped", "&Escaped", None),  # Double ampersand
        ]

        for text, expected_clean, expected_mnemonic in test_cases:
            clean_text, mnemonic = self.converter._extract_mnemonic(text)
            assert clean_text == expected_clean
            assert mnemonic == expected_mnemonic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
