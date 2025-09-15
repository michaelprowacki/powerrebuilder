"""Test suite for DataWindow enhancements (computed fields and validation)."""

import pytest

from src.generate.converters.ui.dw_enhancements import (
    ComputedField,
    ComputedFieldProcessor,
    ValidationRule,
    ValidationRuleProcessor,
)


class TestComputedField:
    """Test cases for ComputedField dataclass."""

    def test_computed_field_creation(self):
        """Test creating a computed field."""
        field = ComputedField(
            name="total_amount",
            expression="quantity * unit_price",
            original_expression="quantity * unit_price",
            inferred_type="double",
            dependencies=["quantity", "unit_price"],
            is_aggregate=False,
        )

        assert field.name == "total_amount"
        assert field.expression == "quantity * unit_price"
        assert field.inferred_type == "double"
        assert len(field.dependencies) == 2
        assert field.is_aggregate is False

    def test_aggregate_computed_field(self):
        """Test creating an aggregate computed field."""
        field = ComputedField(
            name="average_salary",
            expression="avg(salary)",
            original_expression="avg(salary)",
            inferred_type="double",
            dependencies=["salary"],
            is_aggregate=True,
            aggregate_function="avg",
        )

        assert field.is_aggregate is True
        assert field.aggregate_function == "avg"

    def test_computed_field_to_dict(self):
        """Test ComputedField to_dict conversion."""
        field = ComputedField(
            name="full_name",
            expression="firstName + ' ' + lastName",
            original_expression="first_name + ' ' + last_name",
            inferred_type="String",
            dependencies=["first_name", "last_name"],
        )

        field_dict = field.to_dict()

        assert field_dict["name"] == "full_name"
        assert field_dict["type"] == "String"
        assert len(field_dict["dependencies"]) == 2
        assert field_dict["is_aggregate"] is False


class TestValidationRule:
    """Test cases for ValidationRule dataclass."""

    def test_validation_rule_creation(self):
        """Test creating a validation rule."""
        rule = ValidationRule(
            column_name="age",
            rule_type="min",
            rule_value=18,
            error_message="Age must be at least 18",
            dart_validator="// Dart validator code",
            python_validator="# Python validator code",
        )

        assert rule.column_name == "age"
        assert rule.rule_type == "min"
        assert rule.rule_value == 18

    def test_validation_rule_to_dict(self):
        """Test ValidationRule to_dict conversion."""
        rule = ValidationRule(
            column_name="email",
            rule_type="pattern",
            rule_value=r"^[\w\.-]+@[\w\.-]+\.\w+$",
            error_message="Invalid email format",
            dart_validator="// Email validator",
            python_validator="# Email validator",
        )

        rule_dict = rule.to_dict()

        assert rule_dict["column_name"] == "email"
        assert rule_dict["rule_type"] == "pattern"
        assert "@" in rule_dict["rule_value"]


class TestComputedFieldProcessor:
    """Test cases for ComputedFieldProcessor."""

    def setup_method(self):
        """Set up test instances."""
        self.processor = ComputedFieldProcessor()

    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor is not None
        assert len(self.processor.aggregate_functions) > 0
        assert len(self.processor.type_patterns) > 0

    def test_extract_dependencies(self):
        """Test dependency extraction from expressions."""
        columns = [
            {"name": "quantity", "data_type": "int"},
            {"name": "unit_price", "data_type": "double"},
            {"name": "discount", "data_type": "double"},
        ]

        # Simple expression
        deps = self.processor._extract_dependencies("quantity * unit_price", columns)
        assert set(deps) == {"quantity", "unit_price"}

        # Expression with function
        deps = self.processor._extract_dependencies(
            "round(unit_price * (1 - discount))", columns
        )
        assert set(deps) == {"unit_price", "discount"}

        # No dependencies
        deps = self.processor._extract_dependencies("100", columns)
        assert deps == []

    def test_check_aggregate(self):
        """Test aggregate function detection."""
        # Aggregate functions
        is_agg, func = self.processor._check_aggregate("sum(amount)")
        assert is_agg is True
        assert func == "sum"

        is_agg, func = self.processor._check_aggregate("avg(salary) * 1.1")
        assert is_agg is True
        assert func == "avg"

        is_agg, func = self.processor._check_aggregate("count(*)")
        assert is_agg is True
        assert func == "count"

        # Non-aggregate
        is_agg, func = self.processor._check_aggregate("quantity * price")
        assert is_agg is False
        assert func is None

    def test_infer_type(self):
        """Test type inference for expressions."""
        # Numeric operations
        assert self.processor._infer_type("a + b") == "double"
        assert self.processor._infer_type("count(*)") == "int"
        assert self.processor._infer_type("avg(price)") == "double"

        # String operations
        assert self.processor._infer_type("trim(name)") == "String"
        assert self.processor._infer_type("upper(code)") == "String"
        assert self.processor._infer_type("'Hello'") == "String"

        # Date operations
        assert self.processor._infer_type("today()") == "DateTime"
        assert self.processor._infer_type("year(date_field)") == "DateTime"

        # Boolean operations
        assert self.processor._infer_type("a > b") == "bool"
        assert self.processor._infer_type("x and y") == "bool"

        # Numeric literals
        assert self.processor._infer_type("123") == "int"
        assert self.processor._infer_type("123.45") == "double"

    def test_process_computed_field(self):
        """Test processing a complete computed field."""
        columns = [
            {"name": "quantity", "data_type": "int"},
            {"name": "unit_price", "data_type": "double"},
        ]

        field = self.processor.process_computed_field(
            name="line_total",
            expression="quantity * unit_price",
            columns=columns,
        )

        assert field.name == "line_total"
        assert field.inferred_type == "double"
        assert set(field.dependencies) == {"quantity", "unit_price"}
        assert field.is_aggregate is False

    def test_process_aggregate_field(self):
        """Test processing an aggregate computed field."""
        columns = [{"name": "amount", "data_type": "double"}]

        field = self.processor.process_computed_field(
            name="total_amount",
            expression="sum(amount)",
            columns=columns,
        )

        assert field.is_aggregate is True
        assert field.aggregate_function == "sum"
        assert field.inferred_type == "double"

    def test_generate_flutter_method(self):
        """Test Flutter method generation for computed field."""
        field = ComputedField(
            name="full_price",
            expression="basePrice + tax",
            original_expression="base_price + tax",
            inferred_type="double",
            dependencies=["base_price", "tax"],
        )

        lines = self.processor._generate_flutter_method(field)

        assert any("getFullPrice" in line for line in lines)
        assert any("Map<String, dynamic> row" in line for line in lines)
        assert any("double" in line for line in lines)
        assert any("basePrice + tax" in line for line in lines)

    def test_generate_python_method(self):
        """Test Python method generation for computed field."""
        field = ComputedField(
            name="discount_amount",
            expression="price * discountRate",
            original_expression="price * discount_rate",
            inferred_type="double",
            dependencies=["price", "discount_rate"],
        )

        lines = self.processor._generate_python_method(field)

        assert any("def get_discount_amount" in line for line in lines)
        assert any("row: dict" in line for line in lines)
        assert any("float" in line for line in lines)
        assert any("price * discountRate" in line for line in lines)

    def test_pascal_case_conversion(self):
        """Test PascalCase conversion."""
        assert self.processor._to_pascal_case("my_field") == "MyField"
        assert self.processor._to_pascal_case("simple") == "Simple"
        assert self.processor._to_pascal_case("long_field_name") == "LongFieldName"

    def test_python_type_conversion(self):
        """Test Dart to Python type conversion."""
        assert self.processor._python_type("int") == "int"
        assert self.processor._python_type("double") == "float"
        assert self.processor._python_type("String") == "str"
        assert self.processor._python_type("bool") == "bool"
        assert self.processor._python_type("DateTime") == "datetime"
        assert self.processor._python_type("dynamic") == "Any"


class TestValidationRuleProcessor:
    """Test cases for ValidationRuleProcessor."""

    def setup_method(self):
        """Set up test instances."""
        self.processor = ValidationRuleProcessor()

    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor is not None
        assert len(self.processor.rule_patterns) > 0

    def test_process_required_rule(self):
        """Test processing required field validation."""
        rule = self.processor.process_validation_rule("name", "required")

        assert rule is not None
        assert rule.rule_type == "required"
        assert rule.rule_value is True
        assert "is required" in rule.error_message

    def test_process_min_max_rules(self):
        """Test processing min/max validation rules."""
        # Min rule
        rule = self.processor.process_validation_rule("age", "min 18")
        assert rule.rule_type == "min"
        assert rule.rule_value == 18

        # Max rule
        rule = self.processor.process_validation_rule("score", "max 100")
        assert rule.rule_type == "max"
        assert rule.rule_value == 100

        # Range rule
        rule = self.processor.process_validation_rule("price", "between 10 and 1000")
        assert rule.rule_type == "range"
        assert rule.rule_value == (10.0, 1000.0)

    def test_process_length_rule(self):
        """Test processing length validation rules."""
        rule = self.processor.process_validation_rule("code", "len = 10")

        assert rule.rule_type == "length"
        assert rule.rule_value == 10

    def test_process_pattern_rule(self):
        """Test processing pattern validation rules."""
        rule = self.processor.process_validation_rule(
            "email", "match('[a-z]+@[a-z]+\\.[a-z]+')"
        )

        assert rule.rule_type == "pattern"
        assert "@" in rule.rule_value

    def test_process_custom_rule(self):
        """Test processing custom validation rules."""
        rule = self.processor.process_validation_rule(
            "custom_field", "some_complex_validation()"
        )

        assert rule.rule_type == "custom"
        assert rule.rule_value == "some_complex_validation()"

    def test_generate_dart_required_validator(self):
        """Test Dart required field validator generation."""
        rule = ValidationRule(
            column_name="username",
            rule_type="required",
            rule_value=True,
            error_message="Username is required",
            dart_validator="",
            python_validator="",
        )

        validator = self.processor._generate_dart_validator(
            "username", "required", True
        )

        assert "validateUsername" in validator
        assert "isEmpty" in validator
        assert "return 'username is required'" in validator

    def test_generate_dart_numeric_validators(self):
        """Test Dart numeric validator generation."""
        # Min validator
        validator = self.processor._generate_dart_validator("age", "min", 18)
        assert "validateAge" in validator
        assert "< 18" in validator

        # Max validator
        validator = self.processor._generate_dart_validator("score", "max", 100)
        assert "validateScore" in validator
        assert "> 100" in validator

        # Range validator
        validator = self.processor._generate_dart_validator("price", "range", (10, 100))
        assert "validatePrice" in validator
        assert "< 10" in validator
        assert "> 100" in validator

    def test_generate_dart_pattern_validator(self):
        """Test Dart pattern validator generation."""
        validator = self.processor._generate_dart_validator(
            "email",
            "pattern",
            r"^[\w\.-]+@[\w\.-]+\.\w+$",
        )

        assert "validateEmail" in validator
        assert "RegExp" in validator
        assert "hasMatch" in validator

    def test_generate_python_validators(self):
        """Test Python validator generation."""
        # Required validator
        validator = self.processor._generate_python_validator("name", "required", True)
        assert "def validate_name" in validator
        assert "is None or str(value).strip() == ''" in validator

        # Numeric validator
        validator = self.processor._generate_python_validator("age", "min", 18)
        assert "float(value)" in validator
        assert "< 18" in validator

        # Pattern validator
        validator = self.processor._generate_python_validator(
            "code", "pattern", r"\d{5}"
        )
        assert "import re" in validator
        assert "pattern.match" in validator

    def test_generate_form_validators_flutter(self):
        """Test Flutter form validators generation."""
        rules = [
            ValidationRule("name", "required", True, "Name required", "", ""),
            ValidationRule("age", "min", 18, "Age >= 18", "", ""),
            ValidationRule("email", "pattern", r".*@.*", "Invalid email", "", ""),
        ]

        validators = self.processor.generate_form_validators(rules, "flutter")

        assert "form_validators" in validators
        assert "field_validators" in validators

        form_validators = validators["form_validators"]
        assert any(
            "FormBuilderValidators.required()" in line for line in form_validators
        )
        assert any("FormBuilderValidators.min(18)" in line for line in form_validators)

    def test_generate_form_validators_python(self):
        """Test Python form validators generation."""
        rules = [
            ValidationRule("username", "required", True, "Required", "", ""),
            ValidationRule("password", "length", 8, "8 chars", "", ""),
        ]

        validators = self.processor.generate_form_validators(rules, "python")

        assert "form_validators" in validators
        assert "field_validators" in validators

        form_validators = validators["form_validators"]
        assert any("class FormValidators:" in line for line in form_validators)
        assert any("validate_all" in line for line in form_validators)

    def test_empty_validation_expression(self):
        """Test handling empty validation expressions."""
        rule = self.processor.process_validation_rule("field", "")
        assert rule is None

        rule = self.processor.process_validation_rule("field", None)
        assert rule is None

    def test_complex_validation_patterns(self):
        """Test complex validation pattern matching."""
        # Date validation
        rule = self.processor.process_validation_rule("start_date", "date >= today")
        assert rule.rule_type == "date_compare"

        # Valid date
        rule = self.processor.process_validation_rule("birth_date", "valid date")
        assert rule.rule_type == "valid_date"

        # Like pattern
        rule = self.processor.process_validation_rule("code", "like 'ABC%'")
        assert rule.rule_type == "pattern"
        assert rule.rule_value == "ABC%"

    def test_generate_custom_validators(self):
        """Test custom validator generation."""
        # Dart custom validator
        dart_validator = self.processor._generate_dart_custom_validator(
            "custom_field",
            "validateCustomLogic()",
        )
        assert "validateCustomFieldCustom" in dart_validator
        assert "TODO: Implement custom validation logic" in dart_validator

        # Python custom validator
        python_validator = self.processor._generate_python_custom_validator(
            "custom_field",
            "validateCustomLogic()",
        )
        assert "def validate_custom_field_custom" in python_validator
        assert "TODO: Implement custom validation logic" in python_validator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
