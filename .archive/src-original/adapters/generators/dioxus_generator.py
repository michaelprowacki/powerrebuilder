"""Dioxus generator adapter - Generates Dioxus desktop applications from semantic models.

This adapter implements the GeneratorPort interface for generating
native desktop applications using Dioxus (React-like framework for Rust).
"""

import logging
from typing import Dict, Any

from ...domain.ports import GeneratorPort
from ...domain.models import (
    ApplicationModel,
    SemanticObject,
    GeneratedProject,
    GeneratedFile,
    TargetLanguage,
    ObjectType,
)
from ...domain.services import CodeTemplateEngine

logger = logging.getLogger(__name__)

# ============= Dioxus Templates =============

DIOXUS_CARGO_TOML_TEMPLATE = """[package]
name = "{app_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
dioxus = "0.5"
dioxus-desktop = "0.5"
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
tokio = {{ version = "1", features = ["full"] }}
sqlx = {{ version = "0.7", features = ["runtime-tokio-native-tls", "sqlite"] }}
chrono = "0.4"
log = "0.4"
env_logger = "0.11"

[profile.release]
opt-level = 3
lto = true
strip = true
"""

DIOXUS_MAIN_RS_TEMPLATE = """#![allow(non_snake_case)]

use dioxus::prelude::*;
use serde::{{Deserialize, Serialize}};
use sqlx::sqlite::SqlitePool;
use std::sync::Arc;

// Application configuration
const APP_NAME: &str = "{app_name}";
const APP_VERSION: &str = "{version}";

// Data models
{structs}

// Application state
#[derive(Clone)]
struct AppState {{
    db: Arc<SqlitePool>,
    {state_fields}
}}

impl AppState {{
    async fn new() -> Result<Self, Box<dyn std::error::Error>> {{
        let db = SqlitePool::connect("sqlite:{app_name}.db").await?;

        // Initialize database tables
        {init_tables}

        Ok(Self {{
            db: Arc::new(db),
            {state_init}
        }})
    }}
}}

fn main() {{
    env_logger::init();

    // Create the Dioxus app
    dioxus_desktop::launch_cfg(
        App,
        dioxus_desktop::Config::new()
            .with_window(dioxus_desktop::WindowBuilder::new()
                .with_title(APP_NAME)
                .with_resizable(true)
                .with_inner_size(dioxus_desktop::LogicalSize::new(1200.0, 800.0))
            )
    );
}}

fn App() -> Element {{
    // Initialize app state
    let app_state = use_signal(|| {{
        let runtime = tokio::runtime::Runtime::new().unwrap();
        runtime.block_on(async {{
            AppState::new().await.unwrap()
        }})
    }});

    // Current page/route
    let current_page = use_signal(|| "home");

    rsx! {{
        div {{
            class: "app-container",
            style: "display: flex; flex-direction: column; height: 100vh;",

            // Header
            AppHeader {{
                title: APP_NAME,
                on_navigate: move |page: String| {{
                    current_page.set(page.as_str());
                }}
            }}

            // Main content area
            div {{
                class: "content",
                style: "flex: 1; overflow-y: auto; padding: 20px;",

                match current_page() {{
                    "home" => rsx! {{ HomePage {{}} }},
                    {page_routes}
                    _ => rsx! {{ NotFoundPage {{}} }}
                }}
            }}

            // Footer
            AppFooter {{ version: APP_VERSION }}
        }}
    }}
}}

// Component: App Header
#[component]
fn AppHeader(title: &'static str, on_navigate: EventHandler<String>) -> Element {{
    rsx! {{
        header {{
            style: "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",

            div {{
                style: "display: flex; justify-content: space-between; align-items: center;",

                h1 {{
                    style: "margin: 0; font-size: 24px;",
                    "{{title}}"
                }}

                nav {{
                    style: "display: flex; gap: 20px;",

                    button {{
                        onclick: move |_| on_navigate.call("home".to_string()),
                        style: "background: none; border: none; color: white; cursor: pointer; font-size: 16px;",
                        "Home"
                    }}
                    {nav_buttons}
                }}
            }}
        }}
    }}
}}

// Component: App Footer
#[component]
fn AppFooter(version: &'static str) -> Element {{
    rsx! {{
        footer {{
            style: "background: #f7f7f7; padding: 10px 20px; text-align: center; border-top: 1px solid #e0e0e0;",

            small {{
                style: "color: #666;",
                "{{APP_NAME}} v{{version}} - Powered by Dioxus and PowerRebuilder"
            }}
        }}
    }}
}}

// Component: Home Page
#[component]
fn HomePage() -> Element {{
    rsx! {{
        div {{
            style: "max-width: 800px; margin: 0 auto;",

            h2 {{
                style: "color: #333; margin-bottom: 20px;",
                "Welcome to {{APP_NAME}}"
            }}

            div {{
                style: "background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",

                p {{
                    style: "color: #666; line-height: 1.6;",
                    "This application was generated from PowerBuilder using PowerRebuilder."
                }}

                div {{
                    style: "margin-top: 20px;",

                    h3 {{ "Available Features:" }}
                    ul {{
                        {feature_list}
                    }}
                }}
            }}
        }}
    }}
}}

// Component: Not Found Page
#[component]
fn NotFoundPage() -> Element {{
    rsx! {{
        div {{
            style: "text-align: center; padding: 50px;",

            h2 {{
                style: "color: #e74c3c;",
                "404 - Page Not Found"
            }}
            p {{ "The requested page could not be found." }}
        }}
    }}
}}

{components}

{commands}
"""

DIOXUS_WINDOW_COMPONENT_TEMPLATE = """// Component: {window_name}
#[component]
fn {component_name}() -> Element {{
    // Component state
    let loading = use_signal(|| false);
    let data = use_signal(|| Vec::<{data_type}>::new());
    let error = use_signal(|| None::<String>);

    // Load data on mount
    use_effect(move || {{
        spawn(async move {{
            loading.set(true);
            match load_{window_name_lower}_data().await {{
                Ok(result) => data.set(result),
                Err(e) => error.set(Some(e.to_string())),
            }}
            loading.set(false);
        }});
    }});

    rsx! {{
        div {{
            class: "{window_name_lower}-container",
            style: "padding: 20px;",

            h2 {{
                style: "color: #333; margin-bottom: 20px;",
                "{window_title}"
            }}

            if loading() {{
                div {{
                    style: "text-align: center; padding: 20px;",
                    "Loading..."
                }}
            }} else if let Some(err) = error() {{
                div {{
                    style: "background: #fee; color: #c00; padding: 10px; border-radius: 4px;",
                    "Error: {{err}}"
                }}
            }} else {{
                div {{
                    style: "background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",

                    {content}
                }}
            }}
        }}
    }}
}}

async fn load_{window_name_lower}_data() -> Result<Vec<{data_type}>, Box<dyn std::error::Error>> {{
    // TODO: Implement data loading
    Ok(vec![])
}}
"""

DIOXUS_DATAWINDOW_COMPONENT_TEMPLATE = """// DataWindow Component: {datawindow_name}
#[component]
fn {component_name}(data: Vec<{data_type}>) -> Element {{
    // Table state
    let sort_column = use_signal(|| None::<String>);
    let sort_ascending = use_signal(|| true);
    let filter_text = use_signal(|| String::new());

    // Apply filtering and sorting
    let mut filtered_data = data.iter()
        .filter(|item| {{
            if filter_text().is_empty() {{
                true
            }} else {{
                // TODO: Implement filtering logic based on your data structure
                true
            }}
        }})
        .collect::<Vec<_>>();

    // Sort data if needed
    if let Some(col) = sort_column() {{
        // TODO: Implement sorting logic based on column
    }}

    rsx! {{
        div {{
            class: "datawindow-container",
            style: "padding: 20px;",

            // Search bar
            div {{
                style: "margin-bottom: 20px;",

                input {{
                    r#type: "text",
                    placeholder: "Search...",
                    value: "{{filter_text()}}",
                    oninput: move |evt| filter_text.set(evt.value.clone()),
                    style: "padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 300px;",
                }}
            }}

            // Data table
            table {{
                style: "width: 100%; border-collapse: collapse; background: white;",

                thead {{
                    tr {{
                        style: "background: #f5f5f5;",

                        {headers}
                    }}
                }}

                tbody {{
                    for item in filtered_data {{
                        tr {{
                            style: "border-bottom: 1px solid #eee;",

                            {rows}
                        }}
                    }}
                }}
            }}

            // Pagination (if needed)
            div {{
                style: "margin-top: 20px; text-align: center;",

                "Showing {{filtered_data.len()}} of {{data.len()}} records"
            }}
        }}
    }}
}}
"""

DIOXUS_BUILD_RS_TEMPLATE = """fn main() {
    // Optional: Add build-time configuration here
    println!("cargo:rerun-if-changed=build.rs");
}
"""

DIOXUS_STYLE_CSS_TEMPLATE = """/* Global styles for Dioxus application */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    min-height: 100vh;
}

/* Utility classes */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    padding: 20px;
    margin-bottom: 20px;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Table styles */
table {
    width: 100%;
    border-collapse: collapse;
}

th {
    text-align: left;
    padding: 12px;
    background: #f5f5f5;
    font-weight: 600;
    color: #333;
    cursor: pointer;
    user-select: none;
}

th:hover {
    background: #e8e8e8;
}

td {
    padding: 12px;
    border-bottom: 1px solid #eee;
}

tr:hover {
    background: #fafafa;
}

/* Form styles */
input, select, textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Loading spinner */
.spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #667eea;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 20px auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
"""


class DioxusGenerator(GeneratorPort):
    """Generates Dioxus desktop applications from PowerBuilder models.

    Maps PowerBuilder concepts to Dioxus components:
    - Windows -> Dioxus Components with rsx! macro
    - DataWindows -> Table components with sorting/filtering
    - User Objects -> Reusable components
    - Properties -> Rust structs with derive macros
    - Methods -> Async functions and event handlers
    - Database -> SQLite with sqlx
    """

    def __init__(self):
        """Initialize the Dioxus generator."""
        self.template_engine = CodeTemplateEngine()
        self.target = TargetLanguage.DIOXUS

    def supports_target(self, target: TargetLanguage) -> bool:
        """Check if target language is supported."""
        return target == TargetLanguage.DIOXUS

    def generate_file(
        self, obj: SemanticObject, target: TargetLanguage
    ) -> GeneratedFile:
        """Generate single file from semantic object."""
        if not self.supports_target(target):
            raise ValueError(f"Unsupported target: {target}")

        # Generate component based on object type
        if obj.type == ObjectType.WINDOW:
            component = self._create_window_component(obj)
            return GeneratedFile(
                path=f"src/components/{self._to_snake_case(obj.name)}.rs",
                content=component,
                language="rust",
            )
        elif obj.type == ObjectType.DATAWINDOW:
            component = self._generate_datawindow_component_code(obj)
            return GeneratedFile(
                path=f"src/components/{self._to_snake_case(obj.name)}_table.rs",
                content=component,
                language="rust",
            )
        else:
            # Generate as generic component
            return GeneratedFile(
                path=f"src/components/{self._to_snake_case(obj.name)}.rs",
                content=f"// Component for {obj.name}\n",
                language="rust",
            )

    def format_code(self, code: str, language: TargetLanguage) -> str:
        """Format generated Rust code."""
        if language != TargetLanguage.DIOXUS:
            return code

        # Basic Rust formatting (in production, would use rustfmt)
        lines = code.splitlines()
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Decrease indent for closing braces
            if stripped.startswith("}"):
                indent_level = max(0, indent_level - 1)

            # Add indented line
            if stripped:
                formatted_lines.append("    " * indent_level + stripped)
            else:
                formatted_lines.append("")

            # Increase indent for opening braces
            if stripped.endswith("{"):
                indent_level += 1

        return "\n".join(formatted_lines)

    def generate(
        self, model: ApplicationModel, config: Dict[str, Any]
    ) -> GeneratedProject:
        """Generate a complete Dioxus application from the semantic model.

        Args:
            model: The application semantic model
            config: Generation configuration options

        Returns:
            GeneratedProject containing all generated files
        """
        logger.info(f"Generating Dioxus application: {model.name}")

        project = GeneratedProject(name=model.name, target=self.target, files=[])

        # Generate project structure
        self._generate_cargo_toml(project, model)
        self._generate_main_rs(project, model)
        self._generate_build_rs(project, model)
        self._generate_styles(project, model)

        # Generate components for each window
        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.WINDOW:
                self._generate_window_component(project, obj, model)
            elif obj.type == ObjectType.DATAWINDOW:
                self._generate_datawindow_component(project, obj, model)

        # Generate database module if needed
        if self._has_database_operations(model):
            self._generate_database_module(project, model)

        logger.info(f"Generated {len(project.files)} files for Dioxus application")
        return project

    def _generate_cargo_toml(
        self, project: GeneratedProject, model: ApplicationModel
    ) -> None:
        """Generate Cargo.toml file."""
        content = DIOXUS_CARGO_TOML_TEMPLATE.format(
            app_name=self._to_snake_case(model.name)
        )

        project.files.append(
            GeneratedFile(
                path="Cargo.toml",
                content=content,
                language="rust",  # Using rust as language for Cargo.toml
            )
        )

    def _generate_main_rs(
        self, project: GeneratedProject, model: ApplicationModel
    ) -> None:
        """Generate main.rs with app setup and routing."""
        # Extract structs from model
        structs = self._generate_structs(model)

        # Generate state fields
        state_fields = self._generate_state_fields(model)

        # Generate initialization code
        init_tables = self._generate_table_init(model)
        state_init = self._generate_state_init(model)

        # Generate page routes
        page_routes = self._generate_page_routes(model)

        # Generate navigation buttons
        nav_buttons = self._generate_nav_buttons(model)

        # Generate feature list
        feature_list = self._generate_feature_list(model)

        # Generate components
        components = self._generate_components(model)

        # Generate command handlers
        commands = self._generate_commands(model)

        content = DIOXUS_MAIN_RS_TEMPLATE.format(
            app_name=self._to_snake_case(model.name),
            version="0.1.0",
            structs=structs,
            state_fields=state_fields,
            init_tables=init_tables,
            state_init=state_init,
            page_routes=page_routes,
            nav_buttons=nav_buttons,
            feature_list=feature_list,
            components=components,
            commands=commands,
        )

        project.files.append(
            GeneratedFile(path="src/main.rs", content=content, language="rust")
        )

    def _generate_build_rs(
        self, project: GeneratedProject, model: ApplicationModel
    ) -> None:
        """Generate build.rs file."""
        project.files.append(
            GeneratedFile(
                path="build.rs", content=DIOXUS_BUILD_RS_TEMPLATE, language="rust"
            )
        )

    def _generate_styles(
        self, project: GeneratedProject, model: ApplicationModel
    ) -> None:
        """Generate CSS styles."""
        project.files.append(
            GeneratedFile(
                path="assets/style.css",
                content=DIOXUS_STYLE_CSS_TEMPLATE,
                language="rust",  # Using rust as CSS isn't in enum
            )
        )

    def _generate_window_component(
        self, project: GeneratedProject, window: SemanticObject, model: ApplicationModel
    ) -> None:
        """Generate a Dioxus component for a PowerBuilder window."""
        component_name = self._to_pascal_case(window.name)
        window_name_lower = self._to_snake_case(window.name)

        # Determine data type for the window
        data_type = self._get_window_data_type(window)

        # Generate window content based on controls
        content = self._generate_window_content(window)

        component_code = DIOXUS_WINDOW_COMPONENT_TEMPLATE.format(
            window_name=window.name,
            component_name=component_name,
            window_name_lower=window_name_lower,
            window_title=window.name.replace("_", " ").title(),
            data_type=data_type,
            content=content,
        )

        # Add to components in main.rs
        # Note: In a real implementation, we'd append this to the components section

    def _generate_datawindow_component_code(self, datawindow: SemanticObject) -> str:
        """Generate Dioxus component code for a DataWindow."""
        component_name = f"{self._to_pascal_case(datawindow.name)}DataWindow"
        headers = self._generate_table_headers(datawindow)
        rows = self._generate_table_rows(datawindow)
        data_type = self._get_datawindow_data_type(datawindow)

        return DIOXUS_DATAWINDOW_COMPONENT_TEMPLATE.format(
            datawindow_name=datawindow.name,
            component_name=component_name,
            data_type=data_type,
            headers=headers,
            rows=rows,
        )

    def _generate_datawindow_component(
        self,
        project: GeneratedProject,
        datawindow: SemanticObject,
        model: ApplicationModel,
    ) -> None:
        """Generate a Dioxus component for a PowerBuilder DataWindow."""
        component_name = f"{self._to_pascal_case(datawindow.name)}DataWindow"

        # Extract columns/fields from DataWindow
        headers = self._generate_table_headers(datawindow)
        rows = self._generate_table_rows(datawindow)
        data_type = self._get_datawindow_data_type(datawindow)

        component_code = DIOXUS_DATAWINDOW_COMPONENT_TEMPLATE.format(
            datawindow_name=datawindow.name,
            component_name=component_name,
            data_type=data_type,
            headers=headers,
            rows=rows,
        )

        # Add to components in main.rs

    def _generate_database_module(
        self, project: GeneratedProject, model: ApplicationModel
    ) -> None:
        """Generate database module with SQLite setup."""
        # Database code is included in main.rs template
        pass

    # Helper methods
    def _generate_structs(self, model: ApplicationModel) -> str:
        """Generate Rust struct definitions from model."""
        structs = []

        # Handle both list and dict formats for objects
        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )

        for obj in objects:
            if obj.type == ObjectType.STRUCTURE or self._is_data_object(obj):
                struct_code = f"""#[derive(Debug, Clone, Serialize, Deserialize)]
struct {self._to_pascal_case(obj.name)} {{"""

                for prop in obj.properties:
                    rust_type = self._pb_to_rust_type(
                        prop.type if hasattr(prop, "type") else "string"
                    )
                    field_name = self._to_snake_case(
                        prop.name if hasattr(prop, "name") else "field"
                    )
                    struct_code += f"\n    {field_name}: {rust_type},"

                struct_code += "\n}\n"
                structs.append(struct_code)

        return "\n".join(structs)

    def _generate_state_fields(self, model: ApplicationModel) -> str:
        """Generate state field definitions."""
        fields = []

        # Add common state fields
        fields.append("current_user: Option<String>")
        fields.append("is_authenticated: bool")

        # Add fields based on model analysis
        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.WINDOW:
                field_name = f"{self._to_snake_case(obj.name)}_data"
                fields.append(f"{field_name}: Vec<serde_json::Value>")

        return ",\n    ".join(fields)

    def _generate_table_init(self, model: ApplicationModel) -> str:
        """Generate SQL table initialization code."""
        tables = []

        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.DATAWINDOW:
                # Extract table info from DataWindow
                table_name = self._to_snake_case(obj.name)
                tables.append(f"""
        sqlx::query(
            "CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"
        )
        .execute(&db)
        .await?;""")

        return "\n".join(tables)

    def _generate_state_init(self, model: ApplicationModel) -> str:
        """Generate state initialization code."""
        inits = []
        inits.append("current_user: None")
        inits.append("is_authenticated: false")

        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.WINDOW:
                field_name = f"{self._to_snake_case(obj.name)}_data"
                inits.append(f"{field_name}: vec![]")

        return ",\n            ".join(inits)

    def _generate_page_routes(self, model: ApplicationModel) -> str:
        """Generate page routing code."""
        routes = []

        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.WINDOW:
                route_name = self._to_snake_case(obj.name)
                component_name = self._to_pascal_case(obj.name)
                routes.append(f'"{route_name}" => rsx! {{ {component_name} {{}} }}')

        return ",\n                    ".join(routes)

    def _generate_nav_buttons(self, model: ApplicationModel) -> str:
        """Generate navigation buttons."""
        buttons = []

        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.WINDOW:
                route_name = self._to_snake_case(obj.name)
                display_name = obj.name.replace("_", " ").title()
                buttons.append(f"""
                    button {{
                        onclick: move |_| on_navigate.call("{route_name}".to_string()),
                        style: "background: none; border: none; color: white; cursor: pointer; font-size: 16px;",
                        "{display_name}"
                    }}""")

        return "\n".join(buttons)

    def _generate_feature_list(self, model: ApplicationModel) -> str:
        """Generate feature list for home page."""
        features = []

        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        window_count = sum(1 for obj in objects if obj.type == ObjectType.WINDOW)
        datawindow_count = sum(
            1 for obj in objects if obj.type == ObjectType.DATAWINDOW
        )

        if window_count > 0:
            features.append(f'li {{ "{window_count} Windows" }}')
        if datawindow_count > 0:
            features.append(f'li {{ "{datawindow_count} DataWindows" }}')

        features.append('li {{ "SQLite Database Integration" }}')
        features.append('li {{ "Native Desktop Performance" }}')

        return "\n                        ".join(features)

    def _generate_components(self, model: ApplicationModel) -> str:
        """Generate all component definitions."""
        components = []

        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.WINDOW:
                component = self._create_window_component(obj)
                components.append(component)

        return "\n\n".join(components)

    def _create_window_component(self, window: SemanticObject) -> str:
        """Create a complete window component."""
        component_name = self._to_pascal_case(window.name)
        window_name_lower = self._to_snake_case(window.name)
        window_title = window.name.replace("_", " ").title()

        return f"""// Component: {window.name}
#[component]
fn {component_name}() -> Element {{
    let loading = use_signal(|| false);
    let data = use_signal(|| Vec::<serde_json::Value>::new());

    rsx! {{
        div {{
            class: "{window_name_lower}-container",
            style: "padding: 20px;",

            h2 {{
                style: "color: #333; margin-bottom: 20px;",
                "{window_title}"
            }}

            div {{
                style: "background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",

                p {{ "This is the {window_title} window." }}

                // Add controls based on window definition
                {self._generate_window_controls(window)}
            }}
        }}
    }}
}}"""

    def _generate_window_controls(self, window: SemanticObject) -> str:
        """Generate controls for a window."""
        controls = []

        # Add basic controls based on window properties
        for prop in window.properties:
            if hasattr(prop, "name") and "button" in prop.name.lower():
                controls.append(f"""
                button {{
                    class: "btn btn-primary",
                    onclick: move |_| {{ /* TODO: Handle click */ }},
                    "{getattr(prop, "name", "Button")}"
                }}""")

        return "\n".join(controls) if controls else ""

    def _generate_commands(self, model: ApplicationModel) -> str:
        """Generate async command handlers."""
        commands = []

        # Generate CRUD operations for data objects
        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type == ObjectType.DATAWINDOW:
                table_name = self._to_snake_case(obj.name)
                commands.append(f"""
// CRUD operations for {obj.name}
async fn get_{table_name}_list(db: &SqlitePool) -> Result<Vec<serde_json::Value>, String> {{
    // TODO: Implement query
    Ok(vec![])
}}

async fn create_{table_name}(db: &SqlitePool, data: serde_json::Value) -> Result<i64, String> {{
    // TODO: Implement insert
    Ok(0)
}}

async fn update_{table_name}(db: &SqlitePool, id: i64, data: serde_json::Value) -> Result<(), String> {{
    // TODO: Implement update
    Ok(())
}}

async fn delete_{table_name}(db: &SqlitePool, id: i64) -> Result<(), String> {{
    // TODO: Implement delete
    Ok(())
}}""")

        return "\n".join(commands)

    def _generate_window_content(self, window: SemanticObject) -> str:
        """Generate content for a window component."""
        # Basic implementation - would be expanded based on window controls
        return """
                    p {{ "Window content goes here" }}

                    div {{
                        style: "margin-top: 20px;",

                        button {{
                            class: "btn btn-primary",
                            "Refresh"
                        }}
                    }}"""

    def _generate_table_headers(self, datawindow: SemanticObject) -> str:
        """Generate table headers for a DataWindow."""
        headers = []

        # Extract columns from DataWindow properties
        for prop in datawindow.properties:
            if hasattr(prop, "type") and prop.type == "column":
                col_name = (
                    prop.name.replace("_", " ").title()
                    if hasattr(prop, "name")
                    else "Column"
                )
                headers.append(f"""
                        th {{
                            onclick: move |_| {{
                                // TODO: Implement sorting
                            }},
                            "{col_name}"
                        }}""")

        # Default headers if none found
        if not headers:
            headers = ['th { "ID" }', 'th { "Name" }', 'th { "Actions" }']

        return "\n".join(headers)

    def _generate_table_rows(self, datawindow: SemanticObject) -> str:
        """Generate table rows for a DataWindow."""
        # Basic row template
        return """
                            td {{ "{{item.id}}" }}
                            td {{ "{{item.name}}" }}
                            td {{
                                button {{
                                    class: "btn btn-sm",
                                    "Edit"
                                }}
                            }}"""

    def _get_window_data_type(self, window: SemanticObject) -> str:
        """Determine the data type for a window."""
        # Check if window has associated data type
        for prop in window.properties:
            if hasattr(prop, "type") and prop.type == "datatype":
                return self._to_pascal_case(getattr(prop, "value", "Data"))

        return "serde_json::Value"

    def _get_datawindow_data_type(self, datawindow: SemanticObject) -> str:
        """Determine the data type for a DataWindow."""
        # Use DataWindow name as basis for type
        return self._to_pascal_case(f"{datawindow.name}Row")

    def _has_database_operations(self, model: ApplicationModel) -> bool:
        """Check if the model requires database operations."""
        objects = (
            model.objects.values() if isinstance(model.objects, dict) else model.objects
        )
        for obj in objects:
            if obj.type in [ObjectType.DATAWINDOW, ObjectType.QUERY]:
                return True

            # Check methods for SQL operations
            for method in obj.methods:
                if any(
                    keyword in getattr(method, "body", "").upper()
                    for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]
                ):
                    return True

        return False

    def _is_data_object(self, obj: SemanticObject) -> bool:
        """Check if an object represents data structure."""
        return obj.type == ObjectType.STRUCTURE or (
            obj.type == ObjectType.USER_OBJECT
            and any(hasattr(p, "type") and p.type == "datatype" for p in obj.properties)
        )

    def _pb_to_rust_type(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Rust type."""
        type_map = {
            "string": "String",
            "char": "char",
            "integer": "i32",
            "long": "i64",
            "decimal": "f64",
            "double": "f64",
            "real": "f32",
            "boolean": "bool",
            "date": "chrono::NaiveDate",
            "datetime": "chrono::DateTime<chrono::Utc>",
            "time": "chrono::NaiveTime",
            "blob": "Vec<u8>",
            "any": "serde_json::Value",
        }

        return type_map.get(pb_type.lower(), "String")

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        parts = name.replace("-", "_").split("_")
        return "".join(part.capitalize() for part in parts if part)

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        # Handle various formats
        name = name.replace("-", "_").replace(" ", "_")

        # Convert camelCase to snake_case
        import re

        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)

        return name.lower()
