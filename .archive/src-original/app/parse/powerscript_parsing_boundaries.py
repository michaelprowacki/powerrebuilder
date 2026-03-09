"""Parse Application - Ports.

Small, specific interfaces for the parse slice.
"""

from typing import Protocol
from src_new.domain.parse.shared import ASTNode


class ISourceReader(Protocol):
    """Port for reading source files."""

    async def read_source(self, path: str) -> str:
        """Read PowerBuilder source file.

        Args:
            path: Path to source file

        Returns:
            Source code text

        Raises:
            IOError: If file cannot be read
        """
        ...

    async def get_encoding(self, path: str) -> str:
        """Detect source file encoding.

        Args:
            path: Path to source file

        Returns:
            Encoding name (e.g., 'utf-8', 'cp1252')
        """
        ...


class IASTWriter(Protocol):
    """Port for writing AST."""

    async def write_ast(self, path: str, ast: ASTNode) -> None:
        """Write AST to storage.

        Args:
            path: Output path
            ast: AST to write

        Raises:
            IOError: If write fails
        """
        ...

    async def write_ast_json(self, path: str, ast_dict: dict) -> None:
        """Write AST as JSON.

        Args:
            path: Output path
            ast_dict: AST dictionary representation
        """
        ...
