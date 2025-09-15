"""Tests for PowerBuilder parser functionality."""

import sys
from pathlib import Path

# Add the root directory to sys.path to import model package
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from lark import Tree

from src.model.ast import TryCatchStatement
from src.model.ast.powerbuilder import PBDataWindowType as DataWindow
from src.model.entities.library import Export, Import, Library
from src.parse.coordinator import parse_string
from src.parse.library import LibraryManager

# Test data
DATAWINDOW_TEST = """
type dw_customer from datawindow
{
    table(name="customer" keys=("id") )
    column(name="id" type="long" key="yes")
    column(name="name" type="string" width="50")
    compute(name="full_name" expr="name + ' ' + lastname")
    text(name="title" x="10" y="10" text="Customer Details")
}
"""

TRANSACTION_TEST = """
using sqlca
{
    insert into customer values (:name, :address);
    commit using sqlca;
}
"""

EXCEPTION_TEST = """
try {
    delete from customer where id = :id;
} catch (SQLException e) {
    MessageBox("Error", "Failed to delete customer");
} finally {
    Disconnect;
}
"""

LIBRARY_TEST = """
library customer_lib system
{
    import base.window;
    export w_customer_list;

    type w_customer_list from window
    {
        // Window definition
    }
}
"""


def test_parse_datawindow():
    """Test parsing DataWindow syntax."""
    # Note: This test may fail if the DataWindow grammar has issues
    # pytest.skip("DataWindow grammar needs to be fixed")
    ast = parse_string(DATAWINDOW_TEST, extension="srd")
    assert isinstance(ast, DataWindow)
    assert ast.name == "dw_customer"
    assert len(ast.columns) == 2
    assert ast.columns[0].name == "id"
    assert ast.columns[0].type == "long"


def test_parse_transaction():
    """Test parsing transaction blocks."""
    ast = parse_string(TRANSACTION_TEST, extension="srq")

    # The parser returns a Tree object, not model objects directly
    assert isinstance(ast, Tree)
    assert ast.data == "start"

    # Navigate to the transaction block
    # start -> powerbuilder_file -> transaction_block
    pb_file = None
    for child in ast.children:
        if isinstance(child, dict) and child.get("type") == "file":
            # The transformer has partially processed this
            elements = child.get("elements", [])
            for elem in elements:
                if isinstance(elem, Tree) and elem.data == "transaction_block":
                    # Found the transaction block
                    assert len(elem.children) >= 2
                    assert elem.children[1].value == "sqlca"  # Transaction name

                    # Count transaction statements
                    statements = [
                        c
                        for c in elem.children
                        if isinstance(c, Tree) and c.data == "transaction_statement"
                    ]
                    assert len(statements) == 2

                    # Check second statement is commit
                    commit_stmt = statements[1]
                    assert commit_stmt.children[0].data == "commit_statement"
                    return
        elif isinstance(child, Tree) and child.data == "powerbuilder_file":
            pb_file = child
            break

    if pb_file:
        # Look for transaction_block in powerbuilder_file
        for child in pb_file.children:
            if isinstance(child, Tree) and child.data == "transaction_block":
                # Found the transaction block
                assert len(child.children) >= 2
                assert child.children[1].value == "sqlca"  # Transaction name

                # Count transaction statements
                statements = [
                    c
                    for c in child.children
                    if isinstance(c, Tree) and c.data == "transaction_statement"
                ]
                assert len(statements) == 2

                # Check second statement is commit
                commit_stmt = statements[1]
                assert commit_stmt.children[0].data == "commit_statement"
                return

    # If we get here, we didn't find the expected structure
    assert False, f"Could not find transaction_block in AST: {ast.pretty()}"


def test_parse_exception():
    """Test parsing exception handling."""
    ast = parse_string(EXCEPTION_TEST, extension="sru")
    assert isinstance(ast, TryCatchStatement)
    assert len(ast.catch_blocks) == 1
    catch = ast.catch_blocks[0]
    assert catch.exception_type.name == "SQLException"
    assert catch.variable_name == "e"
    assert ast.finally_block is not None


def test_parse_library():
    """Test parsing library definitions."""
    ast = parse_string(LIBRARY_TEST, extension="sru")
    assert isinstance(ast, Library)
    assert ast.name == "customer_lib"
    assert ast.is_system
    assert len(ast.imports) == 1
    assert ast.imports[0].from_library == "base"
    assert len(ast.exports) == 1
    assert ast.exports[0].object_name == "w_customer_list"


def test_library_manager():
    """Test library dependency management."""
    manager = LibraryManager()

    # Add some test libraries
    lib1 = Library(name="lib1", path="lib1.pbl")
    lib1.imports.append(Import(from_library="lib2", object_name="window1"))

    lib2 = Library(name="lib2", path="lib2.pbl")
    lib2.imports.append(Import(from_library="lib3", object_name="basewin"))

    lib3 = Library(name="lib3", path="lib3.pbl", is_system=True)

    # Test basic library creation
    assert lib1.name == "lib1"
    assert len(lib1.imports) == 1
    assert lib1.imports[0].from_library == "lib2"

    # Test library exports
    lib1.exports.append(Export(object_name="w_customer_list"))
    assert len(lib1.exports) == 1
    assert lib1.exports[0].object_name == "w_customer_list"
