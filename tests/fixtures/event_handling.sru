forward
global type u_event_handler from userobject
end type
type st_status from statictext within u_event_handler
end type
type cb_trigger from commandbutton within u_event_handler
end type
type sle_input from singlelineedit within u_event_handler
end type
end forward

global type u_event_handler from userobject
integer width = 1600
integer height = 800
long backcolor = 67108864
string text = "none"
long tabtextcolor = 33554432
long picturemaskcolor = 536870912
event ue_custom ( string as_data )
event ue_validate ( ref string as_value,  ref boolean ab_cancel )
event type integer ue_process ( readonly string as_command )
st_status st_status
cb_trigger cb_trigger
sle_input sle_input
end type
global u_event_handler u_event_handler

type variables
// Event tracking
protected:
integer ii_event_count = 0
string is_last_event
datetime idt_last_event

// Event queue
private:
string is_event_queue[]
boolean ib_processing = false
end type

forward prototypes
public function integer of_trigger_event (string as_event_name)
public function integer of_post_event (string as_event_name, long al_delay)
protected subroutine of_update_status (string as_message)
public function boolean of_is_event_pending ()
end prototypes

event ue_custom(string as_data);// Custom event handler
ii_event_count++
is_last_event = "ue_custom"
idt_last_event = DateTime(Today(), Now())

of_update_status("Custom event received: " + as_data)

// Chain to another event
if Len(as_data) > 0 then
    this.Event ue_validate(as_data, ib_processing)
end if
end event

event type integer ue_process(readonly string as_command);// Process command event with return value
integer li_return = 0

ii_event_count++
is_last_event = "ue_process"
idt_last_event = DateTime(Today(), Now())

// Process based on command
choose case Lower(as_command)
    case "save"
        of_update_status("Processing save command...")
        li_return = 1

    case "validate"
        of_update_status("Processing validation...")
        li_return = 2

    case "cancel"
        of_update_status("Processing cancel...")
        li_return = -1

    case else
        of_update_status("Unknown command: " + as_command)
        li_return = 0
end choose

// Post a completion event
this.Post Event ue_custom("Process completed: " + String(li_return))

return li_return
end event

event ue_validate(ref string as_value, ref boolean ab_cancel);// Validation event with pass-by-reference parameters
ii_event_count++
is_last_event = "ue_validate"
idt_last_event = DateTime(Today(), Now())

// Validate the value
if Len(Trim(as_value)) = 0 then
    of_update_status("Validation failed: Empty value")
    ab_cancel = true
    return
end if

// Transform the value
as_value = Upper(Trim(as_value))

// Check for special values
if as_value = "STOP" then
    ab_cancel = true
    of_update_status("Validation cancelled by user")
else
    ab_cancel = false
    of_update_status("Validation passed: " + as_value)
end if
end event

public function integer of_trigger_event (string as_event_name);// Trigger an event dynamically
integer li_return = 0

choose case Lower(as_event_name)
    case "custom"
        this.Event ue_custom("Triggered dynamically")
        li_return = 1

    case "validate"
        string ls_value = "test"
        boolean lb_cancel = false
        this.Event ue_validate(ls_value, lb_cancel)
        if lb_cancel then li_return = -1 else li_return = 1

    case "process"
        li_return = this.Event ue_process("save")

    case else
        of_update_status("Unknown event: " + as_event_name)
        li_return = 0
end choose

return li_return
end function

public function integer of_post_event (string as_event_name, long al_delay);// Post an event with optional delay
if al_delay > 0 then
    // Use timer for delayed execution
    if UpperBound(is_event_queue) < 10 then
        is_event_queue[UpperBound(is_event_queue) + 1] = as_event_name
        Timer(al_delay / 1000.0) // Convert milliseconds to seconds
        return 1
    else
        return -1 // Queue full
    end if
else
    // Post immediately
    this.Post of_trigger_event(as_event_name)
    return 1
end if
end function

protected subroutine of_update_status (string as_message);// Update status display
st_status.text = as_message + " (Events: " + String(ii_event_count) + ")"
end subroutine

public function boolean of_is_event_pending ();// Check if events are pending
return UpperBound(is_event_queue) > 0
end function

on u_event_handler.create
this.st_status=create st_status
this.cb_trigger=create cb_trigger
this.sle_input=create sle_input
this.Control[]={this.st_status,&
this.cb_trigger,&
this.sle_input}
end on

on u_event_handler.destroy
destroy(this.st_status)
destroy(this.cb_trigger)
destroy(this.sle_input)
end on

event constructor;// Initialize
of_update_status("Event handler initialized")

// Trigger initial event
this.Post Event ue_custom("Constructor completed")
end event

event destructor;// Clean up
Timer(0) // Cancel any pending timer
end event

event timer;// Process queued events
if UpperBound(is_event_queue) > 0 then
    string ls_event
    ls_event = is_event_queue[1]

    // Remove from queue
    integer li_i
    for li_i = 2 to UpperBound(is_event_queue)
        is_event_queue[li_i - 1] = is_event_queue[li_i]
    next
    is_event_queue[UpperBound(is_event_queue)] = ""

    // Trigger the event
    of_trigger_event(ls_event)

    // Continue timer if more events
    if UpperBound(is_event_queue) > 0 then
        Timer(0.1)
    else
        Timer(0)
    end if
else
    Timer(0)
end if
end event

type st_status from statictext within u_event_handler
integer x = 50
integer y = 600
integer width = 1500
integer height = 64
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Arial"
long textcolor = 33554432
long backcolor = 67108864
string text = "Ready"
boolean focusrectangle = false
end type

type cb_trigger from commandbutton within u_event_handler
integer x = 800
integer y = 300
integer width = 400
integer height = 112
integer taborder = 20
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Arial"
string text = "Trigger Event"
end type

event clicked;// Get value from input
string ls_value
ls_value = sle_input.text

if Len(ls_value) > 0 then
    // Trigger process event with the value
    integer li_result
    li_result = parent.Event ue_process(ls_value)

    // Post delayed event based on result
    if li_result > 0 then
        parent.of_post_event("custom", 500)
    end if
else
    // Direct trigger
    parent.of_trigger_event("validate")
end if
end event

type sle_input from singlelineedit within u_event_handler
integer x = 50
integer y = 300
integer width = 600
integer height = 112
integer taborder = 10
integer textsize = -10
integer weight = 400
fontcharset fontcharset = ansi!
fontpitch fontpitch = variable!
fontfamily fontfamily = swiss!
string facename = "Arial"
long textcolor = 33554432
string text = "none"
borderstyle borderstyle = stylelowered!
end type

event modified;// Trigger validation on change
boolean lb_cancel = false
string ls_value = this.text

parent.Event ue_validate(ls_value, lb_cancel)

if lb_cancel then
    this.text = ""
    this.SetFocus()
else
    this.text = ls_value
end if
end event
