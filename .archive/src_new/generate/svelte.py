"""Svelte Generator - Generate Svelte applications from semantic models.

This generator creates modern Svelte applications with TypeScript support,
SvelteKit routing, and reactive stores.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from src_new._core.models import (
    ApplicationModel,
    GeneratedFile,
    GeneratedProject,
    Property,
    SemanticObject,
    TargetLanguage,
)
from .generator import BaseCodeGenerator

logger = logging.getLogger(__name__)


class SvelteGenerator(BaseCodeGenerator):
    """Generator for Svelte applications."""

    def __init__(self, input_path: str, output_path: str):
        """Initialize Svelte generator.

        Args:
            input_path: Input directory path
            output_path: Output directory path
        """
        super().__init__(TargetLanguage.JAVASCRIPT)
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.models: Dict[str, ApplicationModel] = {}
        self.generated_files: List[GeneratedFile] = []

    def generate_project(self, model: ApplicationModel) -> GeneratedProject:
        """Generate complete Svelte project.

        Args:
            model: Application model

        Returns:
            Generated project
        """
        project = GeneratedProject(
            name=model.name, target=TargetLanguage.JAVASCRIPT, files=[]
        )

        # Generate project structure
        self._generate_package_json(model, project)
        self._generate_svelte_config(model, project)
        self._generate_vite_config(model, project)
        self._generate_tsconfig(model, project)
        self._generate_app_html(model, project)

        # Generate layout
        self._generate_layout(model, project)

        # Generate components for each object
        for obj in model.objects:
            if obj.type == "window" or obj.type == "class":
                self._generate_component(obj, project)
            elif obj.type == "datawindow":
                self._generate_data_table(obj, project)

        # Generate stores
        self._generate_stores(model, project)

        # Generate routes
        self._generate_routes(model, project)

        # Generate styles
        self._generate_styles(model, project)

        return project

    def _generate_package_json(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate package.json file.

        Args:
            model: Application model
            project: Generated project
        """
        package = {
            "name": model.name.lower().replace(" ", "-"),
            "version": model.version or "1.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite dev",
                "build": "vite build",
                "preview": "vite preview",
                "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json",
                "check:watch": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --watch",
                "lint": "eslint .",
                "format": "prettier --write .",
            },
            "devDependencies": {
                "@sveltejs/adapter-auto": "^3.0.0",
                "@sveltejs/kit": "^2.0.0",
                "@sveltejs/vite-plugin-svelte": "^3.0.0",
                "@types/node": "^20.10.0",
                "svelte": "^4.2.0",
                "svelte-check": "^3.6.0",
                "typescript": "^5.3.0",
                "vite": "^5.0.0",
                "eslint": "^8.55.0",
                "eslint-plugin-svelte": "^2.35.0",
                "prettier": "^3.1.0",
                "prettier-plugin-svelte": "^3.1.0",
            },
            "dependencies": {"@fontsource/inter": "^5.0.0", "axios": "^1.6.0"},
        }

        project.files.append(
            GeneratedFile(
                path=Path("package.json"),
                content=json.dumps(package, indent=2),
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_svelte_config(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate svelte.config.js.

        Args:
            model: Application model
            project: Generated project
        """
        config = """import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: vitePreprocess(),

    kit: {
        adapter: adapter(),
        alias: {
            $components: 'src/components',
            $lib: 'src/lib',
            $stores: 'src/stores'
        }
    }
};

export default config;"""

        project.files.append(
            GeneratedFile(
                path=Path("svelte.config.js"),
                content=config,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_vite_config(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate Vite configuration.

        Args:
            model: Application model
            project: Generated project
        """
        config = """import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    }
});"""

        project.files.append(
            GeneratedFile(
                path=Path("vite.config.ts"),
                content=config,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_tsconfig(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate TypeScript configuration.

        Args:
            model: Application model
            project: Generated project
        """
        tsconfig = {
            "extends": "./.svelte-kit/tsconfig.json",
            "compilerOptions": {
                "allowJs": True,
                "checkJs": True,
                "esModuleInterop": True,
                "forceConsistentCasingInFileNames": True,
                "resolveJsonModule": True,
                "skipLibCheck": True,
                "sourceMap": True,
                "strict": True,
                "moduleResolution": "bundler",
            },
        }

        project.files.append(
            GeneratedFile(
                path=Path("tsconfig.json"),
                content=json.dumps(tsconfig, indent=2),
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_app_html(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate app.html template.

        Args:
            model: Application model
            project: Generated project
        """
        html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{model.name}</title>
    %sveltekit.head%
</head>
<body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
</body>
</html>"""

        project.files.append(
            GeneratedFile(
                path=Path("src/app.html"),
                content=html,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_layout(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate layout component.

        Args:
            model: Application model
            project: Generated project
        """
        layout_content = """<script lang="ts">
    import '@fontsource/inter/400.css';
    import '@fontsource/inter/500.css';
    import '@fontsource/inter/600.css';
    import './app.css';

    import Header from '$components/Header.svelte';
    import Sidebar from '$components/Sidebar.svelte';
    import { page } from '$app/stores';
    import { appStore } from '$stores/app';

    $: showSidebar = $appStore.showSidebar;
</script>

<div class="app">
    <Header />

    <div class="main-container">
        {#if showSidebar}
            <Sidebar />
        {/if}

        <main class="content">
            <slot />
        </main>
    </div>
</div>

<style>
    .app {
        height: 100vh;
        display: flex;
        flex-direction: column;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .main-container {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    .content {
        flex: 1;
        padding: 2rem;
        overflow-y: auto;
        background-color: #fafafa;
    }
</style>"""

        project.files.append(
            GeneratedFile(
                path=Path("src/routes/+layout.svelte"),
                content=layout_content,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_component(
        self, obj: SemanticObject, project: GeneratedProject
    ) -> None:
        """Generate Svelte component for an object.

        Args:
            obj: Semantic object
            project: Generated project
        """
        component_content = f"""<script lang="ts">
    import {{ onMount }} from 'svelte';

    // Component props
    export let id: string | undefined = undefined;

    // Component state
    {self._generate_state_declarations(obj)}

    // Methods
    {self._generate_methods(obj)}

    // Lifecycle
    onMount(() => {{
        console.log('{obj.name} component mounted');
        // Initialize component
    }});
</script>

<div class="{obj.name.lower()}-container">
    <div class="card">
        <div class="card-header">
            <h2>{obj.name}</h2>
        </div>

        <div class="card-body">
            {self._generate_component_body(obj)}
        </div>

        {self._generate_actions(obj)}
    </div>
</div>

<style>
    .{obj.name.lower()}-container {{
        padding: 1rem;
    }}

    .card {{
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}

    .card-header {{
        padding: 1rem;
        border-bottom: 1px solid #e0e0e0;
    }}

    .card-header h2 {{
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
    }}

    .card-body {{
        padding: 1rem;
    }}

    .form-group {{
        margin-bottom: 1rem;
    }}

    .form-group label {{
        display: block;
        margin-bottom: 0.25rem;
        font-weight: 500;
    }}

    .form-group input,
    .form-group select {{
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #d0d0d0;
        border-radius: 4px;
    }}

    .actions {{
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
        display: flex;
        gap: 0.5rem;
        justify-content: flex-end;
    }}

    button {{
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
    }}

    button.primary {{
        background-color: #4f46e5;
        color: white;
    }}

    button.primary:hover {{
        background-color: #4338ca;
    }}

    button.secondary {{
        background-color: #f3f4f6;
        color: #374151;
    }}

    button.secondary:hover {{
        background-color: #e5e7eb;
    }}
</style>"""

        # Determine component path
        component_path = Path(f"src/components/{obj.name}.svelte")

        project.files.append(
            GeneratedFile(
                path=component_path,
                content=component_content,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_state_declarations(self, obj: SemanticObject) -> str:
        """Generate state variable declarations.

        Args:
            obj: Semantic object

        Returns:
            TypeScript state declarations
        """
        declarations = []
        for prop in obj.properties:
            ts_type = self._map_to_ts_type(prop.data_type)
            default_value = self._get_default_value(prop)
            declarations.append(f"let {prop.name}: {ts_type} = {default_value};")
        return "\n    ".join(declarations)

    def _generate_methods(self, obj: SemanticObject) -> str:
        """Generate component methods.

        Args:
            obj: Semantic object

        Returns:
            TypeScript method implementations
        """
        methods = []
        for method in obj.methods:
            if method.access == "public":
                params = ", ".join(
                    f"{p.name}: {self._map_to_ts_type(p.data_type)}"
                    for p in method.parameters
                )
                methods.append(f"""async function {method.name}({params}) {{
        try {{
            // {method.name} implementation
            {method.body or "// TODO: Implement method"}
        }} catch (error) {{
            console.error('Error in {method.name}:', error);
        }}
    }}""")
        return "\n    ".join(methods)

    def _generate_component_body(self, obj: SemanticObject) -> str:
        """Generate component body HTML.

        Args:
            obj: Semantic object

        Returns:
            Component body HTML
        """
        if not obj.properties:
            return "<p>No properties defined</p>"

        fields = []
        for prop in obj.properties:
            field_html = self._generate_form_field_svelte(prop)
            fields.append(field_html)

        return "\n            ".join(fields)

    def _generate_form_field_svelte(self, prop: Property) -> str:
        """Generate Svelte form field.

        Args:
            prop: Property

        Returns:
            Form field HTML
        """
        label = self._format_label(prop.name)
        required = "required" if prop.is_required else ""

        if prop.data_type == "boolean":
            return f"""<div class="form-group">
                <label>
                    <input type="checkbox" bind:checked={{{prop.name}}} {required} />
                    {label}
                </label>
            </div>"""
        elif prop.data_type in ["number", "integer"]:
            return f"""<div class="form-group">
                <label for="{prop.name}">{label}</label>
                <input type="number" id="{prop.name}" bind:value={{{prop.name}}} {required} />
            </div>"""
        elif prop.data_type == "date":
            return f"""<div class="form-group">
                <label for="{prop.name}">{label}</label>
                <input type="date" id="{prop.name}" bind:value={{{prop.name}}} {required} />
            </div>"""
        else:
            return f"""<div class="form-group">
                <label for="{prop.name}">{label}</label>
                <input type="text" id="{prop.name}" bind:value={{{prop.name}}} {required} />
            </div>"""

    def _generate_actions(self, obj: SemanticObject) -> str:
        """Generate action buttons.

        Args:
            obj: Semantic object

        Returns:
            Actions HTML
        """
        if not obj.methods:
            return ""

        buttons = []
        for method in obj.methods:
            if method.access == "public" and not method.name.startswith("_"):
                label = self._format_label(method.name)
                buttons.append(
                    f'<button class="primary" on:click={{{method.name}}}>{label}</button>'
                )

        if not buttons:
            return ""

        return f"""<div class="actions">
            {" ".join(buttons)}
        </div>"""

    def _generate_data_table(
        self, obj: SemanticObject, project: GeneratedProject
    ) -> None:
        """Generate data table component.

        Args:
            obj: Semantic object (DataWindow)
            project: Generated project
        """
        table_content = f"""<script lang="ts">
    import {{ onMount }} from 'svelte';
    import {{ writable }} from 'svelte/store';

    // Table state
    let data: any[] = [];
    let loading = false;
    let currentPage = 1;
    let pageSize = 20;
    let totalItems = 0;
    let selectedItems: any[] = [];

    // Computed
    $: totalPages = Math.ceil(totalItems / pageSize);
    $: paginatedData = data.slice(
        (currentPage - 1) * pageSize,
        currentPage * pageSize
    );

    // Fetch data
    async function fetchData() {{
        loading = true;
        try {{
            // TODO: Replace with actual API call
            const response = await fetch(`/api/{obj.name.lower()}?page=${{currentPage}}&size=${{pageSize}}`);
            const result = await response.json();
            data = result.data;
            totalItems = result.total;
        }} catch (error) {{
            console.error('Failed to fetch data:', error);
        }} finally {{
            loading = false;
        }}
    }}

    // Edit item
    function handleEdit(item: any) {{
        console.log('Edit item:', item);
        // TODO: Implement edit functionality
    }}

    // Delete item
    async function handleDelete(item: any) {{
        if (confirm('Are you sure you want to delete this item?')) {{
            try {{
                await fetch(`/api/{obj.name.lower()}/${{item.id}}`, {{
                    method: 'DELETE'
                }});
                await fetchData();
            }} catch (error) {{
                console.error('Failed to delete item:', error);
            }}
        }}
    }}

    // Selection
    function toggleSelection(item: any) {{
        const index = selectedItems.findIndex(i => i.id === item.id);
        if (index >= 0) {{
            selectedItems = selectedItems.filter(i => i.id !== item.id);
        }} else {{
            selectedItems = [...selectedItems, item];
        }}
    }}

    // Pagination
    function goToPage(page: number) {{
        if (page >= 1 && page <= totalPages) {{
            currentPage = page;
            fetchData();
        }}
    }}

    onMount(() => {{
        fetchData();
    }});
</script>

<div class="table-container">
    <div class="table-header">
        <h2>{obj.name} Data</h2>
        <button class="primary" on:click={{fetchData}}>Refresh</button>
    </div>

    {{#if loading}}
        <div class="loading">Loading...</div>
    {{:else}}
        <table>
            <thead>
                <tr>
                    <th>
                        <input
                            type="checkbox"
                            checked={{selectedItems.length === paginatedData.length}}
                            on:change={{() => {{
                                selectedItems = selectedItems.length === paginatedData.length
                                    ? []
                                    : [...paginatedData];
                            }}}}
                        />
                    </th>
                    {self._generate_table_headers(obj)}
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {{#each paginatedData as item}}
                    <tr>
                        <td>
                            <input
                                type="checkbox"
                                checked={{selectedItems.some(i => i.id === item.id)}}
                                on:change={{() => toggleSelection(item)}}
                            />
                        </td>
                        {self._generate_table_cells(obj)}
                        <td>
                            <button class="link" on:click={{() => handleEdit(item)}}>Edit</button>
                            <button class="link danger" on:click={{() => handleDelete(item)}}>Delete</button>
                        </td>
                    </tr>
                {{/each}}
            </tbody>
        </table>

        <div class="pagination">
            <button on:click={{() => goToPage(currentPage - 1)}} disabled={{currentPage === 1}}>
                Previous
            </button>
            <span>Page {{currentPage}} of {{totalPages}}</span>
            <button on:click={{() => goToPage(currentPage + 1)}} disabled={{currentPage === totalPages}}>
                Next
            </button>
        </div>
    {{/if}}
</div>

<style>
    .table-container {{
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1rem;
    }}

    .table-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }}

    .table-header h2 {{
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
    }}

    th {{
        text-align: left;
        padding: 0.75rem;
        border-bottom: 2px solid #e0e0e0;
        font-weight: 600;
    }}

    td {{
        padding: 0.75rem;
        border-bottom: 1px solid #f0f0f0;
    }}

    tr:hover {{
        background-color: #f9f9f9;
    }}

    .link {{
        background: none;
        border: none;
        color: #4f46e5;
        cursor: pointer;
        padding: 0.25rem 0.5rem;
        text-decoration: underline;
    }}

    .link.danger {{
        color: #dc2626;
    }}

    .pagination {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin-top: 1rem;
    }}

    .loading {{
        text-align: center;
        padding: 2rem;
        color: #666;
    }}
</style>"""

        project.files.append(
            GeneratedFile(
                path=Path(f"src/components/tables/{obj.name}Table.svelte"),
                content=table_content,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_table_headers(self, obj: SemanticObject) -> str:
        """Generate table headers.

        Args:
            obj: Semantic object

        Returns:
            Table header HTML
        """
        headers = []
        for prop in obj.properties[:6]:  # Limit to first 6 columns
            label = self._format_label(prop.name)
            headers.append(f"<th>{label}</th>")
        return "\n                    ".join(headers)

    def _generate_table_cells(self, obj: SemanticObject) -> str:
        """Generate table cells.

        Args:
            obj: Semantic object

        Returns:
            Table cell HTML
        """
        cells = []
        for prop in obj.properties[:6]:  # Limit to first 6 columns
            cells.append(f"<td>{{item.{prop.name}}}</td>")
        return "\n                        ".join(cells)

    def _generate_stores(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate Svelte stores.

        Args:
            model: Application model
            project: Generated project
        """
        app_store = """import { writable, derived } from 'svelte/store';

// App state
export const appStore = writable({
    showSidebar: true,
    theme: 'light',
    user: null
});

// Derived stores
export const isLoggedIn = derived(
    appStore,
    $app => !!$app.user
);

// Actions
export function toggleSidebar() {
    appStore.update(state => ({
        ...state,
        showSidebar: !state.showSidebar
    }));
}

export function setTheme(theme: string) {
    appStore.update(state => ({
        ...state,
        theme
    }));
    document.documentElement.setAttribute('data-theme', theme);
}

export function login(user: any) {
    appStore.update(state => ({
        ...state,
        user
    }));
}

export function logout() {
    appStore.update(state => ({
        ...state,
        user: null
    }));
}"""

        project.files.append(
            GeneratedFile(
                path=Path("src/stores/app.ts"),
                content=app_store,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_routes(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate SvelteKit routes.

        Args:
            model: Application model
            project: Generated project
        """
        # Home page
        home_page = """<script lang="ts">
    import { appStore } from '$stores/app';
</script>

<svelte:head>
    <title>Home</title>
</svelte:head>

<div class="page">
    <h1>Welcome to {$appStore.user?.name || 'PowerRebuilder'}</h1>
    <p>Your application has been successfully converted from PowerBuilder to Svelte.</p>
</div>

<style>
    .page {
        max-width: 800px;
        margin: 0 auto;
    }

    h1 {
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    p {
        font-size: 1.125rem;
        color: #666;
    }
</style>"""

        project.files.append(
            GeneratedFile(
                path=Path("src/routes/+page.svelte"),
                content=home_page,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_styles(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate global styles.

        Args:
            model: Application model
            project: Generated project
        """
        styles = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background-color: #fafafa;
}

button.primary {
    background-color: #4f46e5;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
}

button.primary:hover {
    background-color: #4338ca;
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}"""

        project.files.append(
            GeneratedFile(
                path=Path("src/app.css"),
                content=styles,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _map_to_ts_type(self, data_type: str) -> str:
        """Map data type to TypeScript type.

        Args:
            data_type: Data type

        Returns:
            TypeScript type
        """
        type_map = {
            "string": "string",
            "number": "number",
            "integer": "number",
            "boolean": "boolean",
            "date": "Date",
            "datetime": "Date",
            "array": "any[]",
            "object": "Record<string, any>",
        }
        return type_map.get(data_type, "any")

    def _get_default_value(self, prop: Property) -> str:
        """Get default value for property.

        Args:
            prop: Property

        Returns:
            Default value as string
        """
        if prop.default_value:
            return prop.default_value

        type_defaults = {
            "string": "''",
            "number": "0",
            "integer": "0",
            "boolean": "false",
            "date": "new Date()",
            "datetime": "new Date()",
            "array": "[]",
            "object": "{}",
        }
        return type_defaults.get(prop.data_type, "null")

    def _format_label(self, name: str) -> str:
        """Format name as label.

        Args:
            name: Property/method name

        Returns:
            Formatted label
        """
        import re

        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", name)
        if not words:
            words = name.split("_")
        return " ".join(word.capitalize() for word in words)
