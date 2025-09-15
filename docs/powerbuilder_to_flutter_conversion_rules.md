# PowerBuilder to Flutter/Dart Conversion Rules

## Overview

This document defines the comprehensive mapping rules for converting PowerBuilder applications to Flutter/Dart. The conversion process preserves the business logic, data management, and UI structure while modernizing the technology stack.

## Table of Contents

1. [Type System Mapping](#type-system-mapping)
2. [Object Type Conversions](#object-type-conversions)
3. [UI Control Mappings](#ui-control-mappings)
4. [DataWindow Conversion](#datawindow-conversion)
5. [Event System Mapping](#event-system-mapping)
6. [Data Access Layer](#data-access-layer)
7. [State Management](#state-management)
8. [Navigation and Routing](#navigation-and-routing)
9. [Styling and Theming](#styling-and-theming)
10. [Best Practices](#best-practices)

---

## 1. Type System Mapping

### Basic Types

| PowerBuilder Type | Dart Type | Notes |
|------------------|-----------|-------|
| integer | int | 32-bit integer |
| long | int | Dart int is 64-bit |
| decimal(n,m) | double | Use decimal package for precision |
| real | double | Single precision float |
| double | double | Double precision float |
| string | String | Unicode by default |
| char(n) | String | Fixed length → String |
| boolean | bool | Direct mapping |
| date | DateTime | Date only |
| time | DateTime | Time only with date set to epoch |
| datetime | DateTime | Full timestamp |
| timestamp | DateTime | With timezone info |
| blob | Uint8List | Binary data |

### Complex Types

| PowerBuilder Type | Dart Type | Notes |
|------------------|-----------|-------|
| array[] | List<T> | Dynamic arrays |
| structure | class/freezed | Immutable data classes |
| any | dynamic | Use sparingly |
| powerobject | Object | Base class |
| nonvisualobject | Service class | Singleton or provider |
| datastore | Repository | Data access pattern |

---

## 2. Object Type Conversions

### Windows → Screens

PowerBuilder Window objects map to Flutter Screen widgets:

```dart
// PowerBuilder: w_customer_list
// Flutter: customer_list_screen.dart

class CustomerListScreen extends StatefulWidget {
  // Window parameters → constructor parameters
  final String? filterType;
  final int? customerId;

  // Window instance variables → State properties
  @override
  _CustomerListScreenState createState() => _CustomerListScreenState();
}
```

### User Objects → Widgets

PowerBuilder User Objects become reusable Flutter widgets:

```dart
// PowerBuilder: u_customer_detail
// Flutter: customer_detail_widget.dart

class CustomerDetailWidget extends StatelessWidget {
  // Object properties → widget properties
  final Customer customer;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
}
```

### Menu Objects → Navigation

PowerBuilder menus map to Flutter navigation patterns:

```dart
// PowerBuilder: m_main_menu
// Flutter: Drawer, BottomNavigationBar, or AppBar actions

Drawer(
  child: ListView(
    children: [
      ListTile(title: Text('Customers'), onTap: () => navigateToCustomers()),
      ListTile(title: Text('Orders'), onTap: () => navigateToOrders()),
    ],
  ),
)
```

---

## 3. UI Control Mappings

### Basic Controls

| PowerBuilder Control | Flutter Widget | Configuration |
|---------------------|----------------|---------------|
| StaticText | Text | Style with Theme |
| SingleLineEdit | TextField | With TextEditingController |
| MultiLineEdit | TextField | maxLines: null |
| CommandButton | ElevatedButton | With onPressed callback |
| CheckBox | Checkbox | With value binding |
| RadioButton | Radio | In RadioListTile |
| DropDownListBox | DropdownButton | With items list |
| ListBox | ListView | With ListTile items |
| ComboBox | Autocomplete | With options builder |
| Picture | Image | Asset/Network/File |
| PictureButton | IconButton | With icon |
| GroupBox | Container + Column | With decoration |
| Tab | TabBar + TabBarView | With TabController |

### Advanced Controls

| PowerBuilder Control | Flutter Widget | Implementation |
|---------------------|----------------|----------------|
| TreeView | TreeView (package) | Use flutter_treeview |
| ListView | ListView.builder | With custom item widgets |
| DataWindow | DataTable/Custom | See DataWindow section |
| Graph | charts_flutter | Map graph types |
| RichTextEdit | flutter_quill | Rich text editor |
| OLE | WebView/Platform | Platform-specific view |

---

## 4. DataWindow Conversion

DataWindows are the most complex PowerBuilder objects. They map to custom Flutter widgets with multiple presentation styles:

### Presentation Styles

| PowerBuilder Style | Flutter Implementation |
|-------------------|------------------------|
| Grid | DataTable with sorting/filtering |
| Freeform | Form with positioned fields |
| Tabular | ListView with custom rows |
| Group | Grouped ListView |
| Crosstab | Custom pivot table widget |
| Graph | charts_flutter widgets |
| Composite | Multiple embedded widgets |
| RichText | Formatted document view |

### DataWindow Components

```dart
class DataWindowWidget extends StatefulWidget {
  // Data source
  final Future<List<T>> Function()? retrieveData;

  // CRUD operations
  final Future<void> Function(T)? onInsert;
  final Future<void> Function(T)? onUpdate;
  final Future<void> Function(T)? onDelete;

  // Features
  final bool allowSort;
  final bool allowFilter;
  final bool allowExport;

  // Column definitions
  final List<DataWindowColumn> columns;
}
```

### Column Mapping

| DataWindow Column Property | Flutter DataColumn Property |
|---------------------------|----------------------------|
| name | DataColumn label |
| data_type | Type validation |
| format | Text formatting |
| width | Column width constraints |
| alignment | Text alignment |
| edit_style | Input widget type |
| validation | Form validation |

---

## 5. Event System Mapping

### Window Events

| PowerBuilder Event | Flutter Equivalent |
|-------------------|-------------------|
| open | initState() |
| close | dispose() |
| activate | onResume (with lifecycle) |
| deactivate | onPause (with lifecycle) |
| resize | LayoutBuilder |
| key | RawKeyboardListener |

### Control Events

| PowerBuilder Event | Flutter Callback |
|-------------------|------------------|
| clicked | onPressed/onTap |
| doubleclicked | onDoubleTap |
| getfocus | FocusNode.addListener |
| losefocus | FocusNode.addListener |
| modified | onChanged |
| itemchanged | onChanged (dropdown) |
| selectionchanged | onSelectionChanged |

### DataWindow Events

| PowerBuilder Event | Flutter Implementation |
|-------------------|------------------------|
| itemchanged | Cell edit callback |
| itemerror | Validation error handler |
| retrieverow | Stream builder update |
| updatestart | Pre-save validation |
| updateend | Post-save callback |
| rowfocuschanged | Selection callback |

---

## 6. Data Access Layer

### Transaction Objects → Repositories

PowerBuilder SQLCA maps to repository pattern:

```dart
abstract class CustomerRepository {
  Future<List<Customer>> findAll();
  Future<Customer?> findById(int id);
  Future<Customer> save(Customer customer);
  Future<void> delete(int id);
}

class SqlCustomerRepository implements CustomerRepository {
  final Database database;

  // SQL operations using database connection
}
```

### Embedded SQL → Repository Methods

| PowerBuilder SQL | Repository Method |
|-----------------|-------------------|
| SELECT ... INTO | findOne() |
| DECLARE cursor | findAll() with pagination |
| INSERT | create() |
| UPDATE | update() |
| DELETE | delete() |
| COMMIT | Transaction handling |

---

## 7. State Management

### PowerBuilder State → Flutter State

| PowerBuilder Concept | Flutter Pattern |
|---------------------|-----------------|
| Instance variables | State class properties |
| Shared variables | Static properties |
| Global variables | Provider/Riverpod |
| Window parameters | Constructor parameters |
| Message object | Navigation arguments |

### Recommended State Management

1. **Local State**: StatefulWidget for UI state
2. **Shared State**: Provider/Riverpod for app state
3. **Remote State**: Repository + FutureBuilder
4. **Complex State**: BLoC pattern for business logic

---

## 8. Navigation and Routing

### Window Operations

| PowerBuilder | Flutter Navigation |
|--------------|-------------------|
| Open(window) | Navigator.push() |
| OpenSheet() | showModalBottomSheet() |
| OpenWithParm() | Navigator.push with arguments |
| Close() | Navigator.pop() |
| CloseWithReturn() | Navigator.pop with result |

### Navigation Patterns

```dart
// Named routes
Navigator.pushNamed(context, '/customer/detail', arguments: customerId);

// Direct navigation
Navigator.push(
  context,
  MaterialPageRoute(
    builder: (context) => CustomerDetailScreen(customerId: id),
  ),
);

// Dialog
showDialog(
  context: context,
  builder: (context) => CustomerEditDialog(customer: customer),
);
```

---

## 9. Styling and Theming

### Visual Properties

| PowerBuilder Property | Flutter Theme Property |
|----------------------|------------------------|
| BackColor | backgroundColor |
| TextColor | foregroundColor |
| Font | TextStyle |
| Border | Border/BoxDecoration |
| Enabled | enabled property |
| Visible | Visibility widget |

### Design System

Create a centralized design system:

```dart
class AppDesignSystem {
  // Colors
  static const primaryColor = Color(0xFF2196F3);
  static const secondaryColor = Color(0xFF03DAC6);

  // Typography
  static const headingStyle = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
  );

  // Spacing
  static const defaultPadding = EdgeInsets.all(16.0);

  // Themes
  static final lightTheme = ThemeData(...);
  static final darkTheme = ThemeData(...);
}
```

---

## 10. Best Practices

### Code Organization

```
lib/
├── core/           # Core utilities, themes
├── data/           # Repositories, models
├── domain/         # Business logic
├── presentation/   # UI layer
│   ├── screens/    # Full screens
│   ├── widgets/    # Reusable widgets
│   └── providers/  # State management
└── main.dart       # App entry point
```

### Conversion Guidelines

1. **Preserve Business Logic**: Keep PowerBuilder business rules intact
2. **Modernize UI**: Use Material Design or Cupertino widgets
3. **Async Operations**: Convert to Future/Stream patterns
4. **Error Handling**: Use try-catch and Result types
5. **Testing**: Write unit and widget tests
6. **Documentation**: Document complex conversions

### Performance Optimization

1. Use `const` constructors where possible
2. Implement lazy loading for large datasets
3. Optimize images and assets
4. Use ListView.builder for long lists
5. Implement proper disposal of resources

### Migration Strategy

1. **Phase 1**: Core data models and repositories
2. **Phase 2**: Business logic services
3. **Phase 3**: UI screens and widgets
4. **Phase 4**: Integration and testing
5. **Phase 5**: Performance optimization

---

## Appendix: Code Templates

### Screen Template
```dart
class ${Name}Screen extends StatefulWidget {
  // Parameters from PowerBuilder window

  @override
  _${Name}ScreenState createState() => _${Name}ScreenState();
}

class _${Name}ScreenState extends State<${Name}Screen> {
  // Instance variables from PowerBuilder

  @override
  void initState() {
    super.initState();
    // Open event logic
  }

  @override
  Widget build(BuildContext context) {
    // Window controls layout
  }

  @override
  void dispose() {
    // Close event logic
    super.dispose();
  }
}
```

### Repository Template
```dart
abstract class ${Name}Repository {
  Future<List<${Model}>> findAll();
  Future<${Model}?> findById(int id);
  Future<${Model}> save(${Model} model);
  Future<void> delete(int id);
}
```

### Model Template
```dart
@freezed
class ${Name} with _$${Name} {
  const factory ${Name}({
    // Properties from PowerBuilder structure
  }) = _${Name};

  factory ${Name}.fromJson(Map<String, dynamic> json) =>
      _$${Name}FromJson(json);
}
```

---

This document serves as the authoritative guide for converting PowerBuilder applications to Flutter/Dart. It should be updated as new patterns and best practices emerge during the conversion process.

---

## Merged from docs/powerbuilder_flutter_conversion_example.md

# PowerBuilder to Flutter Conversion Example

This document demonstrates a practical example of converting a PowerBuilder application component to Flutter/Dart using the defined conversion rules.

## Example: Customer Management Window

### Original PowerBuilder Code

#### Window: w_customer_management

```powerbuilder
// Window Properties
window type w_customer_management from window
string title = "Customer Management"
boolean maxbox = true
boolean resizable = true
long backcolor = 67108864
string icon = "customer.ico"
boolean center = true

// Instance Variables
datawindow dw_customers
commandbutton cb_new
commandbutton cb_edit
commandbutton cb_delete
commandbutton cb_refresh
singlelineedit sle_search
statictext st_search_label

// Window Open Event
event open;
    // Initialize datawindow
    dw_customers.SetTransObject(SQLCA)
    dw_customers.Retrieve()

    // Set focus to search field
    sle_search.SetFocus()
end event

// Search functionality
event ue_search;
    string ls_search
    ls_search = sle_search.text

    if Len(ls_search) > 0 then
        dw_customers.SetFilter("customer_name like '%" + ls_search + "%'")
        dw_customers.Filter()
    else
        dw_customers.SetFilter("")
        dw_customers.Filter()
    end if
end event

// Button Events
event cb_new::clicked;
    OpenWithParm(w_customer_detail, "NEW")
    if Message.DoubleParm = 1 then
        dw_customers.Retrieve()
    end if
end event

event cb_edit::clicked;
    long ll_row
    long ll_customer_id

    ll_row = dw_customers.GetRow()
    if ll_row > 0 then
        ll_customer_id = dw_customers.GetItemNumber(ll_row, "customer_id")
        OpenWithParm(w_customer_detail, ll_customer_id)
        if Message.DoubleParm = 1 then
            dw_customers.Retrieve()
        end if
    end if
end event

event cb_delete::clicked;
    long ll_row
    integer li_response

    ll_row = dw_customers.GetRow()
    if ll_row > 0 then
        li_response = MessageBox("Confirm", "Delete this customer?", Question!, YesNo!)
        if li_response = 1 then
            dw_customers.DeleteRow(ll_row)
            if dw_customers.Update() = 1 then
                Commit;
                MessageBox("Success", "Customer deleted successfully")
            else
                Rollback;
                MessageBox("Error", "Failed to delete customer")
            end if
        end if
    end if
end event
```

#### DataWindow: d_customers

```sql
SELECT customer_id,
       customer_name,
       contact_person,
       phone,
       email,
       address,
       city,
       country,
       credit_limit,
       status,
       created_date
FROM customers
ORDER BY customer_name
```

### Converted Flutter/Dart Code

#### Screen: customer_management_screen.dart

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/customer.dart';
import '../repositories/customer_repository.dart';
import '../widgets/customer_datawindow_widget.dart';
import 'customer_detail_screen.dart';

class CustomerManagementScreen extends StatefulWidget {
  const CustomerManagementScreen({Key? key}) : super(key: key);

  @override
  _CustomerManagementScreenState createState() => _CustomerManagementScreenState();
}

class _CustomerManagementScreenState extends State<CustomerManagementScreen> {
  // Instance Variables (from PowerBuilder)
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocusNode = FocusNode();
  List<Customer> _customers = [];
  List<Customer> _filteredCustomers = [];
  bool _isLoading = false;
  Customer? _selectedCustomer;

  // Repository
  late final CustomerRepository _repository;

  @override
  void initState() {
    super.initState();
    // Window Open Event equivalent
    _repository = context.read<CustomerRepository>();
    _loadCustomers();

    // Set focus to search field
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _searchFocusNode.requestFocus();
    });

    // Listen to search changes
    _searchController.addListener(_onSearchChanged);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  // Load customers (Retrieve equivalent)
  Future<void> _loadCustomers() async {
    setState(() => _isLoading = true);

    try {
      final customers = await _repository.findAll();
      setState(() {
        _customers = customers;
        _filteredCustomers = customers;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      _showErrorMessage('Failed to load customers: $e');
    }
  }

  // Search functionality (ue_search event equivalent)
  void _onSearchChanged() {
    final searchText = _searchController.text.toLowerCase();

    setState(() {
      if (searchText.isEmpty) {
        _filteredCustomers = _customers;
      } else {
        _filteredCustomers = _customers
            .where((customer) =>
                customer.customerName.toLowerCase().contains(searchText))
            .toList();
      }
    });
  }

  // New button clicked event
  Future<void> _onNewCustomer() async {
    final result = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) => CustomerDetailScreen(
          mode: CustomerDetailMode.create,
        ),
      ),
    );

    if (result == true) {
      _loadCustomers();
    }
  }

  // Edit button clicked event
  Future<void> _onEditCustomer() async {
    if (_selectedCustomer == null) return;

    final result = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) => CustomerDetailScreen(
          mode: CustomerDetailMode.edit,
          customerId: _selectedCustomer!.customerId,
        ),
      ),
    );

    if (result == true) {
      _loadCustomers();
    }
  }

  // Delete button clicked event
  Future<void> _onDeleteCustomer() async {
    if (_selectedCustomer == null) return;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm'),
        content: const Text('Delete this customer?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('No'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Yes'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await _repository.delete(_selectedCustomer!.customerId);
        _showSuccessMessage('Customer deleted successfully');
        _loadCustomers();
      } catch (e) {
        _showErrorMessage('Failed to delete customer: $e');
      }
    }
  }

  void _showSuccessMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.green),
    );
  }

  void _showErrorMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Customer Management'),
        centerTitle: true,
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                const Text('Search:'),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    focusNode: _searchFocusNode,
                    decoration: const InputDecoration(
                      hintText: 'Enter customer name...',
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Action buttons
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Row(
              children: [
                ElevatedButton.icon(
                  onPressed: _onNewCustomer,
                  icon: const Icon(Icons.add),
                  label: const Text('New'),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  onPressed: _selectedCustomer != null ? _onEditCustomer : null,
                  icon: const Icon(Icons.edit),
                  label: const Text('Edit'),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  onPressed: _selectedCustomer != null ? _onDeleteCustomer : null,
                  icon: const Icon(Icons.delete),
                  label: const Text('Delete'),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  onPressed: _loadCustomers,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Refresh'),
                ),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // DataWindow equivalent
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : CustomerDataWindowWidget(
                    customers: _filteredCustomers,
                    onSelectionChanged: (customer) {
                      setState(() => _selectedCustomer = customer);
                    },
                    onRowDoubleTap: (customer) {
                      _selectedCustomer = customer;
                      _onEditCustomer();
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
```

#### DataWindow Widget: customer_datawindow_widget.dart

```dart
import 'package:flutter/material.dart';
import '../models/customer.dart';
import '../core/app_design_system.dart';

class CustomerDataWindowWidget extends StatefulWidget {
  final List<Customer> customers;
  final Function(Customer?)? onSelectionChanged;
  final Function(Customer)? onRowDoubleTap;

  const CustomerDataWindowWidget({
    Key? key,
    required this.customers,
    this.onSelectionChanged,
    this.onRowDoubleTap,
  }) : super(key: key);

  @override
  _CustomerDataWindowWidgetState createState() =>
      _CustomerDataWindowWidgetState();
}

class _CustomerDataWindowWidgetState extends State<CustomerDataWindowWidget> {
  int? _selectedIndex;
  int _sortColumnIndex = 1; // Default sort by customer name
  bool _sortAscending = true;

  @override
  Widget build(BuildContext context) {
    // Sort the data
    final sortedCustomers = List<Customer>.from(widget.customers)
      ..sort((a, b) {
        int result;
        switch (_sortColumnIndex) {
          case 0:
            result = a.customerId.compareTo(b.customerId);
            break;
          case 1:
            result = a.customerName.compareTo(b.customerName);
            break;
          case 2:
            result = (a.contactPerson ?? '').compareTo(b.contactPerson ?? '');
            break;
          case 3:
            result = (a.email ?? '').compareTo(b.email ?? '');
            break;
          case 4:
            result = a.creditLimit.compareTo(b.creditLimit);
            break;
          case 5:
            result = a.status.compareTo(b.status);
            break;
          default:
            result = 0;
        }
        return _sortAscending ? result : -result;
      });

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SingleChildScrollView(
        child: Theme(
          data: Theme.of(context).copyWith(
            dataTableTheme: DataTableThemeData(
              headingRowColor: MaterialStateProperty.all(
                AppDesignSystem.primaryColor.withOpacity(0.1),
              ),
            ),
          ),
          child: DataTable(
            sortColumnIndex: _sortColumnIndex,
            sortAscending: _sortAscending,
            showCheckboxColumn: false,
            columns: [
              DataColumn(
                label: const Text('ID'),
                numeric: true,
                onSort: (index, ascending) => _sort(index, ascending),
              ),
              DataColumn(
                label: const Text('Customer Name'),
                onSort: (index, ascending) => _sort(index, ascending),
              ),
              DataColumn(
                label: const Text('Contact Person'),
                onSort: (index, ascending) => _sort(index, ascending),
              ),
              DataColumn(
                label: const Text('Email'),
                onSort: (index, ascending) => _sort(index, ascending),
              ),
              DataColumn(
                label: const Text('Credit Limit'),
                numeric: true,
                onSort: (index, ascending) => _sort(index, ascending),
              ),
              DataColumn(
                label: const Text('Status'),
                onSort: (index, ascending) => _sort(index, ascending),
              ),
            ],
            rows: sortedCustomers.asMap().entries.map((entry) {
              final index = entry.key;
              final customer = entry.value;
              final isSelected = _selectedIndex == index;

              return DataRow(
                selected: isSelected,
                onSelectChanged: (_) => _onRowSelected(index, customer),
                onLongPress: () => widget.onRowDoubleTap?.call(customer),
                cells: [
                  DataCell(Text(customer.customerId.toString())),
                  DataCell(Text(customer.customerName)),
                  DataCell(Text(customer.contactPerson ?? '')),
                  DataCell(Text(customer.email ?? '')),
                  DataCell(Text('\$${customer.creditLimit.toStringAsFixed(2)}')),
                  DataCell(
                    Chip(
                      label: Text(customer.status),
                      backgroundColor: customer.status == 'Active'
                          ? Colors.green.withOpacity(0.2)
                          : Colors.orange.withOpacity(0.2),
                    ),
                  ),
                ],
              );
            }).toList(),
          ),
        ),
      ),
    );
  }

  void _sort(int columnIndex, bool ascending) {
    setState(() {
      _sortColumnIndex = columnIndex;
      _sortAscending = ascending;
    });
  }

  void _onRowSelected(int index, Customer customer) {
    setState(() {
      _selectedIndex = _selectedIndex == index ? null : index;
    });
    widget.onSelectionChanged?.call(
      _selectedIndex != null ? customer : null,
    );
  }
}
```

#### Model: customer.dart

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'customer.freezed.dart';
part 'customer.g.dart';

@freezed
class Customer with _$Customer {
  const factory Customer({
    required int customerId,
    required String customerName,
    String? contactPerson,
    String? phone,
    String? email,
    String? address,
    String? city,
    String? country,
    @Default(0.0) double creditLimit,
    @Default('Active') String status,
    required DateTime createdDate,
  }) = _Customer;

  factory Customer.fromJson(Map<String, dynamic> json) =>
      _$CustomerFromJson(json);
}
```

#### Repository: customer_repository.dart

```dart
import '../models/customer.dart';

abstract class CustomerRepository {
  Future<List<Customer>> findAll();
  Future<Customer?> findById(int id);
  Future<Customer> create(Customer customer);
  Future<Customer> update(Customer customer);
  Future<void> delete(int id);
}

class SqlCustomerRepository implements CustomerRepository {
  final Database database;

  SqlCustomerRepository(this.database);

  @override
  Future<List<Customer>> findAll() async {
    final result = await database.query(
      'customers',
      orderBy: 'customer_name',
    );

    return result.map((row) => Customer.fromJson(row)).toList();
  }

  @override
  Future<Customer?> findById(int id) async {
    final result = await database.query(
      'customers',
      where: 'customer_id = ?',
      whereArgs: [id],
      limit: 1,
    );

    if (result.isEmpty) return null;
    return Customer.fromJson(result.first);
  }

  @override
  Future<Customer> create(Customer customer) async {
    final id = await database.insert(
      'customers',
      customer.toJson()..remove('customer_id'),
    );

    return customer.copyWith(customerId: id);
  }

  @override
  Future<Customer> update(Customer customer) async {
    await database.update(
      'customers',
      customer.toJson(),
      where: 'customer_id = ?',
      whereArgs: [customer.customerId],
    );

    return customer;
  }

  @override
  Future<void> delete(int id) async {
    await database.delete(
      'customers',
      where: 'customer_id = ?',
      whereArgs: [id],
    );
  }
}
```

## Conversion Summary

### Key Transformations

1. **Window → Screen**: The PowerBuilder window became a StatefulWidget screen
2. **DataWindow → DataTable**: The grid-style DataWindow became a sortable DataTable
3. **Instance Variables → State**: PowerBuilder instance variables became state properties
4. **Events → Methods**: PowerBuilder events became Flutter methods
5. **SQLCA → Repository**: Direct SQL became repository pattern
6. **MessageBox → Dialog**: PowerBuilder MessageBox became Flutter AlertDialog
7. **Transaction → async/await**: PowerBuilder Commit/Rollback became try-catch with async

### Architecture Improvements

1. **Separation of Concerns**: UI, business logic, and data access are separated
2. **Type Safety**: Strong typing with Dart and freezed models
3. **Reactive UI**: Flutter's reactive framework replaces imperative updates
4. **Modern Patterns**: Repository pattern, dependency injection, state management
5. **Error Handling**: Proper exception handling with user feedback

This example demonstrates how PowerBuilder's event-driven, database-centric approach transforms into Flutter's widget-based, reactive architecture while maintaining the same functionality and business logic.
