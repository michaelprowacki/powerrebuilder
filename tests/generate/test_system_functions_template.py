"""Tests for system functions template generation.

This module tests the generation of system functions from templates.
"""

import os

from jinja2 import Environment, FileSystemLoader

# TODO: These classes need to be implemented or the test needs to be updated
# from src.model.unified_expressions import (
#     PBBuiltInFunction,
#     PBFunctionCategory,
#     PBParameter,
# )


class TestSystemFunctionsTemplate:
    """Tests for system functions template generation."""

    def setup_method(self):
        """Set up the test."""
        # Create a Jinja2 environment with our templates directory
        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "generate",
            "templates",
            "python",
        )
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def test_system_functions_template(self):
        """Test rendering the system functions template."""
        # Create some test system functions with names that already exist in the class
        test_functions = [
            PBBuiltInFunction(
                name="len",
                category=PBFunctionCategory.STRING,
                return_type="integer",
                parameters=[
                    PBParameter(name="string", type_name="string"),
                ],
                description="Test length function",
            ),
            PBBuiltInFunction(
                name="abs",
                category=PBFunctionCategory.MATH,
                return_type="double",
                parameters=[
                    PBParameter(name="number", type_name="double"),
                ],
                description="Test absolute value function",
            ),
        ]

        # Render the template
        template = self.env.get_template("system_functions.py.jinja2")
        result = template.render(system_functions=test_functions)

        # Check that our test functions are in the registry
        assert '"len": PowerBuilderSystemFunctions.len' in result
        assert '"abs": PowerBuilderSystemFunctions.abs' in result

        # Check that only these functions are in the registry (not the default ones)
        assert "SYSTEM_FUNCTIONS = {" in result
        # Should only have our 2 functions, not all the default ones
        assert '"left":' not in result
        assert '"right":' not in result

    def test_system_functions_default_template(self):
        """Test rendering the system functions template with default functions."""
        # Render the template without providing custom functions
        template = self.env.get_template("system_functions.py.jinja2")
        result = template.render()

        # Check that the default functions are included in the registry
        assert '"len": PowerBuilderSystemFunctions.len' in result
        assert '"left": PowerBuilderSystemFunctions.left' in result
        assert '"abs": PowerBuilderSystemFunctions.abs' in result
        assert '"today": PowerBuilderSystemFunctions.today' in result

    def test_call_system_function(self):
        """Test that the call_system_function function is correctly generated."""
        # Render the template
        template = self.env.get_template("system_functions.py.jinja2")
        result = template.render()

        # Check that the call_system_function function is included
        assert "def call_system_function(name: str, *args: Any) -> Any:" in result
        assert "func = SYSTEM_FUNCTIONS.get(name.lower())" in result
        assert "return func(*args)" in result
