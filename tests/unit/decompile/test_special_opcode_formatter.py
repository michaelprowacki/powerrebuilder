#!/usr/bin/env python3
"""Test special opcode formatting for decompiled code."""

from src.decompile.core.opcode_formatter import SpecialOpcodeFormatter


class TestSpecialOpcodeFormatter:
    """Test the special opcode formatter."""

    def test_database_operations(self):
        """Test formatting of database operations."""
        formatter = SpecialOpcodeFormatter(
            string_table={
                1: "SELECT * FROM customers WHERE id = ?",
                2: "customers",
                3: "UPDATE customers SET name = ? WHERE id = ?",
            },
        )

        # Test DBOPEN
        result = formatter.format_opcode("DBOPEN", [1], None)
        assert result == "OPEN cursor_1"

        # Test DBCLOSE
        result = formatter.format_opcode("DBCLOSE", [2], None)
        assert result == "CLOSE cursor_2"

        # Test DBSELECT with SQL string
        result = formatter.format_opcode("DBSELECT", [5, 1, 1], None)
        assert result == "SELECT /* 5 columns */ SELECT * FROM customers WHERE id = ?"

        # Test DBINSERT
        result = formatter.format_opcode("DBINSERT", [2], None)
        assert result == "INSERT INTO customers"

        # Test DBUPDATE
        result = formatter.format_opcode("DBUPDATE", [2], None)
        assert result == "UPDATE customers SET ..."

        # Test DBDELETE
        result = formatter.format_opcode("DBDELETE", [2], None)
        assert result == "DELETE FROM customers"

        # Test DBEXECUTE
        result = formatter.format_opcode("DBEXECUTE", [3], None)
        assert result == "EXECUTE IMMEDIATE UPDATE customers SET name = ? WHERE id = ?"

        # Test DBCOMMIT
        result = formatter.format_opcode("DBCOMMIT", [], None)
        assert result == "COMMIT"

        # Test DBROLLBACK
        result = formatter.format_opcode("DBROLLBACK", [], None)
        assert result == "ROLLBACK"

    def test_control_flow_operations(self):
        """Test formatting of control flow operations."""
        formatter = SpecialOpcodeFormatter()

        # Test JUMP
        result = formatter.format_opcode("JUMP", [0x1234], None)
        assert result == "goto L_1234"

        # Test JUMPTRUE
        result = formatter.format_opcode("JUMPTRUE", [0x5678], None)
        assert result == "if (condition) goto L_5678"

        # Test JUMPFALSE
        result = formatter.format_opcode("JUMPFALSE", [0xABCD], None)
        assert result == "if not (condition) goto L_ABCD"

        # Test GOSUB
        result = formatter.format_opcode("GOSUB", [0xEF01], None)
        assert result == "gosub L_EF01"

    def test_function_calls(self):
        """Test formatting of function calls."""
        formatter = SpecialOpcodeFormatter(
            function_table={
                10: "calculate_total",
                20: "MessageBox",
                30: "GetCurrentDirectory",
            },
        )

        # Test global function call
        result = formatter.format_opcode("GLOBFUNCCALL", [10], None)
        assert result == "calculate_total() /* global function */"

        # Test DLL function call
        result = formatter.format_opcode("DLLFUNCCALL", [30], None)
        assert result == "GetCurrentDirectory() /* external function */"

        # Test system function call
        result = formatter.format_opcode("SYSFUNCCALL", [20], None)
        assert result == "MessageBox() /* system function */"

        # Test method call with arg count
        result = formatter.format_opcode("DOTFUNCCALL", [10, 3], None)
        assert result == "calculate_total() /* 3 args */ /* method function */"

    def test_array_operations(self):
        """Test formatting of array operations."""
        formatter = SpecialOpcodeFormatter()

        # Test ARRAYLIST
        result = formatter.format_opcode("ARRAYLIST", [10], None)
        assert result == "/* Create array list with 10 elements */"

        # Test BUILD_UNBOUNDED_ARRAYLIST
        result = formatter.format_opcode("BUILD_UNBOUNDED_ARRAYLIST", [], None)
        assert result == "/* Build unbounded array */"

        # Test LOWERBOUND
        result = formatter.format_opcode("LOWERBOUND", [], None)
        assert result == "LowerBound(array, dimension)"

        # Test UPPERBOUND
        result = formatter.format_opcode("UPPERBOUND", [], None)
        assert result == "UpperBound(array, dimension)"

    def test_exception_handling(self):
        """Test formatting of exception handling operations."""
        formatter = SpecialOpcodeFormatter()

        # Test PUSH_TRY
        result = formatter.format_opcode("PUSH_TRY", [], None)
        assert result == "TRY"

        # Test POP_TRY
        result = formatter.format_opcode("POP_TRY", [], None)
        assert result == "/* End TRY block */"

        # Test CATCH_EXCEPTION
        result = formatter.format_opcode("CATCH_EXCEPTION", [5], None)
        assert result == "CATCH (Exception_5 e)"

        # Test CATCH_EXCEPTION without type
        result = formatter.format_opcode("CATCH_EXCEPTION", [], None)
        assert result == "CATCH (Exception e)"

        # Test THROW_EXCEPTION
        result = formatter.format_opcode("THROW_EXCEPTION", [], None)
        assert result == "THROW"

    def test_event_calls(self):
        """Test formatting of event calls."""
        formatter = SpecialOpcodeFormatter(
            function_table={
                100: "clicked",
                200: "modified",
            },
        )

        # Test EVENTCALL
        result = formatter.format_opcode("EVENTCALL", [100, 50], None)
        assert result == "TriggerEvent('clicked')"

        # Test EVENTCALL without parameters
        result = formatter.format_opcode("EVENTCALL", [], None)
        assert result == "TriggerEvent()"

    def test_object_creation(self):
        """Test formatting of object creation operations."""
        formatter = SpecialOpcodeFormatter()

        # Test CREATE_EXT_OBJ
        result = formatter.format_opcode("CREATE_EXT_OBJ", [], None)
        assert result == "CREATE object"

        # Test CREATE_USING with stack context
        result = formatter.format_opcode("CREATE_USING", [], ["n_calculator"])
        assert result == "CREATE USING 'n_calculator'"

        # Test CREATE_USING without stack context
        result = formatter.format_opcode("CREATE_USING", [], None)
        assert result == "CREATE USING class_name"

    def test_unknown_opcodes(self):
        """Test that unknown opcodes return None."""
        formatter = SpecialOpcodeFormatter()

        # Test unknown opcode
        result = formatter.format_opcode("UNKNOWN_OP", [], None)
        assert result is None

        # Test opcode that doesn't need special formatting
        result = formatter.format_opcode("PUSH_LOCAL_VAR", [1], None)
        assert result is None
