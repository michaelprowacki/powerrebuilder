"""React Generator - Generate React applications from PowerBuilder objects.

This module generates React components, hooks, and state management from
PowerBuilder semantic models.
"""

import json
import logging
from typing import List, Optional

from src_new._core import (
    ApplicationModel,
    GeneratedFile,
    SemanticObject,
    TargetLanguage,
)
from .generator import BaseCodeGenerator

logger = logging.getLogger(__name__)


class ReactGenerator(BaseCodeGenerator):
    """Generator for React applications."""

    def __init__(self):
        """Initialize React generator."""
        super().__init__(TargetLanguage.REACT)

        self.type_map = {
            "string": "string",
            "char": "string",
            "int": "number",
            "integer": "number",
            "long": "number",
            "decimal": "number",
            "float": "number",
            "double": "number",
            "boolean": "boolean",
            "bool": "boolean",
            "date": "Date",
            "datetime": "Date",
            "blob": "Blob",
            "any": "any",
            "object": "Record<string, any>",
        }

    def generate_window(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate React component from window.

        Args:
            obj: Window object

        Returns:
            Generated React files
        """
        files = []

        # Generate main component
        component = self._generate_component(obj)
        files.append(
            GeneratedFile(
                path=f"src/components/{obj.name}/{obj.name}.tsx",
                content=component,
                language=TargetLanguage.REACT,
            )
        )

        # Generate styles
        styles = self._generate_styles(obj)
        files.append(
            GeneratedFile(
                path=f"src/components/{obj.name}/{obj.name}.module.css",
                content=styles,
                language=TargetLanguage.REACT,
                file_type="style",
            )
        )

        # Generate tests
        test = self._generate_test(obj)
        files.append(
            GeneratedFile(
                path=f"src/components/{obj.name}/{obj.name}.test.tsx",
                content=test,
                language=TargetLanguage.REACT,
                file_type="test",
            )
        )

        return files

    def generate_datawindow(self, obj: SemanticObject) -> List[GeneratedFile]:
        """Generate React data grid component.

        Args:
            obj: DataWindow object

        Returns:
            Generated React files
        """
        files = []

        # Generate data grid component
        grid = self._generate_data_grid(obj)
        files.append(
            GeneratedFile(
                path=f"src/components/{obj.name}Grid/{obj.name}Grid.tsx",
                content=grid,
                language=TargetLanguage.REACT,
            )
        )

        # Generate hooks
        hook = self._generate_data_hook(obj)
        files.append(
            GeneratedFile(
                path=f"src/hooks/use{obj.name}Data.ts",
                content=hook,
                language=TargetLanguage.REACT,
            )
        )

        # Generate API service
        service = self._generate_api_service(obj)
        files.append(
            GeneratedFile(
                path=f"src/services/{obj.name}Service.ts",
                content=service,
                language=TargetLanguage.REACT,
            )
        )

        return files

    def generate_config(self, model: ApplicationModel) -> List[GeneratedFile]:
        """Generate React project configuration.

        Args:
            model: Application model

        Returns:
            Configuration files
        """
        files = []

        # Generate package.json
        package = {
            "name": model.name.lower().replace(" ", "-"),
            "version": model.version,
            "private": True,
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject",
                "lint": "eslint src/**/*.{ts,tsx}",
                "format": "prettier --write src/**/*.{ts,tsx,css}",
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.14.0",
                "@mui/material": "^5.14.0",
                "@mui/icons-material": "^5.14.0",
                "@emotion/react": "^11.11.0",
                "@emotion/styled": "^11.11.0",
                "axios": "^1.4.0",
                "@tanstack/react-query": "^4.29.0",
                "@reduxjs/toolkit": "^1.9.0",
                "react-redux": "^8.1.0",
                "react-hook-form": "^7.45.0",
                "ag-grid-react": "^30.0.0",
                "date-fns": "^2.30.0",
            },
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@types/node": "^20.0.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.0",
                "@testing-library/user-event": "^14.4.0",
                "react-scripts": "5.0.1",
                "typescript": "^5.0.0",
                "eslint": "^8.0.0",
                "prettier": "^2.8.0",
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": [
                    "last 1 chrome version",
                    "last 1 firefox version",
                    "last 1 safari version",
                ],
            },
        }

        files.append(
            GeneratedFile(
                path="package.json",
                content=json.dumps(package, indent=2),
                language=TargetLanguage.REACT,
                file_type="config",
            )
        )

        # Generate tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "lib": ["DOM", "DOM.Iterable", "ESNext"],
                "allowJs": True,
                "skipLibCheck": True,
                "esModuleInterop": True,
                "allowSyntheticDefaultImports": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "noFallthroughCasesInSwitch": True,
                "module": "esnext",
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
            },
            "include": ["src"],
        }

        files.append(
            GeneratedFile(
                path="tsconfig.json",
                content=json.dumps(tsconfig, indent=2),
                language=TargetLanguage.REACT,
                file_type="config",
            )
        )

        # Generate App.tsx
        app = self._generate_app(model)
        files.append(
            GeneratedFile(
                path="src/App.tsx",
                content=app,
                language=TargetLanguage.REACT,
            )
        )

        # Generate index.tsx
        index = self._generate_index(model)
        files.append(
            GeneratedFile(
                path="src/index.tsx",
                content=index,
                language=TargetLanguage.REACT,
            )
        )

        # Generate Redux store
        store = self._generate_store(model)
        files.append(
            GeneratedFile(
                path="src/store/index.ts",
                content=store,
                language=TargetLanguage.REACT,
            )
        )

        return files

    def _generate_component(self, obj: SemanticObject) -> str:
        """Generate React component.

        Args:
            obj: Semantic object

        Returns:
            Component code
        """
        lines = []
        comp_name = self._to_component_name(obj.name)

        # Imports
        lines.append("import React, { useState, useEffect, useCallback } from 'react';")
        lines.append("import {")
        lines.append("  Box,")
        lines.append("  Paper,")
        lines.append("  Typography,")
        lines.append("  Button,")
        lines.append("  TextField,")
        lines.append("  Grid,")
        lines.append("} from '@mui/material';")
        lines.append(f"import styles from './{obj.name}.module.css';")
        lines.append("")

        # Interface
        lines.append(f"interface {comp_name}Props {{")
        lines.append("  // Component props")
        for prop in obj.properties[:5]:  # First 5 as examples
            if prop.access != "private":
                ts_type = self._map_type(prop.type)
                optional = "?" if not prop.is_required else ""
                lines.append(f"  {prop.name}{optional}: {ts_type};")
        lines.append("}")
        lines.append("")

        # Component
        lines.append(
            f"export const {comp_name}: React.FC<{comp_name}Props> = (props) => {{"
        )

        # State
        lines.append("  // Component state")
        for prop in obj.properties[:3]:  # First 3 as state examples
            default_val = self._get_default_value(prop.type)
            lines.append(
                f"  const [{prop.name}, set{self._to_pascal_case(prop.name)}] = useState({default_val});"
            )
        lines.append("")

        # Effects
        lines.append("  // Lifecycle effects")
        lines.append("  useEffect(() => {")
        lines.append("    // Component mount")
        lines.append("    console.log('Component mounted');")
        lines.append("    return () => {")
        lines.append("      // Component unmount")
        lines.append("      console.log('Component unmounted');")
        lines.append("    };")
        lines.append("  }, []);")
        lines.append("")

        # Event handlers
        if obj.events:
            lines.append("  // Event handlers")
            for event in obj.events[:3]:  # First 3 events
                lines.append(
                    f"  const handle{self._to_pascal_case(event.name)} = useCallback(() => {{"
                )
                lines.append(f"    console.log('Handle {event.name}');")
                if event.body:
                    lines.append(f"    // {event.body}")
                lines.append("  }, []);")
                lines.append("")

        # Methods
        if obj.methods:
            lines.append("  // Methods")
            for method in obj.methods[:3]:  # First 3 methods
                if method.access != "private":
                    lines.append(f"  const {method.name} = useCallback(() => {{")
                    if method.body:
                        lines.append(f"    // {method.body}")
                    lines.append("  }, []);")
                    lines.append("")

        # Render
        lines.append("  return (")
        lines.append("    <Paper className={styles.container}>")
        lines.append("      <Box p={3}>")
        lines.append("        <Typography variant='h4' gutterBottom>")
        lines.append(f"          {obj.name}")
        lines.append("        </Typography>")
        lines.append("        ")
        lines.append("        <Grid container spacing={3}>")

        # Form fields for properties
        for prop in obj.properties[:4]:
            if prop.access != "private":
                lines.append("          <Grid item xs={12} md={6}>")
                lines.append("            <TextField")
                lines.append("              fullWidth")
                lines.append(f"              label='{prop.name}'")
                lines.append(f"              value={{{prop.name}}}")
                lines.append(
                    f"              onChange={{(e) => set{self._to_pascal_case(prop.name)}(e.target.value)}}"
                )
                lines.append("            />")
                lines.append("          </Grid>")

        lines.append("        </Grid>")
        lines.append("        ")
        lines.append("        <Box mt={3}>")
        lines.append("          <Button variant='contained' color='primary'>")
        lines.append("            Submit")
        lines.append("          </Button>")
        lines.append("        </Box>")
        lines.append("      </Box>")
        lines.append("    </Paper>")
        lines.append("  );")
        lines.append("};")
        lines.append("")
        lines.append(f"export default {comp_name};")

        return "\n".join(lines)

    def _generate_data_grid(self, obj: SemanticObject) -> str:
        """Generate data grid component.

        Args:
            obj: DataWindow object

        Returns:
            Grid component code
        """
        lines = []
        comp_name = f"{self._to_component_name(obj.name)}Grid"

        lines.append("import React, { useMemo, useCallback } from 'react';")
        lines.append("import { AgGridReact } from 'ag-grid-react';")
        lines.append(
            "import { ColDef, GridApi, GridReadyEvent } from 'ag-grid-community';"
        )
        lines.append("import 'ag-grid-community/styles/ag-grid.css';")
        lines.append("import 'ag-grid-community/styles/ag-theme-material.css';")
        lines.append(
            f"import {{ use{obj.name}Data }} from '../../hooks/use{obj.name}Data';"
        )
        lines.append("")

        lines.append(f"export const {comp_name}: React.FC = () => {{")
        lines.append(
            f"  const {{ data, loading, error, refetch }} = use{obj.name}Data();"
        )
        lines.append(
            "  const [gridApi, setGridApi] = React.useState<GridApi | null>(null);"
        )
        lines.append("")

        # Column definitions
        lines.append("  const columnDefs = useMemo<ColDef[]>(() => [")
        for prop in obj.properties[:6]:  # First 6 columns
            lines.append("    {")
            lines.append(f"      field: '{prop.name}',")
            lines.append(f"      headerName: '{self._to_title(prop.name)}',")
            lines.append("      sortable: true,")
            lines.append("      filter: true,")
            lines.append("      resizable: true,")
            lines.append("    },")
        lines.append("  ], []);")
        lines.append("")

        lines.append("  const onGridReady = useCallback((event: GridReadyEvent) => {")
        lines.append("    setGridApi(event.api);")
        lines.append("  }, []);")
        lines.append("")

        lines.append("  if (loading) return <div>Loading...</div>;")
        lines.append("  if (error) return <div>Error: {error.message}</div>;")
        lines.append("")

        lines.append("  return (")
        lines.append(
            "    <div className='ag-theme-material' style={{ height: 600, width: '100%' }}>"
        )
        lines.append("      <AgGridReact")
        lines.append("        rowData={data}")
        lines.append("        columnDefs={columnDefs}")
        lines.append("        onGridReady={onGridReady}")
        lines.append("        animateRows={true}")
        lines.append("        pagination={true}")
        lines.append("        paginationPageSize={20}")
        lines.append("      />")
        lines.append("    </div>")
        lines.append("  );")
        lines.append("};")

        return "\n".join(lines)

    def _generate_data_hook(self, obj: SemanticObject) -> str:
        """Generate React Query hook.

        Args:
            obj: DataWindow object

        Returns:
            Hook code
        """
        lines = []

        lines.append(
            "import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';"
        )
        lines.append(
            f"import {{ {obj.name}Service }} from '../services/{obj.name}Service';"
        )
        lines.append("")

        lines.append(f"const service = new {obj.name}Service();")
        lines.append("")

        lines.append(f"export const use{obj.name}Data = () => {{")
        lines.append("  const queryClient = useQueryClient();")
        lines.append("")

        lines.append("  const query = useQuery({")
        lines.append(f"    queryKey: ['{obj.name.lower()}'],")
        lines.append("    queryFn: () => service.getAll(),")
        lines.append("  });")
        lines.append("")

        lines.append("  const createMutation = useMutation({")
        lines.append("    mutationFn: service.create,")
        lines.append("    onSuccess: () => {")
        lines.append(
            f"      queryClient.invalidateQueries({{ queryKey: ['{obj.name.lower()}'] }});"
        )
        lines.append("    },")
        lines.append("  });")
        lines.append("")

        lines.append("  const updateMutation = useMutation({")
        lines.append("    mutationFn: ({ id, data }: any) => service.update(id, data),")
        lines.append("    onSuccess: () => {")
        lines.append(
            f"      queryClient.invalidateQueries({{ queryKey: ['{obj.name.lower()}'] }});"
        )
        lines.append("    },")
        lines.append("  });")
        lines.append("")

        lines.append("  const deleteMutation = useMutation({")
        lines.append("    mutationFn: service.delete,")
        lines.append("    onSuccess: () => {")
        lines.append(
            f"      queryClient.invalidateQueries({{ queryKey: ['{obj.name.lower()}'] }});"
        )
        lines.append("    },")
        lines.append("  });")
        lines.append("")

        lines.append("  return {")
        lines.append("    data: query.data,")
        lines.append("    loading: query.isLoading,")
        lines.append("    error: query.error,")
        lines.append("    refetch: query.refetch,")
        lines.append("    create: createMutation.mutate,")
        lines.append("    update: updateMutation.mutate,")
        lines.append("    delete: deleteMutation.mutate,")
        lines.append("  };")
        lines.append("};")

        return "\n".join(lines)

    def _generate_api_service(self, obj: SemanticObject) -> str:
        """Generate API service.

        Args:
            obj: DataWindow object

        Returns:
            Service code
        """
        lines = []

        lines.append("import axios from 'axios';")
        lines.append("")

        lines.append(f"export interface {obj.name}Model {{")
        for prop in obj.properties[:8]:
            ts_type = self._map_type(prop.type)
            optional = "?" if not prop.is_required else ""
            lines.append(f"  {prop.name}{optional}: {ts_type};")
        lines.append("}")
        lines.append("")

        lines.append(f"export class {obj.name}Service {{")
        lines.append("  private baseURL = '/api';")
        lines.append("")

        lines.append(f"  async getAll(): Promise<{obj.name}Model[]> {{")
        lines.append(
            f"    const response = await axios.get(`${{this.baseURL}}/{obj.name.lower()}`);"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append(
            f"  async getById(id: string | number): Promise<{obj.name}Model> {{"
        )
        lines.append(
            f"    const response = await axios.get(`${{this.baseURL}}/{obj.name.lower()}/${{id}}`);"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append(
            f"  async create(data: {obj.name}Model): Promise<{obj.name}Model> {{"
        )
        lines.append(
            f"    const response = await axios.post(`${{this.baseURL}}/{obj.name.lower()}`, data);"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append(
            f"  async update(id: string | number, data: Partial<{obj.name}Model>): Promise<{obj.name}Model> {{"
        )
        lines.append(
            f"    const response = await axios.put(`${{this.baseURL}}/{obj.name.lower()}/${{id}}`, data);"
        )
        lines.append("    return response.data;")
        lines.append("  }")
        lines.append("")

        lines.append("  async delete(id: string | number): Promise<void> {")
        lines.append(
            f"    await axios.delete(`${{this.baseURL}}/{obj.name.lower()}/${{id}}`);"
        )
        lines.append("  }")
        lines.append("}")

        return "\n".join(lines)

    def _generate_styles(self, obj: SemanticObject) -> str:
        """Generate CSS module.

        Args:
            obj: Semantic object

        Returns:
            CSS code
        """
        lines = []

        lines.append(".container {")
        lines.append("  margin: 24px;")
        lines.append("  padding: 24px;")
        lines.append("  background: #ffffff;")
        lines.append("  border-radius: 8px;")
        lines.append("  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);")
        lines.append("}")
        lines.append("")

        lines.append(".header {")
        lines.append("  margin-bottom: 24px;")
        lines.append("  padding-bottom: 16px;")
        lines.append("  border-bottom: 1px solid #e0e0e0;")
        lines.append("}")
        lines.append("")

        lines.append(".content {")
        lines.append("  padding: 16px;")
        lines.append("}")
        lines.append("")

        lines.append(".actions {")
        lines.append("  margin-top: 24px;")
        lines.append("  display: flex;")
        lines.append("  gap: 12px;")
        lines.append("  justify-content: flex-end;")
        lines.append("}")

        return "\n".join(lines)

    def _generate_test(self, obj: SemanticObject) -> str:
        """Generate component test.

        Args:
            obj: Semantic object

        Returns:
            Test code
        """
        lines = []
        comp_name = self._to_component_name(obj.name)

        lines.append("import React from 'react';")
        lines.append(
            "import { render, screen, fireEvent } from '@testing-library/react';"
        )
        lines.append("import '@testing-library/jest-dom';")
        lines.append(f"import {{ {comp_name} }} from './{obj.name}';")
        lines.append("")

        lines.append(f"describe('{comp_name}', () => {{")
        lines.append("  it('renders without crashing', () => {")
        lines.append(f"    render(<{comp_name} />);")
        lines.append(f"    expect(screen.getByText('{obj.name}')).toBeInTheDocument();")
        lines.append("  });")
        lines.append("")

        lines.append("  it('handles user interactions', () => {")
        lines.append(f"    render(<{comp_name} />);")
        lines.append("    const submitButton = screen.getByText('Submit');")
        lines.append("    fireEvent.click(submitButton);")
        lines.append("    // Add assertions")
        lines.append("  });")
        lines.append("});")

        return "\n".join(lines)

    def _generate_app(self, model: ApplicationModel) -> str:
        """Generate App.tsx.

        Args:
            model: Application model

        Returns:
            App component code
        """
        lines = []

        lines.append("import React from 'react';")
        lines.append(
            "import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';"
        )
        lines.append(
            "import { ThemeProvider, createTheme } from '@mui/material/styles';"
        )
        lines.append(
            "import { CssBaseline, AppBar, Toolbar, Typography, Container } from '@mui/material';"
        )
        lines.append(
            "import { QueryClient, QueryClientProvider } from '@tanstack/react-query';"
        )
        lines.append("import { Provider } from 'react-redux';")
        lines.append("import { store } from './store';")
        lines.append("")

        # Import components
        for obj_name in list(model.objects.keys())[:5]:  # First 5
            lines.append(
                f"import {{ {self._to_component_name(obj_name)} }} from './components/{obj_name}/{obj_name}';"
            )
        lines.append("")

        lines.append("const theme = createTheme({")
        lines.append("  palette: {")
        lines.append("    primary: {")
        lines.append("      main: '#1976d2',")
        lines.append("    },")
        lines.append("    secondary: {")
        lines.append("      main: '#dc004e',")
        lines.append("    },")
        lines.append("  },")
        lines.append("});")
        lines.append("")

        lines.append("const queryClient = new QueryClient();")
        lines.append("")

        lines.append("function App() {")
        lines.append("  return (")
        lines.append("    <Provider store={store}>")
        lines.append("      <QueryClientProvider client={queryClient}>")
        lines.append("        <ThemeProvider theme={theme}>")
        lines.append("          <CssBaseline />")
        lines.append("          <Router>")
        lines.append("            <AppBar position='static'>")
        lines.append("              <Toolbar>")
        lines.append(
            f"                <Typography variant='h6'>{model.name}</Typography>"
        )
        lines.append("              </Toolbar>")
        lines.append("            </AppBar>")
        lines.append("            <Container maxWidth='lg' sx={{ mt: 4 }}>")
        lines.append("              <Routes>")

        # Routes
        for obj_name in list(model.objects.keys())[:5]:
            comp_name = self._to_component_name(obj_name)
            path = obj_name.lower()
            lines.append(
                f"                <Route path='/{path}' element={{<{comp_name} />}} />"
            )

        lines.append("                <Route path='/' element={<div>Home</div>} />")
        lines.append("              </Routes>")
        lines.append("            </Container>")
        lines.append("          </Router>")
        lines.append("        </ThemeProvider>")
        lines.append("      </QueryClientProvider>")
        lines.append("    </Provider>")
        lines.append("  );")
        lines.append("}")
        lines.append("")
        lines.append("export default App;")

        return "\n".join(lines)

    def _generate_index(self, model: ApplicationModel) -> str:
        """Generate index.tsx.

        Args:
            model: Application model

        Returns:
            Index file code
        """
        lines = []

        lines.append("import React from 'react';")
        lines.append("import ReactDOM from 'react-dom/client';")
        lines.append("import './index.css';")
        lines.append("import App from './App';")
        lines.append("")

        lines.append("const root = ReactDOM.createRoot(")
        lines.append("  document.getElementById('root') as HTMLElement")
        lines.append(");")
        lines.append("")

        lines.append("root.render(")
        lines.append("  <React.StrictMode>")
        lines.append("    <App />")
        lines.append("  </React.StrictMode>")
        lines.append(");")

        return "\n".join(lines)

    def _generate_store(self, model: ApplicationModel) -> str:
        """Generate Redux store.

        Args:
            model: Application model

        Returns:
            Store configuration
        """
        lines = []

        lines.append("import { configureStore } from '@reduxjs/toolkit';")
        lines.append("")

        lines.append("// Import reducers")
        lines.append("// Add your slice reducers here")
        lines.append("")

        lines.append("export const store = configureStore({")
        lines.append("  reducer: {")
        lines.append("    // Add reducers here")
        lines.append("  },")
        lines.append("});")
        lines.append("")

        lines.append("export type RootState = ReturnType<typeof store.getState>;")
        lines.append("export type AppDispatch = typeof store.dispatch;")

        return "\n".join(lines)

    def _to_component_name(self, name: str) -> str:
        """Convert to React component name.

        Args:
            name: Original name

        Returns:
            Component name
        """
        return self._to_pascal_case(name)

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

    def _map_type(self, pb_type: Optional[str]) -> str:
        """Map PowerBuilder type to TypeScript.

        Args:
            pb_type: PowerBuilder type

        Returns:
            TypeScript type
        """
        if not pb_type:
            return "any"

        type_lower = pb_type.lower()
        return self.type_map.get(type_lower, "any")

    def _get_default_value(self, pb_type: str) -> str:
        """Get default value for type.

        Args:
            pb_type: PowerBuilder type

        Returns:
            Default value
        """
        ts_type = self._map_type(pb_type)

        if ts_type == "string":
            return "''"
        elif ts_type == "number":
            return "0"
        elif ts_type == "boolean":
            return "false"
        elif ts_type == "Date":
            return "new Date()"
        else:
            return "null"
