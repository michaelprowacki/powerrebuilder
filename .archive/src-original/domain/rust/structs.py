"""Rust Structs and Types Domain.

Rust-specific manifestations of core type concepts.
These represent Rust's type system including structs, enums, traits.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Generic, TypeVar
from enum import Enum
from datetime import datetime


T = TypeVar("T")


# ============================================================================
# RUST TYPE SYSTEM (Manifestation of core Type concepts)
# ============================================================================


@dataclass(frozen=True)
class RustType:
    """A Rust type.

    Manifestation of core Type concept with Rust specifics.
    """

    name: str
    rust_kind: "RustTypeKind"
    generics: List["Generic"] = field(default_factory=list)
    lifetimes: List["Lifetime"] = field(default_factory=list)
    is_copy: bool = False  # Implements Copy trait
    is_send: bool = True  # Can be sent between threads
    is_sync: bool = True  # Can be shared between threads


class RustTypeKind(str, Enum):
    """Kinds of Rust types."""

    PRIMITIVE = "primitive"  # i32, bool, etc.
    STRUCT = "struct"
    ENUM = "enum"
    TRAIT = "trait"
    UNION = "union"
    TUPLE = "tuple"
    ARRAY = "array"
    SLICE = "slice"
    REFERENCE = "reference"
    POINTER = "pointer"
    FUNCTION = "function"
    CLOSURE = "closure"
    NEVER = "never"  # ! type


# ============================================================================
# PRIMITIVE TYPES
# ============================================================================


@dataclass(frozen=True)
class RustPrimitive:
    """Rust primitive type.

    Maps to PowerBuilder basic types.
    """

    primitive_type: "PrimitiveKind"
    size_bytes: int


class PrimitiveKind(str, Enum):
    """Rust primitive types."""

    # Integers
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    I128 = "i128"
    ISIZE = "isize"
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    U64 = "u64"
    U128 = "u128"
    USIZE = "usize"
    # Floats
    F32 = "f32"
    F64 = "f64"
    # Others
    BOOL = "bool"
    CHAR = "char"
    STR = "str"  # String slice
    UNIT = "()"  # Unit type


# ============================================================================
# STRUCTS (Manifestation of core ProductType)
# ============================================================================


@dataclass(frozen=True)
class Struct:
    """Rust struct - product type.

    Maps to PowerBuilder structures and user objects.
    """

    name: str
    fields: List["StructField"]
    generics: List["Generic"] = field(default_factory=list)
    lifetimes: List["Lifetime"] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)  # #[derive(...)]
    visibility: "Visibility" = "Visibility.PRIVATE"
    is_tuple_struct: bool = False
    is_unit_struct: bool = False


@dataclass(frozen=True)
class StructField:
    """Field in a struct."""

    name: Optional[str]  # None for tuple structs
    field_type: RustType
    visibility: "Visibility" = "Visibility.PRIVATE"
    attributes: List[str] = field(default_factory=list)  # #[serde(rename = "...")]


class Visibility(str, Enum):
    """Rust visibility modifiers."""

    PRIVATE = ""  # private (default)
    PUB = "pub"  # public
    PUB_CRATE = "pub(crate)"  # public within crate
    PUB_SUPER = "pub(super)"  # public to parent module
    PUB_IN = "pub(in path)"  # public in specific path


# ============================================================================
# ENUMS (Manifestation of core SumType)
# ============================================================================


@dataclass(frozen=True)
class RustEnum:
    """Rust enum - sum type.

    Maps to PowerBuilder enumerated types and variant records.
    """

    name: str
    variants: List["EnumVariant"]
    generics: List["Generic"] = field(default_factory=list)
    lifetimes: List["Lifetime"] = field(default_factory=list)
    derives: List[str] = field(default_factory=list)
    visibility: Visibility = Visibility.PRIVATE


@dataclass(frozen=True)
class EnumVariant:
    """Variant in an enum."""

    name: str
    variant_type: "VariantType"
    discriminant: Optional[int] = None  # Explicit discriminant


@dataclass(frozen=True)
class VariantType:
    """Type of enum variant."""

    kind: "VariantKind"
    data: Optional[Any] = None


class VariantKind(str, Enum):
    """Kinds of enum variants."""

    UNIT = "unit"  # No data
    TUPLE = "tuple"  # Unnamed fields
    STRUCT = "struct"  # Named fields


# ============================================================================
# TRAITS (Manifestation of core Interface)
# ============================================================================


@dataclass(frozen=True)
class Trait:
    """Rust trait - interface/contract.

    Maps to PowerBuilder interfaces and abstract methods.
    """

    name: str
    methods: List["TraitMethod"]
    associated_types: List["AssociatedType"] = field(default_factory=list)
    supertraits: List[str] = field(default_factory=list)
    generics: List["Generic"] = field(default_factory=list)
    is_unsafe: bool = False
    is_auto: bool = False  # Auto trait like Send, Sync
    visibility: Visibility = Visibility.PUB


@dataclass(frozen=True)
class TraitMethod:
    """Method in a trait."""

    name: str
    signature: "FunctionSignature"
    has_default: bool = False
    is_async: bool = False
    is_unsafe: bool = False


@dataclass(frozen=True)
class AssociatedType:
    """Associated type in a trait."""

    name: str
    bounds: List[str] = field(default_factory=list)
    default: Optional[RustType] = None


# ============================================================================
# IMPLEMENTATIONS
# ============================================================================


@dataclass(frozen=True)
class Impl:
    """Implementation block.

    Implements methods or traits for types.
    """

    impl_type: "ImplType"
    target_type: RustType
    trait_name: Optional[str] = None  # None for inherent impl
    methods: List["Method"] = field(default_factory=list)
    generics: List["Generic"] = field(default_factory=list)
    where_clause: Optional["WhereClause"] = None


class ImplType(str, Enum):
    """Types of impl blocks."""

    INHERENT = "inherent"  # impl Type
    TRAIT = "trait"  # impl Trait for Type
    BLANKET = "blanket"  # impl<T> Trait for T where ...


@dataclass(frozen=True)
class Method:
    """Method implementation."""

    name: str
    signature: "FunctionSignature"
    body: str  # Method body
    visibility: Visibility = Visibility.PRIVATE
    is_async: bool = False
    is_unsafe: bool = False
    is_const: bool = False


# ============================================================================
# FUNCTIONS AND CLOSURES
# ============================================================================


@dataclass(frozen=True)
class Function:
    """Rust function.

    Maps to PowerBuilder functions and event handlers.
    """

    name: str
    signature: "FunctionSignature"
    body: str
    visibility: Visibility = Visibility.PRIVATE
    is_async: bool = False
    is_unsafe: bool = False
    is_const: bool = False
    is_extern: bool = False


@dataclass(frozen=True)
class FunctionSignature:
    """Function signature."""

    parameters: List["Parameter"]
    return_type: Optional[RustType] = None
    generics: List["Generic"] = field(default_factory=list)
    lifetimes: List["Lifetime"] = field(default_factory=list)
    where_clause: Optional["WhereClause"] = None


@dataclass(frozen=True)
class Parameter:
    """Function parameter."""

    name: str
    param_type: RustType
    is_mut: bool = False
    is_ref: bool = False
    pattern: Optional["Pattern"] = None


@dataclass(frozen=True)
class Closure:
    """Rust closure.

    Maps to PowerBuilder anonymous functions/callbacks.
    """

    capture_mode: "CaptureMode"
    parameters: List[Parameter]
    return_type: Optional[RustType]
    body: str
    is_async: bool = False
    is_move: bool = False


class CaptureMode(str, Enum):
    """How closure captures variables."""

    BORROW = "borrow"  # &T
    BORROW_MUT = "borrow_mut"  # &mut T
    MOVE = "move"  # T


# ============================================================================
# GENERICS AND LIFETIMES
# ============================================================================


@dataclass(frozen=True)
class Generic:
    """Generic type parameter."""

    name: str
    bounds: List["TraitBound"] = field(default_factory=list)
    default: Optional[RustType] = None


@dataclass(frozen=True)
class Lifetime:
    """Lifetime parameter.

    Rust's unique lifetime system for memory safety.
    """

    name: str  # 'a, 'static, etc.
    bounds: List[str] = field(default_factory=list)  # 'a: 'b
    is_static: bool = False


@dataclass(frozen=True)
class TraitBound:
    """Bound on a generic type."""

    trait_name: str
    is_positive: bool = True  # T: Trait vs T: !Trait
    lifetime: Optional[Lifetime] = None


@dataclass(frozen=True)
class WhereClause:
    """Where clause for complex bounds."""

    predicates: List["WherePredicate"]


@dataclass(frozen=True)
class WherePredicate:
    """Single predicate in where clause."""

    bounded_type: str
    bounds: List[TraitBound]


# ============================================================================
# PATTERN MATCHING
# ============================================================================


@dataclass(frozen=True)
class Pattern:
    """Pattern for matching.

    Rust's powerful pattern matching system.
    """

    pattern_type: "PatternType"
    bindings: List[str] = field(default_factory=list)
    guards: Optional[str] = None  # if condition


class PatternType(str, Enum):
    """Types of patterns."""

    WILDCARD = "_"  # Matches anything
    LITERAL = "literal"  # Literal value
    VARIABLE = "variable"  # Bind to variable
    STRUCT = "struct"  # Struct destructuring
    TUPLE = "tuple"  # Tuple destructuring
    SLICE = "slice"  # Slice pattern
    REFERENCE = "reference"  # &pattern
    RANGE = "range"  # 1..=10
    OR = "or"  # pattern | pattern


@dataclass(frozen=True)
class Match:
    """Match expression.

    Maps to PowerBuilder CHOOSE CASE.
    """

    scrutinee: str  # Expression being matched
    arms: List["MatchArm"]
    is_exhaustive: bool = True


@dataclass(frozen=True)
class MatchArm:
    """Arm in a match expression."""

    pattern: Pattern
    guard: Optional[str] = None  # if condition
    body: str


# ============================================================================
# MODULES AND CRATES
# ============================================================================


@dataclass(frozen=True)
class Module:
    """Rust module.

    Maps to PowerBuilder libraries/packages.
    """

    name: str
    path: Optional[str] = None  # File path
    items: List[Any] = field(default_factory=list)  # Module items
    visibility: Visibility = Visibility.PRIVATE
    is_inline: bool = False  # mod { } vs mod name;


@dataclass(frozen=True)
class Crate:
    """Rust crate - compilation unit."""

    name: str
    crate_type: "CrateType"
    root_module: Module
    dependencies: List["Dependency"] = field(default_factory=list)
    edition: str = "2021"


class CrateType(str, Enum):
    """Types of crates."""

    BIN = "bin"  # Binary executable
    LIB = "lib"  # Library
    DYLIB = "dylib"  # Dynamic library
    CDYLIB = "cdylib"  # C-compatible dynamic library
    STATICLIB = "staticlib"  # Static library
    PROC_MACRO = "proc-macro"  # Procedural macro


@dataclass(frozen=True)
class Dependency:
    """Crate dependency."""

    name: str
    version: str
    features: List[str] = field(default_factory=list)
    optional: bool = False
    source: str = "crates.io"


# ============================================================================
# ATTRIBUTES AND MACROS
# ============================================================================


@dataclass(frozen=True)
class Attribute:
    """Rust attribute #[...] or #![...]."""

    name: str
    arguments: List[str] = field(default_factory=list)
    is_inner: bool = False  # #![...] vs #[...]


@dataclass(frozen=True)
class MacroCall:
    """Macro invocation."""

    macro_name: str
    arguments: str  # Raw token stream
    is_procedural: bool = False


# ============================================================================
# DOMAIN EVENTS (Colocated with Rust aggregate)
# ============================================================================


@dataclass(frozen=True)
class TypeDefined:
    """Event: Rust type was defined."""

    rust_type: RustType
    module: str
    timestamp: datetime


@dataclass(frozen=True)
class TraitImplemented:
    """Event: Trait was implemented for type."""

    impl: Impl
    timestamp: datetime


@dataclass(frozen=True)
class PatternMatched:
    """Event: Pattern matching occurred."""

    match_expr: Match
    matched_arm: MatchArm
    timestamp: datetime


@dataclass(frozen=True)
class CrateCompiled:
    """Event: Crate was compiled."""

    crate: Crate
    success: bool
    warnings: List[str]
    timestamp: datetime
