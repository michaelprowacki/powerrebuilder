"""Vue 3 Generator Workflow.

Application layer workflow for generating Vue 3 code from PowerBuilder.
Uses Parse Don't Validate pattern with factory functions.
Transforms PowerBuilder domain types to Vue components and TypeScript code.
"""

from typing import List, Optional, Dict, Any
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
from src_new.domain.modern.vue import (
    VueComponent,
    VueProp,
    VueEmit,
    VueStyle,
    PiniaStore,
    VueComponentCreated,
)


# ============================================================================
# PARSE DON'T VALIDATE - FACTORY FUNCTIONS
# ============================================================================


class _VueGeneratorToken:
    """Hidden token for Parse Don't Validate pattern."""

    pass


def create_vue_component(window: Window) -> Result[VueComponent, str]:
    """Create a validated Vue component from PowerBuilder window.

    Parse Don't Validate entry point.
    """
    # Validate window structure
    if not window.name:
        return Error("Window must have a name")

    # Extract props
    props_result = _extract_props(window)
    if isinstance(props_result, Error):
        return props_result
    props = props_result.value

    # Extract emits
    emits_result = _extract_emits(window)
    if isinstance(emits_result, Error):
        return emits_result
    emits = emits_result.value

    # Generate setup function return
    setup_result = _generate_setup_return(window)
    if isinstance(setup_result, Error):
        return setup_result
    setup_return = setup_result.value

    # Generate template
    template_result = _generate_template(window)
    if isinstance(template_result, Error):
        return template_result
    template = template_result.value

    # Generate styles
    style = _generate_styles(window)

    # Create validated component with hidden token
    return Success(
        _create_component_internal(
            name=_to_pascal_case(window.name),
            props=props,
            emits=emits,
            setup_return=setup_return,
            template=template,
            style=style,
            token=_VueGeneratorToken(),
        )
    )


def _create_component_internal(
    name: str,
    props: List[VueProp],
    emits: List[VueEmit],
    setup_return: Dict[str, Any],
    template: str,
    style: Optional[VueStyle],
    token: _VueGeneratorToken,
) -> VueComponent:
    """Internal factory - requires token."""
    if not isinstance(token, _VueGeneratorToken):
        raise ValueError("Invalid token")

    return VueComponent(
        name=name,
        props=props,
        emits=emits,
        setup_return=setup_return,
        template=template,
        style=style,
        is_script_setup=True,  # Use modern <script setup> syntax
    )


# ============================================================================
# PROPS EXTRACTION
# ============================================================================


def _extract_props(window: Window) -> Result[List[VueProp], str]:
    """Extract Vue props from window properties."""
    props = []

    # Window title as prop
    if window.title:
        props.append(
            VueProp(
                name="title", type="String", default=f'"{window.title}"', required=False
            )
        )

    # Dimensions
    props.append(VueProp(name="initialWidth", type="Number", default=str(window.width)))

    props.append(
        VueProp(name="initialHeight", type="Number", default=str(window.height))
    )

    # Data prop for DataWindow controls
    if any(isinstance(c, DataWindowControl) for c in window.controls):
        props.append(
            VueProp(name="data", type="Array", default="() => []", required=False)
        )

    return Success(props)


# ============================================================================
# EMITS EXTRACTION
# ============================================================================


def _extract_emits(window: Window) -> Result[List[VueEmit], str]:
    """Extract Vue emits from window events."""
    emits = []

    for event in window.events:
        emits.append(
            VueEmit(
                name=_to_kebab_case(event.name),
                payload_type="any",  # Would need type analysis
            )
        )

    # Standard window events
    emits.extend(
        [
            VueEmit(name="close"),
            VueEmit(name="resize", payload_type="{ width: number, height: number }"),
            VueEmit(name="update:modelValue", payload_type="any"),
        ]
    )

    return Success(emits)


# ============================================================================
# SETUP FUNCTION GENERATION
# ============================================================================


def _generate_setup_return(window: Window) -> Result[Dict[str, Any], str]:
    """Generate setup function return object."""
    setup_return = {}

    # Reactive state from instance variables
    for var in window.instance_variables:
        ref_name = var.name
        setup_return[ref_name] = (
            f"ref({_convert_pb_value_to_js(var.initial_value, var.data_type)})"
        )

    # Reactive state for controls
    for control in window.controls:
        if isinstance(control, SingleLineEdit):
            setup_return[f"{control.name}Value"] = 'ref("")'
        elif isinstance(control, CheckBox):
            setup_return[f"{control.name}Checked"] = "ref(false)"
        elif isinstance(control, DataWindowControl):
            setup_return[f"{control.name}Data"] = "ref([])"
            setup_return[f"{control.name}Loading"] = "ref(false)"

    # Methods for event handlers
    for event in window.events:
        method_name = f"handle{_to_pascal_case(event.name)}"
        setup_return[method_name] = f"() => {{ /* {event.name} handler */ }}"

    # Control event handlers
    for control in window.controls:
        if isinstance(control, CommandButton):
            setup_return[f"handle{_to_pascal_case(control.name)}Click"] = (
                "() => { /* click handler */ }"
            )
        elif isinstance(control, SingleLineEdit):
            setup_return[f"handle{_to_pascal_case(control.name)}Input"] = (
                "(e: Event) => { /* input handler */ }"
            )

    return Success(setup_return)


# ============================================================================
# TEMPLATE GENERATION
# ============================================================================


def _generate_template(window: Window) -> Result[str, str]:
    """Generate Vue template from window controls."""
    lines = ["<template>"]
    lines.append(f'  <div class="{_to_kebab_case(window.name)}-container">')

    # Window title
    if window.title:
        lines.append("    <h1>{{ title }}</h1>")

    # Generate controls
    for control in window.controls:
        control_template = _control_to_template(control)
        for line in control_template:
            lines.append(f"    {line}")

    lines.append("  </div>")
    lines.append("</template>")

    return Success("\n".join(lines))


def _control_to_template(control) -> List[str]:
    """Convert PowerBuilder control to Vue template."""
    lines = []

    if isinstance(control, CommandButton):
        lines.append(
            f'<button @click="handle{_to_pascal_case(control.name)}Click" '
            f':disabled="{not control.enabled}">'
        )
        lines.append(f"  {control.text}")
        lines.append("</button>")

    elif isinstance(control, SingleLineEdit):
        lines.append(
            f"<input "
            f'v-model="{control.name}Value" '
            f'@input="handle{_to_pascal_case(control.name)}Input" '
            f'type="text" '
            f'placeholder="{control.text}" />'
        )

    elif isinstance(control, StaticText):
        lines.append(f"<span>{control.text}</span>")

    elif isinstance(control, CheckBox):
        lines.append('<div class="form-check">')
        lines.append(
            f"  <input "
            f'v-model="{control.name}Checked" '
            f'type="checkbox" '
            f'class="form-check-input" />'
        )
        lines.append(f'  <label class="form-check-label">{control.text}</label>')
        lines.append("</div>")

    elif isinstance(control, DataWindowControl):
        lines.extend(_generate_data_table_template(control))

    else:
        lines.append(f"<!-- {control.control_type}: {control.name} -->")

    return lines


def _generate_data_table_template(dw_control: DataWindowControl) -> List[str]:
    """Generate data table template for DataWindow."""
    return [
        f'<div v-if="{dw_control.name}Loading" class="loading">Loading...</div>',
        '<table v-else class="data-table">',
        "  <thead>",
        "    <tr>",
        f'      <th v-for="col in {dw_control.name}Columns" :key="col.key">',
        "        {{ col.label }}",
        "      </th>",
        "    </tr>",
        "  </thead>",
        "  <tbody>",
        f'    <tr v-for="row in {dw_control.name}Data" :key="row.id">',
        f'      <td v-for="col in {dw_control.name}Columns" :key="col.key">',
        "        {{ row[col.key] }}",
        "      </td>",
        "    </tr>",
        "  </tbody>",
        "</table>",
    ]


# ============================================================================
# STYLE GENERATION
# ============================================================================


def _generate_styles(window: Window) -> Optional[VueStyle]:
    """Generate component styles."""
    styles = []

    # Container styles
    styles.append(f".{_to_kebab_case(window.name)}-container {{")
    styles.append(f"  width: {window.width}px;")
    styles.append(f"  height: {window.height}px;")
    styles.append("  padding: 16px;")
    styles.append("  display: flex;")
    styles.append("  flex-direction: column;")
    styles.append("  gap: 12px;")
    styles.append("}")
    styles.append("")

    # Control styles
    styles.append("button {")
    styles.append("  padding: 8px 16px;")
    styles.append("  border-radius: 4px;")
    styles.append("  background-color: #007bff;")
    styles.append("  color: white;")
    styles.append("  border: none;")
    styles.append("  cursor: pointer;")
    styles.append("}")
    styles.append("")

    styles.append("button:disabled {")
    styles.append("  opacity: 0.6;")
    styles.append("  cursor: not-allowed;")
    styles.append("}")
    styles.append("")

    styles.append('input[type="text"] {')
    styles.append("  padding: 8px;")
    styles.append("  border: 1px solid #ccc;")
    styles.append("  border-radius: 4px;")
    styles.append("}")
    styles.append("")

    styles.append(".data-table {")
    styles.append("  width: 100%;")
    styles.append("  border-collapse: collapse;")
    styles.append("}")
    styles.append("")

    styles.append(".data-table th, .data-table td {")
    styles.append("  padding: 8px;")
    styles.append("  border: 1px solid #ddd;")
    styles.append("  text-align: left;")
    styles.append("}")

    return VueStyle(content="\n".join(styles), scoped=True, lang="css")


# ============================================================================
# CODE GENERATION
# ============================================================================


def generate_component_code(component: VueComponent) -> Result[str, str]:
    """Generate Vue SFC code."""
    lines = []

    # Script setup section
    lines.append('<script setup lang="ts">')
    lines.extend(_generate_script_setup(component))
    lines.append("</script>")
    lines.append("")

    # Template section
    lines.append(component.template)
    lines.append("")

    # Style section
    if component.style:
        scoped = " scoped" if component.style.scoped else ""
        lines.append(f'<style{scoped} lang="{component.style.lang}">')
        lines.append(component.style.content)
        lines.append("</style>")

    return Success("\n".join(lines))


def _generate_script_setup(component: VueComponent) -> List[str]:
    """Generate script setup content."""
    lines = []

    # Imports
    lines.append("import { ref, computed, watch, onMounted } from 'vue'")
    if component.props:
        lines.append("import type { PropType } from 'vue'")
    lines.append("")

    # Props definition
    if component.props:
        lines.append("const props = defineProps({")
        for prop in component.props:
            required = ", required: true" if prop.required else ""
            default_val = f", default: {prop.default}" if prop.default else ""
            lines.append(f"  {prop.name}: {{")
            lines.append(
                f"    type: {prop.type} as PropType<{_vue_type_to_ts(prop.type)}>,"
            )
            if required:
                lines.append("    required: true,")
            if default_val:
                lines.append(f"    default: {prop.default},")
            lines.append("  },")
        lines.append("})")
        lines.append("")

    # Emits definition
    if component.emits:
        emit_names = ", ".join(f'"{emit.name}"' for emit in component.emits)
        lines.append(f"const emit = defineEmits([{emit_names}])")
        lines.append("")

    # Setup return values
    for key, value in component.setup_return.items():
        if "ref(" in str(value):
            lines.append(f"const {key} = {value}")
        elif "=>" in str(value):
            lines.append(f"const {key} = {value}")

    # Lifecycle hooks
    lines.append("")
    lines.append("onMounted(() => {")
    lines.append("  // Component mounted")
    lines.append("})")

    return lines


# ============================================================================
# PINIA STORE GENERATION
# ============================================================================


def create_pinia_store(window: Window) -> Result[PiniaStore, str]:
    """Create Pinia store for window state management."""
    store_name = f"{_to_camel_case(window.name)}Store"

    # Extract state
    state = {}
    for var in window.instance_variables:
        state[var.name] = _convert_pb_value_to_js(var.initial_value, var.data_type)

    # Generate getters
    getters = {
        "hasData": "state => state.data && state.data.length > 0",
        "isLoading": "state => state.loading === true",
    }

    # Generate actions
    actions = {}
    for event in window.events:
        action_name = _to_camel_case(event.name)
        actions[action_name] = f"async function() {{ /* {event.name} logic */ }}"

    return Success(
        PiniaStore(id=store_name, state=state, getters=getters, actions=actions)
    )


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


def _convert_pb_value_to_js(value: Any, pb_type: str) -> str:
    """Convert PowerBuilder value to JavaScript literal."""
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


def _vue_type_to_ts(vue_type: str) -> str:
    """Convert Vue prop type to TypeScript type."""
    type_map = {
        "String": "string",
        "Number": "number",
        "Boolean": "boolean",
        "Array": "any[]",
        "Object": "Record<string, any>",
        "Date": "Date",
        "Function": "(...args: any[]) => any",
    }
    return type_map.get(vue_type, "any")


# ============================================================================
# EVENT EMISSION
# ============================================================================


def emit_component_created(
    component: VueComponent, source_window: Window
) -> VueComponentCreated:
    """Emit component created event."""
    return VueComponentCreated(component=component, props={}, timestamp=datetime.now())
