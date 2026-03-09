"""Model stage coordinator for PowerRebuilder pipeline.

This coordinator orchestrates the model stage, which transforms ASTs into semantic models.
It coordinates the various services in src/model/services/ to process AST files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from src.core.coordination_base import CoordinationBase
from src.model.services.ast_processor import ASTProcessor
from src.model.services.model_extractor import ModelExtractor
from src.model.services.entity_factory import EntityFactory
from src.model.services.entity_validator import EntityValidator
from src.model.services.model_persistence import ModelPersistence
from src.model.services.relationship_manager import RelationshipManager

logger = logging.getLogger(__name__)


class ModelCoordinator(CoordinationBase):
    """Coordinator for the Model stage of the pipeline.

    Transforms Abstract Syntax Trees (ASTs) from the Parse stage into
    semantic models with resolved types and dependencies.
    """

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the Model coordinator.

        Args:
            input_path: Directory containing AST JSON files from Parse stage
            output_path: Directory to write semantic model files
            config: Optional configuration dictionary
        """
        super().__init__(config or {})
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)

        # Initialize services
        self.ast_processor = ASTProcessor()
        self.model_extractor = ModelExtractor()
        self.entity_factory = EntityFactory()
        self.entity_validator = EntityValidator()
        self.model_persistence = ModelPersistence()
        self.relationship_manager = RelationshipManager()

        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized ModelCoordinator: {input_path} -> {output_path}")

    def process(self) -> Dict[str, Any]:
        """Process AST files to generate semantic models.

        Returns:
            Dictionary containing processing results and statistics
        """
        try:
            logger.info("Starting Model stage processing")

            # Discover AST files
            ast_files = self._discover_ast_files()
            if not ast_files:
                logger.warning("No AST files found to process")
                return {
                    "status": "completed",
                    "files_processed": 0,
                    "models_created": 0,
                    "errors": [],
                }

            logger.info(f"Found {len(ast_files)} AST files to process")

            # Process each AST file
            results = {
                "status": "success",
                "files_processed": 0,
                "models_created": 0,
                "errors": [],
                "models": [],
            }

            for ast_file in ast_files:
                try:
                    model = self._process_single_file(ast_file)
                    if model:
                        results["models"].append(model)
                        results["models_created"] += 1
                    results["files_processed"] += 1
                except Exception as e:
                    logger.error(f"Error processing {ast_file}: {e}")
                    results["errors"].append({"file": str(ast_file), "error": str(e)})

            # Resolve cross-module references
            if results["models"]:
                self._resolve_dependencies(results["models"])

            logger.info(
                f"Model stage completed: {results['models_created']} models created"
            )
            return results

        except Exception as e:
            logger.error(f"Model stage failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "files_processed": 0,
                "models_created": 0,
            }

    def _discover_ast_files(self) -> List[Path]:
        """Discover AST JSON files in the input directory.

        Returns:
            List of paths to AST files
        """
        patterns = ["*.ast.json", "*.json"]
        ast_files = []

        for pattern in patterns:
            ast_files.extend(self.input_path.glob(pattern))

        # Remove duplicates and sort
        ast_files = sorted(set(ast_files))
        return ast_files

    def _process_single_file(self, ast_file: Path) -> Optional[Dict[str, Any]]:
        """Process a single AST file to create a semantic model.

        Args:
            ast_file: Path to the AST JSON file

        Returns:
            Semantic model dictionary or None if processing failed
        """
        try:
            logger.debug(f"Processing AST file: {ast_file}")

            # Load and validate AST
            with open(ast_file, "r", encoding="utf-8") as f:
                ast_data = json.load(f)

            # Process AST to extract model
            model = self.ast_processor.process(ast_data)

            if not model:
                logger.warning(f"No model extracted from {ast_file}")
                return None

            # Extract entities
            entities = self.model_extractor.extract(model)

            # Create and validate entities
            for entity in entities:
                created_entity = self.entity_factory.create(entity)
                if self.entity_validator.validate(created_entity):
                    model.setdefault("entities", []).append(created_entity)

            # Save model to output
            output_file = self.output_path / f"{ast_file.stem}.model.json"
            self.model_persistence.save(model, output_file)

            logger.debug(f"Created model: {output_file}")
            return model

        except Exception as e:
            logger.error(f"Failed to process {ast_file}: {e}")
            return None

    def _resolve_dependencies(self, models: List[Dict[str, Any]]) -> None:
        """Resolve cross-module dependencies between models.

        Args:
            models: List of semantic models to resolve
        """
        try:
            logger.debug("Resolving cross-module dependencies")

            # Build symbol table from all models
            for model in models:
                self.relationship_manager.register_model(model)

            # Resolve references
            self.relationship_manager.resolve_all()

            # Update models with resolved references
            for model in models:
                resolved = self.relationship_manager.get_resolved_model(model)
                if resolved:
                    # Update the saved model
                    model_file = model.get("_file_path")
                    if model_file:
                        self.model_persistence.save(resolved, Path(model_file))

            logger.debug("Dependency resolution completed")

        except Exception as e:
            logger.error(f"Error resolving dependencies: {e}")


# Factory function for backwards compatibility
def create_model_coordinator(
    input_path: str, output_path: str, config: Optional[Dict[str, Any]] = None
) -> ModelCoordinator:
    """Create a ModelCoordinator instance.

    Args:
        input_path: Input directory path
        output_path: Output directory path
        config: Optional configuration

    Returns:
        ModelCoordinator instance
    """
    return ModelCoordinator(Path(input_path), Path(output_path), config)
