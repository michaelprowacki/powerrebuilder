forward
global type n_base_service from nonvisualobject
end type
end forward

global type n_base_service from nonvisualobject
end type
global n_base_service n_base_service

type variables
protected:
string is_service_name = "base_service"
datetime idt_created
boolean ib_debug_mode = false

private:
long il_instance_id
end type

forward prototypes
public function integer of_initialize()
public function string of_get_service_name()
protected function integer of_log(string as_message)
public subroutine of_set_debug(boolean ab_debug)
end prototypes

public function integer of_initialize();// Base initialization
idt_created = DateTime(Today(), Now())
il_instance_id = CPU()

of_log("Service initialized: " + is_service_name)
return 1
end function

public function string of_get_service_name();// Return service name
return is_service_name
end function

protected function integer of_log(string as_message);// Log message if debug mode is on
if ib_debug_mode then
    string ls_output
    ls_output = String(DateTime(Today(), Now()), "yyyy-mm-dd hh:mm:ss") + &
                " [" + is_service_name + "] " + as_message

    // In real app, would write to file
    // For testing, just store in instance variable
    return 1
end if

return 0
end function

public subroutine of_set_debug(boolean ab_debug);// Set debug mode
ib_debug_mode = ab_debug
end subroutine

on n_base_service.create
call super::create
TriggerEvent( this, "constructor" )
end on

on n_base_service.destroy
TriggerEvent( this, "destructor" )
call super::destroy
end on

event constructor;// Base constructor
of_initialize()
end event

event destructor;// Base destructor
of_log("Service destroyed: " + is_service_name)
end event
