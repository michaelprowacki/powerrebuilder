"""Generate Coordinator - Orchestrates code generation from models.

This coordinator manages the generation stage of the pipeline using
the GenerateCodeUseCase with proper dependency injection.
"""

import asyncio
from pathlib import Path
from typing import Optional, Any

from ...domain.models import PipelineStage, StageResult
from ...domain.ports import (
    GeneratorPort,
    FileSystemPort,
    LoggerPort,
    ProgressPort,
)
# from ...domain.use_cases import GenerateCodeUseCase  # Not implemented yet


class GenerateCoordinator:
    """Coordinator for the code generation stage of the pipeline."""

    def __init__(
        self,
        generator: Optional[GeneratorPort],
        filesystem: FileSystemPort,
        logger: LoggerPort,
        progress: ProgressPort,
        input_path: Path,
        output_path: Path,
        target: str = "flutter",
        config: Optional[Any] = None,
    ):
        """Initialize the generate coordinator.

        Args:
            generator: Generator port implementation (optional)
            filesystem: Filesystem port implementation
            logger: Logger port implementation
            progress: Progress port implementation
            input_path: Input directory containing models
            output_path: Output directory for generated code
            target: Target platform (flutter, python, react)
            config: Optional configuration object
        """
        self.input_path = input_path
        self.output_path = output_path
        self.target = target
        self.config = config
        self.logger = logger
        self.progress = progress
        self.filesystem = filesystem

        # Create use case if generator is available (GenerateCodeUseCase not implemented yet)
        self.use_case = None
        self.generator = generator

    async def execute(self) -> StageResult:
        """Execute the generation stage.

        Returns:
            StageResult with generation statistics
        """
        self.logger.info(
            f"Starting code generation ({self.target}): {self.input_path} -> {self.output_path}"
        )

        if not self.use_case:
            # Check if we have a generator to use directly
            if hasattr(self, "generator") and self.generator:
                self.logger.info("Using generator directly (no use case available)")
                return await self._direct_generation()
            else:
                # If no generator implementation, use a basic template generator
                self.logger.warning(
                    "No generator implementation available, using basic template generator"
                )
                return await self._basic_code_generation()

        # Execute the use case
        result = await self.use_case.execute(
            input_path=self.input_path, output_path=self.output_path, target=self.target
        )

        # Log summary
        self.logger.info(
            f"Code generation completed: {result.files_processed} files generated, "
            f"{result.files_failed} failed"
        )

        return result

    async def _direct_generation(self) -> StageResult:
        """Direct generation using the generator port implementation.

        Returns:
            StageResult with generation statistics
        """
        import json
        from ...domain.models import ApplicationModel

        result = StageResult(stage=PipelineStage.GENERATE, success=True)

        try:
            # Ensure output directory exists
            await self.filesystem.mkdir(self.output_path)

            # Find model file
            model_file = self.input_path / "application_model.json"
            if not await self.filesystem.exists(model_file):
                self.logger.warning(f"No application model found in {self.input_path}")
                result.warnings.append("No model file found")
                return result

            # Read and parse model
            model_content = await self.filesystem.read_text(model_file)
            model_data = json.loads(model_content)

            self.logger.info(
                f"Generating {self.target} code using {self.generator.__class__.__name__}"
            )
            self.progress.start_stage(PipelineStage.GENERATE, 1)

            # Create ApplicationModel from JSON data
            app_model = ApplicationModel(
                name=model_data.get("name", "PowerBuilderApp"),
                version=model_data.get("version", "1.0.0"),
                entry_point=model_data.get("entry_point"),
                metadata=model_data.get("metadata", {}),
            )

            # Add objects to model
            for obj_name, obj_data in model_data.get("objects", {}).items():
                semantic_obj = self._json_to_semantic_object(obj_data)
                app_model.objects[obj_name] = semantic_obj

            # Generate project using the generator
            config = {"target": self.target}
            generated_project = self.generator.generate(app_model, config)

            # Write all generated files
            files_written = 0
            for gen_file in generated_project.files:
                file_path = self.output_path / gen_file.path

                # Ensure parent directory exists
                await self.filesystem.mkdir(file_path.parent)

                # Write file
                await self.filesystem.write_text(file_path, gen_file.content)
                files_written += 1

                self.logger.debug(f"Generated: {gen_file.path}")

            result.files_processed = files_written
            self.progress.update(1, f"Generated {files_written} files")
            self.progress.complete_stage(PipelineStage.GENERATE)

            self.logger.info(f"Successfully generated {files_written} files")

        except Exception as e:
            self.logger.error(f"Direct generation failed: {e}", exception=e)
            result.success = False
            result.errors.append(str(e))
            result.files_failed = 1

        return result

    def _json_to_semantic_object(self, obj_data: dict) -> "SemanticObject":
        """Convert JSON object data to SemanticObject."""
        from ...domain.models import (
            SemanticObject,
            ObjectType,
            Property,
            Method,
            Parameter,
            Event,
        )

        # Create semantic object
        obj = SemanticObject(
            name=obj_data.get("name", "unknown"),
            type=ObjectType(obj_data.get("type", "user_object")),
            metadata=obj_data.get("metadata", {}),
        )

        # Add properties
        for prop_data in obj_data.get("properties", []):
            prop = Property(
                name=prop_data.get("name", "unknown"),
                type=prop_data.get("type", "any"),
                default_value=prop_data.get("default_value"),
                is_required=prop_data.get("is_required", False),
            )
            obj.properties.append(prop)

        # Add methods
        for method_data in obj_data.get("methods", []):
            method = Method(
                name=method_data.get("name", "unknown"),
                return_type=method_data.get("return_type", "void"),
                body=method_data.get("body", ""),
            )

            # Add parameters
            for param_data in method_data.get("parameters", []):
                param = Parameter(
                    name=param_data.get("name", "param"),
                    type=param_data.get("type", "any"),
                    is_optional=param_data.get("is_optional", False),
                )
                method.parameters.append(param)

            obj.methods.append(method)

        # Add events
        for event_data in obj_data.get("events", []):
            event = Event(
                name=event_data.get("name", "unknown"), body=event_data.get("body", "")
            )
            obj.events.append(event)

        return obj

    async def _basic_code_generation(self) -> StageResult:
        """Basic code generation without a full generator implementation.

        Returns:
            StageResult with generation statistics
        """
        import json

        result = StageResult(stage=PipelineStage.GENERATE, success=True)

        try:
            # Ensure output directory exists
            await self.filesystem.mkdir(self.output_path)

            # Find model file
            model_file = self.input_path / "application_model.json"
            if not await self.filesystem.exists(model_file):
                self.logger.warning(f"No application model found in {self.input_path}")
                result.warnings.append("No model file found")
                return result

            # Read model
            model_content = await self.filesystem.read_text(model_file)
            model_data = json.loads(model_content)

            self.logger.info(f"Generating {self.target} code from model")
            self.progress.start_stage(PipelineStage.GENERATE, 1)

            # Generate based on target
            if self.target == "flutter":
                await self._generate_flutter_stub(model_data)
            elif self.target == "python":
                await self._generate_python_stub(model_data)
            elif self.target in ["react", "react-typescript"]:
                await self._generate_react_typescript_stub(model_data)
            elif self.target == "tauri":
                await self._generate_tauri_stub(model_data)
            elif self.target == "dioxus":
                await self._generate_dioxus_stub(model_data)
            else:
                self.logger.warning(
                    f"Unknown target: {self.target}, generating generic stub"
                )
                await self._generate_generic_stub(model_data)

            result.files_processed = 1
            self.progress.update(1, f"Generated {self.target} code")
            self.progress.complete_stage(PipelineStage.GENERATE)

        except Exception as e:
            self.logger.error(f"Generation stage failed: {e}", exception=e)
            result.success = False
            result.errors.append(str(e))
            result.files_failed = 1

        return result

    async def _generate_flutter_stub(self, model_data: dict) -> None:
        """Generate Flutter stub application."""
        # Create main.dart
        main_dart = """import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PowerBuilder App',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'PowerBuilder Converted App'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text('PowerBuilder application successfully converted!'),
            Text('Objects found: ${len(model_data.get("objects", {}))}'),
          ],
        ),
      ),
    );
  }
}
"""

        lib_dir = self.output_path / "lib"
        await self.filesystem.mkdir(lib_dir)
        await self.filesystem.write_text(lib_dir / "main.dart", main_dart)

        # Create pubspec.yaml
        pubspec = """name: powerbuilder_app
description: A Flutter application converted from PowerBuilder
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"""
        await self.filesystem.write_text(self.output_path / "pubspec.yaml", pubspec)

    async def _generate_python_stub(self, model_data: dict) -> None:
        """Generate Python/Litestar stub application."""
        # Create main.py
        main_py = f'''"""PowerBuilder application converted to Python/Litestar."""

from litestar import Litestar, get

@get("/")
async def index() -> dict:
    """Root endpoint."""
    return {{
        "message": "PowerBuilder application successfully converted!",
        "app_name": "{model_data.get("name", "PowerBuilderApp")}",
        "version": "{model_data.get("version", "1.0.0")}",
        "objects": {len(model_data.get("objects", {}))}
    }}

@get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {{"status": "healthy"}}

app = Litestar(route_handlers=[index, health])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

        await self.filesystem.write_text(self.output_path / "main.py", main_py)

        # Create requirements.txt
        requirements = """litestar>=2.0.0
uvicorn>=0.23.0
pydantic>=2.0.0
sqlmodel>=0.0.8
"""
        await self.filesystem.write_text(
            self.output_path / "requirements.txt", requirements
        )

    async def _generate_react_typescript_stub(self, model_data: dict) -> None:
        """Generate React/TypeScript stub application."""
        # Create App.tsx
        app_tsx = f"""import React from 'react';
import {{ ThemeProvider, createTheme }} from '@mui/material/styles';
import {{ CssBaseline, Container, Typography, Card, CardContent, Box }} from '@mui/material';

const theme = createTheme({{
  palette: {{
    primary: {{
      main: '#1976d2',
    }},
    secondary: {{
      main: '#dc004e',
    }},
  }},
}});

const App: React.FC = () => {{
  return (
    <ThemeProvider theme={{theme}}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{{{ py: 4 }}}}>
          <Typography variant="h2" component="h1" gutterBottom align="center">
            PowerBuilder Application
          </Typography>
          <Card sx={{{{ mt: 4 }}}}>
            <CardContent>
              <Typography variant="h4" component="h2" gutterBottom>
                Conversion Complete!
              </Typography>
              <Typography variant="body1" paragraph>
                Your PowerBuilder application has been successfully converted to React/TypeScript.
              </Typography>
              <Typography variant="body2">
                <strong>Application:</strong> {model_data.get("name", "PowerBuilderApp")}
              </Typography>
              <Typography variant="body2">
                <strong>Version:</strong> {model_data.get("version", "1.0.0")}
              </Typography>
              <Typography variant="body2">
                <strong>Objects found:</strong> {len(model_data.get("objects", {{}}))}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Container>
    </ThemeProvider>
  );
}};

export default App;
"""

        # Create directory structure
        src_dir = self.output_path / "src"
        await self.filesystem.mkdir(src_dir)
        await self.filesystem.mkdir(src_dir / "components")
        await self.filesystem.mkdir(src_dir / "pages")
        await self.filesystem.mkdir(src_dir / "services")
        await self.filesystem.mkdir(src_dir / "types")

        # Write App.tsx
        await self.filesystem.write_text(src_dir / "App.tsx", app_tsx)

        # Create main.tsx
        main_tsx = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
        await self.filesystem.write_text(src_dir / "main.tsx", main_tsx)

        # Create package.json with full React/TypeScript stack
        app_name = model_data.get("name", "powerbuilder-app").lower().replace(" ", "-")
        app_version = model_data.get("version", "1.0.0")

        package_json = f'''{{
  "name": "{app_name}",
  "version": "{app_version}",
  "private": true,
  "description": "React/TypeScript application converted from PowerBuilder",
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "@mui/material": "^5.11.0",
    "@mui/icons-material": "^5.11.0",
    "@emotion/react": "^11.10.5",
    "@emotion/styled": "^11.10.5",
    "axios": "^1.3.0",
    "@types/react": "^18.0.27",
    "@types/react-dom": "^18.0.10",
    "typescript": "^4.9.4"
  }},
  "devDependencies": {{
    "@vitejs/plugin-react": "^3.1.0",
    "vite": "^4.1.0",
    "@types/node": "^18.14.0",
    "eslint": "^8.34.0",
    "@typescript-eslint/eslint-plugin": "^5.52.0",
    "@typescript-eslint/parser": "^5.52.0",
    "eslint-plugin-react": "^7.32.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "prettier": "^2.8.4"
  }},
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write src/**/*.ts,tsx",
    "preview": "vite preview",
    "type-check": "tsc --noEmit"
  }},
  "browserslist": {{
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }}
}}'''
        await self.filesystem.write_text(
            self.output_path / "package.json", package_json
        )

        # Create tsconfig.json
        tsconfig = """{
  "compilerOptions": {
    "target": "ES2020",
    "lib": [
      "DOM",
      "DOM.Iterable",
      "ES6"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": [
    "src"
  ]
}
"""
        await self.filesystem.write_text(self.output_path / "tsconfig.json", tsconfig)

        # Create vite.config.ts
        vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
"""
        await self.filesystem.write_text(
            self.output_path / "vite.config.ts", vite_config
        )

        # Create index.html
        index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{model_data.get("name", "PowerBuilder App")}</title>
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"
    />
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/icon?family=Material+Icons"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
        await self.filesystem.write_text(self.output_path / "index.html", index_html)

    async def _generate_tauri_stub(self, model_data: dict) -> None:
        """Generate Tauri desktop application stub."""
        # Create Rust backend main.rs
        main_rs = f'''// Tauri Application: {model_data.get("name", "PowerBuilderApp")}
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::State;
use serde::{{Deserialize, Serialize}};

#[derive(Default)]
struct AppState {{
    counter: std::sync::Mutex<i32>,
}}

#[derive(Serialize, Deserialize)]
struct AppInfo {{
    name: String,
    version: String,
    objects: usize,
}}

#[tauri::command]
fn get_app_info() -> AppInfo {{
    AppInfo {{
        name: "{model_data.get("name", "PowerBuilderApp")}".to_string(),
        version: "{model_data.get("version", "0.1.0")}".to_string(),
        objects: {len(model_data.get("objects", {}))},
    }}
}}

#[tauri::command]
fn increment_counter(state: State<AppState>) -> i32 {{
    let mut counter = state.counter.lock().unwrap();
    *counter += 1;
    *counter
}}

fn main() {{
    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![get_app_info, increment_counter])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}}
'''

        # Create directories
        await self.filesystem.mkdir(self.output_path / "src-tauri" / "src")
        await self.filesystem.write_text(
            self.output_path / "src-tauri" / "src" / "main.rs", main_rs
        )

        # Create Cargo.toml
        cargo_toml = f'''[package]
name = "{model_data.get("name", "app").lower().replace(" ", "_")}"
version = "{model_data.get("version", "0.1.0")}"
edition = "2021"

[build-dependencies]
tauri-build = {{ version = "1.5", features = [] }}

[dependencies]
tauri = {{ version = "1.5", features = ["shell-open"] }}
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
'''
        await self.filesystem.write_text(
            self.output_path / "src-tauri" / "Cargo.toml", cargo_toml
        )

        # Create tauri.conf.json
        tauri_conf = f'''{{
  "build": {{
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:1420",
    "distDir": "../dist"
  }},
  "package": {{
    "productName": "{model_data.get("name", "PowerBuilderApp")}",
    "version": "{model_data.get("version", "0.1.0")}"
  }},
  "tauri": {{
    "bundle": {{
      "active": true,
      "identifier": "com.powerrebuilder.{model_data.get("name", "app").lower()}",
      "icon": ["icons/icon.ico"]
    }},
    "security": {{
      "csp": null
    }},
    "windows": [{{
      "title": "{model_data.get("name", "PowerBuilderApp")}",
      "width": 1200,
      "height": 800
    }}]
  }}
}}
'''
        await self.filesystem.write_text(
            self.output_path / "src-tauri" / "tauri.conf.json", tauri_conf
        )

        # Create build.rs
        build_rs = """fn main() {
    tauri_build::build()
}
"""
        await self.filesystem.write_text(
            self.output_path / "src-tauri" / "build.rs", build_rs
        )

        # Create frontend files
        await self.filesystem.mkdir(self.output_path / "src")

        # Create App.tsx
        app_tsx = """import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import "./App.css";

interface AppInfo {
  name: string;
  version: string;
  objects: number;
}

function App() {
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null);
  const [counter, setCounter] = useState(0);

  useEffect(() => {
    loadAppInfo();
  }, []);

  async function loadAppInfo() {
    const info = await invoke<AppInfo>("get_app_info");
    setAppInfo(info);
  }

  async function incrementCounter() {
    const newValue = await invoke<number>("increment_counter");
    setCounter(newValue);
  }

  return (
    <div className="container">
      <h1>Tauri + PowerBuilder</h1>

      {appInfo && (
        <div className="info">
          <p>Application: {appInfo.name}</p>
          <p>Version: {appInfo.version}</p>
          <p>Objects converted: {appInfo.objects}</p>
        </div>
      )}

      <div className="row">
        <button onClick={incrementCounter}>
          Count is {counter}
        </button>
      </div>

      <p className="read-the-docs">
        Successfully converted from PowerBuilder to Tauri!
      </p>
    </div>
  );
}

export default App;
"""
        await self.filesystem.write_text(self.output_path / "src" / "App.tsx", app_tsx)

        # Create main.tsx
        main_tsx = """import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
"""
        await self.filesystem.write_text(
            self.output_path / "src" / "main.tsx", main_tsx
        )

        # Create package.json
        package_json = f'''{{
  "name": "{model_data.get("name", "app").lower().replace(" ", "-")}",
  "private": true,
  "version": "{model_data.get("version", "0.1.0")}",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  }},
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tauri-apps/api": "^1.5.0"
  }},
  "devDependencies": {{
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@tauri-apps/cli": "^1.5.0",
    "@vitejs/plugin-react": "^4.0.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.4"
  }}
}}
'''
        await self.filesystem.write_text(
            self.output_path / "package.json", package_json
        )

        # Create vite.config.ts
        vite_config = """import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(async () => ({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
  },
}));
"""
        await self.filesystem.write_text(
            self.output_path / "vite.config.ts", vite_config
        )

        # Create index.html
        index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{model_data.get("name", "Tauri App")}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
        await self.filesystem.write_text(self.output_path / "index.html", index_html)

    async def _generate_dioxus_stub(self, model_data: dict) -> None:
        """Generate Dioxus stub application."""
        # Create Cargo.toml
        cargo_toml = f'''[package]
name = "{model_data.get("name", "app").lower().replace(" ", "_")}"
version = "{model_data.get("version", "0.1.0")}"
edition = "2021"

[dependencies]
dioxus = "0.5"
dioxus-desktop = "0.5"
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
tokio = {{ version = "1", features = ["full"] }}
'''
        await self.filesystem.write_text(self.output_path / "Cargo.toml", cargo_toml)

        # Create src directory
        await self.filesystem.mkdir(self.output_path / "src")

        # Create main.rs
        main_rs = f'''#![allow(non_snake_case)]

use dioxus::prelude::*;

const APP_NAME: &str = "{model_data.get("name", "PowerBuilderApp")}";
const APP_VERSION: &str = "{model_data.get("version", "0.1.0")}";

fn main() {{
    dioxus_desktop::launch(App);
}}

fn App() -> Element {{
    let mut counter = use_signal(|| 0);

    rsx! {{
        div {{
            style: "padding: 20px; font-family: Arial, sans-serif;",

            h1 {{ "{{APP_NAME}}" }}
            p {{ "Version: {{APP_VERSION}}" }}

            div {{
                style: "margin: 20px 0;",

                h2 {{ "Application Information" }}
                p {{ "Objects: {len(model_data.get("objects", {}))}" }}
                p {{ "Generated with PowerRebuilder using Dioxus" }}
            }}

            div {{
                style: "margin: 20px 0;",

                h3 {{ "Demo Counter" }}
                p {{ "Count: {{counter}}" }}
                button {{
                    onclick: move |_| counter += 1,
                    "Increment"
                }}
                button {{
                    onclick: move |_| counter -= 1,
                    style: "margin-left: 10px;",
                    "Decrement"
                }}
            }}
        }}
    }}
}}
'''
        await self.filesystem.write_text(self.output_path / "src" / "main.rs", main_rs)

        # Create README
        readme = f"""# {model_data.get("name", "PowerBuilderApp")} - Dioxus Application

## About
This Dioxus desktop application was generated from a PowerBuilder application using PowerRebuilder.

## Building and Running

### Prerequisites
- Rust (latest stable)
- Cargo

### Development
```bash
cargo run
```

### Release Build
```bash
cargo build --release
```

## Application Structure
- `src/main.rs` - Main application entry point
- `Cargo.toml` - Rust dependencies and project configuration

## Features
- Native desktop performance
- Cross-platform support (Windows, macOS, Linux)
- React-like component model in Rust
"""
        await self.filesystem.write_text(self.output_path / "README.md", readme)

    async def _generate_generic_stub(self, model_data: dict) -> None:
        """Generate generic stub output."""
        # Create README
        readme = f"""# PowerBuilder Application Conversion

## Application Information
- Name: {model_data.get("name", "PowerBuilderApp")}
- Version: {model_data.get("version", "1.0.0")}
- Objects: {len(model_data.get("objects", {}))}

## Conversion Status
The PowerBuilder application has been successfully analyzed and modeled.
Code generation for the target platform is pending implementation.

## Model Structure
The application model has been saved in JSON format and contains:
- Application metadata
- Object definitions
- Dependencies
- Global functions and variables

## Next Steps
1. Implement target-specific code generator
2. Create templates for UI components
3. Map PowerBuilder constructs to target platform
4. Generate database access layer
"""
        await self.filesystem.write_text(self.output_path / "README.md", readme)

    def execute_sync(self) -> StageResult:
        """Synchronous wrapper for execute method.

        Returns:
            StageResult with generation statistics
        """
        return asyncio.run(self.execute())

    def process(self) -> dict:
        """Process method for CLI compatibility.

        Returns:
            Dictionary with processing results
        """
        result = self.execute_sync()

        # Convert StageResult to expected dictionary format
        return {
            "files_generated": result.files_processed,
            "total_models": result.files_processed,  # Assuming 1:1 model to file ratio
            "failed_files": result.errors,
            "success": result.success,
            "warnings": result.warnings,
        }
