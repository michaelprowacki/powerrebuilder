"""Dioxus (Rust) Code Generator.

Generates Dioxus web/desktop applications from PowerBuilder semantic models.
"""

import logging
from pathlib import Path

from src_new._core.models import (
    ApplicationModel,
    GeneratedFile,
    GeneratedProject,
    Method,
    ObjectType,
    Property,
    SemanticObject,
    TargetLanguage,
)
from .generator import BaseCodeGenerator

logger = logging.getLogger(__name__)


class DioxusGenerator(BaseCodeGenerator):
    """Generate Dioxus (Rust) web/desktop applications."""

    def __init__(self, input_path: Path, output_path: Path):
        """Initialize Dioxus generator.

        Args:
            input_path: Path to model files
            output_path: Output directory for Dioxus app
        """
        from src_new._core.models import TargetLanguage

        super().__init__(TargetLanguage.DIOXUS)
        self.input_path = input_path
        self.output_path = output_path
        self.app_name = "powerbuilder_app"
        self.generated_files = []

    def generate_project(self, data: ApplicationModel) -> GeneratedProject:
        """Generate Dioxus project from application model.

        Args:
            data: Application model

        Returns:
            Generated Dioxus project
        """
        self.app_name = data.name.lower().replace(" ", "_")

        project = GeneratedProject(
            name=self.app_name, target=TargetLanguage.DIOXUS, files=[]
        )

        # Generate Cargo.toml
        project.files.append(self._generate_cargo_toml(data))

        # Generate main.rs
        project.files.append(self._generate_main_rs(data))

        # Generate app module
        project.files.append(self._generate_app_rs(data))

        # Generate components for windows
        for obj in data.objects:
            if obj.type == ObjectType.WINDOW:
                project.files.append(self._generate_component(obj))

        # Generate models
        for obj in data.objects:
            if obj.type in [ObjectType.USER_OBJECT, ObjectType.STRUCTURE]:
                project.files.append(self._generate_model(obj))

        # Generate state management
        project.files.append(self._generate_state_rs(data))

        # Generate Dioxus.toml config
        project.files.append(self._generate_dioxus_config(data))

        return project

    def _generate_cargo_toml(self, app: ApplicationModel) -> GeneratedFile:
        """Generate Cargo.toml file."""
        content = f'''[package]
name = "{self.app_name}"
version = "{app.version}"
edition = "2021"

[dependencies]
dioxus = {{ version = "0.5", features = ["desktop", "router", "fermi"] }}
dioxus-desktop = "0.5"
serde = {{ version = "1", features = ["derive"] }}
serde_json = "1"
tokio = {{ version = "1", features = ["full"] }}
futures = "0.3"
chrono = {{ version = "0.4", features = ["serde"] }}
uuid = {{ version = "1", features = ["v4", "serde"] }}
thiserror = "1"
anyhow = "1"
tracing = "0.1"
tracing-subscriber = "0.3"

# Optional database support
sqlx = {{ version = "0.7", features = ["runtime-tokio-native-tls", "sqlite"], optional = true }}

[features]
default = ["database"]
database = ["sqlx"]

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
'''
        return GeneratedFile(path=Path("Cargo.toml"), content=content, language="toml")

    def _generate_main_rs(self, app: ApplicationModel) -> GeneratedFile:
        """Generate main.rs file."""
        content = f'''//! {app.name} - Dioxus Application
//! Generated from PowerBuilder application

use dioxus::prelude::*;
use dioxus_desktop::{{Config, WindowBuilder}};

mod app;
mod components;
mod models;
mod state;

fn main() {{
    // Initialize tracing
    tracing_subscriber::fmt::init();

    // Configure the desktop application
    let config = Config::new()
        .with_window(
            WindowBuilder::new()
                .with_title("{app.name}")
                .with_inner_size(dioxus_desktop::LogicalSize::new(1200.0, 800.0))
                .with_resizable(true)
        );

    // Launch the app
    dioxus_desktop::launch_cfg(app::App, config);
}}
'''
        return GeneratedFile(path=Path("src/main.rs"), content=content, language="rust")

    def _generate_app_rs(self, app: ApplicationModel) -> GeneratedFile:
        """Generate app.rs with main application component."""
        # Find main window
        main_window = next(
            (obj for obj in app.objects if obj.type == ObjectType.WINDOW), None
        )

        content = f'''//! Main Application Component
//! Generated from PowerBuilder application

use dioxus::prelude::*;
use crate::state::AppState;
use crate::components::*;

/// Main application component
#[component]
pub fn App() -> Element {{
    // Initialize application state
    use_context_provider(|| Signal::new(AppState::new()));

    rsx! {{
        Router::<Route> {{}}
    }}
}}

/// Application routes
#[derive(Clone, Routable, Debug, PartialEq)]
pub enum Route {{
    #[layout(NavBar)]
    #[route("/")]
    Home {{}},

    #[route("/windows/:name")]
    Window {{ name: String }},

    #[route("/about")]
    About {{}},
}}

/// Navigation bar component
#[component]
fn NavBar() -> Element {{
    rsx! {{
        nav {{
            class: "navbar",
            div {{
                class: "navbar-brand",
                "{app.name}"
            }}
            div {{
                class: "navbar-menu",
                Link {{
                    to: Route::Home {{}},
                    "Home"
                }}
                Link {{
                    to: Route::About {{}},
                    "About"
                }}
            }}
        }}
        Outlet::<Route> {{}}
    }}
}}

/// Home page component
#[component]
fn Home() -> Element {{
    let state = use_context::<Signal<AppState>>();

    rsx! {{
        div {{
            class: "container",
            h1 {{ "{app.name}" }}
            p {{ "Version: {app.version}" }}
            p {{ "Converted from PowerBuilder with PowerRebuilder" }}

            div {{
                class: "window-list",
                h2 {{ "Available Windows" }}
                // List all windows
                // TODO: Add dynamic window list here
            }}
        }}
    }}
}}

/// About page component
#[component]
fn About() -> Element {{
    rsx! {{
        div {{
            class: "container",
            h1 {{ "About" }}
            p {{ "This application was generated from a PowerBuilder application using PowerRebuilder." }}
            p {{ "Original application: {app.name}" }}
            p {{ "Version: {app.version}" }}
        }}
    }}
}}
'''
        return GeneratedFile(path=Path("src/app.rs"), content=content, language="rust")

    def _generate_component(self, obj: SemanticObject) -> GeneratedFile:
        """Generate a Dioxus component for a window."""
        # Generate form fields for properties
        fields = []
        for prop in obj.properties:
            fields.append(self._generate_form_field(prop))

        # Generate event handlers for methods
        handlers = []
        for method in obj.methods:
            handlers.append(self._generate_event_handler(method))

        content = f'''//! {obj.name} Component
//! Generated from PowerBuilder window

use dioxus::prelude::*;
use crate::models::*;
use crate::state::AppState;

/// {obj.description or obj.name} window component
#[component]
pub fn {obj.name}() -> Element {{
    let state = use_context::<Signal<AppState>>();
    let mut form_data = use_signal(|| {obj.name}Data::default());

    rsx! {{
        div {{
            class: "window {obj.name.lower()}",
            h2 {{ "{obj.name}" }}

            form {{
                onsubmit: move |evt| {{
                    evt.prevent_default();
                    // Handle form submission
                    tracing::info!("Form submitted: {{:?}}", form_data.read());
                }},

                {"".join(fields)}

                div {{
                    class: "form-actions",
                    button {{
                        r#type: "submit",
                        "Submit"
                    }}
                    button {{
                        r#type: "button",
                        onclick: move |_| {{
                            form_data.set({obj.name}Data::default());
                        }},
                        "Reset"
                    }}
                }}
            }}
        }}
    }}
}}

/// Form data for {obj.name}
#[derive(Debug, Clone, Default)]
struct {obj.name}Data {{
    // Limited to first 5 properties for demo
    {", ".join(f"pub {prop.name}: String" for prop in obj.properties[:5])}
}}
'''
        return GeneratedFile(
            path=Path(f"src/components/{obj.name.lower()}.rs"),
            content=content,
            language="rust",
        )

    def _generate_form_field(self, prop: Property) -> str:
        """Generate a form field for a property."""
        return f'''
                div {{
                    class: "form-field",
                    label {{
                        r#for: "{prop.name}",
                        "{prop.name}:"
                    }}
                    input {{
                        r#type: "text",
                        id: "{prop.name}",
                        value: "{{form_data.read().{prop.name}}}",
                        oninput: move |evt| {{
                            form_data.write().{prop.name} = evt.value();
                        }}
                    }}
                }}'''

    def _generate_event_handler(self, method: Method) -> str:
        """Generate an event handler for a method."""
        return f"""
    // Handler for {method.name}
    let handle_{method.name} = move |_| {{
        tracing::info!("Executing {method.name}");
        // TODO: Implement {method.name} logic
    }};"""

    def _generate_model(self, obj: SemanticObject) -> GeneratedFile:
        """Generate a Rust model struct."""
        fields = []
        for prop in obj.properties:
            rust_type = self._pb_to_rust_type(prop.data_type)
            fields.append(f"    pub {prop.name}: {rust_type},")

        content = f"""//! {obj.name} Model
//! Generated from PowerBuilder {obj.type.value}

use serde::{{Deserialize, Serialize}};
use chrono::{{DateTime, Utc}};

/// {obj.description or obj.name}
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct {obj.name} {{
{"\n".join(fields)}
}}

impl {obj.name} {{
    /// Create new instance
    pub fn new() -> Self {{
        Self {{
            {", ".join(f"{prop.name}: Default::default()" for prop in obj.properties)}
        }}
    }}
}}

impl Default for {obj.name} {{
    fn default() -> Self {{
        Self::new()
    }}
}}
"""
        return GeneratedFile(
            path=Path(f"src/models/{obj.name.lower()}.rs"),
            content=content,
            language="rust",
        )

    def _generate_state_rs(self, app: ApplicationModel) -> GeneratedFile:
        """Generate state management module."""
        content = f'''//! Application State Management
//! Generated from PowerBuilder application

use std::collections::HashMap;
use serde_json::Value;

/// Application state
#[derive(Debug, Clone)]
pub struct AppState {{
    pub app_name: String,
    pub version: String,
    pub data: HashMap<String, Value>,
}}

impl AppState {{
    /// Create new application state
    pub fn new() -> Self {{
        Self {{
            app_name: "{app.name}".to_string(),
            version: "{app.version}".to_string(),
            data: HashMap::new(),
        }}
    }}

    /// Get a value from state
    pub fn get(&self, key: &str) -> Option<&Value> {{
        self.data.get(key)
    }}

    /// Set a value in state
    pub fn set(&mut self, key: String, value: Value) {{
        self.data.insert(key, value);
    }}

    /// Clear all state data
    pub fn clear(&mut self) {{
        self.data.clear();
    }}
}}

impl Default for AppState {{
    fn default() -> Self {{
        Self::new()
    }}
}}
'''
        return GeneratedFile(
            path=Path("src/state.rs"), content=content, language="rust"
        )

    def _generate_dioxus_config(self, app: ApplicationModel) -> GeneratedFile:
        """Generate Dioxus.toml configuration."""
        content = f'''[application]
name = "{self.app_name}"
default_platform = "desktop"

[application.tools]
out_dir = "dist"

[web.app]
title = "{app.name}"

[web.watcher]
watch_path = ["src"]

[desktop]
prerender = false

[[desktop.window]]
title = "{app.name}"
width = 1200
height = 800
resizable = true
'''
        return GeneratedFile(path=Path("Dioxus.toml"), content=content, language="toml")

    def _pb_to_rust_type(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Rust type."""
        type_map = {
            "integer": "i32",
            "long": "i64",
            "decimal": "f64",
            "real": "f32",
            "string": "String",
            "boolean": "bool",
            "date": "chrono::NaiveDate",
            "datetime": "DateTime<Utc>",
            "time": "chrono::NaiveTime",
            "blob": "Vec<u8>",
            "char": "char",
            "any": "serde_json::Value",
        }
        return type_map.get(pb_type.lower(), "serde_json::Value")
