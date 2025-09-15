"""Tests for debug module."""

from src.parse.debug import (
    Debugger,
    DebugLevel,
    DebugOutput,
    DebugState,
)


def test_debug_level():
    """Test debug level enumeration."""
    assert DebugLevel.NONE.value < DebugLevel.BASIC.value
    assert DebugLevel.BASIC.value < DebugLevel.DETAILED.value
    assert DebugLevel.DETAILED.value < DebugLevel.VERBOSE.value


def test_debug_state():
    """Test debug state functionality."""
    state = DebugState()

    # Test initial state
    assert not state.enabled
    assert state.level == DebugLevel.NONE
    assert not state.step_mode
    assert state.break_on_error
    assert state.start_time is not None

    # Test breakpoint management
    state.add_breakpoint("test.py", 10)
    assert "test.py:10" in state.breakpoints
    state.remove_breakpoint("test.py", 10)
    assert "test.py:10" not in state.breakpoints

    # Test call stack management
    state.push_call("test_func")
    assert state.call_stack == ["test_func"]
    assert state.pop_call() == "test_func"
    assert not state.call_stack

    # Test variable management
    state.update_variable("x", 42)
    assert state.get_variable("x") == 42
    assert state.get_variable("y") is None

    # Test clear
    state.clear()
    assert not state.call_stack
    assert not state.variables


def test_debug_output(caplog):
    """Test debug output formatting."""
    state = DebugState()
    output = DebugOutput(state)

    # Test disabled output
    output.output("test")
    assert not caplog.records

    # Test enabled output
    state.enabled = True
    output.output("test")
    assert "test" in caplog.text

    # Test indentation
    state.output_indent = 2
    output.output("indented")
    assert "  indented" in caplog.text

    # Test variable output
    state.update_variable("x", 42)
    output.output_variables()
    assert "x = 42" in caplog.text

    # Test call stack output
    state.push_call("func1")
    state.push_call("func2")
    output.output_call_stack()
    assert "Call stack:" in caplog.text
    assert "func2" in caplog.text
    assert "func1" in caplog.text


def test_debugger():
    """Test debugger functionality."""
    debugger = Debugger()

    # Test enable/disable
    debugger.enable(DebugLevel.BASIC)
    assert debugger.state.enabled
    assert debugger.state.level == DebugLevel.BASIC

    debugger.disable()
    assert not debugger.state.enabled
    assert debugger.state.level == DebugLevel.NONE

    # Test step tracking
    debugger.enable()
    debugger.step("test.py", 10)
    assert debugger.state.current_file == "test.py"
    assert debugger.state.current_line == 10

    # Test function tracking
    debugger.enter_function("test_func")
    assert debugger.state.call_stack == ["test_func"]
    assert debugger.state.output_indent == 2

    debugger.exit_function()
    assert not debugger.state.call_stack
    assert debugger.state.output_indent == 0

    # Test error handling
    error = ValueError("test error")
    debugger.handle_error(error)
    assert "Error: test error" in debugger.output.logger.messages


def test_debug_state_should_break():
    """Test break condition evaluation."""
    state = DebugState()
    state.enabled = True

    # Test step mode
    state.step_mode = True
    assert state.should_break()

    # Test breakpoint
    state.step_mode = False
    state.current_file = "test.py"
    state.current_line = 10
    state.add_breakpoint("test.py", 10)
    assert state.should_break()

    # Test no break condition
    state.remove_breakpoint("test.py", 10)
    assert not state.should_break()

    # Test disabled
    state.enabled = False
    state.step_mode = True
    assert not state.should_break()


def test_debug_output_format_value():
    """Test value formatting for output."""
    state = DebugState()
    output = DebugOutput(state)

    # Test simple values
    assert output._format_value(42) == "42"
    assert output._format_value("test") == '"test"'
    assert output._format_value([1, 2, 3]) == "[1, 2, 3]"

    # Test complex values
    class TestClass:
        def __str__(self) -> str:
            return "TestClass()"

    obj = TestClass()
    assert output._format_value(obj) == "TestClass()"
