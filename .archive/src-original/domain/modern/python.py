"""Python/Litestar Domain Types.

Pure data types representing Python/Litestar constructs.
These are the WHAT - no operations, just data models.
Following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================================================
# PYTHON LANGUAGE TYPES
# ============================================================================


class PythonType(str, Enum):
    """Python type hints."""

    INT = "int"
    FLOAT = "float"
    STR = "str"
    BOOL = "bool"
    BYTES = "bytes"
    LIST = "list"
    DICT = "dict"
    SET = "set"
    TUPLE = "tuple"
    NONE = "None"
    ANY = "Any"
    OPTIONAL = "Optional"
    UNION = "Union"
    CALLABLE = "Callable"
    TYPING_GENERIC = "Generic"


@dataclass(frozen=True)
class PythonVariable:
    """A Python variable."""

    name: str
    type_hint: Optional[str] = None
    default_value: Optional[Any] = None
    is_class_var: bool = False
    is_instance_var: bool = False


@dataclass(frozen=True)
class PythonParameter:
    """A function parameter."""

    name: str
    type_hint: Optional[str] = None
    default: Optional[Any] = None
    is_args: bool = False  # *args
    is_kwargs: bool = False  # **kwargs
    is_positional_only: bool = False
    is_keyword_only: bool = False


@dataclass(frozen=True)
class PythonFunction:
    """A Python function."""

    name: str
    parameters: List[PythonParameter] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    body: str = ""
    is_async: bool = False
    is_generator: bool = False


@dataclass(frozen=True)
class PythonClass:
    """A Python class."""

    name: str
    bases: List[str] = field(default_factory=list)
    metaclass: Optional[str] = None
    class_variables: List[PythonVariable] = field(default_factory=list)
    instance_variables: List[PythonVariable] = field(default_factory=list)
    methods: List[PythonFunction] = field(default_factory=list)
    properties: List["PythonProperty"] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PythonProperty:
    """A Python property."""

    name: str
    getter: Optional[PythonFunction] = None
    setter: Optional[PythonFunction] = None
    deleter: Optional[PythonFunction] = None
    docstring: Optional[str] = None


@dataclass(frozen=True)
class PythonModule:
    """A Python module."""

    name: str
    imports: List["ImportStatement"] = field(default_factory=list)
    classes: List[PythonClass] = field(default_factory=list)
    functions: List[PythonFunction] = field(default_factory=list)
    variables: List[PythonVariable] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass(frozen=True)
class ImportStatement:
    """An import statement."""

    module: str
    names: List[str] = field(default_factory=list)  # Empty for 'import module'
    alias: Optional[str] = None
    is_from: bool = False  # True for 'from module import'


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


@dataclass(frozen=True)
class PydanticModel:
    """A Pydantic model."""

    name: str
    fields: List["PydanticField"] = field(default_factory=list)
    validators: List["PydanticValidator"] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    base_model: str = "BaseModel"


@dataclass(frozen=True)
class PydanticField:
    """A Pydantic field."""

    name: str
    type: str
    default: Optional[Any] = None
    default_factory: Optional[str] = None
    alias: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    gt: Optional[float] = None  # Greater than
    ge: Optional[float] = None  # Greater than or equal
    lt: Optional[float] = None  # Less than
    le: Optional[float] = None  # Less than or equal
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex: Optional[str] = None


@dataclass(frozen=True)
class PydanticValidator:
    """A Pydantic validator."""

    name: str
    fields: List[str]
    is_root: bool = False
    pre: bool = True
    always: bool = False
    function_body: str = ""


# ============================================================================
# SQLMODEL/SQLALCHEMY TYPES
# ============================================================================


@dataclass(frozen=True)
class SQLModel:
    """A SQLModel/SQLAlchemy model."""

    name: str
    table_name: str
    fields: List["SQLField"] = field(default_factory=list)
    relationships: List["SQLRelationship"] = field(default_factory=list)
    indexes: List["SQLIndex"] = field(default_factory=list)
    constraints: List["SQLConstraint"] = field(default_factory=list)


@dataclass(frozen=True)
class SQLField:
    """A database field."""

    name: str
    type: str  # Integer, String, DateTime, etc.
    primary_key: bool = False
    foreign_key: Optional[str] = None
    nullable: bool = True
    unique: bool = False
    index: bool = False
    default: Optional[Any] = None
    server_default: Optional[str] = None


@dataclass(frozen=True)
class SQLRelationship:
    """A database relationship."""

    name: str
    target_model: str
    relationship_type: str  # one-to-one, one-to-many, many-to-many
    back_populates: Optional[str] = None
    foreign_keys: List[str] = field(default_factory=list)
    cascade: Optional[str] = None


@dataclass(frozen=True)
class SQLIndex:
    """A database index."""

    name: str
    fields: List[str]
    unique: bool = False


@dataclass(frozen=True)
class SQLConstraint:
    """A database constraint."""

    name: str
    type: str  # check, unique, foreign_key
    expression: str


# ============================================================================
# LITESTAR FRAMEWORK TYPES
# ============================================================================


@dataclass(frozen=True)
class LitestarRoute:
    """A Litestar route."""

    path: str
    method: str  # GET, POST, PUT, DELETE, etc.
    handler: str  # Function name
    name: Optional[str] = None
    guards: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    response_model: Optional[str] = None
    status_code: int = 200


@dataclass(frozen=True)
class LitestarController:
    """A Litestar controller."""

    name: str
    path: str
    routes: List[LitestarRoute] = field(default_factory=list)
    guards: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class LitestarApp:
    """A Litestar application."""

    name: str
    controllers: List[LitestarController] = field(default_factory=list)
    middleware: List["LitestarMiddleware"] = field(default_factory=list)
    exception_handlers: Dict[str, str] = field(default_factory=dict)
    on_startup: List[str] = field(default_factory=list)
    on_shutdown: List[str] = field(default_factory=list)
    cors_config: Optional["CORSConfig"] = None


@dataclass(frozen=True)
class LitestarMiddleware:
    """Middleware configuration."""

    name: str
    type: str
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CORSConfig:
    """CORS configuration."""

    allow_origins: List[str] = field(default_factory=list)
    allow_methods: List[str] = field(default_factory=list)
    allow_headers: List[str] = field(default_factory=list)
    allow_credentials: bool = False
    expose_headers: List[str] = field(default_factory=list)
    max_age: int = 600


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


@dataclass(frozen=True)
class Dependency:
    """A dependency injection definition."""

    name: str
    type: str
    scope: str = "singleton"  # singleton, request, transient
    factory: Optional[str] = None
    provides: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ServiceProvider:
    """Service provider configuration."""

    services: List[Dependency] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)


# ============================================================================
# TESTING
# ============================================================================


@dataclass(frozen=True)
class TestCase:
    """A test case."""

    name: str
    test_class: Optional[str] = None
    fixtures: List[str] = field(default_factory=list)
    marks: List[str] = field(default_factory=list)  # pytest marks
    parameters: List[Dict[str, Any]] = field(default_factory=list)  # parametrize


@dataclass(frozen=True)
class TestFixture:
    """A test fixture."""

    name: str
    scope: str = "function"  # function, class, module, session
    autouse: bool = False
    params: List[Any] = field(default_factory=list)


# ============================================================================
# PROJECT STRUCTURE
# ============================================================================


@dataclass(frozen=True)
class PythonPackage:
    """A Python package."""

    name: str
    modules: List[PythonModule] = field(default_factory=list)
    subpackages: List["PythonPackage"] = field(default_factory=list)
    init_file: Optional[PythonModule] = None


@dataclass(frozen=True)
class ProjectStructure:
    """Python project structure."""

    name: str
    root_package: PythonPackage
    tests: List[TestCase] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    pyproject_toml: Dict[str, Any] = field(default_factory=dict)
