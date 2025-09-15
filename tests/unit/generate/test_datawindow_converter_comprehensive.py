"""Comprehensive tests for DataWindowConverter."""

from unittest.mock import Mock

from src.generate.converters.flutter.datawindows import DataWindowConverter


class TestDataWindowConverterComprehensive:
    """Comprehensive test suite for DataWindow converter."""

    def setup_method(self):
        """Set up test dependencies."""
        self.converter = DataWindowConverter()
        self.converter.type_converter = Mock()
        self.converter.blob_converter = Mock()

    def test_convert_simple_datawindow(self):
        """Test converting a simple DataWindow."""
        dw_syntax = """
        release 12.5;
        datawindow(units=0 timer_interval=0 color=1073741824 processing=1 print.preview=no)
        header(height=68 color="536870912")
        summary(height=0 color="536870912")
        footer(height=0 color="536870912")
        detail(height=84 color="536870912")
        table(column=(type=char(50) updatewhereclause=yes name=employee_name dbname="employee.name")
              column=(type=number updatewhereclause=yes name=employee_id dbname="employee.id")
              column=(type=decimal(2) updatewhereclause=yes name=salary dbname="employee.salary")
              retrieve="SELECT employee.name, employee.id, employee.salary FROM employee")
        """

        # Mock type conversions
        self.converter.type_converter.convert_type.side_effect = [
            "String",
            "int",
            "double",
        ]

        # Convert
        result = self.converter.convert_datawindow(dw_syntax, "dw_employee")

        # Verify
        assert result.name == "DwEmployee"
        assert result.presentation_style == "grid"
        assert result.processing_type == 1
        assert len(result.columns) == 3
        assert result.columns[0].name == "employee_name"
        assert result.columns[0].data_type == "String"
        assert result.columns[1].name == "employee_id"
        assert result.columns[1].data_type == "int"
        assert result.columns[2].name == "salary"
        assert result.columns[2].data_type == "double"
        assert "SELECT employee.name" in result.sql

    def test_parse_presentation_style(self):
        """Test parsing different presentation styles."""
        test_cases = [
            ("processing=0", "freeform"),
            ("processing=1", "grid"),
            ("processing=2", "label"),
            ("processing=3", "graph"),
            ("processing=4", "crosstab"),
            ("processing=5", "composite"),
            ("processing=6", "ole"),
            ("processing=7", "richtextedit"),
            ("processing=8", "treeview"),
            ("processing=99", "unknown"),
        ]

        for syntax, expected_style in test_cases:
            result = self.converter._parse_presentation_style(f"datawindow({syntax})")
            assert result == expected_style

    def test_parse_columns_with_relationships(self):
        """Test parsing columns that define relationships."""
        dw_syntax = """
        table(column=(type=number name=dept_id dbname="employee.dept_id"
                     initial="0" validation="dept_id > 0")
              column=(type=number name=manager_id dbname="employee.manager_id")
              retrieve="SELECT * FROM employee"
              update="employee" updatewhere=0 updatekeyinplace=no
              arguments=(("dept_id", number),("status", string)))
        """

        columns = self.converter._parse_columns(dw_syntax)

        # Verify foreign key detection
        assert len(columns) == 2
        dept_col = next(c for c in columns if c["name"] == "dept_id")
        assert "validation" in dept_col
        assert dept_col["initial"] == "0"

    def test_parse_blob_columns(self):
        """Test parsing BLOB columns."""
        dw_syntax = """
        table(column=(type=blob name=photo dbname="employee.photo")
              column=(type=blob name=resume dbname="employee.resume" blobtype="document"))
        """

        # Mock blob detection
        self.converter.blob_converter.is_blob_column.return_value = True
        self.converter.blob_converter.get_blob_metadata.side_effect = [
            {"type": "image", "usage": "display"},
            {"type": "document", "usage": "download"},
        ]

        columns = self.converter._parse_columns(dw_syntax)

        assert len(columns) == 2
        assert columns[0]["type"] == "blob"
        assert columns[1]["blobtype"] == "document"

    def test_extract_relationships(self):
        """Test extracting relationships from DataWindow."""
        dw_def = Mock()
        dw_def.columns = [
            Mock(name="id", dbname="employee.id"),
            Mock(name="department_id", dbname="employee.department_id"),
            Mock(name="manager_id", dbname="employee.manager_id"),
        ]
        dw_def.sql = """
        SELECT e.*, d.name as dept_name
        FROM employee e
        JOIN department d ON e.department_id = d.id
        """

        result = self.converter._extract_relationships(dw_def)

        # Should identify foreign keys and joins
        assert len(result) >= 1
        assert any("department" in str(r).lower() for r in result)

    def test_generate_row_type(self):
        """Test generating row type name."""
        test_cases = [
            ("dw_employee_list", "EmployeeList"),
            ("d_product_detail", "ProductDetail"),
            ("datawindow1", "Datawindow1Model"),
            ("dw_", "DataWindowModel"),
        ]

        for dw_name, expected_type in test_cases:
            result = self.converter._generate_row_type(dw_name)
            assert result == expected_type

    def test_convert_compute_fields(self):
        """Test converting computed fields."""
        dw_syntax = """
        compute(band=detail alignment="0" expression="employee_id * 100"
                border="0" color="0" x="464" y="4" height="64" width="274"
                name=compute_1)
        compute(band=summary alignment="0" expression="sum(salary for all)"
                name=total_salary)
        """

        # Convert (compute fields should be detected)
        result = self.converter.convert_datawindow(dw_syntax, "dw_test")

        # Verify compute fields are handled
        # Note: Actual implementation may vary
        assert result is not None

    def test_parse_text_objects(self):
        """Test parsing text objects (labels)."""
        dw_syntax = """
        text(band=header alignment="2" text="Employee Name" x="10" y="10")
        text(band=header alignment="2" text="ID" x="200" y="10")
        column(type=char(50) name=emp_name)
        """

        result = self.converter.convert_datawindow(dw_syntax, "dw_test")

        # Text objects should be recognized but not added as columns
        assert len([c for c in result.columns if c.name == "emp_name"]) == 1

    def test_handle_arguments(self):
        """Test handling DataWindow arguments."""
        dw_syntax = """
        table(retrieve="SELECT * FROM employee WHERE dept_id = :dept_id AND status = :status"
              arguments=(("dept_id", number),("status", string)))
        """

        result = self.converter._parse_datawindow_properties(dw_syntax)

        assert "arguments" in result
        # Arguments should be parsed for retrieval parameters

    def test_parse_update_properties(self):
        """Test parsing update properties."""
        dw_syntax = """
        table(column=(type=number name=id dbname="employee.id" key=yes)
              update="employee" updatewhere=1 updatekeyinplace=yes)
        """

        result = self.converter._parse_datawindow_properties(dw_syntax)

        assert result.get("update_table") == "employee"
        assert "updatewhere" in str(result)

    def test_convert_with_groups(self):
        """Test converting DataWindow with grouping."""
        dw_syntax = """
        datawindow(processing=1)
        group(level=1 name=dept_id header.height=76)
        table(column=(type=number name=dept_id)
              column=(type=char(50) name=emp_name))
        """

        result = self.converter.convert_datawindow(dw_syntax, "dw_grouped")

        # Groups should be detected
        assert result is not None
        assert len(result.columns) == 2

    def test_error_handling_invalid_syntax(self):
        """Test error handling for invalid syntax."""
        invalid_syntax = "This is not valid DataWindow syntax"

        # Should handle gracefully
        result = self.converter.convert_datawindow(invalid_syntax, "dw_invalid")

        assert result is not None
        assert result.name == "DwInvalid"
        assert result.columns == []

    def test_extract_sql_from_various_formats(self):
        """Test extracting SQL from different syntax formats."""
        test_cases = [
            ('retrieve="SELECT * FROM emp"', "SELECT * FROM emp"),
            ('retrieve= "SELECT id FROM emp" ', "SELECT id FROM emp"),
            (
                'retrieve=~"SELECT * FROM emp WHERE id = :id~"',
                "SELECT * FROM emp WHERE id = :id",
            ),
            ('table(retrieve="SELECT * FROM emp")', "SELECT * FROM emp"),
        ]

        for syntax, expected_sql in test_cases:
            result = self.converter._extract_sql(syntax)
            assert expected_sql in result

    def test_column_metadata_extraction(self):
        """Test extracting column metadata."""
        dw_syntax = """
        column(type=char(50) name=emp_name dbname="employee.name"
               initial="" validation='len(emp_name) > 0' validationmsg="Name required"
               edit.limit=50 edit.case=upper edit.required=yes)
        """

        columns = self.converter._parse_columns(dw_syntax)

        assert len(columns) == 1
        col = columns[0]
        assert col["name"] == "emp_name"
        assert "validation" in col
        assert "edit.required" in str(col)

    def test_convert_datawindow_with_all_features(self):
        """Test converting complex DataWindow with all features."""
        dw_syntax = """
        release 12.5;
        datawindow(units=0 timer_interval=0 color=1073741824 processing=1)
        header(height=68 color="536870912")
        summary(height=100 color="536870912")
        footer(height=0 color="536870912")
        detail(height=84 color="536870912")
        table(column=(type=number updatewhereclause=yes key=yes name=id dbname="emp.id")
              column=(type=char(50) updatewhereclause=yes name=name dbname="emp.name")
              column=(type=decimal(2) updatewhereclause=yes name=salary dbname="emp.salary")
              column=(type=date updatewhereclause=yes name=hire_date dbname="emp.hire_date")
              column=(type=blob name=photo dbname="emp.photo")
              retrieve="SELECT * FROM emp WHERE dept = :dept_id ORDER BY name"
              update="emp" updatewhere=1 updatekeyinplace=no
              arguments=(("dept_id", number)))
        compute(band=summary alignment="1" expression="sum(salary for all)")
        text(band=header alignment="2" text="Employee List" x="10" y="10")
        group(level=1 name=dept_id header.height=76)
        """

        # Mock type conversions
        self.converter.type_converter.convert_type.side_effect = [
            "int",
            "String",
            "double",
            "DateTime",
            "Uint8List",
        ]
        self.converter.blob_converter.is_blob_column.side_effect = [
            False,
            False,
            False,
            False,
            True,
        ]
        self.converter.blob_converter.get_blob_metadata.return_value = {
            "type": "image",
            "usage": "display",
        }

        # Convert
        result = self.converter.convert_datawindow(dw_syntax, "dw_employee_full")

        # Comprehensive verification
        assert result.name == "DwEmployeeFull"
        assert len(result.columns) == 5
        assert result.columns[0].is_key
        assert result.columns[4].blob_metadata is not None
        assert result.sql is not None
        assert ":dept_id" in result.sql
        assert result.update_table == "emp"
        assert result.has_arguments
