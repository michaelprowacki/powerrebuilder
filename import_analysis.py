#!/usr/bin/env python3
"""Comprehensive Import Map Generator for PowerRebuilder Codebase"""

import ast
import os
from collections import defaultdict
from pathlib import Path


class ImportAnalyzer:
    def __init__(self, root_dir: str = "src"):
        self.root_dir = Path(root_dir)
        self.modules = {}  # file_path -> {imports: [], exports: []}
        self.broken_imports = defaultdict(list)
        self.circular_deps = []
        self.dependency_graph = defaultdict(set)

    def analyze_file(self, file_path: Path) -> dict:
        """Analyze imports and exports in a Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            imports = []
            exports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(
                            {
                                "type": "import",
                                "module": alias.name,
                                "name": alias.asname or alias.name,
                                "line": node.lineno,
                            }
                        )
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(
                            {
                                "type": "from_import",
                                "module": module,
                                "name": alias.name,
                                "asname": alias.asname,
                                "line": node.lineno,
                            }
                        )
                elif isinstance(node, ast.FunctionDef):
                    exports.append(
                        {"type": "function", "name": node.name, "line": node.lineno}
                    )
                elif isinstance(node, ast.ClassDef):
                    exports.append(
                        {"type": "class", "name": node.name, "line": node.lineno}
                    )
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            exports.append(
                                {
                                    "type": "variable",
                                    "name": target.id,
                                    "line": node.lineno,
                                }
                            )

            # Check for __all__ exports
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in node.targets
                ):
                    if isinstance(node.value, ast.List):
                        for item in node.value.elts:
                            if isinstance(item, ast.Str):
                                exports.append(
                                    {
                                        "type": "__all__",
                                        "name": item.s,
                                        "line": node.lineno,
                                    }
                                )
                            elif isinstance(item, ast.Constant) and isinstance(
                                item.value, str
                            ):
                                exports.append(
                                    {
                                        "type": "__all__",
                                        "name": item.value,
                                        "line": node.lineno,
                                    }
                                )

            return {
                "imports": imports,
                "exports": exports,
                "file_path": str(file_path),
                "module_name": self.path_to_module_name(file_path),
            }

        except Exception as e:
            return {
                "imports": [],
                "exports": [],
                "file_path": str(file_path),
                "module_name": self.path_to_module_name(file_path),
                "error": str(e),
            }

    def path_to_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative_path = file_path.relative_to(self.root_dir.parent)
        module_parts = list(relative_path.parts)

        if module_parts[-1] == "__init__.py":
            module_parts = module_parts[:-1]
        elif module_parts[-1].endswith(".py"):
            module_parts[-1] = module_parts[-1][:-3]

        return ".".join(module_parts)

    def find_all_python_files(self) -> list[Path]:
        """Find all Python files in the source directory."""
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)
        return python_files

    def check_import_exists(self, import_module: str) -> bool:
        """Check if an import target actually exists."""
        try:
            # Handle relative imports
            if import_module.startswith("."):
                return True  # Skip relative import validation for now

            # Check if it's a standard library or installed package
            try:
                __import__(import_module.split(".")[0])
                return True
            except ImportError:
                pass

            # Check if it exists in our codebase
            module_path = import_module.replace(".", "/")

            # Check for __init__.py
            init_path = self.root_dir.parent / f"{module_path}/__init__.py"
            if init_path.exists():
                return True

            # Check for .py file
            py_path = self.root_dir.parent / f"{module_path}.py"
            if py_path.exists():
                return True

            return False

        except Exception:
            return False

    def detect_circular_dependencies(self) -> list[list[str]]:
        """Detect circular dependencies using DFS."""

        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.dependency_graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path + [neighbor], visited, rec_stack)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            return None

        visited = set()
        cycles = []

        for node in self.dependency_graph:
            if node not in visited:
                cycle = dfs(node, [node], visited, set())
                if cycle:
                    cycles.append(cycle)

        return cycles

    def analyze_all(self):
        """Run complete analysis on all Python files."""
        print("🔍 Finding Python files...")
        python_files = self.find_all_python_files()
        print(f"Found {len(python_files)} Python files")

        print("\n📊 Analyzing imports and exports...")
        for file_path in python_files:
            analysis = self.analyze_file(file_path)
            self.modules[str(file_path)] = analysis

            # Build dependency graph
            module_name = analysis["module_name"]
            for imp in analysis["imports"]:
                if (imp["type"] == "from_import" and imp["module"]) or imp[
                    "type"
                ] == "import":
                    self.dependency_graph[module_name].add(imp["module"])

        print("\n🔍 Checking for broken imports...")
        for file_path, analysis in self.modules.items():
            for imp in analysis["imports"]:
                module_to_check = imp["module"] if imp["module"] else imp["name"]
                if module_to_check and not self.check_import_exists(module_to_check):
                    self.broken_imports[module_to_check].append(
                        {
                            "file": file_path,
                            "line": imp["line"],
                            "import_type": imp["type"],
                        }
                    )

        print("\n🔄 Detecting circular dependencies...")
        self.circular_deps = self.detect_circular_dependencies()

    def generate_report(self) -> str:
        """Generate comprehensive import analysis report."""
        report = []
        report.append("# PowerRebuilder Codebase Import Analysis")
        report.append("=" * 50)

        # Summary
        report.append("\n## Summary")
        report.append(f"- Total Python files analyzed: {len(self.modules)}")
        report.append(f"- Broken imports found: {len(self.broken_imports)}")
        report.append(f"- Circular dependencies found: {len(self.circular_deps)}")

        # Module breakdown
        report.append("\n## Module Breakdown")

        modules = defaultdict(list)
        for file_path, analysis in self.modules.items():
            if "src/" in file_path:
                module_dir = file_path.split("src/")[1].split("/")[0]
                modules[module_dir].append(analysis)

        for module_name, files in sorted(modules.items()):
            report.append(f"\n### {module_name.upper()} Module")
            report.append(f"- Files: {len(files)}")

            # Count imports per module
            import_counts = defaultdict(int)
            for file_analysis in files:
                for imp in file_analysis["imports"]:
                    if imp["module"]:
                        root_module = imp["module"].split(".")[0]
                        import_counts[root_module] += 1

            if import_counts:
                report.append("- Top imported modules:")
                for mod, count in sorted(
                    import_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    report.append(f"  - {mod}: {count} imports")

        # Broken imports detail
        if self.broken_imports:
            report.append(f"\n## 🚨 BROKEN IMPORTS ({len(self.broken_imports)} issues)")
            for broken_module, occurrences in sorted(self.broken_imports.items()):
                report.append(
                    f"\n### `{broken_module}` (used in {len(occurrences)} files)"
                )
                for occ in occurrences[:10]:  # Limit to first 10
                    file_path = occ["file"].replace(
                        "/Users/michael/Projects/powerrebuilder/", ""
                    )
                    report.append(
                        f"- `{file_path}:{occ['line']}` ({occ['import_type']})"
                    )
                if len(occurrences) > 10:
                    report.append(f"- ... and {len(occurrences) - 10} more files")

        # Circular dependencies
        if self.circular_deps:
            report.append(
                f"\n## 🔄 CIRCULAR DEPENDENCIES ({len(self.circular_deps)} cycles)"
            )
            for i, cycle in enumerate(self.circular_deps, 1):
                report.append(f"\n### Cycle {i}")
                for j, module in enumerate(cycle):
                    if j == len(cycle) - 1:
                        report.append(f"  {module} → {cycle[0]}")
                    else:
                        report.append(f"  {module} → {cycle[j + 1]}")

        # Dependency graph for major modules
        report.append("\n## 📊 Major Module Dependencies")

        major_modules = ["extract", "decompile", "parse", "model", "generate"]
        for module in major_modules:
            deps = set()
            for node, neighbors in self.dependency_graph.items():
                if f"src.{module}" in node:
                    for neighbor in neighbors:
                        if neighbor.startswith("src.") and not neighbor.startswith(
                            f"src.{module}"
                        ):
                            deps.add(neighbor.split(".")[1])

            if deps:
                report.append(f"\n### {module.upper()} depends on:")
                for dep in sorted(deps):
                    report.append(f"- {dep}")

        return "\n".join(report)


def main():
    analyzer = ImportAnalyzer()
    analyzer.analyze_all()

    report = analyzer.generate_report()
    print(report)

    # Also save to file
    with open("import_analysis_report.md", "w") as f:
        f.write(report)

    print("\n💾 Report saved to 'import_analysis_report.md'")


if __name__ == "__main__":
    main()
