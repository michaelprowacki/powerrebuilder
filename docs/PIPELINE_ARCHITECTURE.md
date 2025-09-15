# PowerRebuilder Pipeline Architecture

## Overview

The PowerRebuilder pipeline processes PowerBuilder applications through a sequential architecture that extracts P-code, decompiles it to source, parses it to AST, builds models, and generates modern code.

## The Pipeline Flow

```
┌─────────────────┐
│   PBL/PBD Files │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     EXTRACT     │ Extracts compiled P-code files (.fun)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    P-code Files │ Compiled bytecode files
│      (.fun)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    DECOMPILE    │ Reconstructs PowerBuilder source from P-code
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Source Files  │ PowerBuilder source code
│      (.sru)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      PARSE      │ Builds Abstract Syntax Trees
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    AST JSON     │ Structured representation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      MODEL      │ Creates semantic models
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    GENERATE     │ Produces modern code
└────────┬────────┘
         │
         ▼
   Modern Web App
```

## Key Points

### 1. Extract Stage Outputs P-code Files

PowerBuilder PBL/PBD files contain compiled P-code (primarily `.fun` files). The Extract stage decompresses these files and extracts the bytecode for decompilation.

### 2. Decompile MUST Run Before Parse

**This is a SEQUENTIAL pipeline!** The stages run in this order:

1. **Extract** → Produces `.fun` (P-code) files
2. **Decompile** → Converts `.fun` to `.sru` (source) files
3. **Parse** → Processes `.sru` files to create AST
4. **Model** → Builds semantic models from AST
5. **Generate** → Creates modern code from models

### 3. Why This Order is Required

- **Parse cannot process P-code directly** - it needs PowerBuilder source code
- **Decompile produces the source code** that Parse requires
- **Model needs the AST** that Parse produces
- **Generate needs the semantic models** from Model stage

## File Flow Reference

### Extract Output
| File | Description | Next Stage |
|------|-------------|------------|
| .fun | Compiled P-code | Decompile |

### Decompile Output
| File | Description | Next Stage |
|------|-------------|------------|
| .sru | PowerBuilder source | Parse |

### Parse Output
| File | Description | Next Stage |
|------|-------------|------------|
| .json | AST representation | Model |

### Model Output
| File | Description | Next Stage |
|------|-------------|------------|
| models | Semantic models | Generate |

## Common Misconceptions (CORRECTED)

### ❌ WRONG: "Parse and Decompile run in parallel"
This was incorrect documentation. They run SEQUENTIALLY.

### ✅ CORRECT: "Decompile must complete before Parse begins"
Parse requires the `.sru` files that Decompile produces.

### ❌ WRONG: "Extract outputs both source and P-code files"
Extract primarily outputs P-code files that need decompilation.

### ✅ CORRECT: "Extract outputs P-code files for decompilation"
The `.fun` files contain bytecode, not source code.

### ❌ WRONG: "Parse can process any PowerBuilder file"
Parse can only process PowerBuilder source code files.

### ✅ CORRECT: "Parse processes .sru files from Decompile"
Parse requires decompiled source code as input.

## Implementation Details

### Pipeline Execution Order

```python
def run_pipeline(input_dir, output_dir):
    # Stage 1: Extract P-code files
    extracted_files = extract_stage(input_dir)

    # Stage 2: Decompile P-code to source
    source_files = decompile_stage(extracted_files)

    # Stage 3: Parse source to AST
    ast_files = parse_stage(source_files)

    # Stage 4: Build semantic models
    models = model_stage(ast_files)

    # Stage 5: Generate modern code
    generated_code = generate_stage(models)

    return generated_code
```

### File Type Routing

```python
def process_extracted_file(file_path):
    if file_path.suffix == '.fun':
        # P-code file - send to decompile
        decompiled = decompile_pcode(file_path)
        # Then send decompiled source to parse
        ast = parse_source(decompiled)
        return ast
    else:
        raise ValueError(f"Unexpected file type: {file_path.suffix}")
```

## Performance Considerations

### Sequential Benefits
- **Simpler architecture**: No complex synchronization needed
- **Clear data flow**: Each stage has well-defined inputs/outputs
- **Easy debugging**: Can trace issues through each stage
- **Memory efficiency**: Only one stage active at a time

### Optimization Opportunities
- **File-level parallelism**: Process multiple files within each stage
- **Streaming**: Process large files in chunks
- **Caching**: Cache results between runs
- **Incremental processing**: Only process changed files

## Example: Processing a Function

Consider a PowerBuilder function in `myapp.pbl`:

1. **Extract** finds:
   - `calculate_total.fun` (compiled P-code)

2. **Decompile** processes:
   - Input: `calculate_total.fun` (bytecode)
   - Output: `calculate_total.sru` (source code)
   ```powerbuilder
   function decimal calculate_total(decimal price, integer qty)
       return price * qty * 0.9
   end function
   ```

3. **Parse** processes:
   - Input: `calculate_total.sru`
   - Output: `calculate_total.json` (AST)

4. **Model** processes:
   - Input: AST JSON
   - Output: Function model object

5. **Generate** produces:
   - Modern code (Python/Dart/etc.)

## Summary

The PowerRebuilder pipeline is a **sequential, five-stage process**:

1. **Extract** - Gets P-code from PBL/PBD
2. **Decompile** - Converts P-code to source
3. **Parse** - Converts source to AST
4. **Model** - Builds semantic models
5. **Generate** - Creates modern code

Each stage depends on the output of the previous stage. This sequential design ensures data flows correctly through the transformation process.
