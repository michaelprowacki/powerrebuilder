"""React/TypeScript Generator Workflow.

Application layer workflow for generating React/TypeScript code from PowerBuilder.
Uses Parse Don't Validate pattern with factory functions.
Transforms PowerBuilder domain types to React components and TypeScript code.
"""

from typing import List, Dict, Any
from datetime import datetime

from src_new.shared.result import Result, Success, Error
from src_new.domain.powerbuilder.objects import (
    Window,
    CommandButton,
    SingleLineEdit,
    DataWindowControl,
    StaticText,
    CheckBox,
)
from src_new.domain.modern.react import ReactComponent, ReactHook, JSXElement


# ============================================================================
# PARSE DON'T VALIDATE - FACTORY FUNCTIONS
# ============================================================================


class _GeneratorToken:
    """Hidden token for Parse Don't Validate pattern."""

    pass


def create_react_component(window: Window) -> Result[ReactComponent, str]:
    """Create a validated React component from PowerBuilder window.

    Parse Don't Validate entry point.
    """
    # Validate window structure
    if not window.name:
        return Error("Window must have a name")

    # Convert window properties to React props
    props_result = _extract_props(window)
    if isinstance(props_result, Error):
        return props_result
    props = props_result.value

    # Convert window state to React state
    state_result = _extract_state(window)
    if isinstance(state_result, Error):
        return state_result
    state = state_result.value

    # Generate hooks for window functionality
    hooks_result = _generate_hooks(window)
    if isinstance(hooks_result, Error):
        return hooks_result
    hooks = hooks_result.value

    # Generate JSX from window controls
    jsx_result = _generate_jsx(window)
    if isinstance(jsx_result, Error):
        return jsx_result
    jsx = jsx_result.value

    # Create validated component with hidden token
    return Success(
        _create_component_internal(
            name=_to_pascal_case(window.name),
            props=props,
            state=state,
            hooks=hooks,
            jsx=jsx,
            token=_GeneratorToken(),
        )
    )


def _create_component_internal(
    name: str,
    props: List[ReactProps],
    state: List[ReactState],
    hooks: List[ReactHook],
    jsx: JSXElement,
    token: _GeneratorToken,
) -> ReactComponent:
    """Internal factory - requires token."""
    if not isinstance(token, _GeneratorToken):
        raise ValueError("Invalid token")

    return ReactComponent(
        name=name,
        props=props,
        state=state,
        hooks=hooks,
        jsx=jsx,
        is_functional=True,  # Modern React uses functional components
    )


# ============================================================================
# PROPS EXTRACTION
# ============================================================================


def _extract_props(window: Window) -> Result[List[ReactProps], str]:
    """Extract React props from window properties."""
    props = []

    # Window title as prop
    if window.title:
        props.append(
            ReactProps(
                name="title", type="string", default=f'"{window.title}"', required=False
            )
        )

    # Window dimensions
    props.append(
        ReactProps(
            name="width", type="number", default=str(window.width), required=False
        )
    )

    props.append(
        ReactProps(
            name="height", type="number", default=str(window.height), required=False
        )
    )

    # Event callbacks
    for event in window.events:
        props.append(
            ReactProps(
                name=f"on{_to_pascal_case(event.name)}",
                type="(() => void) | undefined",
                required=False,
            )
        )

    return Success(props)


# ============================================================================
# STATE EXTRACTION
# ============================================================================


def _extract_state(window: Window) -> Result[List[ReactState], str]:
    """Extract React state from window instance variables."""
    state_vars = []

    # Convert instance variables to state
    for var in window.instance_variables:
        initial_value = _convert_pb_value_to_ts(var.initial_value, var.data_type)
        state_vars.append(
            ReactState(
                name=var.name,
                type=_pb_type_to_ts_type(var.data_type),
                initial_value=initial_value,
            )
        )

    # Add state for control values
    for control in window.controls:
        if isinstance(control, SingleLineEdit):
            state_vars.append(
                ReactState(
                    name=f"{control.name}Value", type="string", initial_value='""'
                )
            )
        elif isinstance(control, CheckBox):
            state_vars.append(
                ReactState(
                    name=f"{control.name}Checked", type="boolean", initial_value="false"
                )
            )

    return Success(state_vars)


# ============================================================================
# HOOKS GENERATION
# ============================================================================


def _generate_hooks(window: Window) -> Result[List[ReactHook], str]:
    """Generate React hooks for window functionality."""
    hooks = []

    # useState hooks for state variables
    for var in window.instance_variables:
        hooks.append(
            ReactHook(
                hook_type="useState",
                name=var.name,
                initial_value=_convert_pb_value_to_ts(var.initial_value, var.data_type),
            )
        )

    # useEffect for window open event
    if any(e.name == "open" for e in window.events):
        hooks.append(
            ReactHook(
                hook_type="useEffect",
                name="windowOpen",
                dependencies=[],  # Run once on mount
            )
        )

    # useCallback for event handlers
    for event in window.events:
        hooks.append(
            ReactHook(
                hook_type="useCallback",
                name=f"handle{_to_pascal_case(event.name)}",
                dependencies=[var.name for var in window.instance_variables],
            )
        )

    return Success(hooks)


# ============================================================================
# JSX GENERATION
# ============================================================================


def _generate_jsx(window: Window) -> Result[JSXElement, str]:
    """Generate JSX from window controls."""
    children = []

    for control in window.controls:
        jsx_result = _control_to_jsx(control)
        if isinstance(jsx_result, Error):
            return jsx_result
        children.append(jsx_result.value)

    # Create root container
    root = JSXElement(
        tag="div",
        props={
            "className": f'"{_to_kebab_case(window.name)}-container"',
            "style": _generate_container_style(window),
        },
        children=children,
    )

    return Success(root)


def _control_to_jsx(control) -> Result[JSXElement, str]:
    """Convert PowerBuilder control to JSX element."""
    if isinstance(control, CommandButton):
        return Success(
            JSXElement(
                tag="button",
                props={
                    "className": '"btn btn-primary"',
                    "onClick": f"handle{_to_pascal_case(control.name)}Click",
                    "disabled": "false" if control.enabled else "true",
                },
                children=[control.text],
            )
        )

    elif isinstance(control, SingleLineEdit):
        return Success(
            JSXElement(
                tag="input",
                props={
                    "type": '"text"',
                    "className": '"form-control"',
                    "value": f"{control.name}Value",
                    "onChange": f"handle{_to_pascal_case(control.name)}Change",
                    "placeholder": f'"{control.text}"' if control.text else '""',
                },
            )
        )

    elif isinstance(control, StaticText):
        return Success(
            JSXElement(
                tag="span",
                props={"className": '"static-text"'},
                children=[control.text],
            )
        )

    elif isinstance(control, CheckBox):
        return Success(
            JSXElement(
                tag="div",
                props={"className": '"form-check"'},
                children=[
                    JSXElement(
                        tag="input",
                        props={
                            "type": '"checkbox"',
                            "className": '"form-check-input"',
                            "checked": f"{control.name}Checked",
                            "onChange": f"handle{_to_pascal_case(control.name)}Change",
                        },
                    ),
                    JSXElement(
                        tag="label",
                        props={"className": '"form-check-label"'},
                        children=[control.text],
                    ),
                ],
            )
        )

    elif isinstance(control, DataWindowControl):
        return _generate_datagrid_jsx(control)

    # Default fallback
    return Success(
        JSXElement(
            tag="div",
            props={"className": f'"{control.control_type}"'},
            children=[str(control)],
        )
    )


def _generate_datagrid_jsx(dw_control: DataWindowControl) -> Result[JSXElement, str]:
    """Generate data grid JSX for DataWindow control."""
    return Success(
        JSXElement(
            tag="DataGrid",  # Using MUI DataGrid or similar
            props={
                "rows": f"{dw_control.name}Data",
                "columns": f"{dw_control.name}Columns",
                "pageSize": "10",
                "checkboxSelection": "true",
                "disableSelectionOnClick": "true",
            },
        )
    )


# ============================================================================
# CODE GENERATION
# ============================================================================


def generate_component_code(component: ReactComponent) -> Result[str, str]:
    """Generate TypeScript code for React component."""
    lines = []

    # Imports
    lines.extend(_generate_imports(component))
    lines.append("")

    # Props interface
    if component.props:
        lines.extend(_generate_props_interface(component))
        lines.append("")

    # Component function
    lines.extend(_generate_component_function(component))

    return Success("\n".join(lines))


def _generate_imports(component: ReactComponent) -> List[str]:
    """Generate import statements."""
    imports = ["import React, { useState, useEffect, useCallback } from 'react';"]

    # Add component library imports based on usage
    if _uses_mui_components(component):
        imports.append(
            "import { Button, TextField, Checkbox, Grid, Box } from '@mui/material';"
        )
        imports.append("import { DataGrid } from '@mui/x-data-grid';")

    return imports


def _generate_props_interface(component: ReactComponent) -> List[str]:
    """Generate TypeScript props interface."""
    lines = [f"interface {component.name}Props {{"]

    for prop in component.props:
        optional = "?" if not prop.required else ""
        lines.append(f"  {prop.name}{optional}: {prop.type};")

    lines.append("}")
    return lines


def _generate_component_function(component: ReactComponent) -> List[str]:
    """Generate component function."""
    lines = []

    # Function signature
    props_type = f"{component.name}Props" if component.props else "{}"
    lines.append(
        f"export const {component.name}: React.FC<{props_type}> = (props) => {{"
    )

    # State declarations
    for state in component.state:
        lines.append(
            f"  const [{state.name}, set{_to_pascal_case(state.name)}] = useState<{state.type}>({state.initial_value});"
        )

    if component.state:
        lines.append("")

    # Hook declarations
    for hook in component.hooks:
        if hook.hook_type == "useEffect":
            lines.append("  useEffect(() => {")
            lines.append(f"    // {hook.name} logic")
            lines.append(f"  }}, [{', '.join(hook.dependencies)}]);")
        elif hook.hook_type == "useCallback":
            lines.append(f"  const {hook.name} = useCallback(() => {{")
            lines.append("    // Handler logic")
            lines.append(f"  }}, [{', '.join(hook.dependencies)}]);")

    if component.hooks:
        lines.append("")

    # Return JSX
    lines.append("  return (")
    lines.extend(_generate_jsx_code(component.jsx, indent=4))
    lines.append("  );")
    lines.append("};")

    return lines


def _generate_jsx_code(element: JSXElement, indent: int = 0) -> List[str]:
    """Generate JSX code from element."""
    lines = []
    indent_str = " " * indent

    # Self-closing tags
    if not element.children:
        props_str = _generate_props_string(element.props)
        lines.append(f"{indent_str}<{element.tag}{props_str} />")
    else:
        # Opening tag
        props_str = _generate_props_string(element.props)
        lines.append(f"{indent_str}<{element.tag}{props_str}>")

        # Children
        for child in element.children:
            if isinstance(child, JSXElement):
                lines.extend(_generate_jsx_code(child, indent + 2))
            else:
                lines.append(f"{' ' * (indent + 2)}{child}")

        # Closing tag
        lines.append(f"{indent_str}</{element.tag}>")

    return lines


def _generate_props_string(props: Dict[str, Any]) -> str:
    """Generate props string for JSX element."""
    if not props:
        return ""

    prop_parts = []
    for key, value in props.items():
        if isinstance(value, dict):
            # Style object
            prop_parts.append(f"{key}={{{value}}}")
        elif value.startswith('"'):
            # String literal
            prop_parts.append(f"{key}={value}")
        else:
            # Variable/expression
            prop_parts.append(f"{key}={{{value}}}")

    return " " + " ".join(prop_parts) if prop_parts else ""


# ============================================================================
# TYPE CONVERSION
# ============================================================================


def _pb_type_to_ts_type(pb_type: str) -> str:
    """Convert PowerBuilder type to TypeScript type."""
    type_map = {
        "string": "string",
        "integer": "number",
        "long": "number",
        "decimal": "number",
        "boolean": "boolean",
        "date": "Date",
        "datetime": "Date",
        "time": "string",
        "any": "any",
    }
    return type_map.get(pb_type.lower(), "unknown")


def _convert_pb_value_to_ts(value: Any, pb_type: str) -> str:
    """Convert PowerBuilder value to TypeScript literal."""
    if value is None:
        return "null"
    elif pb_type.lower() == "string":
        return f'"{value}"'
    elif pb_type.lower() == "boolean":
        return "true" if value else "false"
    elif pb_type.lower() in ["integer", "long", "decimal"]:
        return str(value)
    elif pb_type.lower() in ["date", "datetime"]:
        return f'new Date("{value}")'
    return "undefined"


# ============================================================================
# STYLING
# ============================================================================


def _generate_container_style(window: Window) -> str:
    """Generate container style object."""
    style = {
        "width": f"{window.width}px",
        "height": f"{window.height}px",
        "display": "flex",
        "flexDirection": "column",
        "padding": "16px",
    }
    return str(style).replace("'", '"')


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _to_pascal_case(name: str) -> str:
    """Convert to PascalCase."""
    parts = name.split("_")
    return "".join(part.capitalize() for part in parts)


def _to_camel_case(name: str) -> str:
    """Convert to camelCase."""
    pascal = _to_pascal_case(name)
    return pascal[0].lower() + pascal[1:] if pascal else ""


def _to_kebab_case(name: str) -> str:
    """Convert to kebab-case."""
    return name.lower().replace("_", "-")


def _uses_mui_components(component: ReactComponent) -> bool:
    """Check if component uses Material-UI components."""
    # Simplified check - would analyze JSX tree
    return True


# ============================================================================
# EVENT EMISSION
# ============================================================================


def emit_component_generated(
    component: ReactComponent, source_window: Window
) -> ComponentGenerated:
    """Emit component generated event."""
    return ComponentGenerated(
        component=component,
        source_type="Window",
        source_name=source_window.name,
        timestamp=datetime.now(),
    )
