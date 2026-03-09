"""Generate Feature - Code generation from semantic models.

This package generates modern application code from semantic models,
supporting multiple target languages and frameworks.
"""

from .generator import (
    BaseCodeGenerator,
    FlutterGenerator,
    GenerateCoordinator,
    PythonGenerator,
)
from .templates import get_template, render_template

# Import new generators conditionally
try:
    from .typescript import TypeScriptGenerator
    from .react import ReactGenerator
    from .dioxus import DioxusGenerator
    from .vue import VueGenerator
    from .svelte import SvelteGenerator
    from .tauri import TauriGenerator
    from .rust_dioxus import DioxusGenerator as RustDioxusGenerator

    _new_generators = True
except ImportError:
    _new_generators = False

__all__ = [
    "GenerateCoordinator",
    "BaseCodeGenerator",
    "FlutterGenerator",
    "PythonGenerator",
    "get_template",
    "render_template",
]

if _new_generators:
    __all__.extend(
        [
            "TypeScriptGenerator",
            "ReactGenerator",
            "DioxusGenerator",
            "VueGenerator",
            "SvelteGenerator",
            "TauriGenerator",
            "RustDioxusGenerator",
        ]
    )
