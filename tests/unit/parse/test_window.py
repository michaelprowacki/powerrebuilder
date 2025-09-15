"""Tests for window parsing."""

import pytest

from src.model.window import Window
from src.parse.coordinator import parse_text
from src.parse.transformer import PBTransformer


@pytest.mark.parametrize(
    ("test_input", "expected_controls", "expected_events"),
    [
        (
            """
            type w_customer from window
            {
                cb_save:commandbutton {
                    text = "Save"
                    event clicked()
                    {
                        MessageBox("Save", "Save clicked")
                    }
                }

                dw_main:datawindow {
                    dataobject = "d_customer"
                    event itemchanged()
                    {
                        MessageBox("Change", "Item changed")
                    }
                }
            }
            """,
            2,  # Save button and DataWindow
            2,  # clicked and itemchanged events
        ),
    ],
)
def test_window_parsing(test_input: str, expected_controls: int, expected_events: int):
    """Test parsing window definitions."""
    tree = parse_text(test_input)
    transformer = PBTransformer()
    result = transformer.transform(tree)

    assert isinstance(result, Window)
    assert len(result.controls) == expected_controls

    # Test Save button
    save_btn = result.controls[0]
    assert save_btn.name == "cb_save"
    assert save_btn.type == "commandbutton"
    assert save_btn.properties["text"] == "Save"

    # Test DataWindow
    dw = result.controls[1]
    assert dw.name == "dw_main"
    assert dw.type == "datawindow"
    assert dw.properties["dataobject"] == "d_customer"

    # Test events
    total_events = sum(len(c.events) for c in result.controls)
    assert total_events == expected_events
