# Visitor Pattern Implementation Guide

## Overview

The PowerRebuilder project has migrated from regex-based AST parsing to a robust visitor pattern implementation. This guide explains how to use the visitor pattern for AST traversal and information extraction.

## Why Visitor Pattern?

### Problems with Regex Approach

The old approach used regex patterns to parse string representations of AST:

```python
# Old regex-based approach (fragile)
event_matches = re.findall(
    r"Tree\(Token\('RULE', 'event_handler'\).*?Token\('IDENTIFIER', '(\w+)'\)",
    ast_str
)
```

Issues:
- Fragile string parsing
- Breaks with format changes
- Cannot handle nested structures properly
- Difficult to maintain and extend
- No type safety

### Visitor Pattern Benefits

- **Type-safe**: Works with structured AST nodes
- **Maintainable**: Clear separation of traversal and processing logic
- **Extensible**: Easy to add new node types and visitors
- **Robust**: Handles various AST formats (Lark trees, dictionaries, legacy)
- **Testable**: Each visitor can be unit tested independently

## Architecture

### Core Components

1. **ASTTreeVisitor** (`src/model/visitors/ast_tree_visitor.py`)
   - Base visitor that handles AST traversal
   - Supports multiple AST formats
   - Provides node type dispatching

2. **ModelExtractorVisitor** (`src/model/visitors/model_extractor_visitor.py`)
   - Extends ASTTreeVisitor
   - Extracts model information from AST
   - Builds structured data for code generation

3. **ASTWalker** (`src/model/visitors/ast_walker.py`)
   - Utility for traversing AST structures
   - Provides search and pattern matching
   - No string manipulation required

4. **PatternMatcher** (`src/model/visitors/ast_walker.py`)
   - Advanced pattern matching for AST nodes
   - Pre-defined PowerBuilder patterns
   - Extensible with custom patterns

## Usage Examples

### Basic Visitor Usage

```python
from src.model.visitors import ModelExtractorVisitor

# Create visitor
visitor = ModelExtractorVisitor()

# Extract model from AST
model = visitor.extract_model(ast, 'window', 'w_customer')

# Access extracted data
events = model['events']
methods = model['methods']
controls = model['controls']
```

### Finding Specific Nodes

```python
from src.model.visitors.ast_walker import ASTWalker

# Find all function declarations
functions = ASTWalker.find_by_type(ast, 'function_decl')

# Extract all identifiers
identifiers = ASTWalker.extract_identifiers(ast)

# Find nodes matching a predicate
public_functions = ASTWalker.find_by_predicate(
    ast,
    lambda n: is_function(n) and has_public_modifier(n)
)
```

### Pattern Matching

```python
from src.model.visitors.ast_walker import create_pb_pattern_matcher

# Create PowerBuilder pattern matcher
matcher = create_pb_pattern_matcher()

# Find all event handlers
event_handlers = matcher.find_all(ast, 'event_handler')

# Find window declarations
windows = matcher.find_all(ast, 'window_declaration')

# Find CREATE/DESTROY blocks
create_destroy = matcher.find_all(ast, 'create_destroy_block')
```

### Custom Visitors

```python
from src.model.visitors.ast_tree_visitor import ASTTreeVisitor

class MyCustomVisitor(ASTTreeVisitor):
    def __init__(self):
        super().__init__()
        self.functions = []

    def visit_function_declaration(self, node):
        """Custom handler for function declarations."""
        # Extract function information
        func_info = self._extract_function_info(node)
        self.functions.append(func_info)

        # Continue traversal
        return super().visit_function_declaration(node)
```

## AST Format Support

The visitor pattern supports multiple AST formats:

### 1. Lark Tree Objects

```python
from lark import Tree, Token

tree = Tree('function_decl', [
    Token('TYPE_NAME', 'integer'),
    Token('IDENTIFIER', 'calculate')
])
```

### 2. Dictionary Representation

```python
ast_dict = {
    'type': 'tree',
    'data': 'function_decl',
    'children': [
        {'type': 'token', 'type_': 'TYPE_NAME', 'value': 'integer'},
        {'type': 'token', 'type_': 'IDENTIFIER', 'value': 'calculate'}
    ]
}
```

### 3. Legacy String Format

```python
legacy_ast = {
    'type': 'legacy_ast',
    'content': 'Tree(Token(RULE, function_decl), ...)'
}
```

## Migration Guide

### Updating Existing Code

1. **Replace regex patterns with visitors:**

```python
# Old approach
import re
func_matches = re.findall(r"function_decl.*?'(\w+)'", ast_str)

# New approach
from src.model.visitors.ast_walker import ASTWalker
functions = ASTWalker.find_by_type(ast, 'function_decl')
```

2. **Use ModelExtractorVisitor for model extraction:**

```python
# Old approach
def _extract_window_model(self, ast):
    # Complex regex parsing...

# New approach
def _extract_window_model(self, ast):
    visitor = ModelExtractorVisitor()
    return visitor.extract_model(ast, 'window', object_name)
```

3. **Leverage pattern matching:**

```python
# Old approach
if "'CREATE'" in ast_str:
    events.append({'name': 'create', 'type': 'system_event'})

# New approach
create_blocks = matcher.find_all(ast, 'create_destroy_block')
for block in create_blocks:
    # Process CREATE/DESTROY events
```

## Best Practices

1. **Extend visitors for custom logic** - Don't modify core visitors
2. **Use ASTWalker for simple searches** - More efficient than full visitor traversal
3. **Cache visitor instances** - Reuse visitors when processing multiple ASTs
4. **Handle all AST formats** - Ensure compatibility with various input formats
5. **Write unit tests** - Test each visitor method independently

## Performance Considerations

- Visitor pattern is generally faster than regex for complex patterns
- ASTWalker provides efficient node searching without full traversal
- Pattern matchers can be pre-compiled and reused
- No regex compilation overhead

## Future Enhancements

1. **Parallel visitor execution** for large AST processing
2. **Visitor composition** for combining multiple visitors
3. **AST transformation visitors** for code modification
4. **Incremental visiting** for partial AST updates
5. **Visitor result caching** for repeated operations

## Examples

See `examples/visitor_pattern_demo.py` for complete working examples.

## Testing

Run visitor tests:

```bash
pytest tests/unit/model/test_visitors.py -v
```

## Troubleshooting

### Common Issues

1. **ImportError for visitors**
   - Ensure src/model/visitors is in Python path
   - Check __init__.py files exist

2. **Visitor not finding expected nodes**
   - Verify node type names match grammar rules
   - Use ASTWalker to explore AST structure

3. **Legacy AST handling**
   - Legacy string ASTs have limited extraction capability
   - Consider re-parsing source files for full AST

### Debug Tips

```python
# Print AST structure
import json
print(json.dumps(ast, indent=2))

# List all node types in AST
node_types = set()
for node in ASTWalker.walk(ast):
    node_type = ASTWalker._get_node_type(node)
    if node_type:
        node_types.add(node_type)
print("Node types:", sorted(node_types))

# Trace visitor execution
visitor = ModelExtractorVisitor()
visitor.debug = True  # If implemented
```
