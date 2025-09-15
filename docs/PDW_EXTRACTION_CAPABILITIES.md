# PDW Extraction Capabilities

## Overview

PDW (PowerBuilder DataWindow) files are compiled binary formats that contain DataWindow definitions. While the original source code cannot be fully reconstructed, we have discovered that PDW files contain significant structured data that can be extracted and decompiled.

## What is a PDW File?

- **Format**: Binary compiled format
- **Signature**: Files start with "PDW" followed by version (e.g., "PDW1000" for PowerBuilder 10.0)
- **Purpose**: Compiled DataWindow definitions used by PowerBuilder applications
- **Extensions**: Usually `.dwo` files that have been compiled

## Discovered Structure

Through binary analysis, we've identified the following structure in PDW files:

### Header (0x00-0x20)
- **0x00-0x08**: Version signature (e.g., "PDW1000")
- **0x08-0x0C**: Header field 1 (purpose unclear, possibly object count)
- **0x0C-0x10**: Header field 2 (purpose unclear, possibly size)
- **0x10-0x20**: Additional metadata

### Data Sections
1. **Metadata Region** (0x20-0x100)
   - Contains various counts and offsets
   - Includes coordinate and size information

2. **String Table** (typically starts around 0xB20)
   - UTF-16 LE encoded strings
   - Contains column names, display names, format strings
   - Example: "treatment_id", "person_id", "[general]"

3. **SQL Region** (variable location)
   - UTF-16 LE encoded SQL statements
   - Complete SELECT statements with joins and subqueries
   - Preserves original query structure

4. **Layout Information**
   - Column positions (x, y, width, height)
   - Alignment values (0=Left, 1=Center, 2=Right)
   - Font information (names and sizes)
   - Color values (RGB format)

## What We Can Extract

### 1. SQL Queries
- Complete SELECT statements
- Table names and aliases
- Column names and expressions
- JOIN conditions
- WHERE clauses
- Subqueries

### 2. Column Information
- Column names
- Display names
- Database column names
- Position and size (x, y, width, height)
- Data types (inferred)

### 3. Layout Properties
- Window dimensions
- Column positions
- Text alignment
- Background colors
- Font information (name, size)

### 4. DataWindow Properties
- Version information
- Format strings (e.g., "[general]", date formats)
- Display properties

## What We Cannot Extract

- **Event Scripts**: Button clicks, row changes, etc.
- **Computed Fields**: Expressions and calculations
- **Validation Rules**: Input validation logic
- **Complex Expressions**: Display conditions, dynamic properties
- **Original Comments**: Developer comments and documentation
- **Exact Formatting**: Precise original source code layout

## Implementation

We've implemented a comprehensive PDW extractor with the following components:

### 1. PDW Detector (`pdw_detector.py`)
- Detects PDW format by signature
- Identifies PowerBuilder version
- Determines if extraction is possible

### 2. PDW SQL Extractor (`pdw_sql_extractor.py`)
- Extracts SQL statements using multiple strategies
- Handles both ASCII and UTF-16 encoding
- Cleans and validates extracted SQL

### 3. PDW Comprehensive Extractor (`pdw_comprehensive_extractor.py`)
- Extracts complete DataWindow structure
- Parses column definitions with properties
- Extracts layout and display information
- Generates source code approximation

### 4. PDW Handler (`pdw_handler.py`)
- Unified interface for PDW processing
- Multiple extraction modes (SQL only, metadata, comprehensive)
- Integration with existing pipeline

## Usage Example

```python
from decompile.analysis.pdw_handler import PDWHandler

# Read PDW file
with open('datawindow.dwo', 'rb') as f:
    data = f.read()

# Extract comprehensive information
result = PDWHandler.process_pdw_file(data, 'datawindow.dwo')

# Access extracted data
if result['datawindow']:
    dw = result['datawindow']
    print(f"SQL: {dw.sql}")
    print(f"Columns: {[col.name for col in dw.columns]}")
    print(f"Source: {dw.get_source_approximation()}")
```

## Future Enhancements

1. **Pattern Recognition**: Identify more binary patterns for additional properties
2. **Version-Specific Parsing**: Handle differences between PowerBuilder versions
3. **Enhanced Layout Extraction**: Extract more detailed positioning information
4. **Property Mapping**: Better understanding of binary property encodings
5. **Validation Rule Detection**: Attempt to identify validation patterns

## Conclusion

While PDW files are compiled and don't contain the complete source code, they preserve significant structural information that can be extracted and used to reconstruct a functional approximation of the original DataWindow. This is particularly valuable when original source files are lost or unavailable.
