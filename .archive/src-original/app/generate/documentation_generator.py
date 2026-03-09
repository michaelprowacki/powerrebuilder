"""Generate Documentation - Self-Contained FDM Module.

Following Scott Wlaschin's functional domain modeling principles:
- Types are co-located with the functions that use them (no separate type files)
- All data structures are immutable using frozen dataclasses
- Functions are pure and return Result types for error handling
- No external dependencies except the core Result type
- Uses domain language from documentation/API problem space

This module is completely self-contained - both types and operations
for documentation generation live together in this single file.
"""

from typing import NewType, List, Dict, Optional, Any, FrozenSet, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

from src_new._core.result import Result, Success, Failure


# ============================================================================
# DOMAIN TYPES (Co-located with operations that use them)
# ============================================================================

# Value types using domain language
APIEndpoint = NewType("APIEndpoint", str)
MarkdownDocument = NewType("MarkdownDocument", str)
DiagramDefinition = NewType("DiagramDefinition", str)
DocString = NewType("DocString", str)
CodeExample = NewType("CodeExample", str)


class DocumentationType(str, Enum):
    """Types of documentation to generate."""

    API = "api"
    ARCHITECTURE = "architecture"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    MIGRATION_GUIDE = "migration_guide"
    README = "readme"
    CHANGELOG = "changelog"
    REFERENCE = "reference"


class DiagramType(str, Enum):
    """Types of architecture diagrams."""

    SEQUENCE = "sequence"
    CLASS = "class"
    COMPONENT = "component"
    DEPLOYMENT = "deployment"
    FLOWCHART = "flowchart"
    ERD = "entity_relationship"
    STATE = "state_machine"
    DATA_FLOW = "data_flow"


class APIMethod(str, Enum):
    """HTTP methods for API documentation."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


# ============================================================================
# IMMUTABLE DOMAIN ENTITIES
# ============================================================================


@dataclass(frozen=True)
class APIParameter:
    """API parameter definition - immutable."""

    name: str
    param_type: str  # path, query, header, body
    data_type: str  # string, integer, boolean, etc.

    # Properties
    required: bool
    default_value: Optional[Any]
    description: str

    # Validation
    min_value: Optional[Any]
    max_value: Optional[Any]
    pattern: Optional[str]  # Regex pattern
    enum_values: Optional[FrozenSet[Any]]

    def __post_init__(self):
        """Validate parameter definition."""
        valid_types = {"path", "query", "header", "body"}
        if self.param_type not in valid_types:
            raise ValueError(f"Invalid param type: {self.param_type}")

        # Path parameters must be required
        if self.param_type == "path" and not self.required:
            raise ValueError("Path parameters must be required")


@dataclass(frozen=True)
class APIResponse:
    """API response definition - immutable."""

    status_code: int
    description: str

    # Response schema
    content_type: str
    schema: Dict[str, Any]  # Would be frozendict in production

    # Examples
    examples: Tuple[CodeExample, ...]

    def __post_init__(self):
        """Validate response definition."""
        # Valid HTTP status codes
        if not 100 <= self.status_code <= 599:
            raise ValueError(f"Invalid status code: {self.status_code}")

        # Success responses should have schema
        if 200 <= self.status_code < 300 and not self.schema:
            raise ValueError("Success responses should have a schema")


@dataclass(frozen=True)
class APIDocumentation:
    """API endpoint documentation - immutable."""

    endpoint: APIEndpoint
    method: APIMethod

    # Description
    summary: str
    description: str
    tags: FrozenSet[str]

    # Request/Response
    parameters: Tuple[APIParameter, ...]
    request_body: Optional[Dict[str, Any]]
    responses: Tuple[APIResponse, ...]

    # Examples
    examples: Tuple[CodeExample, ...]

    # Security
    authentication_required: bool
    permissions: FrozenSet[str]

    def __post_init__(self):
        """Enforce documentation rules."""
        # Every endpoint must document at least one response
        if not self.responses:
            raise ValueError("API must have at least one response documented")

        # POST/PUT must have request body or parameters
        if self.method in [APIMethod.POST, APIMethod.PUT]:
            if not self.request_body and not self.parameters:
                raise ValueError(
                    f"{self.method} endpoints must have request body or parameters"
                )

        # Must have at least one success response
        success_responses = [r for r in self.responses if 200 <= r.status_code < 300]
        if not success_responses:
            raise ValueError("API must document at least one success response")


@dataclass(frozen=True)
class OpenAPISpec:
    """OpenAPI specification - immutable."""

    openapi_version: str

    # Info
    title: str
    description: str
    version: str

    # Servers
    servers: Tuple[Dict[str, str], ...]

    # Paths
    paths: Dict[str, List[APIDocumentation]]

    # Components
    schemas: Dict[str, Any]
    security_schemes: Dict[str, Any]

    # Tags
    tags: Tuple[Dict[str, str], ...]

    def to_yaml(self) -> str:
        """Pure function to generate YAML."""
        # Simplified - would use ruamel.yaml in production
        return f"openapi: {self.openapi_version}\n..."

    def to_json(self) -> str:
        """Pure function to generate JSON."""
        return json.dumps({"openapi": self.openapi_version}, indent=2)


@dataclass(frozen=True)
class DiagramNode:
    """Node in an architecture diagram - immutable."""

    id: str
    label: str
    node_type: str  # component, service, database, etc.

    # Styling
    shape: str  # box, circle, diamond, etc.
    color: Optional[str]
    icon: Optional[str]

    # Metadata
    properties: Dict[str, Any]


@dataclass(frozen=True)
class DiagramEdge:
    """Edge in an architecture diagram - immutable."""

    source: str
    target: str

    # Properties
    label: Optional[str]
    directed: bool
    style: str  # solid, dashed, dotted

    # Metadata
    properties: Dict[str, Any]


@dataclass(frozen=True)
class ArchitectureDiagram:
    """Architecture diagram definition - immutable."""

    name: str
    diagram_type: DiagramType

    # Diagram elements
    nodes: Tuple[DiagramNode, ...]
    edges: Tuple[DiagramEdge, ...]

    # Layout
    layout: str  # horizontal, vertical, circular

    # Metadata
    description: str
    tags: FrozenSet[str]

    def to_mermaid(self) -> DiagramDefinition:
        """Pure function to generate Mermaid diagram."""
        mermaid = f"graph {self.layout[0].upper()}D\n"

        # Add nodes
        for node in self.nodes:
            mermaid += f"  {node.id}[{node.label}]\n"

        # Add edges
        for edge in self.edges:
            arrow = "-->" if edge.directed else "---"
            mermaid += f"  {edge.source} {arrow} {edge.target}\n"

        return DiagramDefinition(mermaid)

    def to_plantuml(self) -> str:
        """Pure function to generate PlantUML."""
        return "@startuml\n...\n@enduml"


@dataclass(frozen=True)
class MigrationStep:
    """Single step in migration guide - immutable."""

    step_number: int
    title: str
    description: str

    # Commands/Actions
    commands: Tuple[str, ...]

    # Validation
    validation: str

    # Time estimate
    estimated_time: str

    # Risks
    risks: Tuple[str, ...]

    def __post_init__(self):
        """Validate step."""
        if self.step_number <= 0:
            raise ValueError("Step number must be positive")


@dataclass(frozen=True)
class MigrationGuide:
    """Migration guide documentation - immutable."""

    title: str

    # Overview
    summary: str
    scope: str
    timeline: str

    # Prerequisites
    prerequisites: Tuple[str, ...]

    # Migration steps
    steps: Tuple[MigrationStep, ...]

    # Validation
    validation_steps: Tuple[str, ...]

    # Rollback
    rollback_procedure: str

    # FAQs
    faqs: Tuple[Tuple[str, str], ...]  # (question, answer)

    def __post_init__(self):
        """Validate migration guide."""
        if not self.steps:
            raise ValueError("Migration guide must have at least one step")

        # Each step must be numbered sequentially
        for i, step in enumerate(self.steps, 1):
            if step.step_number != i:
                raise ValueError("Steps must be numbered sequentially")

    def to_markdown(self) -> MarkdownDocument:
        """Pure function to generate Markdown."""
        md = f"# {self.title}\n\n"
        md += f"## Summary\n{self.summary}\n\n"
        md += "## Prerequisites\n"
        for prereq in self.prerequisites:
            md += f"- {prereq}\n"
        md += "\n## Migration Steps\n"
        for step in self.steps:
            md += f"\n### Step {step.step_number}: {step.title}\n"
            md += f"{step.description}\n"
        return MarkdownDocument(md)


@dataclass(frozen=True)
class README:
    """README documentation - immutable."""

    project_name: str
    description: str

    # Sections
    badges: Tuple[str, ...]  # Badge URLs
    features: Tuple[str, ...]
    installation: str
    usage: str

    # Examples
    examples: Tuple[CodeExample, ...]

    # Contributing
    contributing: Optional[str]
    license: str

    # Links
    documentation_url: Optional[str]
    repository_url: Optional[str]

    def to_markdown(self) -> MarkdownDocument:
        """Pure function to generate README."""
        md = f"# {self.project_name}\n\n"

        # Badges
        for badge in self.badges:
            md += f"![Badge]({badge}) "
        md += "\n\n"

        # Description
        md += f"{self.description}\n\n"

        # Features
        md += "## Features\n"
        for feature in self.features:
            md += f"- {feature}\n"

        # Installation
        md += f"\n## Installation\n{self.installation}\n"

        # Usage
        md += f"\n## Usage\n{self.usage}\n"

        # Examples
        if self.examples:
            md += "\n## Examples\n"
            for example in self.examples:
                md += f"```\n{example}\n```\n"

        # License
        md += f"\n## License\n{self.license}\n"

        return MarkdownDocument(md)


@dataclass(frozen=True)
class DocumentationSuite:
    """Complete documentation suite - immutable."""

    # API documentation
    api_docs: OpenAPISpec

    # Architecture
    architecture_diagrams: Tuple[ArchitectureDiagram, ...]

    # Guides
    user_guide: Optional[MarkdownDocument]
    developer_guide: Optional[MarkdownDocument]
    migration_guide: Optional[MigrationGuide]

    # README
    readme: README

    # Metadata
    generated_at: datetime
    version: str

    @property
    def total_pages(self) -> int:
        """Calculate total documentation pages."""
        count = 1  # README
        count += len(self.architecture_diagrams)
        count += 1 if self.user_guide else 0
        count += 1 if self.developer_guide else 0
        count += 1 if self.migration_guide else 0
        return count


@dataclass(frozen=True)
class DocumentationError:
    """Error during documentation generation."""

    error_type: str
    message: str
    file_path: Optional[str] = None
    details: Dict[str, Any] = None


# ============================================================================
# PURE DOMAIN OPERATIONS (Functions that operate on the types above)
# ============================================================================


def extract_api_endpoints(
    application_model: Any,
) -> Result[List[APIEndpoint], DocumentationError]:
    """Extract API endpoints from application model.

    Pure function that analyzes the application model to find
    all API endpoints that need documentation.
    """
    try:
        endpoints = []
        # Would analyze model for controllers, routes, etc.
        # This is simplified for demonstration
        return Success(endpoints)
    except Exception as e:
        return Failure(
            DocumentationError(error_type="extraction_error", message=str(e))
        )


def generate_openapi_spec(
    api_docs: List[APIDocumentation], title: str, version: str
) -> Result[OpenAPISpec, DocumentationError]:
    """Generate OpenAPI specification from API documentation.

    Pure function that transforms API documentation into
    a complete OpenAPI 3.0 specification.
    """
    try:
        # Group endpoints by path
        paths = {}
        for doc in api_docs:
            path = str(doc.endpoint)
            if path not in paths:
                paths[path] = []
            paths[path].append(doc)

        spec = OpenAPISpec(
            openapi_version="3.0.0",
            title=title,
            description=f"API documentation for {title}",
            version=version,
            servers=tuple([{"url": "http://localhost:8000"}]),
            paths=paths,
            schemas={},
            security_schemes={},
            tags=tuple(),
        )

        return Success(spec)
    except Exception as e:
        return Failure(
            DocumentationError(error_type="generation_error", message=str(e))
        )


def generate_architecture_diagram(
    components: List[Any], relationships: List[Any]
) -> Result[ArchitectureDiagram, DocumentationError]:
    """Generate architecture diagram from components.

    Pure function that creates a visual representation
    of the system architecture.
    """
    try:
        # Convert components to nodes
        nodes = []
        for comp in components:
            node = DiagramNode(
                id=str(id(comp)),
                label=getattr(comp, "name", "Component"),
                node_type="component",
                shape="box",
                color=None,
                icon=None,
                properties={},
            )
            nodes.append(node)

        # Convert relationships to edges
        edges = []
        for rel in relationships:
            edge = DiagramEdge(
                source=str(id(rel)),
                target=str(id(rel)),
                label=None,
                directed=True,
                style="solid",
                properties={},
            )
            edges.append(edge)

        diagram = ArchitectureDiagram(
            name="System Architecture",
            diagram_type=DiagramType.COMPONENT,
            nodes=tuple(nodes),
            edges=tuple(edges),
            layout="horizontal",
            description="Component architecture diagram",
            tags=frozenset(["architecture"]),
        )

        return Success(diagram)
    except Exception as e:
        return Failure(DocumentationError(error_type="diagram_error", message=str(e)))


def generate_migration_guide(
    legacy_model: Any, modern_model: Any, migration_plan: Any
) -> Result[MigrationGuide, DocumentationError]:
    """Generate migration guide from legacy to modern.

    Pure function that creates step-by-step migration
    documentation for transitioning systems.
    """
    try:
        # Create migration steps
        steps = []
        step_num = 1

        # Add default steps (simplified)
        steps.append(
            MigrationStep(
                step_number=step_num,
                title="Backup existing system",
                description="Create full backup of legacy system",
                commands=tuple(["backup.sh"]),
                validation="Verify backup integrity",
                estimated_time="1 hour",
                risks=tuple(["Data loss if backup fails"]),
            )
        )

        guide = MigrationGuide(
            title="Legacy System Migration Guide",
            summary="Guide for migrating from legacy to modern system",
            scope="Full system migration",
            timeline="2-4 weeks",
            prerequisites=tuple(["System backup", "Test environment"]),
            steps=tuple(steps),
            validation_steps=tuple(["Run test suite", "Verify data integrity"]),
            rollback_procedure="Restore from backup",
            faqs=tuple([("How long?", "2-4 weeks")]),
        )

        return Success(guide)
    except Exception as e:
        return Failure(DocumentationError(error_type="guide_error", message=str(e)))


def generate_readme(
    project_name: str, description: str, features: List[str]
) -> Result[README, DocumentationError]:
    """Generate README documentation.

    Pure function that creates a complete README
    with all standard sections.
    """
    try:
        readme = README(
            project_name=project_name,
            description=description,
            badges=tuple(),
            features=tuple(features),
            installation="pip install package",
            usage="import package",
            examples=tuple(),
            contributing=None,
            license="MIT",
            documentation_url=None,
            repository_url=None,
        )

        return Success(readme)
    except Exception as e:
        return Failure(DocumentationError(error_type="readme_error", message=str(e)))


def build_documentation_suite(
    application_model: Any, project_info: Dict[str, Any]
) -> Result[DocumentationSuite, DocumentationError]:
    """Build complete documentation suite for application.

    Pure function that orchestrates all documentation generation
    to create a comprehensive documentation package.
    """
    try:
        # Generate individual documentation pieces
        api_result = extract_api_endpoints(application_model)
        if isinstance(api_result, Failure):
            return api_result

        # Generate OpenAPI spec
        openapi_result = generate_openapi_spec(
            [],  # Would use api_result.value
            project_info.get("name", "Project"),
            project_info.get("version", "1.0.0"),
        )
        if isinstance(openapi_result, Failure):
            return openapi_result

        # Generate README
        readme_result = generate_readme(
            project_info.get("name", "Project"),
            project_info.get("description", ""),
            project_info.get("features", []),
        )
        if isinstance(readme_result, Failure):
            return readme_result

        # Build complete suite
        suite = DocumentationSuite(
            api_docs=openapi_result.value,
            architecture_diagrams=tuple(),
            user_guide=None,
            developer_guide=None,
            migration_guide=None,
            readme=readme_result.value,
            generated_at=datetime.now(),
            version=project_info.get("version", "1.0.0"),
        )

        return Success(suite)
    except Exception as e:
        return Failure(DocumentationError(error_type="suite_error", message=str(e)))


def render_documentation_as_markdown(
    suite: DocumentationSuite,
) -> Result[str, DocumentationError]:
    """Render documentation suite as Markdown.

    Pure function that converts the entire documentation
    suite into Markdown format for display or export.
    """
    try:
        output = ""

        # Render README
        output += suite.readme.to_markdown() + "\n\n"

        # Render API docs as Markdown
        output += "# API Documentation\n\n"
        output += f"OpenAPI Version: {suite.api_docs.openapi_version}\n\n"

        # Render architecture diagrams
        for diagram in suite.architecture_diagrams:
            output += f"## {diagram.name}\n\n"
            output += f"```mermaid\n{diagram.to_mermaid()}\n```\n\n"

        # Render guides
        if suite.migration_guide:
            output += suite.migration_guide.to_markdown() + "\n\n"

        return Success(output)
    except Exception as e:
        return Failure(DocumentationError(error_type="render_error", message=str(e)))
