# Classes

## InteractableABC

### Accounting for a Simulated Interactable

    interactable.isSimulation(): Boolean

This function returns True if the interactable is being simulated, False otherwise.

These "simulation checks" should be called in any method that accesses hardware components. In doing so, we can write simple logic for what to do if the interactable is being simulated.

For example, within a door's open() function we write:

    if door.isSimulation() is True: 
        # simulation is running, set new state and return 
        door.state = True 
        return 
    else: 
        # door hardware is present, continue with normal execution...

### Dependent vs Independent Interactables

    interactable.isIndependent is set to True if the interactable's behavior is independent of a vole's behavior, and is based on some value of another interactable. 

- Door is Independent (depends on lever.pressed value)
- Lever is Dependent (dependent on vole presses)
- RFID is Dependent (dependent on vole whereabouts)

#### Dependents Loop

    class interactableABC
        def dependents_loop() 
If an interactable has any dependents, then there must be a method dependents_loop defined in that interactable's class (overrides the interactableABC method). This method should do the following things:

- set the interactables isIndependent attribute to True (results in the simulation side not directly setting this interactable's attribute to its goal_value, as this should instead be triggered by the interactable's dependents)
- define how the interactable handles/interacts with its dependents.

Example: For a door, we define that if any of its dependents (levers) reaches threshold, then we call open() or close() the door (whichever was indicated in the threshold_condition['goal_value']). If there are any other buttons that control the opening/closing of a door, the logic for those buttons should be added within this function. (i.e. if button_press, then open() door)

*On the simulation side of things, if we try to call vole_interactable_interaction on an interactable that isIndependent==True, then we return and do not procede with a simulation becuase we defined that the interactable acts independent of a vole's behavior, so we don't want to simulate a behavior that doesn't make sense in a real experiment.*

## Map

## ModeABC
