type w_customer from window {
    cb_save: commandbutton {
        text = "Save"
        enabled = true
    }

    dw_main: datawindow {
        dataobject = "d_customer_list"
        visible = true
    }

    on clicked() {
        MessageBox("Save", "Saving customer data...");
    }

    on create() {
        dw_main.retrieve();
    }
}
