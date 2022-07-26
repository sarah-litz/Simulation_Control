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

## Map

## ModeABC
