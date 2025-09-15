# PowerRebuilder Infrastructure Components

This document describes the infrastructure components that have been enabled in PowerRebuilder to support scalable, maintainable code generation pipelines.

## Overview

The infrastructure provides:
- **Dependency Injection** - Loose coupling and testability
- **Event Bus** - Decoupled communication between components
- **Caching** - Performance optimization for repeated operations
- **Progress Tracking** - User-friendly progress reporting

## Initialization

All infrastructure is initialized through a single entry point:

```python
from src.core.startup import initialize_application

# Initialize with default settings
startup = initialize_application()

# Initialize with verbose logging
startup = initialize_application(verbose=True)

# Initialize with custom cache directory
startup = initialize_application(cache_dir=Path("/tmp/powerrebuilder_cache"))
```

The initialization is automatically handled in `main.py` when the CLI starts.

## Component Access

Components can be accessed in two ways:

1. **By name (string)**:
```python
from src.core.startup import get_infrastructure_component

container = get_infrastructure_component("container")
event_bus = get_infrastructure_component("event_bus")
ast_cache = get_infrastructure_component("ast_cache")
progress = get_infrastructure_component("progress")
```

2. **By type**:
```python
from src.core.events import EventBus
from src.common.pipeline.progress import PipelineProgress

event_bus = get_infrastructure_component(EventBus)
progress = get_infrastructure_component(PipelineProgress)
```

## Dependency Injection

The DI container manages service lifetimes and dependencies:

### Registering Services

Services are registered in `src/common/di_configuration.py`:

```python
# Singleton service
container.register_singleton(IPathValidator, PathValidator)

# Transient service (new instance each time)
container.register_transient(IProgressTracker, TqdmProgressTracker)

# Factory registration
container.register_factory(
    IPBDReader,
    lambda c: lambda file_path: StreamingPBDReader(file_path)
)
```

### Using Services

```python
# Get container
container = get_infrastructure_component("container")

# Resolve service
path_validator = container.resolve(IPathValidator)

# Use service
safe_path = path_validator.validate_output_path(user_path)
```

### Decorator Support

```python
from src.core.dependency_injection import inject, injectable

@injectable()  # Auto-registers with container
class MyService:
    def __init__(self, validator: IPathValidator):
        self.validator = validator

@inject  # Auto-injects dependencies
def process_file(service: MyService):
    service.do_something()
```

## Event Bus

The event bus enables decoupled communication:

### Publishing Events

```python
from src.contracts.interfaces import Event, EventType

event_bus = get_infrastructure_component("event_bus")

# Create event
event = Event(
    type=EventType.FILE_PROCESSED,
    source="extract_coordinator",
    data={"file": "example.pbl", "entries": 42}
)

# Publish
event_bus.publish(event)
```

### Subscribing to Events

```python
from src.core.events import EventHandler

# Create handler
def on_file_processed(event: Event):
    print(f"Processed: {event.data['file']}")

handler = EventHandler(
    on_file_processed,
    event_types={EventType.FILE_PROCESSED}
)

# Subscribe
event_bus.subscribe(EventType.FILE_PROCESSED, handler)
```

### Built-in Handlers

- **LoggingEventHandler** - Logs all events
- **MetricsEventHandler** - Collects metrics
- **FileEventHandler** - Writes events to file

## Caching

Three types of caches are available:

### AST Cache (In-Memory)

```python
ast_cache = get_infrastructure_component("ast_cache")

# Async usage
await ast_cache.put("file.sru", parsed_ast)
cached_ast = await ast_cache.get("file.sru")

# Statistics
stats = ast_cache.stats()
# {'size': 10, 'memory': 102400, 'hits': 8, 'misses': 2, 'hit_rate': 0.8}
```

### Validation Cache (In-Memory)

```python
validation_cache = get_infrastructure_component("validation_cache")

# Cache validation results
await validation_cache.put(file_hash, validation_result)
```

### File Cache (Persistent)

```python
file_cache = get_infrastructure_component("file_cache")

# Persists to disk with TTL
await file_cache.put("analysis_result", large_data)
result = await file_cache.get("analysis_result")

# Cleanup expired entries
await file_cache.cleanup()
```

### Cache Decorators

```python
from src.core.cache import cached, LRUCache

cache = LRUCache(max_size=100)

@cached(cache)
async def expensive_operation(file_path: str):
    # This will be cached
    return await parse_file(file_path)
```

## Progress Tracking

Rich terminal UI for progress tracking:

### Pipeline Progress

```python
progress = get_infrastructure_component(PipelineProgress)

# Full pipeline with multiple stages
with progress.pipeline_context(total_steps=5) as pipeline:
    # Stage 1
    pipeline.start_step("Extracting files", 1)
    # ... do work ...
    pipeline.complete_step(1)

    # Stage 2
    pipeline.start_step("Decompiling", 2)
    # ... do work ...
    pipeline.complete_step(2)
```

### File Operations

```python
# Track file extraction
with progress.file_extraction_context(total_files=100) as task_id:
    for i, file in enumerate(files):
        # Process file
        size = process_file(file)

        # Update progress with transfer speed
        progress.update_file_progress(
            completed=i+1,
            current_file=file.name,
            speed=size / elapsed_time
        )
```

### Individual Operations

```python
# Track specific operations
with progress.operation_context("Analyzing dependencies", total=50) as task_id:
    for i in range(50):
        analyze_dependency(i)
        progress.update_operation(i + 1, f"Dependency {i+1}/50")
```

## Integration in Coordinators

The coordinators have been updated to use infrastructure:

### ExtractCoordinator

- Accepts optional `progress_reporter` parameter
- Can publish events through event bus
- Uses caching for repeated extractions

### ParseCoordinator

- Uses AST cache to avoid re-parsing
- Publishes parsing progress events
- Validates through DI-injected validators

### GenerateCoordinator

- Uses cached models
- Reports generation progress
- Publishes completion events

## Example Usage

See `examples/infrastructure_demo.py` for a complete demonstration of all infrastructure components.

## Testing

Infrastructure components can be mocked for testing:

```python
# Override services for testing
test_container = DIContainer()
test_container.register_singleton(IPathValidator, MockPathValidator)

# Use test container
with override_container(test_container):
    # Run tests with mocked services
    pass
```

## Performance Considerations

1. **Caching**: The in-memory caches have size and memory limits to prevent unbounded growth
2. **Event Bus**: Async processing prevents blocking on event delivery
3. **Progress Tracking**: Uses Rich library for efficient terminal updates
4. **DI Container**: Singleton services are lazily instantiated on first use

## Future Enhancements

1. **Distributed Caching**: Redis backend for multi-process scenarios
2. **Event Persistence**: Store events for replay and debugging
3. **Metrics Dashboard**: Real-time pipeline metrics visualization
4. **Configuration Management**: Environment-based configuration injection
