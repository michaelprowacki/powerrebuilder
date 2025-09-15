# PowerBuilder to Modern Code Conversion Guide

## Overview

This guide covers the conversion patterns and mappings used when transforming PowerBuilder applications to Flutter (Dart) or Python.

## Control Mappings

### PowerBuilder → Flutter

| PowerBuilder Control | Flutter Widget | Notes |
|---------------------|----------------|-------|
| Window | Scaffold + Screen | Full page with app bar |
| CommandButton | ElevatedButton | With onPressed handler |
| StaticText | Text | Read-only text display |
| SingleLineEdit | TextField | Single line input |
| MultiLineEdit | TextField(maxLines: null) | Multi-line input |
| CheckBox | Checkbox + Text | With label |
| RadioButton | Radio + Text | In RadioListTile |
| ListBox | ListView | Scrollable list |
| DropDownListBox | DropdownButton | Dropdown selection |
| DataWindow | DataTable / Custom | Complex data grid |
| GroupBox | Container + Border | Visual grouping |
| Picture | Image | Image display |
| PictureButton | IconButton | Button with image |
| Tab | TabBarView | Tabbed interface |
| TreeView | TreeView (package) | Hierarchical data |
| Menu | AppBar actions / Drawer | Navigation menu |

### PowerBuilder → Python

| PowerBuilder Control | Python/Web Equivalent | Framework |
|---------------------|----------------------|-----------|
| Window | HTML Page / Jinja Template | FastAPI + Templates |
| CommandButton | `<button>` | HTML |
| StaticText | `<span>` or `<p>` | HTML |
| SingleLineEdit | `<input type="text">` | HTML |
| MultiLineEdit | `<textarea>` | HTML |
| CheckBox | `<input type="checkbox">` | HTML |
| RadioButton | `<input type="radio">` | HTML |
| ListBox | `<select>` or list component | HTML/JS |
| DataWindow | DataTables / Grid component | JavaScript library |
| Menu | Navigation component | Bootstrap/CSS |

## Event Mappings

### Common Event Conversions

| PowerBuilder Event | Flutter/Dart | Python/Web |
|-------------------|--------------|------------|
| clicked | onPressed / onTap | onclick |
| modified | onChanged | onchange |
| getfocus | onFocusChange (gain) | onfocus |
| losefocus | onFocusChange (lose) | onblur |
| constructor | initState() | `__init__()` |
| destructor | dispose() | `__del__()` |
| open | initState() | on_mount |
| close | dispose() | on_unmount |
| key | onKey | onkeypress |
| doubleclicked | onDoubleTap | ondblclick |
| rbuttondown | onSecondaryTap | oncontextmenu |

## Data Type Mappings

### PowerBuilder → Dart

| PowerBuilder | Dart | Notes |
|--------------|------|-------|
| integer | int | 32-bit integer |
| long | int | 64-bit integer |
| decimal | double | Fixed decimal |
| real | double | Floating point |
| boolean | bool | true/false |
| string | String | Unicode text |
| char | String | Single character |
| date | DateTime | Date only |
| time | DateTime | Time only |
| datetime | DateTime | Date and time |
| blob | Uint8List | Binary data |
| any | dynamic | Any type |

### PowerBuilder → Python

| PowerBuilder | Python | Notes |
|--------------|--------|-------|
| integer | int | Arbitrary precision |
| long | int | Arbitrary precision |
| decimal | Decimal | decimal.Decimal |
| real | float | 64-bit float |
| boolean | bool | True/False |
| string | str | Unicode string |
| char | str | Single character |
| date | date | datetime.date |
| time | time | datetime.time |
| datetime | datetime | datetime.datetime |
| blob | bytes | Binary data |
| any | Any | typing.Any |

## Code Pattern Conversions

### Variable Declaration

**PowerBuilder:**
```powerbuilder
integer li_count
string ls_name = "John"
boolean lb_active
```

**Dart:**
```dart
int liCount;
String lsName = "John";
bool lbActive;
```

**Python:**
```python
li_count: int
ls_name: str = "John"
lb_active: bool
```

### Control Structures

**PowerBuilder IF:**
```powerbuilder
IF li_count > 0 THEN
    MessageBox("Info", "Count is positive")
ELSEIF li_count < 0 THEN
    MessageBox("Info", "Count is negative")
ELSE
    MessageBox("Info", "Count is zero")
END IF
```

**Dart:**
```dart
if (liCount > 0) {
    showDialog(context: context,
        builder: (_) => AlertDialog(
            title: Text("Info"),
            content: Text("Count is positive")));
} else if (liCount < 0) {
    // ... negative case
} else {
    // ... zero case
}
```

**Python:**
```python
if li_count > 0:
    messages.info("Count is positive")
elif li_count < 0:
    messages.info("Count is negative")
else:
    messages.info("Count is zero")
```

### Loops

**PowerBuilder FOR:**
```powerbuilder
FOR li_i = 1 TO 10
    // loop body
NEXT
```

**Dart:**
```dart
for (int i = 1; i <= 10; i++) {
    // loop body
}
```

**Python:**
```python
for i in range(1, 11):
    # loop body
```

## Database Operations

### PowerBuilder Embedded SQL

```powerbuilder
SELECT employee_name, salary
INTO :ls_name, :ld_salary
FROM employees
WHERE employee_id = :li_id;
```

### Dart with sqflite/drift

```dart
final result = await db.select(employees)
    .where((e) => e.employeeId.equals(liId))
    .getSingle();

String lsName = result.employeeName;
double ldSalary = result.salary;
```

### Python with SQLAlchemy

```python
result = session.query(Employee)\
    .filter(Employee.employee_id == li_id)\
    .first()

ls_name = result.employee_name
ld_salary = result.salary
```

## Window/Screen Structure

### PowerBuilder Window
```powerbuilder
window w_employee
    // controls
    commandbutton cb_save
    singlelineedit sle_name

    // events
    event clicked() on cb_save
        // save logic
    end event
end window
```

### Flutter Screen
```dart
class EmployeeScreen extends StatefulWidget {
    @override
    _EmployeeScreenState createState() => _EmployeeScreenState();
}

class _EmployeeScreenState extends State<EmployeeScreen> {
    final _nameController = TextEditingController();

    void _onSaveClicked() {
        // save logic
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            body: Column(children: [
                TextField(controller: _nameController),
                ElevatedButton(
                    onPressed: _onSaveClicked,
                    child: Text("Save"))
            ])
        );
    }
}
```

### Python FastAPI + Templates
```python
@app.get("/employee")
async def employee_form():
    return templates.TemplateResponse("employee.html", {})

@app.post("/employee/save")
async def save_employee(name: str = Form(...)):
    # save logic
    return {"status": "saved"}
```

## DataWindow Conversion

DataWindows are complex and may require custom implementation:

### Simple Grid
- **Flutter**: Use DataTable or third-party grid packages
- **Python**: Use DataTables.js or AG-Grid

### Complex Reports
- **Flutter**: Consider pdf generation packages
- **Python**: Use ReportLab or similar

### Master-Detail
- **Flutter**: Nested ListView or expansion tiles
- **Python**: JavaScript components with AJAX

## Best Practices

1. **Naming Conventions**
   - Convert Hungarian notation to language conventions
   - `li_count` → `count` (with proper typing)

2. **State Management**
   - PowerBuilder instance variables → Flutter State/Provider
   - PowerBuilder global variables → Singleton services

3. **Error Handling**
   - PowerBuilder TRY-CATCH → Dart try-catch or Python try-except
   - Add proper null safety in Dart

4. **Async Operations**
   - PowerBuilder synchronous → Dart Future/async-await
   - Database operations should be async

5. **Architecture**
   - Consider MVVM or Clean Architecture
   - Separate business logic from UI
   - Use dependency injection

## Limitations

Some PowerBuilder features have no direct equivalent:
- DataWindow's built-in data pipeline
- PowerBuilder's transaction object model
- Certain visual inheritance patterns
- Some system-level API calls

These require architectural redesign or custom implementation.

## Detailed Conversion Rules

### Type System Mapping (Extended)

#### Complex Types
| PowerBuilder Type | Dart Type | Notes |
|------------------|-----------|-------|
| array[] | List<T> | Dynamic arrays |
| structure | class/freezed | Immutable data classes |
| powerobject | Object | Base class |
| nonvisualobject | Service class | Singleton or provider |

#### PowerBuilder Arrays to Dart
```powerbuilder
// PowerBuilder
integer li_values[10]
string ls_names[]
```

```dart
// Dart
List<int> liValues = List.filled(10, 0);
List<String> lsNames = [];
```

### State Management Patterns

#### PowerBuilder Instance Variables
```powerbuilder
// Instance variables in window
instance variables
    integer ii_customer_id
    string is_customer_name
    boolean ib_modified
end variables
```

#### Flutter State Management
```dart
class CustomerScreenState extends State<CustomerScreen> {
    int? _customerId;
    String _customerName = '';
    bool _isModified = false;

    // Or using Provider/Riverpod
    final customerProvider = StateNotifierProvider<CustomerNotifier, CustomerState>((ref) {
        return CustomerNotifier();
    });
}
```

## Practical Conversion Example

### Customer Management Window

#### Original PowerBuilder Code
```powerbuilder
window type w_customer_management from window
string title = "Customer Management"

// Instance Variables
datawindow dw_customers
commandbutton cb_new, cb_edit, cb_delete
singlelineedit sle_search

// Window Open Event
event open;
    dw_customers.SetTransObject(SQLCA)
    dw_customers.Retrieve()
    sle_search.SetFocus()
end event

// Search functionality
event ue_search;
    string ls_search
    ls_search = sle_search.text

    if Len(ls_search) > 0 then
        dw_customers.SetFilter("customer_name like '%" + ls_search + "%'")
        dw_customers.Filter()
    end if
end event
```

#### Converted Flutter Code
```dart
class CustomerManagementScreen extends StatefulWidget {
    @override
    _CustomerManagementScreenState createState() => _CustomerManagementScreenState();
}

class _CustomerManagementScreenState extends State<CustomerManagementScreen> {
    final _searchController = TextEditingController();
    List<Customer> _customers = [];
    List<Customer> _filteredCustomers = [];

    @override
    void initState() {
        super.initState();
        _loadCustomers();
    }

    Future<void> _loadCustomers() async {
        final customers = await CustomerService.getAll();
        setState(() {
            _customers = customers;
            _filteredCustomers = customers;
        });
    }

    void _searchCustomers(String query) {
        setState(() {
            if (query.isEmpty) {
                _filteredCustomers = _customers;
            } else {
                _filteredCustomers = _customers
                    .where((c) => c.name.toLowerCase().contains(query.toLowerCase()))
                    .toList();
            }
        });
    }

    @override
    Widget build(BuildContext context) {
        return Scaffold(
            appBar: AppBar(
                title: Text('Customer Management'),
                actions: [
                    IconButton(
                        icon: Icon(Icons.add),
                        onPressed: _newCustomer,
                    ),
                ],
            ),
            body: Column(
                children: [
                    Padding(
                        padding: EdgeInsets.all(8.0),
                        child: TextField(
                            controller: _searchController,
                            onChanged: _searchCustomers,
                            decoration: InputDecoration(
                                labelText: 'Search',
                                prefixIcon: Icon(Icons.search),
                            ),
                        ),
                    ),
                    Expanded(
                        child: DataTable(
                            columns: [
                                DataColumn(label: Text('ID')),
                                DataColumn(label: Text('Name')),
                                DataColumn(label: Text('Actions')),
                            ],
                            rows: _filteredCustomers.map((customer) =>
                                DataRow(cells: [
                                    DataCell(Text(customer.id.toString())),
                                    DataCell(Text(customer.name)),
                                    DataCell(Row(
                                        children: [
                                            IconButton(
                                                icon: Icon(Icons.edit),
                                                onPressed: () => _editCustomer(customer),
                                            ),
                                            IconButton(
                                                icon: Icon(Icons.delete),
                                                onPressed: () => _deleteCustomer(customer),
                                            ),
                                        ],
                                    )),
                                ])
                            ).toList(),
                        ),
                    ),
                ],
            ),
        );
    }
}
```

### Menu Conversion

#### PowerBuilder Menu
```powerbuilder
menu m_main from menu
    on m_main.create
        this.Item[] = {this.m_file, this.m_edit, this.m_window}
    end on

    menu m_file from menu
        menuitem m_new "&New\tCtrl+N"
        menuitem m_open "&Open\tCtrl+O"
        menuitem m_separator "-"
        menuitem m_exit "E&xit"
    end menu
end menu
```

#### Flutter Drawer Menu
```dart
Drawer(
    child: ListView(
        children: [
            DrawerHeader(
                child: Text('Main Menu'),
            ),
            ListTile(
                leading: Icon(Icons.add),
                title: Text('New'),
                onTap: () => _handleNew(),
            ),
            ListTile(
                leading: Icon(Icons.folder_open),
                title: Text('Open'),
                onTap: () => _handleOpen(),
            ),
            Divider(),
            ListTile(
                leading: Icon(Icons.exit_to_app),
                title: Text('Exit'),
                onTap: () => SystemNavigator.pop(),
            ),
        ],
    ),
)
```

## DataWindow SQL to Model Generation

DataWindow SQL should be parsed to generate:

### 1. Entity Classes
Dart classes representing database tables:
```dart
class Patient {
    final int patientId;
    final String firstName;
    final String lastName;
    // ... other fields
}
```

### 2. Repository Interfaces
Data access abstractions:
```dart
abstract class PatientRepository {
    Future<List<Patient>> findAll();
    Future<Patient?> findById(int id);
    Future<void> save(Patient patient);
}
```

### 3. DTO Classes
Data transfer objects for complex queries:
```dart
class PatientDetailsDto {
    final Patient patient;
    final List<Appointment> appointments;
    final InsuranceInfo insurance;
}
```

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Parse PowerBuilder source files
2. Extract DataWindow SQL definitions
3. Generate Dart entity models from SQL
4. Create base widget templates

### Phase 2: UI Generation
1. Map window definitions to Flutter screens
2. Convert visual controls to Flutter widgets
3. Implement event handling mappings
4. Generate navigation structure

### Phase 3: Business Logic
1. Convert PowerScript to Dart
2. Migrate non-visual objects
3. Implement data access layer
4. Handle transaction management

### Phase 4: DataWindow Migration
1. Extract SQL and display properties
2. Generate appropriate Flutter widgets
3. Implement data binding
4. Handle updates and validation

## Critical Considerations

1. **State Management**: PowerBuilder's event-driven model maps well to Flutter's reactive approach using providers or Riverpod

2. **Database Access**: PowerBuilder's embedded SQL needs to be converted to use Dart database packages like Drift or Floor

3. **DataWindow Complexity**: Complex DataWindows may require custom Flutter widgets combining multiple standard widgets

4. **Performance**: PowerBuilder's client-server architecture differs from Flutter's mobile-first approach - consider pagination and lazy loading

5. **Platform Differences**: Some PowerBuilder features (like OLE, ActiveX) have no direct Flutter equivalent and need alternative solutions
