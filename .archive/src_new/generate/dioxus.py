"""Dioxus Generator - Generate Rust/Dioxus desktop applications.

This module generates Rust desktop applications using the Dioxus framework
from PowerBuilder semantic models.
"""

import logging
from typing import List, Optional

from src_new._core import (
    ApplicationModel,
    GeneratedFile,
    Method,
    ObjectType,
    SemanticObject,
    TargetLanguage,
)
from .generator import BaseCodeGenerator

logger = logging.getLogger(__name__)


class DioxusGenerator(BaseCodeGenerator):
    """Generator for Dioxus/Rust applications."""

    def __init__(self):
        """Initialize Dioxus generator."""
        super().__init__(TargetLanguage.DIOXUS)

        self.type_map = {
            "string": "String",
            "char": "char",
            "int": "i32",
            "integer": "i32",
            "long": "i64",
            "decimal": "f64",
            "float": "f32",
            "double": "f64",
            "boolean": "bool",
            "bool": "bool",
            "date": "chrono::NaiveDate",
            "datetime": "chrono::DateTime<Utc>",
            "blob": "Vec<u8>",
            "any": "serde_json::Value",
            "object": "HashMap<String, serde_json::Value>",
        }

    def generate_window(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate Dioxus component from window.

        Args:
            obj: Window object

        Returns:
            Generated Rust files
        """
        files = []

        # Generate component module
        component = self._generate_component(obj)
        files.append(
            GeneratedFile(
                path=f"src/components/{obj.name.lower()}.rs",
                content=component,
                language=TargetLanguage.DIOXUS,
            )
        )

        return files

    def generate_datawindow(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate Dioxus data table component.

        Args:
            obj: DataWindow object

        Returns:
            Generated Rust files
        """
        files = []

        # Generate data model
        model = self._generate_model(obj)
        files.append(
            GeneratedFile(
                path=f"src/models/{obj.name.lower()}.rs",
                content=model,
                language=TargetLanguage.DIOXUS,
            )
        )

        # Generate table component
        table = self._generate_table_component(obj)
        files.append(
            GeneratedFile(
                path=f"src/components/{obj.name.lower()}_table.rs",
                content=table,
                language=TargetLanguage.DIOXUS,
            )
        )

        return files

    def generate_config(self, model: ApplicationModel) -> List[GeneratedFile]:
        """Generate Rust/Dioxus project configuration.

        Args:
            model: Application model

        Returns:
            Configuration files
        """
        files = []

        # Generate Cargo.toml
        cargo = self._generate_cargo_toml(model)
        files.append(
            GeneratedFile(
                path="Cargo.toml",
                content=cargo,
                language=TargetLanguage.DIOXUS,
                file_type="config",
            )
        )

        # Generate main.rs
        main_rs = self._generate_main(model)
        files.append(
            GeneratedFile(
                path="src/main.rs",
                content=main_rs,
                language=TargetLanguage.DIOXUS,
            )
        )

        # Generate lib.rs
        lib_rs = self._generate_lib(model)
        files.append(
            GeneratedFile(
                path="src/lib.rs",
                content=lib_rs,
                language=TargetLanguage.DIOXUS,
            )
        )

        # Generate app.rs
        app_rs = self._generate_app(model)
        files.append(
            GeneratedFile(
                path="src/app.rs",
                content=app_rs,
                language=TargetLanguage.DIOXUS,
            )
        )

        return files

    def _generate_component(self, obj: SemanticObject) -> str:
        """Generate Dioxus component.

        Args:
            obj: Semantic object

        Returns:
            Component code
        """
        lines = []
        comp_name = self._to_pascal_case(obj.name)

        # Imports
        lines.append("use dioxus::prelude::*;")
        lines.append("use serde::{Deserialize, Serialize};")
        lines.append("")

        # Props struct
        if obj.properties:
            lines.append("#[derive(Props, PartialEq, Clone)]")
            lines.append(f"pub struct {comp_name}Props {{")
            for prop in obj.properties[:5]:  # First 5 as props
                if prop.access != "private":
                    rust_type = self._map_type(prop.type)
                    optional = "Option<" if not prop.is_required else ""
                    optional_close = ">" if not prop.is_required else ""
                    lines.append(
                        f"    pub {prop.name}: {optional}{rust_type}{optional_close},"
                    )
            lines.append("}")
            lines.append("")

        # Component function
        lines.append("#[component]")
        props_param = f"props: {comp_name}Props" if obj.properties else ""
        lines.append(f"pub fn {comp_name}({props_param}) -> Element {{")

        # State hooks
        lines.append("    // Component state")
        for prop in obj.properties[:3]:  # First 3 as state
            default_val = self._get_default_value(prop.type)
            lines.append(f"    let mut {prop.name} = use_signal(|| {default_val});")
        lines.append("")

        # Effects
        lines.append("    // Effects")
        lines.append("    use_effect(move || {")
        lines.append('        println!("Component mounted");')
        lines.append("    });")
        lines.append("")

        # Event handlers
        if obj.events:
            lines.append("    // Event handlers")
            for event in obj.events[:3]:
                lines.append(f"    let on_{event.name} = move |_| {{")
                lines.append(f'        println!("Handle {event.name}");')
                if event.body:
                    lines.append(f"        // {event.body}")
                lines.append("    };")
                lines.append("")

        # Render
        lines.append("    rsx! {")
        lines.append("        div {")
        lines.append('            class: "container",')
        lines.append("            ")
        lines.append("            h1 {")
        lines.append(f'                "{obj.name}"')
        lines.append("            }")
        lines.append("            ")

        # Form fields
        for prop in obj.properties[:4]:
            if prop.access != "private":
                lines.append("            div {")
                lines.append('                class: "form-group",')
                lines.append("                label {")
                lines.append(f'                    "{prop.name}: "')
                lines.append("                }")
                lines.append("                input {")
                lines.append('                    r#type: "text",')
                lines.append(f'                    value: "{{{prop.name}()}}",')
                lines.append(
                    f"                    oninput: move |evt| {prop.name}.set(evt.value()),"
                )
                lines.append("                }")
                lines.append("            }")

        # Submit button
        lines.append("            ")
        lines.append("            button {")
        lines.append("                onclick: move |_| {")
        lines.append('                    println!("Submit clicked");')
        lines.append("                },")
        lines.append('                "Submit"')
        lines.append("            }")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")

        return "\n".join(lines)

    def _generate_model(self, obj: SemanticObject) -> str:
        """Generate Rust data model.

        Args:
            obj: DataWindow object

        Returns:
            Model code
        """
        lines = []
        struct_name = self._to_pascal_case(obj.name)

        lines.append("use serde::{Deserialize, Serialize};")
        lines.append("use chrono::{DateTime, Utc};")
        lines.append("")

        lines.append("#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]")
        lines.append(f"pub struct {struct_name} {{")

        for prop in obj.properties:
            rust_type = self._map_type(prop.type)
            visibility = "" if prop.access == "private" else "pub "
            optional = "Option<" if not prop.is_required else ""
            optional_close = ">" if not prop.is_required else ""
            lines.append(
                f"    {visibility}{prop.name}: {optional}{rust_type}{optional_close},"
            )

        lines.append("}")
        lines.append("")

        # Implement Default
        lines.append(f"impl Default for {struct_name} {{")
        lines.append("    fn default() -> Self {")
        lines.append("        Self {")
        for prop in obj.properties:
            default_val = self._get_default_value(prop.type)
            if not prop.is_required:
                default_val = "None"
            lines.append(f"            {prop.name}: {default_val},")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")
        lines.append("")

        # Add methods
        if obj.methods:
            lines.append(f"impl {struct_name} {{")
            for method in obj.methods[:5]:
                if method.access != "private":
                    lines.extend(self._generate_method(method))
                    lines.append("")
            lines.append("}")

        return "\n".join(lines)

    def _generate_table_component(self, obj: SemanticObject) -> str:
        """Generate table component.

        Args:
            obj: DataWindow object

        Returns:
            Table component code
        """
        lines = []
        comp_name = f"{self._to_pascal_case(obj.name)}Table"
        model_name = self._to_pascal_case(obj.name)

        lines.append("use dioxus::prelude::*;")
        lines.append(f"use crate::models::{obj.name.lower()}::{model_name};")
        lines.append("")

        lines.append("#[component]")
        lines.append(f"pub fn {comp_name}() -> Element {{")
        lines.append(f"    let mut data = use_signal(|| Vec::<{model_name}>::new());")
        lines.append("    let mut selected = use_signal(|| None::<usize>);")
        lines.append("")

        lines.append("    // Load data")
        lines.append("    use_effect(move || {")
        lines.append("        // Fetch data from API")
        lines.append("        spawn(async move {")
        lines.append("            // let fetched_data = fetch_data().await;")
        lines.append("            // data.set(fetched_data);")
        lines.append("        });")
        lines.append("    });")
        lines.append("")

        lines.append("    rsx! {")
        lines.append("        div {")
        lines.append('            class: "table-container",')
        lines.append("            ")
        lines.append("            table {")
        lines.append('                class: "data-table",')
        lines.append("                ")
        lines.append("                thead {")
        lines.append("                    tr {")

        # Headers
        for prop in obj.properties[:6]:
            if prop.access != "private":
                lines.append("                        th {")
                lines.append(
                    f'                            "{self._to_title(prop.name)}"'
                )
                lines.append("                        }")

        lines.append("                    }")
        lines.append("                }")
        lines.append("                ")
        lines.append("                tbody {")
        lines.append(
            "                    for (idx, item) in data().iter().enumerate() {"
        )
        lines.append("                        tr {")
        lines.append('                            key: "{idx}",')
        lines.append(
            '                            class: if selected() == Some(idx) { "selected" } else { "" },'
        )
        lines.append(
            "                            onclick: move |_| selected.set(Some(idx)),"
        )

        # Data cells
        for prop in obj.properties[:6]:
            if prop.access != "private":
                lines.append("                            td {")
                lines.append(f'                                "{{item.{prop.name}}}"')
                lines.append("                            }")

        lines.append("                        }")
        lines.append("                    }")
        lines.append("                }")
        lines.append("            }")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")

        return "\n".join(lines)

    def _generate_method(self, method: Method) -> List[str]:
        """Generate Rust method.

        Args:
            method: Method object

        Returns:
            Method code lines
        """
        lines = []

        # Method signature
        visibility = "" if method.access == "private" else "pub "
        params = self._format_parameters(method.parameters)
        return_type = self._map_type(method.return_type) if method.return_type else "()"

        lines.append(f"    {visibility}fn {method.name}({params}) -> {return_type} {{")

        # Method body
        if method.body:
            lines.append(f"        // {method.body}")

        # Default return
        if method.return_type:
            default_return = self._get_default_value(method.return_type)
            lines.append(f"        {default_return}")

        lines.append("    }")

        return lines

    def _generate_cargo_toml(self, model: ApplicationModel) -> str:
        """Generate Cargo.toml.

        Args:
            model: Application model

        Returns:
            Cargo.toml content
        """
        lines = []

        lines.append("[package]")
        lines.append(f'name = "{model.name.lower().replace(" ", "_")}"')
        lines.append(f'version = "{model.version}"')
        lines.append('edition = "2021"')
        lines.append("")

        lines.append("[dependencies]")
        lines.append('dioxus = { version = "0.5", features = ["desktop", "router"] }')
        lines.append('dioxus-desktop = "0.5"')
        lines.append('tokio = { version = "1", features = ["full"] }')
        lines.append('serde = { version = "1.0", features = ["derive"] }')
        lines.append('serde_json = "1.0"')
        lines.append('chrono = { version = "0.4", features = ["serde"] }')
        lines.append('reqwest = { version = "0.11", features = ["json"] }')
        lines.append('log = "0.4"')
        lines.append('env_logger = "0.10"')
        lines.append("")

        lines.append("[profile.release]")
        lines.append('opt-level = "z"')
        lines.append("lto = true")
        lines.append("codegen-units = 1")
        lines.append('panic = "abort"')
        lines.append("strip = true")

        return "\n".join(lines)

    def _generate_main(self, model: ApplicationModel) -> str:
        """Generate main.rs.

        Args:
            model: Application model

        Returns:
            main.rs content
        """
        lines = []

        lines.append("#![allow(non_snake_case)]")
        lines.append("")
        lines.append("use dioxus::prelude::*;")
        lines.append("use dioxus_desktop::{Config, WindowBuilder};")
        lines.append("")
        lines.append("mod app;")
        lines.append("mod components;")
        lines.append("mod models;")
        lines.append("")
        lines.append("use app::App;")
        lines.append("")

        lines.append("fn main() {")
        lines.append("    env_logger::init();")
        lines.append("    ")
        lines.append("    let config = Config::new()")
        lines.append("        .with_window(WindowBuilder::new()")
        lines.append(f'            .with_title("{model.name}")')
        lines.append("            .with_resizable(true)")
        lines.append(
            "            .with_inner_size(dioxus_desktop::LogicalSize::new(1280.0, 720.0)));"
        )
        lines.append("    ")
        lines.append("    dioxus_desktop::launch_cfg(App, config);")
        lines.append("}")

        return "\n".join(lines)

    def _generate_lib(self, model: ApplicationModel) -> str:
        """Generate lib.rs.

        Args:
            model: Application model

        Returns:
            lib.rs content
        """
        lines = []

        lines.append("pub mod components {")
        for obj_name in list(model.objects.keys())[:10]:
            lines.append(f"    pub mod {obj_name.lower()};")
        lines.append("}")
        lines.append("")

        lines.append("pub mod models {")
        for obj_name in list(model.objects.keys())[:10]:
            obj = model.objects[obj_name]
            if obj.type == ObjectType.DATAWINDOW:
                lines.append(f"    pub mod {obj_name.lower()};")
        lines.append("}")

        return "\n".join(lines)

    def _generate_app(self, model: ApplicationModel) -> str:
        """Generate app.rs.

        Args:
            model: Application model

        Returns:
            app.rs content
        """
        lines = []

        lines.append("use dioxus::prelude::*;")
        lines.append("use dioxus_router::prelude::*;")
        lines.append("")

        # Import components
        for obj_name in list(model.objects.keys())[:5]:
            comp_name = self._to_pascal_case(obj_name)
            lines.append(f"use crate::components::{obj_name.lower()}::{comp_name};")
        lines.append("")

        # Routes enum
        lines.append("#[derive(Clone, Routable, PartialEq)]")
        lines.append("enum Route {")
        lines.append('    #[route("/")]')
        lines.append("    Home {},")

        for obj_name in list(model.objects.keys())[:5]:
            comp_name = self._to_pascal_case(obj_name)
            path = obj_name.lower()
            lines.append(f'    #[route("/{path}")]')
            lines.append(f"    {comp_name} {{}},")

        lines.append("}")
        lines.append("")

        lines.append("#[component]")
        lines.append("pub fn App() -> Element {")
        lines.append("    rsx! {")
        lines.append("        Router::<Route> {}")
        lines.append("    }")
        lines.append("}")
        lines.append("")

        lines.append("#[component]")
        lines.append("fn Home() -> Element {")
        lines.append("    rsx! {")
        lines.append("        div {")
        lines.append(f'            h1 {{ "Welcome to {model.name}" }}')
        lines.append("            nav {")
        lines.append("                ul {")

        for obj_name in list(model.objects.keys())[:5]:
            path = obj_name.lower()
            lines.append("                    li {")
            lines.append(
                f'                        Link {{ to: Route::{self._to_pascal_case(obj_name)} {{}}, "{obj_name}" }}'
            )
            lines.append("                    }")

        lines.append("                }")
        lines.append("            }")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")

        return "\n".join(lines)

    def _format_parameters(self, parameters: Optional[List]) -> str:
        """Format method parameters.

        Args:
            parameters: Method parameters

        Returns:
            Formatted parameters
        """
        if not parameters:
            return "&self"

        params = ["&self"]
        for param in parameters:
            rust_type = self._map_type(param.type)
            ref_prefix = "&" if param.is_ref else ""
            params.append(f"{param.name}: {ref_prefix}{rust_type}")

        return ", ".join(params)

    def _map_type(self, pb_type: Optional[str]) -> str:
        """Map PowerBuilder type to Rust.

        Args:
            pb_type: PowerBuilder type

        Returns:
            Rust type
        """
        if not pb_type:
            return "()"

        type_lower = pb_type.lower()
        return self.type_map.get(type_lower, "String")

    def _get_default_value(self, pb_type: str) -> str:
        """Get default value for type.

        Args:
            pb_type: PowerBuilder type

        Returns:
            Default value
        """
        rust_type = self._map_type(pb_type)

        if rust_type == "String":
            return "String::new()"
        elif rust_type in ["i32", "i64", "f32", "f64"]:
            return "0"
        elif rust_type == "bool":
            return "false"
        elif rust_type == "Vec<u8>":
            return "Vec::new()"
        elif "HashMap" in rust_type:
            return "HashMap::new()"
        elif "chrono" in rust_type:
            return "chrono::Utc::now()"
        else:
            return "Default::default()"

    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase.

        Args:
            name: Original name

        Returns:
            PascalCase name
        """
        parts = name.replace("_", " ").replace("-", " ").split()
        return "".join(word.capitalize() for word in parts)

    def _to_title(self, name: str) -> str:
        """Convert to title case.

        Args:
            name: Original name

        Returns:
            Title case
        """
        return name.replace("_", " ").replace("-", " ").title()
