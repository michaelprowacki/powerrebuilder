# PowerRebuilder Codebase Import Analysis
==================================================

## Summary
- Total Python files analyzed: 289
- Broken imports found: 134
- Circular dependencies found: 2

## Module Breakdown

### __INIT__.PY Module
- Files: 1

### COMMON Module
- Files: 21
- Top imported modules:
  - typing: 30 imports
  - rich: 30 imports
  - src: 27 imports
  - time: 12 imports
  - collections: 12 imports

### CONTRACTS Module
- Files: 4
- Top imported modules:
  - typing: 13 imports
  - logging: 6 imports
  - collections: 5 imports
  - types: 5 imports
  - interfaces: 3 imports

### CORE Module
- Files: 16
- Top imported modules:
  - typing: 27 imports
  - src: 18 imports
  - pathlib: 14 imports
  - collections: 14 imports
  - logging: 11 imports

### DECOMPILE Module
- Files: 54
- Top imported modules:
  - src: 138 imports
  - typing: 62 imports
  - dataclasses: 46 imports
  - logging: 38 imports
  - rich: 34 imports

### EXTRACT Module
- Files: 50
- Top imported modules:
  - src: 195 imports
  - typing: 60 imports
  - logging: 38 imports
  - pathlib: 33 imports
  - struct: 17 imports

### GENERATE Module
- Files: 53
- Top imported modules:
  - src: 96 imports
  - typing: 45 imports
  - logging: 36 imports
  - dataclasses: 29 imports
  - re: 24 imports

### MODEL Module
- Files: 59
- Top imported modules:
  - src: 107 imports
  - typing: 70 imports
  - dataclasses: 45 imports
  - __future__: 30 imports
  - enum: 25 imports

### PARSE Module
- Files: 31
- Top imported modules:
  - src: 133 imports
  - lark: 34 imports
  - typing: 31 imports
  - logging: 18 imports
  - pathlib: 15 imports

## 🚨 BROKEN IMPORTS (134 issues)

### `analysis.control` (used in 1 files)
- `src/decompile/coordinator.py:57` (from_import)

### `analyzers.parser` (used in 1 files)
- `src/decompile/coordinator.py:58` (from_import)

### `analyzers.schema_generator` (used in 1 files)
- `src/decompile/coordinator.py:59` (from_import)

### `application` (used in 2 files)
- `src/model/entities/__init__.py:3` (from_import)
- `src/generate/converters/logic/__init__.py:3` (from_import)

### `ast_processor` (used in 1 files)
- `src/model/services/__init__.py:5` (from_import)

### `ast_tree_visitor` (used in 1 files)
- `src/model/visitors/__init__.py:8` (from_import)

### `ast_walker` (used in 1 files)
- `src/model/visitors/__init__.py:7` (from_import)

### `base` (used in 24 files)
- `src/parse/parser/powerbuilder.py:22` (from_import)
- `src/parse/parser/sql.py:21` (from_import)
- `src/common/pipeline/__init__.py:7` (from_import)
- `src/common/pipeline/__init__.py:7` (from_import)
- `src/common/pipeline/__init__.py:7` (from_import)
- `src/common/coordinators/__init__.py:3` (from_import)
- `src/model/types/__init__.py:3` (from_import)
- `src/model/types/__init__.py:3` (from_import)
- `src/model/utils/__init__.py:5` (from_import)
- `src/model/ast/nodes/__init__.py:6` (from_import)
- ... and 14 more files

### `blobs` (used in 1 files)
- `src/generate/converters/data/__init__.py:3` (from_import)

### `celery` (used in 2 files)
- `src/core/distributed.py:28` (from_import)
- `src/core/distributed.py:382` (from_import)

### `context_recovery` (used in 1 files)
- `src/decompile/reconstruction/enhanced_reconstructor.py:17` (from_import)

### `converters.data.db_formatter` (used in 1 files)
- `src/generate/factory.py:16` (from_import)

### `converters.flutter.design_system` (used in 1 files)
- `src/generate/factory.py:17` (from_import)

### `converters.flutter.layouts` (used in 2 files)
- `src/generate/coordinator.py:49` (from_import)
- `src/generate/coordinator.py:49` (from_import)

### `converters.flutter.models` (used in 1 files)
- `src/generate/coordinator.py:50` (from_import)

### `converters.flutter.widgets` (used in 1 files)
- `src/generate/coordinator.py:51` (from_import)

### `converters.utils.ast` (used in 1 files)
- `src/generate/coordinator.py:52` (from_import)

### `converters.utils.types` (used in 1 files)
- `src/generate/factory.py:18` (from_import)

### `coordinator` (used in 3 files)
- `src/parse/factory.py:21` (from_import)
- `src/generate/factory.py:19` (from_import)
- `src/extract/__init__.py:10` (from_import)

### `data_block` (used in 3 files)
- `src/extract/pbd/object.py:13` (from_import)
- `src/extract/pbd/object.py:13` (from_import)
- `src/extract/pbd/object.py:13` (from_import)

### `datawindow` (used in 7 files)
- `src/decompile/extractors/__init__.py:10` (from_import)
- `src/decompile/extractors/__init__.py:10` (from_import)
- `src/decompile/extractors/__init__.py:10` (from_import)
- `src/decompile/extractors/__init__.py:10` (from_import)
- `src/decompile/extractors/__init__.py:10` (from_import)
- `src/decompile/extractors/__init__.py:10` (from_import)
- `src/decompile/extractors/__init__.py:18` (from_import)

### `datawindow_extractor` (used in 7 files)
- `src/decompile/extractors/__init__.py:21` (from_import)
- `src/decompile/extractors/__init__.py:21` (from_import)
- `src/decompile/extractors/__init__.py:21` (from_import)
- `src/decompile/extractors/__init__.py:21` (from_import)
- `src/decompile/extractors/__init__.py:21` (from_import)
- `src/decompile/extractors/__init__.py:21` (from_import)
- `src/decompile/extractors/__init__.py:21` (from_import)

### `datawindow_integration` (used in 6 files)
- `src/decompile/extractors/__init__.py:30` (from_import)
- `src/decompile/extractors/__init__.py:30` (from_import)
- `src/decompile/extractors/__init__.py:30` (from_import)
- `src/decompile/extractors/__init__.py:30` (from_import)
- `src/decompile/extractors/__init__.py:30` (from_import)
- `src/decompile/extractors/__init__.py:30` (from_import)

### `datawindows` (used in 1 files)
- `src/generate/converters/flutter/__init__.py:7` (from_import)

### `db_formatter` (used in 1 files)
- `src/generate/converters/data/__init__.py:4` (from_import)

### `declarations` (used in 2 files)
- `src/model/ast/nodes/__init__.py:7` (from_import)
- `src/model/ast/nodes/__init__.py:7` (from_import)

### `design_system` (used in 2 files)
- `src/generate/converters/flutter/__init__.py:10` (from_import)
- `src/generate/converters/flutter/widgets.py:10` (from_import)

### `detector` (used in 5 files)
- `src/decompile/pcode/tiered_detector.py:23` (from_import)
- `src/decompile/pcode/tiered_detector.py:23` (from_import)
- `src/decompile/pcode/__init__.py:7` (from_import)
- `src/decompile/pcode/__init__.py:7` (from_import)
- `src/decompile/pcode/__init__.py:7` (from_import)

### `distributed` (used in 4 files)
- `src/model/transaction/__init__.py:9` (from_import)
- `src/model/transaction/__init__.py:9` (from_import)
- `src/model/transaction/__init__.py:9` (from_import)
- `src/model/transaction/__init__.py:9` (from_import)

### `dw_enhancements` (used in 1 files)
- `src/generate/converters/flutter/datawindows.py:22` (from_import)

### `enhanced_reconstructor` (used in 2 files)
- `src/decompile/reconstruction/integration.py:13` (from_import)
- `src/decompile/reconstruction/integration.py:13` (from_import)

### `enhanced_stack` (used in 10 files)
- `src/decompile/reconstruction/context_recovery.py:15` (from_import)
- `src/decompile/reconstruction/context_recovery.py:15` (from_import)
- `src/decompile/reconstruction/context_recovery.py:15` (from_import)
- `src/decompile/reconstruction/enhanced_reconstructor.py:18` (from_import)
- `src/decompile/reconstruction/enhanced_reconstructor.py:18` (from_import)
- `src/decompile/reconstruction/enhanced_reconstructor.py:18` (from_import)
- `src/decompile/reconstruction/enhanced_reconstructor.py:18` (from_import)
- `src/decompile/reconstruction/expression.py:193` (from_import)
- `src/decompile/reconstruction/expression.py:193` (from_import)
- `src/decompile/reconstruction/expression.py:193` (from_import)

### `entity_factory` (used in 1 files)
- `src/model/services/__init__.py:2` (from_import)

### `entity_validator` (used in 1 files)
- `src/model/services/__init__.py:3` (from_import)

### `entry` (used in 1 files)
- `src/extract/pbd/object.py:14` (from_import)

### `error_handling` (used in 3 files)
- `src/model/transaction/__init__.py:15` (from_import)
- `src/model/transaction/__init__.py:15` (from_import)
- `src/model/transaction/__init__.py:15` (from_import)

### `errors` (used in 2 files)
- `src/model/types/validation.py:9` (from_import)
- `src/model/utils/__init__.py:6` (from_import)

### `evaluator` (used in 2 files)
- `src/model/expressions/__init__.py:11` (from_import)
- `src/model/expressions/__init__.py:11` (from_import)

### `event` (used in 2 files)
- `src/model/entities/__init__.py:4` (from_import)
- `src/model/entities/application.py:7` (from_import)

### `events` (used in 6 files)
- `src/model/system/__init__.py:9` (from_import)
- `src/model/system/__init__.py:9` (from_import)
- `src/model/system/__init__.py:9` (from_import)
- `src/model/system/__init__.py:9` (from_import)
- `src/generate/converters/flutter/__init__.py:13` (from_import)
- `src/generate/processors/__init__.py:3` (from_import)

### `exceptions` (used in 1 files)
- `src/core/errors.py:24` (from_import)

### `expressions` (used in 10 files)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/model/ast/nodes/__init__.py:8` (from_import)
- `src/generate/converters/utils/__init__.py:4` (from_import)

### `extract` (used in 3 files)
- `src/extract/__init__.py:11` (from_import)
- `src/extract/__init__.py:11` (from_import)
- `src/extract/__init__.py:37` (from_import)

### `extractors.datawindow` (used in 2 files)
- `src/decompile/coordinator.py:60` (from_import)
- `src/decompile/coordinator_cached.py:16` (from_import)

### `extractors.logic` (used in 2 files)
- `src/decompile/coordinator.py:61` (from_import)
- `src/decompile/coordinator_cached.py:17` (from_import)

### `extractors.schema` (used in 1 files)
- `src/decompile/coordinator_cached.py:18` (from_import)

### `factory` (used in 3 files)
- `src/decompile/coordinator_cached.py:22` (from_import)
- `src/decompile/coordinator_cached.py:65` (from_import)
- `src/generate/factories/__init__.py:3` (from_import)

### `files` (used in 8 files)
- `src/common/utils/__init__.py:8` (from_import)
- `src/common/utils/__init__.py:8` (from_import)
- `src/common/utils/__init__.py:8` (from_import)
- `src/common/utils/__init__.py:8` (from_import)
- `src/common/utils/__init__.py:8` (from_import)
- `src/common/utils/__init__.py:8` (from_import)
- `src/common/utils/__init__.py:8` (from_import)
- `src/common/utils/__init__.py:8` (from_import)

### `filters` (used in 1 files)
- `src/generate/base.py:14` (from_import)

### `flutter` (used in 2 files)
- `src/generate/coordinator.py:53` (from_import)
- `src/generate/coordinators/__init__.py:7` (from_import)

### `function` (used in 3 files)
- `src/model/entities/__init__.py:5` (from_import)
- `src/model/entities/__init__.py:5` (from_import)
- `src/model/entities/__init__.py:5` (from_import)

### `functions` (used in 5 files)
- `src/model/system/__init__.py:10` (from_import)
- `src/model/system/__init__.py:10` (from_import)
- `src/model/system/__init__.py:10` (from_import)
- `src/model/system/__init__.py:10` (from_import)
- `src/model/ast/nodes/sql.py:16` (from_import)

### `globals` (used in 3 files)
- `src/model/system/__init__.py:11` (from_import)
- `src/model/system/__init__.py:11` (from_import)
- `src/model/system/__init__.py:11` (from_import)

### `grammar.loader` (used in 3 files)
- `src/parse/coordinator.py:44` (from_import)
- `src/parse/factory.py:22` (from_import)
- `src/parse/coordinator_cached.py:21` (from_import)

### `high_performance_detector` (used in 4 files)
- `src/decompile/pcode/detector.py:183` (from_import)
- `src/decompile/pcode/detector.py:800` (from_import)
- `src/decompile/pcode/tiered_detector.py:24` (from_import)
- `src/decompile/pcode/__init__.py:8` (from_import)

### `integration` (used in 2 files)
- `src/decompile/reconstruction/expression.py:26` (from_import)
- `src/decompile/reconstruction/expression.py:158` (from_import)

### `interfaces` (used in 3 files)
- `src/contracts/__init__.py:14` (from_import)
- `src/contracts/__init__.py:103` (from_import)
- `src/contracts/logger.py:8` (from_import)

### `layouts` (used in 1 files)
- `src/generate/converters/flutter/__init__.py:14` (from_import)

### `library` (used in 5 files)
- `src/parse/coordinator.py:45` (from_import)
- `src/parse/factory.py:23` (from_import)
- `src/parse/coordinator_cached.py:22` (from_import)
- `src/parse/resolution.py:22` (from_import)
- `src/model/entities/__init__.py:6` (from_import)

### `literals` (used in 12 files)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/__init__.py:19` (from_import)
- `src/model/ast/nodes/sql.py:15` (from_import)
- `src/model/ast/nodes/sql.py:15` (from_import)
- ... and 2 more files

### `logger` (used in 3 files)
- `src/contracts/__init__.py:15` (from_import)
- `src/contracts/__init__.py:15` (from_import)
- `src/contracts/__init__.py:109` (from_import)

### `logic` (used in 1 files)
- `src/generate/converters/flutter/__init__.py:17` (from_import)

### `menus` (used in 1 files)
- `src/generate/converters/flutter/__init__.py:18` (from_import)

### `method_call` (used in 2 files)
- `src/model/entities/__init__.py:7` (from_import)
- `src/model/entities/__init__.py:7` (from_import)

### `model` (used in 1 files)
- `src/generate/coordinators/__init__.py:8` (from_import)

### `model_extractor` (used in 1 files)
- `src/model/services/__init__.py:6` (from_import)

### `model_extractor_visitor` (used in 1 files)
- `src/model/visitors/__init__.py:9` (from_import)

### `model_persistence` (used in 1 files)
- `src/model/services/__init__.py:7` (from_import)

### `models` (used in 1 files)
- `src/generate/coordinator.py:54` (from_import)

### `modes.parallel` (used in 1 files)
- `src/common/pipeline/__init__.py:8` (from_import)

### `modes.streaming` (used in 1 files)
- `src/common/pipeline/__init__.py:9` (from_import)

### `node_kind` (used in 2 files)
- `src/model/ast/__init__.py:21` (from_import)
- `src/model/ast/nodes/sql.py:14` (from_import)

### `nodes.base` (used in 10 files)
- `src/model/ast/functions.py:15` (from_import)
- `src/model/ast/functions.py:15` (from_import)
- `src/model/ast/functions.py:19` (from_import)
- `src/model/ast/io.py:10` (from_import)
- `src/model/ast/io.py:10` (from_import)
- `src/model/ast/__init__.py:14` (from_import)
- `src/model/ast/__init__.py:14` (from_import)
- `src/model/ast/__init__.py:14` (from_import)
- `src/model/ast/__init__.py:175` (from_import)
- `src/model/ast/__init__.py:175` (from_import)

### `nodes.declarations` (used in 4 files)
- `src/model/ast/functions.py:16` (from_import)
- `src/model/ast/__init__.py:15` (from_import)
- `src/model/ast/__init__.py:15` (from_import)
- `src/model/ast/__init__.py:15` (from_import)

### `nodes.expressions` (used in 1 files)
- `src/model/ast/__init__.py:17` (from_import)

### `nodes.literals` (used in 1 files)
- `src/model/ast/__init__.py:16` (from_import)

### `nodes.sql` (used in 1 files)
- `src/model/ast/__init__.py:19` (from_import)

### `nodes.variables` (used in 1 files)
- `src/model/ast/__init__.py:18` (from_import)

### `opcodes` (used in 13 files)
- `src/decompile/pcode/opcodes/definitions.py:24` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- `src/decompile/opcodes/__init__.py:8` (from_import)
- ... and 3 more files

### `opcodes.opcodes` (used in 1 files)
- `src/decompile/coordinator_cached.py:19` (from_import)

### `orchestrator` (used in 1 files)
- `src/extract/components/__init__.py:7` (from_import)

### `output_formatter` (used in 2 files)
- `src/decompile/reconstruction/integration.py:17` (from_import)
- `src/decompile/reconstruction/integration.py:17` (from_import)

### `parallel` (used in 1 files)
- `src/common/pipeline/modes/__init__.py:8` (from_import)

### `parser` (used in 2 files)
- `src/decompile/analyzers/__init__.py:3` (from_import)
- `src/extract/components/__init__.py:8` (from_import)

### `parser.base` (used in 2 files)
- `src/parse/coordinator.py:46` (from_import)
- `src/parse/coordinator_cached.py:23` (from_import)

### `parser.powerbuilder` (used in 4 files)
- `src/parse/coordinator.py:47` (from_import)
- `src/parse/library.py:131` (from_import)
- `src/parse/factory.py:24` (from_import)
- `src/parse/coordinator_cached.py:24` (from_import)

### `paths` (used in 1 files)
- `src/extract/security/__init__.py:3` (from_import)

### `pattern_engine` (used in 1 files)
- `src/decompile/reconstruction/enhanced_reconstructor.py:24` (from_import)

### `pb_access` (used in 4 files)
- `src/model/constructs/__init__.py:7` (from_import)
- `src/model/constructs/__init__.py:7` (from_import)
- `src/model/constructs/__init__.py:7` (from_import)
- `src/model/constructs/__init__.py:7` (from_import)

### `pb_entity` (used in 1 files)
- `src/model/base/__init__.py:3` (from_import)

### `pb_expressions` (used in 23 files)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- `src/model/expressions/__init__.py:12` (from_import)
- ... and 13 more files

### `pbd.constants` (used in 2 files)
- `src/extract/__init__.py:12` (from_import)
- `src/extract/__init__.py:12` (from_import)

### `positions` (used in 5 files)
- `src/parse/transformer/visitors/__init__.py:7` (from_import)
- `src/parse/transformer/visitors/__init__.py:7` (from_import)
- `src/parse/transformer/visitors/__init__.py:7` (from_import)
- `src/parse/transformer/visitors/__init__.py:7` (from_import)
- `src/parse/transformer/visitors/__init__.py:7` (from_import)

### `preprocessor.imports` (used in 1 files)
- `src/parse/factory.py:25` (from_import)

### `preprocessor.preprocessor` (used in 3 files)
- `src/parse/coordinator.py:48` (from_import)
- `src/parse/factory.py:26` (from_import)
- `src/parse/coordinator_cached.py:25` (from_import)

### `progress` (used in 1 files)
- `src/common/pipeline/__init__.py:10` (from_import)

### `pseudocode` (used in 1 files)
- `src/parse/parser/specialized/__init__.py:3` (from_import)

### `python_ui` (used in 1 files)
- `src/generate/coordinator.py:55` (from_import)

### `ray` (used in 1 files)
- `src/core/distributed.py:463` (import)

### `reconstructor` (used in 1 files)
- `src/model/expressions/__init__.py:26` (from_import)

### `recovery` (used in 1 files)
- `src/extract/components/__init__.py:9` (from_import)

### `recovery_strategy` (used in 2 files)
- `src/parse/coordinator.py:49` (from_import)
- `src/parse/coordinator_cached.py:26` (from_import)

### `relationship_manager` (used in 1 files)
- `src/model/services/__init__.py:4` (from_import)

### `relationships` (used in 1 files)
- `src/generate/converters/data/__init__.py:5` (from_import)

### `resolution` (used in 1 files)
- `src/parse/factory.py:27` (from_import)

### `resources` (used in 1 files)
- `src/extract/components/__init__.py:10` (from_import)

### `savepoint` (used in 4 files)
- `src/model/transaction/transaction.py:15` (from_import)
- `src/model/transaction/__init__.py:16` (from_import)
- `src/model/transaction/__init__.py:16` (from_import)
- `src/model/transaction/__init__.py:16` (from_import)

### `scaffolder` (used in 1 files)
- `src/generate/scaffolders/__init__.py:3` (from_import)

### `schema_generator` (used in 1 files)
- `src/decompile/analyzers/__init__.py:4` (from_import)

### `schemas` (used in 1 files)
- `src/generate/base.py:15` (from_import)

### `service` (used in 2 files)
- `src/generate/coordinator.py:56` (from_import)
- `src/generate/coordinators/__init__.py:9` (from_import)

### `specialized.pseudocode` (used in 1 files)
- `src/parse/parser/powerbuilder.py:23` (from_import)

### `specialized.transactions` (used in 1 files)
- `src/parse/parser/powerbuilder.py:24` (from_import)

### `specialized.types` (used in 1 files)
- `src/parse/parser/powerbuilder.py:25` (from_import)

### `sql` (used in 7 files)
- `src/parse/parser/powerbuilder.py:26` (from_import)
- `src/parse/parser/specialized/__init__.py:4` (from_import)
- `src/parse/parser/specialized/__init__.py:4` (from_import)
- `src/model/ast/nodes/__init__.py:29` (from_import)
- `src/model/ast/nodes/__init__.py:29` (from_import)
- `src/model/ast/nodes/__init__.py:29` (from_import)
- `src/model/ast/nodes/__init__.py:29` (from_import)

### `sql_optimizer` (used in 2 files)
- `src/model/optimization/__init__.py:6` (from_import)
- `src/model/optimization/__init__.py:6` (from_import)

### `statement` (used in 3 files)
- `src/model/transaction/transaction.py:16` (from_import)
- `src/model/transaction/__init__.py:17` (from_import)
- `src/model/transaction/__init__.py:17` (from_import)

### `streaming` (used in 1 files)
- `src/common/pipeline/modes/__init__.py:9` (from_import)

### `strings` (used in 4 files)
- `src/common/utils/__init__.py:18` (from_import)
- `src/common/utils/__init__.py:18` (from_import)
- `src/common/utils/__init__.py:18` (from_import)
- `src/common/utils/__init__.py:18` (from_import)

### `table` (used in 5 files)
- `src/model/symbols/__init__.py:7` (from_import)
- `src/model/symbols/__init__.py:7` (from_import)
- `src/model/symbols/__init__.py:7` (from_import)
- `src/model/symbols/__init__.py:7` (from_import)
- `src/model/symbols/__init__.py:7` (from_import)

### `templates.engine` (used in 3 files)
- `src/generate/factory.py:20` (from_import)
- `src/generate/factory.py:20` (from_import)
- `src/generate/base.py:47` (from_import)

### `themes` (used in 1 files)
- `src/generate/converters/flutter/__init__.py:19` (from_import)

### `tiered_config` (used in 4 files)
- `src/decompile/pcode/tiered_detector.py:25` (from_import)
- `src/decompile/pcode/tiered_detector.py:25` (from_import)
- `src/decompile/pcode/__init__.py:13` (from_import)
- `src/decompile/pcode/__init__.py:13` (from_import)

### `tiered_detector` (used in 2 files)
- `src/decompile/pcode/__init__.py:12` (from_import)
- `src/decompile/pcode/__init__.py:12` (from_import)

### `transaction` (used in 4 files)
- `src/model/transaction/__init__.py:18` (from_import)
- `src/model/transaction/__init__.py:18` (from_import)
- `src/model/transaction/__init__.py:18` (from_import)
- `src/model/transaction/distributed.py:15` (from_import)

### `transactions` (used in 1 files)
- `src/parse/parser/specialized/__init__.py:5` (from_import)

### `transformer.builder` (used in 3 files)
- `src/parse/coordinator.py:50` (from_import)
- `src/parse/factory.py:28` (from_import)
- `src/parse/coordinator_cached.py:27` (from_import)

### `ui` (used in 1 files)
- `src/generate/processors/__init__.py:4` (from_import)

### `utils.binary` (used in 2 files)
- `src/extract/__init__.py:13` (from_import)
- `src/extract/__init__.py:13` (from_import)

### `validator` (used in 1 files)
- `src/extract/components/__init__.py:12` (from_import)

### `variables` (used in 6 files)
- `src/model/ast/nodes/__init__.py:30` (from_import)
- `src/model/ast/nodes/__init__.py:30` (from_import)
- `src/model/ast/nodes/__init__.py:30` (from_import)
- `src/model/ast/nodes/__init__.py:30` (from_import)
- `src/model/ast/nodes/__init__.py:30` (from_import)
- `src/model/ast/nodes/__init__.py:30` (from_import)

### `visitor` (used in 2 files)
- `src/parse/transformer/visitors/__init__.py:14` (from_import)
- `src/parse/transformer/visitors/positions.py:17` (from_import)

### `widgets` (used in 1 files)
- `src/generate/converters/flutter/__init__.py:20` (from_import)

### `wiring` (used in 1 files)
- `src/generate/converters/logic/__init__.py:4` (from_import)

## 🔄 CIRCULAR DEPENDENCIES (2 cycles)

### Cycle 1
  src.extract.pbd.structures → src.extract.pbd.recovery
  src.extract.pbd.recovery → src.extract.pbd.structures
  src.extract.pbd.structures → src.extract.pbd.structures

### Cycle 2
  src.generate.coordinator → src.generate.coordinators.service
  src.generate.coordinators.service → src.generate.coordinator
  src.generate.coordinator → src.generate.coordinator

## 📊 Major Module Dependencies

### EXTRACT depends on:
- common
- contracts
- core
- decompile

### DECOMPILE depends on:
- contracts
- core
- extract
- model
- parse

### PARSE depends on:
- common
- contracts
- core
- extract
- model

### MODEL depends on:
- core
- decompile

### GENERATE depends on:
- base
- contracts
- core
- model
- models
- parse
- python_ui
- service
