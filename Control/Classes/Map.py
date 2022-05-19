
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
from code import interact
from collections import deque
import time
import json 
import os

# Local Imports 
from Logging.logging_specs import control_log
from .ModeABC import modeABC 
from . import InteractableABC
from .InteractableABC import lever, door, rfid

class Map: 
    def __init__(self, config_directory): 
        ''' key is id assigned to vertex: Chamber instance'''
        
        self.graph = {} # { chamberid: chamber instance }

        self.edges = [] # list of all edge objects that have been created ( can also access thru each Chamber instance )

        self.instantiated_interactables = {} # dict of (interactable name: interactable object ) to represent every object of type interactableABC that has been created to avoid repeats
        
        self.config_directory = config_directory # directory containing all of the configuration files 

        self.configure_setup(config_directory + '/map.json')

    def print_graph_info(self): 
        for chamber in self.graph.values(): 
            print(chamber)                       # chamber id and adjacent vertices
            for adj in chamber.connections.keys(): 
                edge = chamber.connections[adj]  
                print(edge)                      # edge id and vertices it connects




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
            try: new_obj = door(ID=objspec['id'], servoPin = objspec['servoPin'], threshold_condition = objspec['threshold_condition']) # instantiate door 
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')

        elif type == 'rfid': 

            try: new_obj = rfid(ID=objspec['id'], threshold_condition = objspec['threshold_condition']) # ASK: also need to pass in rfidQ?? confused on where this comes from though. 
            except Exception as e: raise Exception(f'there was a problem instantiating the object: {name}: {e}')

        elif type == 'lever': 
            
            try: new_obj = lever(ID=objspec['id'], threshold_condition = objspec['threshold_condition'], hardware_specs = objspec['hardware_specs'])
            except Exception as e: raise Exception(f'there was a problem instantiating the object {name}: {e}')


        else: 

            raise Exception(f'interactableABC does not have a subclass {type} implemented in InteractableABC.py')


        # dynamically set any attributes that can be optionally added to an interactable's configurations
        if "check_threshold_with_fn" in objspec.keys(): 
            setattr(new_obj, 'check_threshold_with_fn', eval(objspec['check_threshold_with_fn']) ) # function for checking if the threshold condition has been met
        if "dependents" in objspec.keys(): 
            setattr( new_obj, 'dependent_names', objspec['dependents'] ) # interactable that the threshold is dependent on (e.g. if we want lever1 to control door1, then set door1's dependent to be lever1. )
            
        
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
        for (n,i) in self.instantiated_interactables.items(): 
            if not i.active: 
                i.activate()
        
    def deactivate_interactables(self, clear_threshold_queue = True): 
        ''' loops thru all instantiated interactables and sets each of them to be inactive. Called in between modes '''
        for (n,i) in self.instantiated_interactables.items(): 
            i.deactivate()
        if clear_threshold_queue: 
            self.reset_interactables() # empties the interactables threshold queue

                
        
            


    #
    # Map Configuration 
    #
    def configure_setup(self, config_filepath): 
        ''' function to read/parse configuration file map.py and set up map accordingly '''

        # opening JSON file 
        f = open(config_filepath)

        # returns json object as a dictionary 
        data = json.load(f) 

        # closing JSON file
        f.close() 

        # Iterate thru to chambers list to initalize the diff chambers and their interactables 
        for chmbr in data['chambers']: 
            
            new_c = self.new_chamber( chmbr['id'] )
            
            for i in chmbr['components']: 
                
                # instantiate interactable hardware 
                #try: 
                    new_i = self.instantiate_interactable_hardware( i['interactable_name'], i['type'] )
                    # assign the interactable to a chamber object
                    new_c.new_component( new_i )
                
            '''except Exception as e: 
                    print(f"Ran into an issue when trying to instantiate the interactable object: {i['interactable_name']}")
                    print('Error Message: ', e)
                    print(f'would you like to continue running the experiment without instantiating this interactable? If yes, I wont be aware of any interactions a vole may have with it. If no, I will exit the experiment immediately.')
                    ans = input('input (y/n) \n')
                    if ans == 'n': exit() '''
                    
 
        
        # Iterate thru edges list to make connections between the chambers 
        for edge in data['edges']: 

            if edge['type'] == 'shared': 
                
                new_edge = self.new_shared_edge(edge['id'], edge['start_chamber_id'], edge['target_chamber_id'])
                
                for i in edge['components']:

                    
                    # (NOTE changes!!!! ) CHECK IF REFERNCE TO AN EXISTING CHAMBER INTERACTABLE 
                    # edge components may point to an already instanted interactable that is in a chamber
                    # denoted with the key "chamber_interactable" 
                    ref = False
                    if 'chamber_interactable' in i.keys(): 
                        # reference to an already instanted interactable 
                        ## check validity ## 

                        # edge case: reference to a nonexistent interactable
                        try: old_i = self.instantiated_interactables[i['chamber_interactable']]
                        except KeyError as e: 
                            raise Exception(f'(Map.py, configure_setup) chamber_interactable is trying to reference a nonexistent interactable {i["chamber_interactable"]}. KeyError: {e}')
                        
                        # edge case: reference to an edge interactable (can only reference a chamber interactable)
                        if old_i.edge_or_chamber == 'edge': raise Exception(f'(Map.py, configure_setup) invalid chamber_interactable: cannot reference {old_i.name} as a chamber_interactable, because it is on an edge interactable (edge{old_i.edge_or_chamber_id})')

                        # edge case: reference to a chamber that does not touch the current edge 
                        if old_i.edge_or_chamber_id != new_edge.v1 and old_i.edge_or_chamber_id != new_edge.v2: raise Exception(f'(Map.py, configure_setup) invalid chamber_interactable: {old_i.name} is in chamber{old_i.edge_or_chamber_id} which is not connected to edge{new_edge.id}: {new_edge}') 
                        
                        ref = True 
                        new_i = self.instantiated_interactables[i['chamber_interactable']]
                        component_obj = self.get_chamber(new_i.edge_or_chamber_id).get_component_from_interactable(new_i)
                        new_edge.new_component(new_i, chamber_interactable_reference=True)
                        

                    # instantiate interactable hardware
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
        
        self.set_dependent_interactables()
    
         

    def set_dependent_interactables(self): 

        # if an interactable specified a "dependent" in its configuration file, then it gets an attribute "interactable_name" which serves as a string representation of the interactable
        # after all objects have been instantiated, we now want to assign the actual interactable objects rather than just their string representation

        # loop thru all instantiated interactables and check for the attribute dependent_name 
        for i_name in self.instantiated_interactables:
            i = self.instantiated_interactables[i_name]
            if hasattr(i, 'dependent_names'): 
                # has dependents we need to add 
                for dname in i.dependent_names:
                    try: 
                        i.dependents.append(self.instantiated_interactables[dname]) # assign parent its new dependent 
                        self.instantiated_interactables[dname].parents.append(i) # assign dependent its new parent

                    except KeyError as e: 
                        print(f' specified an unknown interactable {e} as a dependent for {i.name}. Double check the config files for {e} and for {i.name} to ensure they are correct, and ensure that {e} was added in the map config file as well.')
                        ans = input(f' would you like to carry on the experiment without adding {e} as a dependent for {i.name}? (y/n)')
                        if ans == 'n': exit()

                
                delattr(i, 'dependent_names')  # delete the dependent_names attribute since we don't need it anymore 



    def get_chamber(self, id): 
        ''' returns chamber object with specified id '''
        for cid in self.graph.keys(): 
            if cid == id: 
                return self.graph[cid]
        return None

    def new_chamber(self, id): 
        ''' new Chamber instantiated and added to graph'''
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

        print(f'(Map, get_chamber_path) {start}->{goal}')

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

        print(f'(Map, get_path) args: start={start}, goal={goal}')

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
        print(f'(Map, get_edge_chamber_path) args: start={start}, goal={goal}')
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


    def get_component_path(self, start_component, goal_component ): 
        ''' 
        arguments should be of component type 
        function first gets list of sequential edge and chamber components that fall between the start Location and the goal location
        then, it removes any components that fall outside of the start_compoennt and goal_component and returns this list. 
        returns list of iNTERACTABLE TYPE! 
        '''
        
        print(f'(Map, get_component_path) {start_component}->{goal_component}')
            
        # Error Check: Incorrect Argument Type 
        if type(start_component) is not self.OrderedComponents.Component or type(goal_component) is not self.OrderedComponents.Component: 
            control_log(f'(Map, get_component_path) arguments must be of type Component, but recieved start_component of type {type(start_component)} and goal_component of type {type(goal_component)}')
            raise Exception(f'(Map, get_component_path) arguments must be of type Component, but recieved start_component of type {type(start_component)} and goal_component of type {type(goal_component)}')


        # convert components to their edge or chamber location objects (get_location_object requires interactable arguments rather than the component)
        start_loc = self.get_location_object(start_component.interactable)
        goal_loc = self.get_location_object(goal_component.interactable)


        #
        # edge case: components are in the same lcoation 
        #
        if start_loc == goal_loc: 
            # get full component list of location 
            component_path = start_loc.get_component_list() 

            # convert to interactable version 
            interactable_path = [c.interactable for c in component_path]
            startIdx = interactable_path.index(start_component.interactable)
            goalIdx = interactable_path.index(goal_component.interactable)      
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
            
            # loop thru loc_path of edges and chambers
            for idx in range(len(loc_path)): 
                
                loc = loc_path[idx] # edge or chamber object specified by path 

                components = loc.get_component_list() # locations components 

                if type(loc) == self.Chamber: # if current loc is a chamber 

                    # if loc_path[i+1] exists, grab this edges component list 
                    adj_components = [] 
                    if idx+1 < len(loc_path): 
                        # nxt loc will be an edge. grab its component list 
                        adj_components = loc_path[idx+1].get_component_list() 
                    
                    # add any chamber components with interactables that are not also assigned to an edge
                    for c in components: # for each component assigned to the current chamber 
                        # convert from components to their interactables 
                        interactable_path = [x.interactable for x in component_path]
                        adj_interactables = [x.interactable for x in adj_components]
                        # IF the component.interactable does not already exist in the component_path (case that it was already added by the previous edge)
                        # AND if the component does not exist in the next edges component list (case that it will be specified in the following edge)
                        # THEN add the component to the component_path 
                        # ELSE we don't want to add this component as we can let the edges handle that.
                        if c.interactable not in interactable_path and c.interactable not in adj_interactables: 
                            component_path.append(c)
                

                else: 
                    # current loc is an Edge! 
                    # based on direction that we are moving in path, check if we should reverse the order of the edge components 
                    # grab edges components list and add components to component path 

                    ## Preserve Component Ordering based on Direction of Vole Movement ## 
                    if idx+1 < len(loc_path): 
                        # grab id of the chamber that follows 
                        adj_cid = loc_path[idx+1].id
                        # compare to the ordering of the edges chambers 
                        if adj_cid == loc.v1: # nxt chamber in path is the 1st chamber of the edge, so we should reverse the edge components 
                            reverse = True 
                        else: reverse = False  
                    
                    # Edge Case: Final Element in path. Use the previous chamber to figure out component ordering
                    else: 
                        # grab id of the chamber that precedes 
                        adj_cid = loc_path[idx-1].id 
                        # compare to the chamber ordering that the edge chamber knows
                        if adj_cid == loc.v1: # prev chamber in path is the 1st chamber of the edge, so do NOT reverse the edge components 
                            reverse = False
                        else: reverse = True 

                    # Add All Edge Components in the Specifed Ordering #                        
                    component_path.extend(loc.get_component_list(reverse=reverse))
            

        # full component path has been compiled. Final step is to remove elements that fall outside of the range of the start_component and goal_component 
        # since start or goal components may have been chamber component where we added the edge version of the component, we should check for the index by interactable rather than by component 
        interactable_path = [c.interactable for c in component_path]
        start_idx = interactable_path.index(start_component.interactable)
        goal_idx = interactable_path.index(goal_component.interactable)
        if start_idx > goal_idx: 
            return component_path[goal_idx:start_idx+1]
        return component_path[start_idx:goal_idx+1] 
                    

    #
    # Linked List for Interactable Ordering w/in Edge or Chamber
    #
    class OrderedComponents: 
        ''' Class for Traversing and Locating Components on an Edge or w/in a Chamber. 
        Manages Linked Lists that preserves order of interactable components.
        Possible to add info on the "edges" that link two components. i.e. can assign values so we can identify where a vole sits relative to interactables w/in the linked list. 
        '''

        ''' Methods for Traversing and Locating Components on an Edge '''
        def __iter__(self): 
            component = self.headval
            while component is not None: 
                yield component
                print 
                component = component.nextval


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
    # Chamber -- vertices in the graph
    #  
    class Chamber(OrderedComponents): 
        
        def __init__(self,id): 

            self.id = id 

            self.edge_or_chamber = 'chamber'
            
            self.connections = {} # adjacent chamber: a single Edge object which points to linked list of components

            self.headval = None
            # (NOTE CHANGES!) self.interactables is now accessed thru self.headval 

            self.action_probability_dist = None # probabilities are optional; must be added after all interacables and chamber connections have been added. can be added thru function 'add_action_probabilities'


        def __str__(self): 
            return 'Chamber: ' + str(self.id) + ', adjacent: ' + str([x for x in self.connections]) + ', interactables: ' + str([c.interactable.name for c in self])


        ''' Adding Component to Chamber '''
        def new_component(self, newinteractable): 
            # instantiates new Component and adds to end of linked list
            newinteractable.edge_or_chamber = 'chamber'
            newinteractable.edge_or_chamber_id = self.id
            newComp = self.Component(newinteractable)

            if self.headval is None: 
                self.headval = newComp
                return newComp
            
            component = self.headval 
            while(component.nextval):
                component = component.nextval # list traversal to get last component in linked list 
                if component.interactable == newComp.interactable:                 
                    # check that component is not a repeat 
                    del newComp
                    raise Exception(f'component not added because this component has already been added to the edge')
            
            
            component.nextval = newComp # update list w/ new Component
            newComp.prevval = component # set new Component's previous component to allow for backwards traversal     
            return newComp


        
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
    # Edges -- linked list for storing Components
    # 
    class Edge(OrderedComponents):    
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

        ''' Adding Component to an Edge'''
        def new_component(self, newobj, chamber_interactable_reference = False): 
            # instantiates new Component and adds to end of linked list
            if chamber_interactable_reference is False: 
                newobj.edge_or_chamber = 'edge'
                newobj.edge_or_chamber_id = self.id
            else: 
                # if type(newobj) != self.Component: raise Exception(f'(Map.py, new_component) chamber_interactable_reference=True, sop must pass in a Component object, not an interactable object. ')
                # if not issubclass(type(newobj), InteractableABC): raise Exception(f'(Map.py, new_component (on edge)) chamber_interactable=True, but newobj {type(newobj)}was not of IneractableABC type')
                newComp = newobj

            newComp = self.Component(newobj)

            if self.headval is None: 
                self.headval = newComp
                return newComp
            
            component = self.headval 
            while(component.nextval):
                component = component.nextval # list traversal to get last component in linked list 
                if component.interactable == newComp.interactable:                 
                    # check that component is not a repeat 
                    del newComp
                    raise Exception(f'component not added because this component has already been added to the edge')
            
            
            component.nextval = newComp # update list w/ new Component
            newComp.prevval = component # set new Component's previous component to allow for backwards traversal     
            return newComp




            

            
            



                