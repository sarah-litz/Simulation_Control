"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 12/2/2022
Description: Class definition for a simulated vole. Contains methods that allow for a vole to move throughout a box and simulate interactions with interactables along the way.

Property of Donaldson Lab at the University of Colorado at Boulder
"""


# Standard Lib Imports 
from itertools import count
import time, random

# Local Imports 
from ..Logging.logging_specs import sim_log, vole_log


class SimVole: 

    def __init__(self, tag, start_chamber, rfid_id, map): 
        """ initializer for a Simulated Vole 

        Args: 
            tag (int) : number value assigned to the vole. This value will be used to id voles when recording data in the output csv file. Assigned in config file. 
            rfid_id (hex | int) : the rfid chip value. This value is used to id voles when CAN Bus signals are recieved. If vole has no chip, then this value can be left blank in config file, in which case it will be set to be the value of the tag. 
            start_chamber (int) : the starting location for the sim vole 
            map (Map) : the map instance getting used by the Simulation and Control package. 
        """

        self.rfid_id = rfid_id # rfid hex value 
        self.tag  = tag # human assigned value for simplicity 
        self.map = map 
        self.event_manager = map.event_manager
        self.active = True 

        ## Vole Location Information ## 
        self.curr_loc = self.map.get_chamber(start_chamber)
        self.prev_loc = None # object representing the voles previous location.

        # starting position between interactables is between chamber edge or wall and the first interactable in the chamber, if it exists
        if len(self.curr_loc.orderedSet) == 0: 
            self.prev_component=None # no "bridge" interactables to a nearby edge, meaning this chamber only has Unordered Interactables in it.
        else: 
            self.prev_component = self.curr_loc.get_component_for_ordered_interactable(self.curr_loc.orderedSet[0]) # last interactable that vole moved away from (so we know the direction of movement)
        try: self.curr_component = self.curr_loc.unorderedComponent # current interactable the vole is closest to ( when in a chamber, this can be a list of Unordered interactables! Vole is free to simulate with any of them )
        except AttributeError: self.curr_component = None # (interactable1, interactable2)

        self.action_probability_dist = {} # Can assign probabilities to a certain action that the vole takes 

        print(f'{self} starting in {self.curr_loc.edge_or_chamber}{self.curr_loc.id}, positioned between interactables: {self.prev_component}, {self.curr_component}')
        # vole_log(f'{self} starting in {self.curr_loc.edge_or_chamber}{self.curr_loc.id}, positioned between interactables: {self.prev_component}, {self.curr_component}')

    def __str__(self): 
        return f'SimVole{self.tag}'
    
    def at_location_of(self, interactable): 
        ''' Physical Proximity Check to see if the SimVole is at the location of <interactable>. Depends on both the chamber/edge vole is in, as well as where the vole is positioned w/in that location. 
            If <interactable> is apart of a Chamber's Unordered Interactable Set, then as long as the vole's current_component is at the Unordered Set, return True
        Args: 
            interactable (InteractableABC) : the interactable that method checks to see if the vole is sitting by. 
        Returns: 
            (boolean) : True if vole's location is at the current interactable, false otherwise. 
        '''

         
        if self.curr_component is None: # Edge Case: Vole can be sitting at component==None. Check for this.
            return False 
        
        if type(self.curr_component) is self.map.Chamber.ComponentSet: # Check the type of Interactable 
            if interactable in self.curr_component.interactableSet: # check if sitting at unordered interatables. 
                return True 
            else: 
                return False 

        if self.curr_component.interactable.name == interactable.name: # check if sitting at ordered interactable 
            return True 
        else:  
            return False 

    def simulate_move_and_interactable(self, interactable): 
        ''' calls helper functions to simulate a movement to <interactable> and then simulate an interaction with <interactable>.
        first moves to the interactable, and if movement is successful then procedes by calling simulate_vole_interactable_interaction on the interactable 
        Args: 
            interactable (InteractableABC) : the interactable that vole will attempt moving to and interacting with 
        Returns: 
            None 
        '''
        try: 
            self.move_to_interactable(interactable)
        except Exception as e: 
            self.event_manager.print_to_terminal(e)
            return 
        # procede with simulation 
        self.simulate_vole_interactable_interaction(interactable)
        return 

    def simulate_vole_interactable_interaction(self, interactable): 
        ''' simulates a voles interaction with a simulated or non-simulated hardware interactable. 
        runs through a series of error checks to ensure that the requested simulation is valid. 
        if valid, procedes with simulating the interaction in accordance with the values set in the simulation config file. 
        
        Args: 
            interactable(interactableABC) - interactable to simulate with 
        '''
        
        if not self.active: 
            # sim_log(f'(Vole{self.tag}, simulate_vole_interactable_interaction) Vole Inactive. Cannot perform the requested action.')
            # self.event_manager.new_timestamp(f'(Vole{self.tag}, simulate_vole_interactable_interaction) Vole Inactive. Cannot perform the requested action.', time.time(), print_to_screen = False )
            return 
        
        #
        # Active Check
        #
        if interactable.active is False: 
            # self.event_manager.new_timestamp(f'(Vole{self.tag}, simulate_vole_interactable_interaction) {interactable.name} is inactive', time.time(), print_to_screen = False )
            # sim_log(f'(Vole{self.tag}, simulate_vole_interactable_interaction, simulate_vole_interactable_interaction) {interactable.name} is inactive')
            # we don't care to simulate an inactive interactable
            # vole unable to effect the threshold attribute value of an inactive interactable (so threshold value is the same the entire time)
            return 


        #
        # Physical Proximity Check 
        #
        if not self.at_location_of(interactable): 
            # self.event_manager.print_to_terminal(f'(Vole{self.tag}, simulate_vole_interactable_interaction) vole{self.tag} is not at_location_of({interactable.name}). Failed the physical proximity check; cannot simulate.')
            # sim_log(f'(Vole{self.tag}, simulate_vole_interactable_interaction) vole{self.tag} is not at_location_of({interactable.name}). Failed the physical proximity check; cannot simulate.')
            return 



        #
        # Dependency Chain Check
        #
        
        # Simulation Rules: 
        # can simulate any non-barrier interactable 
        # if barrier, can simulate if and only if that interactable is Autonomous. 
        
        if interactable.barrier: 
            # ensure that barrier is also autonomous 
            if not interactable.autonomous: 
                # self.event_manager.print_to_terminal(f'(Vole{self.tag}, simulate_vole_interactable_interaction) {interactable.name} is a Barrier but is NOT autonomous. Interactables of this type do not allow for direct vole interactions.')
                # sim_log(f'(Vole{self.tag}, simulate_vole_interactable_interaction) {interactable.name} is a barrier and not autonomous. Interactables of this type do not allow for direct vole interactions. Vole must attempt simulating with {interactable.name} controllers ( interactables who have {interactable.name} as a parent )')
                return 

        #
        # Simulate
        #
        if interactable.isSimulation: 

            # vole_log( f'(Vole{self.tag}, simulate_vole_interactable_interaction) simulating vole{self.tag} interaction with {interactable.name}' ) 
            # self.event_manager.print_to_terminal(f'(Vole{self.tag}, simulate_vole_interactable_interaction) Simulating vole{self.tag} interaction with {interactable.name}')
    
            if hasattr(interactable, 'simulate_with_fn'):
                
                # sets the attributes to values that meet the threshold condition by calling simulate_with_fn 
                interactable.simulate_with_fn(interactable, self.tag)

            else:
                
                # set value using the threshold condition attribute/value pairing 
                threshold_attr_name = interactable.threshold_condition["attribute"]
                # attribute = getattr(interactable, threshold_attr_name) # get object specified by the attribute name

                # sim_log(f'(Vole{self.tag}, attempt_move) {interactable.name}, threshold attribute: {threshold_attr_name}, threshold value: {interactable.threshold_condition["goal_value"]}')
            
                # manually set the attribute to its goal value so we meet the threshold condition, and trigger the control side to add an event to the threshold_event_queue 
                setattr(interactable, threshold_attr_name, interactable.threshold_condition['goal_value'])
                
                newattrval = getattr(interactable, threshold_attr_name)
                # # sim_log(f'{interactable.name}, manual attribute check: {interactable.buttonObj}')
                # sim_log(f"(Vole{self.tag}, attempt_move) {interactable.name}, attribute result: {newattrval}")
            
            # countdown(5, f'simulating vole{self.tag} interaction with {interactable.name}') 
            time.sleep(2) # gives the threshold listener a chance to react to the simulation
            return 
        
        else:  # component should not be simulated, as the hardware for this component is present. 
            # assumes that there is a person present to perform a lever press, interrupt the rfid reader so it sends a ping, etc. 
            print ( f'\nif testing the hardware for {interactable.name}, take any necessary actions now. \n ')
            time.sleep(5)
            
    
    ##
    ## Vole Movements
    ##
    def attempt_move_validity_check(self, destination): 
        """helper function for attempt_move(). attempt_move() method is for making a move in a singular step. This checks that destination 
        can be reached in a single step, based on the vole's current location. Destination must be a Chamber. 
        Does not actually make move/update the voles location, just checks if the move is possible in a single move according to map layout. 
        Args: 
            destination (id) : the id of a Chamber (i.e. destination must be a chamber)
        Returns: 
            (boolean) : True if move is possible, False otherwise 
        """

        if self.curr_loc.edge_or_chamber == 'chamber': 
            if destination in self.curr_loc.connections.keys(): 
                return True # chamber has edge connecting it to destination 
        else: 
            if destination == self.curr_loc.v1 or destination == self.curr_loc.v2: 
                return True # edge is connected to destination chamber
        return False  
    
    def update_location(self, newcomponent=None, nxt_edge_or_chmbr_id = None): 
        ''' Updates vole's current component position (what component is the vole positioned at) and current location (edge/chamber vole is in). 
        if current component position is None, then check to see if we need to update the vole's chamber/edge/id location 
        if next component position is None, then see if we can deduce which direction the vole is traveling, so which chamber the vole should now be in. 
        Args: 
            newComponent (None | ComponentSet | Component) : the component that the vole moved to be postioned in front of 
            nxt_edge_or_chamber_id (None | int) : The id of the edge or chamber that the vole moved into. If newcomponent is None, requires that the edge/chamber id that the vole moved into is specified. 
        Returns: 
            None
        '''
        
        # make sure that the current chamber/edge/id reflects the newcomponent 
        prev_loc = self.curr_loc 

        if newcomponent is None: 
            if nxt_edge_or_chmbr_id is None: 
                raise Exception(f'(Vole{self.tag}, update_location) If trying to update vole{self.tag} component location to a newcomponent of None, then must specify the argument for next edge or chamber id that vole should be in!')
            if prev_loc.edge_or_chamber == 'chamber': 
                # grab edge 
                self.curr_loc = self.map.get_edge(nxt_edge_or_chmbr_id)
            else: 
                # grab chamber 
                self.curr_loc = self.map.graph[nxt_edge_or_chmbr_id]


        else: 
            # update voles current location to location of new interactable
            if type(newcomponent) is self.map.Chamber.ComponentSet: 
                # Unordered Component
                # new component is a chamber's unordered component set. Grab any interactable from this set. 
                self.curr_loc = self.map.get_location_object(newcomponent.interactableSet[0])
            else: 
                # Ordered Component
                self.curr_loc = self.map.get_location_object(newcomponent.interactable) 
        if prev_loc != self.curr_loc: 
            self.event_manager.print_to_terminal(f'Vole {self.tag} traveled from {prev_loc.edge_or_chamber}{prev_loc.id} into {self.curr_loc.edge_or_chamber}{self.curr_loc.id}')
            # vole_log(f'\nVole {self.tag} traveled from {prev_loc.edge_or_chamber}{prev_loc.id} into {self.curr_loc.edge_or_chamber}{self.curr_loc.id}')            
            self.prev_loc = prev_loc # update the voles previous location

        self.prev_component = self.curr_component 
        self.curr_component = newcomponent 

        self.event_manager.new_timestamp(f'(Vole{self.tag}, update_location) {self.prev_component} to {self.curr_component}', time.time())
        # vole_log(f'\n(Vole{self.tag}, update_location) {self.prev_component} to {self.curr_component}\n')

        location_visual = self.map.draw_location(location = self.curr_loc)
        self.event_manager.print_to_terminal('\n')
        # vole_log(location_visual)
    
    def move_to_interactable(self, goal_interactable): 
        ''' converts interactable to component, and calls the move_to_component function. 
        Args: 
            goal_interactable (InteractableABC) : the interactable the vole will move to 
        Returns: 
            None : calls move_to_component in its return statement. 
        '''

        if not self.active: 
            # sim_log(f'(Vole{self.tag}, move_to_interactable) Vole Inactive. Cannot perform the requested action.')
            return 

        if goal_interactable.edge_or_chamber_id < 0: 
            # ensure that interactable's location is reachable by a vole 
            # Goal Location does not exist or is not reachable by a vole (e.g. if the interactable is in a chamber with a negative integer for its id)
            raise Exception(f'(Vole{self.tag}, move_to_interactable) Invalid Argument for Vole Movement: {goal_interactable} exists in a location that is unreachable for a vole.')


        ## Printing/Logging Statements
        # if self.curr_component is not None: 
            # self.event_manager.print_to_terminal(f'(Vole{self.tag}, move_to_interactable) {self.curr_component}->{goal_interactable}')
            # vole_log(f'(Vole{self.tag}, move_to_interactable) {self.curr_component}->{goal_interactable}')
        # else: 
            # self.event_manager.print_to_terminal(f'(Vole{self.tag}, move_to_interactable) {self.curr_loc.edge_or_chamber}{self.curr_loc.id}(Empty)->{goal_interactable}')
            # vole_log(f'(Vole{self.tag}, move_to_interactable)  {self.curr_loc.edge_or_chamber}{self.curr_loc.id}(Empty)->{goal_interactable}')


        interactable_loc = self.map.get_location_object(goal_interactable)

 
        if interactable_loc.edge_or_chamber == 'chamber': 
            # check if the interactable is apart of the ordered or unordered set in the chamber 
            if goal_interactable in interactable_loc.unorderedSet: 
                # just need to move to the chamber itself
                self.move_to_component(interactable_loc.unorderedComponent, interactable_within_component = goal_interactable) # moves vole to stand at the Chamber's ComponentSet Object
                # TODO
            else: # if not in unordered set, then must be in ordered set 
                # goal interactable is a chamber interactable that is referenced by an edge, so we should just move to its component
                for (edge, interactable_lst) in interactable_loc.edgeReferences.items(): 
                    if goal_interactable in interactable_lst: # retrieve component from the edge 
                        goal_component = edge.get_component_from_interactable(goal_interactable)
                        return self.move_to_component(goal_component)

        else: # Goal is an interactable on an Edge
            goal_component = interactable_loc.get_component_from_interactable(goal_interactable)
            return self.move_to_component(goal_component)

    def move_to_component(self, goal_component, interactable_within_component = None): 
        """ executes steps to simulate a vole moving from throughout map to reach the goal_component. 
        if a vole is sitting in a location with no components, then takes extra steps to get the vole to a loctaion where we can begin compiling a component path. 
        compiles list of components that fall in between voles current component and the goal_component, then takes single steps by calling move_next_component() until the goal component is reached.
        If at any point move_next_component cannot successfully be completed, meaning vole wasn't able to reach threshold, then we return from this function. 
        Voles location gets updated within the move_next_component function as we take each step. 
        
        Args: 
            goal_component (ComponentSet | Component) : component that vole will move to. Specifies a singular interactable (Component) or a set of unordered interactables (ComponentSet)
            interactable_within_component (InteractableABC, optional) : because ordered Component objects are each paired with one interactable, if the goal component is a ComponentSet with multiple interactables, then this extra argument recieves the interactable within the ComponentSet that the vole is moving to. 
        
        Returns: 
            None 
        """
        if not self.active: 
            # sim_log(f'(Vole{self.tag}, move_to_component) Vole Inactive. Cannot perform the requested action.')
            return 

        # if the goal_component is a ComponentSet, then an interactable should be specified with the interactable_within_component argument! 
        if type(goal_component) is self.map.Chamber.ComponentSet and interactable_within_component is None: 
            raise Exception(f'(Vole{self.tag}, move_to_component) Must specify the goal interactable within {goal_component} since the goal component is a set of interactables.')
        
        # sim_log(f'(Vole{self.tag}, move_to_component) {str(self.curr_component)} -> {str(goal_component)}')
        self.event_manager.print_to_terminal(f'(Vole{self.tag}, move_to_component) {str(self.curr_component)} -> {str(goal_component)}')

        # check that goal_component exists and set Goal Location
        if type(goal_component) is self.map.Chamber.ComponentSet: 
            # Goal Component is an Unordered Component Set --> Requires checking that interactable_within_component exists. 
            if interactable_within_component.name not in self.map.instantiated_interactables: 
                raise Exception(f'(Vole{self.tag}, move_to_component) Unordered Interactable {interactable_within_component} does not exist.')
            goal_loc = self.map.get_location_object(interactable_within_component)
        else: 
            goal_loc = self.map.get_location_object(goal_component.interactable)
            if goal_component.interactable.name not in self.map.instantiated_interactables: 
                raise Exception(f'(Vole{self.tag}, move_to_component) goal component {goal_component} does not exist.')
            
        
        ### If Voles Current Component is None, the we Must first reposition at nearest component before getting the component path 
        while self.curr_component is None: # loops Until We Find the first Component along our path that we can position the vole at
            
            if not self.active: 
                return 
            
            ### This entire while loop is just to get the vole positioned at some component, since its current component is None and that is unhelpful to start out on!  
            
            # sim_log(f'(Vole{self.tag}, move_to_component) Vole{self.tag} current component is None; Searching for the nearest component to update the voles location to.')
            
            path = self.map.get_edge_chamber_path(self.curr_loc, goal_loc) # get orderd path of edges/chambers so Vole can attempt moving to any of these locations to start out with.
            
            ## position vole in place that provides more information for us ( we know that vole is in an EMPTY edge/chamber, so there is some flexibility for the vole movements here! )
            
            if self.curr_loc == 'edge': # sitting in empty edge. Move to the closest chamber. 
                # get first chamber in path, and add the chamber's interactables to our component list
                if self.map.get_chamber(self.curr_loc.v1) in path: # figure out if we need to reverse the component list or not
                    newloc = self.curr_loc.v1
                    clst = newloc.get_component_list(reverse=True)
                else: 
                    newloc = self.map.get_chamber(self.curr_loc.v2)
                    clst = newloc.get_component_list()
                if clst is not None: 
                    # move to first component 
                    self.update_location(clst[0])
                else: 
                    self.update_location(None, nxt_edge_or_chmbr_id=newloc)                
            else: # current location is an empty chamber. move to closest edge.
                for (c,e) in self.curr_loc.connections.items(): 
                    if e in path: 
                        # move to new edge 
                        # check if interactables exist on this edge. If they do, make move to that interactable. 
                        if self.curr_loc.id == e.v2: 
                            clst = e.get_component_list(reverse=True)
                        else: 
                            clst = e.get_component_list() 
                    # STILL IN WHILE LOOP FOR WHEN VOLE START COMPONENT IS NONE!
                    if clst is not None: 
                        # move to first component 
                        self.update_location(clst[0])
                    else: 
                        # new edge is empty, manually move the vole there anyways. 
                        self.update_location(None, nxt_edge_or_chmbr_id = e.id)        
        # END of While loop that ensures voles current location is not "None" 

        
        ### COMPILE COMPONENT PATH: Get list of components in between current location and goal location 
        component_lst = self.map.get_component_path(self.curr_component, goal_component) 
        self.event_manager.print_to_terminal( f'\n(Vole{self.tag}, move_to_component) components between curr_loc and goal_loc:, {[*(str(c) for c in component_lst)]}\n')
        # vole_log(f'(Vole{self.tag}, move_to_component) components between curr_loc and goal_loc:, {[*(str(c) for c in component_lst)]}')

        # for each component in component_lst, call move_next_component
        for c in component_lst: 

            # move from current component to the next component in the path 
            if not self.active: 
                return 
            
            res = self.move_next_component(c)
            if not res: 
                return 
            
        return component_lst

    def move_next_component(self, goal_component, nxt_edge_or_chmbr_id = None): 
        """ 
        [summary] Moves passed the voles current component in order to reach goal_component. 
        To move passed a vole's current component, must ensure that it is physically possible for that vole to pass that component, or if any signals (e.g. rfid) should be sent when the vole does so. 
        Using the interactable's autonomous and barrier attributes to decide what actions to take, this method takes steps to accurately simulate vole's movement when passing a single interactable. 
        
        The following rules explain how interactable's are treated differently based on their autonomous(boolean) and barrier(boolean) values: 
            For Each Interactable: 
                    if is autonomous: simulate 
                    if not barrier: pass 
                    if barrier with true threshold: pass 
                    if barrier with false threshold: cannot pass 
        
        On success, the vole's current component will be updated to the goal_component. Note that this means the vole is positioned at goal_component, and has not simulated/interacted with that component yet, as this happens when the vole moves passed a component. (i.e. any component that has been set to a vole's prev_component means that a vole successfully moved passed that component.)
        
        Args: 
            goal_component (Component | ComponentSet) : component that vole will move to position itself infront of by passing the current interactable it is located at. 
            nxt_edge_or_chmbr_id (int, optional) : if goal_component is None, must supply a next_edge_or_chmbr_id value. (goal_component could be None if at end of an edge's linked list.)
        Returns: 
            (boolean) : True if vole is now positioned at goal_componnet, False otherwise. 
        """


        #
        # Edge Cases 
        #

        if not self.active: 
            # sim_log(f'(Vole{self.tag}, move_next_component) Vole Inactive. Cannot perform the requested action.')
            return 

        # inner helper function, getInteractable
        def getInteractable(component): 
            """ inner method to retrieve a component's interactable. If component is None, this prevents errors from getting thrown. """
            if type(component) is self.map.Chamber.ComponentSet: 
                return component.interactableSet[0] # just return the first interactable from the unordered set!! 
            try: return component.interactable # convert to a list so we can iterate thru interactables even if there is only a single interactable
            except AttributeError: return None

        # Interactables At/Around Vole's Current Position
        if type(self.curr_component) is self.map.Chamber.ComponentSet: 
            curr_interactable = getInteractable(self.curr_component)   
            nxt_interactable = None 
            prev_interactable = None 
        else: 
            curr_interactable = getInteractable(self.curr_component)
            nxt_interactable = getInteractable(self.curr_component.nextval)
            prev_interactable = getInteractable(self.curr_component.prevval)

        # Interactables At/Around Goal Position 
        goal_interactable = getInteractable(goal_component)
        if goal_interactable is None or type(goal_component) is self.map.Chamber.ComponentSet: 
            goal_nxt = None 
            goal_prev = None
            if goal_interactable is None and nxt_edge_or_chmbr_id is None: 
                raise Exception(f'(Vole{self.tag}, move_next_component) if goal component is None, must specify an argument for next_chamber_or_edge_id')
            
        else: 
            goal_nxt = getInteractable(goal_component.nextval)
            goal_prev = getInteractable(goal_component.prevval)

        # vole_log(f'(Vole{self.tag}, move_next_component) New Move: {str(curr_interactable)}->{str(goal_interactable)}')
        
        if curr_interactable == goal_interactable: 
            # vole_log(f'(Vole{self.tag}, move_next_component) Goal interactable and voles current interactable are the same.')
            return True 
        
        self.event_manager.new_timestamp(f'(Vole{self.tag}, move_next_component) New Move: {str(curr_interactable)}->{str(goal_interactable)}', time.time(), print_to_screen = True)
        
        if self.prev_component == goal_component: 
            # Case: Vole is Turning Around!
            # e.g. is in between rfid1 and door1, so curr_component is door1 and prev is rfid1. The passed in goal would be rfid1. 
            # in order to make a direction change, we simply need to swap the prev and the curr component to represent this change in direction 
            self.update_location(goal_component)
            # vole_log(f'(vole{self.tag}, move_next_component) Vole is Turning Around but still positioned between the same interactables! Now facing {self.curr_component}, with back to {self.prev_component}.')
            return True

        # Validity Check: ensure that we only need to take a single step/move to complete the requested move.
        if nxt_interactable != goal_interactable and prev_interactable != goal_interactable: # if curr_component->nxt.interactable != goal AND currcomponent->prev != goal

            # possible that the next component is on an adjacent edge/chamber to the vole's current location 

            if len(self.map.get_component_path(self.curr_component,goal_component)) == 2: 
                # Valid Move Request: there are no components that stand in between the current component and the goal component
                pass 
            else: 
                # Invalid Move Request: there are 1+ components in between the vole's current component and the goal component
                raise Exception(f'Vole{self.tag}, move_next_component) only accepts components as arguments that are directly next to the voles location: {self.curr_component}. prev={self.curr_component.prevval}, next={self.curr_component.nextval}. The goal component {goal_component} has prev={goal_component.prevval} and next={goal_component.nextval}')
                return False

        
        #
        # Check that we are able to move past the interactable that vole is currently positioned at ( this only happens for ONE interactable, the current one, each time this function gets called )
        #
        #       for each interactable, 
        #           if is autonomous: simulate 
        #           if not barrier: pass 
        #           if barrier with true threshold: pass 
        #           if barrier with false threshold: cannot pass 
                   
        
        if curr_interactable.barrier is False: ## Interactable is Not a Barrier, Move Passed the Interactable Freely. 

            if curr_interactable.autonomous: # if Autonomous --> Simulate! 
                
                # interactable is not a barrier, but is autonomous so we simulate to interact with it anyways. Voles location will update even if this is not successful, as this is not a barrier interactable 
                self.simulate_vole_interactable_interaction(curr_interactable) 

            # we can make move freely, update location 
            self.update_location(goal_component, nxt_edge_or_chmbr_id = nxt_edge_or_chmbr_id)
            return True



        ### Interactable is a Barrier Interactable. Barrier interactables require that threshold is True. 
        
        if curr_interactable.threshold is True: # TRUE Threshold, can make move freely. 
            self.event_manager.print_to_terminal(f'(Simulation/Vole{self.tag}, move_next_component) the threshold condition was met for {curr_interactable}. Vole{self.tag} making the move from {self.curr_component} to {goal_component}.')
            self.update_location(goal_component, nxt_edge_or_chmbr_id = nxt_edge_or_chmbr_id)
            return True

        if not curr_interactable.autonomous: # false threshold, and not autonomous. cannot simulate if not autonomous 
            # DOORs without dependents will fall into this, as they are a barrier and not autonomous, meaning they must be controlled by something else. 
            self.event_manager.print_to_terminal(f'(Simulation/Vole{self.tag}, move_next_component) Movement from {self.curr_component}->{goal_component} cannot be completed because {self.curr_component} is a barrier but not autonomous, so requires an interaction with its child interactables to operate it.')
            return False 
        

        else: # false threshold, barrier AND autonomous
            # 
            # OK to simulate! 
            #

            self.simulate_vole_interactable_interaction(curr_interactable)
            
            time.sleep(5) 
            
            # After simulating, since this autonomous interactable IS a barrier to vole movements, we must confirm that the threshold is True before allowing the vole to move forward. 
            if curr_interactable.threshold: # recheck the threshold 
                self.event_manager.print_to_terminal(f'(Simulation/Vole{self.tag}, move_next_component) threshold met for {curr_interactable}. Vole{self.tag} moving from {self.curr_component} to {goal_component}.')
                # update location 
                self.update_location(goal_component, nxt_edge_or_chmbr_id = nxt_edge_or_chmbr_id)
                return True 

            # Simulation did not successfully meet threshold. 
            else: 
                self.event_manager.print_to_terminal(f'(Simulation/Vole{self.tag}, move_next_component) Movement from {self.curr_component}->{goal_component} cannot be completed because after simulating {self.curr_component} the threshold is still False.')
                return False 

    def attempt_move( self, destination, validity_check = True ): 
        """
        Attempts simulating a vole's movement into a BORDERING chamber (max step size is 1). <destination> must be the id of a chamber. 
        With the goal move in mind, any interactables that control a barrier that the vole will need to pass later in the move are simulated with the hope that the barrier will have a True threshold (e.g. simulate a lever press to open a door the vole will need to eventually go through)
        Only simulates interactables that are related to the goal movement (i.e. they are a barrier, autonomous, or have a parent that is a barrier component)
            SETS the interactable threshold to meet their goal value by calling simulate_vole_interaction 
            GETS the thresholds of each barrier interactable to ensure that it is True before passing
                Allowed Movements ( these are both considered to be a step size of 1 ): 
                    edge -> chamber 
                    chamber -> edge -> chamber 
        Args: 
            destination(int) : id of chamber vole will simulate an attempted move into. destination chamber must be a single move away from the vole's current edge/chamber. 
            validity_check (boolean) : if set to True, then checks if the move is physically valid or not before attempting the move (i.e. can execute a physically invalid movement in order to test error checking in the Control software)
        Returns: 
            (Boolean) : True if the vole reached destination, False otherwise. 
        """
        
        if not self.active: 
            # sim_log(f'(Vole{self.tag}, attempt_move) Vole Inactive. Cannot perform the requested action.')
            return False 
        

        self.event_manager.print_to_terminal(f'(Vole{self.tag}, attempt_move) Attempting move from {self.curr_loc.edge_or_chamber}{self.curr_loc.id} -> Chamber{destination}.')
        # vole_log(f'(Vole{self.tag}, attempt_move) Attempting move from {self.curr_loc.edge_or_chamber}{self.curr_loc.id} -> Chamber{destination}.')

        if self.curr_loc == destination: 
            self.event_manager.print_to_terminal(f'(Vole{self.tag}, attempt_move) Start Location and Goal Location are the same. ( {self.curr_loc.edge_or_chamber}{self.curr_loc.id} -> Chamber{destination} ).')
            # vole_log(f'(Vole{self.tag}, attempt_move) Start Location and Goal Location are the same. ( {self.curr_loc.edge_or_chamber}{self.curr_loc.id} -> Chamber{destination} ).')
        
        if validity_check: 

            if not self.attempt_move_validity_check(destination): 
                # print reason that move is invalid, and then return.
                if self.curr_loc == destination: 
                    # sim_log(f'(Vole{self.tag}, attempt_move) Vole{self.tag} is already in chamber{destination}!')
                    self.event_manager.print_to_terminal(f'(Vole{self.tag}, attempt_move) Vole{self.tag} is already in chamber {destination}!')
                else: 
                    # sim_log(f'(Vole{self.tag}, attempt_move) attempting a move that is not physically possible according to Map layout. Skipping Move Request')
                    self.event_manager.print_to_terminal(f'(Vole{self.tag}, attempt_move) attempting a move that is not physically possible according to Map layout. Skipping Move Request.')

                return False


        # compile a list of interactables we need to pass over to reach destination (include both chamber and edge interactables)
        
        # sort thru chamber interactables, and only add the ones that are related to the goal movement (i.e. they are a barrier, autonomous, or have a parent that is a barrier component)

        # then, we can update the vole's location by using the interactable location info 


        # # # # # # # # # # # # # # # # 
        # retrieve edge between current location and the destination, and check threshold for each of these 
        if self.curr_loc.edge_or_chamber == 'edge': 
            # vole already on edge, retrieve the current edge 
            edge = self.curr_loc 
        else: 
            edge = self.curr_loc.connections[destination]


        # check if we need to do a forwards or backwards traversal of the edge components 
        if destination == edge.v1: 
            # reverse order of the components 
            edge = edge.reverse_components() 
            reversed = True 
        
        else: 
            # converts to list of components
            edge = edge.get_component_list()
            reversed = False 

        #
        # Position for Start of Edge Traversal 
        #

        # position start location along the edge to be where the vole's current position is 
        # if the current position is None, then we will start at the beginning of the list and loop thru all components on edge.
        # if the current position is Not None, traverse along edge until we find edge component, where self.curr_component == component
        
        # Case that vole is in a chamber
        if self.curr_loc.edge_or_chamber == 'chamber': 
            # if vole is in a chamber, then the first step we should take is traversing any chamber components that lie between the vole and the first component in the chamber 
            self.move_to_component(edge[0]) # traverses components in current chamber to reach first component on edge ( this could be a chamber interactable that the edge references tho )


        # vole_log(f'(Vole{self.tag}, attempt_move) vole{self.tag} is on the edge with the following components: {[*(ele.interactable.name for ele in edge)]}')
        
        # remove any components that come before vole's current position 
        i = 0
        while self.curr_component.interactable.name != edge[i].interactable.name: 
            i+=1 
        edge = edge[i::]


        # vole_log(f'(Vole{self.tag}, attempt_move) vole{self.tag} traversing the components: {[*(ele.interactable.name for ele in edge)]}')


        #
        # Edge Traversal ( and Simulating certain interactables that we pass along the way )
        #

        # traverse the linked list containing the edge components 
        for i in range(len(edge)):

            component = edge[i] 

            # check that vole's current interactable position allows us to simulate
            if self.curr_component.interactable.name != component.interactable.name: 
                
                self.event_manager.print_to_terminal(f'(Vole{self.tag}, attempt_move) vole{self.tag} is positioned at {self.curr_component}, so unable to simulate interaction with {component.interactable.name} and cannot complete the attempted move.')
                # sim_log(f'(Vole{self.tag}, attempt_move) vole{self.tag} is positioned at {self.curr_component}, so unable to simulate interaction with {component.interactable.name} and cannot complete the attempted move.')
                return False
            
            else: 
                
                # Simulation for any non-autonomous Component ( because all autonomous components are automatically simulated in the move_next_component function ) 
                interactable = component.interactable
                if not interactable.autonomous: # For a non-autonomous interactable, we care to interact with the interactable if it controls a Parent Interactable.

                    if len(interactable.parents) > 0: 

                        self.simulate_vole_interactable_interaction(interactable) # If the component has control of some parent component (i.e., has at least one parent that is dependent on this interactable's value), then simulate this component! 


                # 
                # vole should pass the interactable it just simulated. 
                # 
                if i+1 < len(edge): 
                    success = self.move_next_component(edge[i+1]) # completed sim for the interactable at edge[i], so move past it.
                    if success is False: 
                        return 
                else: 
                    # On the Final Component on the edge: edge[i]
                    # In order to move past this component, we need to grab the first component from our goal (next) chamber. 
                    goal_edge_components = self.map.graph[destination].get_component_list() 
                    if len(goal_edge_components) > 0: 
                        # if we REVERSED the edge, then we should be grabbing the last component. Otherwise, grab the first element. 
                        if reversed: 
                            nxt_component = goal_edge_components[len(goal_edge_components) -1]
                        else: 
                            nxt_component = goal_edge_components[0]
                    else: 
                        nxt_component = None 
                    

                    # If that chamber is empty, then we can just manually update the voles location to exist in that chamber. 
                    success = self.move_next_component(nxt_component, nxt_edge_or_chmbr_id = destination)
                    if success is False: 
                        return 

                
                # Goal Check After Every Move! # 
                if self.curr_loc == self.map.graph[destination]: 
                    # Goal reached. No need to traverse any further on the edge 
                    # vole_log(f'(Vole{self.tag}, attempt_move) Simulated Vole {self.tag} moved into {self.curr_loc}. Component Location is between ({self.prev_component}, {self.curr_component}')
                    self.event_manager.print_to_terminal(f'Simulated Vole{self.tag} New Location is {self.curr_loc}. Component Location is between ({self.prev_component}, {self.curr_component})')
                    return True 

        self.event_manager.print_to_terminal(f'(Vole.py, attempt_move) Finished iterating through the path but never reached goal. This may mean that there is an issue in the attempt_move funciton.')
        # sim_log(f'(Vole.py, attempt_move) Finished iterating through the path but never reached goal. This may mean that there is an issue in the attempt_move funciton.')
        return False
     
    #
    # Random Vole 
    #   
    def possible_actions(self): 
        """ creates a list of all possible actions a vole can take given the vole's curent location 
            reference: how to add functions to a list, where we will call the function at a later point in time: https://stackoverflow.com/questions/26881396/how-to-add-a-function-call-to-a-list
        Args: 
            None 
        Returns: 
            ( [ tuple ]) : list of tuples, where each tuple contains a function to call followed by the arguments to pass that function
                        -> the 0th position w/in each tuple is the function name, and positions [1:] in the tuple are the arguments
                        -> possible_actions[0][0](*possible_actions[0][1:])
                        -> possible_actions[1][0](*possible_actions[1][1:])
        """
        # NOTE: this function has not been updated, so before use will need fixing!! 

        actions = [ (time.sleep,5)  ]  # initialize with option to do nothing, as this action is always available, independent of the vole's current location

        
        if self.curr_component is not None: 
            # Add Interactable Interaction Options
            try: 
                # Unordered Set in a Chamber; add options to interact w/ any of these interactables
                for i in self.curr_component.interactableSet: 
                    actions.append( (self.simulate_vole_interactable_interaction, i ))
                # Add 

            except AttributeError: 
                # Ordered Component ; add option to interact w/ this interactable
                actions.append( (self.simulate_vole_interactable_interaction, self.curr_component.interactable ))        
        
        ''' else: # current component is None. 
            
            if self.prev_component is None: # Current Edge or Chamber is Empty. 
                pass 
            else: 
                # prev component specified. We are at the end of a locations component list. We can either choose to turn around by navigating back to prev_component, or we can move forward into next chamber/edge 
                actions.append((self.move_next_component(self.prev_component))) # Adds option for vole to turn around! 
        '''
        
        if self.curr_loc.edge_or_chamber == 'chamber': 
            # In Chamber
            # add all move to interactable options
            for i in self.curr_loc.allChamberInteractables: 
                actions.append( (self.move_to_interactable, i) )

            # add all possible "move chamber" options 
            for c_id in self.curr_loc.connections.keys(): # for all of the current chamber's neighboring chambers
                actions.append( (self.attempt_move, c_id) ) # add adjacent chambers to list of possible moves 
        else: 
            # In Edge
            # add all move to interactable options 
            for c in self.curr_loc: 
                actions.append( (self.move_to_interactable, c.interactable) )
            # add all possible chambers to move into 
            actions.append( (self.attempt_move, self.curr_loc.v1) )
            actions.append( (self.attempt_move, self.curr_loc.v2) )

        return actions

    def attempt_random_action(self): 
        """ calls random_action to chose an action at random (or w/ weighted probabilities), and then executes the chosen function 
        """
        
        if not self.active: 
            # sim_log(f'(Vole{self.tag}, attempt_random_action) Vole Inactive. Cannot perform the requested action.')
            return 

        (action_fn, arg) = self.random_action() 
            
        # sim_log(f'(Vole{self.tag}, attempt_random_action) Vole{self.tag} attempting: {action_fn.__name__} (arg: {arg}) ')
        # self.event_manager.print_to_terminal(f'(Vole{self.tag}, attempt_random_action) Vole{self.tag} attempting: {action_fn.__name__} (arg: {arg}) ')

        action_fn(arg) 

    def random_action(self): 
        """ randomly chooses between the following options: 
        1. pass, i.e. vole sits still. Have vole sleep for 1<x<10 number of seconds (where the value of x is also randomly chosen). 
        2. vole interacts w/ an interactable in its chamber (look @ self.map.graph[self.current_loc].interactables to randomly choose an interactable to interact with)
        3. vole attempts to make a move to a random chamber (look @ self.map.graph[self.current_loc].connections to randomly choose a neighboring chamber to choose to)

        Args: 
            None 
        Returns: 
            ( tuple ) : tuple element containing the randomly chosen function and the arguments that will need to passed when executing the that function. ( function, arguments_for_funciton )
        """

        possible_actions = self.possible_actions()
        
        # initialize to a uniform distribution 
        p = 1/len(possible_actions)
        p_dist = {} # the probability distribution for the vole's current state. Updates every function call as the vole changes states. 
        for a in possible_actions:
            p_dist[a] = p 

        ## Check if any of the possible actions were assigned a probability in the vole's action probability distribution. If so, update the probability in p_dist
        for a in possible_actions: 
            if a in self.action_probability_dist.keys(): 
                p_dist[a] = self.action_probability_dist[a]
        
        # Normalize the Probabilities 
        sum_p = sum(p_dist.values())
        norm_p = {key: value/sum_p for key,value in p_dist.items()} # Divide each probability by sum of probabilties to normalize! 
            
        print(norm_p)
        # Use norm_p to choose an action based on assigned probabilities 
        action = random.choices( list(norm_p.keys()), weights =list(norm_p.values()), k = 1 )[0] # [0] takes the action from the tuple 

        return action # returns the ( function, arguments ) tuple of the randomly chosen action

    def set_action_probability(self, action, probability): 

        ''' adjust the probability of Vole taking a certain action, where vole either sleeps, interacts w/ interactables, or moves chambers
        automatically adjusts the probability of the other actions accordingly 
        e.g. if we increase probability of action=sleep to 10%, then we will auto-adjust the probability of action and interactable to 45% each. 

        Args: 
            action(tuple) : tuple where the first element is the function and the second element is the argument that will be passed to that function 
            probability(int) : value that probability of the action being chosen will get set to 
        
        Returns: 
            None 
        '''

        self.action_probability_dist[action] = probability

        


        
    
