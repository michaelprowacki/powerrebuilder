"""Tests for interactive module."""

import os
import tempfile
from typing import Any
from unittest.mock import patch

import pytest

from src.parse.interactive import REPL, Command, CommandType, REPLState


@pytest.fixture
def temp_history_file() -> str:
    """Create temporary history file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)


def test_command_type():
    """Test command type enumeration."""
    assert CommandType.HELP.value < CommandType.DEBUG.value
    assert CommandType.DEBUG.value < CommandType.HISTORY.value
    assert CommandType.HISTORY.value < CommandType.CLEAR.value
    assert CommandType.CLEAR.value < CommandType.SAVE.value
    assert CommandType.SAVE.value < CommandType.LOAD.value
    assert CommandType.LOAD.value < CommandType.QUIT.value
    assert CommandType.QUIT.value < CommandType.EXEC.value


def test_command():
    """Test command class."""

    def handler(repl, args) -> None:
        return None

    cmd = Command(
        type=CommandType.HELP,
        name="help",
        help="Test help",
        handler=handler,
    )

    assert cmd.type == CommandType.HELP
    assert cmd.name == "help"
    assert cmd.help == "Test help"
    assert cmd.handler == handler


def test_repl_state(temp_history_file):
    """Test REPL state functionality."""
    state = REPLState(history_file=temp_history_file)

    # Test initial state
    assert not state.history
    assert not state.variables
    assert state.start_time is not None
    assert not state.multiline_buffer
    assert not state.in_multiline

    # Test history management
    state.add_to_history("test command")
    assert state.history == ["test command"]
    state.clear_history()
    assert not state.history

    # Test variable management
    state.update_variable("x", 42)
    assert state.get_variable("x") == 42
    assert state.get_variable("y") is None
    state.clear_variables()
    assert not state.variables


@patch("builtins.input")
@patch("builtins.print")
def test_repl_basic(mock_print: Any, mock_input: Any) -> None:
    """Test basic REPL functionality."""
    mock_input.side_effect = ["x = 42", ":help", ":quit"]
    repl = REPL()

    # Test command creation
    assert "help" in repl.commands
    assert "debug" in repl.commands
    assert "history" in repl.commands
    assert "clear" in repl.commands
    assert "save" in repl.commands
    assert "load" in repl.commands
    assert "quit" in repl.commands

    # Run REPL
    repl.run()

    # Verify welcome message
    mock_print.assert_any_call("PowerBuilder/Pseudocode Interactive Console")
    mock_print.assert_any_call("Type :help for commands, Ctrl+D to exit")


@patch("builtins.input")
@patch("builtins.print")
def test_repl_multiline(mock_print: Any, mock_input: Any) -> None:
    """Test multiline input handling."""
    mock_input.side_effect = [
        "def test():",
        "    x = 42",
        "    return x",
        "",  # Empty line to end multiline
        ":quit",
    ]
    repl = REPL()

    # Run REPL
    repl.run()

    # Verify multiline handling
    assert not repl.state.in_multiline
    assert not repl.state.multiline_buffer


@patch("builtins.input")
@patch("builtins.print")
def test_repl_commands(mock_print: Any, mock_input: Any) -> None:
    """Test REPL command handling."""
    mock_input.side_effect = [
        ":help",
        ":debug",
        ":debug verbose",
        ":history",
        ":history clear",
        ":clear",
        ":quit",
    ]
    repl = REPL()

    # Run REPL
    repl.run()

    # Verify command handling
    mock_print.assert_any_call("Available commands:")
    mock_print.assert_any_call("Debugging enabled (basic level)")
    mock_print.assert_any_call("Debugging enabled (verbose level)")
    mock_print.assert_any_call("History cleared")


@patch("builtins.input")
@patch("builtins.print")
def test_repl_variable_persistence(
    mock_print: Any,
    mock_input: Any,
    temp_history_file: str,
) -> None:
    """Test variable save/load functionality."""
    # Create temporary file for variables
    with tempfile.NamedTemporaryFile(delete=False) as f:
        var_file = f.name

    mock_input.side_effect = [
        "x = 42",
        f":save {var_file}",
        ":clear",
        f":load {var_file}",
        ":quit",
    ]
    repl = REPL()
    repl.state.history_file = temp_history_file

    # Run REPL
    repl.run()

    # Verify variable persistence
    assert repl.state.get_variable("x") == 42

    # Clean up
    os.unlink(var_file)


@patch("builtins.input")
@patch("builtins.print")
def test_repl_error_handling(mock_print: Any, mock_input: Any) -> None:
    """Test error handling in REPL."""
    mock_input.side_effect = [
        "1/0",  # ZeroDivisionError
        ":debug",  # Enable debugging
        "1/0",  # Error with debugging
        ":quit",
    ]
    repl = REPL()

    # Run REPL
    repl.run()

    # Verify error handling
    mock_print.assert_any_call("Error: division by zero")


@patch("builtins.input")
@patch("builtins.print")
def test_repl_keyboard_interrupt(mock_print: Any, mock_input: Any) -> None:
    """Test keyboard interrupt handling."""
    mock_input.side_effect = KeyboardInterrupt
    repl = REPL()

    # Run REPL
    repl.run()

    # Verify interrupt handling
    mock_print.assert_any_call("\nKeyboardInterrupt")
