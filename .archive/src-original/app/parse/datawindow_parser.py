"""Parse Domain - DataWindow Parsing.

Pure functions for parsing DataWindow definition files.
DataWindows are PowerBuilder's data presentation components.
Events track the parsing process for observability.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Union
from enum import Enum

from .shared import (
    ASTNode,
    NodeType,
    ParseResult,
    ParseSuccess,
    ParseFailed,
    SyntaxError,
)


# ============================================================================
# DATAWINDOW TYPES
# ============================================================================


class DataWindowType(str, Enum):
    """Types of DataWindow objects."""

    GRID = "grid"
    TABULAR = "tabular"
    FREEFORM = "freeform"
    LABEL = "label"
    GRAPH = "graph"
    CROSSTAB = "crosstab"
    COMPOSITE = "composite"
    NESTED = "nested"
    RICHTEXT = "richtext"


class DataWindowBand(str, Enum):
    """DataWindow band types."""

    HEADER = "header"
    DETAIL = "detail"
    FOOTER = "footer"
    SUMMARY = "summary"
    GROUP_HEADER = "group_header"
    GROUP_FOOTER = "group_footer"
    GROUP_TRAILER = "group_trailer"


@dataclass(frozen=True)
class DataWindowColumn:
    """A column definition in a DataWindow."""

    name: str
    datatype: str
    width: int
    label: Optional[str] = None
    format: Optional[str] = None
    validation: Optional[str] = None


@dataclass(frozen=True)
class DataWindowControl:
    """A control in the DataWindow layout."""

    name: str
    control_type: str  # text, column, computed field, etc.
    band: DataWindowBand
    x: int
    y: int
    width: int
    height: int
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DataWindowDefinition:
    """Complete DataWindow definition."""

    name: str
    type: DataWindowType
    sql: Optional[str]
    columns: List[DataWindowColumn]
    controls: List[DataWindowControl]
    bands: Dict[DataWindowBand, Dict[str, str]]  # Band properties
    properties: Dict[str, str]  # Global properties


# ============================================================================
# DATAWINDOW PARSING EVENTS
# ============================================================================


@dataclass(frozen=True)
class DataWindowParsed:
    """Event emitted when a DataWindow is successfully parsed."""

    name: str
    type: DataWindowType
    column_count: int
    control_count: int
    has_sql: bool


@dataclass(frozen=True)
class ColumnParsed:
    """Event emitted when a column is parsed."""

    column_name: str
    datatype: str
    has_validation: bool


@dataclass(frozen=True)
class ControlParsed:
    """Event emitted when a control is parsed."""

    control_name: str
    control_type: str
    band: DataWindowBand


@dataclass(frozen=True)
class SQLExtracted:
    """Event emitted when SQL is extracted from DataWindow."""

    table_count: int
    has_joins: bool
    has_where_clause: bool
    line_count: int


@dataclass(frozen=True)
class DataWindowWarning:
    """Event emitted when a parsing issue is detected."""

    component: str
    issue: str
    line: int


# Union type for all DataWindow events
DataWindowEvent = Union[
    DataWindowParsed, ColumnParsed, ControlParsed, SQLExtracted, DataWindowWarning
]


# ============================================================================
# DATAWINDOW PARSING FUNCTIONS
# ============================================================================


def parse_datawindow(source: str) -> Tuple[ParseResult, List[DataWindowEvent]]:
    """Parse DataWindow source to AST.

    Pure function: source -> (ParseResult, Events)
    Returns both AST and events for observability.
    """
    events = []

    if not source or not source.strip():
        events.append(
            DataWindowWarning(
                component="source", issue="Empty DataWindow source", line=1
            )
        )
        return ParseFailed(error="Empty DataWindow source", line=1, column=1), events

    try:
        # Parse DataWindow sections
        dw_def = parse_datawindow_definition(source)

        # Emit parsing events
        for column in dw_def.columns:
            events.append(
                ColumnParsed(
                    column_name=column.name,
                    datatype=column.datatype,
                    has_validation=column.validation is not None,
                )
            )

        for control in dw_def.controls:
            events.append(
                ControlParsed(
                    control_name=control.name,
                    control_type=control.control_type,
                    band=control.band,
                )
            )

        # Extract SQL if present
        if dw_def.sql:
            sql_info = analyze_sql(dw_def.sql)
            events.append(
                SQLExtracted(
                    table_count=sql_info["table_count"],
                    has_joins=sql_info["has_joins"],
                    has_where_clause=sql_info["has_where_clause"],
                    line_count=dw_def.sql.count("\n") + 1,
                )
            )

        # Emit main parsing event
        events.append(
            DataWindowParsed(
                name=dw_def.name,
                type=dw_def.type,
                column_count=len(dw_def.columns),
                control_count=len(dw_def.controls),
                has_sql=dw_def.sql is not None,
            )
        )

        # Convert to AST
        ast = datawindow_to_ast(dw_def)

        # Validate and collect warnings
        warnings = validate_datawindow(dw_def)
        for warning in warnings:
            events.append(
                DataWindowWarning(component="validation", issue=warning, line=0)
            )

        return ParseSuccess(
            ast=ast,
            warnings=warnings,
            tokens_processed=len(source.split()),  # Approximate
        ), events

    except SyntaxError as e:
        events.append(DataWindowWarning(component="parser", issue=str(e), line=e.line))
        return ParseFailed(error=e.message, line=e.line, column=e.column), events


def parse_datawindow_definition(source: str) -> DataWindowDefinition:
    """Parse DataWindow source into structured definition.

    Pure function extracting DataWindow structure.
    """
    lines = source.split("\n")

    # Parse header section
    name, dw_type = parse_header(lines)

    # Parse SQL section
    sql = extract_sql_section(lines)

    # Parse columns
    columns = parse_columns_section(lines)

    # Parse controls/objects
    controls = parse_controls_section(lines)

    # Parse band properties
    bands = parse_bands_section(lines)

    # Parse global properties
    properties = parse_properties_section(lines)

    return DataWindowDefinition(
        name=name,
        type=dw_type,
        sql=sql,
        columns=columns,
        controls=controls,
        bands=bands,
        properties=properties,
    )


def parse_header(lines: List[str]) -> Tuple[str, DataWindowType]:
    """Parse DataWindow header to extract name and type.

    Pure function: lines -> (name, type)
    """
    name = "datawindow"
    dw_type = DataWindowType.TABULAR

    for line in lines:
        # Look for release/header line
        if line.strip().startswith("release"):
            continue

        # Look for datawindow definition
        if "datawindow(" in line.lower():
            # Parse properties in parentheses
            props = extract_properties(line)
            name = props.get("name", name)

            # Determine type from processing or other properties
            processing = props.get("processing", "0")
            if processing == "1":
                dw_type = DataWindowType.GRID
            elif processing == "2":
                dw_type = DataWindowType.LABEL
            elif processing == "3":
                dw_type = DataWindowType.GRAPH
            elif processing == "4":
                dw_type = DataWindowType.CROSSTAB
            elif processing == "5":
                dw_type = DataWindowType.COMPOSITE
            else:
                dw_type = DataWindowType.TABULAR
            break

    return name, dw_type


def extract_sql_section(lines: List[str]) -> Optional[str]:
    """Extract SQL statement from DataWindow source.

    Pure function: lines -> SQL string or None
    """
    in_sql = False
    sql_lines = []

    for line in lines:
        if "retrieve=" in line.lower() or "table(column=" in line.lower():
            in_sql = True
            # Extract SQL from retrieve= property
            if "retrieve=" in line:
                sql_start = line.find('"', line.find("retrieve=")) + 1
                if sql_start > 0:
                    sql_lines.append(line[sql_start:])
            continue

        if in_sql:
            if '"' in line and not line.strip().startswith('"'):
                # End of SQL
                sql_end = line.find('"')
                if sql_end >= 0:
                    sql_lines.append(line[:sql_end])
                break
            else:
                sql_lines.append(line)

    if sql_lines:
        # Join and clean SQL
        sql = " ".join(sql_lines)
        sql = sql.replace("~n", "\n").replace("~t", "\t").replace("~~", "~")
        return sql.strip()

    return None


def parse_columns_section(lines: List[str]) -> List[DataWindowColumn]:
    """Parse column definitions from DataWindow.

    Pure function: lines -> list of columns
    """
    columns = []
    in_columns = False

    for line in lines:
        if "column(" in line.lower():
            in_columns = True
            props = extract_properties(line)

            column = DataWindowColumn(
                name=props.get("name", f"column_{len(columns)}"),
                datatype=props.get("type", "char"),
                width=int(props.get("width", "100")),
                label=props.get("label"),
                format=props.get("format"),
                validation=props.get("validation"),
            )
            columns.append(column)
        elif in_columns and ")" in line and "column" not in line.lower():
            in_columns = False

    return columns


def parse_controls_section(lines: List[str]) -> List[DataWindowControl]:
    """Parse control definitions from DataWindow.

    Pure function: lines -> list of controls
    """
    controls = []
    current_band = DataWindowBand.DETAIL

    for line in lines:
        # Track current band
        if "band(" in line.lower():
            band_props = extract_properties(line)
            band_type = band_props.get("type", "detail")
            current_band = map_band_type(band_type)

        # Parse controls
        control_types = [
            "text(",
            "column(",
            "compute(",
            "button(",
            "line(",
            "rectangle(",
        ]
        for ctrl_type in control_types:
            if ctrl_type in line.lower():
                props = extract_properties(line)
                control_name = ctrl_type[:-1]  # Remove '('

                control = DataWindowControl(
                    name=props.get("name", f"{control_name}_{len(controls)}"),
                    control_type=control_name,
                    band=current_band,
                    x=int(props.get("x", "0")),
                    y=int(props.get("y", "0")),
                    width=int(props.get("width", "100")),
                    height=int(props.get("height", "20")),
                    properties=props,
                )
                controls.append(control)
                break

    return controls


def parse_bands_section(lines: List[str]) -> Dict[DataWindowBand, Dict[str, str]]:
    """Parse band properties from DataWindow.

    Pure function: lines -> band properties dict
    """
    bands = {}

    for line in lines:
        if "header(" in line.lower():
            bands[DataWindowBand.HEADER] = extract_properties(line)
        elif "detail(" in line.lower():
            bands[DataWindowBand.DETAIL] = extract_properties(line)
        elif "footer(" in line.lower():
            bands[DataWindowBand.FOOTER] = extract_properties(line)
        elif "summary(" in line.lower():
            bands[DataWindowBand.SUMMARY] = extract_properties(line)

    return bands


def parse_properties_section(lines: List[str]) -> Dict[str, str]:
    """Parse global DataWindow properties.

    Pure function: lines -> properties dict
    """
    properties = {}

    for line in lines:
        if "datawindow(" in line.lower():
            properties.update(extract_properties(line))
        elif "print(" in line.lower():
            print_props = extract_properties(line)
            for key, value in print_props.items():
                properties[f"print.{key}"] = value

    return properties


def extract_properties(line: str) -> Dict[str, str]:
    """Extract properties from a DataWindow definition line.

    Pure function to parse property="value" pairs.
    """
    properties = {}

    # Simple regex-like parsing
    i = 0
    while i < len(line):
        # Find property name
        eq_pos = line.find("=", i)
        if eq_pos == -1:
            break

        # Extract property name
        prop_start = i
        for j in range(eq_pos - 1, -1, -1):
            if line[j] in " \t(":
                prop_start = j + 1
                break
        prop_name = line[prop_start:eq_pos].strip()

        # Extract value
        i = eq_pos + 1
        if i < len(line) and line[i] == '"':
            # Quoted value
            j = i + 1
            while j < len(line):
                if line[j] == '"' and (j == len(line) - 1 or line[j + 1] != '"'):
                    break
                if line[j] == '"' and j < len(line) - 1 and line[j + 1] == '"':
                    j += 1  # Skip escaped quote
                j += 1
            value = line[i + 1 : j].replace('""', '"')
            i = j + 1
        else:
            # Unquoted value
            j = i
            while j < len(line) and line[j] not in " \t)":
                j += 1
            value = line[i:j]
            i = j

        if prop_name:
            properties[prop_name.lower()] = value

    return properties


def map_band_type(band_str: str) -> DataWindowBand:
    """Map band type string to enum.

    Pure function: string -> DataWindowBand
    """
    mapping = {
        "header": DataWindowBand.HEADER,
        "detail": DataWindowBand.DETAIL,
        "footer": DataWindowBand.FOOTER,
        "summary": DataWindowBand.SUMMARY,
        "groupheader": DataWindowBand.GROUP_HEADER,
        "groupfooter": DataWindowBand.GROUP_FOOTER,
        "grouptrailer": DataWindowBand.GROUP_TRAILER,
    }
    return mapping.get(band_str.lower(), DataWindowBand.DETAIL)


def analyze_sql(sql: str) -> Dict[str, any]:
    """Analyze SQL statement for metrics.

    Pure function to extract SQL characteristics.
    """
    sql_upper = sql.upper()

    return {
        "table_count": sql_upper.count("FROM") + sql_upper.count("JOIN"),
        "has_joins": "JOIN" in sql_upper,
        "has_where_clause": "WHERE" in sql_upper,
        "has_order_by": "ORDER BY" in sql_upper,
        "has_group_by": "GROUP BY" in sql_upper,
    }


def datawindow_to_ast(dw_def: DataWindowDefinition) -> ASTNode:
    """Convert DataWindow definition to AST.

    Pure function: DataWindowDefinition -> ASTNode
    """
    children = []

    # Add SQL node if present
    if dw_def.sql:
        sql_node = ASTNode(
            type=NodeType.SQL_STATEMENT, value=dw_def.sql, metadata={"type": "select"}
        )
        children.append(sql_node)

    # Add column nodes
    for column in dw_def.columns:
        col_node = ASTNode(
            type=NodeType.COLUMN_DEF,
            value=column.name,
            metadata={
                "datatype": column.datatype,
                "width": column.width,
                "format": column.format,
                "validation": column.validation,
            },
        )
        children.append(col_node)

    # Add control nodes
    for control in dw_def.controls:
        ctrl_node = ASTNode(
            type=NodeType.CONTROL_DEF,
            value=control.name,
            metadata={
                "control_type": control.control_type,
                "band": control.band.value,
                "x": control.x,
                "y": control.y,
                "width": control.width,
                "height": control.height,
                **control.properties,
            },
        )
        children.append(ctrl_node)

    # Create DataWindow node
    return ASTNode(
        type=NodeType.DATAWINDOW,
        value=dw_def.name,
        children=tuple(children),
        metadata={"type": dw_def.type.value, **dw_def.properties},
    )


def validate_datawindow(dw_def: DataWindowDefinition) -> List[str]:
    """Validate DataWindow definition.

    Pure function to check for issues.
    """
    warnings = []

    # Check for missing SQL in non-external DataWindows
    if not dw_def.sql and dw_def.type not in [
        DataWindowType.COMPOSITE,
        DataWindowType.NESTED,
    ]:
        warnings.append("DataWindow has no SQL statement")

    # Check for columns without labels
    for column in dw_def.columns:
        if not column.label:
            warnings.append(f"Column {column.name} has no label")

    # Check for overlapping controls
    for i, ctrl1 in enumerate(dw_def.controls):
        for ctrl2 in dw_def.controls[i + 1 :]:
            if ctrl1.band == ctrl2.band:
                # Check for overlap
                if (
                    ctrl1.x < ctrl2.x + ctrl2.width
                    and ctrl1.x + ctrl1.width > ctrl2.x
                    and ctrl1.y < ctrl2.y + ctrl2.height
                    and ctrl1.y + ctrl1.height > ctrl2.y
                ):
                    warnings.append(
                        f"Controls {ctrl1.name} and {ctrl2.name} overlap in {ctrl1.band.value} band"
                    )

    # Check for missing detail band
    if (
        DataWindowBand.DETAIL not in dw_def.bands
        and dw_def.type != DataWindowType.COMPOSITE
    ):
        warnings.append("DataWindow missing detail band")

    return warnings
