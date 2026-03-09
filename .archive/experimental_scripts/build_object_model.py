#!/usr/bin/env python3
"""
Build object model from extracted PBD metadata.
Creates structured representation of the PowerBuilder system.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import sys


@dataclass
class PBControl:
    """PowerBuilder UI control."""

    name: str
    type: str
    parent: Optional[str] = None
    properties: Dict[str, any] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)


@dataclass
class PBWindow:
    """PowerBuilder window definition."""

    name: str
    controls: List[PBControl] = field(default_factory=list)
    datawindows: List[str] = field(default_factory=list)
    menus: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)

    def add_control(self, control: PBControl):
        """Add control to window."""
        self.controls.append(control)
        if control.type == "datawindow" or control.type == "datawindow_control":
            self.datawindows.append(control.name)


@dataclass
class PBBusinessObject:
    """PowerBuilder business/nonvisual object."""

    name: str
    type: str
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    sql_operations: List[str] = field(default_factory=list)


@dataclass
class PBModule:
    """PowerBuilder module (from PBD file)."""

    name: str
    windows: Dict[str, PBWindow] = field(default_factory=dict)
    business_objects: Dict[str, PBBusinessObject] = field(default_factory=dict)
    datawindows: List[str] = field(default_factory=list)
    database_objects: List[str] = field(default_factory=list)

    def add_window(self, window: PBWindow):
        """Add window to module."""
        self.windows[window.name] = window

    def add_business_object(self, obj: PBBusinessObject):
        """Add business object to module."""
        self.business_objects[obj.name] = obj


@dataclass
class DentalClinicSystem:
    """Complete dental clinic system model."""

    modules: Dict[str, PBModule] = field(default_factory=dict)
    total_windows: int = 0
    total_business_objects: int = 0
    total_datawindows: int = 0
    dependencies: Set[str] = field(default_factory=set)

    def add_module(self, module: PBModule):
        """Add module to system."""
        self.modules[module.name] = module
        self.total_windows += len(module.windows)
        self.total_business_objects += len(module.business_objects)
        self.total_datawindows += len(module.datawindows)


class ObjectModelBuilder:
    """Build structured object model from metadata."""

    def __init__(self, metadata_dir: Path):
        """Initialize with metadata directory.

        Args:
            metadata_dir: Directory containing metadata JSON files
        """
        self.metadata_dir = Path(metadata_dir)
        self.system = DentalClinicSystem()

    def build(self) -> DentalClinicSystem:
        """Build complete system model.

        Returns:
            Complete dental clinic system model
        """
        # Process each metadata file
        for json_file in self.metadata_dir.glob("*.json"):
            module = self._process_metadata_file(json_file)
            if module:
                self.system.add_module(module)

        self._analyze_relationships()
        return self.system

    def _process_metadata_file(self, json_file: Path) -> Optional[PBModule]:
        """Process single metadata file.

        Args:
            json_file: Path to metadata JSON

        Returns:
            Module object or None
        """
        try:
            with open(json_file, "r") as f:
                metadata = json.load(f)

            module_name = json_file.stem
            module = PBModule(name=module_name)

            # Process objects
            for obj in metadata.get("objects", []):
                obj_type = obj["type"]
                obj_name = obj["name"]

                # Windows
                if obj_type == "window":
                    window = PBWindow(name=obj_name)
                    module.add_window(window)

                # Business objects
                elif obj_type in ["nonvisual_object", "user_object", "class"]:
                    business_obj = PBBusinessObject(name=obj_name, type=obj_type)
                    module.add_business_object(business_obj)

                # DataWindows
                elif obj_type == "datawindow":
                    module.datawindows.append(obj_name)

                # Controls - associate with windows
                elif obj_type in [
                    "commandbutton",
                    "datawindow_control",
                    "checkbox",
                    "listbox",
                    "statictext",
                    "groupbox",
                ]:
                    control = PBControl(name=obj_name, type=obj_type)
                    # Add to most recent window or create default
                    if module.windows:
                        last_window = list(module.windows.values())[-1]
                        last_window.add_control(control)

            # Add database objects
            module.database_objects = metadata.get("database_objects", [])

            # Add dependencies
            for dep in metadata.get("dependencies", []):
                self.system.dependencies.add(dep)

            return module

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            return None

    def _analyze_relationships(self):
        """Analyze relationships between objects."""
        # Map window-datawindow relationships
        for module in self.system.modules.values():
            for window in module.windows.values():
                # Find datawindows used by this window
                for dw_name in module.datawindows:
                    # Simple heuristic: if names are similar
                    if window.name.replace("w_", "") in dw_name:
                        window.datawindows.append(dw_name)

    def generate_report(self) -> Dict:
        """Generate analysis report.

        Returns:
            Report dictionary
        """
        report = {
            "system_overview": {
                "total_modules": len(self.system.modules),
                "total_windows": self.system.total_windows,
                "total_business_objects": self.system.total_business_objects,
                "total_datawindows": self.system.total_datawindows,
                "dependencies": list(self.system.dependencies),
            },
            "modules": {},
        }

        for module_name, module in self.system.modules.items():
            report["modules"][module_name] = {
                "windows": len(module.windows),
                "business_objects": len(module.business_objects),
                "datawindows": len(module.datawindows),
                "database_operations": len(module.database_objects),
                "window_list": list(module.windows.keys())[:10],  # First 10
                "business_object_list": list(module.business_objects.keys())[:10],
            }

        return report

    def export_for_flutter(self) -> Dict:
        """Export model for Flutter generation.

        Returns:
            Flutter-ready model
        """
        flutter_model = {
            "screens": [],
            "widgets": [],
            "data_models": [],
            "navigation": [],
        }

        for module in self.system.modules.values():
            for window_name, window in module.windows.items():
                screen = {
                    "name": self._to_flutter_name(window_name),
                    "original_name": window_name,
                    "widgets": [],
                }

                for control in window.controls:
                    widget = {
                        "type": self._map_control_to_widget(control.type),
                        "name": self._to_flutter_name(control.name),
                        "original_name": control.name,
                    }
                    screen["widgets"].append(widget)

                flutter_model["screens"].append(screen)

        return flutter_model

    def export_for_python(self) -> Dict:
        """Export model for Python/Litestar generation.

        Returns:
            Python-ready model
        """
        python_model = {
            "services": [],
            "models": [],
            "repositories": [],
            "api_endpoints": [],
        }

        for module in self.system.modules.values():
            for obj_name, obj in module.business_objects.items():
                if "n_cst" in obj_name or "service" in obj_name.lower():
                    # This is a service
                    service = {
                        "name": self._to_python_name(obj_name),
                        "original_name": obj_name,
                        "methods": obj.methods,
                        "module": module.name,
                    }
                    python_model["services"].append(service)

                elif "data" in obj_name.lower() or "repository" in obj_name.lower():
                    # This is a repository
                    repo = {
                        "name": self._to_python_name(obj_name),
                        "original_name": obj_name,
                        "module": module.name,
                    }
                    python_model["repositories"].append(repo)

        # Create API endpoints from windows (they represent UI operations)
        for module in self.system.modules.values():
            for window_name in module.windows.keys():
                if "patient" in window_name.lower():
                    endpoint = {
                        "path": "/api/patients",
                        "operations": ["GET", "POST", "PUT", "DELETE"],
                        "window": window_name,
                    }
                    python_model["api_endpoints"].append(endpoint)

        return python_model

    def _to_flutter_name(self, pb_name: str) -> str:
        """Convert PowerBuilder name to Flutter convention.

        Args:
            pb_name: PowerBuilder name

        Returns:
            Flutter-style name
        """
        # Remove prefixes
        name = pb_name
        for prefix in ["w_", "cb_", "dw_", "st_", "lb_"]:
            if name.startswith(prefix):
                name = name[len(prefix) :]
                break

        # Convert to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def _to_python_name(self, pb_name: str) -> str:
        """Convert PowerBuilder name to Python convention.

        Args:
            pb_name: PowerBuilder name

        Returns:
            Python-style name
        """
        # Remove prefixes
        name = pb_name
        for prefix in ["n_cst_", "n_", "u_"]:
            if name.startswith(prefix):
                name = name[len(prefix) :]
                break

        # Already in snake_case mostly
        return name.lower()

    def _map_control_to_widget(self, control_type: str) -> str:
        """Map PowerBuilder control to Flutter widget.

        Args:
            control_type: PowerBuilder control type

        Returns:
            Flutter widget type
        """
        mapping = {
            "commandbutton": "ElevatedButton",
            "datawindow": "DataTable",
            "datawindow_control": "DataTable",
            "statictext": "Text",
            "singlelineedit": "TextField",
            "multilineedit": "TextField",
            "checkbox": "Checkbox",
            "radiobutton": "Radio",
            "listbox": "ListView",
            "dropdownlistbox": "DropdownButton",
            "groupbox": "Container",
            "tab": "TabBar",
            "treeview": "TreeView",
            "picture": "Image",
        }
        return mapping.get(control_type, "Container")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: build_object_model.py <metadata_dir> [output_dir]")
        sys.exit(1)

    metadata_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/object_model")

    if not metadata_dir.exists():
        print(f"Metadata directory not found: {metadata_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build object model
    builder = ObjectModelBuilder(metadata_dir)
    system = builder.build()

    # Generate report
    report = builder.generate_report()

    print("\n" + "=" * 60)
    print("Dental Clinic System Object Model")
    print("=" * 60)
    print(f"Total Modules: {report['system_overview']['total_modules']}")
    print(f"Total Windows: {report['system_overview']['total_windows']}")
    print(
        f"Total Business Objects: {report['system_overview']['total_business_objects']}"
    )
    print(f"Total DataWindows: {report['system_overview']['total_datawindows']}")

    print("\nDependencies:")
    for dep in report["system_overview"]["dependencies"]:
        print(f"  - {dep}")

    print("\nModule Summary:")
    for module_name, module_info in report["modules"].items():
        print(f"\n  {module_name}:")
        print(f"    Windows: {module_info['windows']}")
        print(f"    Business Objects: {module_info['business_objects']}")
        print(f"    DataWindows: {module_info['datawindows']}")

    # Export models
    flutter_model = builder.export_for_flutter()
    python_model = builder.export_for_python()

    # Save exports
    flutter_file = output_dir / "flutter_model.json"
    with open(flutter_file, "w") as f:
        json.dump(flutter_model, f, indent=2)
    print(f"\nFlutter model saved to: {flutter_file}")

    python_file = output_dir / "python_model.json"
    with open(python_file, "w") as f:
        json.dump(python_model, f, indent=2)
    print(f"Python model saved to: {python_file}")

    # Save complete report
    report_file = output_dir / "system_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Complete report saved to: {report_file}")


if __name__ == "__main__":
    main()
