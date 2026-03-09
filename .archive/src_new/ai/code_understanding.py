"""AI/ML Code Understanding - Use LLMs to understand and modernize legacy code.

This module integrates AI models for understanding PowerBuilder code intent,
suggesting improvements, and generating documentation.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """AI model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    OLLAMA = "ollama"


class AnalysisType(str, Enum):
    """Types of AI analysis."""

    UNDERSTAND = "understand"
    REFACTOR = "refactor"
    DOCUMENT = "document"
    MODERNIZE = "modernize"
    TEST = "test"
    SECURITY = "security"


@dataclass
class CodeUnderstanding:
    """Result of AI code understanding."""

    intent: str
    business_logic: List[str]
    dependencies: List[str]
    patterns_detected: List[str]
    complexity_assessment: str
    modernization_suggestions: List[str]
    confidence_score: float


@dataclass
class RefactoringPlan:
    """AI-suggested refactoring plan."""

    description: str
    steps: List[str]
    estimated_impact: str
    risk_level: str
    modern_patterns: List[str]
    code_snippets: Dict[str, str] = field(default_factory=dict)


@dataclass
class DocumentationOutput:
    """AI-generated documentation."""

    summary: str
    purpose: str
    parameters: List[Dict[str, str]]
    returns: Optional[str]
    examples: List[str]
    notes: List[str]
    business_context: Optional[str] = None


@dataclass
class TestSuggestion:
    """AI-suggested test cases."""

    test_name: str
    test_type: str  # unit, integration, e2e
    description: str
    test_code: str
    edge_cases: List[str]
    expected_behavior: str


class AICodeAnalyzer:
    """AI-powered code analyzer."""

    def __init__(
        self,
        provider: AIProvider = AIProvider.LOCAL,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize AI code analyzer.

        Args:
            provider: AI provider to use
            model_name: Model name/ID
            api_key: API key for provider
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key

        # Initialize provider
        if provider == AIProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI library required: pip install openai")
            if api_key:
                openai.api_key = api_key

        elif provider == AIProvider.HUGGINGFACE:
            if not TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "Transformers library required: pip install transformers"
                )
            self._init_local_model()

    def _init_local_model(self):
        """Initialize local model for inference."""
        if self.provider == AIProvider.HUGGINGFACE:
            model_name = self.model_name or "microsoft/codebert-base"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.pipeline = pipeline(
                "text-generation", model=self.model, tokenizer=self.tokenizer
            )

    def understand_code(
        self,
        code: str,
        language: str = "powerbuilder",
        context: Optional[str] = None,
    ) -> CodeUnderstanding:
        """Understand code intent and business logic.

        Args:
            code: Source code to analyze
            language: Programming language
            context: Additional context

        Returns:
            Code understanding results
        """
        prompt = self._build_understanding_prompt(code, language, context)

        # Get AI response
        response = self._query_ai(prompt, AnalysisType.UNDERSTAND)

        # Parse response
        return self._parse_understanding_response(response)

    def _build_understanding_prompt(
        self,
        code: str,
        language: str,
        context: Optional[str],
    ) -> str:
        """Build prompt for code understanding.

        Args:
            code: Source code
            language: Programming language
            context: Additional context

        Returns:
            Formatted prompt
        """
        prompt = f"""Analyze this {language} code and provide:
1. The main intent and purpose
2. Business logic rules
3. External dependencies
4. Design patterns used
5. Complexity assessment
6. Modernization suggestions

Code:
```{language}
{code}
```
"""

        if context:
            prompt += f"\nContext: {context}"

        prompt += """
Please provide a structured analysis with specific details about what this code does,
why it might have been written this way, and how it could be improved using modern practices."""

        return prompt

    def suggest_refactoring(
        self,
        code: str,
        target_language: Optional[str] = None,
        patterns: Optional[List[str]] = None,
    ) -> RefactoringPlan:
        """Suggest code refactoring.

        Args:
            code: Source code to refactor
            target_language: Target language for refactoring
            patterns: Preferred design patterns

        Returns:
            Refactoring plan
        """
        prompt = self._build_refactoring_prompt(code, target_language, patterns)
        response = self._query_ai(prompt, AnalysisType.REFACTOR)
        return self._parse_refactoring_response(response)

    def _build_refactoring_prompt(
        self,
        code: str,
        target_language: Optional[str],
        patterns: Optional[List[str]],
    ) -> str:
        """Build prompt for refactoring suggestions.

        Args:
            code: Source code
            target_language: Target language
            patterns: Design patterns

        Returns:
            Formatted prompt
        """
        prompt = f"""Suggest refactoring for this code:
```
{code}
```

Requirements:
1. Apply SOLID principles
2. Use modern design patterns
3. Improve readability and maintainability
4. Reduce complexity
"""

        if target_language:
            prompt += f"5. Convert to {target_language} idioms\n"

        if patterns:
            prompt += f"6. Apply these patterns: {', '.join(patterns)}\n"

        prompt += """
Provide a detailed refactoring plan with:
- Description of changes
- Step-by-step implementation
- Risk assessment
- Example code snippets"""

        return prompt

    def generate_documentation(
        self,
        code: str,
        style: str = "technical",
        include_business_context: bool = True,
    ) -> DocumentationOutput:
        """Generate documentation for code.

        Args:
            code: Source code
            style: Documentation style
            include_business_context: Include business context

        Returns:
            Generated documentation
        """
        prompt = self._build_documentation_prompt(code, style, include_business_context)
        response = self._query_ai(prompt, AnalysisType.DOCUMENT)
        return self._parse_documentation_response(response)

    def _build_documentation_prompt(
        self,
        code: str,
        style: str,
        include_business_context: bool,
    ) -> str:
        """Build prompt for documentation generation.

        Args:
            code: Source code
            style: Documentation style
            include_business_context: Include business context

        Returns:
            Formatted prompt
        """
        prompt = f"""Generate {style} documentation for this code:
```
{code}
```

Include:
1. Summary of functionality
2. Purpose and use cases
3. Parameter descriptions
4. Return value explanation
5. Usage examples
6. Important notes or warnings
"""

        if include_business_context:
            prompt += "7. Business context and rules\n"

        prompt += "\nFormat as structured documentation suitable for developers."

        return prompt

    def suggest_tests(
        self,
        code: str,
        framework: str = "pytest",
        coverage_level: str = "comprehensive",
    ) -> List[TestSuggestion]:
        """Suggest test cases for code.

        Args:
            code: Source code
            framework: Test framework
            coverage_level: Desired coverage level

        Returns:
            List of test suggestions
        """
        prompt = self._build_test_prompt(code, framework, coverage_level)
        response = self._query_ai(prompt, AnalysisType.TEST)
        return self._parse_test_response(response)

    def _build_test_prompt(
        self,
        code: str,
        framework: str,
        coverage_level: str,
    ) -> str:
        """Build prompt for test suggestions.

        Args:
            code: Source code
            framework: Test framework
            coverage_level: Coverage level

        Returns:
            Formatted prompt
        """
        prompt = f"""Generate {coverage_level} test cases for this code using {framework}:
```
{code}
```

Provide:
1. Unit tests for each function
2. Edge case tests
3. Error handling tests
4. Integration tests if applicable
5. Performance tests if relevant

For each test:
- Test name and description
- Complete test code
- Expected behavior
- Edge cases to consider"""

        return prompt

    def modernize_code(
        self,
        code: str,
        source_language: str,
        target_language: str,
        preserve_logic: bool = True,
    ) -> Dict[str, Any]:
        """Modernize legacy code to modern equivalent.

        Args:
            code: Legacy source code
            source_language: Source language
            target_language: Target language
            preserve_logic: Preserve exact business logic

        Returns:
            Modernized code and metadata
        """
        prompt = self._build_modernization_prompt(
            code, source_language, target_language, preserve_logic
        )
        response = self._query_ai(prompt, AnalysisType.MODERNIZE)
        return self._parse_modernization_response(response)

    def _build_modernization_prompt(
        self,
        code: str,
        source_language: str,
        target_language: str,
        preserve_logic: bool,
    ) -> str:
        """Build prompt for code modernization.

        Args:
            code: Source code
            source_language: Source language
            target_language: Target language
            preserve_logic: Preserve business logic

        Returns:
            Formatted prompt
        """
        prompt = f"""Modernize this {source_language} code to {target_language}:
```{source_language}
{code}
```

Requirements:
1. Use modern {target_language} idioms and best practices
2. Apply appropriate design patterns
3. Add proper error handling
4. Include type hints/annotations
5. Follow {target_language} naming conventions
"""

        if preserve_logic:
            prompt += "6. Preserve exact business logic and behavior\n"
        else:
            prompt += "6. Improve logic where possible while maintaining intent\n"

        prompt += """
Provide:
- Complete modernized code
- Explanation of changes
- Any assumptions made
- Migration notes"""

        return prompt

    def analyze_security(
        self,
        code: str,
        language: str = "powerbuilder",
    ) -> Dict[str, Any]:
        """Analyze code for security issues.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Security analysis results
        """
        prompt = f"""Analyze this {language} code for security vulnerabilities:
```{language}
{code}
```

Check for:
1. SQL injection risks
2. Input validation issues
3. Authentication/authorization problems
4. Data exposure risks
5. Cryptographic weaknesses
6. Resource management issues

Provide:
- List of vulnerabilities found
- Severity level for each
- Remediation suggestions
- Secure code examples"""

        response = self._query_ai(prompt, AnalysisType.SECURITY)
        return self._parse_security_response(response)

    def _query_ai(self, prompt: str, analysis_type: AnalysisType) -> str:
        """Query AI model with prompt.

        Args:
            prompt: Input prompt
            analysis_type: Type of analysis

        Returns:
            AI response
        """
        if self.provider == AIProvider.OPENAI:
            return self._query_openai(prompt)
        elif self.provider == AIProvider.HUGGINGFACE:
            return self._query_huggingface(prompt)
        elif self.provider == AIProvider.LOCAL:
            return self._query_local(prompt)
        else:
            # Fallback to rule-based analysis
            return self._fallback_analysis(prompt, analysis_type)

    def _query_openai(self, prompt: str) -> str:
        """Query OpenAI API.

        Args:
            prompt: Input prompt

        Returns:
            Response text
        """
        if not OPENAI_AVAILABLE:
            return self._fallback_analysis(prompt, AnalysisType.UNDERSTAND)

        try:
            response = openai.ChatCompletion.create(
                model=self.model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a code analysis expert."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI query failed: %s", e)
            return self._fallback_analysis(prompt, AnalysisType.UNDERSTAND)

    def _query_huggingface(self, prompt: str) -> str:
        """Query HuggingFace model.

        Args:
            prompt: Input prompt

        Returns:
            Response text
        """
        if not TRANSFORMERS_AVAILABLE:
            return self._fallback_analysis(prompt, AnalysisType.UNDERSTAND)

        try:
            outputs = self.pipeline(
                prompt,
                max_length=1000,
                num_return_sequences=1,
                temperature=0.3,
            )
            return outputs[0]["generated_text"]
        except Exception as e:
            logger.error("HuggingFace query failed: %s", e)
            return self._fallback_analysis(prompt, AnalysisType.UNDERSTAND)

    def _query_local(self, prompt: str) -> str:
        """Query local model or service.

        Args:
            prompt: Input prompt

        Returns:
            Response text
        """
        # This would integrate with local LLM servers like Ollama, llama.cpp, etc.
        return self._fallback_analysis(prompt, AnalysisType.UNDERSTAND)

    def _fallback_analysis(self, prompt: str, analysis_type: AnalysisType) -> str:
        """Fallback rule-based analysis when AI is unavailable.

        Args:
            prompt: Input prompt
            analysis_type: Type of analysis

        Returns:
            Analysis result
        """
        # Extract code from prompt
        code_match = re.search(r"```[\w]*\n(.*?)```", prompt, re.DOTALL)
        code = code_match.group(1) if code_match else prompt

        if analysis_type == AnalysisType.UNDERSTAND:
            return self._rule_based_understanding(code)
        elif analysis_type == AnalysisType.REFACTOR:
            return self._rule_based_refactoring(code)
        elif analysis_type == AnalysisType.DOCUMENT:
            return self._rule_based_documentation(code)
        else:
            return "AI analysis unavailable. Using rule-based fallback."

    def _rule_based_understanding(self, code: str) -> str:
        """Rule-based code understanding.

        Args:
            code: Source code

        Returns:
            Understanding analysis
        """
        # Simple pattern matching for code understanding
        patterns = {
            "database": r"SELECT|INSERT|UPDATE|DELETE|FROM|WHERE",
            "file_io": r"open|read|write|close|file",
            "network": r"http|socket|connect|send|receive",
            "ui": r"window|button|label|text|display",
        }

        detected = []
        for name, pattern in patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                detected.append(name)

        return json.dumps(
            {
                "intent": "Code performs " + ", ".join(detected) + " operations",
                "patterns_detected": detected,
                "complexity": "medium" if len(detected) > 2 else "low",
                "suggestions": ["Consider modularization", "Add error handling"],
            }
        )

    def _rule_based_refactoring(self, code: str) -> str:
        """Rule-based refactoring suggestions.

        Args:
            code: Source code

        Returns:
            Refactoring suggestions
        """
        suggestions = []

        # Check for long methods
        lines = code.split("\n")
        if len(lines) > 30:
            suggestions.append("Break down long methods into smaller functions")

        # Check for nested loops
        if code.count("for ") > 1 or code.count("while ") > 1:
            suggestions.append("Reduce nesting depth")

        # Check for magic numbers
        if re.search(r"\b\d{2,}\b", code):
            suggestions.append("Replace magic numbers with named constants")

        return json.dumps(
            {
                "suggestions": suggestions,
                "risk_level": "low",
            }
        )

    def _rule_based_documentation(self, code: str) -> str:
        """Rule-based documentation generation.

        Args:
            code: Source code

        Returns:
            Documentation
        """
        # Extract function signatures
        functions = re.findall(r"(function|def|public)\s+(\w+)\s*\([^)]*\)", code)

        return json.dumps(
            {
                "summary": "Code analysis results",
                "functions": [f[1] for f in functions],
                "purpose": "Extracted from code patterns",
            }
        )

    def _parse_understanding_response(self, response: str) -> CodeUnderstanding:
        """Parse AI response for code understanding.

        Args:
            response: AI response

        Returns:
            Parsed understanding
        """
        try:
            # Try to parse as JSON first
            data = json.loads(response)
            return CodeUnderstanding(
                intent=data.get("intent", ""),
                business_logic=data.get("business_logic", []),
                dependencies=data.get("dependencies", []),
                patterns_detected=data.get("patterns_detected", []),
                complexity_assessment=data.get("complexity", "medium"),
                modernization_suggestions=data.get("suggestions", []),
                confidence_score=data.get("confidence", 0.7),
            )
        except:
            # Fallback to text parsing
            return CodeUnderstanding(
                intent=response[:200],
                business_logic=[],
                dependencies=[],
                patterns_detected=[],
                complexity_assessment="unknown",
                modernization_suggestions=[],
                confidence_score=0.5,
            )

    def _parse_refactoring_response(self, response: str) -> RefactoringPlan:
        """Parse AI response for refactoring plan.

        Args:
            response: AI response

        Returns:
            Parsed refactoring plan
        """
        try:
            data = json.loads(response)
            return RefactoringPlan(
                description=data.get("description", ""),
                steps=data.get("steps", []),
                estimated_impact=data.get("impact", "medium"),
                risk_level=data.get("risk_level", "low"),
                modern_patterns=data.get("patterns", []),
                code_snippets=data.get("snippets", {}),
            )
        except:
            return RefactoringPlan(
                description="Refactoring suggested",
                steps=response.split("\n")[:5],
                estimated_impact="medium",
                risk_level="low",
                modern_patterns=[],
            )

    def _parse_documentation_response(self, response: str) -> DocumentationOutput:
        """Parse AI response for documentation.

        Args:
            response: AI response

        Returns:
            Parsed documentation
        """
        try:
            data = json.loads(response)
            return DocumentationOutput(
                summary=data.get("summary", ""),
                purpose=data.get("purpose", ""),
                parameters=data.get("parameters", []),
                returns=data.get("returns"),
                examples=data.get("examples", []),
                notes=data.get("notes", []),
                business_context=data.get("business_context"),
            )
        except:
            return DocumentationOutput(
                summary=response[:200],
                purpose="Extracted from code",
                parameters=[],
                returns=None,
                examples=[],
                notes=[],
            )

    def _parse_test_response(self, response: str) -> List[TestSuggestion]:
        """Parse AI response for test suggestions.

        Args:
            response: AI response

        Returns:
            List of test suggestions
        """
        suggestions = []

        try:
            data = json.loads(response)
            if isinstance(data, list):
                for test in data:
                    suggestions.append(
                        TestSuggestion(
                            test_name=test.get("name", "test_unknown"),
                            test_type=test.get("type", "unit"),
                            description=test.get("description", ""),
                            test_code=test.get("code", ""),
                            edge_cases=test.get("edge_cases", []),
                            expected_behavior=test.get("expected", ""),
                        )
                    )
        except:
            # Create basic test suggestion
            suggestions.append(
                TestSuggestion(
                    test_name="test_basic",
                    test_type="unit",
                    description="Basic functionality test",
                    test_code="# TODO: Implement test",
                    edge_cases=[],
                    expected_behavior="Function should work correctly",
                )
            )

        return suggestions

    def _parse_modernization_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for modernization.

        Args:
            response: AI response

        Returns:
            Modernization results
        """
        try:
            return json.loads(response)
        except:
            return {
                "modern_code": response,
                "changes": [],
                "notes": [],
            }

    def _parse_security_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for security analysis.

        Args:
            response: AI response

        Returns:
            Security analysis results
        """
        try:
            return json.loads(response)
        except:
            return {
                "vulnerabilities": [],
                "severity": "low",
                "recommendations": [],
            }
