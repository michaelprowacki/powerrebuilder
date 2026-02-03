forward
global type n_data_service from n_base_service
end type
end forward

global type n_data_service from n_base_service
end type
global n_data_service n_data_service

type variables
// Additional instance variables
protected:
transaction itr_database
boolean ib_connected = false

private:
string is_connection_string
long il_query_count = 0
end type

forward prototypes
public function integer of_initialize()
public function integer of_connect(string as_database)
public function integer of_disconnect()
public function boolean of_is_connected()
public function datastore of_retrieve_data(string as_sql)
protected function integer of_execute_sql(string as_sql)
end prototypes

public function integer of_initialize();// Override parent initialization
integer li_return

// Call parent first
li_return = super::of_initialize()

// Set our service name
is_service_name = "data_service"

// Create transaction object
itr_database = create transaction

of_log("Data service initialized")

return li_return
end function

public function integer of_connect(string as_database);// Connect to database
if ib_connected then
    of_log("Already connected")
    return 0
end if

is_connection_string = as_database

// Set connection properties
itr_database.DBMS = "ODBC"
itr_database.AutoCommit = False
itr_database.DBParm = "ConnectString='" + as_database + "'"

// Connect
connect using itr_database;

if itr_database.SQLCode = 0 then
    ib_connected = true
    of_log("Connected to: " + as_database)
    return 1
else
    of_log("Connection failed: " + itr_database.SQLErrText)
    return -1
end if
end function

public function integer of_disconnect();// Disconnect from database
if not ib_connected then
    return 0
end if

disconnect using itr_database;
ib_connected = false

of_log("Disconnected from database")

return 1
end function

public function boolean of_is_connected();// Return connection status
return ib_connected
end function

public function datastore of_retrieve_data(string as_sql);// Retrieve data into datastore
datastore lds_data

if not ib_connected then
    of_log("Not connected to database")
    SetNull(lds_data)
    return lds_data
end if

lds_data = create datastore

// Create syntax from SQL
string ls_syntax, ls_errors
ls_syntax = SQLCA.SyntaxFromSQL(as_sql, "Style(Type=Grid)", ls_errors)

if Len(ls_errors) > 0 then
    of_log("Syntax error: " + ls_errors)
    destroy lds_data
    SetNull(lds_data)
    return lds_data
end if

// Create datastore
lds_data.Create(ls_syntax, ls_errors)

if Len(ls_errors) > 0 then
    of_log("Create error: " + ls_errors)
    destroy lds_data
    SetNull(lds_data)
    return lds_data
end if

// Set transaction and retrieve
lds_data.SetTransObject(itr_database)
long ll_rows
ll_rows = lds_data.Retrieve()

il_query_count++
of_log("Retrieved " + String(ll_rows) + " rows. Query #" + String(il_query_count))

return lds_data
end function

protected function integer of_execute_sql(string as_sql);// Execute SQL statement
if not ib_connected then
    of_log("Not connected to database")
    return -1
end if

execute immediate :as_sql using itr_database;

if itr_database.SQLCode = 0 then
    il_query_count++
    of_log("Executed SQL successfully. Query #" + String(il_query_count))
    return 1
else
    of_log("SQL Error: " + itr_database.SQLErrText)
    return -1
end if
end function

on n_data_service.create
call super::create
end on

on n_data_service.destroy
call super::destroy
end on

event destructor;// Clean up
if ib_connected then
    of_disconnect()
end if

if IsValid(itr_database) then
    destroy itr_database
end if

// Call parent
call super::destructor
end event
