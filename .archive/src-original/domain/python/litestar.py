"""Python Litestar Framework Domain Types.

Litestar REST API framework types - Python's modern async web framework.
These are Python-specific manifestations of core API/Service concepts.
Pure data types following Scott Wlaschin's FDM principles.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from datetime import datetime


# ============================================================================
# LITESTAR APPLICATION
# ============================================================================


@dataclass(frozen=True)
class LitestarApp:
    """Litestar application.

    Maps to PowerBuilder application with web API exposure.
    """

    name: str
    controllers: List["Controller"]
    middleware: List["Middleware"]
    dependencies: Dict[str, "Dependency"]
    on_startup: List[Callable]
    on_shutdown: List[Callable]
    debug: bool = False


@dataclass(frozen=True)
class Controller:
    """API controller grouping related endpoints.

    Maps to PowerBuilder DataWindow/Window exposed as API.
    """

    path: str  # Base path like /api/users
    endpoints: List["Endpoint"]
    dependencies: Dict[str, "Dependency"]
    guards: List["Guard"]
    tags: List[str] = field(default_factory=list)  # OpenAPI tags


# ============================================================================
# ENDPOINTS (Manifestation of core Function concept)
# ============================================================================


@dataclass(frozen=True)
class Endpoint:
    """REST API endpoint.

    Maps to PowerBuilder function/event exposed as API.
    """

    path: str
    method: "HTTPMethod"
    handler: "Handler"
    status_code: int = 200
    response_model: Optional[Any] = None
    dependencies: Dict[str, "Dependency"] = field(default_factory=dict)
    guards: List["Guard"] = field(default_factory=list)
    cache: Optional["CacheConfig"] = None


class HTTPMethod(str, Enum):
    """HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass(frozen=True)
class Handler:
    """Endpoint handler function.

    The actual function that processes requests.
    """

    name: str
    parameters: List["Parameter"]
    return_type: Optional[str]
    is_async: bool = True
    docstring: Optional[str] = None


@dataclass(frozen=True)
class Parameter:
    """Handler parameter."""

    name: str
    param_type: "ParamType"
    python_type: str
    default: Optional[Any] = None
    required: bool = True
    validation: Optional["Validation"] = None


class ParamType(str, Enum):
    """Parameter types in Litestar."""

    PATH = "path"  # Path parameter
    QUERY = "query"  # Query string
    BODY = "body"  # Request body
    HEADER = "header"  # HTTP header
    COOKIE = "cookie"  # Cookie value
    DEPENDENCY = "dependency"  # Injected dependency
    REQUEST = "request"  # Raw request object
    STATE = "state"  # App state


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


@dataclass(frozen=True)
class Dependency:
    """Dependency injection configuration.

    Litestar's DI system for managing dependencies.
    """

    provider: Callable
    scope: "DIScope"
    cache: bool = False
    sync_to_thread: bool = False


class DIScope(str, Enum):
    """Dependency injection scopes."""

    APP = "app"  # Singleton per app
    REQUEST = "request"  # Per request
    SESSION = "session"  # Per session


@dataclass(frozen=True)
class Provide:
    """Dependency provider."""

    dependency: Callable
    use_cache: bool = True
    sync_to_thread: bool = False


# ============================================================================
# MIDDLEWARE
# ============================================================================


@dataclass(frozen=True)
class Middleware:
    """Middleware for request/response processing.

    Cross-cutting concerns like auth, logging, CORS.
    """

    middleware_type: "MiddlewareType"
    config: Dict[str, Any] = field(default_factory=dict)
    exclude_paths: List[str] = field(default_factory=list)


class MiddlewareType(str, Enum):
    """Types of middleware."""

    CORS = "cors"
    AUTHENTICATION = "auth"
    SESSION = "session"
    RATE_LIMIT = "rate_limit"
    COMPRESSION = "compression"
    LOGGING = "logging"
    EXCEPTION = "exception"
    CUSTOM = "custom"


@dataclass(frozen=True)
class CORSMiddleware(Middleware):
    """CORS configuration."""

    allow_origins: List[str] = field(default_factory=lambda: ["*"])
    allow_methods: List[str] = field(default_factory=lambda: ["*"])
    allow_headers: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    max_age: int = 600


# ============================================================================
# GUARDS (Authorization)
# ============================================================================


@dataclass(frozen=True)
class Guard:
    """Authorization guard.

    Maps to PowerBuilder security/role checks.
    """

    guard_type: "GuardType"
    handler: Callable
    exception_handler: Optional[Callable] = None


class GuardType(str, Enum):
    """Types of guards."""

    AUTHENTICATION = "auth"
    AUTHORIZATION = "authz"
    RATE_LIMIT = "rate"
    CUSTOM = "custom"


@dataclass(frozen=True)
class AuthenticationGuard(Guard):
    """Authentication requirement."""

    required_auth: bool = True
    auth_backend: str = "session"  # session, jwt, oauth


@dataclass(frozen=True)
class AuthorizationGuard(Guard):
    """Authorization requirement."""

    required_roles: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    check_ownership: bool = False


# ============================================================================
# REQUEST/RESPONSE
# ============================================================================


@dataclass(frozen=True)
class Request:
    """HTTP request."""

    method: HTTPMethod
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, Any]
    path_params: Dict[str, Any]
    body: Optional[Any] = None
    cookies: Dict[str, str] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Response:
    """HTTP response."""

    status_code: int
    content: Any
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: List["Cookie"] = field(default_factory=list)
    media_type: str = "application/json"


@dataclass(frozen=True)
class Cookie:
    """HTTP cookie."""

    key: str
    value: str
    max_age: Optional[int] = None
    expires: Optional[datetime] = None
    path: str = "/"
    domain: Optional[str] = None
    secure: bool = False
    httponly: bool = True
    samesite: str = "lax"


# ============================================================================
# VALIDATION
# ============================================================================


@dataclass(frozen=True)
class Validation:
    """Input validation rules.

    Maps to PowerBuilder field validation.
    """

    validators: List["Validator"]
    on_fail: str = "raise"  # raise, ignore, default


@dataclass(frozen=True)
class Validator:
    """Single validation rule."""

    validator_type: "ValidatorType"
    constraint: Any
    message: Optional[str] = None


class ValidatorType(str, Enum):
    """Types of validators."""

    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    PATTERN = "pattern"
    MIN_VALUE = "min"
    MAX_VALUE = "max"
    EMAIL = "email"
    URL = "url"
    UUID = "uuid"
    CUSTOM = "custom"


# ============================================================================
# CACHING
# ============================================================================


@dataclass(frozen=True)
class CacheConfig:
    """Cache configuration for endpoints."""

    key_builder: Callable
    expiration: int  # Seconds
    cache_backend: "CacheBackend"


class CacheBackend(str, Enum):
    """Cache backend types."""

    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"


# ============================================================================
# WEBSOCKETS
# ============================================================================


@dataclass(frozen=True)
class WebSocketEndpoint:
    """WebSocket endpoint.

    For real-time communication.
    """

    path: str
    on_connect: Callable
    on_receive: Callable
    on_disconnect: Callable
    heartbeat: Optional[int] = None


# ============================================================================
# BACKGROUND TASKS
# ============================================================================


@dataclass(frozen=True)
class BackgroundTask:
    """Background task configuration."""

    task: Callable
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    delay: Optional[int] = None  # Delay in seconds


# ============================================================================
# OPENAPI DOCUMENTATION
# ============================================================================


@dataclass(frozen=True)
class OpenAPIConfig:
    """OpenAPI/Swagger configuration."""

    title: str
    version: str
    description: Optional[str] = None
    servers: List["Server"] = field(default_factory=list)
    tags: List["Tag"] = field(default_factory=list)


@dataclass(frozen=True)
class Server:
    """API server definition."""

    url: str
    description: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Tag:
    """API tag for grouping."""

    name: str
    description: Optional[str] = None


# ============================================================================
# DOMAIN EVENTS (Colocated with Litestar aggregate)
# ============================================================================


@dataclass(frozen=True)
class ApplicationStarted:
    """Event: Litestar app started."""

    app: LitestarApp
    port: int
    timestamp: datetime


@dataclass(frozen=True)
class RequestReceived:
    """Event: HTTP request received."""

    request: Request
    endpoint: Endpoint
    timestamp: datetime


@dataclass(frozen=True)
class ResponseSent:
    """Event: HTTP response sent."""

    response: Response
    duration_ms: float
    timestamp: datetime


@dataclass(frozen=True)
class ValidationFailed:
    """Event: Request validation failed."""

    endpoint: Endpoint
    errors: List[str]
    timestamp: datetime


@dataclass(frozen=True)
class DependencyInjected:
    """Event: Dependency was injected."""

    dependency: Dependency
    scope: DIScope
    timestamp: datetime


@dataclass(frozen=True)
class WebSocketConnected:
    """Event: WebSocket client connected."""

    endpoint: WebSocketEndpoint
    client_id: str
    timestamp: datetime
