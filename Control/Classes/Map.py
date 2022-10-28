
"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 4/6/2022
Description: Class definition for Map, a network of Vertices and Edges, where vertices are chambers, and edges are the connections existing between chambers. 
            Objects that represent the hardware (subclasses of InteractableABC) in a box are assigned to either an edge or a chamber within the map. 
            All outside software recieves a Map object, and will go through the Map class in order to interact with any physical hardware.

Property of Donaldson Lab at the University of Colorado at Boulder
"""


# Standard Lib Imports 
from collections import deque
import time
import json 
import os
import threading

# Local Imports 
from .Timer import Visuals, PRINTING_MUTEX
from Logging.logging_specs import control_log, sim_log
from .ModeABC import modeABC 
from . import InteractableABC
from .InteractableABC import lever, door, rfid, buttonInteractable, dispenser, laser, beam
from .Timer import EventManager 

class Map: 
    def __init__(self, config_directory, map_file_name = None ): 
        ''' key is id assigned to vertex: Chamber instance'''
        
        self.graph = {} # { chamberid: chamber instance }

        self.edges = [] # list of all edge objects that have been created ( can also access thru each Chamber instance )

        self.instantiated_interactables = {} # dict of (interactable name: interactable object ) to represent every object of type interactableABC that has been created to avoid repeats
        
        self.voles = [] # list of Vole objects to allow the map to perform basic vole location tracking

        self.event_manager = EventManager()

        self.config_directory = config_directory # directory containing all of the configuration files 

        if map_file_name is not None: 
            self.configure_setup(config_directory + f'/{map_file_name}')
        else: self.configure_setup(config_directory + '/map.json') 

    #
    # Map Visualization Methods
    #
    def draw_map(self, voles=[]): 
        '''prints the chambers, edges, and components to the screen. If this is called from a Simulation, there is an option to pass the voles argument to also print the vole positions in the map'''
        print('\n')
        # * note - do NOT aquire the printing mutex here because that would cause deadlock since both functions we call will also attempt to acquire the mutex
        self.draw_chambers(voles)
        self.draw_edges(voles)
        print('\n')
    
    def draw_helper(self, voles, interactables): 

        # arguments: 
        #   interactables are string representations of interactable names 
        #       - to retrieve the actual object, use the function

        # If in a chamber, then interactables is a list with [ordered components + [ list of unordered component] + ordered components]
        vole_interactable_lst = [] 
        if len(interactables) == 0: 
            # chamber or edge has no interactables. just draw voles 
            for v in voles: 
                vole_interactable_lst.append('Vole'+str(v.tag))
        
        for idx in range(len(interactables)): # For Each Interactable 

            # loop thru interactales w/in the edge or chamber
            i = interactables[idx]

            voles_before_i = [] 
            voles_after_i = []
            
               
            for v in voles: # for each interactable, loop thru the voles w/in the same chamber and check their component location 
                
                if not hasattr(v, 'curr_component'): 
                    # voles are the Map version of the vole class, which does not have info on the component location, only the chamber/edge location 
                    # simply place this vole before i 
                    voles_before_i.append('Vole' + str(v.tag)) 

                elif type(v.curr_component) is self.Chamber.ComponentSet and v.curr_component.interactableSet == i: 
                    # voles current_component.interactableSet is the entire set of Unordered Interactables 
                    # as we loop through interactables, one of the elements should also be the entire set of Unordered Interactables 
                    # so we should look for the direct comparison between i and the interactableSet, as these should be identical.

                    # Vole is standing at an Unordered Component Set 
                    
                    # Figure out which side of Unordered Component Set the vole is on
                    
                    unordered_component = v.curr_component.interactableSet
                    if v.prev_component is not None:
        
                        # check if voles **Previous** location is an Ordered Chamber Interactable:                             
                        if v.prev_component.interactable in interactables: # where interactables is the entire set of Chamber interactables (ordered and unordered)
                            # figure out if this interactable comes before or after the set of Unordered Interactables ( where the vole currently stands )
                            if interactables.index(v.prev_component.interactable) > interactables.index(unordered_component): 
                                voles_after_i.append('Vole'+str(v.tag))
                            else: 
                                voles_before_i.append('Vole'+str(v.tag))

                        else: 
                            # The voles prev location is some interactable on an adjacent Edge. Place Vole Wherever I guess? 
                            voles_before_i.append('Vole'+str(v.tag)) 
                    
                    # Finish looping/printing the Unordered Component Set so we don't reprint the vole everytime 
                    # idx = idx + len(unordered_component) + 1 # skip the index iterator forward 

                else:    
                    # ORDERED COMPONENT: not at the unordered interactable set, we can make a direct comparison between curr_component and i

                    # Set the Current Interactable and the Previous Interactable Values 
                    if type(v.curr_component) is self.Chamber.ComponentSet: 
                        vole_curr_i = v.curr_component.interactableSet
                    else: 
                        vole_curr_i = v.curr_component.interactable
                    if v.prev_component is not None: 
                        if type(v.prev_component) is self.Chamber.ComponentSet: 
                            vole_prev_i = v.prev_component.interactableSet
                        else: 
                            vole_prev_i = v.prev_component.interactable 
                    else: vole_prev_i = None 


                    if vole_curr_i == i: # for every vole located by the current interactable, append to list so we can draw it 

                        # figure out if vole should be drawn before or after the interactable

                        # edge case to avoid out of bounds error...
                        if idx == 0 or idx == (len(interactables)-1): # if vole in first or last position of linked list 
                            if idx == 0: 
                                # vole before interactable
                                voles_before_i.append('Vole'+str(v.tag))
                            else: # case: if idx == (len(interactables)-1)
                                # interactable after vole
                                if v.prev_component != None and vole_prev_i == interactables[idx-1]: 
                                    voles_before_i.append('Vole'+str(v.tag))
                                else: 
                                    voles_after_i.append('Vole'+str(v.tag))
                        
                        elif vole_prev_i == interactables[idx-1]: 
                            # draw v before i 
                            voles_before_i.append('Vole'+str(v.tag)) # append string representation for the vole 
                        else: 
                            # draw i before v 
                            voles_after_i.append('Vole'+str(v.tag)) # append string representation for the vole 

            if type(i) is list: 
                # Interactable Set! 
                # On Each Component, append to vole_interactable_lst in order to make one complete list with ordered voles/interactables 
                vole_interactable_lst.extend(voles_before_i)
                vole_interactable_lst.append(str([o.name for o in i]))
                vole_interactable_lst.extend(voles_after_i)
            else: 
                # Single Interactable
                # On Each Component, append to vole_interactable_lst in order to make one complete list with ordered voles/interactables 
                vole_interactable_lst.extend(voles_before_i)
                vole_interactable_lst.append(str(i))
                vole_interactable_lst.extend(voles_after_i)

                
        # make list of string names rather than the objects 
        return vole_interactable_lst
    
    def draw_chambers(self, voles=[]): 

        if len(voles) == 0: 
            voles = self.voles 


        PRINTING_MUTEX.acquire() # # Aquire Lock for Active Printing Section # # 
        for cid in self.graph.keys(): 
            
            chmbr = self.get_chamber(cid)
            cvoles = []

            # get chamber voles 
            for v in voles: 
                if v.curr_loc == chmbr: 
                    cvoles.append(v)

            
            print(f'-------------------------------------------------------')
            print(f'|                       (C{chmbr.id})                          |')

            # get chamber interactables: Group off into Ordered Components -> [ single list of unordered interactables ] -> Ordered Components
            beforeUnordered = [] 
            afterUnordered = []
            unorderedGroup = [] 
            for idx in range(len(chmbr.allChamberInteractables)): 

                if chmbr.allChamberInteractables[idx] in chmbr.unorderedSet: 
                    unorderedGroup.append(chmbr.allChamberInteractables[idx])
                else: 
                    if len(unorderedGroup) < 1: 
                        beforeUnordered.append(chmbr.allChamberInteractables[idx])
                    else: 
                        afterUnordered.append(chmbr.allChamberInteractables[idx])
            interactables = []
            if len(beforeUnordered) > 0: 
                interactables.extend(beforeUnordered)
            if len(unorderedGroup) > 0: 
                interactables.append(unorderedGroup)
            if len(afterUnordered) > 0: 
                interactables.extend(afterUnordered)



            # chamber interactable ordering is Unordered. Therefore if a vole stands at one of them, it can interact with any of them. 
            # in drawing the vole, only need to worry about if it should come before all of the unordered interactables, or after all of the unordered interactables
            
            # if the voles location is of type Component, then we know that the vole is standing at an Ordered Chamber Interactable. 
            # We should figure out which side of the Unordered (ComponentSet) that this Component exists on.
            vole_interactable_list = self.draw_helper(cvoles, interactables)

            
            def draw_name(name): 
                if len(str(name)) > 50: 
                    name = name[:49] + '-'
                space = 51 - len(str(name)) 
                print(f'|[{name}]' + f"{'':>{space}}" + '|')
            
            
            # Draw! 
            for name in vole_interactable_list: 
                draw_name(name)
                    
                        
            print(f'-------------------------------------------------------')

        PRINTING_MUTEX.release() # # End of Active Printing Section, Release Lock # # 
    
    def draw_edges(self, voles=[]): 

        if len(voles) == 0: 
            voles = self.voles

        edges = self.edges

        PRINTING_MUTEX.acquire() # GET PRINTING LOCK
        for e in edges: 
            
            # Make List of Edge Voles
            evoles = []
            for v in voles: 
                # get voles that are on edge e 
                if v.curr_loc == e: 
                    evoles.append(v)

            # Make List of Edge Interactables        
            interactables = [c.interactable for c in e] # creates list of the interactable names 

            vole_interactable_lst = self.draw_helper(evoles, interactables)

            print(f'({e.v1}) <---{vole_interactable_lst}----> ({e.v2})')
        PRINTING_MUTEX.release() # RELEASE PRINTING LOCK


    def draw_location(self, location, voles=[]): 
        
        # draws the specified location, not the entire map 
        drawing = '' # we return a string that represents all of the things to print ( this way we can write the drawings to the logging files )

        if len(voles) == 0:
            voles = self.voles

        # get voles that are at location 
        loc_voles = []
        for v in voles: 
            if v.curr_loc == location: 
                loc_voles.append(v)
        
        # make list of interactables at location 
        interactables = [] # creates list of the interactable names 
        for c in location: 
            if type(c) is self.Chamber.ComponentSet: 
                # contains interactable list 
                interactables.append(c.interactableSet)
            else: 
                # Component
                interactables.append(c.interactable)
        # interactables = [c.interactable for c in location] 

        vole_interactable_lst = self.draw_helper(loc_voles, interactables)

        PRINTING_MUTEX.acquire() # RETRIEVE PRINTING LOCK 
        if location.edge_or_chamber == 'edge': 
            # draw edge 
            print(f'({location.v1}) <---{vole_interactable_lst}----> ({location.v2})')
            drawing += (f'({location.v1}) <---{vole_interactable_lst}----> ({location.v2})')
        else: 
            # draw chamber
            print(f'_____________\n|   (C{location.id})    |')
            drawing += (f'_____________\n|   (C{location.id})    |')
            def draw_name(name): 
                if len(str(name)) > 8: 
                    name = name[:7] + '-'
                space = 9 - len(str(name)) 
                print(f'|[{name}]' + f"{'':>{space}}" + '|')
                return (f'\n|[{name}]' + f"{'':>{space}}" + '|')
            for name in vole_interactable_lst: 
                drawing += draw_name(name)          
            print(f'-------------')
            drawing += (f'\n-------------')

        PRINTING_MUTEX.release() # RELEASE PRINTING LOCK
        return drawing

    #
    # Summary Tables
    #
    def print_map_summary(self): 
        ''' prints info for each chamber and the edges that it is connected to '''
        for chamber in self.graph.values(): 
            print(chamber)                       # chamber id and adjacent vertices
            for adj in chamber.connections.keys(): 
                edge = chamber.connections[adj]  
                print(edge)                      # edge id and vertices it connects

    
    def print_interactable_table(self): 
        ''' 
        outputs a table of interactables, if they are being simulated or not, and any returned messages that occurred during the setup process 
        '''
        row1 = ['Interactable', 'is Simulation?', 'Returned Messages During Setup (reference Logging Files for error specifics)']
        data = [ row1 ] 
        for i_name in self.instantiated_interactables.keys(): 
            data.append( [i_name, self.instantiated_interactables[i_name].isSimulation, self.instantiated_interactables[i_name].messagesReturnedFromSetup ] )
        Visuals.draw_table(data, cellwidth=20)
    
    def print_dependency_chain(self): 
        '''
        prints table to display the relationships between interactables ( parents and dependency )
        '''
        row1 = ['Interactable', 'Can Control (Parent)']
        data = [row1]
        for i_name in self.instantiated_interactables.keys(): 
            # dnames = ','.join([d.name for d in self.instantiated_interactables[i_name].dependents]) # makes list of names and converts list to string 
            pnames = ','.join([p.name for p in self.instantiated_interactables[i_name].parents]) 
            data.append( [i_name, pnames] )
        Visuals.draw_table(data, cellwidth=40)
        


    #
    # Getters and Setters 
    #        
    def instantiate_interactable_hardware( self, name, type ): 

        ''' anytime that an interactable is added (either to a chamber or to an edge), first a call to this function is made. 
            called from configure_setup in 2 places: 
                (1) first called to instantiate objects that are added to chamber.interactables 
                (2) second called to instantiate objects that are added to chamber.connections[adjacent_chmbr_id].components
            based on the object type and object id, instantiates a new interactableABC subclass object
            the specified "type" is a string representation of an existing interactableABC subclass, specified in the map configuration file
        '''


        # Edge Case: if type is not a valid subclass of interactableABC, raise Exception
        try: getattr(InteractableABC, type)
        except: raise Exception(f' unknown interacatable type: {type} ')


        # Edge Case: if an object of the same type and id has already been created
        if name in self.instantiated_interactables.keys(): raise Exception(f'the interactable {name} already exists. please assign unique names to the interactables.')


        # Edge Case: missing configuration file for either this type of interactable
        config_filepath = None 
        filename = type+'.json'
        for root, dirs, files in os.walk(self.config_directory): 
            if filename in files: 
                config_filepath = os.path.join(root,filename)
        if config_filepath is None: raise Exception(f'there is no configuration file for {type} in {self.config_directory}')
            
        #
        # Read in the config file for this type of interactable
        #
        f = open( config_filepath ) # opening json file 
        
        data = json.load( f ) # returns json object as a dictionary 

        f.close() # close file

        # edge case: configuration file does not have specifications for an object with this name
        try: objspec = data[name]
        except: raise Exception(f'there is no entry for {name} in the {type} configuration file, {filename}')

        #
        # Instantiate New Interactable
        # 
        if type == 'door': 
            
            # get door w/ <id> from the door config file 
            try: new_obj = door(ID=objspec['id'], threshold_condition = objspec['threshold_condition'], hardware_specs = objspec['hardware_specs'], name = name, event_manager = self.event_manager) # instantiate door 
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')

        elif type == 'rfid': 

            try: new_obj = rfid(ID=objspec['id'], threshold_condition = objspec['threshold_condition'], name = name, event_manager = self.event_manager) # ASK: also need to pass in rfidQ?? confused on where this comes from though. 
            except Exception as e: raise Exception(f'there was a problem instantiating the object: {name}: {e}')

        elif type == 'lever': 
            
            try: new_obj = lever(ID=objspec['id'], threshold_condition = objspec['threshold_condition'], hardware_specs = objspec['hardware_specs'], name = name, event_manager = self.event_manager)
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')

        elif type == 'buttonInteractable': 
            
            try: new_obj = buttonInteractable(ID = objspec['id'], threshold_condition = objspec['threshold_condition'], hardware_specs = objspec['hardware_specs'], name = name, event_manager = self.event_manager)
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')

        elif type == 'dispenser': 

            try: new_obj = dispenser(ID = objspec['id'], threshold_condition = objspec['threshold_condition'], hardware_specs = objspec['hardware_specs'], name = name, event_manager = self.event_manager)
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')
        
        elif type == 'laser': 
            print(data.keys())
            print('\n')
            print(objspec)
            try: dutycycle_definitions = data['dutycycle_definitions']
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')
            
            try: new_obj = laser(ID = objspec['id'], threshold_condition = objspec['threshold_condition'], hardware_specs = objspec['hardware_specs'], name = name, dutycycle_definitions = dutycycle_definitions, event_manager = self.event_manager)
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')

        elif type == 'beam': 
            
            try: new_obj = beam(ID = objspec['id'], threshold_condition = objspec['threshold_condition'], hardware_specs = objspec['hardware_specs'], name = name, event_manager = self.event_manager)
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')
        
        else: 

            raise Exception(f'interactableABC does not have a subclass {type} implemented in InteractableABC.py')


        # dynamically set any attributes that can be optionally added to an interactable's configurations
        if "check_threshold_with_fn" in objspec['threshold_condition'].keys(): 
            setattr(new_obj, 'check_threshold_with_fn', eval(objspec['threshold_condition']['check_threshold_with_fn']) ) # function for checking if the threshold condition has been met
        # FISH --> delete once i confirm its ok to delete all dependents stuff!
        # if "dependents" in objspec.keys(): 
        #     setattr( new_obj, 'dependent_names', objspec['dependents'] ) # interactable that the threshold is dependent on. Prevents a vole from directly interacting with the interactable, as the presence of any dependents specifies that the vole must directly interact with the dependents to trigger a threshold event.
        if "parents" in objspec.keys(): 
            setattr( new_obj, 'parent_names', objspec['parents']) # interactables can call functions to control their parent behavior (e.g. if we want lever1 to control door1, then add door1 as lever1's parent )
        
        self.instantiated_interactables[name] = new_obj  # add string identifier to list of instantiated interactables
        
        # activate the object so it begins watching for threshold events --> can potentially reposition this to save CPU energy since each interactable gets its own thread. 
        # be careful/don't add the activation statement to the interactable's __init__ statements, because then we get a race condition between this function which sets "check_threshold_with_fn" and the watch_for_threshold_event which gets the "check_threshold_with_fn" value.  

        # new_obj.activate()
        return new_obj

    
    #
    # Handling Instantiated Interacables: Activate, Deactivate, and Reset all Interactables
    #
    def reset_interactables(self): 
        ''' loops thru all instantiated interactables and resets them (emptys their threshold event queue '''
        for (n,i) in self.instantiated_interactables.items() :
            i.reset() 
    def activate_interactables(self): 
        ''' loops thru all instantiated interactables and ensures that all are actively running '''
        
        control_log('\n\n')
        for (n,i) in self.instantiated_interactables.items(): 
            if not i.active: 
                i.activate()
        control_log('\n')
        
    def deactivate_interactables(self, clear_threshold_queue = True): 
        ''' loops thru all instantiated interactables and sets each of them to be inactive. Called in between modes '''
        
        control_log('\n')

        for (n,i) in self.instantiated_interactables.items(): 
            i.deactivate()
        if clear_threshold_queue: 
            self.reset_interactables() # empties the interactables threshold queue
        
        control_log('\n')

    
                
        
            


    #
    # Map Configuration 
    #
    def validate_chmbr_interactable_references(self, new_edge, all_edge_components): 
        '''argument should be list of the actual interactable objects that are w/in a chamber'''
        '''loop thru the edges chmbr_interactable_lst and return True if the ordering of the references reflects the ordering provided in the chamber config''' 

        control_log(f'(Map.py, validate_chmbr_interactable) validating configurations for edge{new_edge.id}')
        print(f'(Map.py, validate_chmbr_interactable) validating configurations for edge{new_edge.id}')

        ## Before Adding Edge Components, Perform a One Time Check to Validate the Chamber Interactables That Are Optionally Specified on the Edge:      
            # argument is entire dictionary of edge components provided in the configuration file 
            # returns list of only the references to chamber_interactables that are provided w/in the dictionary 
        chmbr_interactable_names = [] 
        for i in all_edge_components: 
            if 'chamber_interactable' in i.keys(): 
                    chmbr_interactable_names.append(i['chamber_interactable'])
        
        if len(chmbr_interactable_names) < 1: return # no chamber_interactables referenced along this edge 

        # edge case: references an interactable that based on the component ordering provided in the initial chamber, skips over an interactable. 
        # In order to fix this: the chamber interactable ordering should be changed, or the components that stand inbetween the interactable 
        # trying to get added should also be added as chamber_interactables to preserve ordering.  
       
        
        # for each interactable: if chmbr_interactable is at the first or last index of its own chamber, this is a valid entry 
        # if chmbr_interactable is NOT at the first or last index of its own chamber, then we must ensure that all 
        # interactables between itself and the interactable that "bridges" with the edge (will be either the first or last indexed interactable)
        # are present in the chmbr_interactable_lst 
        i_obj_lst = [] # convert chmbr_interactable_lst from string interactable names => actual interactable objects
        for i_name in chmbr_interactable_names: 
            i = self.instantiated_interactables[i_name]
            i_obj_lst.append(i)
        
        # separate the list by chamber id 
        chmbr1references = []
        chmbr2references = [] 
        chmbr1id = i_obj_lst[0].edge_or_chamber_id # retrieve one of the two chamber ids that could possibly be referenced w/in the list
        chmbr2id = -1
        for i in i_obj_lst: 
            # separate chmbr_interactable_lst into their different chambers. We will perform two diff checks for two diff chambers referenced by the chmbr interactables 
            if i.edge_or_chamber_id == chmbr1id: 
                # throw error if there is a chamber 1 chamber_interactable AFTER we have already encountered a chamber 2 interactable, as this is not preserving the order of chmbr1->edge->chmbr2
                if len(chmbr2references) > 0: 
                    raise Exception(f'(Map.py, validate_chmbr_interactable_references) configuration for Edge{new_edge.id} Components is invalid because trying to place a chamber{i.edge_or_chamber_id}, {i} after specifying chamber{chmbr2references[0].edge_or_chamber_id} interactable(s): {chmbr2references}. Please ensure that map.json configs are correct and run again.')
                chmbr1references.append(i)
            else: 
                chmbr2id = i.edge_or_chamber_id
                chmbr2references.append(i)



        # figure out which chamber interactable is the "bridge" interactable for the current edge 
        # if chmbr1obj.id == new_edge.v1: 
        #    chmbr1references = [ele for ele in reversed(chmbr1references)]
        chmbr1obj = self.get_chamber(chmbr1id)
        chamber1_interactable_lst = [interactable for interactable in chmbr1obj.allChamberInteractables]
        chamber1_bridge_interactable = chmbr1references[0]
        print(f'edge {new_edge.id} references the following interactables assigned to chamber {chmbr1id}:', [ ele.name for ele in chmbr1references ] )
        # Ensure that the Bridges are on an End of the Chamber Interactables
        if chamber1_bridge_interactable != chamber1_interactable_lst[0] and chamber1_bridge_interactable != chamber1_interactable_lst[len(chamber1_interactable_lst) -1 ]: 
                raise Exception(f'(Map,py, validate_chmbr_interactable_references) {chamber1_bridge_interactable.name} must be on the edge of the chamber, or edge{new_edge.id} must include the chamber_interactables inbetween {chamber1_bridge_interactable.name} and the edge of the chamber (in the direction of where edge{new_edge.id} exists)')

        if chmbr2id > 0: 
            chmbr2obj = self.get_chamber(chmbr2id)
            chamber2_interactable_lst = [interactable for interactable in chmbr2obj.allChamberInteractables]
            chamber2_bridge_interactable = chmbr2references[len(chmbr2references)-1]
            print(f'edge {new_edge.id} references the following interactables assigned to chamber {chmbr2id}:', [ *(ele.name for ele in chmbr2references) ] )
            # Ensure that the Bridges are on an End of the Chamber Interactables
            if chamber2_bridge_interactable != chamber2_interactable_lst[0] and chamber2_bridge_interactable != chamber2_interactable_lst[len(chamber2_interactable_lst)-1]: 
                raise Exception(f'(Map,py, configure_setup, validate_chmbr_interactable_references) {chamber2_bridge_interactable.name} must be on the edge of the chamber, or edge{new_edge.id} must include the chamber_interactables inbetween {chamber2_bridge_interactable.name} and the edge of the chamber (in the direction of where edge{new_edge.id} exists)')
        

        # ensure that the chmbr1references and chmbr2references match the ordering and items of the componentlst 
        # index into the lst to get the matching lst, and then compare 
        for counter in range(2):
            counter += 1
            if counter == 1: 
                chmbrRefs = chmbr1references
                chmbrinteractables = chamber1_interactable_lst
                chmbrbridge = chamber1_bridge_interactable
                # print(f'----edge{new_edge.id} references to chamber{chmbr1id}------')
            else: 
                if len(chmbr2references) > 0: 
                    chmbrRefs = chmbr2references 
                    chmbrinteractables = chamber2_interactable_lst
                    chmbrbridge = chamber2_bridge_interactable
                    # print(f'-------edge{new_edge.id} references to chamber{chmbr2id}--------')
                else: 
                    break 


            startidx = chmbrinteractables.index(chmbrRefs[0]) # get indexes of the first and last element in our chmber interactable lst 
            endidx = chmbrinteractables.index(chmbrRefs[len(chmbrRefs)-1])
            if (endidx < startidx): 
                # raise Exception(f'(Map,py, configure_setup, validate_chmbr_interactable_references) chamber_interactables on edge{new_edge.id} must match the order given in chamber{chmbrRefs[0].edge_or_chamber_id}. Please reverse/change the order of {[*(c.name for c in chmbrRefs)]} in map.json to align according to the chambers ordering: {[*(ele.name for ele in chmbrinteractables )]} **Note that this ordering should match the physical ordering of the chamber as we move from the chamber into the edge that we are providing chamber_interactables for!**')
                e = endidx 
                endidx = startidx 
                startidx = e
            interactable_lst = chmbrinteractables[startidx:endidx+1] 
            
            # print(f'checking for references to: {[*(c.name for c in chmbrRefs)]}' ) 
            # print(f'comparing with: {[*(ele.name for ele in interactable_lst )]}')

            # check that lists are the same 
            
            if interactable_lst != chmbrRefs and interactable_lst != [ele for ele in reversed(chmbrRefs)]: 
                raise Exception(f'(Map,py, configure_setup, validate_chmbr_interactable_references) configuration for Edge{new_edge.id} Components are invalid because chamber interactables {[*(c.name for c in chmbrRefs)]} are not an ordered subset to what is specified in chamber{chmbrRefs[0].edge_or_chamber_id} interactables: {[*(ele.name for ele in chmbrinteractables )]}')

    def configure_setup(self, config_filepath): 
        ''' function to read/parse configuration file map.py and set up map accordingly '''

        # opening JSON file 
        f = open(config_filepath)

        # returns json object as a dictionary 
        data = json.load(f) 

        # closing JSON file
        f.close() 

        # Iterate thru to chambers list to initalize the diff chambers and their interactables 
        print('Adding Interactables To Chambers....')
        for chmbr in data['chambers']: 
            
            # instantiate new chamber 
            new_c = self.new_chamber( chmbr['id'] )
            
            for i in chmbr['components']: # loop thru chamber components specified in the json file 
                
                # instantiate interactable hardware 
                new_i = self.instantiate_interactable_hardware( i['interactable_name'], i['type'] )

                # assign the interactable to a chamber object
                new_c.new_interactable( new_i )
                
            '''except Exception as e: 
                    print(f"Ran into an issue when trying to instantiate the interactable object: {i['interactable_name']}")
                    print('Error Message: ', e)
                    print(f'would you like to continue running the experiment without instantiating this interactable? If yes, I wont be aware of any interactions a vole may have with it. If no, I will exit the experiment immediately.')
                    ans = input('input (y/n) \n')
                    if ans == 'n': exit() '''
        
        # Iterate thru edges list to make connections between the chambers 
        print('Adding Interactabes to Edges.....')
        for edge in data['edges']: 

            if edge['type'] == 'shared': 
                
                new_edge = self.new_shared_edge(edge['id'], edge['start_chamber_id'], edge['target_chamber_id'])


                self.validate_chmbr_interactable_references(new_edge, all_edge_components=edge['components'])


                for i in edge['components']:
                    
                    ## Chamber Interactable Checks ## 
                    # edge components may point to an already instanted interactable that is in a chamber
                    # denoted with the key "chamber_interactable" 
                    ref = False
                    if 'chamber_interactable' in i.keys(): 
                        # reference to an already instanted interactable 

                        # edge case: reference to a nonexistent interactable
                        try: i = self.instantiated_interactables[i['chamber_interactable']]
                        except KeyError as e: 
                            raise Exception(f'(Map.py, configure_setup) chamber_interactable is trying to reference a nonexistent interactable {i["chamber_interactable"]}. KeyError: {e}')
                        
                        # edge case: reference to an edge interactable (can only reference a chamber interactable)
                        if i.edge_or_chamber == 'edge': raise Exception(f'(Map.py, configure_setup) invalid chamber_interactable: cannot reference {i.name} as a chamber_interactable, because it is on an edge interactable (edge{i.edge_or_chamber_id})')

                        # edge case: reference to a chamber that does not touch the current edge 
                        if i.edge_or_chamber_id != new_edge.v1 and i.edge_or_chamber_id != new_edge.v2: raise Exception(f'(Map.py, configure_setup) invalid chamber_interactable: {i.name} is in chamber{i.edge_or_chamber_id} which is not connected to edge{new_edge.id}: {new_edge}') 
                        

                        # Change interactable to become an ORDERED Interactable that is referenced by an Edge! 
                        ref = True 
                        chamber_obj = self.get_chamber(i.edge_or_chamber_id)
                        chamber_obj.set_as_ordered(interactable = i, edge = new_edge) # function removes the interactable from the Chamber's unordered set and adds to the ordered set, assigning it to the speicifed edge object
                        
                        # create the new component on the edge that contains a reference to a chamber interactable
                        new_component = new_edge.new_component(i, chamber_interactable_reference = True)
                        

                    # Edge Component is not a reference to a chamber interactable. Instantiate interactable hardware along the edge normally
                    if not ref: 
                        new_i = self.instantiate_interactable_hardware( i['interactable_name'], i['type'] )
                        new_edge.new_component( new_i )
            



            ## Not Implemented: Unidirectional Edges ## 
            '''
            elif edge['type'] == 'unidirectional': 

                new_edge = self.new_unidirectional_edge

                for c in edge['components']: 

                    # Unidirectional Edges bring up special case where we may need to reuse/point to an already instantiated interactable.
                    # i.e. the components along the edge may have already been instantiated if a unidirectional edge connecting the same 2 chambers was already created.
                    # If this is the case, then we need to point to the existing component instead of instantiating a new one.  
            '''
        
        # loop back thru all chambers and call function that will finalize/set a component for containing the chamber's Unordered Interactables 
        for (cid, chamber) in self.graph.items(): 
            chamber._set_unordered_component()

        # FISH)) DELETE ME)) self.set_dependent_interactables()
        self.set_parent_interactables() 


        # Finally, create Vole objects! 
        self._setup_voles(data = data)

        # Lastly, set attributes for convenient access to all of the hardware components 
        for (name, interactable) in self.instantiated_interactables.items(): 

            setattr( self, name, interactable )

    
    def set_parent_interactables(self): 
        
        # if an interactable specified a "parent" in its configuration file, then it gets an attribute "parent_names" which serves as a string representation of the interactable
        # after all objects have been instantiated, we now want to assign the actual interactable objects rather than just their string representation
        
        for i_name in self.instantiated_interactables:
            i = self.instantiated_interactables[i_name]
            if hasattr(i, 'parent_names'): 
                # has dependents we need to add 
                for pname in i.parent_names:
                    try: 
                        i.parents.append(self.instantiated_interactables[pname]) # assign parent its new dependent 
                        # self.instantiated_interactables[dname].parents.append(i) # assign dependent its new parent

                    except KeyError as e: 
                        print(e)
                        print(f' specified an unknown interactable {e} as a parent for {i.name}. Double check the config files for {e} and for {i.name} to ensure they are correct, and ensure that {e} was added in the map config file as well.')
                        ans = input(f' would you like to carry on the experiment without adding {e} as a parent for {i.name}? (y/n)')
                        if ans == 'n': exit()
        
                delattr(i, 'parent_names')  # delete the dependent_names attribute since we don't need it anymore 
          


    def get_chamber(self, id): 
        ''' returns chamber object with specified id '''
        for cid in self.graph.keys(): 
            if cid == id: 
                return self.graph[cid]
        return None

    def new_chamber(self, id): 
        ''' new Chamber instantiated and added to graph'''
        if id < 0: 
            # NOTE --> TESTME! ensure that this does not cause any problems. 
            # skip adding this chamber to graph, as it is just for storing override button components 
            newChamber = self.Chamber(id)
            return newChamber

        if self.get_chamber(id) is not None: 
            raise Exception(f'chamber with id {id} already exists')
        
        newChamber = self.Chamber(id)
        self.graph[id] = newChamber
        return newChamber


    def new_shared_edge(self, id, v1, v2, components=None):
        ''' single Edge object that is shared by both vertices. Ordering of linked list will require checking the vertex indices ''' 
        if not all(v in self.graph.keys() for v in [v1, v2]): raise Exception(f'Could Not Create Edge: one or both of the chambers has not been created yet, so could not add edge between them.')
        if self.get_edge(id): raise Exception(f'An edge with the id {id} already exists, could not create edge.')
        
        newEdge = self.Edge(id, v1, v2,'shared')
        self.graph[v2].connections[v1] = newEdge 
        self.graph[v1].connections[v2] = newEdge
        self.edges.append(newEdge)
        return newEdge
        

    def new_unidirectional_edges(self, id, v1, v2, components=None): 
        ''' creates 2 new Edges for connecting 2 chambers -- each has a different Edge instance tho, so components may differ '''
        if not all(v in self.graph.keys() for v in [v1, v2]): raise Exception(f'Could Not Create Edge: one or both of the chambers has not been created yet, so could not add edge between them.')
        if self.get_edge(id): raise Exception(f'An edge with the id {id} already exists, could not create edge.')
        
        edge1 = self.Edge(id,v1,v2,"unidirectional")
        self.graph[v1].connections[v2] = edge1 # add edges to vertices' adjacency dict 
        
        rev_id = int(str(id)[::-1]) # reverse the id for the edge going the reverse direction 
        edge2 = self.Edge(rev_id, v2, v1, "unidirectional")
        self.graph[v2].connections[v1] = edge2
        
        self.edges.extend([edge1, edge2]) # add new edges list of map edges
        return (edge1, edge2)

    
    def get_edge(self, edgeid): 
        # sort thru chamber edges and locate edge with <id> 
        for cid in self.graph.keys(): # for all chambers stored in graph
            chamber = self.graph[cid] # get Chamber object
            for adj_id in chamber.connections.keys(): # for all of its adjacent vertices 
                if chamber.connections[adj_id].id == edgeid: # check if vertex has edge w/ that id 
                    return chamber.connections[adj_id]

        return None

    def get_location_object(self, interactable): 
        ''' returns chamber or edge object that the component exists in '''
                
        if interactable.edge_or_chamber == 'chamber': 

            return self.get_chamber(interactable.edge_or_chamber_id)
        
        else: 

            return self.get_edge(interactable.edge_or_chamber_id)
    
    
    #
    # Path Finding Methods
    #
    def get_chamber_path(self, start, goal): 
        '''pass in only the integer ids to specify the start/goal'''
        '''Returns list of sequential chambers to move from start->goal chamber'''

        # print(f'(Map, get_chamber_path) {start}->{goal}')

        if (start < 0 or goal < 0): 
            if start == goal: 
                return [start]
            else: 
                print(f'(Map, get_chamber_path) paths do not exist for isolated chambers. No path connecting chamber{start}->chamber{goal}')
            

        def trace_path(previous, s): #helper function for get_path 
            # recursive trace back thru previous dictionary to get path 
            if s is None: return [] 
            else: return trace_path(previous, previous[s])+[s]
        
        # check that start and end chamber exist 
        if start not in self.graph.keys() or goal not in self.graph.keys(): 
            raise Exception(f'chamber {start} and/or chamber {goal} does not exist in the map, so cannot find path')
        
        # BFS 
        frontier = deque([start]) # chambers already explored 
        previous = {start: None} # keeps track of the chamber that came before current chamber 
        if start == goal: return [start]
        while frontier: 
            chmbr_id = frontier.popleft() 
            for adj in self.graph[chmbr_id].connections: 
                if (adj not in previous) and (adj not in frontier): 
                    frontier.append(adj) 
                    previous[adj] = chmbr_id # set new chamber's parent chamber 
                    # Goal Check 
                    if adj == goal: 
                        return trace_path(previous, adj)
    

    def get_path(self, start, goal): 
        '''Must pass in the actual edge/chamber objects to specify the start and goal'''
        '''Returns list of sequential CHAMBERS to move to in order to reach a chamber that is adjacent to edge '''
        '''basically just a little parent function to get_chamber_path '''

        # print(f'(Map, get_path) args: start={start}, goal={goal}')

        if(start.id < 0 or goal.id < 0) and start != goal: # check for if either start or goal is an island chamber (and also not the same island chamber)
            # chambers or edges with an id that is a negative number represents an "island" chamber, where the chamber has no edges that connects it to other chambers, so it is impossible for a vole to reach 
            raise Exception(f'(Map, get_path) no paths exist from {start}->{goal}') 
            

        def edge_to_chamber_path(start, goal): 
            p1 = self.get_chamber_path(start.v1, goal.id)
            p2 = self.get_chamber_path(start.v2, goal.id)
            if len(p1) < len(p2): return p1 
            else: return p2

        def chamber_to_edge_path(start, goal): 
            # check the edges vertices that it connects. we want to get the chamber path that it takes to reach each of these chambers and then return the shortest path
            p1 = self.get_chamber_path(start.id, goal.v1) # path to vertex/chamber1 that edge touches
            p2 = self.get_chamber_path(start.id, goal.v2) # path to vertex/chamber2 that edge touches
            if len(p1) < len(p2): return p1 
            else: return p2 
        
        def edge_to_edge_path(start, goal): 
            # get path starting from both chambers 
            p1 = chamber_to_edge_path(self.graph[start.v1], goal) 
            p2 = chamber_to_edge_path(self.graph[start.v2], goal)
            if len(p1) < len(p2): return p1 
            else: return p2      

        def chamber_to_chamber_path(start,goal): 
            return self.get_chamber_path(start.id, goal.id)   


        ### Figure Out Which function from above we should call! ###

        if type(start) == self.Edge:
            if type(goal) == self.Edge:
                # edge->edge 
                print("edge to edge!")
                return edge_to_edge_path(start,goal)
            else: 
                # edge->chamber
                return edge_to_chamber_path(start,goal)
        
        else: 
            if type(goal) == self.Chamber: 
                # chamber->chamber
                return chamber_to_chamber_path(start,goal)
            else: 
                # chamber->edge
                return chamber_to_edge_path(start,goal)


    def get_edge_chamber_path(self, start, goal): 
        # (f'(Map, get_edge_chamber_path) args: start={start}, goal={goal}')
        '''Returns list of sequential EDGE AND CHAMBER objects that fall between the start Location and the goal location (inclusive list, so start and goal will also be apart of list)'''

        if start == goal: 
           return goal 
        
        chamberIDpath = self.get_path(start, goal) # returns list of chamber ids that we can follow along to get from start->goal

        # convert the chamberIDpath to chamber and edge objects 
        path = [] 
        if type(start) == self.Edge: 
            path.append(start)
        
        
        for i in range(len(chamberIDpath)): # loop thru chamber path
            
            cid = chamberIDpath[i] # for each chamber id 

            # retrieve chamber object corresponding with the chamber id 
            c = self.graph[cid]

            # append chamber object to path 
            path.append(c)

            # if there is another chamber specified in the path, then we know that there is an edge to add 
            # look one chamber forward if it exists
            if (i+1) < len(chamberIDpath): 
                e = c.connections[chamberIDpath[i+1]] # grab nxt edge and append 
                path.append(e)
            
            i += 1 
        
        # if goal specified was an edge, append the edge object now 
        if type(goal) == self.Edge: 
            path.append(goal)
        

        return path 


    def get_component_path_within_edge(self, edge, start_component, goal_component): 
        '''
        basically just figures out if we need to reverse components on an edge or not. 
        Using the start_component, it finds the quickest path to reach goal_compoennt
        both components must exist on the same edge. 
        '''
        if start_component not in edge or goal_component not in edge: 
            raise Exception(f'(Map.py, get_component_path_within_edge) Invalid Arguments: {start_component} and {goal_component} must be on {edge} to get a path within a single edge')
        edge_component_list = edge.get_component_list()
        if edge_component_list.index(start_component) > edge_component_list.index(goal_component): 
            # reverse is true! 
            return edge.get_component_list(reverse = True)
        else: 
            return edge_component_list

    def get_component_path(self, start_component, goal_component ): 
        ''' 
        arguments should be of component type 
        function first gets list of sequential edge and chamber components that fall between the start Location and the goal location
        then, it removes any components that fall outside of the start_compoennt and goal_component and returns this list. 
        returns list of INTERACTABLE TYPE! 
        '''
        
        control_log(f'(Map, get_component_path) {start_component}->{goal_component}')
            
        # Error Check: Incorrect Argument Type 
        if type(start_component) is not self.Edge.Component and type(start_component) is not self.Chamber.ComponentSet: 
            control_log(f'(Map, get_component_path) arguments must be of type Component, but recieved start_component of type {type(start_component)} and goal_component of type {type(goal_component)}')
            raise Exception(f'(Map, get_component_path) arguments must be of type Component, but recieved start_component of type {type(start_component)} and goal_component of type {type(goal_component)}')
        elif type(goal_component) is not self.Edge.Component and type(goal_component) is not self.Chamber.ComponentSet: 
            control_log(f'(Map, get_component_path) arguments must be of type Component, but recieved start_component of type {type(start_component)} and goal_component of type {type(goal_component)}')
            raise Exception(f'(Map, get_component_path) arguments must be of type Component, but recieved start_component of type {type(start_component)} and goal_component of type {type(goal_component)}')


        # convert components to their edge or chamber location objects (get_location_object requires interactable arguments rather than the component)
        if type(start_component) is self.Chamber.ComponentSet: 
            start_interactable = start_component.interactableSet[0] # any component from the unordered set 
            start_loc = self.get_location_object(start_interactable)
        else: 
            start_interactable = start_component.interactable
            start_loc = self.get_location_object(start_interactable)
        if type(goal_component) is self.Chamber.ComponentSet: 
            goal_interactable = goal_component.interactableSet[0]
            goal_loc = self.get_location_object(goal_interactable)
        else: 
            goal_interactable = goal_component.interactable
            goal_loc = self.get_location_object(goal_interactable)


        #
        # edge case: components are in the same lcoation 
        #
        if start_loc == goal_loc: 
            # get full component list of location 
            component_path = start_loc.get_component_list() 
            # print(' (Map.py, get_component_path) unedited version of the Component List we will traverse: ', component_path)

            # convert to interactable version 
            interactable_path = []
            for c in component_path: 
                if type(c) is self.Chamber.ComponentSet: 
                    interactable_path.extend([i for i in c.interactableSet])
                else: 
                    interactable_path.append(c.interactable)

            startIdx = interactable_path.index(start_interactable)
            goalIdx = interactable_path.index(goal_interactable)      
            # based off of the start/goal values, ensure that locations components mimic this ordering. Reverse the component list if they dont. 
            if startIdx > goalIdx: # lst is currently ordered with goal -> other components -> start, and we want to reverse that. 
                # reverse lst! 
                component_path = start_loc.get_component_list(reverse=True)
        

        #
        # Components Specified Exist in 2 different Locations # 
        #
        else: 
            # we have at least two locations in our path, meaning loc_path contains at least 1 chamber and 1 edge 
            component_path = [] 

            # get path of edge/chamber objects that makeup the path 
            loc_path = self.get_edge_chamber_path(start_loc, goal_loc)

            def checkEdgeReversal(loc1, loc2, finalLocation = False): 
                ''' loc1 is always the current location, and then loc2 is the location that comes directly after or before the current location. 
                    if loc2 is the lcoation that comes directly before loc1 in the component path, we set finalLocation=True, because the only time we will do this is when we have reached the final location.
                '''
                if finalLocation: 
                    current = loc1 
                    prev_loc = loc2 
                    # we need to look backwards to figure out if we should reverse components or not. 
          
                    if current.edge_or_chamber == 'edge': # final location is an edge
                        # if the final location is an edge, then simply check which chamber we came from.
                            # if we came from the chamber v1, then reverse is False. Else, reverse is true. 
                        if prev_loc.id == current.v1: 
                            reverse = False 
                        else: 
                            reverse = True 

                    else: # final location is a chamber  
                        # if final location is a chamber, then check the previous edge. 
                            # if the final chamber is stored as v2 for the previous edge, then reverse is False. Else, reverse is true 
                        if prev_loc.v2 == current.id: 
                            reverse = False 
                        else: 
                            reverse = True 

                else: 
                    start = loc1
                    nxt_loc = loc2

                    if start.edge_or_chamber == 'chamber': 
                        # first location is a chamber, second location is an edge 
                        if start.id == nxt_loc.v1: 
                            reverse = False 
                        else: 
                            reverse = True 

                    else: 
                        # first location is an edge, second location is a chamber 
                        if nxt_loc.id == start.v2: 
                            reverse = False
                        else: 
                            reverse = True 
                return reverse
            # End Of Reversal Check Function 


            # loop through the location path. At each location, retrieve the components and append to the component path 
            # for each component on an edge: 
            #   edges have a simple way of figuring out how to order the components, as we will either reverse or not reverse them. 
            #   check reversal for every edge location that we encounter. 
            #   check if its interactable has already has been added to the component path. 
            #   If yes, remove the existing component and replace it (at the same index) with the edge version.
            # for each component in a chamber: 
            #   chambers do not have a simple way of figuring out how to order the components, as we have a mix of ordered and unordered components. 
            #   if the current chamber is coming after an edge, then check the most recently added component to see if it points us to a bridge?? 
            #   see if we have a bridge component present to indicate the direction of components. 
            #   if the current chamber is coming before an edge, then check to see if we have a bridge component present connecting with that edge to indicate a direction of components.
            #       perform this check_for_bridge by examining the first and last interactable along the edge and seeing if any of them are an interactable assigned to the current chamber.
            #       if it is, then locate this 
            #            
            #   If we have no bridge components with the previous or next edge, then that means we should ONLY add the chamber's UnorderedComponent to the component_path. 
            #
            #   check if its interactable has already been added to the component path. If yes, do not add this component. 


            for i in range(len(loc_path)): 
                
                if goal_component in component_path: 

                    break # when we reach the goal component we can exit the loop 

                loc = loc_path[i] # set current location
                curr_loc_components = [] # reset current location components to blank

                if type(loc) is self.Edge: 
                    if (i+1) <= (len(loc_path)-1): 
                        reverse = checkEdgeReversal(loc, loc_path[i+1])
                    else: 
                        # final location in the location path
                        reverse = checkEdgeReversal(loc, loc_path[i-1], finalLocation = True)
                       
                    curr_loc_components = loc.get_component_list(reverse = reverse) 
                
                else: 
                    #
                    # Current Location is a Chamber
                    #

                    # if we are on first location (i==0), then look forward to next edge to see if we can figure out a direction. 
                    # if we are on the final location, then ensure we traverse far enough into the chamber to reach our goal_component
                    # if we are on neither the first or final location, we only need to add the Unordered Set in the chamber, 
                    #    since we can ensure that the prev and nxt edge will handle adding the components that they reference                    
                    
                    if i == 0: 
                        # First Location 
                        # if the start_component is apart of the unorderedComponent, then just add the unorderedComponent 
                        # Otherwise, first add the start_component + [Ordered Components in between start and unordered Component] + [Unordered Component]
                        if type(start_component) is self.Chamber.ComponentSet: 
                            
                            # start component is part of the Unordered Set in the Chamber! 
                            # add the unordered set and continue
                            curr_loc_components.append(loc.unorderedComponent)
                        
                        else: 

                            # Start Component is an Ordered Component in the chamber!
                            e = loc.get_edge_for_ordered_interactable(start_component.interactable)
                            if e not in loc_path: 
                                print('FIRST LOCATION IS A CHAMBER, START COMPONENT IS ORDERED, ITS EDGE NOT IN LOCATION PATH')
                                # our start component is on an Edge that is not in the loc_path, meaning we need to manually retrieve this edge's component list
                                #       , add these components, and then add the unordered Component before continuing. 
                                reverse = checkEdgeReversal(e, loc)
                                curr_loc_components.extend(e.get_component_list(reverse = reverse)) # add everything from the edge that references our start_component
                                curr_loc_components.append(loc.unorderedComponent) # add unordered component set in the chamber

                            else: 
                                # our start component is on an Edge that IS referenced by an edge in loc_path ( presumably the next edge ), so we do not need to add anything. 
                                pass 

                            
                    elif(i == len(loc_path) -1 ):  # final location!
                        
                        #
                        # Final *Chamber* Location
                        #
 
                        if goal_component in component_path: 
                            
                            # meaning the goal_component came before the Chamber's Unordered Component in the path, so we have added everything we need to.
                            break 
                        
                        else: 
                            
                            # have yet to reach the goal_component, implying that we will cross over the Chamber's Unordered Set in order to reach the goal component!
                            curr_loc_components.append(loc.unorderedComponent)
                        
                        
                        if type(goal_component) is not self.Chamber.ComponentSet: 

                            # Goal component is an Ordered Component ( referenced by an edge ) that has not yet been added to the component path 
                            # Add the unordered component, and then add the entire next edge that references the goal component, since we will widdle it down in the final step anyways
                            
                            nxt_edge = loc.get_edge_for_ordered_interactable(goal_component.interactable)
                            reverse = checkEdgeReversal(loc, nxt_edge)
                            curr_loc_components.append(nxt_edge.get_component_list(reverse = reverse)) # adds everything including our goal_component
                            

                    else: 
                        # current chamber is neither the first nor last location in our loc path, so we only need to add the unordered component ( since we know the surrounding edges in the loc_path will add all necessary ordered components )
                        curr_loc_components.append(loc.unorderedComponent)
                                
                    
                component_path.extend(curr_loc_components)
                

            print('RAW COMPONENT PATH: ', *(str(c) for c in component_path))



        ## FINAL STEP: Widdle Down the component path! Get rid of anything that falls outside of the index of [start::goal] or [goal::start]
        interactable_path = []
        for c in component_path: 
            if type(c) is self.Chamber.ComponentSet: 
                interactable_path.extend([i for i in c.interactableSet])
            else: 
                interactable_path.append(c.interactable)

        start_idx = component_path.index(start_component)
        goal_idx = component_path.index(goal_component)   
        
        if start_idx > goal_idx: 
            print(f'(Map.py, get_component_path) COMPONENT PATH: {[*(str(ele) for ele in component_path[goal_idx:start_idx+1])]}')

            return component_path[goal_idx:start_idx+1]
        
        print(f'(Map.py, get_component_path) COMPONENT PATH: {[*(str(ele) for ele in component_path[start_idx:goal_idx+1])]}')
        return component_path[start_idx:goal_idx+1] 

            
        ##########

        '''
                        # Figure out if a bridge component exists between the chamber and the next edge. 
                        # RECURSIVE CALL 
                    something = False
                    if something: # added this in for spacing reason! 
                        print([str(c) for c in curr_loc_components]) 
                        print('RECURSIVE CALL SECTION')
                        nxt_edge = loc_path[i+1]
                        within_chmbr_list = None
                        for comp in nxt_edge: 
                            if comp.interactable.edge_or_chamber == 'chamber' and comp.interactable.edge_or_chamber_id == loc.id: 
                                within_chmbr_list = self.get_component_path(start_component, goal_component = comp)
                                break 
                        if within_chmbr_list is None: 
                            # no bridge component for this edge. Only add the unordered set. 
                            curr_loc_components = loc.unorderedComponent
                        else: 
                            print('\n\n(Map.py, get_component_path) RECURSIVE CALL RETURNED: ', ([str(c) for c in within_chmbr_list]))

                    '''

        '''print('Current Location Components: ', curr_loc_components)
                # get the interactable version of the component path we are iterating/appending to
                interactable_path = []
                for c in component_path: 
                    if type(c) is self.Chamber.ComponentSet: 
                        interactable_path.extend([i for i in c.interactableSet])
                    else: 
                        interactable_path.append(c.interactable)

                # get the interactable version of the current location's components
                curr_loc_interactables = []
                for c in curr_loc_components: 
                    if type(c) is self.Chamber.ComponentSet: 
                        curr_loc_interactables.extend([i for i in c.interactableSet])
                    else: 
                        curr_loc_interactables.append(c.interactable)
                # print('(Map.py, get_component_path) CURR LOCATION COMPONENTS:', [*(str(ele) for ele in curr_loc_components)])
                if loc.edge_or_chamber == 'chamber': 

                    for c in curr_loc_components: # loop thru the chamber's components
                        if c in component_path: 
                            # LEAVING OFF HERE!
                        # if c.interactable in interactable_path: 
                            pass # skip component if that interactable is already in path (meaning it got added by an edge reference)
                        else: 
                            component_path.append(c) 
                else: # location is an edge! 
                    for c in curr_loc_components: # loop thru edge's components 
                        if c.interactable in interactable_path: # interactable already in path (meaning it got added by a chamber, and now we are encountering an edge reference to that same interactable)
                            # REPLACE this interactable added by a chamber component with the edge's version of the interactable!! 
                            interactable_to_replace =  self.get_chamber(c.interactable.edge_or_chamber_id).get_component_from_interactable(c.interactable) # retrieve the chamber component paired with this interactable
                            idx = component_path.index(interactable_to_replace)
                            print(f'\n\n(Map.py, get_component_path) REPLACING {interactable_to_replace} with the edge component version. Before path: {[*(str(c) for c in component_path)]}')
                            component_path = component_path[:idx] + [c] + component_path[idx+1:]
                            print(f'(Map.py, get_component_path) After Path: {[*(str(c) for c in component_path)]}')
                        else: 
                            component_path.append(c)
            
            
        ''' 
        # full component path has been compiled. Final step is to remove elements that fall outside of the range of the start_component and goal_component 
        # since start or goal components may have been chamber component where we added the edge version of the component, we should check for the index by interactable rather than by component 
                        # get the interactable version of the component path we are iterating/appending to
        # print('(Map.py, get_component_path) FULL COMPONENT PATH: ', str(*(component_path)))

                    



    class ChamberComponents: 
        ''' 
        class for traversing and locating the UNORDERED components in a chamber 
        contains list of InteractableABC objects. 
        '''
        
        


    # 
    # Chamber -- vertices in the graph
    #  
    class Chamber: 
        
        def __init__(self,id): 

            super().__init__() 

            self.id = id 

            self.edge_or_chamber = 'chamber'
            
            self.connections = {} # adjacent chamber: a single Edge object which points to linked list of components

            self.action_probability_dist = None # probabilities are optional; must be added after all interacables and chamber connections have been added. can be added thru function 'add_action_probabilities'

            # 
            # Interactable Tracking 
            # 
            self.allChamberInteractables = [] # Entire Set of both unordered and ordered interactables assigned to the chamber 
            
            self.unorderedSet = [] # interactables that are not referenced by an edge, and therefore are considered to be unordered

            self.orderedSet = [] # Interactables referenced by an Edge! key: Edge that references the interactable, value: list of interactable objects that have a component object on that edge to specify ordering

            #
            # Component Tracking 
            #
            self.unorderedComponent_isSet = False # gets set to true after _set_unordered_component() is called!
            self.unorderedComponent = self.ComponentSet() # Contains the Unordered Components of a chamber! attribute set after map finishes setting up all chambers/edges and their interactables. 
            
            self.edgeReferences =  {} # Interactables referenced by an Edge! key: Edge that references the interactable, value: list of interactable objects that have a component object on that edge to specify ordering
            # # doesn't make sense for a chamberSet to have nextval and prevval, cuz they may have more than one connection to surrounding edges



        class ComponentSet: 
            ''' 
            creates a singular ComponentSet instance to contain all of the unordered interactables 
            '''
            def __init__(self, interactableSet=[]): 
                self.interactableSet = interactableSet # access to the actual object that represents a hardware component
            def __str__(self): 
                return str([i.name for i in self.interactableSet]) 
            def __iter__(self): 
                for i in self.interactableSet: 
                    yield i
            def set_interactables(self, interactableSet): 
                self.interactableSet = interactableSet
            def remove(self, interactable): 
                self.interactableSet.remove(interactable)
        


        def _set_unordered_component(self): 
            ''' 
            called after all edges/chambers have been set with their interactables 
            updates the attribute self.unorderedComponent to contain the unorderedSet of interactables
            '''
            self.unorderedComponent.set_interactables(self.unorderedSet)
            self.unorderedComponent_isSet = True 


        def get_component_for_ordered_interactable(self, interactable): 
            ''' returns the Component object that was created by the edge when the edge referenced a chamber interactable '''
            for (edge, interactablelst) in self.edgeReferences.items(): 
                if interactable in interactablelst: 
                    return edge.get_component_from_interactable(interactable)
        
        def get_edge_for_ordered_interactable(self, interactable): 
            '''returns the Edge object that contains a Component that references a chamber interactable'''
            for (edge, interactablelst) in self.edgeReferences.items(): 
                if interactable in interactablelst: 
                    return edge 


        def get_component_list(self, reverse = False ): 
            ''' 
            returns all components w/in chamber in a list format 
            this will be in the format [ ordered components + [inner list of unordered components] + ordered components ]
            '''
            component_list = []
            for idx in range(0, len(self.allChamberInteractables)): 
                i = self.allChamberInteractables[idx]
                if i not in self.unorderedSet: 
                    component_list.append(self.get_component_for_ordered_interactable(i))
                    idx += 1
                else:  # interactable apart of ordered set 
                    if self.unorderedComponent in component_list: 
                        continue # skips ahead to next iteration of loop
                    component_list.append(self.unorderedComponent)
                
            if not reverse: 
                return component_list
            else: 
                return [ele for ele in reversed(component_list)]


        def __str__(self): 
            return 'Chamber: ' + str(self.id) + ', adjacent: ' + str([x for x in self.connections]) + ', interactables: ' + str([i.name for i in self.allChamberInteractables])
        
        def __iter__(self): 
            # Edge Referenced Components -> Unordered Components -> More Edge Referenced Components
            unordered_done = False 
            for i in self.allChamberInteractables: 
                if i in self.orderedSet: 
                    yield self.get_component_for_ordered_interactable(interactable = i)
                elif not unordered_done: 
                    yield self.unorderedComponent
                    unordered_done = True  
        
        def get_component_from_interactable(self, interactable): 
            '''simply return the Chamber object'''
            # figure out what Set the interactable belongs in, and return the Component accordingly 
            
            if interactable in self.unorderedSet: 
                return self.unorderedComponent
            
            elif interactable in self.orderedSet: 
                # retrieve the Ordered Component for this interactable and return 
                return self.get_component_for_ordered_interactable(interactable)
            
            else: 
                return None # interactable does not exist in this chamber

        def set_as_ordered(self, interactable, edge): 
            ''' 
            Called during setup whenever we encounter a "chamber_interactable" referenced on an Edge! 
            Interactable will no longer be an "unordered" interactable, but is now treated as an ordered edge interactable
            removes interactable from the Chamber's unordered interactable set, and moves it to the ordered interactable set
            assigns it to the specified edge in the edgeReferences dictionary
            '''
            control_log(f'(Map.py, set_as_ordered) Edge referencing a chamber object! Setting {interactable.name} as an ordered component in {edge.id}')
            
            self.unorderedSet.remove(interactable)
            self.orderedSet.append(interactable)

            if interactable in self.unorderedComponent.interactableSet: 
                self.unorderedComponent.remove(interactable)

            # Add to Dictionary where we store edge -> [list of chamber interactables referenced on this edge]
            if edge in self.edgeReferences.keys(): 
                self.edgeReferences[edge] += [interactable]
            else: 
                self.edgeReferences[edge] = [interactable]

            # print('Unordered Set: ', [i.name for i in self.unorderedSet])
            # print('Ordered Set', [i.name for i in self.orderedSet])    
            #for (k,v) in self.edgeReferences.items():
            #    print(f'Edge{k.id}->Chamber{self.id} References: {k} ---> {[i.name for i in v]}')


        def remove_interactable(self, interactable): 
            '''removes interactable from the Chamber's ComponentSet'''
            # TESTME
            if interactable not in (self.allChamberInteractables): # nothing to remove
                return  


            # remove the interactable from all relevant sets and Components
            if interactable in self.unorderedSet: 
                self.unorderedSet.remove(interactable)
                self.unorderedComponent.remove(interactable)
            
            else: 
                # interactable in ordered set! Must also delete this component from the edge
                for (edge, interactable_list) in self.edgeReferences.items(): 
                    if interactable in interactable_list: 
                        e = edge # grab edge that interactable was assigned to
                        new_i_list = interactable_list.remove(interactable)
                        self.edgeReferences[edge] = new_i_list # remove interactable from the edge references list
                        e.remove_component(interactable) # remove component from the edge 
                
                self.orderedSet.remove(interactable)
                
                
            self.allChamberInteractables.remove(interactable)
            
        ''' Adding Interactable to Chamber's Interactable Set! Defaults to an Unordered Chamber Interactable ( to make an ordered one, we must reference the interactable from an edge ) '''
        def new_interactable(self, newinteractable): 
            
            # check that this interactable doesn't already exist in the chamber 
            if newinteractable in self.allChamberInteractables: 
                raise Exception(f'(Map.py, Chamber.new_component) {newinteractable.name} not added because this component has already been added to the chamber')

            newinteractable.edge_or_chamber = 'chamber'
            newinteractable.edge_or_chamber_id = self.id 

            # Add Interactable to the Chamber's Interactable Sets! --> Defaults to the Unordered Set 
            self.allChamberInteractables.append(newinteractable) # set of all interactables 
            self.unorderedSet.append(newinteractable) # set of unordered chamber interactables 
            if self.unorderedComponent_isSet: 
                # unordered component was already assigned the unordered set. manually add this new unordered component 
                self.unorderedComponent.interactableSet.append(newinteractable)

        
        #
        # (for Simulation Use Only) Probability Tracking: tracking probabilities of some Action-Object getting chosen by a Vole when a simulated vole is told to make random decisions
        #
        def add_action_probabilities( self, actionobj_probability_dict ): 
            
            ''' function for extensive error checking before assigning the probabilities to the possible actions from the current chamber '''

            # Check that probabilities have been set for every value (the +1 is for the time.sleep() option)
            if len(actionobj_probability_dict) != len(self.interactables) + len(self.connections) + 1: 
                raise Exception(f'must set the probability value for all action objects (the connecting chambers and the interactables) within the chamber, as well as the "sleep" option (even if this means setting their probability to 0) ')


            # check that the specified action-objects are accessible from the current chamber, and of type Chamber, Interactable, or 'sleep'
            p_sum = 0
            for (k,v) in actionobj_probability_dict.items():  
                if isinstance(k, type(self)): # type: Chamber 
                    if k.id not in self.connections.keys(): 
                        raise Exception(f'attempting to set the probability of moving to chamber{k.id}, which is not adjacent to chamber{self.id}, so cannot set its probability.') 
                elif isinstance(k, type(self.interactables[0])): # type: Interactable 
                    if k.id not in self.interactables: 
                        raise Exception(f'attempting to set the probability of choosing interactable {k.id} which does not exist in chamber {self.id}, so cannot set its probability.')
                elif k != 'sleep': # only remaining option is type=='sleep', throw error if it is not
                    raise Exception(f'{k} is an invalid object to set a probability for')
                else: 
                    p_sum += v


            # check that the probability values sum to 1
            if p_sum != 1: 
                raise Exception(f'the probabilities must sum to 1, but the given probabilities for chamber{self.id} summed to {p_sum}')
            

            self.action_probability_dist = actionobj_probability_dict

    


    #
    #
    #                    e d g e s 
    #
    #
    # Linked List for Interactable Ordering w/in Edge 
    #
    class EdgeComponents: 
        ''' Class for Traversing and Locating the ORDERED Components on an Edge. 
        Manages Linked Lists that preserves order of interactable components.
        Possible to add info on the "edges" that link two components. i.e. can assign values so we can identify where a vole sits relative to interactables w/in the linked list. 
        '''

        def component_exists(self, interactable): 
            # beginning at headval, traverses linked list to find component. Returns True if exists, False otherwise 
            if (self.headval.interactable == interactable): 
                return True
            c = self.headval
            while(c.nextval): 
                c = c.nextval 
                if c.interactable == interactable: 
                    return True
            return False

        def get_interactable_from_component(self, name): 
            '''traverses linked list and returns object with specified name'''
            if not (self.headval): 
                # Edge does not contain any components (i.e. no interactables) 
                return None 

            if (self.headval.interactable.name == name): 
                return self.headval.interactable
            
            c = self.headval
            while(c.nextval):
                c = c.nextval 
                if c.interactable.name == name: 
                    return c.interactable
            return None # a component with an interactable with name does not exist in linked list

        def get_component_list(self, reverse = False ): 
            ''' returns all components w/in edge or chamber in a list format '''
            if not reverse: 
                return [c for c in self] 
            else: 
                return self.reverse_components() 

        def get_interactable_list(self, reverse = False): 
            ''' returns all interactables w/in edge or chamber in a list format '''
            components = self.get_component_list(self, reverse)
            return [c.interactable for c in components]


        def get_component_from_interactable(self, interactable): 
            ## helper function for adding components into the linked list ## 
            '''beginning at headval, traverses linked list to find component. Returns None if it does not exist'''
            
            if not (self.headval): 
                # Edge does not contain any components 
                return None 

            if (self.headval.interactable == interactable): 
                return self.headval 

            c = self.headval
            while(c.nextval): 
                c = c.nextval 
                if c.interactable == interactable: 
                    return c 
            return None # c does not exist in linked list 


        def new_component_after(self, newinteractable, previnteractable): 
            '''instantiates and adds new component directly after the specified interactable (so can be in middle of linked list if desired)''' 

            if (self.component_exists(newinteractable)) is True: raise Exception(f'{newinteractable} already exists on this edge')
            if previnteractable is not None: 
                if (self.component_exists(previnteractable)) is False: raise Exception(f'{previnteractable} must already exist on this edge to add a component that follows it, so could not add {newinteractable}')

            newComp = self.Component(newinteractable) # Instantiate New Component object to get added into linked list

            # if previous component set to None, then make new component the new head of Linked List
            if previnteractable == None: 
                if self.headval is None: 
                    del newComp
                    # linked list is empty, use new_component() to add the first component
                    return self.new_component(newinteractable)
                else: 
                    # make newinteractable the new head of the linked list 
                    prevhead = self.headval 
                    self.headval = newComp
                    self.headval.nextval = prevhead
                    return self.headval
            
            else: 
                prevComp = self.get_component_from_interactable(previnteractable) # retrieve prevComp and check that it exists 
                nxtComp = prevComp.nextval

                # once prevcomponent is located, instantiate new component and update the vals of the previous component, current component, and next component
                newComp.prevval = prevComp 
                newComp.nextval = nxtComp

                # update the components on either side of newComp to reflect changes
                prevComp.nextval = newComp 
                nxtComp.prevval = newComp 
                return newComp
        
        def remove_component(self, interactable): 
            ''' updates linked list to remove specified interactable '''

            remComp = self.get_component_from_interactable(interactable)
            if remComp==None: raise Exception(f'{interactable} does not exist, so cannot remove it from linked list') 

            prevComp = remComp.prevval
            nxtComp = remComp.nextval

            if self.headval == remComp: 
                # update the head value of linked list 
                self.headval = nxtComp 
                nxtComp.prevval = None 
            elif nxtComp == None: 
                # remComp is the last element of the linked list
                prevComp.nextval = None 
            else: 
                prevComp.nextval = nxtComp 
                nxtComp.prevval = prevComp 

            del remComp 
            return 
        

        def reverse_components(self): 

            ''' returns list of components in the reverse order that they were added in '''
            # instantiates new Component and adds to end of linked list

            if self.headval is None: 
                return self.headval 
            
            component = self.headval 
            while(component.nextval):
                component = component.nextval # list traversal to get last component in linked list 
            
            # last element reached. This item will be the first one in our list. Then traverse back to start of linked list, adding the elements as we go. 
            reversed_lst = [component]
            while(component.prevval): 
                component = component.prevval
                reversed_lst.append(component)

            return reversed_lst

        #
        # Component Object: subclass of OrderedComponents. Used for implementing Linked List 
        #
        class Component: 
       
            def __init__(self, interactable): 
                self.interactable = interactable # access to the actual object that represents a hardware component
                self.nextval = None
                self.prevval = None
            
            def __str__(self): 
                return str(self.interactable.name)

    #
    # Edges -- linked list for storing Components
    # 
    class Edge(EdgeComponents):    
        def __init__(self, id, chamber1, chamber2, type=None): 
            
            # Identifying Edge w/ id val and the chambers it connects 
            self.id = id 
            self.v1 = chamber1 
            self.v2 = chamber2
            self.type = type 
            self.edge_or_chamber = 'edge'

            self.headval = None # points to first component in linked list



        def __str__(self): 
            interactables = [c.interactable.name for c in self] # list of the interactable object's Names -- (concatenation of type+ID)
            if self.type=='shared': 
                return 'Edge ' + str(self.id) + f', connects: {self.v1} <--{interactables}--> {self.v2}'

            return 'Edge ' + str(self.id) + f', connects: {self.v1} --{interactables}---> {self.v2}'


        ''' Methods for Traversing and Locating Components on an Edge '''
        def __iter__(self): 
            component = self.headval
            while component is not None: 
                yield component
                print 
                component = component.nextval


        ''' Adding Component to an Edge'''
        def new_component(self, newobj, chamber_interactable_reference = False): 
            # instantiates new Component and adds to end of linked list
            # newobj is of interactable type 
            if chamber_interactable_reference is False: 
                newobj.edge_or_chamber = 'edge'
                newobj.edge_or_chamber_id = self.id
            else: 
                # Chamber Interaactable Reference! 
                    # referencing an existing chamber interactable, which is stored in the chamber's interactableSet
                    # Leaving the interactable the same (so it is still assigned to the same chamber), we need remove the interactable from the Chamber's unorderedSet and add it to the Chamber's edgeReferences 
                    # and then create a new Edge Component that will store this interactable

                # (FISH) we have already removed the interactable from the ComnponentSet, so just need to create the new, regular Component version of the interactable
                #### if we wanna connect the Component to the ComponentSet, and the ComponentSet with its surrounding Components, add logic here!

                # newComp = newobj 
                pass 

            newComp = self.Component(newobj) # Component to store the interactable called newobj

            if self.headval is None: 

                self.headval = newComp
                return newComp
            
            component = self.headval 
            while(component.nextval):
                component = component.nextval # list traversal to get last component in linked list 
                if component.interactable == newComp.interactable:
                    del newComp 
                    raise Exception(f'{component.interactable.name} not added because this component has already been added to the edge')
            
            
            component.nextval = newComp # update list w/ new Component
            newComp.prevval = component # set new Component's previous component to allow for backwards traversal     
            return newComp



    class Vole: 

        ''' allows map to perform some basic vole tracking '''

        def __init__(self, tag, start_chamber, map): 
            
            self.tag  = tag 

            ## Vole Location Information ## 
            self.curr_loc = map.get_chamber(start_chamber)
            self.prev_loc = None # object representing the voles previous location.

        
    def _setup_voles(self, data): 
        # uses data in the map config file to create voles and set their start location
        for v in data['voles']: 
            self.new_vole(v['tag'], v['start_chamber'])

    def update_vole_location(self, tag, loc): 
        ''' retrieves the vole object specified by <tag> and updates its location to <loc> '''
        v = self.get_vole(tag)
        v.prev_loc = v.curr_loc 
        v.curr_loc = loc 

    def get_vole(self, tag): 
        # searches list of voles and returns vole object w/ the specified tag 
        for v in self.voles: 
            if v.tag == tag: return v  
        return None

    def new_vole(self, tag, start_chamber): 
        
        ''' creates a new Vole object and adds it to the list of voles. Returns Vole object on success '''

        # ensure vole does not already exist 
        if self.get_vole(tag) is not None: 
            sim_log(f'vole with tag {tag} already exists')
            print(f'you are trying to create a vole with the tag {tag} twice')
            input(f'Would you like to skip the creating of this vole and continue running the experiment? If no, the experiment will stop running immediately. Please enter: "y" or "n". ')
            if 'y': return 
            if 'n': exit() 
        
        # ensure that start_chamber exists in map
        chmbr = self.get_chamber(start_chamber) 
        if chmbr is None: 
            control_log(f'trying to place vole {tag} in a nonexistent chamber #{start_chamber}.')
            print(f'trying to place vole {tag} in a nonexistent chamber #{start_chamber}.')
            print(f'existing chambers: ', self.graph.keys())
            while chmbr is None: 
                ans = input(f'enter "q" if you would like to exit the experiment, or enter the id of a different chamber to place this vole in.\n')
                if ans == 'q': exit() 
                try: 
                    start_chamber = int(ans)
                    chmbr = self.get_chamber(int(start_chamber)) 
                except ValueError as e: print(f'invalid input. Must be a number or the letter q. ({e})')            

                

        # Create new Vole 
        newVole = self.Vole(tag, start_chamber, self)
        self.voles.append(newVole)
        return newVole