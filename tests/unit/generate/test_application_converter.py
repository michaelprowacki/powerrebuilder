"""Test suite for ApplicationConverter."""

import pytest

from src.generate.converters.logic.application import (
    ApplicationConverter,
    ApplicationDefinition,
    ApplicationEvent,
    ApplicationVariable,
)


class TestApplicationConverter:
    """Test cases for PowerBuilder to Flutter/Python application conversion."""

    def setup_method(self):
        """Set up test instances."""
        self.converter = ApplicationConverter()

    def test_initialization(self):
        """Test converter initialization."""
        assert self.converter is not None
        assert hasattr(self.converter, "type_converter")
        assert hasattr(self.converter, "parse_application")

    def test_parse_simple_application(self):
        """Test parsing a simple application definition."""
        app_syntax = """
            global type myapp from application
            end type
            global myapp myapp

            on myapp.create
                appname = "My Application"
                appdisplayname = "My Test App"
                national = true
                toolbartext = true
            end on
        """

        app_def = self.converter.parse_application(app_syntax)

        assert app_def is not None
        assert app_def.name == "myapp"
        assert app_def.app_name == "My Application"
        assert app_def.display_name == "My Test App"
        assert app_def.toolbar_text is True

    def test_parse_application_with_database(self):
        """Test parsing application with database configuration."""
        app_syntax = """
            global type salesapp from application
            end type
            global salesapp salesapp

            on salesapp.create
                appname = "Sales Manager"
                appdisplayname = "Sales Management System"

                // Database settings
                SQLCA.DBMS = "ODBC"
                SQLCA.Database = "sales_db"
                SQLCA.UserID = "sa"
                SQLCA.DBPass = "password123"
                SQLCA.ServerName = "localhost"
                SQLCA.DBParm = "ConnectString='DSN=SalesDB'"
            end on
        """

        app_def = self.converter.parse_application(app_syntax)

        assert app_def is not None
        assert app_def.name == "salesapp"
        assert app_def.dbms == "ODBC"
        assert app_def.database == "sales_db"
        assert app_def.userid == "sa"
        assert app_def.server_name == "localhost"
        assert "DSN=SalesDB" in app_def.db_parm

    def test_parse_application_events(self):
        """Test parsing application events."""
        app_syntax = """
            global type myapp from application
            end type
            global myapp myapp

            event open()
                // Application startup
                open(w_main)
            end event

            event close()
                // Cleanup
                disconnect;
            end event

            event systemerror(string message, integer error_number)
                messagebox("System Error", message + " (" + string(error_number) + ")")
            end event
        """

        app_def = self.converter.parse_application(app_syntax)

        assert app_def is not None
        assert len(app_def.events) == 3

        # Check open event
        open_event = next((e for e in app_def.events if e.name == "open"), None)
        assert open_event is not None
        assert "open(w_main)" in " ".join(open_event.body)

        # Check systemerror event
        error_event = next((e for e in app_def.events if e.name == "systemerror"), None)
        assert error_event is not None
        assert len(error_event.parameters) == 2
        assert error_event.parameters[0] == ("string", "message")
        assert error_event.parameters[1] == ("integer", "error_number")

    def test_parse_global_variables(self):
        """Test parsing global application variables."""
        app_syntax = """
            global type myapp from application
            end type
            global myapp myapp

            // Global variables
            global string gs_app_version = "1.0.0"
            global integer gi_user_count
            global boolean gb_debug_mode = true
            global n_business_logic gn_business

            on myapp.create
                appname = "My App"
            end on
        """

        app_def = self.converter.parse_application(app_syntax)

        assert app_def is not None
        assert len(app_def.variables) == 4

        # Check version variable
        version_var = next(
            (v for v in app_def.variables if v.name == "gs_app_version"), None
        )
        assert version_var is not None
        assert version_var.pb_type == "string"
        assert version_var.dart_type == "String"
        assert version_var.initial_value == '"1.0.0"'

        # Check debug variable
        debug_var = next(
            (v for v in app_def.variables if v.name == "gb_debug_mode"), None
        )
        assert debug_var is not None
        assert debug_var.pb_type == "boolean"
        assert debug_var.dart_type == "bool"
        assert debug_var.initial_value == "true"

    def test_convert_to_flutter(self):
        """Test converting application definition to Flutter format."""
        app_def = ApplicationDefinition(
            name="myapp",
            app_name="My Application",
            display_name="My Test Application",
            initial_window="w_main",
            theme="liquid_glass",
        )

        # Add a global variable
        app_def.variables.append(
            ApplicationVariable(
                name="gs_version",
                pb_type="string",
                dart_type="String",
                python_type="str",
                initial_value='"1.0.0"',
            )
        )

        # Add open event
        app_def.events.append(
            ApplicationEvent(
                name="open",
                body=["// Initialize app", "open(w_main)"],
            )
        )

        flutter_data = self.converter.convert_to_flutter(app_def)

        assert flutter_data is not None
        assert flutter_data["app_name"] == "My Application"
        assert flutter_data["display_name"] == "My Test Application"
        assert flutter_data["initial_window"] == "w_main"
        assert flutter_data["theme"] == "liquid_glass"
        assert flutter_data["has_database"] is False
        assert flutter_data["has_globals"] is True
        assert len(flutter_data["global_variables"]) == 1

    def test_convert_to_python(self):
        """Test converting application definition to Python format."""
        app_def = ApplicationDefinition(
            name="salesapp",
            app_name="Sales Manager",
            display_name="Sales Management System",
            initial_window="w_login",
            dbms="PostgreSQL",
            database="sales_db",
        )

        python_data = self.converter.convert_to_python(app_def)

        assert python_data is not None
        assert python_data["app_name"] == "Sales Manager"
        assert python_data["display_name"] == "Sales Management System"
        assert python_data["initial_window"] == "w_login"
        assert python_data["has_database"] is True
        assert python_data["database_config"] is not None
        assert python_data["database_config"]["engine"] == "postgresql"
        assert python_data["database_config"]["database"] == "sales_db"

    def test_database_config_conversion(self):
        """Test database configuration conversion."""
        # Test PostgreSQL
        pg_config = self.converter._create_database_config(
            dbms="PostgreSQL",
            database="mydb",
            userid="postgres",
            server_name="localhost",
            db_parm="Port=5432",
        )

        assert pg_config.engine == "postgresql"
        assert pg_config.host == "localhost"
        assert pg_config.port == 5432
        assert pg_config.database == "mydb"
        assert pg_config.username == "postgres"

        # Test MySQL
        mysql_config = self.converter._create_database_config(
            dbms="MySQL",
            database="testdb",
            userid="root",
            server_name="192.168.1.100",
        )

        assert mysql_config.engine == "mysql"
        assert mysql_config.host == "192.168.1.100"
        assert mysql_config.port == 3306  # Default MySQL port
        assert mysql_config.database == "testdb"

        # Test SQL Server
        mssql_config = self.converter._create_database_config(
            dbms="SQL Server",
            database="sales",
            userid="sa",
            server_name="DESKTOP\\SQLEXPRESS",
        )

        assert mssql_config.engine == "mssql+pyodbc"
        assert mssql_config.host == "DESKTOP\\SQLEXPRESS"
        assert mssql_config.database == "sales"

    def test_extract_db_parameters(self):
        """Test extracting parameters from DBParm string."""
        # Test with multiple parameters
        db_parm = "ConnectString='DSN=MyDSN',Port=5433,Timeout=30"
        params = self.converter._extract_db_parameters(db_parm)

        assert params["connectstring"] == "DSN=MyDSN"
        assert params["port"] == "5433"
        assert params["timeout"] == "30"

        # Test with quoted values
        db_parm = 'Database="C:\\Data\\mydb.db",UserId="domain\\user"'
        params = self.converter._extract_db_parameters(db_parm)

        assert params["database"] == "C:\\Data\\mydb.db"
        assert params["userid"] == "domain\\user"

    def test_application_with_theme(self):
        """Test application with theme settings."""
        app_syntax = """
            global type myapp from application
            end type
            global myapp myapp

            on myapp.create
                appname = "Themed App"
                theme = "liquid_glass"
                icon = "app_icon.ico"
            end on
        """

        app_def = self.converter.parse_application(app_syntax)
        flutter_data = self.converter.convert_to_flutter(app_def)

        assert flutter_data["theme"] == "liquid_glass"
        assert flutter_data["uses_glassmorphism"] is True
        assert flutter_data["icon"] == "app_icon.ico"

    def test_convert_app_name(self):
        """Test application name conversion for package names."""
        test_cases = [
            ("My Application", "my_application"),
            ("Sales-Manager", "sales_manager"),
            ("POS System 2.0", "pos_system_2_0"),
            ("HR&Payroll", "hr_payroll"),
            ("123App", "app_123_app"),  # Can't start with number
        ]

        for input_name, expected in test_cases:
            result = self.converter._convert_app_name_to_package(input_name)
            assert result == expected

    def test_empty_application(self):
        """Test handling empty application definition."""
        app_syntax = """
            global type emptyapp from application
            end type
            global emptyapp emptyapp
        """

        app_def = self.converter.parse_application(app_syntax)

        assert app_def is not None
        assert app_def.name == "emptyapp"
        assert app_def.app_name == ""  # Should be empty
        assert len(app_def.events) == 0
        assert len(app_def.variables) == 0

    def test_application_to_dict(self):
        """Test ApplicationDefinition to_dict method."""
        app_def = ApplicationDefinition(
            name="testapp",
            app_name="Test Application",
            display_name="Test App Display",
            micro_help=True,
            toolbar_tips=True,
        )

        # Add variable and event
        app_def.variables.append(
            ApplicationVariable(
                name="g_test",
                pb_type="string",
                dart_type="String",
                python_type="str",
            )
        )

        app_def.events.append(
            ApplicationEvent(
                name="open",
                body=["// Open event"],
            )
        )

        app_dict = app_def.to_dict()

        assert app_dict["name"] == "testapp"
        assert app_dict["app_name"] == "Test Application"
        assert app_dict["display_name"] == "Test App Display"
        assert app_dict["micro_help"] is True
        assert app_dict["has_variables"] is True
        assert app_dict["has_events"] is True
        assert len(app_dict["variables"]) == 1
        assert len(app_dict["events"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
