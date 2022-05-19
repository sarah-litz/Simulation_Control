
# Writing Scripts #

## Setup() ##

### Activating Interactables ### 

    interactableABC.activate() 
    map.activate_interactables()

> Method 1: interactableABC.activate()

- sets interactableABC.active to True
- starts running interactable's watch_for_threshold_event in a separate thread

> Method 2: map.activate_interactables()

- activates all interactables in the box
- automatically called at the start of a mode
- to prevent an interatable from being active in a mode, then a call to deactivate() should be made from the mode's setup() method.

### Deactivating Interactables ###

    interactableABC.deactivate()
    map.deactivate_interactables(clear_threshold_queue=True) 

> Method 1: interactableABC.deactivate()

- sets interactableABC.active to False
- this will interrupt execution of the interactable's watch_for_threshold_event
- prints to console which interactable is getting deactivated

> Method 2: map.deactivate_interactables(clear_threshold_queue=True)

- call automatically happens in between modes through a call to map.deactivate_interactables(clear_threshold_queue = True) which deactivates all interactables in the box, and, assuming clear_threshold_queue has not been set to False, will empty their threshold_event_queue before beginning the next mode.

#### What happens when I deactivate an interactable? ####

    When you deactivate an interactable, you will notice one main effect: the interactable's threshold_event_queue will remain empty throughout the mode that it is deactivated for. This is because the interactable's watch_for_threshold_event method will not be called when it is deactivated. 

#### When should I deactivate an interactable? ####

    If you notice an interactable's threshold_event_queue is overflowing with events, then it could be beneficial to deactivate this interactable during the mode's execution. (It will still respond to any function calls that you make to it, however they will not be recorded in its event queue.) 

    Example of why/when interactable has a ton of events recorded: If we setup a box that has door1, and lever1 as door1's dependent, but for one of the mode's we just want the door to sit open and the lever to have no effect on the door's state, then we deactivate the lever. As a result, during this mode door1 is not dependent on the occurence of a lever1 threshold event. Therefore, door1's threshold_event is now dictated only by if door1 is sitting in its goal_state value. Becuase we have told door1 to sit in its goal_state throughout the entire mode, if we activate door1, activating its watch_for_threshold_event method, then every iteration of this function will find that door1 has reached its threshold goal_value, and append yet another event to its threshold_event_queue. 

    If at any point throughout the mode's script you want to activate these interactables, simply make calls to their activate() methods.
