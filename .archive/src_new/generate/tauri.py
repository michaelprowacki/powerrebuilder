"""Tauri (Rust) Code Generator.

Generates Tauri desktop applications from PowerBuilder semantic models.
"""

import logging
from pathlib import Path

from src_new._core.models import (
    ApplicationModel,
    GeneratedFile,
    GeneratedProject,
    Method,
    ObjectType,
    SemanticObject,
    TargetLanguage,
)
from .generator import BaseCodeGenerator

logger = logging.getLogger(__name__)


class TauriGenerator(BaseCodeGenerator):
    """Generate Tauri (Rust) desktop applications."""

    def __init__(self, input_path: Path, output_path: Path):
        """Initialize Tauri generator.

        Args:
            input_path: Path to model files
            output_path: Output directory for Tauri app
        """
        from src_new._core.models import TargetLanguage

        super().__init__(TargetLanguage.TAURI)
        self.input_path = input_path
        self.output_path = output_path
        self.app_name = "powerbuilder_app"
        self.generated_files = []

    def generate_project(self, data: ApplicationModel) -> GeneratedProject:
        """Generate Tauri project from application model.

        Args:
            data: Application model

        Returns:
            Generated Tauri project
        """
        self.app_name = data.name.lower().replace(" ", "_")

        project = GeneratedProject(
            name=self.app_name, target=TargetLanguage.TAURI, files=[]
        )

        # Generate Cargo.toml
        project.files.append(self._generate_cargo_toml(data))

        # Generate main.rs
        project.files.append(self._generate_main_rs(data))

        # Generate lib.rs with commands
        project.files.append(self._generate_lib_rs(data))

        # Generate models
        for obj in data.objects:
            if obj.type in [ObjectType.USER_OBJECT, ObjectType.STRUCTURE]:
                project.files.append(self._generate_model(obj))

        # Generate windows/views
        for obj in data.objects:
            if obj.type == ObjectType.WINDOW:
                project.files.append(self._generate_window(obj))

        # Generate tauri.conf.json
        project.files.append(self._generate_tauri_config(data))

        # Generate frontend index.html
        project.files.append(self._generate_index_html(data))

        return project

    def _generate_cargo_toml(self, app: ApplicationModel) -> GeneratedFile:
        """Generate Cargo.toml file."""
        content = f'''[package]
name = "{self.app_name}"
version = "{app.version}"
edition = "2021"

[dependencies]
tauri = {{ version = "2.0", features = ["shell-open"] }}
serde = {{ version = "1", features = ["derive"] }}
serde_json = "1"
tokio = {{ version = "1", features = ["full"] }}
sqlx = {{ version = "0.7", features = ["runtime-tokio-native-tls", "sqlite"] }}
chrono = {{ version = "0.4", features = ["serde"] }}
uuid = {{ version = "1", features = ["v4", "serde"] }}
thiserror = "1"
anyhow = "1"

[dependencies.tauri-plugin-shell]
version = "2.0"

[build-dependencies]
tauri-build = {{ version = "2.0", features = [] }}

[profile.release]
panic = "abort"
codegen-units = 1
lto = true
opt-level = "s"
strip = true
'''
        return GeneratedFile(path=Path("Cargo.toml"), content=content, language="toml")

    def _generate_main_rs(self, app: ApplicationModel) -> GeneratedFile:
        """Generate main.rs file."""
        content = f'''//! {app.name} - Tauri Application
//! Generated from PowerBuilder application

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::Manager;

mod commands;
mod models;
mod state;

fn main() {{
    tauri::Builder::default()
        .setup(|app| {{
            // Initialize application state
            let app_state = state::AppState::new();
            app.manage(app_state);

            // Setup window
            let window = app.get_webview_window("main").unwrap();
            window.set_title("{app.name}").unwrap();

            Ok(())
        }})
        .invoke_handler(tauri::generate_handler![
            commands::get_version,
            commands::get_objects,
            commands::execute_method,
            commands::get_property,
            commands::set_property,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}}
'''
        return GeneratedFile(path=Path("src/main.rs"), content=content, language="rust")

    def _generate_lib_rs(self, app: ApplicationModel) -> GeneratedFile:
        """Generate lib.rs with commands."""
        # Find business objects
        business_objects = [
            obj for obj in app.objects if obj.type == ObjectType.USER_OBJECT
        ]

        commands = []
        for obj in business_objects:
            for method in obj.methods:
                commands.append(self._generate_command(obj, method))

        content = f'''//! Tauri Commands
//! Generated from PowerBuilder business logic

use serde::{{Deserialize, Serialize}};
use tauri::State;

pub mod models;
pub mod state;

use crate::state::AppState;

/// Get application version
#[tauri::command]
pub fn get_version() -> String {{
    "{app.version}".to_string()
}}

/// Get all objects
#[tauri::command]
pub fn get_objects(state: State<AppState>) -> Vec<String> {{
    state.get_object_names()
}}

/// Execute a method on an object
#[tauri::command]
pub async fn execute_method(
    object_name: String,
    method_name: String,
    params: Vec<serde_json::Value>,
    state: State<'_, AppState>,
) -> Result<serde_json::Value, String> {{
    state.execute_method(&object_name, &method_name, params)
        .map_err(|e| e.to_string())
}}

/// Get property value
#[tauri::command]
pub fn get_property(
    object_name: String,
    property_name: String,
    state: State<AppState>,
) -> Result<serde_json::Value, String> {{
    state.get_property(&object_name, &property_name)
        .map_err(|e| e.to_string())
}}

/// Set property value
#[tauri::command]
pub fn set_property(
    object_name: String,
    property_name: String,
    value: serde_json::Value,
    state: State<'_, AppState>,
) -> Result<(), String> {{
    state.set_property(&object_name, &property_name, value)
        .map_err(|e| e.to_string())
}}

{"".join(commands)}
'''
        return GeneratedFile(
            path=Path("src/commands.rs"), content=content, language="rust"
        )

    def _generate_command(self, obj: SemanticObject, method: Method) -> str:
        """Generate a Tauri command for a method."""
        # Convert PowerBuilder types to Rust types
        param_types = []
        for param in method.parameters:
            rust_type = self._pb_to_rust_type(param.data_type)
            param_types.append(f"{param.name}: {rust_type}")

        return_type = (
            self._pb_to_rust_type(method.return_type) if method.return_type else "()"
        )

        return f"""
/// {method.description or method.name}
#[tauri::command]
pub async fn {obj.name.lower()}_{method.name}(
    {", ".join(param_types)},
    state: State<'_, AppState>,
) -> Result<{return_type}, String> {{
    // TODO: Implement {obj.name}.{method.name}
    Ok(Default::default())
}}
"""

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

    def _generate_window(self, obj: SemanticObject) -> GeneratedFile:
        """Generate window/view code."""
        content = f'''//! {obj.name} Window
//! Generated from PowerBuilder window

use tauri::{{Window, Manager}};
use serde_json::json;

/// Initialize {obj.name} window
pub fn init_{obj.name.lower()}(window: &Window) -> Result<(), String> {{
    // Set window properties
    window.set_title("{obj.name}").map_err(|e| e.to_string())?;

    // Emit initial data
    window.emit("window_ready", json!({{
        "name": "{obj.name}",
        "controls": {len(obj.controls)}
    }})).map_err(|e| e.to_string())?;

    Ok(())
}}
'''
        return GeneratedFile(
            path=Path(f"src/windows/{obj.name.lower()}.rs"),
            content=content,
            language="rust",
        )

    def _generate_tauri_config(self, app: ApplicationModel) -> GeneratedFile:
        """Generate tauri.conf.json configuration."""
        import json

        config = {
            "$schema": "https://schema.tauri.app/config/2",
            "productName": app.name,
            "version": app.version,
            "identifier": f"com.powerbuilder.{self.app_name}",
            "build": {
                "beforeDevCommand": "",
                "beforeBuildCommand": "",
                "devUrl": "../index.html",
                "frontendDist": "../index.html",
            },
            "app": {
                "windows": [
                    {
                        "title": app.name,
                        "width": 1200,
                        "height": 800,
                        "resizable": True,
                        "fullscreen": False,
                    }
                ],
                "security": {"csp": None},
            },
            "bundle": {
                "active": True,
                "targets": "all",
                "icon": [
                    "icons/32x32.png",
                    "icons/128x128.png",
                    "icons/128x128@2x.png",
                    "icons/icon.icns",
                    "icons/icon.ico",
                ],
            },
        }

        return GeneratedFile(
            path=Path("tauri.conf.json"),
            content=json.dumps(config, indent=2),
            language="json",
        )

    def _generate_index_html(self, app: ApplicationModel) -> GeneratedFile:
        """Generate basic HTML frontend."""
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app.name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }}
        p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        button {{
            margin-top: 2rem;
            padding: 0.8rem 2rem;
            font-size: 1rem;
            border: none;
            border-radius: 50px;
            background: white;
            color: #667eea;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        button:hover {{
            transform: scale(1.05);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{app.name}</h1>
        <p>Version {app.version}</p>
        <p>Converted from PowerBuilder with PowerRebuilder</p>
        <button onclick="testCommand()">Test Tauri Command</button>
    </div>

    <script>
        const {{ invoke }} = window.__TAURI__.core;

        async function testCommand() {{
            try {{
                const version = await invoke('get_version');
                alert('App Version: ' + version);
            }} catch (error) {{
                console.error('Error:', error);
            }}
        }}
    </script>
</body>
</html>
"""
        return GeneratedFile(path=Path("index.html"), content=content, language="html")

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
