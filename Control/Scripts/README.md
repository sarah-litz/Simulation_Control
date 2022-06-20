
# Writing Scripts #

## Setup() ##


## Notes on other Methods ## 

    notes on other important methods; These functions are always in use/being called by the control software code, but users could also be called from a script if needed. 

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





