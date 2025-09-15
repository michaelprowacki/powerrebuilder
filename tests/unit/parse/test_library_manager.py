"""Unit tests for LibraryManager functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from src.parse.library import LibraryManager, SymbolCache, SymbolInfo


class TestSymbolCache:
    """Test the SymbolCache functionality."""

    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        cache = SymbolCache(max_size=3)

        # Test empty cache
        assert cache.get("test") is None

        # Test put and get
        symbol = SymbolInfo("test", Path("/test"), "window", {})
        cache.put("test", symbol)
        assert cache.get("test") == symbol

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = SymbolCache(max_size=3)

        # Fill cache
        symbols = []
        for i in range(3):
            symbol = SymbolInfo(f"test{i}", Path(f"/test{i}"), "window", {})
            symbols.append(symbol)
            cache.put(f"test{i}", symbol)

        # Access test0 to make it recently used
        cache.get("test0")

        # Add new item - should evict test1 (least recently used)
        new_symbol = SymbolInfo("test3", Path("/test3"), "window", {})
        cache.put("test3", new_symbol)

        # test1 should be evicted
        assert cache.get("test1") is None
        assert cache.get("test0") is not None
        assert cache.get("test2") is not None
        assert cache.get("test3") is not None

    def test_cache_clear(self):
        """Test cache clearing."""
        cache = SymbolCache()

        # Add items
        for i in range(5):
            symbol = SymbolInfo(f"test{i}", Path(f"/test{i}"), "window", {})
            cache.put(f"test{i}", symbol)

        # Clear cache
        cache.clear()

        # All items should be gone
        for i in range(5):
            assert cache.get(f"test{i}") is None


class TestLibraryManager:
    """Test the LibraryManager functionality."""

    def test_initialization(self):
        """Test LibraryManager initialization."""
        paths = [Path("/lib1"), Path("/lib2")]
        manager = LibraryManager(library_paths=paths, cache_size=500)

        assert manager.library_paths == paths
        assert len(manager.libraries) == 0
        assert len(manager.symbol_index) == 0

    def test_object_type_detection(self):
        """Test PowerBuilder object type detection."""
        manager = LibraryManager()

        test_cases = [
            # (name, extension, expected_type)
            ("n_cst_example", "", "userobject"),
            ("u_datawindow", "", "userobject"),
            ("w_main", "", "window"),
            ("d_employee", "", "datawindow"),
            ("m_popup", "", "menu"),
            ("f_calculate", "", "function"),
            ("q_report", "", "query"),
            ("s_person", "", "structure"),
            ("p_data_pipeline", "", "pipeline"),
            ("a_myapp", "", "application"),
            ("unknown_obj", "", "unknown"),
            ("test", ".srw", "window"),
            ("test", ".sru", "userobject"),
            ("test", ".srf", "function"),
            ("test", ".srm", "menu"),
            ("test", ".srs", "structure"),
            ("test", ".sra", "application"),
            ("test", ".srd", "datawindow"),
            ("test", ".dwo", "datawindow"),
        ]

        for name, ext, expected in test_cases:
            result = manager._detect_object_type(name, ext)
            assert result == expected, (
                f"Failed for {name}{ext}: got {result}, expected {expected}"
            )

    def test_add_and_get_symbol(self):
        """Test adding and retrieving symbols."""
        manager = LibraryManager()

        # Create mock AST
        mock_ast = {"type": "window", "name": "w_test"}

        # Add symbol
        manager.add_symbol("w_test", mock_ast, Path("/test.pbl"))

        # Retrieve symbol
        symbol = manager.get_symbol("w_test")
        assert symbol is not None
        assert symbol.name == "w_test"
        assert symbol.ast == mock_ast
        assert symbol.object_type == "window"
        assert symbol.library_path == Path("/test.pbl")

        # Test case insensitivity
        symbol_upper = manager.get_symbol("W_TEST")
        assert symbol_upper is not None
        assert symbol_upper.name == "w_test"

    def test_hierarchical_search(self):
        """Test hierarchical symbol search."""
        manager = LibraryManager()

        # Add same symbol in different libraries
        manager.add_symbol("w_base", {"version": 1}, Path("/lib1.pbl"))
        manager.add_symbol("w_base", {"version": 2}, Path("/lib2.pbl"))

        # Clear cache to ensure search order is respected
        manager.clear_cache()

        # Search with specific order
        symbol = manager.get_symbol("w_base", search_order=[Path("/lib2.pbl")])
        assert symbol.ast["version"] == 2

        # Clear cache again
        manager.clear_cache()

        # Search with different order
        symbol = manager.get_symbol("w_base", search_order=[Path("/lib1.pbl")])
        assert symbol.ast["version"] == 1

    def test_dependency_extraction(self):
        """Test dependency extraction from AST."""
        manager = LibraryManager()

        # Create a mock AST node with attributes
        from types import SimpleNamespace

        # Create AST with dependencies using objects with attributes
        ast = SimpleNamespace(
            type="window",
            name="w_child",
            ancestor="w_base",
            controls=[
                SimpleNamespace(type="userobject", type_name="u_custom"),
            ],
            functions=[
                SimpleNamespace(
                    name="test", calls=[SimpleNamespace(function_name="f_utility")]
                )
            ],
        )

        deps = manager._extract_dependencies(ast)
        assert "w_base" in deps
        assert "u_custom" in deps
        assert "f_utility" in deps

    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        manager = LibraryManager()

        # Create circular dependency
        manager.add_symbol("w_a", {"name": "w_a"})
        manager.add_symbol("w_b", {"name": "w_b"})
        manager.add_symbol("w_c", {"name": "w_c"})

        # Manually set up circular dependencies
        symbol_a = manager.get_symbol("w_a")
        symbol_b = manager.get_symbol("w_b")
        symbol_c = manager.get_symbol("w_c")

        symbol_a.dependencies.add("w_b")
        symbol_b.dependencies.add("w_c")
        symbol_c.dependencies.add("w_a")

        # Update dependency graph
        manager.dependency_graph["w_b"].add("w_a")
        manager.dependency_graph["w_c"].add("w_b")
        manager.dependency_graph["w_a"].add("w_c")

        # Check for cycle
        cycle = manager.check_circular_dependencies("w_a")
        assert cycle is not None
        assert len(cycle) == 4  # w_a -> w_b -> w_c -> w_a
        assert cycle[0] == cycle[-1]  # Starts and ends with same symbol

    def test_resolve_dependencies(self):
        """Test dependency resolution order."""
        manager = LibraryManager()

        # Create dependency chain: w_child -> w_parent -> w_grandparent
        manager.add_symbol("w_grandparent", {})
        manager.add_symbol("w_parent", {})
        manager.add_symbol("w_child", {})

        # Set up dependencies
        manager.get_symbol("w_parent").dependencies.add("w_grandparent")
        manager.get_symbol("w_child").dependencies.add("w_parent")

        # Resolve dependencies
        order = manager.resolve_dependencies("w_child")

        # Should be in dependency order
        assert order == ["w_grandparent", "w_parent", "w_child"]

    def test_get_dependents(self):
        """Test getting symbols that depend on a given symbol."""
        manager = LibraryManager()

        # Set up dependency graph
        manager.dependency_graph["w_base"] = {"w_child1", "w_child2"}
        manager.dependency_graph["u_custom"] = {"w_child1", "w_main"}

        # Get dependents
        base_dependents = manager.get_dependents("w_base")
        assert base_dependents == {"w_child1", "w_child2"}

        custom_dependents = manager.get_dependents("u_custom")
        assert custom_dependents == {"w_child1", "w_main"}

        # Non-existent symbol
        none_dependents = manager.get_dependents("nonexistent")
        assert none_dependents == set()

    def test_export_symbol_table(self):
        """Test symbol table export."""
        manager = LibraryManager()

        # Add some test data
        manager.add_symbol("w_test", {}, Path("/lib1.pbl"))
        manager.add_symbol("u_custom", {}, Path("/lib2.pbl"))

        # Export table
        table = manager.export_symbol_table()

        assert "libraries" in table
        assert "symbols" in table
        assert "dependencies" in table

        # Check libraries
        assert str(Path("/lib1.pbl")) in table["libraries"]
        assert str(Path("/lib2.pbl")) in table["libraries"]

        # Check symbols
        assert "w_test" in table["symbols"]
        assert table["symbols"]["w_test"]["type"] == "window"
        assert "u_custom" in table["symbols"]
        assert table["symbols"]["u_custom"]["type"] == "userobject"

    def test_unload_library(self):
        """Test library unloading."""
        manager = LibraryManager()

        # Add library with symbols
        lib_path = Path("/test.pbl")
        manager.add_symbol("w_test1", {}, lib_path)
        manager.add_symbol("w_test2", {}, lib_path)

        # Set up some dependencies
        manager.dependency_graph["w_base"] = {"w_test1"}
        manager.dependency_graph["w_test1"] = {"w_test2"}

        # Verify symbols exist
        assert manager.get_symbol("w_test1") is not None
        assert manager.get_symbol("w_test2") is not None

        # Unload library
        manager.unload_library(lib_path)

        # Verify symbols removed
        assert "w_test1" not in manager.symbol_index
        assert "w_test2" not in manager.symbol_index
        assert "w_test1" not in manager.dependency_graph
        assert "w_test1" not in manager.dependency_graph["w_base"]

    @patch("src.parse.library.extract_pbl")
    @patch("shutil.rmtree")
    def test_load_library_integration(self, mock_rmtree, mock_extract):
        """Test library loading with mocked extraction."""
        manager = LibraryManager()

        # Mock successful extraction
        mock_extract.return_value = None

        # Create mock parser
        mock_parser = MagicMock()
        mock_parser.EXTENSION_PARSERS = {"srw": Mock, "sru": Mock}
        mock_parser.parse.return_value = {"type": "window", "name": "w_test"}

        with patch.object(manager, "_get_parser", return_value=mock_parser):
            with patch("pathlib.Path.iterdir") as mock_iterdir:
                # Mock extracted files
                mock_file1 = MagicMock()
                mock_file1.is_file.return_value = True
                mock_file1.suffix = ".srw"
                mock_file1.stem = "w_test"

                mock_iterdir.return_value = [mock_file1]

                # Load library
                lib_path = Path("/test.pbl")
                lib_info = manager.load_library(lib_path)

                # Verify
                assert lib_info.path == lib_path
                assert "w_test" in lib_info.objects
                assert mock_extract.called
                assert mock_rmtree.called

    def test_library_auto_loading(self):
        """Test automatic library loading from configured paths."""
        with patch.object(LibraryManager, "load_library") as mock_load:
            # Create temp directory with mock library files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Create mock library files
                lib1 = temp_path / "lib1.pbl"
                lib2 = temp_path / "subdir" / "lib2.pbd"
                lib1.touch()
                lib2.parent.mkdir()
                lib2.touch()

                # Initialize manager with path
                manager = LibraryManager(library_paths=[temp_path])

                # Verify load_library was called for both files
                assert mock_load.call_count == 2
                called_paths = [call[0][0] for call in mock_load.call_args_list]
                assert lib1 in called_paths
                assert lib2 in called_paths
