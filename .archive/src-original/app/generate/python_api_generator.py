"""Python API Generator Workflow.

Application layer workflow for generating Python/Litestar APIs from PowerBuilder.
Uses Parse Don't Validate pattern with factory functions.
Transforms PowerBuilder domain types to Python API endpoints and models.
"""

from typing import List
from datetime import datetime

from src_new.shared.result import Result, Success, Error
from src_new.domain.powerbuilder.objects import DataWindow
from src_new.domain.modern.python import (
    PydanticModel,
    SQLModelTable,
    LitestarController,
    APIEndpoint,
    HTTPMethod,
    APIResponse,
    ModelGenerated,
    EndpointCreated,
)


# ============================================================================
# PARSE DON'T VALIDATE - FACTORY FUNCTIONS
# ============================================================================


class _APIGeneratorToken:
    """Hidden token for Parse Don't Validate pattern."""

    pass


def create_api_from_datawindow(
    datawindow: DataWindow,
) -> Result[LitestarController, str]:
    """Create a validated API controller from DataWindow.

    Parse Don't Validate entry point.
    """
    if not datawindow.name:
        return Error("DataWindow must have a name")

    # Extract data model
    model_result = _create_data_model(datawindow)
    if isinstance(model_result, Error):
        return model_result

    # Create endpoints
    endpoints_result = _create_crud_endpoints(datawindow, model_result.value)
    if isinstance(endpoints_result, Error):
        return endpoints_result

    # Create validation
    validation_result = _create_validation(datawindow)
    if isinstance(validation_result, Error):
        return validation_result

    return Success(
        _create_controller_internal(
            name=f"{_to_pascal_case(datawindow.name)}Controller",
            model=model_result.value,
            endpoints=endpoints_result.value,
            validation=validation_result.value,
            token=_APIGeneratorToken(),
        )
    )


def _create_controller_internal(
    name: str,
    model: SQLModelTable,
    endpoints: List[APIEndpoint],
    validation: PydanticModel,
    token: _APIGeneratorToken,
) -> LitestarController:
    """Internal factory - requires token."""
    if not isinstance(token, _APIGeneratorToken):
        raise ValueError("Invalid token")

    return LitestarController(
        name=name,
        path=f"/{_to_kebab_case(name.replace('Controller', ''))}",
        endpoints=endpoints,
        dependencies=["SQLModel", "Litestar"],
        middleware=["CORS", "Authentication"],
        model=model,
        validation=validation,
    )


# ============================================================================
# MODEL CREATION
# ============================================================================


def _create_data_model(datawindow: DataWindow) -> Result[SQLModelTable, str]:
    """Create SQLModel table from DataWindow."""
    columns = []

    for col in datawindow.columns:
        columns.append(
            {
                "name": col.name,
                "type": _pb_to_python_type(col.data_type),
                "nullable": not col.required,
                "default": col.default_value,
            }
        )

    # Add standard fields
    columns.extend(
        [
            {"name": "id", "type": "int", "nullable": False, "primary_key": True},
            {"name": "created_at", "type": "datetime", "nullable": False},
            {"name": "updated_at", "type": "datetime", "nullable": False},
        ]
    )

    return Success(
        SQLModelTable(
            name=_to_pascal_case(datawindow.name),
            table_name=_to_snake_case(datawindow.name),
            columns=columns,
            relationships=[],
        )
    )


def _create_validation(datawindow: DataWindow) -> Result[PydanticModel, str]:
    """Create Pydantic validation model."""
    fields = []

    for col in datawindow.columns:
        field_type = _pb_to_python_type(col.data_type)
        if not col.required:
            field_type = f"Optional[{field_type}]"

        fields.append(
            {"name": col.name, "type": field_type, "validators": _get_validators(col)}
        )

    return Success(
        PydanticModel(
            name=f"{_to_pascal_case(datawindow.name)}Schema",
            fields=fields,
            config={"validate_assignment": True},
        )
    )


# ============================================================================
# ENDPOINT CREATION
# ============================================================================


def _create_crud_endpoints(
    datawindow: DataWindow, model: SQLModelTable
) -> Result[List[APIEndpoint], str]:
    """Create CRUD endpoints for DataWindow."""
    endpoints = []
    base_path = f"/{_to_kebab_case(datawindow.name)}"

    # GET all
    endpoints.append(
        APIEndpoint(
            path=base_path,
            method=HTTPMethod.GET,
            handler_name=f"get_{_to_snake_case(datawindow.name)}_list",
            parameters=["limit: int = 100", "offset: int = 0"],
            response=APIResponse(
                status_code=200,
                content_type="application/json",
                schema=f"List[{model.name}]",
            ),
            description=f"Get all {datawindow.name} records",
        )
    )

    # GET by ID
    endpoints.append(
        APIEndpoint(
            path=f"{base_path}/{{id:int}}",
            method=HTTPMethod.GET,
            handler_name=f"get_{_to_snake_case(datawindow.name)}_by_id",
            parameters=["id: int"],
            response=APIResponse(
                status_code=200, content_type="application/json", schema=model.name
            ),
            description=f"Get {datawindow.name} by ID",
        )
    )

    # POST
    endpoints.append(
        APIEndpoint(
            path=base_path,
            method=HTTPMethod.POST,
            handler_name=f"create_{_to_snake_case(datawindow.name)}",
            parameters=[f"data: {model.name}Schema"],
            response=APIResponse(
                status_code=201, content_type="application/json", schema=model.name
            ),
            description=f"Create new {datawindow.name}",
        )
    )

    # PUT
    endpoints.append(
        APIEndpoint(
            path=f"{base_path}/{{id:int}}",
            method=HTTPMethod.PUT,
            handler_name=f"update_{_to_snake_case(datawindow.name)}",
            parameters=["id: int", f"data: {model.name}Schema"],
            response=APIResponse(
                status_code=200, content_type="application/json", schema=model.name
            ),
            description=f"Update {datawindow.name}",
        )
    )

    # DELETE
    endpoints.append(
        APIEndpoint(
            path=f"{base_path}/{{id:int}}",
            method=HTTPMethod.DELETE,
            handler_name=f"delete_{_to_snake_case(datawindow.name)}",
            parameters=["id: int"],
            response=APIResponse(status_code=204, content_type=None),
            description=f"Delete {datawindow.name}",
        )
    )

    return Success(endpoints)


# ============================================================================
# CODE GENERATION
# ============================================================================


def generate_controller_code(controller: LitestarController) -> Result[str, str]:
    """Generate Python controller code."""
    lines = []

    # Imports
    lines.extend(_generate_imports(controller))
    lines.append("")

    # Model definition
    lines.extend(_generate_model(controller.model))
    lines.append("")

    # Validation schema
    lines.extend(_generate_schema(controller.validation))
    lines.append("")

    # Controller class
    lines.extend(_generate_controller_class(controller))

    return Success("\n".join(lines))


def _generate_imports(controller: LitestarController) -> List[str]:
    """Generate import statements."""
    return [
        "from datetime import datetime",
        "from typing import List, Optional",
        "from litestar import Litestar, get, post, put, delete, Controller",
        "from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin",
        "from litestar.exceptions import NotFoundException",
        "from sqlmodel import Field, Session, SQLModel, select",
        "from pydantic import BaseModel, validator",
    ]


def _generate_model(model: SQLModelTable) -> List[str]:
    """Generate SQLModel table class."""
    lines = [f"class {model.name}(SQLModel, table=True):"]
    lines.append(f'    """Database model for {model.name}."""')
    lines.append(f'    __tablename__ = "{model.table_name}"')
    lines.append("")

    for col in model.columns:
        col_type = col.get("type", "str")
        nullable = "Optional" if col.get("nullable") else ""
        primary_key = ", primary_key=True" if col.get("primary_key") else ""
        default = f", default={col.get('default')}" if col.get("default") else ""

        if nullable:
            lines.append(
                f"    {col['name']}: Optional[{col_type}] = Field(None{primary_key}{default})"
            )
        else:
            lines.append(
                f"    {col['name']}: {col_type} = Field(...{primary_key}{default})"
            )

    return lines


def _generate_schema(validation: PydanticModel) -> List[str]:
    """Generate Pydantic validation schema."""
    lines = [f"class {validation.name}(BaseModel):"]
    lines.append(f'    """Validation schema for {validation.name}."""')

    for field in validation.fields:
        lines.append(f"    {field['name']}: {field['type']}")

    lines.append("")
    lines.append("    class Config:")
    for key, value in validation.config.items():
        lines.append(f"        {key} = {value}")

    return lines


def _generate_controller_class(controller: LitestarController) -> List[str]:
    """Generate Litestar controller class."""
    lines = [f"class {controller.name}(Controller):"]
    lines.append(f'    """API controller for {controller.name}."""')
    lines.append(f'    path = "{controller.path}"')
    lines.append("")

    for endpoint in controller.endpoints:
        lines.extend(_generate_endpoint_method(endpoint))
        lines.append("")

    return lines


def _generate_endpoint_method(endpoint: APIEndpoint) -> List[str]:
    """Generate endpoint method."""
    lines = []

    # Decorator
    method_name = endpoint.method.value.lower()
    lines.append(f'    @{method_name}("{endpoint.path}")')

    # Method signature
    params = ", ".join(["self"] + endpoint.parameters)
    lines.append(f"    async def {endpoint.handler_name}({params}):")

    # Docstring
    lines.append(f'        """{endpoint.description}"""')

    # Method body (simplified)
    if endpoint.method == HTTPMethod.GET:
        lines.append("        async with Session(engine) as session:")
        lines.append("            # Query logic here")
        lines.append("            return []")
    elif endpoint.method == HTTPMethod.POST:
        lines.append("        async with Session(engine) as session:")
        lines.append("            # Create logic here")
        lines.append("            return data")
    elif endpoint.method == HTTPMethod.DELETE:
        lines.append("        async with Session(engine) as session:")
        lines.append("            # Delete logic here")
        lines.append("            return")

    return lines


# ============================================================================
# UTILITIES
# ============================================================================


def _to_pascal_case(name: str) -> str:
    """Convert to PascalCase."""
    return "".join(p.capitalize() for p in name.split("_"))


def _to_snake_case(name: str) -> str:
    """Convert to snake_case."""
    return name.lower()


def _to_kebab_case(name: str) -> str:
    """Convert to kebab-case."""
    return name.lower().replace("_", "-")


def _pb_to_python_type(pb_type: str) -> str:
    """Convert PowerBuilder type to Python type."""
    type_map = {
        "string": "str",
        "char": "str",
        "integer": "int",
        "long": "int",
        "decimal": "float",
        "boolean": "bool",
        "date": "date",
        "datetime": "datetime",
        "time": "time",
    }
    return type_map.get(pb_type.lower(), "str")


def _get_validators(column) -> List[str]:
    """Get validators for column."""
    validators = []

    if hasattr(column, "max_length") and column.max_length:
        validators.append(f"max_length={column.max_length}")

    if hasattr(column, "min_value") and column.min_value:
        validators.append(f"ge={column.min_value}")

    if hasattr(column, "max_value") and column.max_value:
        validators.append(f"le={column.max_value}")

    return validators


# ============================================================================
# EVENT EMISSION
# ============================================================================


def emit_model_generated(model: SQLModelTable, source: DataWindow) -> ModelGenerated:
    """Emit model generated event."""
    return ModelGenerated(
        model=model,
        source_type="DataWindow",
        source_name=source.name,
        timestamp=datetime.now(),
    )


def emit_endpoint_created(endpoint: APIEndpoint, controller: str) -> EndpointCreated:
    """Emit endpoint created event."""
    return EndpointCreated(
        endpoint=endpoint, controller_name=controller, timestamp=datetime.now()
    )
