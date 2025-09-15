"""Contracts and interfaces for PowerRebuilder components.

This module provides lazy loading for interfaces and protocols from the consolidated
interfaces.py file to reduce import overhead.
"""

from typing import TYPE_CHECKING, Any

# Lazy loading support
_interface_cache = {}

# Import types for type checking but not at runtime to avoid circular imports
if TYPE_CHECKING:
    from .interfaces import *
    from .logger import DetailedLoggerAdapter, StandardLogger


def __getattr__(name: str) -> Any:
    """Lazy import interfaces on first access."""
    if name in _interface_cache:
        return _interface_cache[name]

    # Define interface mappings for lazy loading
    interface_mapping = {
        # Event interfaces
        "Event": ".interfaces",
        "EventType": ".interfaces",
        # Generator interfaces
        "IASTExtractor": ".interfaces",
        # Model interfaces
        "IASTProcessor": ".interfaces",
        # Extractor interfaces
        "IBinaryExtractor": ".interfaces",
        "IBinaryFileParser": ".interfaces",
        # Decompiler interfaces
        "IControlFlowAnalyzer": ".interfaces",
        "IDecompiler": ".interfaces",
        "IDecompilerCoordinator": ".interfaces",
        "IEntityFactory": ".interfaces",
        "IEntityValidator": ".interfaces",
        # Parser interfaces
        "IEnumeratedType": ".interfaces",
        "IEventBus": ".interfaces",
        "IEventHandler": ".interfaces",
        "IEventProcessor": ".interfaces",
        "IExpressionEvaluator": ".interfaces",
        "IExpressionReconstructor": ".interfaces",
        "IExtractionStatistics": ".interfaces",
        "IExtractionValidator": ".interfaces",
        "IExtractor": ".interfaces",
        "IExtractOrchestrator": ".interfaces",
        "IExtractorCoordinator": ".interfaces",
        "IGenerator": ".interfaces",
        "IGeneratorCoordinator": ".interfaces",
        "IGeneratorFactory": ".interfaces",
        "IGrammarManager": ".interfaces",
        "IImportResolver": ".interfaces",
        "ILibraryManager": ".interfaces",
        # Logger interfaces
        "ILogger": ".interfaces",
        "IModelExtractor": ".interfaces",
        "IModelPersistence": ".interfaces",
        "IObjectTypeDetector": ".interfaces",
        "IOutputFormatter": ".interfaces",
        "IOutputValidator": ".interfaces",
        "IParser": ".interfaces",
        "IParserCoordinator": ".interfaces",
        "IPathValidator": ".interfaces",
        "IPBDReader": ".interfaces",
        "IPCodeDecoder": ".interfaces",
        # Pipeline interfaces
        "IPipelineCoordinator": ".interfaces",
        "IPipelineStage": ".interfaces",
        "IPipelineState": ".interfaces",
        "IPreprocessor": ".interfaces",
        "IProgressReporter": ".interfaces",
        "IProgressTracker": ".interfaces",
        "IProjectScaffolder": ".interfaces",
        "IRecoveryEngine": ".interfaces",
        "IResourceExtractor": ".interfaces",
        "IResourceMonitor": ".interfaces",
        "IStateManager": ".interfaces",
        "IStructureType": ".interfaces",
        "ITemplateEngine": ".interfaces",
        "ITransformer": ".interfaces",
        "ITypeConverter": ".interfaces",
        "ITypeParser": ".interfaces",
        "ITypeResolver": ".interfaces",
        "IUIProcessor": ".interfaces",
        "IVersionDetector": ".interfaces",
        "PipelineStage": ".interfaces",
        "ProgressCallback": ".interfaces",
        "StageStatus": ".interfaces",
        # Logger classes
        "DetailedLoggerAdapter": ".logger",
        "StandardLogger": ".logger",
    }

    if name in interface_mapping:
        module_name = interface_mapping[name]
        try:
            if module_name == ".interfaces":
                from .interfaces import __dict__ as interfaces_dict

                if name in interfaces_dict:
                    _interface_cache[name] = interfaces_dict[name]
                    return _interface_cache[name]
            elif module_name == ".logger":
                from .logger import __dict__ as logger_dict

                if name in logger_dict:
                    _interface_cache[name] = logger_dict[name]
                    return _interface_cache[name]
        except ImportError:
            # Logger interface not available, continue to raise AttributeError
            logger.debug("Logger interface not available for attribute '%s'", name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "DetailedLoggerAdapter",
    # Events
    "Event",
    "EventType",
    # Generators
    "IASTExtractor",
    # Models
    "IASTProcessor",
    # Extractors
    "IBinaryExtractor",
    "IBinaryFileParser",
    # Decompilers
    "IControlFlowAnalyzer",
    "IDecompiler",
    "IDecompilerCoordinator",
    "IEntityFactory",
    "IEntityValidator",
    # Parsers
    "IEnumeratedType",
    "IEventBus",
    "IEventHandler",
    "IEventProcessor",
    "IExpressionEvaluator",
    "IExpressionReconstructor",
    "IExtractOrchestrator",
    "IExtractionStatistics",
    "IExtractionValidator",
    "IExtractor",
    "IExtractorCoordinator",
    "IGenerator",
    "IGeneratorCoordinator",
    "IGeneratorFactory",
    "IGrammarManager",
    "IImportResolver",
    "ILibraryManager",
    # Logger
    "ILogger",
    "IModelExtractor",
    "IModelPersistence",
    "IObjectTypeDetector",
    "IOutputFormatter",
    "IOutputValidator",
    "IPBDReader",
    "IPCodeDecoder",
    "IParser",
    "IParserCoordinator",
    "IPathValidator",
    # Pipeline
    "IPipelineCoordinator",
    "IPipelineStage",
    "IPipelineState",
    "IPreprocessor",
    "IProgressReporter",
    "IProgressTracker",
    "IProjectScaffolder",
    "IRecoveryEngine",
    "IResourceExtractor",
    "IResourceMonitor",
    "IStateManager",
    "IStructureType",
    "ITemplateEngine",
    "ITransformer",
    "ITypeConverter",
    "ITypeParser",
    "ITypeResolver",
    "IUIProcessor",
    "IVersionDetector",
    "PipelineStage",
    "ProgressCallback",
    "StageStatus",
    "StandardLogger",
]
