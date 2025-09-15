"""Test PowerBuilder event parsing."""

from src.model.base.pb_behavioral import PBEvent, PBTrigger
from src.parse.parser.specialized.transactions import TransactionParser


def test_simple_event():
    """Test parsing of simple event declaration."""
    code = """
    event void clicked();
    // Event handler code
    end event
    """
    parser = TransactionParser()
    result = parser.parse_event(code)
    assert isinstance(result, PBEvent)
    assert result.name == "clicked"
    assert result.event_type.name == "void"
    assert len(result.parameters) == 0


def test_event_with_parameters():
    """Test parsing of event with parameters."""
    code = """
    event integer itemchanged(integer row, string column);
    // Event handler code
    return 1
    end event
    """
    parser = TransactionParser()
    result = parser.parse_event(code)
    assert isinstance(result, PBEvent)
    assert result.name == "itemchanged"
    assert result.event_type.name == "integer"
    assert len(result.parameters) == 2
    assert result.parameters[0].name == "row"
    assert result.parameters[0].pb_type.name == "integer"
    assert result.parameters[1].name == "column"
    assert result.parameters[1].pb_type.name == "string"


def test_trigger_definition():
    """Test parsing of trigger definition."""
    code = """
    on clicked;
    // Trigger code
    end on
    """
    parser = TransactionParser()
    result = parser.parse_trigger(code)
    assert isinstance(result, PBTrigger)
    assert result.event_name == "clicked"
    assert result.object_name is None


def test_object_trigger():
    """Test parsing of object-specific trigger."""
    code = """
    on cb_save.clicked;
    // Trigger code
    end on
    """
    parser = TransactionParser()
    result = parser.parse_trigger(code)
    assert isinstance(result, PBTrigger)
    assert result.event_name == "clicked"
    assert result.object_name == "cb_save"


def test_event_with_custom_type():
    """Test parsing of event with custom type."""
    code = """
    event window.response ue_response();
    // Event handler code
    end event
    """
    parser = TransactionParser()
    result = parser.parse_event(code)
    assert isinstance(result, PBEvent)
    assert result.name == "ue_response"
    assert result.event_type.name == "response"
    assert result.event_type.namespace == "window"


def test_event_with_super_call():
    """Test parsing of event with super call."""
    code = """
    event integer ue_save();
    call super::ue_save;
    // Additional code
    return 1
    end event
    """
    parser = TransactionParser()
    result = parser.parse_event(code)
    assert isinstance(result, PBEvent)
    assert result.name == "ue_save"
    assert result.has_super_call is True


def test_event_attribute():
    """Test parsing of event attribute."""
    code = """event integer itemchanged"""
    parser = TransactionParser()
    result = parser.parse_event_attribute(code)
    assert isinstance(result, PBEvent)
    assert result.name == "itemchanged"
    assert result.event_type.name == "integer"


def test_event_reference():
    """Test parsing of event reference name."""
    code = """dw_1::itemchanged"""
    parser = TransactionParser()
    result = parser.parse_event_reference(code)
    assert result.object_name == "dw_1"
    assert result.event_name == "itemchanged"
