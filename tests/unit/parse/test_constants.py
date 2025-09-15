"""Unit tests for PowerBuilder parsing constants."""

import pytest

from src.parse.constants import (
    COMMON_GRAMMAR,
    DATAWINDOW_GRAMMAR,
    FILE_EXTENSIONS,
    PB_BASIC_TYPES,
    PB_CONTROL_TYPES,
    PB_EVENT_TYPES,
    PB_KEYWORDS,
    PB_SYSTEM_TYPES,
    POWERBUILDER_GRAMMAR,
    SQL_GRAMMAR,
    SQL_KEYWORDS,
    FileType,
)


class TestPowerBuilderConstants:
    """Test PowerBuilder constant definitions."""

    def test_keywords_defined(self):
        """Test that keywords are properly defined."""
        assert len(PB_KEYWORDS) > 0

        # Check for common keywords
        assert "if" in PB_KEYWORDS
        assert "then" in PB_KEYWORDS
        assert "else" in PB_KEYWORDS
        assert "end" in PB_KEYWORDS
        assert "for" in PB_KEYWORDS
        assert "next" in PB_KEYWORDS
        assert "function" in PB_KEYWORDS
        assert "return" in PB_KEYWORDS

    def test_basic_types_defined(self):
        """Test that basic types are properly defined."""
        assert len(PB_BASIC_TYPES) > 0

        # Check for basic types
        assert "integer" in PB_BASIC_TYPES
        assert "string" in PB_BASIC_TYPES
        assert "boolean" in PB_BASIC_TYPES
        assert "date" in PB_BASIC_TYPES
        assert "decimal" in PB_BASIC_TYPES
        assert "long" in PB_BASIC_TYPES
        assert "real" in PB_BASIC_TYPES
        assert "char" in PB_BASIC_TYPES

    def test_system_types_defined(self):
        """Test that system types are properly defined."""
        assert len(PB_SYSTEM_TYPES) > 0

        # Check for system types
        assert "powerobject" in PB_SYSTEM_TYPES
        assert "window" in PB_SYSTEM_TYPES
        assert "transaction" in PB_SYSTEM_TYPES
        assert "menu" in PB_SYSTEM_TYPES
        assert "datastore" in PB_SYSTEM_TYPES

    def test_control_types_defined(self):
        """Test that control types are properly defined."""
        assert len(PB_CONTROL_TYPES) > 0

        # Check for control types
        assert "commandbutton" in PB_CONTROL_TYPES
        assert "datawindow" in PB_CONTROL_TYPES
        assert "edit" in PB_CONTROL_TYPES
        assert "statictext" in PB_CONTROL_TYPES
        assert "checkbox" in PB_CONTROL_TYPES
        assert "listview" in PB_CONTROL_TYPES

    def test_event_types_defined(self):
        """Test that event types are properly defined."""
        assert len(PB_EVENT_TYPES) > 0

        # Check for event types
        assert "clicked" in PB_EVENT_TYPES
        assert "doubleclicked" in PB_EVENT_TYPES
        assert "create" in PB_EVENT_TYPES
        assert "destroy" in PB_EVENT_TYPES
        assert "getfocus" in PB_EVENT_TYPES
        assert "losefocus" in PB_EVENT_TYPES

    def test_sql_keywords_defined(self):
        """Test that SQL keywords are properly defined."""
        assert len(SQL_KEYWORDS) > 0

        # Check for SQL keywords
        assert "select" in SQL_KEYWORDS
        assert "insert" in SQL_KEYWORDS
        assert "update" in SQL_KEYWORDS
        assert "delete" in SQL_KEYWORDS
        assert "where" in SQL_KEYWORDS
        assert "from" in SQL_KEYWORDS

    def test_file_extensions_defined(self):
        """Test that file extensions are properly defined."""
        assert len(FILE_EXTENSIONS) > 0

        # Check for common extensions
        assert "pbl" in FILE_EXTENSIONS
        assert "pbd" in FILE_EXTENSIONS
        assert "sru" in FILE_EXTENSIONS
        assert "srw" in FILE_EXTENSIONS
        assert "srd" in FILE_EXTENSIONS

        # Check mappings
        assert FILE_EXTENSIONS["pbl"] == FileType.LIBRARY
        assert FILE_EXTENSIONS["pbd"] == FileType.LIBRARY
        assert FILE_EXTENSIONS["sru"] == FileType.USER_OBJECT
        assert FILE_EXTENSIONS["srw"] == FileType.WINDOW
        assert FILE_EXTENSIONS["srd"] == FileType.DATAWINDOW

    def test_grammar_paths_exist(self):
        """Test that grammar file paths are defined."""
        # Check that paths are defined
        assert POWERBUILDER_GRAMMAR is not None
        assert COMMON_GRAMMAR is not None
        assert DATAWINDOW_GRAMMAR is not None
        assert SQL_GRAMMAR is not None

        # Check file extensions
        assert str(POWERBUILDER_GRAMMAR).endswith(".lark")
        assert str(COMMON_GRAMMAR).endswith(".lark")
        assert str(DATAWINDOW_GRAMMAR).endswith(".lark")
        assert str(SQL_GRAMMAR).endswith(".lark")

    def test_filetype_enum(self):
        """Test FileType enum."""
        # Check enum values exist
        assert FileType.WINDOW
        assert FileType.USER_OBJECT
        assert FileType.FUNCTION
        assert FileType.MENU
        assert FileType.STRUCTURE
        assert FileType.QUERY
        assert FileType.APPLICATION
        assert FileType.DATAWINDOW
        assert FileType.PROJECT
        assert FileType.LIBRARY
        assert FileType.UNKNOWN

        # Check that each has a unique value
        values = [ft.value for ft in FileType]
        assert len(values) == len(set(values))

    def test_type_aliases(self):
        """Test that type aliases are included."""
        # Integer aliases
        assert "int" in PB_BASIC_TYPES
        assert "uint" in PB_BASIC_TYPES
        assert "ulong" in PB_BASIC_TYPES

        # String aliases
        assert "char" in PB_BASIC_TYPES
        assert "character" in PB_BASIC_TYPES

        # Boolean aliases
        assert "bool" in PB_BASIC_TYPES

        # Decimal aliases
        assert "dec" in PB_BASIC_TYPES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
