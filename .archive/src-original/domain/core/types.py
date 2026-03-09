"""Core Type System Semantic Invariants.

Universal type concepts that exist across all programming languages.
These represent classification and safety mechanisms.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# FUNDAMENTAL TYPE CONCEPTS
# ============================================================================


@dataclass(frozen=True)
class Type:
    """The universal concept of a type - a classification of values.

    Types provide a way to categorize data and define valid operations.
    """

    name: str
    kind: "TypeKind"
    operations: List[str] = field(default_factory=list)  # Valid operations
    constraints: List["TypeConstraint"] = field(default_factory=list)


@dataclass(frozen=True)
class Value:
    """A concrete piece of data with a specific type.

    The actual data that programs manipulate.
    """

    data: Any
    value_type: Type
    is_immutable: bool = True


class TypeKind(str, Enum):
    """Fundamental categories of types."""

    PRIMITIVE = "primitive"  # Built-in atomic types
    COMPOSITE = "composite"  # Composed of other types
    ABSTRACT = "abstract"  # Cannot be instantiated
    GENERIC = "generic"  # Parameterized type
    FUNCTION = "function"  # Function type
    REFERENCE = "reference"  # Pointer/reference type


# ============================================================================
# PRIMITIVE TYPES
# ============================================================================


@dataclass(frozen=True)
class PrimitiveType(Type):
    """Basic built-in types that exist in most languages.

    Numbers, strings, booleans, etc.
    """

    size_bytes: Optional[int] = None
    is_signed: bool = True  # For numeric types
    precision: Optional[int] = None  # For floating point


@dataclass(frozen=True)
class NumericType(PrimitiveType):
    """Numeric types - integers, floats, decimals."""

    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    is_exact: bool = True  # False for floating point


@dataclass(frozen=True)
class BooleanType(PrimitiveType):
    """Boolean/logical type."""

    true_value: Any = True
    false_value: Any = False


@dataclass(frozen=True)
class StringType(PrimitiveType):
    """Text/character sequence type."""

    encoding: str = "utf-8"
    max_length: Optional[int] = None


# ============================================================================
# COMPOSITE TYPES
# ============================================================================


@dataclass(frozen=True)
class CompositeType(Type):
    """Types composed of other types."""

    components: List[Type]


@dataclass(frozen=True)
class ProductType(CompositeType):
    """Product type - combines multiple types (tuple, struct, record).

    Has all components simultaneously.
    """

    fields: List["Field"]
    is_ordered: bool = True  # True for tuple, False for record


@dataclass(frozen=True)
class SumType(CompositeType):
    """Sum type - choice between types (union, variant, enum).

    Has exactly one of the variants.
    """

    variants: List["Variant"]
    is_discriminated: bool = True  # Has explicit tag


@dataclass(frozen=True)
class Field:
    """A field in a product type."""

    name: str
    field_type: Type
    is_optional: bool = False
    default_value: Optional[Value] = None


@dataclass(frozen=True)
class Variant:
    """A variant in a sum type."""

    name: str
    variant_type: Optional[Type] = None  # None for unit variants
    discriminator: Any = None  # Tag value


# ============================================================================
# COLLECTION TYPES
# ============================================================================


@dataclass(frozen=True)
class CollectionType(CompositeType):
    """Types that contain multiple values."""

    element_type: Type
    is_homogeneous: bool = True  # All elements same type


@dataclass(frozen=True)
class ArrayType(CollectionType):
    """Fixed-size sequence of elements."""

    size: int
    is_mutable: bool = True


@dataclass(frozen=True)
class ListType(CollectionType):
    """Variable-size sequence of elements."""

    is_mutable: bool = True
    max_size: Optional[int] = None


@dataclass(frozen=True)
class SetType(CollectionType):
    """Unordered collection of unique elements."""

    is_mutable: bool = True


@dataclass(frozen=True)
class MapType(CollectionType):
    """Key-value mapping."""

    key_type: Type
    value_type: Type
    is_mutable: bool = True


# ============================================================================
# GENERIC/PARAMETRIC TYPES
# ============================================================================


@dataclass(frozen=True)
class GenericType(Type):
    """Parameterized type - type with type parameters.

    Enables parametric polymorphism.
    """

    type_parameters: List["TypeParameter"]
    constraints: List["TypeConstraint"] = field(default_factory=list)


@dataclass(frozen=True)
class TypeParameter:
    """A type variable in a generic type."""

    name: str
    bounds: List[Type] = field(default_factory=list)  # Upper bounds
    variance: str = "invariant"  # invariant, covariant, contravariant


@dataclass(frozen=True)
class TypeApplication:
    """Application of type arguments to generic type."""

    generic_type: GenericType
    type_arguments: List[Type]


# ============================================================================
# FUNCTION TYPES
# ============================================================================


@dataclass(frozen=True)
class FunctionType(Type):
    """Type of a function."""

    parameter_types: List[Type]
    return_type: Type
    is_pure: bool = True
    effects: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MethodType(FunctionType):
    """Type of a method (function with receiver)."""

    receiver_type: Type
    is_static: bool = False


# ============================================================================
# TYPE RELATIONSHIPS
# ============================================================================


@dataclass(frozen=True)
class Subtype:
    """Subtyping relationship - Liskov substitution."""

    subtype: Type
    supertype: Type
    is_nominal: bool = False  # True for nominal, False for structural


@dataclass(frozen=True)
class TypeEquality:
    """Type equality relationship."""

    type1: Type
    type2: Type
    is_structural: bool = True  # Structural vs nominal equality


@dataclass(frozen=True)
class TypeConstraint:
    """Constraint on a type."""

    constraint_type: str  # "implements", "extends", "bounded", etc.
    required_type: Type


# ============================================================================
# TYPE SAFETY
# ============================================================================


@dataclass(frozen=True)
class TypeSafety:
    """Type safety guarantees."""

    is_strongly_typed: bool  # Types enforced
    is_statically_typed: bool  # Types checked at compile time
    is_type_safe: bool  # Well-typed programs don't go wrong
    allows_casting: bool  # Explicit type conversion
    allows_coercion: bool  # Implicit type conversion


@dataclass(frozen=True)
class TypeCheck:
    """Type checking operation."""

    expression: Any  # Would be Expression from computation.py
    expected_type: Type
    actual_type: Type
    is_valid: bool
    coercions_needed: List["TypeCoercion"] = field(default_factory=list)


@dataclass(frozen=True)
class TypeCoercion:
    """Implicit type conversion."""

    from_type: Type
    to_type: Type
    is_safe: bool  # No data loss


@dataclass(frozen=True)
class TypeCast:
    """Explicit type conversion."""

    from_type: Type
    to_type: Type
    is_checked: bool  # Runtime check performed


# ============================================================================
# NULL/OPTION TYPES
# ============================================================================


@dataclass(frozen=True)
class OptionType(SumType):
    """Optional/nullable type - may or may not have a value.

    Universal concept of potential absence.
    """

    wrapped_type: Type
    none_value: Any = None


@dataclass(frozen=True)
class ResultType(SumType):
    """Result type - either success or error.

    Universal concept of fallible computation.
    """

    success_type: Type
    error_type: Type


# ============================================================================
# REFINEMENT TYPES
# ============================================================================


@dataclass(frozen=True)
class RefinementType(Type):
    """Type with additional predicates/constraints.

    A subset of values from base type.
    """

    base_type: Type
    predicate: str  # Constraint expression
    examples: List[Value] = field(default_factory=list)


@dataclass(frozen=True)
class DependentType(Type):
    """Type that depends on a value.

    Advanced type system feature.
    """

    base_type: Type
    dependency: Value


# ============================================================================
# DOMAIN EVENTS (Colocated with Type aggregate)
# ============================================================================


@dataclass(frozen=True)
class TypeDefined:
    """Event: New type was defined."""

    type_def: Type
    module: str
    timestamp: datetime


@dataclass(frozen=True)
class TypeChecked:
    """Event: Type checking performed."""

    check: TypeCheck
    location: str
    timestamp: datetime


@dataclass(frozen=True)
class TypeMismatch:
    """Event: Type error detected."""

    expected: Type
    actual: Type
    expression: str
    timestamp: datetime


@dataclass(frozen=True)
class TypeCoerced:
    """Event: Implicit type conversion occurred."""

    coercion: TypeCoercion
    value: Any
    timestamp: datetime


@dataclass(frozen=True)
class TypeCasted:
    """Event: Explicit type conversion performed."""

    cast: TypeCast
    value: Any
    success: bool
    timestamp: datetime
