"""Tests for library import resolution."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parse.coordinator import ParseCoordinator
from src.parse.library import Library, LibraryManager


class TestLibraryManager:
    """Test LibraryManager functionality."""

    @pytest.fixture
    def library_manager(self, tmp_path):
        """Create LibraryManager with test paths."""
        lib_path = tmp_path / "libraries"
        lib_path.mkdir()
        return LibraryManager([lib_path])

    def test_add_library_path(self, library_manager, tmp_path):
        """Test adding library search paths."""
        new_path = tmp_path / "new_libs"
        new_path.mkdir()

        library_manager.add_library_path(new_path)
        assert new_path in library_manager.library_paths

    def test_find_library_file(self, library_manager, tmp_path):
        """Test finding library files."""
        lib_path = tmp_path / "libraries"

        # Create test library files
        (lib_path / "test.pbl").touch()
        (lib_path / "utils.pbd").touch()

        # Test exact match
        found = library_manager._find_library_file("test")
        assert found is not None
        assert found.name == "test.pbl"

        # Test case-insensitive match
        found = library_manager._find_library_file("UTILS")
        assert found is not None
        assert found.name.lower() == "utils.pbd"

        # Test not found
        found = library_manager._find_library_file("nonexistent")
        assert found is None

    def test_cache_library_lookup(self, library_manager, tmp_path):
        """Test library file lookup caching."""
        lib_path = tmp_path / "libraries"
        (lib_path / "cached.pbl").touch()

        # First lookup
        found1 = library_manager._find_library_file("cached")
        assert found1 is not None

        # Second lookup should use cache
        found2 = library_manager._find_library_file("cached")
        assert found2 == found1
        assert len(library_manager._file_cache) == 1

    @patch("extract.pbd.extraction.library.Library")
    def test_extract_pb_exports(self, mock_library_class, library_manager):
        """Test extracting exports from PowerBuilder libraries."""
        # Mock the PBLibrary class
        mock_instance = MagicMock()
        mock_library_class.return_value = mock_instance
        mock_instance.extract_all.return_value = {
            "w_main": {"data": "window w_main..."},
            "dw_customer.dwo": {"data": "datawindow dw_customer..."},
            "n_business": {"data": "userobject n_business..."},
        }

        # Create library
        library = Library("test", Path("test.pbl"))
        library_manager._extract_pb_exports(library)

        # Check exports
        assert "w_main" in library.exports
        assert library.exports["w_main"]["type"] == "window"
        assert "dw_customer.dwo" in library.exports
        assert library.exports["dw_customer.dwo"]["type"] == "datawindow"
        assert "n_business" in library.exports
        assert library.exports["n_business"]["type"] == "userobject"

    def test_circular_dependencies(self, library_manager):
        """Test circular dependency detection."""
        # Create circular dependency: A -> B -> C -> A
        library_manager._import_graph = {
            "lib_a": {"lib_b"},
            "lib_b": {"lib_c"},
            "lib_c": {"lib_a"},
        }

        cycles = library_manager.check_circular_dependencies()
        assert len(cycles) == 1
        assert set(cycles[0]) == {"lib_a", "lib_b", "lib_c"}

    def test_dependency_order(self, library_manager):
        """Test topological sort of dependencies."""
        # Create dependency graph: A -> B, A -> C, B -> D, C -> D
        library_manager._import_graph = {
            "lib_a": {"lib_b", "lib_c"},
            "lib_b": {"lib_d"},
            "lib_c": {"lib_d"},
            "lib_d": set(),
        }

        order = library_manager.get_dependency_order()

        # D should come before B and C
        assert order.index("lib_d") < order.index("lib_b")
        assert order.index("lib_d") < order.index("lib_c")

        # B and C should come before A
        assert order.index("lib_b") < order.index("lib_a")
        assert order.index("lib_c") < order.index("lib_a")


class TestParseCoordinator:
    """Test ParseCoordinator with library resolution."""

    @pytest.fixture
    def coordinator(self, tmp_path):
        """Create ParseCoordinator with test setup."""
        return ParseCoordinator([tmp_path])

    def test_extract_imports(self, coordinator):
        """Test extracting imports from parsed tree."""
        # Create mock tree with import statements
        from lark import Token, Tree

        tree = Tree(
            "start",
            [
                Tree(
                    "import_statement",
                    [
                        Token("IMPORT", "import"),
                        Token("STRING", '"foundation.pbl"'),
                    ],
                ),
                Tree(
                    "import_statement",
                    [
                        Token("IMPORT", "import"),
                        Tree("library_name", [Token("IDENTIFIER", "utils")]),
                    ],
                ),
            ],
        )

        imports = coordinator._extract_imports(tree)
        assert "foundation.pbl" in imports
        assert "utils" in imports

    @patch("parse.parse_coordinator.parse_file")
    def test_parse_with_imports(self, mock_parse_file, coordinator, tmp_path):
        """Test parsing with import resolution."""
        # Mock parse result
        from lark import Tree

        mock_tree = Tree("start", [])
        mock_parse_file.return_value = mock_tree

        # Mock library resolution
        mock_library = Library("test_lib", Path("test.pbl"))
        mock_library.add_export(
            "global_function",
            {
                "type": "function",
                "return_type": "integer",
            },
        )

        with patch.object(
            coordinator.library_manager, "resolve_import", return_value=mock_library
        ):
            # Parse file
            test_file = tmp_path / "test.sru"
            test_file.touch()

            result = coordinator.parse_with_imports(test_file)

            # Check caching
            assert test_file in coordinator.parsed_files
            assert test_file in coordinator.transformers

    def test_symbol_resolution(self, coordinator):
        """Test symbol resolution from libraries."""
        # Add mock library with symbols
        mock_library = Library("utils", Path("utils.pbl"))
        mock_library.add_export("f_calculate", {"type": "function"})
        mock_library.add_export("n_business", {"type": "userobject"})

        coordinator.library_manager._cache["utils"] = mock_library

        # Test symbol lookup
        symbol = coordinator.get_symbol("f_calculate")
        assert symbol is not None

        symbol = coordinator.get_symbol("unknown_symbol")
        assert symbol is None
