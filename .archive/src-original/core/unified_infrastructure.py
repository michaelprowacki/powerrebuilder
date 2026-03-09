"""Unified Infrastructure - ALL core infrastructure in ONE place.

This mega-module consolidates all core infrastructure components into a single
unified interface. It merges caching, circuit breakers, coordination, distributed
processing, events, logging, recovery, security, state management, streams, and
error handling into ONE comprehensive infrastructure layer.

Components consolidated:
- Caching (cache.py, cache_config.py)
- Circuit Breaker (circuit_breaker.py)
- Coordination (coordination_base.py, coordination_mixins.py)
- Distributed Processing (distributed.py)
- Events (events.py)
- Logging (logging.py)
- Recovery (recovery.py)
- Resource Management (resource_limits.py)
- Security (security.py)
- State Management (state_management.py)
- Streams (streams.py)
- Error Handling (errors.py, exceptions.py)
"""

# =============================================================================
# IMPORTS - All dependencies for the infrastructure
# =============================================================================

import asyncio
import contextlib
import hashlib
import json
import logging
import mmap
import multiprocessing as mp
import os
import re
import shutil
import struct
import sys
import threading
import time
import traceback
import uuid
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from collections.abc import Callable, Iterator
from concurrent.futures import Future, ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from functools import wraps
from pathlib import Path
from queue import Empty, Queue
from typing import Any, BinaryIO, Protocol, TypeVar

import aiofiles
import aiofiles.os
import psutil

# Import event types from unified_core (contracts were consolidated)
from src.core.unified_core import (
    Event,
    EventType,
    IEventHandler,
    IEventBus,
)

T = TypeVar("T")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])

# =============================================================================
# MISSING INTERFACES - Previously in src/contracts
# =============================================================================


class StageStatus(Enum):
    """Status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class IPipelineState(Protocol):
    """Interface for pipeline state management."""

    def get_stage_status(self, stage: str) -> StageStatus:
        """Get the status of a specific stage."""
        ...

    def set_stage_status(self, stage: str, status: StageStatus) -> None:
        """Set the status of a specific stage."""
        ...


class IStateManager(Protocol):
    """Interface for state management."""

    def create_state(self) -> IPipelineState:
        """Create a new pipeline state."""
        ...

    def save_state(self, state: IPipelineState, path: Path) -> None:
        """Save state to a file."""
        ...

    def load_state(self, path: Path) -> IPipelineState:
        """Load state from a file."""
        ...


# =============================================================================
# CONSTANTS SECTION - All constants from constants.py
# =============================================================================

"""
CONSTANTS CONSOLIDATION

This section contains all constants previously defined in src/core/constants.py
Organized into logical categories for maintainability:

1. Core Constants - Buffer sizes, offsets, timeouts, file markers
2. File Format Constants - Grammar paths, file extensions, file types
3. PowerBuilder Language Constants - Types, keywords, operators, SQL
4. Magic Numbers - Counts, factors, limits, sizes, and miscellaneous values

These constants are used throughout the PowerRebuilder codebase for:
- PBD/PBL file format parsing
- PowerBuilder language processing
- P-code decompilation
- System integration limits
- Performance tuning parameters
"""

# =============================================================================
# Core Constants - Sizes, limits, and file format markers
# =============================================================================

# Sizes and limits
HEADER_SIZE = 52  # Standard PBD header size
BUFFER_SIZE = 8192  # Default buffer size for streaming
MAX_PATH_LENGTH = 255
MAX_NAME_LENGTH = 50

# Offsets
STRING_TABLE_OFFSET = 0xB20
METADATA_OFFSET = 0x20

# Time values
DEFAULT_TIMEOUT = 120000  # 2 minutes in ms
MAX_TIMEOUT = 600000  # 10 minutes in ms

# File format markers
PBD_HEADER_MARKER = b"HDR*"
PBD_SIGNATURE_HDR = b"HDR*"  # Alias for compatibility
ENTRY_MARKER = b"ENT*"
DATA_MARKER = b"DAT*"

# =============================================================================
# File Format Constants - Grammar paths and extensions
# =============================================================================

# Grammar file paths
GRAMMAR_DIR = Path(__file__).parent.parent / "parse" / "grammar"
POWERBUILDER_GRAMMAR = GRAMMAR_DIR / "powerbuilder.lark"
COMMON_GRAMMAR = GRAMMAR_DIR / "common_grammar.lark"
DATAWINDOW_GRAMMAR = GRAMMAR_DIR / "datawindow.lark"
SQL_GRAMMAR = GRAMMAR_DIR / "sql.lark"
PSEUDOCODE_GRAMMAR = GRAMMAR_DIR / "pseudocode.lark"
POWERBUILDER_CORE_GRAMMAR = GRAMMAR_DIR / "powerbuilder_core.lark"
POWERBUILDER_JS_GRAMMAR = GRAMMAR_DIR / "powerbuilder_js.lark"
TRANSACTION_GRAMMAR = GRAMMAR_DIR / "transactions.lark"


# File extensions and types
class FileType(Enum):
    """PowerBuilder file types."""

    WINDOW = auto()  # .srw
    USER_OBJECT = auto()  # .sru
    FUNCTION = auto()  # .srf
    MENU = auto()  # .srm
    STRUCTURE = auto()  # .srs
    QUERY = auto()  # .srq
    APPLICATION = auto()  # .sra
    DATAWINDOW = auto()  # .srd
    PROJECT = auto()  # .pbt
    LIBRARY = auto()  # .pbl, .pbd
    UNKNOWN = auto()


# File extension mappings
FILE_EXTENSIONS: dict[str, FileType] = {
    "srw": FileType.WINDOW,
    "sru": FileType.USER_OBJECT,
    "srf": FileType.FUNCTION,
    "srm": FileType.MENU,
    "srs": FileType.STRUCTURE,
    "srq": FileType.QUERY,
    "sra": FileType.APPLICATION,
    "srd": FileType.DATAWINDOW,
    "dwo": FileType.DATAWINDOW,
    "sql": FileType.QUERY,
    "pbt": FileType.PROJECT,
    "pbl": FileType.LIBRARY,
    "pbd": FileType.LIBRARY,
}

# =============================================================================
# PowerBuilder Language Constants
# =============================================================================

# PowerBuilder basic types
PB_BASIC_TYPES: set[str] = {
    "integer",
    "int",
    "long",
    "uint",
    "ulong",
    "string",
    "char",
    "character",
    "boolean",
    "bool",
    "date",
    "datetime",
    "time",
    "decimal",
    "dec",
    "real",
    "double",
    "blob",
    "any",
}

# PowerBuilder system types
PB_SYSTEM_TYPES: set[str] = {
    "powerobject",
    "window",
    "transaction",
    "dynamicdescriptionarea",
    "dynamicstagingarea",
    "error",
    "menu",
    "message",
    "connection",
    "datastore",
}

# PowerBuilder control types
PB_CONTROL_TYPES: set[str] = {
    # Text controls
    "statictext",
    "singlelineedit",
    "multilineedit",
    "editmask",
    "statichyperlink",
    # Button controls
    "commandbutton",
    "picturebutton",
    # Selection controls
    "checkbox",
    "radiobutton",
    # List controls
    "dropdownlistbox",
    "listbox",
    "combobox",
    # Container controls
    "groupbox",
    "tab",
    # Data controls
    "datawindow",
    # Shape controls
    "line",
    "rectangle",
    "roundrectangle",
    "oval",
    "drawobject",
    # Advanced controls
    "treeview",
    "listview",
    "richtextedit",
    "graph",
    "ole",
    "mdiclient",
    # Progress controls
    "progressbar",
    "hprogressbar",
    "vprogressbar",
    # Slider/Trackbar controls
    "htrackbar",
    "vtrackbar",
    # Scrollbar controls
    "vscrollbar",
    "hscrollbar",
    # Date/Time controls
    "datepicker",
    "monthcalendar",
    # Ink controls
    "inkpicture",
    "inkedit",
    # Other controls
    "picture",
    "animation",
    "spin",
    "edit",  # edit is generic
}

# PowerBuilder event types
PB_EVENT_TYPES: set[str] = {
    "clicked",
    "doubleclicked",
    "itemchanged",
    "itererror",
    "itemfocuschanged",
    "rbuttondown",
    "rowfocuschanged",
    "rowfocuschanging",
    "create",
    "destroy",
    "buttonclicked",
    "buttonclicking",
    "getfocus",
    "losefocus",
    "modified",
}

# PowerBuilder keywords
PB_KEYWORDS: set[str] = {
    "if",
    "then",
    "else",
    "elseif",
    "end",
    "case",
    "choose",
    "do",
    "loop",
    "while",
    "until",
    "for",
    "next",
    "step",
    "continue",
    "exit",
    "return",
    "try",
    "catch",
    "finally",
    "throw",
    "this",
    "super",
    "goto",
    "gosub",
    "call",
    "post",
    "trigger",
    "create",
    "destroy",
    "open",
    "close",
    "function",
    "subroutine",
    "event",
    "private",
    "public",
    "protected",
    "global",
    "shared",
    "on",
    "type",
    "constant",
    "variables",
    "forward",
    "from",
    "to",
    "ref",
    "autoinstantiate",
    "within",
    "of",
    "parent",
    "using",
    "dynamic",
    "indirect",
    "not",
    "and",
    "or",
    "xor",
    "true",
    "false",
}

# PowerBuilder operators
PB_OPERATORS: set[str] = {
    # Arithmetic operators
    "+",
    "-",
    "*",
    "/",
    "^",
    # Comparison operators
    "=",
    "<>",
    "<",
    ">",
    "<=",
    ">=",
    # Logical operators
    "and",
    "or",
    "not",
    # Assignment operators
    "+=",
    "-=",
    "*=",
    "/=",
}

# SQL keywords
SQL_KEYWORDS: set[str] = {
    "select",
    "insert",
    "update",
    "delete",
    "where",
    "from",
    "join",
    "inner",
    "outer",
    "left",
    "right",
    "full",
    "on",
    "group",
    "by",
    "having",
    "order",
    "asc",
    "desc",
    "distinct",
    "union",
    "all",
    "into",
    "values",
    "set",
    "null",
    "is",
    "not",
    "like",
    "in",
    "between",
    "exists",
    "create",
    "alter",
    "drop",
    "table",
    "view",
    "index",
    "procedure",
    "function",
    "constraint",
    "primary",
    "key",
    "foreign",
    "references",
    "default",
    "check",
    "unique",
    "identity",
}

# Map of all built-in PowerBuilder types for quick lookup
PB_TYPE_MAP: dict[str, bool] = dict.fromkeys(PB_BASIC_TYPES | PB_SYSTEM_TYPES, True)

# =============================================================================
# Magic Numbers - Extracted from analysis and usage patterns
# =============================================================================

# COUNT constants - Used for various counting operations
COUNTS_11, COUNTS_12, COUNTS_13, COUNTS_14, COUNTS_15 = 11, 12, 13, 14, 15
COUNTS_16, COUNTS_17, COUNTS_18, COUNTS_19, COUNTS_20 = 16, 17, 18, 19, 20
COUNTS_21, COUNTS_22, COUNTS_23, COUNTS_24, COUNTS_25 = 21, 22, 23, 24, 25
COUNTS_26, COUNTS_27, COUNTS_28, COUNTS_29, COUNTS_30 = 26, 27, 28, 29, 30
COUNTS_31, COUNTS_32, COUNTS_33, COUNTS_34, COUNTS_35 = 31, 32, 33, 34, 35
COUNTS_36, COUNTS_37, COUNTS_38, COUNTS_39, COUNTS_40 = 36, 37, 38, 39, 40
COUNTS_41, COUNTS_42, COUNTS_43, COUNTS_44, COUNTS_45 = 41, 42, 43, 44, 45
COUNTS_46, COUNTS_47, COUNTS_48, COUNTS_49, COUNTS_50 = 46, 47, 48, 49, 50
COUNTS_51, COUNTS_52, COUNTS_53, COUNTS_54, COUNTS_55 = 51, 52, 53, 54, 55
COUNTS_56, COUNTS_57, COUNTS_58, COUNTS_59, COUNTS_61 = 56, 57, 58, 59, 61
COUNTS_62, COUNTS_63, COUNTS_64, COUNTS_65, COUNTS_66 = 62, 63, 64, 65, 66
COUNTS_67, COUNTS_68, COUNTS_69, COUNTS_70, COUNTS_71 = 67, 68, 69, 70, 71
COUNTS_72, COUNTS_73, COUNTS_74, COUNTS_75, COUNTS_76 = 72, 73, 74, 75, 76
COUNTS_77, COUNTS_78, COUNTS_79, COUNTS_80, COUNTS_81 = 77, 78, 79, 80, 81
COUNTS_82, COUNTS_83, COUNTS_84, COUNTS_85, COUNTS_86 = 82, 83, 84, 85, 86
COUNTS_87, COUNTS_88, COUNTS_89, COUNTS_90, COUNTS_91 = 87, 88, 89, 90, 91
COUNTS_92, COUNTS_93, COUNTS_94, COUNTS_95, COUNTS_96 = 92, 93, 94, 95, 96
COUNTS_97, COUNTS_98, COUNTS_99 = 97, 98, 99

# FACTOR constants - Used for scaling and calculations
FACTORS_0_0001, FACTORS_0_001, FACTORS_0_005 = 0.0001, 0.001, 0.005
FACTORS_0_01, FACTORS_0_05, FACTORS_0_07 = 0.01, 0.05, 0.07
FACTORS_0_08, FACTORS_0_12, FACTORS_0_15 = 0.08, 0.12, 0.15
FACTORS_0_2, FACTORS_0_3, FACTORS_0_4 = 0.2, 0.3, 0.4
FACTORS_0_7, FACTORS_0_8, FACTORS_0_95 = 0.7, 0.8, 0.95
FACTORS_1_2, FACTORS_1_5 = 1.2, 1.5
FACTORS_12_5, FACTORS_20_0 = 12.5, 20.0
FACTORS_37_5, FACTORS_62_5, FACTORS_87_5 = 37.5, 62.5, 87.5

# LIMIT constants - Used for boundary checking and validation
LIMITS_1025, LIMITS_1026, LIMITS_1027, LIMITS_1028, LIMITS_1029 = (
    1025,
    1026,
    1027,
    1028,
    1029,
)
LIMITS_1030, LIMITS_1031, LIMITS_1032, LIMITS_1033, LIMITS_1034 = (
    1030,
    1031,
    1032,
    1033,
    1034,
)
LIMITS_1035, LIMITS_1036, LIMITS_1037, LIMITS_1038, LIMITS_1039 = (
    1035,
    1036,
    1037,
    1038,
    1039,
)
LIMITS_1040, LIMITS_1041, LIMITS_1042, LIMITS_1043, LIMITS_1044 = (
    1040,
    1041,
    1042,
    1043,
    1044,
)
LIMITS_1045, LIMITS_1046, LIMITS_1047, LIMITS_1048, LIMITS_1049 = (
    1045,
    1046,
    1047,
    1048,
    1049,
)
LIMITS_1050, LIMITS_1051, LIMITS_1052, LIMITS_1053, LIMITS_1054 = (
    1050,
    1051,
    1052,
    1053,
    1054,
)
LIMITS_1055, LIMITS_1056, LIMITS_1057, LIMITS_1058, LIMITS_1059 = (
    1055,
    1056,
    1057,
    1058,
    1059,
)
LIMITS_1060, LIMITS_1061, LIMITS_1062, LIMITS_1063, LIMITS_1069 = (
    1060,
    1061,
    1062,
    1063,
    1069,
)
LIMITS_1070, LIMITS_1071, LIMITS_1072, LIMITS_1073, LIMITS_1074 = (
    1070,
    1071,
    1072,
    1073,
    1074,
)
LIMITS_1075, LIMITS_1076, LIMITS_1077, LIMITS_1078, LIMITS_1080 = (
    1075,
    1076,
    1077,
    1078,
    1080,
)
LIMITS_1081, LIMITS_1082, LIMITS_1083 = 1081, 1082, 1083
LIMITS_1280, LIMITS_1364, LIMITS_1536 = 1280, 1364, 1536
LIMITS_2048, LIMITS_2049, LIMITS_2052, LIMITS_2055, LIMITS_2057 = (
    2048,
    2049,
    2052,
    2055,
    2057,
)
LIMITS_2058, LIMITS_2060, LIMITS_2064, LIMITS_2065, LIMITS_2066 = (
    2058,
    2060,
    2064,
    2065,
    2066,
)
LIMITS_2067, LIMITS_2068, LIMITS_2070, LIMITS_2072, LIMITS_2073 = (
    2067,
    2068,
    2070,
    2072,
    2073,
)
LIMITS_2074, LIMITS_2880 = 2074, 2880
LIMITS_3073, LIMITS_3076, LIMITS_3079, LIMITS_3081, LIMITS_3082 = (
    3073,
    3076,
    3079,
    3081,
    3082,
)
LIMITS_3084, LIMITS_4096, LIMITS_4097, LIMITS_4100, LIMITS_4103 = (
    3084,
    4096,
    4097,
    4100,
    4103,
)
LIMITS_4105, LIMITS_4108, LIMITS_5121, LIMITS_5127, LIMITS_5129 = (
    4105,
    4108,
    5121,
    5127,
    5129,
)
LIMITS_5132, LIMITS_6144, LIMITS_6145, LIMITS_7169, LIMITS_7177 = (
    5132,
    6144,
    6145,
    7169,
    7177,
)
LIMITS_8192, LIMITS_8193, LIMITS_9217 = 8192, 8193, 9217

# SIZE constants - Used for buffer and structure sizing
SIZES_101, SIZES_102, SIZES_103, SIZES_104, SIZES_105 = 101, 102, 103, 104, 105
SIZES_106, SIZES_107, SIZES_108, SIZES_109, SIZES_110 = 106, 107, 108, 109, 110
SIZES_111, SIZES_112, SIZES_113, SIZES_114, SIZES_115 = 111, 112, 113, 114, 115
SIZES_116, SIZES_117, SIZES_118, SIZES_119, SIZES_120 = 116, 117, 118, 119, 120
SIZES_121, SIZES_122, SIZES_123, SIZES_124, SIZES_125 = 121, 122, 123, 124, 125
SIZES_126, SIZES_127, SIZES_128, SIZES_129, SIZES_130 = 126, 127, 128, 129, 130
SIZES_131, SIZES_132, SIZES_133, SIZES_134, SIZES_135 = 131, 132, 133, 134, 135
SIZES_136, SIZES_137, SIZES_138, SIZES_139, SIZES_140 = 136, 137, 138, 139, 140
SIZES_141, SIZES_142, SIZES_143, SIZES_144, SIZES_145 = 141, 142, 143, 144, 145
SIZES_146, SIZES_147, SIZES_148, SIZES_149, SIZES_150 = 146, 147, 148, 149, 150
SIZES_151, SIZES_152, SIZES_153, SIZES_154, SIZES_155 = 151, 152, 153, 154, 155
SIZES_156, SIZES_157, SIZES_158, SIZES_159, SIZES_160 = 156, 157, 158, 159, 160
SIZES_161, SIZES_162, SIZES_163, SIZES_164, SIZES_165 = 161, 162, 163, 164, 165
SIZES_166, SIZES_167, SIZES_168, SIZES_169, SIZES_170 = 166, 167, 168, 169, 170
SIZES_171, SIZES_172, SIZES_173, SIZES_174, SIZES_175 = 171, 172, 173, 174, 175
SIZES_176, SIZES_177, SIZES_178, SIZES_179, SIZES_180 = 176, 177, 178, 179, 180
SIZES_181, SIZES_182, SIZES_183, SIZES_184, SIZES_185 = 181, 182, 183, 184, 185
SIZES_186, SIZES_187, SIZES_188, SIZES_189, SIZES_190 = 186, 187, 188, 189, 190
SIZES_191, SIZES_192, SIZES_193, SIZES_194, SIZES_195 = 191, 192, 193, 194, 195
SIZES_196, SIZES_197, SIZES_198, SIZES_199, SIZES_202 = 196, 197, 198, 199, 202
SIZES_203, SIZES_205, SIZES_206, SIZES_207, SIZES_208 = 203, 205, 206, 207, 208
SIZES_209, SIZES_210, SIZES_211, SIZES_212, SIZES_213 = 209, 210, 211, 212, 213
SIZES_214, SIZES_215, SIZES_216, SIZES_217, SIZES_218 = 214, 215, 216, 217, 218
SIZES_219, SIZES_220, SIZES_221, SIZES_222, SIZES_223 = 219, 220, 221, 222, 223
SIZES_224, SIZES_225, SIZES_226, SIZES_227, SIZES_228 = 224, 225, 226, 227, 228
SIZES_229, SIZES_230, SIZES_231, SIZES_232, SIZES_233 = 229, 230, 231, 232, 233
SIZES_234, SIZES_235, SIZES_236, SIZES_237, SIZES_238 = 234, 235, 236, 237, 238
SIZES_239, SIZES_240, SIZES_241, SIZES_242, SIZES_243 = 239, 240, 241, 242, 243
SIZES_244, SIZES_245, SIZES_246, SIZES_247, SIZES_248 = 244, 245, 246, 247, 248
SIZES_249, SIZES_250, SIZES_251, SIZES_252, SIZES_253 = 249, 250, 251, 252, 253
SIZES_254, SIZES_255, SIZES_256, SIZES_257, SIZES_258 = 254, 255, 256, 257, 258
SIZES_259, SIZES_260, SIZES_261, SIZES_262, SIZES_263 = 259, 260, 261, 262, 263
SIZES_264, SIZES_265, SIZES_266, SIZES_267, SIZES_268 = 264, 265, 266, 267, 268
SIZES_269, SIZES_270, SIZES_271, SIZES_272, SIZES_273 = 269, 270, 271, 272, 273
SIZES_274, SIZES_275, SIZES_276, SIZES_277, SIZES_278 = 274, 275, 276, 277, 278
SIZES_279, SIZES_280, SIZES_281, SIZES_282, SIZES_283 = 279, 280, 281, 282, 283
SIZES_284, SIZES_285, SIZES_286, SIZES_287, SIZES_288 = 284, 285, 286, 287, 288
SIZES_289, SIZES_290, SIZES_291, SIZES_292, SIZES_293 = 289, 290, 291, 292, 293
SIZES_294, SIZES_295, SIZES_296, SIZES_297, SIZES_298 = 294, 295, 296, 297, 298
SIZES_299, SIZES_300 = 299, 300
# Additional key sizes used frequently
SIZES_333, SIZES_334, SIZES_335, SIZES_336, SIZES_337 = 333, 334, 335, 336, 337
SIZES_338, SIZES_339, SIZES_340, SIZES_354, SIZES_355 = 338, 339, 340, 354, 355
SIZES_356, SIZES_357, SIZES_358, SIZES_359, SIZES_360 = 356, 357, 358, 359, 360
SIZES_361, SIZES_369, SIZES_370, SIZES_381, SIZES_382 = 361, 369, 370, 381, 382
SIZES_383, SIZES_384, SIZES_385, SIZES_386, SIZES_387 = 383, 384, 385, 386, 387
SIZES_388, SIZES_394, SIZES_395, SIZES_396, SIZES_397 = 388, 394, 395, 396, 397
SIZES_398, SIZES_399, SIZES_405, SIZES_406, SIZES_407 = 398, 399, 405, 406, 407
SIZES_408, SIZES_409, SIZES_410, SIZES_411, SIZES_412 = 408, 409, 410, 411, 412
SIZES_413, SIZES_414, SIZES_415, SIZES_416, SIZES_417 = 413, 414, 415, 416, 417
SIZES_418, SIZES_419, SIZES_420, SIZES_421, SIZES_422 = 418, 419, 420, 421, 422
SIZES_423, SIZES_424, SIZES_425, SIZES_426, SIZES_427 = 423, 424, 425, 426, 427
SIZES_428, SIZES_429, SIZES_430, SIZES_431, SIZES_432 = 428, 429, 430, 431, 432
SIZES_433, SIZES_434, SIZES_435, SIZES_436, SIZES_437 = 433, 434, 435, 436, 437
SIZES_438, SIZES_439, SIZES_440, SIZES_441, SIZES_442 = 438, 439, 440, 441, 442
SIZES_443, SIZES_444, SIZES_445, SIZES_446, SIZES_447 = 443, 444, 445, 446, 447
SIZES_448, SIZES_458, SIZES_472, SIZES_473, SIZES_474 = 448, 458, 472, 473, 474
SIZES_475, SIZES_476, SIZES_477, SIZES_478, SIZES_479 = 475, 476, 477, 478, 479
SIZES_480, SIZES_481, SIZES_482, SIZES_483, SIZES_484 = 480, 481, 482, 483, 484
SIZES_504, SIZES_511, SIZES_512, SIZES_525, SIZES_526 = 504, 511, 512, 525, 526
SIZES_527, SIZES_528, SIZES_529, SIZES_530, SIZES_531 = 527, 528, 529, 530, 531
SIZES_532, SIZES_533, SIZES_534, SIZES_535, SIZES_539 = 532, 533, 534, 535, 539
SIZES_540, SIZES_547, SIZES_577, SIZES_578, SIZES_579 = 540, 547, 577, 578, 579
SIZES_580, SIZES_581, SIZES_582, SIZES_583 = 580, 581, 582, 583
SIZES_600, SIZES_800 = 600, 800

# MISCELLANEOUS constants - Various numeric values used throughout the system
MISC_10000, MISC_10241, MISC_11265, MISC_12289 = 10000, 10241, 11265, 12289
MISC_13313, MISC_14337, MISC_15361, MISC_16383 = 13313, 14337, 15361, 16383
MISC_16384, MISC_16503, MISC_32767, MISC_32768 = 16384, 16503, 32767, 32768
MISC_49152, MISC_50000, MISC_65534, MISC_65535 = 49152, 50000, 65534, 65535
MISC_65536, MISC_100000, MISC_999999 = 65536, 100000, 999999
MISC_16777216, MISC_100000000, MISC_268435456 = 16777216, 100000000, 268435456
MISC_282444864, MISC_4294967293, MISC_4294967294, MISC_4294967295 = (
    282444864,
    4294967293,
    4294967294,
    4294967295,
)

# PowerBuilder-specific magic numbers
MISC_1146047862, MISC_1329744452, MISC_5391432 = 1146047862, 1329744452, 5391432
MISC_1397836832, MISC_1919249509 = 1397836832, 1919249509

# Version and system IDs (16xxx range)
MISC_16385, MISC_16386, MISC_16387, MISC_16388, MISC_16389 = (
    16385,
    16386,
    16387,
    16388,
    16389,
)
MISC_16390, MISC_16391, MISC_16392, MISC_16393, MISC_16394 = (
    16390,
    16391,
    16392,
    16393,
    16394,
)
MISC_16395, MISC_16396, MISC_16397, MISC_16398, MISC_16399 = (
    16395,
    16396,
    16397,
    16398,
    16399,
)
MISC_16400, MISC_16401, MISC_16402, MISC_16403, MISC_16404 = (
    16400,
    16401,
    16402,
    16403,
    16404,
)
MISC_16417, MISC_16431, MISC_16458, MISC_16469, MISC_16470 = (
    16417,
    16431,
    16458,
    16469,
    16470,
)
MISC_16498, MISC_16701 = 16498, 16701

# System function IDs (42xxx-53xxx range)
MISC_42844, MISC_45332, MISC_45344, MISC_45356, MISC_45368 = (
    42844,
    45332,
    45344,
    45356,
    45368,
)
MISC_45380, MISC_45460, MISC_45472, MISC_45484, MISC_45496 = (
    45380,
    45460,
    45472,
    45484,
    45496,
)
MISC_45508, MISC_46780, MISC_46840, MISC_48976, MISC_49044 = (
    45508,
    46780,
    46840,
    48976,
    49044,
)
MISC_49148, MISC_49216, MISC_50076, MISC_50212, MISC_50224 = (
    49148,
    49216,
    50076,
    50212,
    50224,
)
MISC_51996, MISC_52056, MISC_53476, MISC_53548, MISC_53656 = (
    51996,
    52056,
    53476,
    53548,
    53656,
)

# Large P-code related constants (282xxx range) - Used in P-code processing
MISC_282411680, MISC_282412624, MISC_282413632, MISC_282413824 = (
    282411680,
    282412624,
    282413632,
    282413824,
)
MISC_282427568, MISC_282427760, MISC_282427840, MISC_282428224 = (
    282427568,
    282427760,
    282427840,
    282428224,
)
MISC_282435216, MISC_282438352, MISC_282439136, MISC_282444944 = (
    282435216,
    282438352,
    282439136,
    282444944,
)
MISC_282445072, MISC_282445136, MISC_282445200, MISC_282445232 = (
    282445072,
    282445136,
    282445200,
    282445232,
)
MISC_282445264, MISC_282445296, MISC_282445328, MISC_282445616 = (
    282445264,
    282445296,
    282445328,
    282445616,
)
MISC_282446000, MISC_282446064, MISC_282446160, MISC_282446192 = (
    282446000,
    282446064,
    282446160,
    282446192,
)
MISC_282449216, MISC_282449920, MISC_282450048, MISC_282450176 = (
    282449216,
    282449920,
    282450048,
    282450176,
)
MISC_282451552, MISC_282451680, MISC_282451840, MISC_282452128 = (
    282451552,
    282451680,
    282451840,
    282452128,
)

# =============================================================================
# EXCEPTIONS AND ERRORS
# =============================================================================


class InfrastructureError(Exception):
    """Base exception for all infrastructure errors."""

    def __init__(
        self, message: str, error_code: str | None = None, **kwargs: Any
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = kwargs

    def __str__(self) -> str:
        parts = []
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        parts.append(self.message)
        return " ".join(parts)


class SecurityError(InfrastructureError):
    """Security-related infrastructure error."""


class PathTraversalError(SecurityError):
    """Path traversal attempt detected."""


class ResourceLimitError(InfrastructureError):
    """Resource limit exceeded."""

    def __init__(
        self, resource: str, limit: int, requested: int, **kwargs: Any
    ) -> None:
        message = f"Resource limit exceeded for {resource}: requested {requested}, limit {limit}"
        super().__init__(
            message, resource=resource, limit=limit, requested=requested, **kwargs
        )
        self.resource = resource
        self.limit = limit
        self.requested = requested


class CircuitBreakerError(InfrastructureError):
    """Circuit breaker is open."""

    def __init__(self, message: str, last_failure_time: float | None = None) -> None:
        super().__init__(message)
        self.last_failure_time = last_failure_time


class PipelineError(InfrastructureError):
    """Pipeline-level error."""


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================


class ErrorSeverity(Enum):
    """Error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Error recovery strategies."""

    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    FAIL = "fail"
    CONTINUE = "continue"


class LogFormat(Enum):
    """Available log output formats."""

    TEXT = "text"
    JSON = "json"
    SIMPLE = "simple"


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class BackendType(Enum):
    """Available distributed processing backends."""

    MULTIPROCESSING = "multiprocessing"
    THREADING = "threading"
    CELERY = "celery"
    RAY = "ray"
    ASYNCIO = "asyncio"


class JobStatus(Enum):
    """Status of a distributed job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


# Re-export logging levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# =============================================================================
# CACHING SECTION
# =============================================================================


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    key: str
    value: Any
    size: int
    created_at: float
    accessed_at: float
    access_count: int = 0

    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1


class LRUCache:
    """Thread-safe LRU cache implementation."""

    def __init__(self, max_size: int = 1000, max_memory: int | None = None) -> None:
        self.max_size = max_size
        self.max_memory = max_memory or (1024 * 1024 * 512)  # 512MB default
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._current_memory = 0
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                entry.touch()
                self._cache[key] = entry
                self._hits += 1
                return entry.value
            self._misses += 1
            return None

    async def put(self, key: str, value: Any, size: int | None = None) -> None:
        """Put value in cache."""
        if size is None:
            try:
                import pickle

                size = len(pickle.dumps(value))
            except Exception:
                size = sys.getsizeof(value)

        async with self._lock:
            if key in self._cache:
                old_entry = self._cache.pop(key)
                self._current_memory -= old_entry.size

            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                created_at=time.time(),
                accessed_at=time.time(),
            )

            self._cache[key] = entry
            self._current_memory += size
            await self._evict_if_needed()

    async def _evict_if_needed(self) -> None:
        """Evict entries if cache is full."""
        while len(self._cache) > self.max_size:
            key, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size

        while self._current_memory > self.max_memory:
            if not self._cache:
                break
            key, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size

    async def clear(self) -> None:
        """Clear the cache."""
        async with self._lock:
            self._cache.clear()
            self._current_memory = 0
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {
            "size": len(self._cache),
            "memory": self._current_memory,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


class FileCache:
    """File-based cache for persistent storage."""

    def __init__(self, cache_dir: str | Path, ttl: int = 3600) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self._index_file = self.cache_dir / ".cache_index.json"
        self._index: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            if key not in self._index:
                return None

            entry = self._index[key]
            if time.time() - entry["created_at"] > self.ttl:
                await self._remove_entry(key)
                return None

            cache_path = Path(entry["path"])
            if not await aiofiles.os.path.exists(cache_path):
                del self._index[key]
                return None

            try:
                async with aiofiles.open(cache_path, "rb") as f:
                    data = await f.read()
                    import pickle

                    return pickle.loads(data)
            except Exception:
                await self._remove_entry(key)
                return None

    async def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        async with self._lock:
            try:
                import pickle

                data = pickle.dumps(value)
                cache_path = self._get_cache_path(key)
                cache_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(cache_path, "wb") as f:
                    await f.write(data)

                self._index[key] = {
                    "created_at": time.time(),
                    "size": len(data),
                    "path": str(cache_path),
                }
            except Exception:
                if key in self._index:
                    del self._index[key]

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash[:2]}" / f"{key_hash}.cache"

    async def _remove_entry(self, key: str) -> None:
        """Remove cache entry."""
        if key in self._index:
            entry = self._index[key]
            cache_path = Path(entry["path"])
            try:
                if await aiofiles.os.path.exists(cache_path):
                    await aiofiles.os.remove(cache_path)
            except Exception:
                pass
            del self._index[key]

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            for key in list(self._index.keys()):
                await self._remove_entry(key)
            self._index.clear()


@dataclass
class CacheConfig:
    """Configuration for a cache instance."""

    enabled: bool = True
    type: str = "memory"  # "memory", "file", or "hybrid"
    size: int = 1000
    memory: int = 512  # MB
    ttl: int = 3600
    directory: Path | None = None


class CacheManager:
    """Manages caches for all pipeline stages."""

    def __init__(self, base_config: dict[str, Any] | None = None) -> None:
        self.config = base_config or {}
        self.enabled = self._get_bool_env("POWERREBUILDER_CACHE_ENABLED", True)

        cache_dir = os.getenv(
            "POWERREBUILDER_CACHE_DIR", str(Path.home() / ".powerrebuilder" / "cache")
        )
        self.base_cache_dir = Path(cache_dir)
        self.base_cache_dir.mkdir(parents=True, exist_ok=True)
        self._caches: dict[str, Any] = {}

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "yes", "1", "on")

    def get_cache(self, stage: str) -> Any:
        """Get cache for a specific stage."""
        if not self.enabled:
            return None
        return self._caches.get(stage)


# =============================================================================
# CIRCUIT BREAKER SECTION
# =============================================================================


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 60.0
    expected_exceptions: tuple[type[Exception], ...] | None = None
    excluded_exceptions: tuple[type[Exception], ...] | None = None
    on_state_change: Callable[[CircuitState, CircuitState], None] | None = None


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    total_calls: int = 0
    rejected_calls: int = 0
    state_changes: list[tuple[CircuitState, CircuitState, float]] = field(
        default_factory=list
    )


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = threading.RLock()

    def _should_catch_exception(self, exception: Exception) -> bool:
        """Check if exception should trigger circuit breaker."""
        if self.config.excluded_exceptions:
            if isinstance(exception, self.config.excluded_exceptions):
                return False

        if self.config.expected_exceptions:
            return isinstance(exception, self.config.expected_exceptions)
        return True

    def _change_state(self, new_state: CircuitState) -> None:
        """Change circuit breaker state."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.stats.state_changes.append((old_state, new_state, time.time()))
            if self.config.on_state_change:
                self.config.on_state_change(old_state, new_state)

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call function through circuit breaker."""
        with self._lock:
            self.stats.total_calls += 1

            if self._should_attempt_reset():
                self._change_state(CircuitState.HALF_OPEN)
                self.stats.success_count = 0

            if self.state == CircuitState.OPEN:
                self.stats.rejected_calls += 1
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN (failures: {self.stats.failure_count})",
                    self.stats.last_failure_time,
                )

        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            if self._should_catch_exception(e):
                self._handle_failure(e)
            raise

    def _handle_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self.stats.success_count += 1
            self.stats.last_success_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._change_state(CircuitState.CLOSED)
                    self.stats.failure_count = 0
                    self.stats.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.stats.failure_count = 0

    def _handle_failure(self, _exception: Exception) -> None:
        """Handle failed call."""
        with self._lock:
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()

            if self.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._change_state(CircuitState.OPEN)
            elif self.state == CircuitState.HALF_OPEN:
                self._change_state(CircuitState.OPEN)
                self.stats.success_count = 0

    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit."""
        return (
            self.state == CircuitState.OPEN
            and self.stats.last_failure_time is not None
            and time.time() - self.stats.last_failure_time >= self.config.timeout
        )

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "state": self.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_calls": self.stats.total_calls,
            "rejected_calls": self.stats.rejected_calls,
        }


class CircuitBreakerManager:
    """Manage multiple circuit breakers."""

    def __init__(self) -> None:
        self.breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_or_create(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get or create a named circuit breaker."""
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(config)
            return self.breakers[name]

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {
                name: breaker.get_stats() for name, breaker in self.breakers.items()
            }


# =============================================================================
# COORDINATION SECTION
# =============================================================================


class CoordinatorMixin:
    """Unified mixin providing all coordinator functionality."""

    def __init__(self) -> None:
        self._stats: dict[str, Any] = self._create_default_stats()
        self._progress_callback: Callable[[str, float], None] | None = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_default_stats(self) -> dict[str, Any]:
        """Create default statistics dictionary."""
        return {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Get current statistics."""
        return self._stats.copy()

    def add_error(self, error: str | Exception, context: str | None = None) -> None:
        """Add an error to statistics."""
        error_info = {
            "message": str(error),
            "type": type(error).__name__ if isinstance(error, Exception) else "error",
            "timestamp": datetime.now().isoformat(),
        }
        if context:
            error_info["context"] = context
        self._stats["errors"].append(error_info)
        self._stats["failed"] = self._stats.get("failed", 0) + 1

    def set_progress_callback(
        self, callback: Callable[[str, float], None] | None
    ) -> None:
        """Set progress callback function."""
        self._progress_callback = callback

    def validate_paths(
        self, input_path: Path | None = None, output_path: Path | None = None
    ) -> bool:
        """Validate input and output paths."""
        if not input_path or not input_path.exists():
            return False
        if output_path:
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception:
                return False
        return True


class BaseCoordinator(ABC):
    """Base coordinator interface for all pipeline stages."""

    def __init__(self, input_path: Path, output_path: Path) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self._statistics: dict[str, Any] = {
            "files_processed": 0,
            "files_failed": 0,
            "errors": [],
            "warnings": [],
        }

    @abstractmethod
    def process(self) -> dict[str, Any]:
        """Process input files and produce output."""

    @abstractmethod
    def validate_inputs(self) -> bool:
        """Validate input requirements for the stage."""

    def get_statistics(self) -> dict[str, Any]:
        """Get processing statistics."""
        return self._statistics.copy()

    def ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_path.mkdir(parents=True, exist_ok=True)


# =============================================================================
# DISTRIBUTED SECTION
# =============================================================================


@dataclass
class JobResult[R]:
    """Result of a distributed job execution."""

    job_id: str
    status: JobStatus
    result: R | None = None
    error: Exception | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    retry_count: int = 0
    worker_id: str | None = None

    @property
    def duration(self) -> float | None:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_success(self) -> bool:
        return self.status == JobStatus.COMPLETED and self.error is None


@dataclass
class WorkerConfig:
    """Configuration for worker processes."""

    num_workers: int = mp.cpu_count()
    max_tasks_per_worker: int | None = None
    timeout: float | None = None
    retry_attempts: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"
    resource_limits: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskMetrics:
    """Metrics for task execution."""

    tasks_submitted: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_retried: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0


class MultiprocessingBackend:
    """Distributed backend using Python multiprocessing."""

    def __init__(self, config: WorkerConfig) -> None:
        self.config = config
        self.metrics = TaskMetrics()
        self._executor = ProcessPoolExecutor(
            max_workers=config.num_workers,
            mp_context=mp.get_context("spawn"),
        )
        self._shutdown = False

    def submit(self, func: Callable[[T], R], *args: T, **kwargs: Any) -> Future[R]:
        """Submit a task for execution."""
        if self._shutdown:
            raise PipelineError("Backend is shutdown")
        self.metrics.tasks_submitted += 1
        return self._executor.submit(func, *args, **kwargs)

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend."""
        self._shutdown = True
        self._executor.shutdown(wait=wait)

    def get_metrics(self) -> TaskMetrics:
        """Get execution metrics."""
        if self.metrics.tasks_completed > 0:
            self.metrics.avg_duration = (
                self.metrics.total_duration / self.metrics.tasks_completed
            )
        return self.metrics


class DistributedCoordinator:
    """Coordinator for distributed task execution."""

    def __init__(
        self,
        backend_type: BackendType = BackendType.MULTIPROCESSING,
        config: WorkerConfig | None = None,
    ) -> None:
        self.backend_type = backend_type
        self.config = config or WorkerConfig()
        self.backend = self._create_backend()

    def _create_backend(self):
        """Create backend based on type."""
        if self.backend_type == BackendType.MULTIPROCESSING:
            return MultiprocessingBackend(self.config)
        raise ValueError(f"Unknown backend type: {self.backend_type}")

    def submit_task(
        self, func: Callable[[T], R], *args: T, **kwargs: Any
    ) -> tuple[str, Future[R]]:
        """Submit a task and return job ID and future."""
        job_id = str(uuid.uuid4())
        future = self.backend.submit(func, *args, **kwargs)
        return job_id, future

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the coordinator."""
        self.backend.shutdown(wait=wait)


# =============================================================================
# EVENTS SECTION
# =============================================================================


class EventHandler(IEventHandler):
    """Basic event handler implementation."""

    def __init__(
        self,
        handler_func: Callable[[Event], None],
        event_types: set[EventType] | None = None,
    ) -> None:
        self.handler_func = handler_func
        self.event_types = event_types or set(EventType)

    def handle(self, event: Event) -> None:
        """Handle an event."""
        self.handler_func(event)

    def can_handle(self, event_type: EventType) -> bool:
        """Check if handler can handle event type."""
        return event_type in self.event_types


class EventBus(IEventBus):
    """Event bus implementation with comprehensive functionality."""

    def __init__(self, history_size: int = 1000, enable_async: bool = True) -> None:
        self._handlers: dict[EventType, list[weakref.ref]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: list[Event] = []
        self._history_size = history_size
        self._enable_async = enable_async
        self._stats = {"published": 0, "delivered": 0, "failed": 0}

        if enable_async:
            self._event_queue: Queue[Event] = Queue()
            self._processing_thread = threading.Thread(
                target=self._process_events, daemon=True
            )
            self._processing_thread.start()

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers."""
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._history_size:
                self._history.pop(0)
            self._stats["published"] += 1

            handlers = self._get_active_handlers(event.type)
            if self._enable_async:
                self._event_queue.put((event, handlers))
            else:
                self._deliver_event(event, handlers)

    def subscribe(self, event_type: EventType, handler: IEventHandler) -> None:
        """Subscribe to an event type."""
        with self._lock:
            handler_ref = weakref.ref(
                handler, self._create_cleanup_callback(event_type)
            )
            if handler_ref not in self._handlers[event_type]:
                self._handlers[event_type].append(handler_ref)

    def get_handlers(self, event_type: EventType) -> list[IEventHandler]:
        """Get all handlers for an event type."""
        with self._lock:
            return self._get_active_handlers(event_type)

    def _get_active_handlers(self, event_type: EventType) -> list[IEventHandler]:
        """Get active handlers."""
        active_handlers = []
        dead_refs = []

        for handler_ref in self._handlers[event_type]:
            handler = handler_ref()
            if handler is not None:
                active_handlers.append(handler)
            else:
                dead_refs.append(handler_ref)

        for dead_ref in dead_refs:
            self._handlers[event_type].remove(dead_ref)

        return active_handlers

    def _create_cleanup_callback(self, event_type: EventType) -> Callable:
        """Create cleanup callback for weak references."""

        def cleanup(ref) -> None:
            with self._lock:
                try:
                    self._handlers[event_type].remove(ref)
                except ValueError:
                    pass

        return cleanup

    def _deliver_event(self, event: Event, handlers: list[IEventHandler]) -> None:
        """Deliver event to handlers."""
        for handler in handlers:
            try:
                if handler.can_handle(event.type):
                    handler.handle(event)
                    self._stats["delivered"] += 1
            except Exception:
                self._stats["failed"] += 1

    def _process_events(self) -> None:
        """Process events from queue."""
        while True:
            try:
                event, handlers = self._event_queue.get(timeout=1)
                self._deliver_event(event, handlers)
            except Empty:
                continue
            except Exception:
                pass

    def get_statistics(self) -> dict[str, int]:
        """Get event bus statistics."""
        with self._lock:
            return self._stats.copy()


# =============================================================================
# LOGGING SECTION
# =============================================================================


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "getMessage",
            ]:
                log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored text formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class PipelineLogger:
    """Enhanced logger for pipeline operations."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._context: dict[str, Any] = {}
        self._stage: str | None = None
        self._start_times: dict[str, float] = {}

    def _log_with_context(
        self, level: int, msg: str, *args: Any, **kwargs: Any
    ) -> None:
        """Log message with current context."""
        extra = kwargs.get("extra", {})
        extra.update(self._context)
        if self._stage:
            extra["stage"] = self._stage
        kwargs["extra"] = extra
        self._logger.log(level, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message with context."""
        self._log_with_context(DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message with context."""
        self._log_with_context(INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message with context."""
        self._log_with_context(WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log error message with context."""
        self._log_with_context(ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log critical message with context."""
        self._log_with_context(CRITICAL, msg, *args, **kwargs)

    def set_context(self, **kwargs: Any) -> None:
        """Set persistent context fields."""
        self._context.update(kwargs)

    @contextlib.contextmanager
    def context(self, **kwargs: Any):
        """Context manager for temporary context fields."""
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield
        finally:
            self._context = old_context

    def stage_start(self, stage_name: str, **kwargs: Any) -> None:
        """Log the start of a pipeline stage."""
        self._stage = stage_name
        self._start_times[stage_name] = time.time()
        self.info("Starting stage: %s", stage_name, extra=kwargs)

    def stage_end(self, stage_name: str, success: bool = True, **kwargs: Any) -> None:
        """Log the end of a pipeline stage."""
        duration = None
        if stage_name in self._start_times:
            duration = time.time() - self._start_times[stage_name]
            del self._start_times[stage_name]
            kwargs["duration_seconds"] = duration

        level = INFO if success else ERROR
        status = "completed" if success else "failed"
        self._log_with_context(level, f"Stage {stage_name} {status}", extra=kwargs)
        self._stage = None


def setup_logging(
    level: int | str = INFO,
    log_file: str | Path | None = None,
    log_format: LogFormat = LogFormat.TEXT,
    console: bool = True,
) -> None:
    """Set up logging configuration."""
    if isinstance(level, str):
        level = getattr(logging, level.upper(), INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    # Set up formatters
    if log_format == LogFormat.JSON:
        formatter = StructuredFormatter()
    elif log_format == LogFormat.SIMPLE:
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    elif console and hasattr(sys.stderr, "isatty") and sys.stderr.isatty():
        formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        from logging.handlers import RotatingFileHandler

        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(log_path), maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> PipelineLogger:
    """Get a pipeline-aware logger instance."""
    return PipelineLogger(logging.getLogger(name))


# =============================================================================
# RECOVERY SECTION
# =============================================================================


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ) -> None:
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(
            self.initial_delay * (self.exponential_base**attempt), self.max_delay
        )
        if self.jitter:
            import random

            delay *= 1 + random.random() * 0.25
        return delay


class RecoveryContext:
    """Context information for recovery operations."""

    def __init__(self) -> None:
        self.checkpoints: dict[str, Any] = {}
        self.error_history: list[Exception] = []
        self.recovery_attempts: int = 0
        self.start_time: datetime = datetime.now()
        self.metadata: dict[str, Any] = {}

    def add_checkpoint(self, name: str, data: Any) -> None:
        """Add a recovery checkpoint."""
        self.checkpoints[name] = {
            "timestamp": datetime.now(),
            "data": data,
        }

    def get_checkpoint(self, name: str) -> Any:
        """Get checkpoint data."""
        checkpoint = self.checkpoints.get(name)
        return checkpoint["data"] if checkpoint else None


def retry_with_backoff(
    config: RetryConfig | None = None,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] | None = None,
) -> Callable[[F], F]:
    """Decorator for retrying functions with exponential backoff."""
    if config is None:
        config = RetryConfig()

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == config.max_attempts - 1:
                        raise
                    delay = config.get_delay(attempt)
                    if on_retry:
                        on_retry(e, attempt)
                    time.sleep(delay)
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry logic error")

        return wrapper  # type: ignore

    return decorator


class FileCorruptionRecovery:
    """Recovery strategy for file corruption errors."""

    def __init__(self, backup_dir: Path | None = None) -> None:
        self.backup_dir = backup_dir or Path.home() / ".powerrebuilder" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: Path) -> Path:
        """Create a backup of a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(file_path, backup_path)
        return backup_path


# =============================================================================
# RESOURCE MANAGEMENT SECTION
# =============================================================================


@dataclass
class ResourceLimits:
    """Configuration for resource limits."""

    max_file_size: int = 100 * 1024 * 1024  # 100 MB
    max_total_size: int = 1024 * 1024 * 1024  # 1 GB
    max_memory_percent: float = 80.0
    max_memory_bytes: int | None = None
    max_processing_time: float = 300.0
    max_total_time: float = 3600.0
    max_file_count: int = 10000
    max_depth: int = 20
    max_buffer_size: int = 10 * 1024 * 1024

    def __post_init__(self):
        if self.max_memory_bytes is None:
            total_memory = psutil.virtual_memory().total
            self.max_memory_bytes = int(total_memory * self.max_memory_percent / 100)


class ResourceMonitor:
    """Monitor resource usage and enforce limits."""

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        self.limits = limits or ResourceLimits()
        self.start_time = time.time()
        self.file_count = 0
        self.total_size = 0
        self.process = psutil.Process(os.getpid())

    def check_file_size(self, size: int, filename: str = "") -> None:
        """Check if a file size is within limits."""
        if size > self.limits.max_file_size:
            raise ResourceLimitError("file_size", self.limits.max_file_size, size)

    def check_memory_usage(self) -> None:
        """Check current memory usage against limits."""
        memory_info = self.process.memory_info()
        current_memory = memory_info.rss
        if current_memory > self.limits.max_memory_bytes:
            raise ResourceLimitError(
                "memory", self.limits.max_memory_bytes, current_memory
            )

    def register_file(self, size: int) -> None:
        """Register a processed file."""
        self.file_count += 1
        self.total_size += size

    def get_stats(self) -> dict:
        """Get current resource usage statistics."""
        memory_info = self.process.memory_info()
        elapsed = time.time() - self.start_time
        return {
            "file_count": self.file_count,
            "total_size": self.total_size,
            "memory_usage": memory_info.rss,
            "memory_percent": psutil.virtual_memory().percent,
            "elapsed_time": elapsed,
            "cpu_percent": self.process.cpu_percent(),
        }


def with_timeout(timeout: float):
    """Decorator to add timeout to a function."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]

            def target() -> None:
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                raise ResourceLimitError("time", int(timeout), int(timeout + 1))
            if exception[0]:
                raise exception[0]
            return result[0]

        return wrapper

    return decorator


# =============================================================================
# SECURITY SECTION
# =============================================================================


class PathValidator:
    """Validates file paths to prevent directory traversal attacks."""

    DANGEROUS_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"\.\.(?:/|\\|$)",
        r"^~",
        r"^\$",
        r"\\\\",
    ]
    UNSAFE_CHARS = set('<>:"|?*\0')

    @classmethod
    def validate_path(cls, path: str | Path, base_dir: str | Path) -> Path:
        """Validate a path is safe and within the base directory."""
        path = Path(path)
        base_dir = Path(base_dir).resolve()

        # Check for dangerous patterns
        path_str = str(path)
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                raise PathTraversalError(f"Dangerous path pattern detected: {path_str}")

        # Check for unsafe characters
        for part in path.parts:
            if any(char in part for char in cls.UNSAFE_CHARS):
                raise PathTraversalError(f"Unsafe characters in path component: {part}")

        # Resolve the full path
        try:
            if path.is_absolute():
                full_path = path.resolve()
            else:
                full_path = (base_dir / path).resolve()
        except (OSError, RuntimeError) as e:
            raise PathTraversalError(f"Path resolution failed: {e}") from e

        # Ensure the resolved path is within base_dir
        try:
            full_path.relative_to(base_dir)
        except ValueError:
            raise PathTraversalError(
                f"Path {full_path} is outside base directory {base_dir}"
            )

        return full_path

    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Validate a filename is safe."""
        filename = os.path.basename(filename)
        if not filename or filename in (".", ".."):
            raise PathTraversalError(f"Invalid filename: {filename}")

        if any(char in filename for char in cls.UNSAFE_CHARS):
            raise PathTraversalError(f"Unsafe characters in filename: {filename}")

        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        name_without_ext = filename.split(".")[0].upper()
        if name_without_ext in reserved_names:
            raise PathTraversalError(f"Reserved filename: {filename}")

        return filename


def safe_join_path(base_dir: str | Path, *parts: str) -> Path:
    """Safely join path components and validate the result."""
    base_dir = Path(base_dir).resolve()
    safe_parts = []
    for part in parts:
        if not part:
            continue
        part = part.strip("/\\")
        if part:
            safe_parts.append(PathValidator.validate_filename(part))

    if safe_parts:
        path = Path(*safe_parts)
        return PathValidator.validate_path(path, base_dir)
    return base_dir


def safe_write_file(
    path: str | Path, content: str | bytes, base_dir: str | Path, mode: str = "w"
) -> Path:
    """Safely write content to a file after validating the path."""
    safe_path = PathValidator.validate_path(path, base_dir)
    safe_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, bytes) and "b" not in mode:
        mode += "b"

    with safe_path.open(mode) as f:
        f.write(content)

    return safe_path


# =============================================================================
# STATE MANAGEMENT SECTION
# =============================================================================


@dataclass
class StageState:
    """State of a single pipeline stage."""

    name: str
    status: StageStatus = StageStatus.PENDING
    start_time: datetime | None = None
    end_time: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    checkpoint_id: str | None = None


@dataclass
class PipelineState(IPipelineState):
    """Implementation of pipeline state."""

    id: str
    stages: dict[str, StageState] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    checkpoints: dict[str, dict[str, Any]] = field(default_factory=dict)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False, compare=False
    )

    def get_stage_status(self, stage: str) -> StageStatus:
        """Get status of a stage."""
        with self._lock:
            if stage in self.stages:
                return self.stages[stage].status
            return StageStatus.PENDING

    def set_stage_status(self, stage: str, status: StageStatus) -> None:
        """Set status of a stage."""
        with self._lock:
            if stage not in self.stages:
                self.stages[stage] = StageState(name=stage)

            stage_state = self.stages[stage]
            stage_state.status = status

            if status == StageStatus.RUNNING:
                stage_state.start_time = datetime.now()
                if self.start_time is None:
                    self.start_time = stage_state.start_time
            elif status in [StageStatus.COMPLETED, StageStatus.FAILED]:
                stage_state.end_time = datetime.now()

            all_complete = all(
                s.status
                in [StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.ROLLED_BACK]
                for s in self.stages.values()
            )
            if all_complete and self.end_time is None:
                self.end_time = datetime.now()

    def get_stage_result(self, stage: str) -> dict[str, Any] | None:
        """Get result of a stage."""
        with self._lock:
            if stage in self.stages:
                return self.stages[stage].result
            return None

    def set_stage_result(self, stage: str, result: dict[str, Any]) -> None:
        """Set result of a stage."""
        with self._lock:
            if stage not in self.stages:
                self.stages[stage] = StageState(name=stage)
            self.stages[stage].result = result

    def get_context(self) -> dict[str, Any]:
        """Get pipeline context."""
        with self._lock:
            return self.context.copy()

    def update_context(self, updates: dict[str, Any]) -> None:
        """Update pipeline context."""
        with self._lock:
            self.context.update(updates)

    def get_start_time(self) -> datetime | None:
        """Get pipeline start time."""
        return self.start_time

    def get_end_time(self) -> datetime | None:
        """Get pipeline end time."""
        return self.end_time

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        with self._lock:
            return {
                "id": self.id,
                "stages": {
                    name: {
                        "name": stage.name,
                        "status": stage.status.value,
                        "start_time": stage.start_time.isoformat()
                        if stage.start_time
                        else None,
                        "end_time": stage.end_time.isoformat()
                        if stage.end_time
                        else None,
                        "result": stage.result,
                        "error": stage.error,
                        "checkpoint_id": stage.checkpoint_id,
                    }
                    for name, stage in self.stages.items()
                },
                "context": self.context,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "checkpoints": self.checkpoints,
            }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineState":
        """Create PipelineState from dictionary."""
        state = cls(id=data["id"])

        for name, stage_data in data.get("stages", {}).items():
            stage = StageState(
                name=stage_data["name"],
                status=StageStatus(stage_data["status"]),
                start_time=datetime.fromisoformat(stage_data["start_time"])
                if stage_data.get("start_time")
                else None,
                end_time=datetime.fromisoformat(stage_data["end_time"])
                if stage_data.get("end_time")
                else None,
                result=stage_data.get("result"),
                error=stage_data.get("error"),
                checkpoint_id=stage_data.get("checkpoint_id"),
            )
            state.stages[name] = stage

        state.context = data.get("context", {})
        state.start_time = (
            datetime.fromisoformat(data["start_time"])
            if data.get("start_time")
            else None
        )
        state.end_time = (
            datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None
        )
        state.checkpoints = data.get("checkpoints", {})
        return state


class StateManager(IStateManager):
    """Manages pipeline state with persistence and recovery."""

    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir
        self.states: dict[str, PipelineState] = {}
        self._lock = threading.Lock()

        if self.state_dir:
            self.state_dir.mkdir(parents=True, exist_ok=True)

    def create_state(self) -> IPipelineState:
        """Create a new pipeline state."""
        pipeline_id = str(uuid.uuid4())
        with self._lock:
            state = PipelineState(id=pipeline_id)
            self.states[pipeline_id] = state
            return state

    def save_state(self, state: IPipelineState, path: Path) -> None:
        """Save state to disk."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                if hasattr(state, "to_dict"):
                    json.dump(state.to_dict(), f, indent=2)
                else:
                    json.dump({"id": getattr(state, "id", "unknown")}, f, indent=2)
        except Exception as e:
            raise InfrastructureError(f"Failed to save state: {e}")

    def load_state(self, path: Path) -> IPipelineState:
        """Load state from disk."""
        if not path.exists():
            raise InfrastructureError(f"State file not found: {path}")

        try:
            with open(path) as f:
                data = json.load(f)
            state = PipelineState.from_dict(data)
            with self._lock:
                self.states[state.id] = state
            return state
        except Exception as e:
            raise InfrastructureError(f"Failed to load state: {e}")

    def create_checkpoint(self, state: IPipelineState, stage: str) -> str:
        """Create a checkpoint for rollback."""
        if not isinstance(state, PipelineState):
            raise TypeError("State must be a PipelineState instance")

        with self._lock:
            checkpoint_id = f"{stage}_{datetime.now().timestamp()}"
            checkpoint_data = {
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
                "data": state.to_dict(),
            }
            state.checkpoints[checkpoint_id] = checkpoint_data
            if stage in state.stages:
                state.stages[stage].checkpoint_id = checkpoint_id
            return checkpoint_id

    def rollback(self, state: IPipelineState, checkpoint_id: str) -> IPipelineState:
        """Rollback to a checkpoint."""
        if not isinstance(state, PipelineState):
            raise TypeError("State must be a PipelineState instance")

        with self._lock:
            checkpoint = state.checkpoints.get(checkpoint_id)
            if not checkpoint:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")

            checkpoint_data = checkpoint["data"]
            restored_state = PipelineState.from_dict(checkpoint_data)
            self.states[restored_state.id] = restored_state
            return restored_state


# =============================================================================
# STREAMS SECTION
# =============================================================================


class StreamReader:
    """Efficient streaming reader for large binary files."""

    def __init__(self, file_path: str | Path, chunk_size: int = 8192) -> None:
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self._file: BinaryIO | None = None
        self._mmap: mmap.mmap | None = None

    def __enter__(self):
        self._file = Path(self.file_path).open("rb")
        try:
            self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        except (OSError, ValueError):
            self._mmap = None
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._mmap:
            self._mmap.close()
        if self._file:
            self._file.close()

    def read_chunks(self, start: int = 0, size: int | None = None) -> Iterator[bytes]:
        """Read file in chunks from start position."""
        if self._mmap:
            pos = start
            end = min(start + size, len(self._mmap)) if size else len(self._mmap)
            while pos < end:
                chunk_size = min(self.chunk_size, end - pos)
                yield self._mmap[pos : pos + chunk_size]
                pos += chunk_size
        else:
            if not self._file:
                raise ValueError("File not opened")
            self._file.seek(start)
            remaining = size
            while True:
                chunk_size = (
                    min(self.chunk_size, remaining) if remaining else self.chunk_size
                )
                chunk = self._file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                if remaining:
                    remaining -= len(chunk)
                    if remaining <= 0:
                        break

    def read_at(self, offset: int, size: int) -> bytes:
        """Read specific bytes at offset."""
        if self._mmap:
            return self._mmap[offset : offset + size]
        if not self._file:
            raise ValueError("File not opened")
        self._file.seek(offset)
        return self._file.read(size)


class StreamWriter:
    """Streaming writer for efficient output generation."""

    def __init__(self, file_path: str | Path, buffer_size: int = 65536) -> None:
        self.file_path = Path(file_path)
        self.buffer_size = buffer_size
        self._file: BinaryIO | None = None
        self._buffer: bytearray = bytearray()

    def __enter__(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = Path(self.file_path).open("wb")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.flush()
        if self._file:
            self._file.close()

    def write(self, data: bytes) -> None:
        """Write data to buffer, flush when full."""
        self._buffer.extend(data)
        if len(self._buffer) >= self.buffer_size:
            self.flush()

    def write_struct(self, format_str: str, *values: Any) -> None:
        """Write structured data."""
        self.write(struct.pack(format_str, *values))

    def flush(self) -> None:
        """Flush buffer to disk."""
        if self._buffer and self._file:
            self._file.write(self._buffer)
            self._buffer.clear()
        elif self._buffer:
            raise ValueError("File not opened")


def stream_process_file(
    input_path: str | Path,
    output_path: str | Path,
    processor_func: Callable[[bytes], bytes | None],
    chunk_size: int = 8192,
) -> None:
    """Process file in streaming fashion."""
    with StreamReader(input_path, chunk_size) as reader:
        with StreamWriter(output_path) as writer:
            for chunk in reader.read_chunks():
                processed = processor_func(chunk)
                if processed:
                    writer.write(processed)


# =============================================================================
# ERROR HANDLING SECTION
# =============================================================================


@dataclass
class ErrorContext:
    """Context information for an error."""

    stage: str
    operation: str
    file_path: Path | None = None
    line_number: int | None = None
    column_number: int | None = None
    additional_info: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stage": self.stage,
            "operation": self.operation,
            "file_path": str(self.file_path) if self.file_path else None,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "additional_info": self.additional_info,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""

    error_type: str
    message: str
    severity: ErrorSeverity
    context: ErrorContext
    stack_trace: str | None = None
    recovery_attempted: bool = False
    recovery_strategy: RecoveryStrategy | None = None
    recovery_successful: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context.to_dict(),
            "stack_trace": self.stack_trace,
            "recovery_attempted": self.recovery_attempted,
            "recovery_strategy": self.recovery_strategy.value
            if self.recovery_strategy
            else None,
            "recovery_successful": self.recovery_successful,
        }


class ErrorCollector:
    """Collects errors during operations without immediately failing."""

    def __init__(
        self, max_errors: int = 100, fail_fast: bool = False, stage: str = "unknown"
    ) -> None:
        self.max_errors = max_errors
        self.fail_fast = fail_fast
        self.stage = stage
        self.errors: list[ErrorRecord] = []
        self._critical_error: Exception | None = None

    def add_error(
        self,
        error: Exception,
        context: ErrorContext | None = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> None:
        """Add an error to the collection."""
        if context is None:
            context = ErrorContext(stage=self.stage, operation="unknown")

        record = ErrorRecord(
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            context=context,
            stack_trace=traceback.format_exc()
            if severity != ErrorSeverity.INFO
            else None,
        )

        self.errors.append(record)

        if severity == ErrorSeverity.CRITICAL:
            self._critical_error = error

        if self.fail_fast or len(self.errors) >= self.max_errors:
            self.raise_if_errors()

    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return any(
            e.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
            for e in self.errors
        )

    def get_error_count(self) -> int:
        """Get count of actual errors (not warnings)."""
        return sum(
            1
            for e in self.errors
            if e.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]
        )

    def raise_if_errors(self) -> None:
        """Raise an exception if errors were collected."""
        if self._critical_error:
            raise self._critical_error

        error_count = self.get_error_count()
        if error_count > 0:
            msg = f"{self.stage}: {error_count} errors occurred"
            raise InfrastructureError(msg)


class ErrorManager:
    """Central error management for the pipeline."""

    def __init__(self) -> None:
        self.collectors: dict[str, ErrorCollector] = {}
        self.global_errors: list[ErrorRecord] = []

    def get_collector(self, stage: str, **kwargs) -> ErrorCollector:
        """Get or create error collector for a stage."""
        if stage not in self.collectors:
            self.collectors[stage] = ErrorCollector(stage=stage, **kwargs)
        return self.collectors[stage]

    @contextmanager
    def error_context(
        self, stage: str, operation: str, file_path: Path | None = None, **kwargs
    ):
        """Context manager for error handling."""
        context = ErrorContext(
            stage=stage,
            operation=operation,
            file_path=file_path,
            additional_info=kwargs,
        )

        try:
            yield context
        except Exception as e:
            collector = self.get_collector(stage)
            collector.add_error(e, context)
            raise


@contextmanager
def error_handler(
    stage: str,
    operation: str,
    file_path: Path | None = None,
    collector: ErrorCollector | None = None,
    **kwargs,
):
    """Context manager for standardized error handling."""
    context = ErrorContext(
        stage=stage, operation=operation, file_path=file_path, additional_info=kwargs
    )

    try:
        yield context
    except Exception as e:
        if collector:
            collector.add_error(e, context)
            if isinstance(e, (SystemExit, KeyboardInterrupt)):
                raise
        else:
            get_error_manager().get_collector(stage).add_error(e, context)
            raise


def with_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """Execute function with retry logic."""
    last_error = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(current_delay)
                current_delay *= backoff
            else:
                break

    if last_error:
        raise last_error
    raise RuntimeError("Retry logic error")


# =============================================================================
# GLOBAL INSTANCES AND FACTORIES
# =============================================================================

# Global infrastructure instances
_error_manager: ErrorManager | None = None
_circuit_breaker_manager: CircuitBreakerManager | None = None
_cache_manager: CacheManager | None = None
_event_bus: EventBus | None = None


def get_error_manager() -> ErrorManager:
    """Get global error manager instance."""
    global _error_manager
    if _error_manager is None:
        _error_manager = ErrorManager()
    return _error_manager


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager."""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager


def get_cache_manager(config: dict[str, Any] | None = None) -> CacheManager:
    """Get or create global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(config)
    return _cache_manager


def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def create_circuit_breaker(
    name: str, config: CircuitBreakerConfig | None = None
) -> CircuitBreaker:
    """Create or get a named circuit breaker."""
    return get_circuit_breaker_manager().get_or_create(name, config)


def create_event_bus() -> EventBus:
    """Factory function to create event bus."""
    return EventBus()


# =============================================================================
# UNIFIED INFRASTRUCTURE FACADE
# =============================================================================


class UnifiedInfrastructure:
    """Unified facade for all infrastructure components.

    This class provides a single entry point to access all infrastructure
    components including caching, circuit breakers, events, logging,
    recovery, security, state management, streams, and error handling.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize unified infrastructure with optional configuration."""
        self.config = config or {}

        # Initialize core components
        self.error_manager = get_error_manager()
        self.circuit_breaker_manager = get_circuit_breaker_manager()
        self.cache_manager = get_cache_manager(self.config.get("cache"))
        self.event_bus = get_event_bus()

        # Initialize state management
        state_dir = None
        if "state" in self.config and "directory" in self.config["state"]:
            state_dir = Path(self.config["state"]["directory"])
        self.state_manager = StateManager(state_dir)

        # Initialize resource monitoring
        resource_config = self.config.get("resources", {})
        limits = (
            ResourceLimits(**resource_config) if resource_config else ResourceLimits()
        )
        self.resource_monitor = ResourceMonitor(limits)

        # Initialize logging
        logging_config = self.config.get("logging", {})
        if logging_config:
            setup_logging(**logging_config)

        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Unified infrastructure initialized")

    # Caching interface
    def get_cache(self, stage: str) -> Any:
        """Get cache for a pipeline stage."""
        return self.cache_manager.get_cache(stage)

    # Circuit breaker interface
    def get_circuit_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        return self.circuit_breaker_manager.get_or_create(name, config)

    # Event interface
    def publish_event(self, event: Event) -> None:
        """Publish an event."""
        self.event_bus.publish(event)

    def subscribe_to_events(
        self, event_type: EventType, handler: IEventHandler
    ) -> None:
        """Subscribe to events of a specific type."""
        self.event_bus.subscribe(event_type, handler)

    # State management interface
    def create_pipeline_state(self) -> IPipelineState:
        """Create a new pipeline state."""
        return self.state_manager.create_state()

    def save_pipeline_state(self, state: IPipelineState, path: Path) -> None:
        """Save pipeline state to disk."""
        self.state_manager.save_state(state, path)

    def create_checkpoint(self, state: IPipelineState, stage: str) -> str:
        """Create a checkpoint for a pipeline state."""
        return self.state_manager.create_checkpoint(state, stage)

    # Error handling interface
    def get_error_collector(self, stage: str, **kwargs) -> ErrorCollector:
        """Get error collector for a stage."""
        return self.error_manager.get_collector(stage, **kwargs)

    def error_context(self, stage: str, operation: str, **kwargs):
        """Create error handling context."""
        return self.error_manager.error_context(stage, operation, **kwargs)

    # Resource monitoring interface
    def check_resource_limits(self) -> dict[str, Any]:
        """Check current resource usage."""
        try:
            self.resource_monitor.check_memory_usage()
            return self.resource_monitor.get_stats()
        except ResourceLimitError as e:
            self.logger.warning("Resource limit exceeded: %s", e)
            return {"error": str(e), "stats": self.resource_monitor.get_stats()}

    # Security interface
    def validate_path(self, path: str | Path, base_dir: str | Path) -> Path:
        """Validate a path for security."""
        return PathValidator.validate_path(path, base_dir)

    def safe_write(
        self, path: str | Path, content: str | bytes, base_dir: str | Path
    ) -> Path:
        """Safely write content to a file."""
        return safe_write_file(path, content, base_dir)

    # Streaming interface
    def create_stream_reader(
        self, path: str | Path, chunk_size: int = 8192
    ) -> StreamReader:
        """Create a stream reader for large files."""
        return StreamReader(path, chunk_size)

    def create_stream_writer(
        self, path: str | Path, buffer_size: int = 65536
    ) -> StreamWriter:
        """Create a stream writer for efficient output."""
        return StreamWriter(path, buffer_size)

    # Recovery interface
    def create_file_backup(self, file_path: Path) -> Path:
        """Create a backup of a file."""
        recovery = FileCorruptionRecovery()
        return recovery.create_backup(file_path)

    # Unified processing context
    @contextmanager
    def processing_context(
        self,
        stage: str,
        operation: str,
        file_path: Path | None = None,
        use_circuit_breaker: bool = True,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
        **kwargs,
    ):
        """Unified context for processing with all infrastructure components."""

        # Get circuit breaker if requested
        circuit_breaker = None
        if use_circuit_breaker:
            cb_name = f"{stage}_{operation}"
            circuit_breaker = self.get_circuit_breaker(cb_name, circuit_breaker_config)

        # Create error context
        error_collector = self.get_error_collector(stage)

        # Monitor resources
        start_stats = self.resource_monitor.get_stats()

        try:
            with self.error_context(
                stage, operation, file_path=file_path, **kwargs
            ) as error_ctx:
                if circuit_breaker:
                    # Execute with circuit breaker protection
                    def protected_operation():
                        yield error_ctx

                    yield from circuit_breaker.call(lambda: protected_operation())
                else:
                    yield error_ctx

        except Exception as e:
            # Log the error with full context
            self.logger.error(
                "Operation failed in %s:%s - %s",
                stage,
                operation,
                str(e),
                extra={
                    "stage": stage,
                    "operation": operation,
                    "file_path": str(file_path) if file_path else None,
                },
            )
            raise

        finally:
            # Log resource usage changes
            end_stats = self.resource_monitor.get_stats()
            memory_delta = end_stats["memory_usage"] - start_stats["memory_usage"]
            if memory_delta > 10 * 1024 * 1024:  # Log if > 10MB change
                self.logger.info(
                    "Operation %s:%s used %d MB memory",
                    stage,
                    operation,
                    memory_delta // (1024 * 1024),
                )

    # Cleanup and shutdown
    def shutdown(self) -> None:
        """Shutdown all infrastructure components."""
        self.logger.info("Shutting down unified infrastructure")

        # Log final statistics
        cache_stats = self.cache_manager.get_cache("extract")
        if cache_stats:
            self.logger.info(
                "Final cache stats: %s",
                cache_stats.stats() if hasattr(cache_stats, "stats") else "N/A",
            )

        circuit_stats = self.circuit_breaker_manager.get_stats()
        if circuit_stats:
            self.logger.info("Circuit breaker stats: %s", circuit_stats)

        event_stats = self.event_bus.get_statistics()
        self.logger.info("Event bus stats: %s", event_stats)

        resource_stats = self.resource_monitor.get_stats()
        self.logger.info("Final resource stats: %s", resource_stats)


# =============================================================================
# DIRECTORY UTILITIES - Output directory validation and preparation
# =============================================================================


def check_and_prepare_output_directory(
    output_dir: str | Path,
    allow_overwrite: bool = True,
    force_overwrite: bool = False,
    interactive: bool = False,
    stage_name: str = "operation",
) -> tuple[Path, bool]:
    """Check and prepare an output directory for pipeline operations.

    This function validates output directory paths, checks for existing content,
    handles overwrite scenarios, and ensures the directory is ready for use.

    Args:
        output_dir: Path to the output directory
        allow_overwrite: Whether to allow overwriting existing files
        force_overwrite: Whether to force overwrite without asking
        interactive: Whether to prompt user for confirmation
        stage_name: Name of the pipeline stage for logging

    Returns:
        Tuple of (Path object for directory, should_proceed boolean)

    Raises:
        SecurityError: If path validation fails
        PermissionError: If directory cannot be created or accessed
    """
    logger = get_logger("directory_utils")

    # Convert to Path object and resolve
    try:
        output_path = Path(output_dir).resolve()
    except Exception as e:
        raise SecurityError(f"Invalid output directory path: {e}") from e

    # Security validation - ensure path is safe
    try:
        # Basic security checks
        if (
            ".." in str(output_path)
            or str(output_path).startswith("/etc")
            or str(output_path).startswith("/sys")
        ):
            raise SecurityError(f"Unsafe output directory path: {output_path}")

        # Ensure path is within reasonable bounds (not trying to write to system directories)
        if str(output_path).startswith("/bin") or str(output_path).startswith(
            "/usr/bin"
        ):
            raise SecurityError(f"Cannot write to system directory: {output_path}")

    except SecurityError:
        raise
    except Exception as e:
        logger.warning("Path validation warning: %s", e)

    # Check if directory exists and has content
    directory_exists = output_path.exists()
    has_content = False

    if directory_exists and output_path.is_dir():
        try:
            # Check if directory has any files
            content = list(output_path.iterdir())
            has_content = len(content) > 0

            if has_content:
                logger.info(
                    "Output directory %s contains %d existing items",
                    output_path,
                    len(content),
                )
        except PermissionError:
            raise PermissionError(f"Cannot access output directory: {output_path}")
    elif directory_exists and not output_path.is_dir():
        raise FileExistsError(
            f"Output path exists but is not a directory: {output_path}"
        )

    # Handle overwrite scenarios
    should_proceed = True

    if has_content and not allow_overwrite:
        logger.error(
            "Output directory %s contains files but overwrite is disabled", output_path
        )
        return output_path, False

    if has_content and not force_overwrite:
        if interactive:
            # In interactive mode, we would normally prompt the user
            # For now, we'll just log a warning and proceed
            logger.warning(
                "Output directory %s contains existing files. "
                "Proceeding with %s as overwrite is enabled.",
                output_path,
                stage_name,
            )
        else:
            # Non-interactive mode with existing content - proceed with warning
            logger.warning(
                "Output directory %s contains existing files. "
                "Files may be overwritten during %s.",
                output_path,
                stage_name,
            )

    # Create directory if it doesn't exist
    if not directory_exists:
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info("Created output directory: %s", output_path)
        except PermissionError as e:
            raise PermissionError(
                f"Cannot create output directory {output_path}: {e}"
            ) from e
        except Exception as e:
            logger.error("Failed to create output directory %s: %s", output_path, e)
            raise

    # Verify directory is writable
    try:
        test_file = output_path / ".write_test"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        raise PermissionError(f"Output directory is not writable: {output_path}")
    except Exception as e:
        logger.warning("Could not verify directory writability: %s", e)

    logger.debug(
        "Output directory prepared: %s (exists=%s, has_content=%s, proceed=%s)",
        output_path,
        directory_exists,
        has_content,
        should_proceed,
    )

    return output_path, should_proceed


# =============================================================================
# PUBLIC API - Everything exported from this module
# =============================================================================

__all__ = [
    # Core unified interface
    "UnifiedInfrastructure",
    # Constants from constants.py
    # Core constants
    "HEADER_SIZE",
    "BUFFER_SIZE",
    "MAX_PATH_LENGTH",
    "MAX_NAME_LENGTH",
    "STRING_TABLE_OFFSET",
    "METADATA_OFFSET",
    "DEFAULT_TIMEOUT",
    "MAX_TIMEOUT",
    "PBD_HEADER_MARKER",
    "PBD_SIGNATURE_HDR",
    "ENTRY_MARKER",
    "DATA_MARKER",
    # File format constants
    "GRAMMAR_DIR",
    "POWERBUILDER_GRAMMAR",
    "COMMON_GRAMMAR",
    "DATAWINDOW_GRAMMAR",
    "SQL_GRAMMAR",
    "PSEUDOCODE_GRAMMAR",
    "POWERBUILDER_CORE_GRAMMAR",
    "POWERBUILDER_JS_GRAMMAR",
    "TRANSACTION_GRAMMAR",
    "FileType",
    "FILE_EXTENSIONS",
    # PowerBuilder language constants
    "PB_BASIC_TYPES",
    "PB_SYSTEM_TYPES",
    "PB_CONTROL_TYPES",
    "PB_EVENT_TYPES",
    "PB_KEYWORDS",
    "PB_OPERATORS",
    "SQL_KEYWORDS",
    "PB_TYPE_MAP",
    # Magic numbers - representative constants (full list is too long for __all__)
    # COUNT constants
    "COUNTS_11",
    "COUNTS_12",
    "COUNTS_13",
    "COUNTS_14",
    "COUNTS_15",
    "COUNTS_16",
    "COUNTS_17",
    "COUNTS_18",
    "COUNTS_19",
    "COUNTS_20",
    "COUNTS_30",
    "COUNTS_40",
    "COUNTS_50",
    "COUNTS_80",
    "COUNTS_99",
    # FACTOR constants
    "FACTORS_0_0001",
    "FACTORS_0_001",
    "FACTORS_0_01",
    "FACTORS_0_05",
    "FACTORS_0_1",
    "FACTORS_0_2",
    "FACTORS_0_3",
    "FACTORS_0_5",
    "FACTORS_0_8",
    "FACTORS_1_2",
    "FACTORS_1_5",
    "FACTORS_12_5",
    "FACTORS_20_0",
    # LIMIT constants
    "LIMITS_1025",
    "LIMITS_2048",
    "LIMITS_4096",
    "LIMITS_8192",
    "LIMITS_1280",
    "LIMITS_1364",
    "LIMITS_1536",
    "LIMITS_2880",
    # SIZE constants
    "SIZES_101",
    "SIZES_128",
    "SIZES_255",
    "SIZES_256",
    "SIZES_512",
    "SIZES_600",
    "SIZES_800",
    "SIZES_583",
    # MISC constants
    "MISC_10000",
    "MISC_16384",
    "MISC_32767",
    "MISC_32768",
    "MISC_65535",
    "MISC_65536",
    "MISC_100000",
    "MISC_999999",
    "MISC_16777216",
    "MISC_100000000",
    "MISC_268435456",
    "MISC_282444864",
    "MISC_4294967295",
    "MISC_1146047862",
    "MISC_1329744452",
    "MISC_16385",
    "MISC_42844",
    "MISC_282411680",
    # Exceptions
    "InfrastructureError",
    "SecurityError",
    "PathTraversalError",
    "ResourceLimitError",
    "CircuitBreakerError",
    "PipelineError",
    # Enums
    "ErrorSeverity",
    "RecoveryStrategy",
    "LogFormat",
    "CircuitState",
    "BackendType",
    "JobStatus",
    "StageStatus",
    # Interfaces (formerly contracts)
    "IPipelineState",
    "IStateManager",
    # Caching
    "CacheEntry",
    "LRUCache",
    "FileCache",
    "CacheConfig",
    "CacheManager",
    # Circuit Breakers
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerStats",
    "CircuitBreakerManager",
    # Coordination
    "CoordinatorMixin",
    "BaseCoordinator",
    # Distributed Processing
    "JobResult",
    "WorkerConfig",
    "TaskMetrics",
    "MultiprocessingBackend",
    "DistributedCoordinator",
    # Events
    "EventHandler",
    "EventBus",
    # Logging
    "StructuredFormatter",
    "ColoredFormatter",
    "PipelineLogger",
    "setup_logging",
    "get_logger",
    # Recovery
    "RetryConfig",
    "RecoveryContext",
    "retry_with_backoff",
    "FileCorruptionRecovery",
    # Resource Management
    "ResourceLimits",
    "ResourceMonitor",
    "with_timeout",
    # Security
    "PathValidator",
    "safe_join_path",
    "safe_write_file",
    "check_and_prepare_output_directory",
    # State Management
    "StageState",
    "PipelineState",
    "StateManager",
    # Streams
    "StreamReader",
    "StreamWriter",
    "stream_process_file",
    # Error Handling
    "ErrorContext",
    "ErrorRecord",
    "ErrorCollector",
    "ErrorManager",
    "error_handler",
    "with_retry",
    # Factory Functions
    "get_error_manager",
    "get_circuit_breaker_manager",
    "get_cache_manager",
    "get_event_bus",
    "create_circuit_breaker",
    "create_event_bus",
    # Logging constants
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]
