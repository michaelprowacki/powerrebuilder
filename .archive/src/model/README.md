# Model Module

## Overview

The Model module provides the Abstract Syntax Tree (AST) representation for PowerBuilder code. It defines the core data structures that represent PowerBuilder constructs and provides utilities for AST manipulation, analysis, and transformation.

## Structure

```
model/
├── __init__.py
├── core/                    # Core AST node definitions
│   ├── __init__.py
│   ├── application.py       # Application-level nodes
│   ├── attributes.py        # Attribute/property nodes
│   ├── blocks.py           # Block statements
│   ├── classes.py          # Class definitions
│   ├── constants.py        # Constant values
│   ├── controls.py         # UI control definitions
│   ├── datawindow.py       # DataWindow structures
│   ├── enums.py            # Enumeration types
│   ├── events.py           # Event definitions
│   ├── expressions.py      # Expression nodes
│   ├── functions.py        # Function definitions
│   ├── literals.py         # Literal values
│   ├── loops.py            # Loop constructs
│   ├── menus.py            # Menu definitions
│   ├── operations.py       # Operations/operators
│   ├── sql.py              # SQL-related nodes
│   ├── statements.py       # Statement nodes
│   ├── types.py            # Type definitions
│   ├── userdata.py         # User-defined data
│   ├── variables.py        # Variable declarations
│   └── windows.py          # Window definitions
├── relationships/           # Object relationships
│   ├── __init__.py
│   ├── cross_module_resolver.py
│   └── dependency_analyzer.py
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── base.py             # Base classes
│   ├── errors.py           # Error definitions
│   ├── mixins.py           # Shared mixins
│   ├── node_factory.py     # Node creation
│   ├── symbol_table.py     # Symbol management
│   ├── traversal.py        # AST traversal
│   └── validators.py       # AST validation
└── visitors/               # AST visitors
    ├── __init__.py
    ├── analyzer.py         # Code analysis
    ├── code_generator.py   # Code generation
    ├── security_analyzer.py # Security analysis
    ├── traverser.py        # Tree traversal
    └── type_resolver.py    # Type resolution
```

## Key Components

### Core AST Nodes

The core package contains all AST node definitions:

- **Base Nodes**: ASTNode, Statement, Expression
- **Declarations**: Variable, Function, Class, Event
- **Control Flow**: If, For, While, Choose
- **Expressions**: Binary, Unary, Call, Access
- **Types**: BasicType, ArrayType, CustomType
- **UI Elements**: Window, Control, Menu, DataWindow

### Node Features

All AST nodes include:
- Source position tracking
- Parent-child relationships
- Visitor pattern support
- Validation capabilities
- Pretty-printing support

### Utilities

- **Symbol Table**: Manages variable and function scopes
- **Node Factory**: Creates AST nodes with validation
- **Traversal**: Utilities for walking the AST
- **Validators**: Ensures AST correctness

## Usage

```python
from model.core import Function, Variable, Return
from model.utils import SymbolTable

# Create a function
func = Function(
    name="calculate",
    return_type="integer",
    parameters=[
        Variable(name="a", type="integer"),
        Variable(name="b", type="integer")
    ],
    body=[
        Return(value=BinaryOp(
            left=Identifier("a"),
            operator="+",
            right=Identifier("b")
        ))
    ]
)

# Analyze with visitor
from model.visitors import CodeAnalyzer
analyzer = CodeAnalyzer()
analyzer.visit(func)
```

## AST Node Hierarchy

```
ASTNode
├── Statement
│   ├── Declaration
│   │   ├── Variable
│   │   ├── Function
│   │   └── Class
│   ├── ControlFlow
│   │   ├── If
│   │   ├── For
│   │   └── While
│   └── Assignment
├── Expression
│   ├── Literal
│   ├── Identifier
│   ├── BinaryOp
│   ├── UnaryOp
│   └── Call
└── Type
    ├── BasicType
    ├── ArrayType
    └── CustomType
```

## Visitors

The module uses the visitor pattern for AST traversal:

- **Analyzer**: Performs code analysis
- **TypeResolver**: Resolves variable and expression types
- **SecurityAnalyzer**: Identifies security issues
- **CodeGenerator**: Generates code from AST

## Relationships

The relationships package handles:
- Cross-module dependencies
- Inheritance hierarchies
- Event wiring
- Variable scoping

## Validation

The module includes comprehensive validation:
- Type checking
- Scope validation
- Reference resolution
- Syntax validation

## Dependencies

- Python 3.9+
- typing_extensions (for advanced type hints)

## Related Modules

- **Parse**: Creates AST from source code
- **Decompile**: Enhances AST with decompiled info
- **Generate**: Converts AST to target language
