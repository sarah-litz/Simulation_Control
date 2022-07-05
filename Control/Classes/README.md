# Classes

## InteractableABC

### Accounting for a Simulated Interactable

    interactable.isSimulation(): Boolean

This function returns True if the interactable is being simulated, False otherwise.

These "simulation checks" should be called in any method that accesses hardware components. In doing so, we can write simple logic for what to do if the interactable is being simulated.

For example, within a door's open() function we write:

    if door.isSimulation() is True: 
        # simulation is running, set new switch state and return 
        door.buttonObj = True 
        return 
    else: 
        # door hardware is present, continue with normal execution...

### Dependent vs Independent Interactables

- Door is Independent (depends on lever.num_pressed value)
- Lever is Dependent (dependent on vole presses)
- RFID is Dependent (dependent on vole whereabouts)

#### Dependents Loop

    class interactableABC
        def dependents_loop() 
If an interactable has any dependents, then there must be a method dependents_loop defined in that interactable's class (overrides the interactableABC method). This method should do the following things:

- set the interactables isIndependent attribute to True (results in the simulation side not directly setting this interactable's attribute to its goal_value, as this should instead be triggered by the interactable's dependents)
- define how the interactable handles/interacts with its dependents.

## Map

## ModeABC
