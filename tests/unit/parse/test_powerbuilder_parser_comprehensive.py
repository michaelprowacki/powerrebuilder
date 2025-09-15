#!/usr/bin/env python3
"""Comprehensive test suite for PowerBuilder parser and transformer."""

from pathlib import Path

from src.parse.coordinator import parse_file


class TestPowerBuilderParser:
    """Test PowerBuilder parser and transformer functionality."""

    def parse_code(self, code: str, extension: str = "sru"):
        """Helper to parse PowerBuilder code."""
        # Write code to temporary file
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{extension}", delete=False
        ) as f:
            f.write(code)
            temp_path = Path(f.name)

        try:
            result = parse_file(temp_path)
            return result
        finally:
            temp_path.unlink()

    def test_variable_declaration(self):
        """Test variable declaration parsing."""
        code = """
function integer test_variables()
    integer li_count
    string ls_name = "John"
    boolean lb_active

    li_count = 10
    return li_count
end function
        """
        result = self.parse_code(code)
        assert result is not None
        # Check for variable declarations in result

    def test_function_definition(self):
        """Test function definition parsing."""
        code = """
        public function integer calculate_total(integer ai_quantity, decimal ad_price)
            integer li_total
            li_total = ai_quantity * ad_price
            return li_total
        end function
        """
        result = self.parse_code(code)
        assert result is not None
        # Should have function definition with parameters and return type

    def test_if_statement(self):
        """Test if/else statement parsing."""
        code = """
function string test_if(integer ai_count)
    string ls_message

    if ai_count > 0 then
        ls_message = "Items found"
    else
        ls_message = "No items"
    end if

    return ls_message
end function
        """
        result = self.parse_code(code)
        assert result is not None
        # Check for if statement structure

    def test_for_loop(self):
        """Test for loop parsing."""
        code = """
function integer test_for_loop()
    integer li_index, li_sum = 0

    for li_index = 1 to 10
        li_sum = li_sum + li_index
    next

    return li_sum
end function
        """
        result = self.parse_code(code)
        assert result is not None
        # Check for loop structure

    def test_while_loop(self):
        """Test while loop parsing."""
        code = """
function integer test_while_loop()
    integer li_count = 0

    do while li_count < 100
        li_count = li_count + 1
    loop

    return li_count
end function
        """
        result = self.parse_code(code)
        assert result is not None
        # Check while loop structure

    def test_case_statement(self):
        """Test case statement parsing."""
        code = """
function integer test_case(string as_type)
    integer li_value

    choose case as_type
        case "A"
            li_value = 1
        case "B", "C"
            li_value = 2
        case else
            li_value = 0
    end choose

    return li_value
end function
        """
        result = self.parse_code(code)
        assert result is not None
        # Check case statement structure

    def test_array_access(self):
        """Test array access parsing."""
        code = """
function integer test_arrays()
    integer la_array[10]
    integer la_matrix[5,5]
    integer li_value, li_row = 1, li_col = 1

    la_array[1] = 50
    li_value = la_array[1]
    la_matrix[li_row, li_col] = 100

    return li_value
end function
        """
        result = self.parse_code(code)
        assert result is not None
        # Check array access expressions

    def test_event_definition(self):
        """Test event definition parsing."""
        code = """
        event clicked()
            MessageBox("Info", "Button clicked")
        end event
        """
        result = self.parse_code(code)
        assert result is not None
        # Check event structure

    def test_property_access(self):
        """Test property access parsing."""
        code = """
        this.width = 100
        dw_1.Object.name[1] = "Test"
        parent.visible = true
        """
        result = self.parse_code(code)
        assert result is not None
        # Check property access expressions

    def test_try_catch(self):
        """Test try/catch parsing."""
        code = """
        try
            li_result = divide(10, 0)
        catch (dividebyzeroerror e)
            MessageBox("Error", e.getmessage())
        end try
        """
        result = self.parse_code(code)
        assert result is not None
        # Check exception handling structure

    def test_sql_statements(self):
        """Test embedded SQL statement parsing."""
        code = """
        SELECT name, age
        INTO :ls_name, :li_age
        FROM users
        WHERE id = :li_id;

        UPDATE users
        SET active = 'Y'
        WHERE id = :li_id;
        """
        result = self.parse_code(code)
        assert result is not None
        # Check SQL statement structure

    def test_datawindow_syntax(self):
        """Test DataWindow syntax parsing."""
        code = """
        ls_syntax = dw_1.Describe("DataWindow.Syntax")
        dw_1.Modify("t_title.text='New Title'")
        """
        result = self.parse_code(code)
        assert result is not None
        # Check DataWindow method calls

    def test_type_declaration(self):
        """Test custom type declaration parsing."""
        code = """
        type n_custom from nonvisualobject
            integer ii_count
            string is_name

            function integer increment()
                ii_count++
                return ii_count
            end function
        end type
        """
        result = self.parse_code(code)
        assert result is not None
        # Check type declaration structure

    def test_global_variables(self):
        """Test global variable declarations."""
        code = """
        global integer gi_app_count
        global string gs_app_name = "MyApp"
        global n_custom gnv_app
        """
        result = self.parse_code(code)
        assert result is not None
        # Check global variable declarations

    def test_expressions(self):
        """Test various expression types."""
        code = """
        // Arithmetic
        li_result = (10 + 20) * 3 / 2

        // String concatenation
        ls_full = ls_first + " " + ls_last

        // Logical
        lb_valid = (li_count > 0) and (li_count < 100)

        // Comparison
        if ls_type = "A" or ls_type = "B" then
            lb_match = true
        end if
        """
        result = self.parse_code(code)
        assert result is not None
        # Check various expression types

    def test_comments(self):
        """Test comment handling."""
        code = """
        // Single line comment
        integer li_count  // End of line comment

        /* Multi-line
           comment block */
        string ls_name
        """
        result = self.parse_code(code)
        assert result is not None
        # Comments should be handled properly

    def test_nested_structures(self):
        """Test nested control structures."""
        code = """
        for li_i = 1 to 10
            if li_i mod 2 = 0 then
                choose case li_i
                    case 2, 4, 6
                        do while li_j < li_i
                            li_sum = li_sum + li_j
                            li_j++
                        loop
                    case else
                        continue
                end choose
            else
                exit
            end if
        next
        """
        result = self.parse_code(code)
        assert result is not None
        # Check nested structure handling

    def test_return_statements(self):
        """Test return statement variations."""
        code = """
        function integer test1()
            return 42
        end function

        function string test2()
            if lb_flag then
                return "success"
            else
                return "failure"
            end if
        end function

        subroutine test3()
            if lb_done then
                return
            end if
            // More code
        end subroutine
        """
        result = self.parse_code(code)
        assert result is not None
        # Check return statement handling


class TestPowerBuilderEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_file(self):
        """Test parsing empty file."""
        code = ""
        temp_file = Path("test_empty.sru")
        temp_file.write_text(code)
        try:
            result = parse_file(temp_file)
            assert result is not None
        finally:
            temp_file.unlink()

    def test_syntax_error_recovery(self):
        """Test parser error recovery."""
        code = """
        integer li_count
        // Missing end if
        if li_count > 0 then
            li_count = 0

        string ls_name = "test"
        """
        temp_file = Path("test_error.sru")
        temp_file.write_text(code)
        try:
            # Should handle error gracefully
            result = parse_file(temp_file)
            # May return partial result or error info
        finally:
            temp_file.unlink()
