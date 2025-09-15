from src.model.constructs.global_vars import GlobalVariables
from src.parse.coordinator import parse_text
from src.parse.transformer import PBTransformer


def test_global_vars_parsing():
    """Test parsing global variables."""
    test_input = """
    global variables
    {
        string gs_database
        integer gi_userid
    }
    """

    tree = parse_text(test_input)
    transformer = PBTransformer()
    result = transformer.transform(tree)

    assert isinstance(result, GlobalVariables)
    assert len(result.variables) == 2
    assert "gs_database" in result.variables
    assert "gi_userid" in result.variables

    # Test string variable with initial value
    db_var = result.variables["gs_database"]
    assert db_var.name == "gs_database"
    assert db_var.type == "string"
    assert db_var.initial_value == "customer_db"

    # Test integer variable without initial value
    user_id = result.variables["gi_userid"]
    assert user_id.name == "gi_userid"
    assert user_id.type == "integer"
    assert user_id.initial_value is None

    # Test boolean variable with initial value
    logged_in = result.variables["gb_logged_in"]
    assert logged_in.name == "gb_logged_in"
    assert logged_in.type == "boolean"
    assert logged_in.initial_value == "false"

    # Test date variable without initial value
    last_login = result.variables["gd_last_login"]
    assert last_login.name == "gd_last_login"
    assert last_login.type == "date"
    assert last_login.initial_value is None
