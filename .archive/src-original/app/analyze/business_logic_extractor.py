"""Extract Business Logic - Self-Contained FDM Module.

Following Scott Wlaschin's functional domain modeling principles:
- Types are co-located with the functions that use them (no separate type files)
- All data structures are immutable using frozen dataclasses
- Functions are pure and return Result types for error handling
- No external dependencies except the core Result type
- Uses domain language from business logic extraction problem space

This module is completely self-contained - both types and operations
for extracting business rules and logic live together in this single file.
"""

from typing import List, Dict, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src_new._core.result import Result, Success, Failure
from src_new._core.legacy_modernization_types import (
    LegacyApplicationModel,
    GenericAST,
    ASTNodeType,
    CodeModule,
    FunctionDef,
)


# ============================================================================
# BUSINESS LOGIC TYPES
# ============================================================================


class BusinessRuleType(str, Enum):
    """Types of business rules."""

    VALIDATION = "validation"  # Input validation
    CALCULATION = "calculation"  # Business calculations
    WORKFLOW = "workflow"  # Process workflows
    AUTHORIZATION = "authorization"  # Access control
    TRANSFORMATION = "transformation"  # Data transformation
    CONSTRAINT = "constraint"  # Business constraints
    DECISION = "decision"  # Decision logic
    NOTIFICATION = "notification"  # Alert/notification rules


class ComplexityLevel(str, Enum):
    """Complexity level of business logic."""

    SIMPLE = "simple"  # Single condition/calculation
    MODERATE = "moderate"  # Multiple conditions
    COMPLEX = "complex"  # Nested logic/multiple branches
    CRITICAL = "critical"  # Core business algorithm


class LogicPattern(str, Enum):
    """Common business logic patterns."""

    IF_THEN_ELSE = "if_then_else"
    SWITCH_CASE = "switch_case"
    LOOP_AGGREGATION = "loop_aggregation"
    STATE_MACHINE = "state_machine"
    RULE_ENGINE = "rule_engine"
    FORMULA = "formula"
    LOOKUP_TABLE = "lookup_table"
    VALIDATION_CHAIN = "validation_chain"


# ============================================================================
# BUSINESS RULE WITH FACTORY PATTERN (Scott Wlaschin's Parse Don't Validate)
# ============================================================================


def _make_business_rule():
    """Create BusinessRule class with private constructor.

    Following Scott Wlaschin's FDM: The type can only be created through
    parse_business_rule() which validates during parsing, not after construction.
    """
    _token = object()  # Unique token in closure

    @dataclass(frozen=True)
    class BusinessRule:
        """A validated business rule - can only be created through parse function."""

        name: str
        rule_type: BusinessRuleType
        description: str

        # Rule definition
        conditions: Tuple[str, ...]  # When this rule applies (immutable)
        actions: Tuple[str, ...]  # What the rule does (immutable)
        exceptions: Tuple[str, ...]  # Exception cases (immutable)

        # Properties
        complexity: ComplexityLevel
        pattern: LogicPattern
        is_configurable: bool  # Can be externalized to config

        # Source location
        source_file: str
        source_function: str
        line_number: int

        # Dependencies
        depends_on: Tuple[str, ...]  # Other rules/data (immutable)
        affects: Tuple[str, ...]  # What this rule impacts (immutable)

        # Metadata
        priority: int  # Execution priority
        tags: Tuple[str, ...]  # Business domain tags (immutable)
        metadata: Dict[str, Any] = field(default_factory=dict)

        # Private token to prevent direct construction
        _token: object = field(default=None, repr=False, compare=False)

        def __post_init__(self):
            """Prevent direct construction - must use parse_business_rule()."""
            if self._token is not _token:
                raise TypeError(
                    "Cannot construct BusinessRule directly. "
                    "Use parse_business_rule() to create validated instances."
                )

        @classmethod
        def _create(cls, **kwargs):
            """Internal factory - only accessible within this closure."""
            return cls(**kwargs, _token=_token)

    return BusinessRule


BusinessRule = _make_business_rule()
del _make_business_rule  # Remove factory function


def parse_business_rule(data: Dict[str, Any]) -> Result[BusinessRule, Exception]:
    """Parse raw data into validated BusinessRule or error.

    This is the ONLY way to create a BusinessRule. All validation happens
    during parsing, following Scott Wlaschin's "Parse, Don't Validate" principle.
    """
    try:
        # Validate during parsing
        if not data.get("name"):
            return Failure(ValueError("Business rule must have a name"))

        if not data.get("conditions"):
            return Failure(ValueError("Business rule must have at least one condition"))

        if data.get("priority", 0) < 0:
            return Failure(ValueError("Priority must be non-negative"))

        # Parse and create validated instance
        rule = BusinessRule._create(
            name=data["name"],
            rule_type=BusinessRuleType(data.get("type", BusinessRuleType.VALIDATION)),
            description=data.get("description", ""),
            conditions=tuple(data.get("conditions", [])),
            actions=tuple(data.get("actions", [])),
            exceptions=tuple(data.get("exceptions", [])),
            complexity=ComplexityLevel(data.get("complexity", ComplexityLevel.SIMPLE)),
            pattern=LogicPattern(data.get("pattern", LogicPattern.IF_THEN_ELSE)),
            is_configurable=data.get("is_configurable", False),
            source_file=data.get("source_file", ""),
            source_function=data.get("source_function", ""),
            line_number=data.get("line_number", 0),
            depends_on=tuple(data.get("depends_on", [])),
            affects=tuple(data.get("affects", [])),
            priority=data.get("priority", 0),
            tags=tuple(data.get("tags", [])),
            metadata=data.get("metadata", {}),
        )

        return Success(rule)

    except Exception as e:
        return Failure(e)


@dataclass(frozen=True)
class BusinessWorkflow:
    """A business process workflow."""

    name: str
    description: str

    # Workflow steps
    steps: List["WorkflowStep"]
    transitions: List["WorkflowTransition"]

    # Properties
    is_linear: bool  # Sequential vs branching
    has_loops: bool  # Contains loops
    has_parallel: bool  # Parallel execution

    # Actors
    actors: List[str]  # Roles/systems involved
    triggers: List[str]  # What starts the workflow
    outputs: List[str]  # Workflow results

    # Rules
    embedded_rules: List[BusinessRule]

    # Metadata
    sla: Optional[str] = None  # Service level agreement
    frequency: Optional[str] = None  # How often it runs


@dataclass(frozen=True)
class WorkflowStep:
    """A step in a business workflow."""

    id: str
    name: str
    action: str  # What happens
    actor: str  # Who/what performs it

    # Conditions
    pre_conditions: List[str]
    post_conditions: List[str]

    # Timing
    timeout: Optional[str] = None
    is_automated: bool = True


@dataclass(frozen=True)
class WorkflowTransition:
    """A transition between workflow steps."""

    from_step: str
    to_step: str
    condition: Optional[str]  # Transition condition
    is_default: bool = False  # Default path


@dataclass(frozen=True)
class BusinessCalculation:
    """A business calculation or formula."""

    name: str
    description: str

    # Formula definition
    formula: str  # The calculation
    variables: Dict[str, str]  # Variable definitions

    # Properties
    precision: Optional[int]  # Decimal precision
    rounding: Optional[str]  # Rounding method
    unit: Optional[str]  # Unit of measure

    # Validation
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    valid_range: Optional[str] = None

    # Source
    source_location: str
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationRule:
    """A data validation rule."""

    name: str
    field: str  # Field being validated

    # Validation definition
    validation_type: str  # Type of validation
    condition: str  # Validation condition
    error_message: str  # Error to show

    # Properties
    is_required: bool
    is_async: bool = False  # Requires external check
    severity: str = "error"  # error, warning, info

    # Dependencies
    depends_on_fields: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class BusinessLogicModel:
    """Complete business logic model."""

    # Rules and logic
    business_rules: Dict[str, BusinessRule]
    workflows: Dict[str, BusinessWorkflow]
    calculations: Dict[str, BusinessCalculation]
    validations: Dict[str, ValidationRule]

    # Categorization
    rules_by_type: Dict[BusinessRuleType, List[str]]
    rules_by_domain: Dict[str, List[str]]  # Domain/module grouping

    # Complexity metrics
    total_rules: int
    complexity_distribution: Dict[ComplexityLevel, int]
    pattern_distribution: Dict[LogicPattern, int]

    # Dependencies
    rule_dependencies: Dict[str, Set[str]]
    external_dependencies: List[str]  # External systems/data

    # Quality metrics
    documentation_coverage: float  # % of rules documented
    test_coverage: float  # % of rules tested
    duplication_score: float  # Code duplication


@dataclass(frozen=True)
class BusinessLogicExtractionError:
    """Error during business logic extraction."""

    error_type: str
    message: str
    location: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# BUSINESS LOGIC EXTRACTION
# ============================================================================


def extract_business_logic(
    model: LegacyApplicationModel,
) -> Result[BusinessLogicModel, BusinessLogicExtractionError]:
    """Extract business logic from application model.

    Pure function: Model -> Result[BusinessLogic, Error]
    """
    rules = {}
    workflows = {}
    calculations = {}
    validations = {}

    # Extract from code modules
    for module_name, module in model.code_modules.items():
        module_result = _extract_from_module(module, module_name)
        if module_result.is_success():
            module_logic = module_result.value()
            rules.update(module_logic["rules"])
            calculations.update(module_logic["calculations"])
            validations.update(module_logic["validations"])

    # Extract from UI event handlers
    for ui_name, ui_container in model.ui_containers.items():
        ui_result = _extract_from_ui(ui_container, ui_name)
        if ui_result.is_success():
            ui_logic = ui_result.value()
            rules.update(ui_logic["rules"])
            validations.update(ui_logic["validations"])

    # Extract workflows
    workflow_result = _extract_workflows(model)
    if workflow_result.is_success():
        workflows = workflow_result.value()

    # Categorize rules
    rules_by_type = _categorize_by_type(rules)
    rules_by_domain = _categorize_by_domain(rules)

    # Build dependencies
    rule_dependencies = _build_rule_dependencies(rules, calculations)
    external_deps = _find_external_dependencies(rules, workflows)

    # Calculate metrics
    complexity_dist = _calculate_complexity_distribution(rules)
    pattern_dist = _calculate_pattern_distribution(rules)
    doc_coverage = _calculate_documentation_coverage(rules)
    duplication = _calculate_duplication_score(rules)

    logic_model = BusinessLogicModel(
        business_rules=rules,
        workflows=workflows,
        calculations=calculations,
        validations=validations,
        rules_by_type=rules_by_type,
        rules_by_domain=rules_by_domain,
        total_rules=len(rules),
        complexity_distribution=complexity_dist,
        pattern_distribution=pattern_dist,
        rule_dependencies=rule_dependencies,
        external_dependencies=external_deps,
        documentation_coverage=doc_coverage,
        test_coverage=0.0,  # Would need test analysis
        duplication_score=duplication,
    )

    return Success(logic_model)


# ============================================================================
# PATTERN DETECTION
# ============================================================================


def detect_business_patterns(
    ast: GenericAST,
) -> Result[List[Tuple[LogicPattern, str]], BusinessLogicExtractionError]:
    """Detect business logic patterns in AST.

    Pure function: AST -> Result[Patterns, Error]
    """
    patterns = []

    # Traverse AST
    def visit(node: GenericAST) -> None:
        if node.node_type == ASTNodeType.IF_STATEMENT:
            # Check for if-then-else pattern
            if _has_else_branch(node):
                patterns.append((LogicPattern.IF_THEN_ELSE, node.name or "conditional"))

            # Check for validation chain
            if _is_validation_chain(node):
                patterns.append(
                    (LogicPattern.VALIDATION_CHAIN, node.name or "validation")
                )

        elif node.node_type == ASTNodeType.SWITCH_STATEMENT:
            patterns.append((LogicPattern.SWITCH_CASE, node.name or "switch"))

        elif node.node_type == ASTNodeType.LOOP:
            # Check for aggregation pattern
            if _is_aggregation_loop(node):
                patterns.append(
                    (LogicPattern.LOOP_AGGREGATION, node.name or "aggregation")
                )

        elif node.node_type == ASTNodeType.ASSIGNMENT:
            # Check for formula pattern
            if _is_formula(node):
                patterns.append((LogicPattern.FORMULA, node.name or "calculation"))

        # Recurse
        for child in node.children:
            visit(child)

    visit(ast)

    return Success(patterns)


# ============================================================================
# RULE GENERATION
# ============================================================================


def generate_rule_documentation(rule: BusinessRule) -> str:
    """Generate documentation for a business rule.

    Pure function: Rule -> Documentation
    """
    doc = f"""## Business Rule: {rule.name}

**Type:** {rule.rule_type.value}
**Complexity:** {rule.complexity.value}
**Pattern:** {rule.pattern.value}

### Description
{rule.description}

### Conditions
"""

    for i, condition in enumerate(rule.conditions, 1):
        doc += f"{i}. {condition}\n"

    doc += "\n### Actions\n"
    for i, action in enumerate(rule.actions, 1):
        doc += f"{i}. {action}\n"

    if rule.exceptions:
        doc += "\n### Exceptions\n"
        for i, exception in enumerate(rule.exceptions, 1):
            doc += f"{i}. {exception}\n"

    if rule.depends_on:
        doc += "\n### Dependencies\n"
        doc += ", ".join(rule.depends_on) + "\n"

    doc += f"\n### Source\nFile: {rule.source_file}\n"
    doc += f"Function: {rule.source_function}\n"
    doc += f"Line: {rule.line_number}\n"

    return doc


def generate_rules_config(rules: Dict[str, BusinessRule]) -> Dict[str, Any]:
    """Generate configuration file for business rules.

    Pure function: Rules -> Config
    """
    config = {"version": "1.0", "rules": {}}

    for name, rule in rules.items():
        if rule.is_configurable:
            config["rules"][name] = {
                "type": rule.rule_type.value,
                "enabled": True,
                "priority": rule.priority,
                "conditions": rule.conditions,
                "actions": rule.actions,
                "metadata": rule.metadata,
            }

    return config


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _extract_from_module(
    module: CodeModule, module_name: str
) -> Result[Dict[str, Any], BusinessLogicExtractionError]:
    """Extract business logic from a code module."""
    rules = {}
    calculations = {}
    validations = {}

    for func in module.functions:
        # Analyze function for business logic
        if _is_business_function(func):
            # Extract rules
            func_rules = _extract_rules_from_function(func, module_name)
            rules.update(func_rules)

            # Extract calculations
            if _has_calculations(func):
                calcs = _extract_calculations(func, module_name)
                calculations.update(calcs)

            # Extract validations
            if _has_validations(func):
                vals = _extract_validations(func, module_name)
                validations.update(vals)

    return Success(
        {"rules": rules, "calculations": calculations, "validations": validations}
    )


def _extract_from_ui(
    ui_container: Any, ui_name: str
) -> Result[Dict[str, Any], BusinessLogicExtractionError]:
    """Extract business logic from UI container."""
    rules = {}
    validations = {}

    # Extract from event handlers
    if hasattr(ui_container, "event_handlers"):
        for handler in ui_container.event_handlers:
            if hasattr(handler, "code"):
                # Look for business logic in handler
                if _contains_business_logic(handler.code):
                    rule_name = f"{ui_name}_{handler.event}_rule"
                    rules[rule_name] = BusinessRule(
                        name=rule_name,
                        rule_type=BusinessRuleType.WORKFLOW,
                        description=f"UI event handler for {handler.event}",
                        conditions=[f"User triggers {handler.event}"],
                        actions=_extract_actions(handler.code),
                        exceptions=[],
                        complexity=ComplexityLevel.MODERATE,
                        pattern=LogicPattern.IF_THEN_ELSE,
                        is_configurable=False,
                        source_file=ui_name,
                        source_function=handler.event,
                        line_number=0,
                        depends_on=[],
                        affects=[],
                        priority=5,
                        tags=["ui", "event"],
                    )

    # Extract field validations
    if hasattr(ui_container, "controls"):
        for control in ui_container.controls:
            if hasattr(control, "validation"):
                val_name = f"{ui_name}_{control.name}_validation"
                validations[val_name] = ValidationRule(
                    name=val_name,
                    field=control.name,
                    validation_type=control.validation.type,
                    condition=control.validation.condition,
                    error_message=control.validation.message,
                    is_required=control.validation.required,
                    is_async=False,
                )

    return Success({"rules": rules, "validations": validations})


def _extract_workflows(
    model: LegacyApplicationModel,
) -> Result[Dict[str, BusinessWorkflow], BusinessLogicExtractionError]:
    """Extract business workflows from model."""
    workflows = {}

    # Look for workflow patterns in UI navigation
    for ui_name, ui_container in model.ui_containers.items():
        if _is_workflow_screen(ui_container):
            workflow = _build_workflow_from_ui(ui_container, ui_name)
            workflows[workflow.name] = workflow

    # Look for state machines in code
    for module_name, module in model.code_modules.items():
        if _has_state_machine(module):
            workflow = _build_workflow_from_state_machine(module, module_name)
            workflows[workflow.name] = workflow

    return Success(workflows)


def _is_business_function(func: FunctionDef) -> bool:
    """Check if function contains business logic."""
    # Look for indicators
    indicators = [
        "validate",
        "calculate",
        "process",
        "check",
        "verify",
        "compute",
        "determine",
        "evaluate",
        "authorize",
        "approve",
        "reject",
        "transform",
    ]

    name_lower = func.name.lower()
    return any(ind in name_lower for ind in indicators)


def _has_calculations(func: FunctionDef) -> bool:
    """Check if function has calculations."""
    if not hasattr(func, "body"):
        return False

    # Look for mathematical operations
    math_ops = ["+", "-", "*", "/", "%", "**", "Math.", "calculate"]
    body = str(func.body)
    return any(op in body for op in math_ops)


def _has_validations(func: FunctionDef) -> bool:
    """Check if function has validations."""
    if not hasattr(func, "body"):
        return False

    # Look for validation patterns
    patterns = ["if ", "check", "valid", "error", "throw", "assert"]
    body = str(func.body).lower()
    return any(pattern in body for pattern in patterns)


def _extract_rules_from_function(
    func: FunctionDef, module_name: str
) -> Dict[str, BusinessRule]:
    """Extract business rules from function."""
    rules = {}

    # Simplified extraction
    rule_name = f"{module_name}_{func.name}_rule"

    # Determine rule type
    rule_type = BusinessRuleType.CALCULATION
    if "validate" in func.name.lower():
        rule_type = BusinessRuleType.VALIDATION
    elif "authorize" in func.name.lower():
        rule_type = BusinessRuleType.AUTHORIZATION
    elif "transform" in func.name.lower():
        rule_type = BusinessRuleType.TRANSFORMATION

    rules[rule_name] = BusinessRule(
        name=rule_name,
        rule_type=rule_type,
        description=f"Business rule from {func.name}",
        conditions=_extract_conditions(func),
        actions=_extract_actions(func.body if hasattr(func, "body") else ""),
        exceptions=[],
        complexity=_determine_complexity(func),
        pattern=_determine_pattern(func),
        is_configurable=_is_configurable(func),
        source_file=module_name,
        source_function=func.name,
        line_number=func.line_number if hasattr(func, "line_number") else 0,
        depends_on=[],
        affects=[],
        priority=5,
        tags=_extract_tags(func),
    )

    return rules


def _extract_calculations(
    func: FunctionDef, module_name: str
) -> Dict[str, BusinessCalculation]:
    """Extract calculations from function."""
    calculations = {}

    if hasattr(func, "body"):
        # Look for assignment with math
        calc_name = f"{module_name}_{func.name}_calc"
        calculations[calc_name] = BusinessCalculation(
            name=calc_name,
            description=f"Calculation in {func.name}",
            formula="extracted_formula",  # Would parse actual formula
            variables={},
            precision=2,
            rounding="round",
            unit=None,
            source_location=f"{module_name}.{func.name}",
        )

    return calculations


def _extract_validations(
    func: FunctionDef, module_name: str
) -> Dict[str, ValidationRule]:
    """Extract validation rules from function."""
    validations = {}

    val_name = f"{module_name}_{func.name}_validation"
    validations[val_name] = ValidationRule(
        name=val_name,
        field="unknown",  # Would need to parse
        validation_type="custom",
        condition="extracted_condition",
        error_message="Validation failed",
        is_required=True,
    )

    return validations


def _extract_conditions(func: FunctionDef) -> List[str]:
    """Extract conditions from function."""
    conditions = []

    if hasattr(func, "body"):
        # Simplified - would parse AST for actual conditions
        if "if " in str(func.body):
            conditions.append("Conditional logic present")

    return conditions if conditions else ["Always applies"]


def _extract_actions(code: str) -> List[str]:
    """Extract actions from code."""
    actions = []

    # Simplified - would parse for actual actions
    if "return" in code:
        actions.append("Returns calculated value")
    if "throw" in code or "raise" in code:
        actions.append("Raises error on violation")
    if "=" in code:
        actions.append("Updates data")

    return actions if actions else ["Performs business logic"]


def _determine_complexity(func: FunctionDef) -> ComplexityLevel:
    """Determine complexity of function."""
    if not hasattr(func, "body"):
        return ComplexityLevel.SIMPLE

    body = str(func.body)

    # Count complexity indicators
    nested_ifs = body.count("if ") > 2
    loops = "for " in body or "while " in body
    multiple_returns = body.count("return") > 1

    if nested_ifs or (loops and "if " in body):
        return ComplexityLevel.COMPLEX
    elif loops or multiple_returns:
        return ComplexityLevel.MODERATE
    else:
        return ComplexityLevel.SIMPLE


def _determine_pattern(func: FunctionDef) -> LogicPattern:
    """Determine logic pattern of function."""
    if not hasattr(func, "body"):
        return LogicPattern.IF_THEN_ELSE

    body = str(func.body)

    if "switch" in body or "case " in body:
        return LogicPattern.SWITCH_CASE
    elif "for " in body and ("+=" in body or "sum" in body):
        return LogicPattern.LOOP_AGGREGATION
    elif "validate" in func.name.lower():
        return LogicPattern.VALIDATION_CHAIN
    else:
        return LogicPattern.IF_THEN_ELSE


def _is_configurable(func: FunctionDef) -> bool:
    """Check if rule can be externalized to config."""
    # Simple heuristic - no complex logic
    complexity = _determine_complexity(func)
    return complexity == ComplexityLevel.SIMPLE


def _extract_tags(func: FunctionDef) -> List[str]:
    """Extract domain tags from function."""
    tags = []

    # Based on function name
    name_lower = func.name.lower()
    if "customer" in name_lower:
        tags.append("customer")
    if "order" in name_lower:
        tags.append("order")
    if "payment" in name_lower:
        tags.append("payment")
    if "inventory" in name_lower:
        tags.append("inventory")

    return tags


def _contains_business_logic(code: str) -> bool:
    """Check if code contains business logic."""
    indicators = ["if ", "calculate", "validate", "process"]
    return any(ind in code.lower() for ind in indicators)


def _is_workflow_screen(ui_container: Any) -> bool:
    """Check if UI represents a workflow."""
    # Look for wizard-like patterns
    if hasattr(ui_container, "title"):
        title_lower = ui_container.title.lower()
        return any(
            word in title_lower for word in ["wizard", "step", "process", "workflow"]
        )
    return False


def _build_workflow_from_ui(ui_container: Any, name: str) -> BusinessWorkflow:
    """Build workflow from UI container."""
    steps = []
    transitions = []

    # Simplified - would analyze UI flow
    steps.append(
        WorkflowStep(
            id="step1",
            name="Start",
            action="Initialize process",
            actor="system",
            pre_conditions=[],
            post_conditions=[],
        )
    )

    return BusinessWorkflow(
        name=f"{name}_workflow",
        description=f"Workflow from {name}",
        steps=steps,
        transitions=transitions,
        is_linear=True,
        has_loops=False,
        has_parallel=False,
        actors=["user", "system"],
        triggers=["user_action"],
        outputs=["completed"],
        embedded_rules=[],
    )


def _has_state_machine(module: CodeModule) -> bool:
    """Check if module contains state machine."""
    # Look for state pattern indicators
    for func in module.functions:
        if "state" in func.name.lower() or "transition" in func.name.lower():
            return True
    return False


def _build_workflow_from_state_machine(
    module: CodeModule, name: str
) -> BusinessWorkflow:
    """Build workflow from state machine."""
    # Simplified implementation
    return BusinessWorkflow(
        name=f"{name}_state_workflow",
        description=f"State machine from {name}",
        steps=[],
        transitions=[],
        is_linear=False,
        has_loops=True,
        has_parallel=False,
        actors=["system"],
        triggers=["event"],
        outputs=["state_change"],
        embedded_rules=[],
    )


def _has_else_branch(node: GenericAST) -> bool:
    """Check if IF node has else branch."""
    return any(child.node_type == ASTNodeType.ELSE_CLAUSE for child in node.children)


def _is_validation_chain(node: GenericAST) -> bool:
    """Check if node is a validation chain."""
    # Multiple sequential IFs without else
    if_count = sum(
        1 for child in node.children if child.node_type == ASTNodeType.IF_STATEMENT
    )
    return if_count > 2


def _is_aggregation_loop(node: GenericAST) -> bool:
    """Check if loop performs aggregation."""
    # Look for accumulator pattern
    for child in node.children:
        if child.node_type == ASTNodeType.ASSIGNMENT:
            if "+=" in str(child.attributes.get("operator", "")):
                return True
    return False


def _is_formula(node: GenericAST) -> bool:
    """Check if assignment is a formula."""
    # Has mathematical operations
    if "expression" in node.attributes:
        expr = str(node.attributes["expression"])
        return any(op in expr for op in ["+", "-", "*", "/", "%"])
    return False


def _categorize_by_type(
    rules: Dict[str, BusinessRule],
) -> Dict[BusinessRuleType, List[str]]:
    """Categorize rules by type."""
    categorized = {rule_type: [] for rule_type in BusinessRuleType}

    for name, rule in rules.items():
        categorized[rule.rule_type].append(name)

    return categorized


def _categorize_by_domain(rules: Dict[str, BusinessRule]) -> Dict[str, List[str]]:
    """Categorize rules by business domain."""
    domains = {}

    for name, rule in rules.items():
        for tag in rule.tags:
            if tag not in domains:
                domains[tag] = []
            domains[tag].append(name)

    return domains


def _build_rule_dependencies(
    rules: Dict[str, BusinessRule], calculations: Dict[str, BusinessCalculation]
) -> Dict[str, Set[str]]:
    """Build rule dependency graph."""
    dependencies = {}

    for name, rule in rules.items():
        dependencies[name] = set(rule.depends_on)

    return dependencies


def _find_external_dependencies(
    rules: Dict[str, BusinessRule], workflows: Dict[str, BusinessWorkflow]
) -> List[str]:
    """Find external system dependencies."""
    external = set()

    # Check rule dependencies
    for rule in rules.values():
        for dep in rule.depends_on:
            if dep.startswith("external_") or dep.startswith("api_"):
                external.add(dep)

    # Check workflow actors
    for workflow in workflows.values():
        for actor in workflow.actors:
            if actor.startswith("external_"):
                external.add(actor)

    return list(external)


def _calculate_complexity_distribution(
    rules: Dict[str, BusinessRule],
) -> Dict[ComplexityLevel, int]:
    """Calculate distribution of rule complexity."""
    dist = {level: 0 for level in ComplexityLevel}

    for rule in rules.values():
        dist[rule.complexity] += 1

    return dist


def _calculate_pattern_distribution(
    rules: Dict[str, BusinessRule],
) -> Dict[LogicPattern, int]:
    """Calculate distribution of logic patterns."""
    dist = {pattern: 0 for pattern in LogicPattern}

    for rule in rules.values():
        dist[rule.pattern] += 1

    return dist


def _calculate_documentation_coverage(rules: Dict[str, BusinessRule]) -> float:
    """Calculate documentation coverage."""
    if not rules:
        return 1.0

    documented = sum(
        1 for rule in rules.values() if rule.description and rule.description != ""
    )

    return documented / len(rules)


def _calculate_duplication_score(rules: Dict[str, BusinessRule]) -> float:
    """Calculate code duplication score."""
    # Simplified - check for similar conditions/actions
    if not rules:
        return 0.0

    all_conditions = []
    for rule in rules.values():
        all_conditions.extend(rule.conditions)

    unique_conditions = len(set(all_conditions))
    total_conditions = len(all_conditions)

    if total_conditions == 0:
        return 0.0

    return 1.0 - (unique_conditions / total_conditions)
