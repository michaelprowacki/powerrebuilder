from src.model.user_object import UserObject
from src.parse.coordinator import parse_text
from src.parse.transformer import PBTransformer


def test_user_object_parsing():
    """Test parsing user object definitions."""
    test_input = """
    type u_customer from userobject
    {
        cb_save:commandbutton {
            text = "Save"
            enabled = true
            event clicked()
            {
                MessageBox("Save", "Save clicked")
            }
        }

        dw_main:datawindow {
            dataobject = "d_customer"
            enabled = true
            event itemchanged()
            {
                MessageBox("Change", "Item changed")
            }
        }
    }
    """

    tree = parse_text(test_input)
    transformer = PBTransformer()
    result = transformer.transform(tree)

    assert isinstance(result, UserObject)
    assert result.name == "u_customer"
    assert len(result.controls) == 2

    # Test Save button
    save_btn = result.controls[0]
    assert save_btn.name == "cb_save"
    assert save_btn.type == "commandbutton"
    assert save_btn.properties["text"] == "Save"
    assert save_btn.properties["enabled"] == "true"

    # Test DataWindow
    dw = result.controls[1]
    assert dw.name == "dw_main"
    assert dw.type == "datawindow"
    assert dw.properties["dataobject"] == "d_customer"
    assert dw.properties["enabled"] == "true"

    assert len(result.events) == 2  # constructor and validate

    # Test events
    event_names = {e.name for e in result.events}
    assert event_names == {"on_constructor", "on_validate"}
