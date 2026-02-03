#!/usr/bin/env python3
"""
Extract metadata and object definitions from PBD files.
Separates metadata from P-code for proper processing.
"""

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class PBObject:
    """PowerBuilder object extracted from PBD."""

    name: str
    type: str
    properties: Dict[str, str]
    methods: List[str]
    dependencies: List[str]


class PBDMetadataExtractor:
    """Extract metadata and object definitions from PBD files."""

    def __init__(self, pbd_file: Path):
        """Initialize with PBD file.

        Args:
            pbd_file: Path to PBD file
        """
        self.pbd_file = pbd_file
        self.objects = []
        self.strings = set()
        self.metadata = {}

    def extract(self) -> Dict:
        """Extract all metadata from PBD.

        Returns:
            Dictionary with extracted metadata
        """
        with open(self.pbd_file, "rb") as f:
            data = f.read()

        # Extract all strings first
        self.strings = self._extract_strings(data)

        # Identify PowerBuilder objects
        self.objects = self._identify_objects()

        # Build metadata structure
        self.metadata = {
            "file": self.pbd_file.name,
            "size": len(data),
            "objects": [asdict(obj) for obj in self.objects],
            "total_objects": len(self.objects),
            "object_types": self._get_object_types(),
            "dependencies": self._get_dependencies(),
            "database_objects": self._find_database_objects(),
            "ui_controls": self._find_ui_controls(),
            "business_logic": self._find_business_logic(),
        }

        return self.metadata

    def _extract_strings(self, data: bytes) -> Set[str]:
        """Extract all strings from binary data.

        Args:
            data: Binary data

        Returns:
            Set of unique strings
        """
        strings = set()

        # UTF-16LE strings (PowerBuilder default)
        i = 0
        while i < len(data) - 1:
            if data[i + 1] == 0 and 32 <= data[i] <= 126:
                s = []
                while i < len(data) - 1 and data[i + 1] == 0 and 32 <= data[i] <= 126:
                    s.append(chr(data[i]))
                    i += 2
                if len(s) >= 3:
                    strings.add("".join(s))
            else:
                i += 1

        # ASCII strings
        i = 0
        while i < len(data):
            if 32 <= data[i] <= 126:
                s = []
                while i < len(data) and 32 <= data[i] <= 126:
                    s.append(chr(data[i]))
                    i += 1
                if len(s) >= 4:
                    strings.add("".join(s))
            else:
                i += 1

        return strings

    def _identify_objects(self) -> List[PBObject]:
        """Identify PowerBuilder objects from strings.

        Returns:
            List of identified objects
        """
        objects = []

        # PowerBuilder naming patterns
        pb_prefixes = {
            "w_": "window",
            "d_": "datawindow",
            "u_": "user_object",
            "n_": "nonvisual_object",
            "m_": "menu",
            "f_": "function",
            "str_": "structure",
            "q_": "query",
            "p_": "pipeline",
            "uo_": "user_object",
            "dw_": "datawindow_control",
            "cb_": "commandbutton",
            "rb_": "radiobutton",
            "cbx_": "checkbox",
            "ddlb_": "dropdownlistbox",
            "lb_": "listbox",
            "sle_": "singlelineedit",
            "mle_": "multilineedit",
            "st_": "statictext",
            "gb_": "groupbox",
            "ln_": "line",
            "r_": "rectangle",
            "ov_": "oval",
            "rr_": "roundrectangle",
            "p_": "picture",
            "tv_": "treeview",
            "lv_": "listview",
            "tab_": "tab",
            "uo_": "userobject",
        }

        # Find objects by prefix
        for s in self.strings:
            s_lower = s.lower()
            for prefix, obj_type in pb_prefixes.items():
                if s_lower.startswith(prefix):
                    obj = PBObject(
                        name=s,
                        type=obj_type,
                        properties={},
                        methods=[],
                        dependencies=[],
                    )
                    objects.append(obj)
                    break

        # Find classes and structures
        class_keywords = [
            "mailsession",
            "mailrecipient",
            "mailmessage",
            "environment",
            "connection",
            "transaction",
            "datastore",
            "datawindowchild",
        ]

        for keyword in class_keywords:
            matching = [s for s in self.strings if keyword in s.lower()]
            for match in matching:
                obj = PBObject(
                    name=match, type="class", properties={}, methods=[], dependencies=[]
                )
                objects.append(obj)

        # Find methods and events
        method_patterns = [
            "create",
            "destroy",
            "clicked",
            "open",
            "close",
            "retrieve",
            "update",
            "delete",
            "insert",
            "save",
        ]

        for pattern in method_patterns:
            matching = [s for s in self.strings if pattern in s.lower() and "(" in s]
            for match in matching:
                # These are likely method definitions
                if not any(obj.name == match for obj in objects):
                    obj = PBObject(
                        name=match,
                        type="method",
                        properties={},
                        methods=[],
                        dependencies=[],
                    )
                    objects.append(obj)

        return objects

    def _get_object_types(self) -> Dict[str, int]:
        """Count objects by type.

        Returns:
            Dictionary of type counts
        """
        types = {}
        for obj in self.objects:
            types[obj.type] = types.get(obj.type, 0) + 1
        return types

    def _get_dependencies(self) -> List[str]:
        """Extract dependency information.

        Returns:
            List of identified dependencies
        """
        deps = []

        # Look for import/include patterns
        for s in self.strings:
            if "pfc" in s.lower():
                deps.append("PowerBuilder Foundation Classes (PFC)")
            if "pbni" in s.lower():
                deps.append("PowerBuilder Native Interface (PBNI)")
            if ".dll" in s.lower():
                deps.append(f"DLL: {s}")
            if "oracle" in s.lower() or "jdbc" in s.lower():
                deps.append("Database: Oracle/JDBC")

        return list(set(deps))

    def _find_database_objects(self) -> List[str]:
        """Find database-related objects.

        Returns:
            List of database objects
        """
        db_objects = []

        db_keywords = [
            "select",
            "insert",
            "update",
            "delete",
            "from",
            "where",
            "table",
            "column",
            "cursor",
            "procedure",
            "trigger",
        ]

        for s in self.strings:
            s_lower = s.lower()
            if any(kw in s_lower for kw in db_keywords):
                if len(s) > 10 and len(s) < 200:  # Reasonable SQL length
                    db_objects.append(s)

        return db_objects[:20]  # Limit to first 20

    def _find_ui_controls(self) -> List[str]:
        """Find UI control definitions.

        Returns:
            List of UI controls
        """
        ui_controls = []

        ui_types = [
            "button",
            "text",
            "edit",
            "list",
            "combo",
            "check",
            "radio",
            "tree",
            "grid",
            "tab",
            "menu",
            "window",
        ]

        for s in self.strings:
            s_lower = s.lower()
            if any(ui in s_lower for ui in ui_types):
                if len(s) < 100:  # Control names are usually short
                    ui_controls.append(s)

        return list(set(ui_controls))[:30]  # Limit to first 30

    def _find_business_logic(self) -> List[str]:
        """Find potential business logic.

        Returns:
            List of business logic indicators
        """
        logic = []

        # Business terms for dental clinic
        business_terms = [
            "patient",
            "appointment",
            "invoice",
            "payment",
            "treatment",
            "prescription",
            "insurance",
            "claim",
            "doctor",
            "dentist",
            "schedule",
            "billing",
        ]

        for s in self.strings:
            s_lower = s.lower()
            if any(term in s_lower for term in business_terms):
                if len(s) < 150:
                    logic.append(s)

        return list(set(logic))[:30]  # Limit to first 30


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: extract_metadata.py <pbd_file> [output.json]")
        sys.exit(1)

    pbd_file = Path(sys.argv[1])
    if not pbd_file.exists():
        print(f"File not found: {pbd_file}")
        sys.exit(1)

    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    # Extract metadata
    extractor = PBDMetadataExtractor(pbd_file)
    metadata = extractor.extract()

    # Display summary
    print(f"\n{'=' * 60}")
    print(f"Metadata Extraction: {metadata['file']}")
    print(f"{'=' * 60}")
    print(f"Total objects found: {metadata['total_objects']}")

    print("\nObject types:")
    for obj_type, count in metadata["object_types"].items():
        print(f"  {obj_type}: {count}")

    if metadata["dependencies"]:
        print("\nDependencies:")
        for dep in metadata["dependencies"]:
            print(f"  - {dep}")

    if metadata["database_objects"]:
        print(f"\nDatabase objects found: {len(metadata['database_objects'])}")
        for obj in metadata["database_objects"][:5]:
            print(f"  - {obj[:80]}")

    if metadata["ui_controls"]:
        print(f"\nUI controls found: {len(metadata['ui_controls'])}")
        for ctrl in metadata["ui_controls"][:10]:
            print(f"  - {ctrl}")

    if metadata["business_logic"]:
        print(f"\nBusiness logic elements: {len(metadata['business_logic'])}")
        for logic in metadata["business_logic"][:10]:
            print(f"  - {logic}")

    # Save to JSON if requested
    if output_file:
        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"\nMetadata saved to: {output_file}")


if __name__ == "__main__":
    main()
