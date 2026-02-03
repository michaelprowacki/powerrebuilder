"""Vue.js Generator - Generate Vue 3 applications from semantic models.

This generator creates modern Vue.js applications with Composition API,
TypeScript support, and Pinia state management.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

from src_new._core.models import (
    ApplicationModel,
    GeneratedFile,
    GeneratedProject,
    Method,
    Property,
    SemanticObject,
    TargetLanguage,
)
from .generator import BaseCodeGenerator

logger = logging.getLogger(__name__)


class VueGenerator(BaseCodeGenerator):
    """Generator for Vue.js applications."""

    def __init__(self, input_path: str, output_path: str):
        """Initialize Vue generator.

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
        """Generate complete Vue.js project.

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
        self._generate_vite_config(model, project)
        self._generate_tsconfig(model, project)
        self._generate_app_vue(model, project)
        self._generate_main_ts(model, project)

        # Generate components for each object
        for obj in model.objects:
            if obj.type == "window" or obj.type == "class":
                self._generate_component(obj, project)
            elif obj.type == "datawindow":
                self._generate_data_table(obj, project)

        # Generate stores
        self._generate_stores(model, project)

        # Generate router
        self._generate_router(model, project)

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
                "dev": "vite",
                "build": "vue-tsc && vite build",
                "preview": "vite preview",
                "type-check": "vue-tsc --noEmit",
                "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
                "format": "prettier --write .",
            },
            "dependencies": {
                "vue": "^3.3.0",
                "vue-router": "^4.2.0",
                "pinia": "^2.1.0",
                "axios": "^1.6.0",
                "@vueuse/core": "^10.7.0",
                "element-plus": "^2.4.0",
            },
            "devDependencies": {
                "@vitejs/plugin-vue": "^4.5.0",
                "@vue/tsconfig": "^0.5.0",
                "typescript": "^5.3.0",
                "vite": "^5.0.0",
                "vue-tsc": "^1.8.0",
                "@types/node": "^20.10.0",
                "eslint": "^8.55.0",
                "eslint-plugin-vue": "^9.19.0",
                "prettier": "^3.1.0",
            },
        }

        project.files.append(
            GeneratedFile(
                path=Path("package.json"),
                content=json.dumps(package, indent=2),
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
        config = """import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})"""

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
            "extends": "@vue/tsconfig/tsconfig.dom.json",
            "include": ["env.d.ts", "src/**/*", "src/**/*.vue"],
            "exclude": ["src/**/__tests__/*"],
            "compilerOptions": {
                "composite": True,
                "baseUrl": ".",
                "paths": {"@/*": ["./src/*"]},
                "types": ["element-plus/global"],
            },
        }

        project.files.append(
            GeneratedFile(
                path=Path("tsconfig.json"),
                content=json.dumps(tsconfig, indent=2),
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_app_vue(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate main App.vue component.

        Args:
            model: Application model
            project: Generated project
        """
        app_content = """<template>
  <el-config-provider :locale="locale">
    <div id="app">
      <el-container>
        <el-header>
          <AppHeader />
        </el-header>
        <el-container>
          <el-aside width="200px" v-if="showSidebar">
            <AppSidebar />
          </el-aside>
          <el-main>
            <router-view v-slot="{ Component, route }">
              <transition name="fade" mode="out-in">
                <component :is="Component" :key="route.path" />
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElConfigProvider, ElContainer, ElHeader, ElAside, ElMain } from 'element-plus'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import { useAppStore } from '@/stores/app'
import en from 'element-plus/es/locale/lang/en'

const appStore = useAppStore()
const router = useRouter()

const locale = ref(en)
const showSidebar = computed(() => appStore.showSidebar)
</script>

<style scoped>
#app {
  height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.el-aside {
  background-color: #f5f5f5;
  border-right: 1px solid #e6e6e6;
}

.el-main {
  background-color: #fafafa;
  padding: 20px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>"""

        project.files.append(
            GeneratedFile(
                path=Path("src/App.vue"),
                content=app_content,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_main_ts(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate main.ts entry point.

        Args:
            model: Application model
            project: Generated project
        """
        main_content = """import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

// Register Element Plus Icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')"""

        project.files.append(
            GeneratedFile(
                path=Path("src/main.ts"),
                content=main_content,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_component(
        self, obj: SemanticObject, project: GeneratedProject
    ) -> None:
        """Generate Vue component for an object.

        Args:
            obj: Semantic object
            project: Generated project
        """
        # Generate component template
        template = self._generate_template(obj)

        # Generate script setup
        script = self._generate_script_setup(obj)

        # Generate styles
        styles = self._generate_component_styles(obj)

        component_content = f"""<template>
{template}
</template>

<script setup lang="ts">
{script}
</script>

<style scoped>
{styles}
</style>"""

        # Determine component path
        component_path = Path(f"src/components/{obj.name}.vue")

        project.files.append(
            GeneratedFile(
                path=component_path,
                content=component_content,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_template(self, obj: SemanticObject) -> str:
        """Generate component template.

        Args:
            obj: Semantic object

        Returns:
            Template HTML
        """
        template_parts = [
            f'  <div class="{obj.name.lower()}-container">',
            "    <el-card>",
            "      <template #header>",
            '        <div class="card-header">',
            f"          <span>{obj.name}</span>",
            "        </div>",
            "      </template>",
        ]

        # Add form fields for properties
        if obj.properties:
            template_parts.append(
                '      <el-form :model="formData" label-width="120px">'
            )

            for prop in obj.properties:
                field = self._generate_form_field(prop)
                template_parts.append(field)

            template_parts.append("      </el-form>")

        # Add action buttons for methods
        if obj.methods:
            template_parts.append('      <div class="actions">')
            for method in obj.methods:
                if method.access == "public" and not method.name.startswith("_"):
                    template_parts.append(
                        f'        <el-button @click="{method.name}">{self._format_label(method.name)}</el-button>'
                    )
            template_parts.append("      </div>")

        template_parts.extend(["    </el-card>", "  </div>"])

        return "\n".join(template_parts)

    def _generate_form_field(self, prop: Property) -> str:
        """Generate form field for a property.

        Args:
            prop: Property

        Returns:
            Form field HTML
        """
        label = self._format_label(prop.name)

        # Determine input type based on data type
        if prop.data_type == "boolean":
            return f"""        <el-form-item label="{label}">
          <el-switch v-model="formData.{prop.name}" />
        </el-form-item>"""
        elif prop.data_type == "number":
            return f"""        <el-form-item label="{label}">
          <el-input-number v-model="formData.{prop.name}" />
        </el-form-item>"""
        elif prop.data_type == "date":
            return f"""        <el-form-item label="{label}">
          <el-date-picker v-model="formData.{prop.name}" type="date" />
        </el-form-item>"""
        else:
            return f"""        <el-form-item label="{label}">
          <el-input v-model="formData.{prop.name}" />
        </el-form-item>"""

    def _generate_script_setup(self, obj: SemanticObject) -> str:
        """Generate script setup for component.

        Args:
            obj: Semantic object

        Returns:
            TypeScript code
        """
        script_parts = [
            "import { ref, reactive, computed, onMounted } from 'vue'",
            "import { ElMessage } from 'element-plus'",
            "import { useRouter } from 'vue-router'",
            "",
        ]

        # Add interface for form data
        if obj.properties:
            script_parts.append(f"interface {obj.name}Data {{")
            for prop in obj.properties:
                ts_type = self._map_to_ts_type(prop.data_type)
                optional = "" if prop.is_required else "?"
                script_parts.append(f"  {prop.name}{optional}: {ts_type}")
            script_parts.append("}")
            script_parts.append("")

        # Create reactive form data
        if obj.properties:
            script_parts.append(f"const formData = reactive<{obj.name}Data>({{")
            for prop in obj.properties:
                default_value = self._get_default_value(prop)
                script_parts.append(f"  {prop.name}: {default_value},")
            script_parts.append("})")
            script_parts.append("")

        # Add methods
        for method in obj.methods:
            if method.access == "public":
                script_parts.append(self._generate_method(method))
                script_parts.append("")

        # Add lifecycle hooks
        script_parts.append("onMounted(() => {")
        script_parts.append("  // Initialize component")
        script_parts.append("  console.log('Component mounted')")
        script_parts.append("})")

        return "\n".join(script_parts)

    def _generate_method(self, method: Method) -> str:
        """Generate method implementation.

        Args:
            method: Method definition

        Returns:
            TypeScript method code
        """
        params = ", ".join(
            f"{p.name}: {self._map_to_ts_type(p.data_type)}" for p in method.parameters
        )

        return f"""const {method.name} = async ({params}) => {{
  try {{
    // {method.name} implementation
    {method.body or "// TODO: Implement method"}

    ElMessage.success('{self._format_label(method.name)} completed')
  }} catch (error) {{
    ElMessage.error('Operation failed')
    console.error(error)
  }}
}}"""

    def _generate_component_styles(self, obj: SemanticObject) -> str:
        """Generate component styles.

        Args:
            obj: Semantic object

        Returns:
            CSS styles
        """
        return f""".{obj.name.lower()}-container {{
  padding: 20px;
}}

.card-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
}}

.actions {{
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}}"""

    def _generate_data_table(
        self, obj: SemanticObject, project: GeneratedProject
    ) -> None:
        """Generate data table component for DataWindow.

        Args:
            obj: Semantic object (DataWindow)
            project: Generated project
        """
        table_content = f"""<template>
  <div class="data-table-container">
    <el-table
      :data="tableData"
      v-loading="loading"
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      {self._generate_table_columns(obj)}
      <el-table-column fixed="right" label="Operations" width="120">
        <template #default="scope">
          <el-button link type="primary" size="small" @click="handleEdit(scope.row)">Edit</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(scope.row)">Delete</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 50, 100]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup lang="ts">
import {{ ref, onMounted }} from 'vue'
import {{ ElMessage, ElMessageBox }} from 'element-plus'
import {{ use{obj.name}Store }} from '@/stores/{obj.name.lower()}'

const store = use{obj.name}Store()

const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const multipleSelection = ref([])

const fetchData = async () => {{
  loading.value = true
  try {{
    const response = await store.fetchData({{
      page: currentPage.value,
      size: pageSize.value
    }})
    tableData.value = response.data
    total.value = response.total
  }} catch (error) {{
    ElMessage.error('Failed to load data')
  }} finally {{
    loading.value = false
  }}
}}

const handleEdit = (row: any) => {{
  // Handle edit
  console.log('Edit', row)
}}

const handleDelete = async (row: any) => {{
  await ElMessageBox.confirm('Are you sure to delete this item?', 'Warning', {{
    confirmButtonText: 'OK',
    cancelButtonText: 'Cancel',
    type: 'warning',
  }})

  try {{
    await store.deleteItem(row.id)
    ElMessage.success('Deleted successfully')
    fetchData()
  }} catch {{
    ElMessage.error('Delete failed')
  }}
}}

const handleSelectionChange = (val: any[]) => {{
  multipleSelection.value = val
}}

const handleSizeChange = (val: number) => {{
  pageSize.value = val
  fetchData()
}}

const handleCurrentChange = (val: number) => {{
  currentPage.value = val
  fetchData()
}}

onMounted(() => {{
  fetchData()
}})
</script>

<style scoped>
.data-table-container {{
  padding: 20px;
}}

.el-pagination {{
  margin-top: 20px;
  justify-content: flex-end;
}}
</style>"""

        project.files.append(
            GeneratedFile(
                path=Path(f"src/components/tables/{obj.name}Table.vue"),
                content=table_content,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_table_columns(self, obj: SemanticObject) -> str:
        """Generate table columns.

        Args:
            obj: Semantic object

        Returns:
            Table column definitions
        """
        columns = []
        for prop in obj.properties[:6]:  # Limit to first 6 columns
            label = self._format_label(prop.name)
            columns.append(f'<el-table-column prop="{prop.name}" label="{label}" />')
        return "\n      ".join(columns)

    def _generate_stores(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate Pinia stores.

        Args:
            model: Application model
            project: Generated project
        """
        # Generate app store
        app_store = """import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', () => {
  const showSidebar = ref(true)
  const theme = ref('light')
  const user = ref(null)

  const isLoggedIn = computed(() => !!user.value)

  function toggleSidebar() {
    showSidebar.value = !showSidebar.value
  }

  function setTheme(newTheme: string) {
    theme.value = newTheme
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  function login(userData: any) {
    user.value = userData
  }

  function logout() {
    user.value = null
  }

  return {
    showSidebar,
    theme,
    user,
    isLoggedIn,
    toggleSidebar,
    setTheme,
    login,
    logout
  }
})"""

        project.files.append(
            GeneratedFile(
                path=Path("src/stores/app.ts"),
                content=app_store,
                language=TargetLanguage.JAVASCRIPT,
            )
        )

    def _generate_router(
        self, model: ApplicationModel, project: GeneratedProject
    ) -> None:
        """Generate Vue Router configuration.

        Args:
            model: Application model
            project: Generated project
        """
        router_content = """import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue')
    }
  ]
})

export default router"""

        project.files.append(
            GeneratedFile(
                path=Path("src/router/index.ts"),
                content=router_content,
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
        styles = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh;
  overflow: hidden;
}"""

        project.files.append(
            GeneratedFile(
                path=Path("src/assets/main.css"),
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
        # Convert camelCase or snake_case to Title Case
        import re

        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", name)
        if not words:
            words = name.split("_")
        return " ".join(word.capitalize() for word in words)
