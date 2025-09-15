# PowerBuilder to Flutter Component Mapping

## Overview

This document outlines the mapping between PowerBuilder elements and their Flutter/Dart equivalents for the migration project. Understanding these mappings is crucial for generating appropriate Flutter models and widgets from PowerBuilder source code.

## Core Component Mappings

### 1. Windows and Dialogs

| PowerBuilder | Flutter Equivalent | Notes |
|--------------|-------------------|-------|
| Window (w_*) | `Scaffold` + `StatefulWidget` | Main application screens |
| Response Window | `Dialog` or `showDialog()` | Modal dialogs |
| MDI Frame | `Navigator` + nested `Scaffold` | Multi-document interface |
| MDI Sheet | Route/Page in `Navigator` | Child windows in MDI |
| Popup Window | `PopupMenuButton` or `showMenu()` | Context menus |

### 2. Visual Controls

| PowerBuilder | Flutter Equivalent | Notes |
|--------------|-------------------|-------|
| CommandButton | `ElevatedButton` or `TextButton` | Action buttons |
| StaticText | `Text` | Static labels |
| SingleLineEdit | `TextField` (single line) | Text input |
| MultiLineEdit | `TextField` (multiline) | Multi-line text input |
| DataWindow | `DataTable` or custom `ListView` | Complex data display |
| Picture | `Image` | Image display |
| PictureButton | `IconButton` or `ElevatedButton.icon()` | Button with image |
| CheckBox | `Checkbox` or `CheckboxListTile` | Boolean selection |
| RadioButton | `Radio` or `RadioListTile` | Single selection |
| DropDownListBox | `DropdownButton` | Dropdown selection |
| ListBox | `ListView` or `ListTile` | List selection |
| Tab | `TabBar` + `TabBarView` | Tabbed interface |
| GroupBox | `Container` with `InputDecorator` | Visual grouping |
| Line | `Divider` or `Container` with border | Visual separator |
| Rectangle | `Container` with decoration | Shape drawing |
| TreeView | `TreeView` (package) or custom | Hierarchical data |
| ListView | `ListView.builder` | List with columns |

### 3. DataWindow Components

| PowerBuilder DataWindow | Flutter Equivalent | Notes |
|------------------------|-------------------|-------|
| Grid DataWindow | `DataTable` or `GridView` | Tabular data display |
| Freeform DataWindow | Custom `Form` widget | Form-based data entry |
| Tabular DataWindow | `ListView` with `ListTile` | Row-based display |
| Graph DataWindow | `charts_flutter` package | Data visualization |
| Crosstab DataWindow | Custom widget or `DataTable` | Pivot table display |
| Composite DataWindow | `Column` with multiple widgets | Multiple data regions |
| RichText DataWindow | `RichText` or `flutter_html` | Formatted text display |

### 4. Data Access

| PowerBuilder | Flutter/Dart Equivalent | Notes |
|--------------|------------------------|-------|
| Transaction Object | Database connection class | Database connectivity |
| DataStore | Repository/Service class | Non-visual data handling |
| Embedded SQL | ORM queries (e.g., Drift, Floor) | Database queries |
| SQLCA | Database singleton | Global database connection |
| SQLDA | Dynamic query builder | Dynamic SQL |
| Cursor | `Stream` or `Future<List>` | Data iteration |

### 5. Non-Visual Objects

| PowerBuilder | Flutter/Dart Equivalent | Notes |
|--------------|------------------------|-------|
| Application Object | `MaterialApp` or `CupertinoApp` | App configuration |
| Menu | `AppBar` actions or `Drawer` | Navigation menus |
| User Object (nvo) | Dart class | Business logic |
| Structure | Dart class with fields | Data structures |
| Global Functions | Top-level Dart functions | Utility functions |
| Instance Variables | Class fields | Object state |
| Shared Variables | Static class fields | Shared state |

### 6. Events and Methods

| PowerBuilder | Flutter/Dart Equivalent | Notes |
|--------------|------------------------|-------|
| Clicked event | `onPressed` callback | Button actions |
| Constructor event | Constructor method | Object initialization |
| Destructor event | `dispose()` method | Cleanup |
| Open event | `initState()` method | Widget initialization |
| Close event | `dispose()` method | Widget cleanup |
| ItemChanged event | `onChanged` callback | Value changes |
| RowFocusChanged | `onTap` in ListView | Row selection |
| Key events | `RawKeyboardListener` | Keyboard input |
| Timer event | `Timer` class | Periodic actions |

### 7. PowerScript to Dart

| PowerScript Feature | Dart Equivalent | Notes |
|--------------------|----------------|-------|
| Integer, Long | `int` | Numeric types |
| Decimal, Real | `double` | Floating point |
| String | `String` | Text data |
| Boolean | `bool` | True/false |
| Date, DateTime | `DateTime` | Date/time handling |
| Time | `TimeOfDay` or `DateTime` | Time representation |
| Any | `dynamic` or `Object?` | Dynamic typing |
| Arrays | `List<T>` | Collections |
| Structures | Classes | Custom types |
| NULL | `null` | Null value |
| CHOOSE CASE | `switch` statement | Conditional logic |
| FOR...NEXT | `for` loop | Iteration |
| DO...LOOP | `while` or `do-while` | Loops |
| TRY...CATCH | `try-catch` | Exception handling |

### 8. DataWindow SQL to Model Generation

DataWindow SQL should be parsed to generate:

1. **Entity Classes**: Dart classes representing database tables
   ```dart
   class Patient {
     final int patientId;
     final String firstName;
     final String lastName;
     // ... other fields
   }
   ```

2. **Repository Interfaces**: Data access abstractions
   ```dart
   abstract class PatientRepository {
     Future<List<Patient>> findAll();
     Future<Patient?> findById(int id);
     Future<void> save(Patient patient);
   }
   ```

3. **DTO Classes**: Data transfer objects for complex queries
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

## Next Steps

1. Fix DataWindow extraction to properly parse SQL definitions
2. Create code generators for each mapping category
3. Build a prototype converter for simple windows
4. Develop custom widgets for complex DataWindow types
5. Implement PowerScript to Dart transpiler
