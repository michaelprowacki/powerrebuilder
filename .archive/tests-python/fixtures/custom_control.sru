type u_custom_input from userobject {
    cb_ok: commandbutton {
        text = "OK"
        enabled = true
    }

    sle_input: edit {
        text = ""
        width = 200
        height = 30
    }

    st_label: statictext {
        text = "Enter value:"
        visible = true
    }

    on constructor() {
        // Initialize the control
        sle_input.text = "";
    }

    on validate() {
        if len(sle_input.text) > 0 then
            return true;
        return false;
    }
}
