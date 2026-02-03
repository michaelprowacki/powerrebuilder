"""Svelte Generator Workflow.

Application layer workflow for generating Svelte code from PowerBuilder.
Uses Parse Don't Validate pattern with factory functions.
Transforms PowerBuilder domain types to Svelte components.
"""

from typing import List, Optional, Any

from src_new.shared.result import Result, Success, Error
from src_new.domain.powerbuilder.objects import (
    Window,
    CommandButton,
    SingleLineEdit,
    StaticText,
    CheckBox,
)
from src_new.domain.modern.svelte import SvelteComponent, SvelteProp, SvelteState


# ============================================================================
# PARSE DON'T VALIDATE - FACTORY FUNCTIONS
# ============================================================================


class _SvelteToken:
    """Hidden token for Parse Don't Validate pattern."""

    pass


def create_svelte_component(window: Window) -> Result[SvelteComponent, str]:
    """Create a validated Svelte component from PowerBuilder window.

    Parse Don't Validate entry point.
    """
    if not window.name:
        return Error("Window must have a name")

    # Extract props
    props_result = _extract_props(window)
    if isinstance(props_result, Error):
        return props_result

    # Extract state
    state_result = _extract_state(window)
    if isinstance(state_result, Error):
        return state_result

    # Generate script
    script_result = _generate_script(window, props_result.value, state_result.value)
    if isinstance(script_result, Error):
        return script_result

    # Generate template
    template_result = _generate_template(window)
    if isinstance(template_result, Error):
        return template_result

    # Generate styles
    style = _generate_styles(window)

    return Success(
        _create_component_internal(
            name=_to_pascal_case(window.name),
            props=props_result.value,
            state=state_result.value,
            script=script_result.value,
            template=template_result.value,
            style=style,
            token=_SvelteToken(),
        )
    )


def _create_component_internal(
    name: str,
    props: List[SvelteProp],
    state: List[SvelteState],
    script: str,
    template: str,
    style: Optional[str],
    token: _SvelteToken,
) -> SvelteComponent:
    """Internal factory - requires token."""
    if not isinstance(token, _SvelteToken):
        raise ValueError("Invalid token")

    return SvelteComponent(
        name=name,
        props=props,
        state=state,
        script=script,
        template=template,
        style=style,
    )


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================


def _extract_props(window: Window) -> Result[List[SvelteProp], str]:
    """Extract Svelte props from window."""
    props = []

    if window.title:
        props.append(
            SvelteProp(name="title", type="string", default=f'"{window.title}"')
        )

    props.append(SvelteProp(name="width", type="number", default=str(window.width)))

    props.append(SvelteProp(name="height", type="number", default=str(window.height)))

    return Success(props)


def _extract_state(window: Window) -> Result[List[SvelteState], str]:
    """Extract state variables from window."""
    state = []

    for var in window.instance_variables:
        state.append(
            SvelteState(
                name=var.name,
                initial_value=_convert_value(var.initial_value, var.data_type),
                type=_pb_to_js_type(var.data_type),
                is_reactive=False,
            )
        )

    # Add control state
    for control in window.controls:
        if isinstance(control, SingleLineEdit):
            state.append(
                SvelteState(
                    name=f"{control.name}Value", initial_value='""', type="string"
                )
            )
        elif isinstance(control, CheckBox):
            state.append(
                SvelteState(
                    name=f"{control.name}Checked", initial_value="false", type="boolean"
                )
            )

    return Success(state)


# ============================================================================
# CODE GENERATION
# ============================================================================


def _generate_script(
    window: Window, props: List[SvelteProp], state: List[SvelteState]
) -> Result[str, str]:
    """Generate Svelte script section."""
    lines = ["<script>"]

    # Props
    for prop in props:
        default_val = f" = {prop.default}" if prop.default else ""
        lines.append(f"  export let {prop.name}{default_val}")

    if props:
        lines.append("")

    # State
    for var in state:
        lines.append(f"  let {var.name} = {var.initial_value}")

    if state:
        lines.append("")

    # Event handlers
    for control in window.controls:
        if isinstance(control, CommandButton):
            lines.append(f"  function handle{_to_pascal_case(control.name)}Click() {{")
            lines.append(f"    // {control.name} click handler")
            lines.append("  }")
            lines.append("")

    # Reactive statements
    lines.append("  // Reactive statements")
    lines.append(
        '  $: console.log("Component state:", { '
        + ", ".join(s.name for s in state)
        + " })"
    )

    lines.append("</script>")
    return Success("\n".join(lines))


def _generate_template(window: Window) -> Result[str, str]:
    """Generate Svelte template."""
    lines = [f'<div class="{_to_kebab_case(window.name)}-container">']

    if window.title:
        lines.append("  <h1>{title}</h1>")

    for control in window.controls:
        lines.extend(_control_to_template(control))

    lines.append("</div>")
    return Success("\n".join(lines))


def _control_to_template(control) -> List[str]:
    """Convert control to Svelte template."""
    lines = []

    if isinstance(control, CommandButton):
        lines.append(
            f"  <button on:click={{handle{_to_pascal_case(control.name)}Click}}>"
        )
        lines.append(f"    {control.text}")
        lines.append("  </button>")
    elif isinstance(control, SingleLineEdit):
        lines.append(
            f'  <input bind:value={{{control.name}Value}} placeholder="{control.text}" />'
        )
    elif isinstance(control, StaticText):
        lines.append(f"  <span>{control.text}</span>")
    elif isinstance(control, CheckBox):
        lines.append("  <label>")
        lines.append(
            f'    <input type="checkbox" bind:checked={{{control.name}Checked}} />'
        )
        lines.append(f"    {control.text}")
        lines.append("  </label>")

    return lines


def _generate_styles(window: Window) -> str:
    """Generate component styles."""
    styles = ["<style>"]
    styles.append(f"  .{_to_kebab_case(window.name)}-container {{")
    styles.append(f"    width: {window.width}px;")
    styles.append(f"    height: {window.height}px;")
    styles.append("    padding: 1rem;")
    styles.append("  }")
    styles.append("</style>")
    return "\n".join(styles)


# ============================================================================
# UTILITIES
# ============================================================================


def _to_pascal_case(name: str) -> str:
    """Convert to PascalCase."""
    return "".join(p.capitalize() for p in name.split("_"))


def _to_kebab_case(name: str) -> str:
    """Convert to kebab-case."""
    return name.lower().replace("_", "-")


def _pb_to_js_type(pb_type: str) -> str:
    """Convert PowerBuilder type to JavaScript type."""
    type_map = {
        "string": "string",
        "integer": "number",
        "boolean": "boolean",
        "date": "Date",
    }
    return type_map.get(pb_type.lower(), "any")


def _convert_value(value: Any, pb_type: str) -> str:
    """Convert PowerBuilder value to JavaScript."""
    if value is None:
        return "null"
    elif pb_type.lower() == "string":
        return f'"{value}"'
    elif pb_type.lower() == "boolean":
        return "true" if value else "false"
    else:
        return str(value)


def generate_component_code(component: SvelteComponent) -> Result[str, str]:
    """Generate complete Svelte component code."""
    sections = []

    if component.script:
        sections.append(component.script)

    if component.template:
        sections.append(component.template)

    if component.style:
        sections.append(component.style)

    return Success("\n\n".join(sections))
