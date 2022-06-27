"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 4/6/2022
Description: Class definition for a simulated vole. Contains methods that allow for a vole to move throughout a box and simulate interactions with interactables along the way.

Property of Donaldson Lab at the University of Colorado at Boulder
"""


# Standard Lib Imports 
from itertools import count
import random
from re import I
import time 

# Local Imports 
from ..Logging.logging_specs import sim_log, vole_log
from .Timer import countdown


'''
POTENTIAL TODO: create separate vole class that is only the vole with the attributes and no access to the methods provided for a simulated vole. 
then the Map class will be able to track where a vole currently is within a Map. 
will also be able to throw an error if a vole makes a physically impossible move. (e.g. lever press and then another lever press but no rfid ping for an rfid ping that is inbetween the 2 levers)
'''

'''
SIMULATED VOLE
'''
class Vole: 

    def __init__(self, tag, start_chamber, map): 
        
        self.tag  = tag 
        self.map = map 

        ## Vole Location Information ## 
        self.curr_loc = self.map.get_chamber(start_chamber)
        self.prev_loc = None # object representing the voles previous location.

        # starting position between interactables is between chamber edge or wall and the first interactable in the chamber, if it exists
        self.prev_component = None # last interactable that vole moved away from (so we know the direction of movement)
        try: self.curr_component = self.curr_loc.headval # current interactable the vole is closest to
        except AttributeError: self.curr_component = None # (interactable1, interactable2)

        vole_log(f'VOLE {self.tag} STARTING POSITION BETWEEN INTERACTABLES: {self.prev_component}, {self.curr_component}')


    ##
    ## Simulating Interactable thru setting attribute value or thru function call
    ##





    def pre_simulation_error_checks(self, interactable): 
        ''' checks for a bunch of edge cases to ensure that the called simulation is valid '''
    def simulate_autonomous_interactable(self, interactable): 
        ''' really this just applies to rfids at the moment. '''
        ''' any interactable that is classified as a Barrier interactable AND has no dependents is considered to be autonomous, and can be simulated by this quicker function. (skips all of the dependent loops and things) '''
     

    def at_location_of(self, interactable): 
        ''' 
            Physical Proximity Check: returns True if vole's location is at the current interactable, false otherwise.
            Depends on both the chamber/edge vole is in, as well as where the vole is positioned w/in the chamber. 
        '''
        # Edge Case: Vole can be sitting at component==None. Check for this. 
        if self.curr_component is None: 
            return False 

        if self.curr_component.interactable.name == interactable.name:
            return True 
        else: 
            return False 


        
    def simulate_vole_interactable_interaction(self, interactable): 

        ''' called from vole.attempt_move() in order to simulate a vole's interaction with an interactable '''
        ''' prior to simulation, checks if the requested simulation is valid. returns if not '''

        #
        # Independent vs Dependent check 
        #
        if len(interactable.dependents) > 0: 
            # a fully independent interacable means that it is dependent on the values of its dependents and independent of a vole's actions
            # i.e. it is pointless for the vole to interact directly with it. So return. (Doesn't mean we won't interact and simulate w/ its dependents tho)
            print(f'(Vole.py, simulate_vole_interactable_interaction) {interactable.name} isDependent on dependents, not on a vole interaction.')
            return 

        #
        # Active Check
        #
        if interactable.active is False: 
            print(f'(Vole.py, simulate_vole_interactable_interaction) {interactable.name} is inactive')
            # we don't care to simulate an inactive interactable
            # vole unable to effect the threshold attribute value of an inactive interactable (so threshold value is the same the entire time)
            return 

        #
        # Physical Proximity Check 
        #
        if not self.at_location_of(interactable): 
            print(f'(Vole.py, simulate_vole_interactable_interaction) vole{self.tag} is not at_location_of({interactable.name}). Failed the physical proximity check; cannot simulate.')
            return 




        #
        # Simulate
        #
        if interactable.isSimulation: 

            sim_log( f'(Vole.py, simulate_vole_interactable_interaction) simulating vole{self.tag} interaction with {interactable.name}' ) 
            print(f'(Vole.py, simulate_vole_interactable_interaction) Simulating vole{self.tag} interaction with {interactable.name}')
    
            if hasattr(interactable, 'simulate_with_fn'):
                
                # sets the attributes to values that meet the threshold condition by calling simulate_with_fn 
                interactable.simulate_with_fn(interactable, self.tag)

            else:
                
                # set value using the threshold condition attribute/value pairing 
                threshold_attr_name = interactable.threshold_condition["attribute"]
                # attribute = getattr(interactable, threshold_attr_name) # get object specified by the attribute name

                sim_log(f'(Vole.py, attempt_move) {interactable.name}, threshold attribute: {threshold_attr_name}, threshold value: {interactable.threshold_condition["goal_value"]}')
            
                # manually set the attribute to its goal value so we meet the threshold condition, and trigger the control side to add an event to the threshold_event_queue 
                setattr(interactable, threshold_attr_name, interactable.threshold_condition['goal_value'])
                
                newattrval = getattr(interactable, threshold_attr_name)
                # sim_log(f'{interactable.name}, manual attribute check: {interactable.buttonObj}')
                sim_log(f"(Vole.py, attempt_move) {interactable.name}, attribute result: {newattrval}")
            
            # countdown(5, f'simulating vole{self.tag} interaction with {interactable.name}')
    
        
        else:  # component should not be simulated, as the hardware for this component is present. 
            # assumes that there is a person present to perform a lever press, interrupt the rfid reader so it sends a ping, etc. 
            print ( f'\nif testing the hardware for {interactable.name}, take any necessary actions now.')
            # countdown(10, f'remaining to perform interactions to trigger a threshold event for {interactable.name}')
            
    
    
    ##
    ## Vole Movements
    ##
    def is_move_valid(self, destination): 
        # TESTME
        # attempt_move helper function
        '''Check validity of making a move from voles current location to some destination 
        Does not actually make move/update the voles location, just checks if the move is possible in a single move according to map layout 
        Return True if move is possible, False otherwise 
        '''
        # destination must be a chamber id
        # vole can be currently sitting on an edge or in a chamber 

        if self.curr_loc.edge_or_chamber == 'chamber': 
            if destination in self.curr_loc.connections.keys(): 
                return True # chamber has edge connecting it to destination 
        else: 
            if destination == self.curr_loc.v1 or destination == self.curr_loc.v2: 
                return True # edge is connected to destination chamber
        return False  
    

    def update_location(self, newcomponent=None, nxt_edge_or_chmbr_id = None): 
        ''' 
        updates vole's current component position 
        if current component position is None, then check to see if we need to update the vole's chamber/edge/id location 
        if next component position is None, then see if we can deduce which direction the vole is traveling, so which chamber the vole should now be in
        '''
        
        # make sure that the current chamber/edge/id reflects the newcomponent 
        prev_loc = self.curr_loc 

        if newcomponent is None: 
            if nxt_edge_or_chmbr_id is None: 
                raise Exception(f'(vole.py, update_location) If trying to update vole{self.tag} component location to a newcomponent of None, then must specify the argument for next edge or chamber id that vole should be in!')
            if prev_loc.edge_or_chamber == 'chamber': 
                # grab edge 
                self.curr_loc = self.map.get_edge(nxt_edge_or_chmbr_id)
            else: 
                # grab chamber 
                self.curr_loc = self.map.graph[nxt_edge_or_chmbr_id]

        else: self.curr_loc = self.map.get_location_object(newcomponent.interactable) 
        if prev_loc != self.curr_loc: 
            print(f'Vole {self.tag} traveled from {prev_loc.edge_or_chamber}{prev_loc.id} into {self.curr_loc.edge_or_chamber}{self.curr_loc.id}')
            vole_log(f'\nVole {self.tag} traveled from {prev_loc.edge_or_chamber}{prev_loc.id} into {self.curr_loc.edge_or_chamber}{self.curr_loc.id}')            
            self.prev_loc = prev_loc # update the voles previous location

        self.prev_component = self.curr_component 
        self.curr_component = newcomponent 

        print(f'\n(Vole{self.tag}, update_location) {self.prev_component} to {self.curr_component}\n')
        vole_log(f'\n(Vole{self.tag}, update_location) {self.prev_component} to {self.curr_component}\n')

        location_visual = self.map.draw_location(location = self.curr_loc, voles = [self])
        vole_log(location_visual)

        #
        # BIG CHANGE HERE! LEAVING OFF HERE! MAKE SURE THIS IS OK!
        # This is the Vole PASSING prev_component, meaning that we should reset its threshold to True so watch_for_threshold_event begins looping again to look for more threshold events. 
        if self.prev_component is not None: 
            self.prev_component.interactable.threshold = False # threshold back to False now that we used the threshold for a vole to pass! 
            
    
    def move_to_interactable(self, goal_interactable): 
        '''
        converts interactable to component, and calls the move_to_component function. 
        '''
        if self.curr_component is not None: 
            print(f'(Vole{self.tag}, move_to_interactable) {self.curr_component.interactable}->{goal_interactable}')
            vole_log(f'(Vole{self.tag}, move_to_interactable) {self.curr_component.interactable}->{goal_interactable}')
        else: 
            print(f'(Vole{self.tag}, move_to_interactable) {self.curr_loc.edge_or_chamber}{self.curr_loc.id}(Empty)->{goal_interactable}')
            vole_log(f'(Vole{self.tag}, move_to_interactable)  {self.curr_loc.edge_or_chamber}{self.curr_loc.id}(Empty)->{goal_interactable}')

        interactable_loc = self.map.get_location_object(goal_interactable)
        goal_component = interactable_loc.get_component_from_interactable(goal_interactable)
        return self.move_to_component(goal_component)

    def move_to_component(self, goal_component): 
        ''' 
        compiles list of components that stand between current component and the goal component. 
        Then takes single steps by calling move_next_component until the goal component is reached.
        If at any point move_next_component cannot successfully be completed, meaning vole wasn't able to reach threshold, then we return from this function. 
        Voles location gets updated within the move_next_component function as we take each step. 
        '''
        print(f'(Vole{self.tag}, move_to_component) {self.curr_component} -> {goal_component})')

        # check that goal_component exists 
        if goal_component.interactable.name not in self.map.instantiated_interactables: 
            raise Exception(f'(Vole{self.tag}, move_to_component) goal component {goal_component} does not exist.')
            return False 


        # 
        # Voles Current Component is None: Must first reposition at nearest component before getting the component path!
        #
        while self.curr_component is None: # Loop Until We Find the first Component along our path that we can position the vole at! 
            
            # manually put together the component path by using the start_loc and goal_loc 
            goal_loc = self.map.get_location_object(goal_component.interactable)
            path = self.map.get_edge_chamber_path(self.curr_loc, goal_loc)
            
            # position vole in place that provides more information for us 
            # move to closest new location. If sitting on edge, move to closest chamber. If sitting in chamber, move to closest edge. 
            if self.curr_loc == 'edge': 
                
                if self.map.get_chamber(self.curr_loc.v1) in path: 
                    # check if interactables exist in this chamber. if they do, try to move into that chamber 
                    newloc = self.curr_loc.v1
                    clst = newloc.get_component_list(reverse=True)
                else: 
                    newloc = self.map.get_chamber(self.curr_loc.v2)
                    clst = newloc.get_component_list()

                if clst is not None: 
                    # move to first component 
                    self.update_location(clst[0])
                else: 
                    self.curr_loc = newloc # new chamber is empty. manually move vole there anyways and we will loop again. 
                
            
            else: # current location is a chamber. move to closest edge 

                for (c,e) in self.curr_loc.connections.items(): 

                    if e in path: 
                        # move to new edge 
                        # check if interactables exist on this edge. If they do, make move to that interactable. 
                        if self.curr_loc.id == e.v2: 
                            clst = e.get_component_list(reverse=True)
                        else: 
                            clst = e.get_component_list() 
                    
                    if clst is not None: 
                        # move to first component 
                        self.update_location(clst[0])
                    else: 
                        # new edge is empty, manually move the vole there anyways. 
                        self.curr_loc = e



        #
        # Get list of components in between current location and goal location 
        #
        component_lst = self.map.get_component_path(self.curr_component, goal_component) 
        print( f'(Vole{self.tag}, move_to_component) components between curr_loc and goal_loc:, {[*(c.interactable.name for c in component_lst)]} ')


        # for each component in component_lst, call move_next_component
        for c in component_lst: 

            # move from current component to the next component in the path 

            res = self.move_next_component(c)
            if not res: 
                return 
            

    
        return component_lst

    #def move_multiple_components(self, component): 
        # component is the goal component 
        # does not necessarily have to be a component right next to the voles current location 
        # makes calls to move_next_component to see if we are able to reach the goal component 
        # similar to move_next_component, does not simulate anything along the way. Just positions vole so it can interact with component.


    def move_next_component(self, component, nxt_edge_or_chmbr_id = None): 
        #TESTME
        ''' vole positions itself in front of component. component specified must be a component that only requires a singular position change. 
            this will check the threshold of the voles current component to make sure it is okay for us to move passed it.
            This function Simulates any Autonomous Component! 
                -> if the current component is an rfid, will simulate a ping. Any other component does not get automatically simulated in here. 
            Vole is able to freely pass by non-barrier objects. 
            we check if the voles current component is able to be freely passed. If so, we move and position ourselves at this new interactable. 
            Once returned from this function, we would be able to attempt an interaction with the new component without getting a physical proximity error. 
        '''

        #
        # Edge Cases 
        #
        # inner helper function, getInteractable
        def getInteractable(component): 
            ## try except statement for retrieving components interactable. If component is None, this prevents errors from gettting thrown. ## 
            try: return component.interactable
            except AttributeError: return None

        # Interactables At/Around Vole's Current Position
        curr_interactable = getInteractable(self.curr_component)
        nxt_interactable = getInteractable(self.curr_component.nextval)
        prev_interactable = getInteractable(self.curr_component.prevval)

        # Interactables At/Around Goal Position 
        goal = getInteractable(component)
        if goal is None: 
            goal_nxt = None 
            goal_prev = None
            if nxt_edge_or_chmbr_id is None: 
                raise Exception(f'(Vole.py, move_next_component) if goal component is None, must specify an argument for next_chamber_or_edge_id')
            
        else: 
            goal_nxt = getInteractable(component.nextval)
            goal_prev = getInteractable(component.prevval)

        print(f'(Vole{self.tag}, move_next_component) New Move: {curr_interactable}->{goal}')

        if curr_interactable == goal: 
            print(f'(Vole{self.tag}, move_next_component) Goal interactable and voles current interactable are the same.')
            return True 
        
        # this function requires that we only need to take a single step/move to reach the goal component. Ensure that this is possible. 
        if nxt_interactable != goal and prev_interactable != goal: # if curr_component->nxt.interactable != goal AND currcomponent->prev != goal

            # possible that the next component is on an adjacent edge/chamber to the vole's current location 

            # extra check for scenario that current component is a chamber component
            if goal_prev != curr_interactable and goal_nxt != curr_interactable: # this scenario will happen when chamber interactables are added to an edge 
                # if goal->prev != curr_component ( if the target interactable doesn't link back to our current interactable )
                # if goal->nxt != curr_component ( if the target interactable doesn't link forward to our current interactable )
                # invalid move request 
                raise Exception(f'Vole{self.tag}, move_next_component) only accepts components as arguments that are directly next to the voles location: {self.curr_component}. prev={self.curr_component.prevval}, next={self.curr_component.nextval}. The arugment passed in {component} has prev={component.prevval} and next={component.nextval}')
                print(f'(Vole{self.tag}, move_next_component) only accepts components as arguments that are directly next to the voles location: {self.curr_component}. prev={self.curr_component.prevval}, next={self.curr_component.nextval}. The arugment passed in {component} has prev={component.prevval} and next={component.nextval}')
                return False

            else: 

                pass # valid move requested from a chamber component -> adjacent edge component

        
        #
        # Check that we are able to move past the interactable that vole is currently positioned at ( this only happens for ONE interactable, the current one, each time this function gets called )
        #
    
        #
        # Not Barrier
        #
        if curr_interactable.barrier is False: 

            if curr_interactable.autonomous: 
                
                # interactable is not a barrier, but is autonomous so we simulate to interact with it anyways. Voles location will update even if this is not successful, as this is not a barrier interactable 
                self.simulate_vole_interactable_interaction(curr_interactable) 

            # we can make move freely, update location 
            self.update_location(component, nxt_edge_or_chmbr_id = nxt_edge_or_chmbr_id)
            return True
                


        #
        # Barrier Interactable
        #
        # barrier interactables require that threshold is True. If its not, we can simulate only if the interatcable does NOT have dependents. 
        # i.e. rfids can be simulated in only simple step and ARE simulated within this function, but doors are not. 


        # TRUE Threshold 
        if curr_interactable.threshold is True: 
            # threshold is True, we can freely make move 
            print(f'(Simulation/Vole{self.tag}, move_next_component) the threshold condition was met for {curr_interactable}. Vole{self.tag} making the move from {self.curr_component} to {component}.')
            self.update_location(component, nxt_edge_or_chmbr_id = nxt_edge_or_chmbr_id)
            return True


        # FALSE Threshold
        if len(curr_interactable.dependents) > 0: # cannot simulate if dependent interactions are required first
            # component requires dependent interaction in order to get threshold to become True. This would require other movements, so exiting from this request 
            print(f'(Simulation/Vole{self.tag}, move_next_component) Movement from {self.curr_component}->{component} cannot be completed because {self.curr_component} threshold is False, and would require interactions with its dependents in order to pass.')
            return False 

        elif not curr_interactable.autonomous: # cannot simulate if not autonomous 
            print(f'(Simulation/Vole{self.tag}, move_next_component) Movement from {self.curr_component}->{component} cannot be completed because {self.curr_component} has no dependents that were set to control it, and it is not an autonomous interactable so requires dependents to operate it.')
            return False 
        

        else: 
            # Barrier AND Autonomous
            # OK to simulate! 
            # Interactables that are autonomous and do not have interactables can be simulated in a simple step. 

            self.simulate_vole_interactable_interaction(curr_interactable)
            
            time.sleep(5) 
            
            # After simulating, since this autonomous interactable IS a barrier to vole movements, we must confirm that the threshold is True before allowing the vole to move forward. 
            if curr_interactable.threshold: # recheck the threshold 
                print(f'(Simulation/Vole{self.tag}, move_next_component) threshold met for {curr_interactable}. Vole{self.tag} moving from {self.curr_component} to {component}.')
                # update location 
                self.update_location(component, nxt_edge_or_chmbr_id = nxt_edge_or_chmbr_id)
                return True 

            # Simulation did not successfully meet threshold. 
            else: 
                print(f'(Simulation/Vole{self.tag}, move_next_component) Movement from {self.curr_component}->{component} cannot be completed because after simulating {self.curr_component} the threshold is still False.')
                return False 




    def attempt_move( self, destination, validity_check = True ): 
        ## destination is an integer specifying a CHAMBERID that we want to move to. The New destination Chamber must be a single move away from the vole's current edge/chamber. 
        ''' called by a Vole object ''' 
        ''' attempts to executes a move. if validity_check is set to True, then we check if the move is physically valid or not. '''
        ''' SETTING the interactable's to meet their goal_value by calling simulate_vole_interaction '''
        ''' GETTING the thresholds of each interactable and checking that it is True '''
        ''' if the threshold of any interactable is not True, then we cannot successfully make the move '''

        print(f'(Vole{self.tag}, attempt_move) Attempting move from {self.curr_loc.edge_or_chamber}{self.curr_loc.id} -> Chamber{destination}.')
        vole_log(f'(Vole{self.tag}, attempt_move) Attempting move from {self.curr_loc.edge_or_chamber}{self.curr_loc.id} -> Chamber{destination}.')

        if validity_check: 

            if not self.is_move_valid(destination): 
                # print reason that move is invalid, and then return.
                if self.curr_loc == destination: 
                    sim_log(f'(Vole.py, attempt_move) Vole{self.tag} is already in chamber{destination}!')
                    print(f'(Vole.py, attempt_move) Vole{self.tag} is already in chamber {destination}!')
                else: 
                    sim_log(f'(Vole.py, attempt_move) attempting a move that is not physically possible according to Map layout. Skipping Move Request')
                    print(f'(Vole.py, attempt_move) attempting a move that is not physically possible according to Map layout. Skipping Move Request.')

                return False


        # compile a list of interactables we need to pass over to reach destination (include both chamber and edge interactables)
        
        # sort thru chamber interactables, and only add the ones that are related to the goal movement (i.e. they are a barrier, a dependent related to a barrier, or is autonomous)

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
        # Edge Traversal 
        #

        # position start location along the edge to be where the vole's current position is 
        # if the current position is None, then we will start at the beginning of the list and loop thru all components on edge.
        # if the current position is Not None, traverse along edge until we find edge component, where self.curr_component == component
        
        ## Case that vole is in an empty chamber ( positioned at a component == None )
        if self.curr_component is None: 
            self.move_to_component(edge[0]) # move to the starting component
        ## Case that vole is in a chamber that is connected to the edge we need, but vole is currenlty positioned between 2 interactables that are attached to a diff edge ##
        if self.curr_component.interactable.name not in [*(ele.interactable.name for ele in edge)]: 
            self.move_to_component(edge[0])

        vole_log(f'(Vole.py, attempt_move) vole{self.tag} is on the edge with the following components: {[*(ele.interactable.name for ele in edge)]}')
        
        # begin simulation from the vole's current interactable position. 
        # if self.curr_component is None: 
        #    self.curr_component = edge[0] # first component on edge 
        
        # remove any components that come before vole's current position 
        i = 0
        while self.curr_component.interactable.name != edge[i].interactable.name: 
            i+=1 
        edge = edge[i::]


        vole_log(f'(Vole.py, attempt_move) vole{self.tag} traversing the components: {[*(ele.interactable.name for ele in edge)]}')

        # traverse the linked list containing the edge components 
        for i in range(len(edge)):

            component = edge[i] 
            # print(f'Updated Vole Interactable Location from {self.prev_component} to {self.curr_component} ')

            # check that vole's current interactable position allows us to simulate
            if self.curr_component.interactable.name != component.interactable.name: 
                
                raise Exception(f'(Vole.py, attempt_move) vole{self.tag} is positioned at {self.curr_component}, so unable to simulate interaction with {component.interactable.name}')
                print(self.curr_component, component)
                pass 
            
            else: 
                
                # 
                # Dependency Chain Checks to see if we can allow simulation to occur
                #
                # Simulation for any non-autonomous Component ( because all autonomous components are automatically simulated in the move_next_component function ) 
                #
                interactable = component.interactable
                if not interactable.autonomous:
                    for dependent in interactable.dependents:
                        if dependent.threshold is False: 
                            self.simulate_vole_interactable_interaction(dependent)
                    

                    # # # Double Check This!!! # # # 
                    # # # Dependency Chain # # # 
                    # If the component has no dependents and IS a dependent for a parent component (i.e., has at least one parent), then simulate. 
                    if len(interactable.dependents) == 0 and len(interactable.parents) > 0: self.simulate_vole_interactable_interaction(interactable) # function call which simulates interaction thru function call or changing vals of specified attributes
                    # # # # # # 






                ################################################
                '''     LEAVING OFF HERE!! --> if we are at the end of the edge component traversal, and we need to move into our destination chamber, 
                                        we need to call move_next_component one more time to get that last occurrence of the simulation and get the vole 
                                        to actually enter that chamber, but the "next component" is potentially just None, in the scenario that we are walking into 
                                        an empty chamber. So figure out how to account for this situation. '''
                ################################################

                # 
                # now that simulations have completed, vole should pass the interactable it just simulated. 
                # 
                if i+1 < len(edge): 
                    self.move_next_component(edge[i+1]) # completed sim for edge[i], so move past it.
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
                    self.move_next_component(nxt_component, nxt_edge_or_chmbr_id = destination)

                
                # Goal Check After Every Move! # 
                if self.curr_loc == self.map.graph[destination]: 
                    # Goal reached. No need to traverse any further on the edge 
                    vole_log(f'(Vole.py, attempt_move) Simulated Vole {self.tag} moved into {self.curr_loc}. Component Location is between ({self.prev_component}, {self.curr_component}')
                    print(f'Simulated Vole{self.tag} New Location is {self.curr_loc}. Component Location is between ({self.prev_component}, {self.curr_component})')
                    return 



                #
                # Wait for Control Side Software to react to Simulation of this Interactable
                #
                ################################################
                time.sleep(4)  # Pause to give control side a moment to assess if there was a threshold event 
                ################################################




                #
                # Check if Threshold has been met, in which case Vole completed correct moves to "pass" this interactable
                #

                # self.pass_interactable(interactable)

                # The only thresholds that we actually care about are Barrier Interactables 
                # if we encounter an active, barrier interactable (either a door or rfid) that has a False threshold, then something went wrong. 
                # if
                #  
                '''
                if not component.interactable.barrier: # non-barrier interactables wont directly prevent a voles movement, so we can move past this one no matter what the threshold is 
                    
                    pass 

                else: 
                    
                    # handle barrier components 
                    print(f'(Simulation/Vole{self.tag}, attempt_move) Barrier Component Handling: {component}')

                    if (component.interactable.active and not component.interactable.threshold): # active component with a false threshold
                        # if the threshold condition was not met, then display message to tell user that attempted move was unsuccessful, and return from function. 
                        print(f'(Simulation/Vole{self.tag}, attempt_move) the threshold condition was not met for {component.interactable.name}. Vole{self.tag} cannot complete the move from chamber {self.curr_loc} to chamber {destination}.')
                        return False 

                    ## Inactive Interactable Handling ## 
                    elif component.interactable.active is False: # inactive component has no way of its threshold getting set to true, so we manually check here 
                        # Inactive means that the component is sitting idle, however, we still want to check if it is currently sitting at its threshold goal state, because if it is the vole can successfully make its move. 
                        threshold_attr_name = component.interactable.threshold_condition["attribute"]
                        attribute = getattr(component.interactable, threshold_attr_name) # get object specified by the attribute name
                        
                        if hasattr(component.interactable, 'check_threshold_with_fn'): 
                            attribute = attribute(component.interactable)
                        if attribute == component.interactable.threshold_condition['goal_value']: pass # threshold is True, continue executing function
                        else: return False # threshold is False, return from attempt_move
                    
                    else: 
                        pass # active component with a true threshold. update location and continue to next component
                
                    '''

            
            ## END FOR: Done Simulating Components along the Edge ##


        # All Component Thresholds Reached; loop back thru and reset all the edge components threshold values to False now that we have confirmed an event occurred 
        # print('\n')
        # or component in edge:
            # component.interactable.threshold = False  # reset the components threshold => This should now be getting done in vole.update_location for each interatable as we pass it.     
            # print(f'(Simulation/Vole.py, attempt_move) the threshold condition was met for {component.interactable.name}.') #CHANGE Event: {event}')
        
        


        # Check if the final component landed the vole in the new chamber or not. If it did not, then we should
        # if self.curr_loc.edge_or_chamber == 'edge': # vole is sitting at border between edge and chamber. 

      
        return 



    def make_multichamber_move(self, goal): 
        pass 
     
    def random_move(self): 
        ''' chooses a random neighboring chamber to try to move to '''


    #
    # Random Vole 
    #   
    def possible_actions(self): 
        # NOTE: this function has not been updated, so before use will need fixing!! 

        ''' returns a list of all possible actions a vole can take given the voles current location'''
        # Reference on how to add functions to a list, where we will call the function at a later point in time: https://stackoverflow.com/questions/26881396/how-to-add-a-function-call-to-a-list
        '''
        possible_actions is a list of tuples, where each tuple contains a function to call followed by the arguments to pass that function
        -> the 0th position w/in each tuple is the function name, and positions [1:] in the tuple are the arguments
        -> possible_actions[0][0](*possible_actions[0][1:])
        -> possible_actions[1][0](*possible_actions[1][1:])
        '''

        actions = [ (time.sleep,5)  ]  # initialize with option to do nothing, as this action is always available, independent of the vole's current location

        
        if self.curr_component is not None: 
            # add "interact w/ current component" option 
            actions.append( (self.simulate_vole_interactable_interaction, self.curr_component ))
        
        else: # current component is None. 
            
            if self.prev_component is None: # Current Edge or Chamber is Empty. 
                
                # add surrounding locations as options to move to
                
                if self.curr_loc.edge_or_chamber == 'chamber': 
                    # add surrounding edges and neighboring chambers
                    for (c,e) in self.curr_loc.connections.items(): 
                        actions.append( self.attempt_move, e ) # attempt moving into edge

                else: # current location is an edge 
                    # attempt moving into either chamber that the edge connects
                    actions.append(self.attempt_move, self.curr_loc.v1)
                    actions.append(self.attempt_move, self.curr_loc.v2)
            
            else: 
                # prev component specified. We are at the end of a locations component list. We can either choose to turn around by navigating back to prev_component, or we can move forward into next chamber/edge 

                actions.append((self.move_next_component() ))

        # if we are currently in a chamber, add all possible moves to surrounding components
        

        # add all possible "move chamber" options 
        for adj_chmbr_id in self.map.graph[self.curr_loc].connections.keys(): # for all of the current chamber's neighboring chambers
            actions.append( (self.attempt_move, adj_chmbr_id) ) # add to list of possible moves 
        
        # add all possible "interact w/in chamber interactables" options
        for interactable in self.map.graph[self.curr_loc].interactables: # for all of the interactables in the current chamber
            actions.append( (self.simulate_vole_interactable_interaction, interactable) )
        
        return actions



    def attempt_random_action(self): 
        ''' calls random_action to chose an action at random (or w/ weighted probabilities), and then calls the chosen function '''

        (action_fn, arg) = self.random_action() 
            
        sim_log(f'(Vole.py, attempt_random_action) Vole{self.tag} attempting: {action_fn.__name__} (arg: {arg}) ')
        print(f'(Vole.py, attempt_random_action) Vole{self.tag} attempting: {action_fn.__name__} (arg: {arg}) ')

        action_fn(arg) 



    def random_action(self): 
        ''' Randomly choose between interacting with an interactable or making a move or doing nothing
            Returns the (function, arguments) of the chosen action
        '''

        '''
        randomly choose between the following options: 
        1. pass, i.e. vole sits still. Have vole sleep for 1<x<10 number of seconds. 
        2. vole interacts w/ an interactable in its chamber (look @ self.map.graph[self.current_loc].interactables to randomly choose an interactable to interact with)
        3. vole attempts to make a move to a random chamber (look @ self.map.graph[self.current_loc].connections to randomly choose a neighboring chamber to choose to)
        '''

        possible_actions = self.possible_actions()
        # print('possible actions: ', possible_actions)
        
        # choose action from possible_actions based on their value in the current chamber's probability distribution

        action_probability = self.map.graph[self.curr_loc].action_probability_dist
        if action_probability is not None: 
            # User has set probabilities for the actions, make decision based on this. 
            print('action probability:', action_probability)
            pd = [] # list to contain probabilities in same order of actionobject_probability
            for a in possible_actions: 
                # retrieve each possible actions corresponding probability, and append to an ordered lsit 
                pd.append(action_probability[a])
            
            idx = random.choices( [i for i in range(0,len(possible_actions)-1)], weights = pd, k = 1 )

        
        else: 
            # no probabilities have been set, make decision where every possible action has an equal decision of being chosen
            idx = random.randint(0, len(possible_actions)-1)

        return possible_actions[idx] # returns the ( function, arguments ) of randomly chosen action



    

    def set_action_probability(self, action, probability): 

        ''' adjust the probability of Vole taking a certain action, where vole either sleeps, interacts w/ interactables, or moves chambers
        automatically adjusts the probability of the other actions accordingly 
        e.g. if we increase probability of action=sleep to 10%, then we will auto-adjust the probability of action and interactable to 45% each. 
        '''
        
    
