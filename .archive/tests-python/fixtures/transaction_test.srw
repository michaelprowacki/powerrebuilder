forward
global type w_transaction_test from window
end type
type cb_save from commandbutton within w_transaction_test
end type
type cb_rollback from commandbutton within w_transaction_test
end type
type dw_customer from datawindow within w_transaction_test
end type
end forward

global type w_transaction_test from window
integer width = 2400
integer height = 1600
boolean titlebar = true
string title = "Transaction Test Window"
cb_save cb_save
cb_rollback cb_rollback
dw_customer dw_customer
end type
global w_transaction_test w_transaction_test

type variables
transaction itr_local
boolean ib_transaction_active = false
end type

forward prototypes
public function integer of_begin_transaction()
public function integer of_commit_transaction()
public function integer of_rollback_transaction()
public subroutine of_log_transaction(string as_action)
end prototypes

public function integer of_begin_transaction();// Begin a new transaction
if ib_transaction_active then
    MessageBox("Transaction", "Transaction already active")
    return -1
end if

// Create local transaction
itr_local = create transaction
itr_local.DBMS = "SYB"
itr_local.Database = "customer_db"
itr_local.LogID = "sa"
itr_local.LogPass = ""
itr_local.ServerName = "localhost"

// Connect
CONNECT USING itr_local;

if itr_local.SQLCode <> 0 then
    MessageBox("Database Error", "Failed to connect: " + itr_local.SQLErrText)
    destroy itr_local
    return -1
end if

// Set savepoint
EXECUTE IMMEDIATE "SAVEPOINT sp_before_update" USING itr_local;

ib_transaction_active = true
of_log_transaction("BEGIN")

return 1
end function

public function integer of_commit_transaction();// Commit active transaction
if not ib_transaction_active then
    MessageBox("Transaction", "No active transaction")
    return -1
end if

// Update sequence
UPDATE customers
SET last_modified = CURRENT TIMESTAMP,
    modified_by = USER
WHERE customer_id = :dw_customer.GetItemNumber(1, "customer_id")
USING itr_local;

if itr_local.SQLCode <> 0 then
    of_rollback_transaction()
    MessageBox("Update Error", "Failed to update: " + itr_local.SQLErrText)
    return -1
end if

// Commit
COMMIT USING itr_local;

if itr_local.SQLCode = 0 then
    of_log_transaction("COMMIT")
    ib_transaction_active = false
    DISCONNECT USING itr_local;
    destroy itr_local
    return 1
else
    MessageBox("Commit Error", "Failed to commit: " + itr_local.SQLErrText)
    return -1
end if
end function

public function integer of_rollback_transaction();// Rollback active transaction
if not ib_transaction_active then
    return 0
end if

// Rollback to savepoint
EXECUTE IMMEDIATE "ROLLBACK TO SAVEPOINT sp_before_update" USING itr_local;

// Full rollback if savepoint fails
if itr_local.SQLCode <> 0 then
    ROLLBACK USING itr_local;
end if

of_log_transaction("ROLLBACK")
ib_transaction_active = false

DISCONNECT USING itr_local;
destroy itr_local

return 1
end function

public subroutine of_log_transaction(string as_action);// Log transaction activity
datetime ldt_now
string ls_log

ldt_now = DateTime(Today(), Now())
ls_log = String(ldt_now, "yyyy-mm-dd hh:mm:ss") + " - " + as_action

// Write to transaction log
INSERT INTO transaction_log (log_time, action, user_id, window_name)
VALUES (:ldt_now, :as_action, :gs_userid, "w_transaction_test")
USING SQLCA;

COMMIT USING SQLCA;
end subroutine

on w_transaction_test.create
this.cb_save=create cb_save
this.cb_rollback=create cb_rollback
this.dw_customer=create dw_customer
this.Control[]={this.cb_save,&
this.cb_rollback,&
this.dw_customer}
end on

on w_transaction_test.destroy
// Ensure transaction is cleaned up
if ib_transaction_active then
    of_rollback_transaction()
end if

destroy(this.cb_save)
destroy(this.cb_rollback)
destroy(this.dw_customer)
end on

event open;// Initialize the datawindow
dw_customer.SetTransObject(SQLCA)
dw_customer.Retrieve()

// Start transaction
of_begin_transaction()
end event

event closequery;// Check for pending changes
if dw_customer.ModifiedCount() > 0 or dw_customer.DeletedCount() > 0 then
    integer li_response

    li_response = MessageBox("Unsaved Changes", &
        "Do you want to save your changes?", &
        Question!, YesNoCancel!)

    choose case li_response
        case 1 // Yes
            if of_commit_transaction() = -1 then
                return 1 // Prevent close
            end if
        case 2 // No
            of_rollback_transaction()
        case 3 // Cancel
            return 1 // Prevent close
    end choose
end if

return 0
end event

type cb_save from commandbutton within w_transaction_test
integer x = 100
integer y = 1400
integer width = 400
integer height = 112
integer taborder = 20
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Arial"
string text = "&Save"
end type

event clicked;// Save with transaction
if dw_customer.Update() = 1 then
    if of_commit_transaction() = 1 then
        MessageBox("Success", "Changes saved successfully")
        of_begin_transaction() // Start new transaction
    end if
else
    of_rollback_transaction()
    MessageBox("Error", "Failed to save changes")
end if
end event

type cb_rollback from commandbutton within w_transaction_test
integer x = 600
integer y = 1400
integer width = 400
integer height = 112
integer taborder = 30
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Arial"
string text = "&Cancel"
end type

event clicked;// Rollback changes
if MessageBox("Confirm", "Discard all changes?", Question!, YesNo!) = 1 then
    of_rollback_transaction()
    dw_customer.Reset()
    dw_customer.Retrieve()
    of_begin_transaction()
end if
end event

type dw_customer from datawindow within w_transaction_test
integer x = 50
integer y = 50
integer width = 2300
integer height = 1300
integer taborder = 10
string title = "none"
string dataobject = "d_customer_list"
boolean hscrollbar = true
boolean vscrollbar = true
boolean livescroll = true
borderstyle borderstyle = stylelowered!
end type
