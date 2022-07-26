
# Vole Class 

## Movements 

### Vole Movements and Interactable Thresholds  

    for a vole to move passed an interactable, that interactable's threshold must be True

#### methods 
1. at_location_of : boolean - physical proximity check
2. simulate_vole_interactable_interaction : None 

    **i.** first calls methods and makes checks to ensure that simulating this interaction is valid.
    - Active Check = is the designated interactable actively running? 
    - Physical Proximity Check = is the vole standing in front of the interactable? (calls the method at_location_of)
    - Dependency Chain Check = Can simulate any non-barrier interactable. If the interactable is a barrier, can simulate if and only if that interactable is Autonomous.

    **ii.** Simulation (if interactable.isSimulation is True) Peforms a simulated interaction between a vole and a designated interactable
    - simulates by calling function specified by 'simulate_with_fn', *or* simulates by setting the threshold attribute to its goal value 

3. is_move_valid (destination) : boolean 
    - does not actually make a move/update voles location, just checks if the vole can move from its current edge or chamber into the destination chamber in a single move 
    - returns True if the current chamber and destination chamber share an edge 
    - returns True if the current edge is connected to the destination chamber 
    - otherwise returns False 

4. update_location(newcomponent=None): None 
    - updates the vole's current component position 
    - also updates the chamber/edge location if the new component position is in a new chamber/edge 

5. move_to_interactable(goal_interactable): None 
    - converts interactable to component and calls the move_to_component function 
6. move_to_component(goal_component): [components_lst] 
    - compiles list of components that fall in between voles current component and the goal_component, then takes single steps by calling move_next_component() until the goal component is reached. 
7. move_next_component(component)
    - maximum step size between the voles current location and the goal component is 1. i.e., component must be a neighboring component relative to the voles current component position. 
    - checks that the vole can move passed the component that it is currently standing at. 
        - is current interactable a barrier? 
            - if No, then threshold not required to be True at this time, so vole may PASS to the goal component 
            - if Yes, then we require that the threshold is True. 
                - if barrier's threshold is True, Vole may PASS
                - if barrier's threshold is False, then we must check for dependents and/or autonomy of the interactable: 
                    - if the interactable has dependents, then vole CANNOT complete this move, because first requires simulating dependents (doors with dependents fall into this cateogry) 
                    - if no dependents, then check if the interactable is Autonomous, as we can simulate autonomous interactables whenever, but cannot simulate non-autonomous interactables. 
                        - if the barrier interactable is not autonomous, then vole CANNOT complete this move. (doors w/out dependents fall into this category) 
                        - if the barrier interactable is autonomous, then we may simulate this interactable, and vole may PASS. (rfids fall into this barrier/autonomous category)
    




        ## END FOR: Done Simulating Components along the Edge ##


        # All Component Thresholds Reached; loop back thru and reset the dependent components threshold values to False now that we have confirmed an event occurred 
        print('\n')
        for component in edge:

            component.interactable.threshold = False  # reset the components threshold
            
            print(f'(Simulation/Vole.py, attempt_move) the threshold condition was met for {component.interactable.name}.') #CHANGE Event: {event}')
        
        


        ## Update Vole Location ## 