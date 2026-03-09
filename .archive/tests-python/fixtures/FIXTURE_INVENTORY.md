# PowerBuilder Test Fixtures Inventory

## Overview
This document catalogs all PowerBuilder test fixtures available for comprehensive testing of the PowerRebuilder pipeline.

## PBD Files (Binary Libraries)

### PowerBuilder 6.0
- **dcm_email.pbd** - Email functionality test (original fixture)
  - Contains: n_cst_mailsession, n_cst_pdfwriter, n_cst_email, w_mail_test
  - Tests: Object extraction, email components, PDF generation

- **pb6_example_d1.pbd** - PowerBuilder 6.0 example data module 1
  - Source: `reference/pb_code_examples/PowerBuilder 6.0/PWRS/PB6/Examples/`
  - Tests: Legacy PB6 format, data access objects

- **pb6_example_fe.pbd** - PowerBuilder 6.0 frontend examples
  - Source: `reference/pb_code_examples/PowerBuilder 6.0/PWRS/PB6/Examples/`
  - Tests: UI components, window objects

### PowerBuilder 10.0
- **pb10_transtlk_main.pbd** - TransTalk main module
  - Source: `reference/pb_code_examples/PowerBuilder 10.0/Sybase/PowerBuilder 10.0/TransTlk/`
  - Tests: Application structure, main entry points

- **pb10_translate.pbd** - Translation services
  - Source: `reference/pb_code_examples/PowerBuilder 10.0/Sybase/PowerBuilder 10.0/TransTlk/`
  - Tests: String handling, internationalization

- **pb10_crypto_client.pbd** - Cryptography client
  - Source: `reference/pb_code_examples/PowerBuilder 10.0/Sybase/PowerBuilder 10.0/Cryptograph/`
  - Tests: Security features, encryption/decryption

### PowerBuilder 12.0
- **pb12_datawindow_srv.pbd** - DataWindow services
  - Source: `reference/pb_code_examples/PowerBuilder 12.0/Sybase/PowerBuilder 12.0/TransTlk/`
  - Tests: Advanced DataWindow functionality, services architecture

## Source Files (PowerScript)

### Transaction & SQL Testing
- **transaction_test.srw** - Window demonstrating transaction management
  - Features:
    - Local transaction object creation
    - Savepoint management
    - Commit/Rollback functionality
    - Transaction logging
    - Error handling
  - Tests: SQL statements, transaction boundaries, database connectivity

### Inheritance Testing
- **inheritance_test.sru** - Base service class (n_base_service)
  - Features:
    - Protected and private visibility modifiers
    - Virtual methods for overriding
    - Constructor/destructor chain
    - Debug logging functionality

- **inheritance_child.sru** - Derived data service (n_data_service)
  - Features:
    - Method overriding (of_initialize)
    - Additional functionality
    - Transaction management
    - DataStore operations
  - Tests: Inheritance chain, polymorphism, method resolution

### DataWindow Testing
- **complex_datawindow.srd** - Advanced DataWindow definition
  - Features:
    - SQL with retrieval arguments
    - Computed fields (sum, count)
    - Summary band calculations
    - Column formatting (currency, dates)
    - Dropdown DataWindow columns
    - Conditional expressions
  - Tests: DataWindow parsing, SQL extraction, computed field evaluation

### Event Handling Testing
- **event_handling.sru** - UserObject with complex event handling
  - Features:
    - Custom events (ue_custom, ue_validate, ue_process)
    - Events with return values
    - Pass-by-reference parameters
    - Event chaining and posting
    - Timer-based delayed events
    - Event queue management
  - Tests: Event declaration, parameter passing, event triggering

### Basic Fixtures (Original)
- **simple_window.srw** - Basic window with controls
- **custom_control.sru** - Custom user object
- **main_menu.srm** - Menu structure
- **globals.sra** - Application object

## PowerBuilder Features Coverage

### Version Coverage
- ✅ PowerBuilder 6.0 (oldest supported)
- ✅ PowerBuilder 10.0
- ✅ PowerBuilder 10.5 (crypto features)
- ✅ PowerBuilder 12.0
- ❌ PowerBuilder 15+ (not yet added)

### Object Type Coverage
- ✅ Windows (srw)
- ✅ User Objects (sru)
- ✅ DataWindows (srd)
- ✅ Menus (srm)
- ✅ Applications (sra)
- ❌ Functions (srf) - TODO
- ❌ Structures (srs) - TODO
- ❌ Proxy objects - TODO

### Feature Coverage
- ✅ Basic controls and properties
- ✅ SQL and database operations
- ✅ Transactions with savepoints
- ✅ Inheritance and polymorphism
- ✅ Event handling (standard and custom)
- ✅ DataWindow advanced features
- ✅ Pass-by-reference parameters
- ✅ Protected/private visibility
- ❌ External function declarations - TODO
- ❌ Structure definitions - TODO
- ❌ Global functions - TODO
- ❌ Shared variables - TODO

## Integration Test Coverage

### Pipeline Tests
1. **Binary Extraction** - Tests with all PBD files
2. **Decompilation** - P-code to PowerScript conversion
3. **Parsing** - PowerScript to AST
4. **Modeling** - AST to semantic models
5. **Generation** - Models to Flutter/Python

### Feature-Specific Tests
1. **Transaction Management** - Begin/Commit/Rollback flow
2. **Inheritance Chain** - Base class to derived class
3. **Event System** - Event declaration, triggering, and chaining
4. **DataWindow Processing** - SQL extraction, computed fields
5. **Cross-Version Compatibility** - PB6 to PB12 formats

## Usage in Tests

```python
# Example: Testing PB6 email functionality
def test_pb6_email_extraction():
    pbd_file = Path("tests/fixtures/pbd_files/dcm_email.pbd")
    # ... extraction and verification

# Example: Testing inheritance
def test_inheritance_parsing():
    base = Path("tests/fixtures/inheritance_test.sru")
    child = Path("tests/fixtures/inheritance_child.sru")
    # ... parse and verify inheritance chain
```

## Adding New Fixtures

When adding new fixtures:
1. Place PBD files in `tests/fixtures/pbd_files/`
2. Place source files in `tests/fixtures/`
3. Update this inventory
4. Add corresponding tests in `tests/integration/`
5. Document the PowerBuilder features being tested

## Known Issues

1. Some PBD files may contain compressed or encrypted sections
2. Very old PB versions (< 6.0) may have different formats
3. Some advanced features (e.g., .NET integration) not yet covered
