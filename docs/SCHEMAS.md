# Schema Documentation

## Overview

This document describes the data schemas used throughout PowerRebuilder, including file formats, internal data structures, and database schemas.

## Binary File Formats

### PBL/PBD Header Structure

```cue
PBLHeader: {
    signature: bytes & =~"^HDR\\*"  // 4 bytes: "HDR*"
    version: uint32                  // Format version
    encoding: "ASCII" | "Unicode"    // Determined by version
    entryCount: uint32              // Number of entries
    nodeOffset: uint32              // Offset to first NOD block
    timestamp: uint32               // Creation timestamp
}
```

### Node Block (NOD) Structure

```cue
NodeBlock: {
    signature: bytes & =~"^NOD\\*"  // 4 bytes: "NOD*"
    nextOffset: uint32              // Offset to next NOD block
    entryCount: uint16              // Entries in this block
    entries: [...Entry]             // Entry definitions
}

Entry: {
    name: string & =~"^[a-zA-Z_][a-zA-Z0-9_]*$"
    type: EntryType
    size: uint32
    dataOffset: uint32
    timestamp: uint32
    flags: uint16
}

EntryType: "window" | "function" | "datawindow" | "menu" | "application" | "userobject" | "structure"
```

### Data Block (DAT) Structure

```cue
DataBlock: {
    signature: bytes & =~"^DAT\\*"  // 4 bytes: "DAT*"
    nextOffset: uint32              // Offset to next DAT block
    dataLength: uint16              // Length of data
    data: bytes                     // Actual file content
}
```

## AST Schema

### Base Node Structure

```cue
ASTNode: {
    type: string                    // Node type identifier
    location?: SourceLocation       // Source position
    children?: [...ASTNode]         // Child nodes
}

SourceLocation: {
    file: string
    line: number & >=1
    column: number & >=1
    endLine?: number & >=1
    endColumn?: number & >=1
}
```

### Window Definition

```cue
WindowNode: ASTNode & {
    type: "Window"
    name: string & =~"^w_[a-zA-Z0-9_]+$"
    title: string
    windowType: "main" | "child" | "popup" | "response"
    controls: [...ControlNode]
    events: [...EventNode]
    functions: [...FunctionNode]
    instanceVariables: [...VariableNode]
}

ControlNode: ASTNode & {
    type: "Control"
    controlType: ControlType
    name: string
    properties: {[string]: _}
    events: [...EventNode]
}

ControlType: "CommandButton" | "DataWindow" | "EditMask" | "StaticText" |
             "CheckBox" | "RadioButton" | "ListBox" | "DropDownListBox" |
             "Picture" | "GroupBox" | "Line" | "Rectangle"
```

### Function Definition

```cue
FunctionNode: ASTNode & {
    type: "Function"
    name: string & =~"^[a-zA-Z_][a-zA-Z0-9_]*$"
    returnType: DataType
    parameters: [...ParameterNode]
    body: [...StatementNode]
    access: AccessModifier
    scope: "global" | "local" | "instance"
}

ParameterNode: {
    name: string
    dataType: DataType
    passBy: "value" | "reference"
    optional: bool | *false
    defaultValue?: string
}

AccessModifier: "public" | "private" | "protected"
```

### Data Types

```cue
DataType: PrimitiveType | ObjectType | ArrayType

PrimitiveType: "integer" | "long" | "decimal" | "real" | "double" |
               "string" | "char" | "boolean" | "date" | "time" | "datetime" |
               "blob" | "any"

ObjectType: {
    type: "object"
    className: string
}

ArrayType: {
    type: "array"
    elementType: DataType
    dimensions?: [...number]
    bounded: bool | *true
}
```

## Database Schema

### Table Definitions

```cue
TableSchema: {
    name: string & =~"^[a-zA-Z_][a-zA-Z0-9_]*$"
    columns: [...ColumnSchema]
    primaryKey?: [...string]
    foreignKeys?: [...ForeignKeySchema]
    indexes?: [...IndexSchema]
}

ColumnSchema: {
    name: string & =~"^[a-zA-Z_][a-zA-Z0-9_]*$"
    dataType: SQLDataType
    nullable: bool | *true
    defaultValue?: string
    autoIncrement?: bool | *false
    comment?: string
}

SQLDataType: {
    type: "VARCHAR" | "INTEGER" | "DECIMAL" | "DATE" | "TIMESTAMP" |
          "BOOLEAN" | "TEXT" | "BLOB"
    length?: number
    precision?: number
    scale?: number
}

ForeignKeySchema: {
    name?: string
    columns: [...string]
    referencedTable: string
    referencedColumns: [...string]
    onDelete?: "CASCADE" | "SET NULL" | "RESTRICT" | "NO ACTION"
    onUpdate?: "CASCADE" | "SET NULL" | "RESTRICT" | "NO ACTION"
}
```

### DataWindow Schema

```cue
DataWindowSchema: {
    name: string
    dataObject: string
    presentation: PresentationStyle
    dataSource: DataSourceSchema
    columns: [...DataWindowColumn]
    retrieveArguments?: [...ArgumentSchema]
}

PresentationStyle: "grid" | "freeform" | "tabular" | "group" | "crosstab" | "graph"

DataSourceSchema: {
    type: "sql" | "stored_procedure" | "external"
    sql?: string
    procedure?: string
    tables?: [...string]
}

DataWindowColumn: {
    name: string
    dbName: string
    dataType: DataType
    displayFormat?: string
    editMask?: string
    validation?: string
    visible: bool | *true
}
```

## Model Schema

### Application Model

```cue
ApplicationModel: {
    name: string
    version: string
    libraries: [...LibraryModel]
    globalFunctions: [...FunctionModel]
    globalVariables: [...VariableModel]
    systemFunctions: [...string]
}

LibraryModel: {
    name: string
    path: string
    objects: [...ObjectModel]
    dependencies: [...string]
}

ObjectModel: {
    type: ObjectType
    name: string
    parent?: string
    properties: {[string]: _}
    methods: [...MethodModel]
    events: [...EventModel]
}

ObjectType: "window" | "userobject" | "menu" | "datawindow" |
            "application" | "function" | "structure"
```

### Event Model

```cue
EventModel: {
    name: string
    objectName: string
    eventType: string
    parameters: [...ParameterModel]
    returnType?: DataType
    body: [...Statement]
    mappedTo?: string  // System event mapping
}

ParameterModel: {
    name: string
    type: DataType
    direction: "in" | "out" | "inout"
}
```

## Generated Code Schema

### Flutter Widget Schema

```cue
FlutterWidget: {
    name: string & =~"^[A-Z][a-zA-Z0-9]*$"
    type: "StatelessWidget" | "StatefulWidget"
    properties: [...PropertyDef]
    methods: [...MethodDef]
    state?: StateModel
}

PropertyDef: {
    name: string
    type: string  // Dart type
    modifier: "final" | "const" | "var" | "late"
    initialValue?: string
}

StateModel: {
    properties: [...PropertyDef]
    initState?: string
    dispose?: string
}
```

### Python Service Schema

```cue
PythonService: {
    name: string & =~"^[A-Z][a-zA-Z0-9]*Service$"
    imports: [...ImportDef]
    dependencies: [...string]
    methods: [...ServiceMethod]
}

ServiceMethod: {
    name: string & =~"^[a-z_][a-z0-9_]*$"
    async: bool | *false
    parameters: [...ParameterDef]
    returnType: string
    decorators?: [...string]
    body: string
}

ImportDef: {
    module: string
    items?: [...string]
    alias?: string
}
```

## Configuration Schema

### Pipeline Configuration

```cue
PipelineConfig: {
    stages: {
        extract: ExtractConfig
        parse: ParseConfig
        decompile: DecompileConfig
        generate: GenerateConfig
    }
    parallel: bool | *true
    streaming: bool | *true
    cache: CacheConfig
}

ExtractConfig: {
    byteRecovery: bool | *false
    encoding: "auto" | "ascii" | "unicode" | *"auto"
    resourceExtraction: bool | *true
    maxFileSize?: number
}

ParseConfig: {
    errorRecovery: bool | *true
    maxErrors: number | *100
    parserType: "lalr" | "earley" | *"lalr"
    preprocessor: bool | *true
}

CacheConfig: {
    enabled: bool | *true
    maxSize: number | *1000
    maxMemory: number | *536870912  // 512MB
    ttl?: number  // seconds
}
```

### Security Configuration

```cue
SecurityConfig: {
    pathValidation: bool | *true
    sanitizeFilenames: bool | *true
    maxPathDepth: number | *10
    allowedExtensions: [...string] | *[".pbl", ".pbd"]
    resourceLimits: ResourceLimits
}

ResourceLimits: {
    maxFileSize: number | *104857600      // 100MB
    maxMemoryUsage: number | *2147483648  // 2GB
    maxCpuPercent: number | *80
    maxOpenFiles: number | *100
    maxExtractionTime: number | *3600     // 1 hour
}
```

## Validation Rules

### File Name Validation

```cue
ValidFileName: string & =~"^[a-zA-Z0-9_\\-\\.]+$" & !~"\\.\\./"

ValidPath: string & {
    // No path traversal
    !~"\\.\\./"
    // No absolute paths in user input
    !~"^/"
    // No special characters
    !~"[<>:\"|?*]"
}
```

### Type Validation

```cue
ValidIdentifier: string & =~"^[a-zA-Z_][a-zA-Z0-9_]*$" & len<=255

ValidSQLIdentifier: string & =~"^[a-zA-Z_][a-zA-Z0-9_]*$" & len<=64

ValidDartIdentifier: string & =~"^[a-zA-Z_\\$][a-zA-Z0-9_\\$]*$" & len<=255
```

---

*Last updated: 2025-07-14*
