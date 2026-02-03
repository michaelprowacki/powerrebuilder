"""Flutter generator with FFI support and cross-architecture portability."""

from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path

from src_new._core.result import Result, Success, Failure
from .portable_patterns import (
    PortablePatternConfig,
    PortablePatternGenerator,
)


@dataclass(frozen=True)
class FlutterGeneratorConfig:
    """Configuration for Flutter application generation."""

    app_name: str
    app_title: str
    package_name: str
    version: str = "0.1.0"
    enable_ffi: bool = True
    enable_portability: bool = True
    target_platforms: List[str] = None
    use_rust_backend: bool = True

    def __post_init__(self):
        if self.target_platforms is None:
            object.__setattr__(
                self,
                "target_platforms",
                ["ios", "android", "windows", "macos", "linux"],
            )


class FlutterGenerator:
    """Generates Flutter applications with FFI and cross-platform support."""

    def __init__(self):
        """Initialize Flutter generator."""
        self.portable_gen = PortablePatternGenerator()

    def generate_main_dart(
        self, config: FlutterGeneratorConfig, domain_model: Dict[str, Any]
    ) -> Result[str, str]:
        """Generate main.dart with FFI integration."""
        try:
            ffi_imports = (
                """
import 'dart:ffi';
import 'package:ffi/ffi.dart';
import 'ffi/bindings.dart';
import 'ffi/runtime.dart';"""
                if config.enable_ffi
                else ""
            )

            content = f"""import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
{ffi_imports}

import 'models/domain.dart';
import 'services/state_manager.dart';
import 'ui/app_theme.dart';
import 'ui/screens/home_screen.dart';

void main() {{
  {"initializeFFI();" if config.enable_ffi else ""}
  runApp(MyApp());
}}

{"void initializeFFI() {" if config.enable_ffi else ""}
{"  final runtime = PowerBuilderRuntime();" if config.enable_ffi else ""}
{'  print("FFI initialized on ${runtime.platformInfo.archName}");' if config.enable_ffi else ""}
{"}" if config.enable_ffi else ""}

class MyApp extends StatelessWidget {{
  @override
  Widget build(BuildContext context) {{
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => StateManager()),
        {"Provider.value(value: PowerBuilderRuntime())," if config.enable_ffi else ""}
      ],
      child: MaterialApp(
        title: '{config.app_title}',
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        home: HomeScreen(),
      ),
    );
  }}
}}
"""
            return Success(content)

        except Exception as e:
            return Failure(f"Failed to generate main.dart: {e}")

    def generate_ffi_runtime(
        self, config: FlutterGeneratorConfig, domain_model: Dict[str, Any]
    ) -> Result[str, str]:
        """Generate FFI runtime wrapper for Flutter."""
        try:
            content = f"""import 'dart:ffi';
import 'dart:io' show Platform;
import 'dart:typed_data';
import 'dart:convert';
import 'package:ffi/ffi.dart';

import 'bindings.dart';

/// High-level runtime wrapper for FFI bindings
class FFIRuntime {{
  static final FFIRuntime _instance = FFIRuntime._();
  factory FFIRuntime() => _instance;

  late final PowerBuilderRuntime _pbRuntime;

  FFIRuntime._() {{
    _pbRuntime = PowerBuilderRuntime();
    _initialize();
    _initializeFFIFunctions();
  }}

  void _initialize() {{
    // Platform-specific initialization
    if (Platform.isIOS) {{
      // iOS-specific setup
    }} else if (Platform.isAndroid) {{
      // Android-specific setup
    }}
  }}

  // ============================================================================
  // FFI FUNCTION DECLARATIONS
  // ============================================================================

  // Native function pointers (linked from Rust library)
  late final Pointer<NativeFunction<Pointer<Uint8> Function(Uint64)>> _loadEntityNativePtr;
  late final Pointer<Uint8> Function(int) _loadEntityNative;

  late final Pointer<NativeFunction<Void Function(Uint64, Pointer<Uint8>, Uint32)>> _saveEntityNativePtr;
  late final void Function(int, Pointer<Uint8>, int) _saveEntityNative;

  late final Pointer<NativeFunction<Pointer<Uint8> Function(Pointer<Uint8>, Uint32)>> _queryEntitiesNativePtr;
  late final Pointer<Uint8> Function(Pointer<Uint8>, int) _queryEntitiesNative;

  void _initializeFFIFunctions() {{
    // Load function pointers from native library
    final dylib = _pbRuntime._nativeLib;

    _loadEntityNativePtr = dylib.lookup('pb_load_entity');
    _loadEntityNative = _loadEntityNativePtr.asFunction();

    _saveEntityNativePtr = dylib.lookup('pb_save_entity');
    _saveEntityNative = _saveEntityNativePtr.asFunction();

    _queryEntitiesNativePtr = dylib.lookup('pb_query_entities');
    _queryEntitiesNative = _queryEntitiesNativePtr.asFunction();
  }}

  // ============================================================================
  // DOMAIN OPERATIONS (Using FFI)
  // ============================================================================

  {self._generate_ffi_operations(domain_model)}

  // ============================================================================
  // CROSS-ARCHITECTURE DATA CONVERSION
  // ============================================================================

  {self._generate_data_converters()}

  // ============================================================================
  // ERROR HANDLING
  // ============================================================================

  String? getLastError() {{
    return _pbRuntime.getLastErrorMessage();
  }}

  T executeWithErrorHandling<T>(T Function() operation, String operationName) {{
    try {{
      final result = operation();
      return result;
    }} catch (e) {{
      final error = getLastError();
      throw FFIException('$operationName failed: ${{error ?? e.toString()}}');
    }}
  }}
}}

class FFIException implements Exception {{
  final String message;
  FFIException(this.message);

  @override
  String toString() => 'FFIException: $message';
}}
"""
            return Success(content)

        except Exception as e:
            return Failure(f"Failed to generate FFI runtime: {e}")

    def _generate_ffi_operations(self, domain_model: Dict[str, Any]) -> str:
        """Generate FFI operations for domain model."""
        operations = []

        # Entity CRUD operations
        operations.append("""
  Future<Entity?> loadEntity(int id) async {
    return executeWithErrorHandling(() {
      final data = _loadEntityNative(id);
      if (data == nullptr) return null;

      final reader = PortableBinaryReader(data.asTypedList(data.length));
      return Entity.fromBinary(reader);
    }, 'loadEntity');
  }

  Future<void> saveEntity(Entity entity) async {
    return executeWithErrorHandling(() {
      final writer = PortableBinaryWriter();
      entity.writeToBinary(writer);
      final data = writer.toBytes();

      _saveEntityNative(entity.id, data);
    }, 'saveEntity');
  }

  Future<List<Entity>> queryEntities(QueryParams params) async {
    return executeWithErrorHandling(() {
      final writer = PortableBinaryWriter();
      params.writeToBinary(writer);
      final queryData = writer.toBytes();

      final resultPtr = _queryEntitiesNative(queryData);
      if (resultPtr == nullptr) return [];

      final reader = PortableBinaryReader(resultPtr.asTypedList(resultPtr.length));
      final count = reader.readUint32LE();

      final entities = <Entity>[];
      for (int i = 0; i < count; i++) {
        entities.add(Entity.fromBinary(reader));
      }

      return entities;
    }, 'queryEntities');
  }""")

        # Window operations if needed
        if any("window" in str(obj).lower() for obj in domain_model.get("objects", [])):
            operations.append("""
  WindowHandle createWindow({
    int parentId = 0,
    int x = 0,
    int y = 0,
    int width = 800,
    int height = 600,
  }) {
    return executeWithErrorHandling(() {
      final ptr = _pbRuntime.createWindow(
        parentId: parentId,
        x: x,
        y: y,
        width: width,
        height: height,
      );
      return WindowHandle.fromPointer(ptr);
    }, 'createWindow');
  }

  void destroyWindow(WindowHandle window) {
    executeWithErrorHandling(() {
      _pbRuntime.destroyWindow(window.pointer);
    }, 'destroyWindow');
  }""")

        # DataWindow operations if present
        if any(
            "datawindow" in str(obj).lower() for obj in domain_model.get("objects", [])
        ):
            operations.append("""
  Future<DataWindowContent> loadDataWindow(String name) async {
    return executeWithErrorHandling(() async {
      final data = await _loadDataWindowNative(name);
      if (data == nullptr) {
        throw FFIException('DataWindow $name not found');
      }

      final reader = PortableBinaryReader(data.asTypedList(data.length));
      return DataWindowContent.fromBinary(reader);
    }, 'loadDataWindow');
  }""")

        return "\n".join(operations)

    def _generate_data_converters(self) -> str:
        """Generate cross-architecture data converters."""
        return """
  /// Convert Dart types to PowerBuilder binary format
  Uint8List convertToPowerBuilderFormat(dynamic data) {
    final writer = PortableBinaryWriter();

    if (data is String) {
      writer.writeString(data);
    } else if (data is int) {
      writer.writeInt32LE(data);
    } else if (data is double) {
      writer.writeUint64LE(data.toInt());  // Store as fixed-point
    } else if (data is List) {
      writer.writeUint32LE(data.length);
      for (final item in data) {
        final itemBytes = convertToPowerBuilderFormat(item);
        writer.writeBytes(itemBytes);
      }
    } else if (data is Map) {
      final json = jsonEncode(data);
      writer.writeString(json);
    }

    return writer.toBytes();
  }

  /// Convert PowerBuilder binary format to Dart types
  dynamic convertFromPowerBuilderFormat(Uint8List data, String type) {
    final reader = PortableBinaryReader(data);

    switch (type) {
      case 'string':
        final length = reader.readUint16LE();
        final bytes = reader.readBytes(length);
        return utf8.decode(bytes);

      case 'int':
        return reader.readInt32LE();

      case 'double':
        final fixed = reader.readUint64LE();
        return fixed / 10000.0;  // Convert from fixed-point

      case 'list':
        final count = reader.readUint32LE();
        final items = [];
        for (int i = 0; i < count; i++) {
          // Recursive conversion
          items.add(convertFromPowerBuilderFormat(
            reader.readBytes(reader.readUint32LE()),
            'auto'
          ));
        }
        return items;

      case 'map':
        final jsonStr = convertFromPowerBuilderFormat(data, 'string');
        return jsonDecode(jsonStr);

      default:
        return data;
    }
  }"""

    def generate_domain_models(
        self, config: FlutterGeneratorConfig, domain_model: Dict[str, Any]
    ) -> Result[str, str]:
        """Generate domain models with FFI support."""
        try:
            content = """import 'dart:typed_data';
import 'package:json_annotation/json_annotation.dart';

import '../ffi/bindings.dart';

part 'domain.g.dart';

// ============================================================================
// DOMAIN ENTITIES
// ============================================================================

@JsonSerializable()
class Entity {
  final int id;
  final String name;
  final EntityData data;
  final DateTime createdAt;
  final DateTime updatedAt;

  Entity({
    required this.id,
    required this.name,
    required this.data,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Entity.fromJson(Map<String, dynamic> json) =>
      _$EntityFromJson(json);

  Map<String, dynamic> toJson() => _$EntityToJson(this);

  // Binary serialization for FFI
  factory Entity.fromBinary(PortableBinaryReader reader) {
    final id = reader.readUint32LE();
    final nameLength = reader.readUint16LE();
    final nameBytes = reader.readBytes(nameLength);
    final name = String.fromCharCodes(nameBytes);

    // Read nested data
    final dataLength = reader.readUint32LE();
    final dataBytes = reader.readBytes(dataLength);
    final dataReader = PortableBinaryReader(dataBytes);
    final data = EntityData.fromBinary(dataReader);

    final createdAt = DateTime.fromMillisecondsSinceEpoch(reader.readUint64LE());
    final updatedAt = DateTime.fromMillisecondsSinceEpoch(reader.readUint64LE());

    return Entity(
      id: id,
      name: name,
      data: data,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }

  void writeToBinary(PortableBinaryWriter writer) {
    writer.writeUint32LE(id);
    writer.writeString(name);

    // Write nested data
    final dataWriter = PortableBinaryWriter();
    data.writeToBinary(dataWriter);
    final dataBytes = dataWriter.toBytes();
    writer.writeUint32LE(dataBytes.length);
    writer.writeBytes(dataBytes);

    writer.writeUint64LE(createdAt.millisecondsSinceEpoch);
    writer.writeUint64LE(updatedAt.millisecondsSinceEpoch);
  }
}

@JsonSerializable()
class EntityData {
  final Map<String, dynamic> fields;

  EntityData({required this.fields});

  factory EntityData.fromJson(Map<String, dynamic> json) =>
      _$EntityDataFromJson(json);

  Map<String, dynamic> toJson() => _$EntityDataToJson(this);

  factory EntityData.fromBinary(PortableBinaryReader reader) {
    final fieldCount = reader.readUint16LE();
    final fields = <String, dynamic>{};

    for (int i = 0; i < fieldCount; i++) {
      final keyLength = reader.readUint16LE();
      final keyBytes = reader.readBytes(keyLength);
      final key = String.fromCharCodes(keyBytes);

      final valueType = reader.readUint8();
      final value = _readFieldValue(reader, valueType);

      fields[key] = value;
    }

    return EntityData(fields: fields);
  }

  void writeToBinary(PortableBinaryWriter writer) {
    writer.writeUint16LE(fields.length);

    for (final entry in fields.entries) {
      writer.writeString(entry.key);
      _writeFieldValue(writer, entry.value);
    }
  }

  static dynamic _readFieldValue(PortableBinaryReader reader, int type) {
    switch (type) {
      case 0: // String
        final length = reader.readUint16LE();
        final bytes = reader.readBytes(length);
        return String.fromCharCodes(bytes);
      case 1: // Int
        return reader.readInt32LE();
      case 2: // Double
        return reader.readUint64LE() / 10000.0;
      case 3: // Bool
        return reader.readUint8() != 0;
      default:
        throw Exception('Unknown field type: $type');
    }
  }

  static void _writeFieldValue(PortableBinaryWriter writer, dynamic value) {
    if (value is String) {
      writer.writeUint8(0);
      writer.writeString(value);
    } else if (value is int) {
      writer.writeUint8(1);
      writer.writeInt32LE(value);
    } else if (value is double) {
      writer.writeUint8(2);
      writer.writeUint64LE((value * 10000).toInt());
    } else if (value is bool) {
      writer.writeUint8(3);
      writer.writeUint8(value ? 1 : 0);
    } else {
      throw Exception('Unsupported field type: ${value.runtimeType}');
    }
  }
}

// ============================================================================
// QUERY PARAMETERS
// ============================================================================

@JsonSerializable()
class QueryParams {
  final String? filter;
  final String? orderBy;
  final int? limit;
  final int? offset;

  QueryParams({
    this.filter,
    this.orderBy,
    this.limit,
    this.offset,
  });

  factory QueryParams.fromJson(Map<String, dynamic> json) =>
      _$QueryParamsFromJson(json);

  Map<String, dynamic> toJson() => _$QueryParamsToJson(this);

  void writeToBinary(PortableBinaryWriter writer) {
    writer.writeUint8(filter != null ? 1 : 0);
    if (filter != null) writer.writeString(filter!);

    writer.writeUint8(orderBy != null ? 1 : 0);
    if (orderBy != null) writer.writeString(orderBy!);

    writer.writeUint8(limit != null ? 1 : 0);
    if (limit != null) writer.writeUint32LE(limit!);

    writer.writeUint8(offset != null ? 1 : 0);
    if (offset != null) writer.writeUint32LE(offset!);
  }
}

// ============================================================================
// WINDOW HANDLES (for FFI)
// ============================================================================

class WindowHandle {
  final Pointer<PBWindowHandle> pointer;

  WindowHandle.fromPointer(this.pointer);

  int get id => pointer.ref.id;
  int get parentId => pointer.ref.parentId;
  int get x => pointer.ref.x;
  int get y => pointer.ref.y;
  int get width => pointer.ref.width;
  int get height => pointer.ref.height;
}
"""
            return Success(content)

        except Exception as e:
            return Failure(f"Failed to generate domain models: {e}")

    def generate_state_manager(
        self, config: FlutterGeneratorConfig, domain_model: Dict[str, Any]
    ) -> Result[str, str]:
        """Generate state management with FFI integration."""
        try:
            content = f"""import 'package:flutter/foundation.dart';
import 'dart:async';

import '../models/domain.dart';
{'import "../ffi/runtime.dart";' if config.enable_ffi else ""}

/// Functional state management with effects
class StateManager extends ChangeNotifier {{
  {"final FFIRuntime _ffi = FFIRuntime();" if config.enable_ffi else ""}

  // State
  final List<Entity> _entities = [];
  final List<Effect> _pendingEffects = [];
  bool _isLoading = false;
  String? _error;

  // Getters
  List<Entity> get entities => List.unmodifiable(_entities);
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasError => _error != null;

  // ============================================================================
  // COMMANDS (Pure Functions)
  // ============================================================================

  Future<void> dispatch(Command command) async {{
    try {{
      _setLoading(true);
      _clearError();

      // Process command and get effects
      final effects = await _processCommand(command);

      // Add to pending effects
      _pendingEffects.addAll(effects);

      // Interpret effects (I/O at edges)
      await _interpretEffects(effects);

    }} catch (e) {{
      _setError(e.toString());
    }} finally {{
      _setLoading(false);
    }}
  }}

  Future<List<Effect>> _processCommand(Command command) async {{
    switch (command.type) {{
      case CommandType.create:
        return _handleCreate(command.data as EntityData);

      case CommandType.update:
        return _handleUpdate(command.id!, command.data as EntityData);

      case CommandType.delete:
        return _handleDelete(command.id!);

      case CommandType.query:
        return _handleQuery(command.params as QueryParams);

      default:
        return [Effect.none()];
    }}
  }}

  // ============================================================================
  // COMMAND HANDLERS (Return Effects)
  // ============================================================================

  Future<List<Effect>> _handleCreate(EntityData data) async {{
    final entity = Entity(
      id: DateTime.now().millisecondsSinceEpoch,
      name: data.fields['name'] ?? 'Unnamed',
      data: data,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    return [
      Effect.addToState(entity),
      {
                "Effect.persistToFFI(entity),"
                if config.enable_ffi
                else "Effect.persistToLocal(entity),"
            }
      Effect.log('Created entity ${{entity.id}}'),
    ];
  }}

  Future<List<Effect>> _handleUpdate(int id, EntityData data) async {{
    final index = _entities.indexWhere((e) => e.id == id);
    if (index == -1) {{
      return [Effect.error('Entity $id not found')];
    }}

    final oldEntity = _entities[index];
    final updatedEntity = Entity(
      id: oldEntity.id,
      name: data.fields['name'] ?? oldEntity.name,
      data: data,
      createdAt: oldEntity.createdAt,
      updatedAt: DateTime.now(),
    );

    return [
      Effect.updateInState(index, updatedEntity),
      {
                "Effect.persistToFFI(updatedEntity),"
                if config.enable_ffi
                else "Effect.persistToLocal(updatedEntity),"
            }
      Effect.log('Updated entity $id'),
    ];
  }}

  Future<List<Effect>> _handleDelete(int id) async {{
    final index = _entities.indexWhere((e) => e.id == id);
    if (index == -1) {{
      return [Effect.error('Entity $id not found')];
    }}

    return [
      Effect.removeFromState(index),
      {
                "Effect.deleteFromFFI(id),"
                if config.enable_ffi
                else "Effect.deleteFromLocal(id),"
            }
      Effect.log('Deleted entity $id'),
    ];
  }}

  Future<List<Effect>> _handleQuery(QueryParams params) async {{
    return [
      {
                "Effect.queryFromFFI(params),"
                if config.enable_ffi
                else "Effect.queryFromLocal(params),"
            }
      Effect.log('Querying with params: ${{params.toJson()}}'),
    ];
  }}

  // ============================================================================
  // EFFECT INTERPRETER (I/O at Edges)
  // ============================================================================

  Future<void> _interpretEffects(List<Effect> effects) async {{
    for (final effect in effects) {{
      await _interpretEffect(effect);
    }}
  }}

  Future<void> _interpretEffect(Effect effect) async {{
    switch (effect.type) {{
      case EffectType.addToState:
        _entities.add(effect.data as Entity);
        notifyListeners();
        break;

      case EffectType.updateInState:
        final update = effect.data as StateUpdate;
        _entities[update.index] = update.entity;
        notifyListeners();
        break;

      case EffectType.removeFromState:
        _entities.removeAt(effect.data as int);
        notifyListeners();
        break;

      {
                "case EffectType.persistToFFI:"
                if config.enable_ffi
                else "case EffectType.persistToLocal:"
            }
        {
                "await _ffi.saveEntity(effect.data as Entity);"
                if config.enable_ffi
                else "await _saveToLocal(effect.data as Entity);"
            }
        break;

      {
                "case EffectType.deleteFromFFI:"
                if config.enable_ffi
                else "case EffectType.deleteFromLocal:"
            }
        {
                "// FFI delete handled by native code"
                if config.enable_ffi
                else "await _deleteFromLocal(effect.data as int);"
            }
        break;

      {
                "case EffectType.queryFromFFI:"
                if config.enable_ffi
                else "case EffectType.queryFromLocal:"
            }
        {
                "final results = await _ffi.queryEntities(effect.data as QueryParams);"
                if config.enable_ffi
                else "final results = await _queryFromLocal(effect.data as QueryParams);"
            }
        _entities.clear();
        _entities.addAll(results);
        notifyListeners();
        break;

      case EffectType.log:
        debugPrint('[StateManager] ${{effect.data}}');
        break;

      case EffectType.error:
        _setError(effect.data as String);
        break;

      case EffectType.none:
        break;
    }}
  }}

  // ============================================================================
  // HELPER METHODS
  // ============================================================================

  void _setLoading(bool value) {{
    _isLoading = value;
    notifyListeners();
  }}

  void _setError(String? error) {{
    _error = error;
    notifyListeners();
  }}

  void _clearError() {{
    _error = null;
  }}

  {
                ""
                if config.enable_ffi
                else '''
  // Local storage implementations (when FFI is disabled)
  Future<void> _saveToLocal(Entity entity) async {
    // Implementation for local storage
  }

  Future<void> _deleteFromLocal(int id) async {
    // Implementation for local storage
  }

  Future<List<Entity>> _queryFromLocal(QueryParams params) async {
    // Implementation for local storage
    return [];
  }'''
            }
}}

// ============================================================================
// COMMAND AND EFFECT TYPES
// ============================================================================

enum CommandType {{ create, update, delete, query }}

class Command {{
  final CommandType type;
  final int? id;
  final dynamic data;
  final QueryParams? params;

  Command.create(EntityData data)
      : type = CommandType.create,
        id = null,
        data = data,
        params = null;

  Command.update(int id, EntityData data)
      : type = CommandType.update,
        id = id,
        data = data,
        params = null;

  Command.delete(int id)
      : type = CommandType.delete,
        id = id,
        data = null,
        params = null;

  Command.query(QueryParams params)
      : type = CommandType.query,
        id = null,
        data = null,
        params = params;
}}

enum EffectType {{
  addToState,
  updateInState,
  removeFromState,
  {"persistToFFI," if config.enable_ffi else "persistToLocal,"}
  {"deleteFromFFI," if config.enable_ffi else "deleteFromLocal,"}
  {"queryFromFFI," if config.enable_ffi else "queryFromLocal,"}
  log,
  error,
  none,
}}

class Effect {{
  final EffectType type;
  final dynamic data;

  Effect._(this.type, this.data);

  factory Effect.addToState(Entity entity) =>
      Effect._(EffectType.addToState, entity);

  factory Effect.updateInState(int index, Entity entity) =>
      Effect._(EffectType.updateInState, StateUpdate(index, entity));

  factory Effect.removeFromState(int index) =>
      Effect._(EffectType.removeFromState, index);

  {
                "factory Effect.persistToFFI(Entity entity) =>"
                if config.enable_ffi
                else "factory Effect.persistToLocal(Entity entity) =>"
            }
      {
                "Effect._(EffectType.persistToFFI, entity);"
                if config.enable_ffi
                else "Effect._(EffectType.persistToLocal, entity);"
            }

  {
                "factory Effect.deleteFromFFI(int id) =>"
                if config.enable_ffi
                else "factory Effect.deleteFromLocal(int id) =>"
            }
      {
                "Effect._(EffectType.deleteFromFFI, id);"
                if config.enable_ffi
                else "Effect._(EffectType.deleteFromLocal, id);"
            }

  {
                "factory Effect.queryFromFFI(QueryParams params) =>"
                if config.enable_ffi
                else "factory Effect.queryFromLocal(QueryParams params) =>"
            }
      {
                "Effect._(EffectType.queryFromFFI, params);"
                if config.enable_ffi
                else "Effect._(EffectType.queryFromLocal, params);"
            }

  factory Effect.log(String message) => Effect._(EffectType.log, message);

  factory Effect.error(String error) => Effect._(EffectType.error, error);

  factory Effect.none() => Effect._(EffectType.none, null);
}}

class StateUpdate {{
  final int index;
  final Entity entity;

  StateUpdate(this.index, this.entity);
}}
"""
            return Success(content)

        except Exception as e:
            return Failure(f"Failed to generate state manager: {e}")

    def generate_flutter_app(
        self,
        config: FlutterGeneratorConfig,
        domain_model: Dict[str, Any],
        output_dir: Path,
    ) -> Result[Dict[str, Path], str]:
        """Generate complete Flutter application with FFI support."""
        output_dir = Path(output_dir)
        lib_dir = output_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        # Generate main.dart
        main_result = self.generate_main_dart(config, domain_model)
        if main_result.is_success:
            main_path = lib_dir / "main.dart"
            main_path.write_text(main_result.value)
            generated_files["main.dart"] = main_path
        else:
            return Failure(main_result.error)

        # Generate FFI files if enabled
        if config.enable_ffi:
            ffi_dir = lib_dir / "ffi"
            ffi_dir.mkdir(exist_ok=True)

            # Generate FFI bindings from template
            portable_config = PortablePatternConfig(
                app_name=config.app_name,
                version=config.version,
                target_type="flutter",
                enable_ffi=True,
            )

            bindings_result = self.portable_gen.generate_flutter_ffi_bindings(
                portable_config
            )
            if bindings_result.is_success:
                bindings_path = ffi_dir / "bindings.dart"
                bindings_path.write_text(bindings_result.value)
                generated_files["bindings.dart"] = bindings_path

            # Generate FFI runtime
            runtime_result = self.generate_ffi_runtime(config, domain_model)
            if runtime_result.is_success:
                runtime_path = ffi_dir / "runtime.dart"
                runtime_path.write_text(runtime_result.value)
                generated_files["runtime.dart"] = runtime_path

        # Generate domain models
        models_dir = lib_dir / "models"
        models_dir.mkdir(exist_ok=True)

        models_result = self.generate_domain_models(config, domain_model)
        if models_result.is_success:
            models_path = models_dir / "domain.dart"
            models_path.write_text(models_result.value)
            generated_files["domain.dart"] = models_path

        # Generate state manager
        services_dir = lib_dir / "services"
        services_dir.mkdir(exist_ok=True)

        state_result = self.generate_state_manager(config, domain_model)
        if state_result.is_success:
            state_path = services_dir / "state_manager.dart"
            state_path.write_text(state_result.value)
            generated_files["state_manager.dart"] = state_path

        # Generate Rust FFI library if needed
        if config.use_rust_backend:
            rust_result = self._generate_rust_ffi_library(
                config, domain_model, output_dir
            )
            if rust_result.is_failure:
                return Failure(
                    f"Failed to generate Rust FFI library: {rust_result.error}"
                )
            generated_files.update(rust_result.value)

        # Generate pubspec.yaml
        pubspec = self._generate_pubspec(config)
        pubspec_path = output_dir / "pubspec.yaml"
        pubspec_path.write_text(pubspec)
        generated_files["pubspec.yaml"] = pubspec_path

        return Success(generated_files)

    def _generate_rust_ffi_library(
        self,
        config: FlutterGeneratorConfig,
        domain_model: Dict[str, Any],
        output_dir: Path,
    ) -> Result[Dict[str, Path], str]:
        """Generate Rust FFI library for Flutter."""
        rust_dir = output_dir / "rust"
        rust_dir.mkdir(exist_ok=True)

        generated_files = {}

        # Generate portable Rust files
        portable_config = PortablePatternConfig(
            app_name=f"{config.app_name}_lib",
            version=config.version,
            target_type="flutter",
            functional_style=True,
        )

        portable_result = self.portable_gen.generate_all_portable_files(
            portable_config, rust_dir, domain_model
        )

        if portable_result.is_failure:
            return Failure(portable_result.error)

        generated_files.update(portable_result.value)

        return Success(generated_files)

    def _generate_pubspec(self, config: FlutterGeneratorConfig) -> str:
        """Generate pubspec.yaml."""
        ffi_deps = (
            """
  ffi: ^2.1.0
  flutter_rust_bridge: ^2.0.0"""
            if config.enable_ffi
            else ""
        )

        return f"""name: {config.app_name}
description: {config.app_title}
version: {config.version}
publish_to: 'none'

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  provider: ^6.1.0
  json_annotation: ^4.8.0{ffi_deps}

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.0
  json_serializable: ^6.7.0
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
"""
