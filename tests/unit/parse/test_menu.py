from src.model.menu import Menu
from src.parse.coordinator import parse_text
from src.parse.transformer import PBTransformer


def test_menu_parsing():
    """Test parsing menu definitions."""
    test_input = """
    type m_main from menu
    {
        item_file:menuitem {
            text = "File"
            event clicked()
            {
                MessageBox("File", "File menu clicked")
            }
        }
        separator;
        item_exit:menuitem {
            text = "Exit"
            event clicked()
            {
                Close(parent)
            }
        }
    }
    """

    tree = parse_text(test_input)
    transformer = PBTransformer()
    result = transformer.transform(tree)

    assert isinstance(result, Menu)
    assert result.name == "m_main"
    assert len(result.items) == 3  # File, separator, Exit

    # Test File menu item
    file_item = result.items[0]
    assert file_item.name == "item_file"
    assert not file_item.is_separator
    assert file_item.properties["text"] == "File"
    assert len(file_item.events) == 1

    # Test separator
    separator = result.items[1]
    assert separator.is_separator

    # Test Exit menu item
    exit_item = result.items[2]
    assert exit_item.name == "item_exit"
    assert not exit_item.is_separator
    assert exit_item.properties["text"] == "Exit"
    assert len(exit_item.events) == 1
