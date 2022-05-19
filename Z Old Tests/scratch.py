        chamber1 = self.map.get_chamber(1)
        chamber2 = self.map.get_chamber(2)
        chamber3 = self.map.get_chamber(3)

        edge12 = self.map.get_edge(12)
        edge13 = self.map.get_edge(13)

        rfid1 = self.map.instantiated_interactables['rfid1']
        rfid2 = self.map.instantiated_interactables['rfid2']
        rfid4 = self.map.instantiated_interactables['rfid4']
        door2 = self.map.instantiated_interactables['door2']
        lever1 = self.map.instantiated_interactables['lever1']
        lever2 = self.map.instantiated_interactables['lever2']
        
        loc1 = self.map.get_location_object(rfid1)
        loc2 = self.map.get_location_object(door2)
        loc3 = self.map.get_location_object(lever1)
        loc4 = self.map.get_location_object(lever2)
        loc5 = self.map.get_location_object(rfid2)
        loc6 = self.map.get_location_object(rfid4)
        rfid1 = loc1.get_component(rfid1) # convert to the component version rather than the interactable
        rfid2 = loc5.get_component(rfid2)
        rfid4 = loc6.get_component(rfid4)
        door2 = loc2.get_component(door2)
        lever1 = loc3.get_component(lever1)
        lever2 = loc4.get_component(lever2)



        print(self.map.get_path(chamber1,edge12))
        print(self.map.get_path(edge12,chamber2))
        print(self.map.get_path(edge13, edge12))
        print('-----')

        chamber_edge_path = self.map.get_edge_chamber_path(chamber3, chamber2)

        for c in chamber_edge_path:
            print(f'{c.edge_or_chamber}{c.id}')

        chamber_edge_path = self.map.get_edge_chamber_path(edge12, chamber3)

        for c in chamber_edge_path:
            print(f'{c.edge_or_chamber}{c.id}')

        component_path = self.map.get_component_path(lever1, lever2)
        
        for c in component_path: 
            print(c.interactable)
        
        print('\n')

        component_path = self.map.get_component_path(lever1, door2)

        for c in component_path: 
            print(c.interactable)
        
        print('\n')

        component_path = self.map.get_component_path(rfid2, rfid1)
     
        for c in component_path: 
            print(c.interactable)

        
        component_path = self.map.get_component_path(rfid4, rfid1)
     
        for c in component_path: 
            print(c.interactable)



        component1 = self.map.get_edge(12).get_component(lever1)
        component2 = self.map.get_edge(12).get_component(lever2)
        component3 = self.map.get_edge(12).get_component(rfid1)
        component4 = self.map.get_edge(12).get_component(rfid2)
        
        # Testing Component Traversal # 
        res = vole1.move_to_component(component2)

         
        vole1.move_next_component(component1)
        self.draw_edges() 
        # vole1.simulate_vole_interactable_interactable(component1)

        vole2.move_next_component(component2)
        self.draw_edges() 
        # (NOTE--COME BACK TO THIS!) THIS CASE CAUSES AN ERROR THAT ISN'T DEALT WITH: vole2.move_next_component(component2)
        vole3.move_next_component(component2)
        self.draw_edges() 

        vole1.move_next_component(component3)
        self.draw_edges()

        self.draw_chambers()
        self.draw_edges()



            print(path)
            for loc in path: 
                # we can either update location to go back towards our previous location, or we can try to update location into a new edge or chamber. 


                '''# if prev component exists in same location as current location, vole is simply sitting at the end of a component list. 
                if self.prev_component is not None and self.map.get_location_object(self.prev_component.interactable) == self.curr_loc:
                # Positioned At End Of Linked List. we want to get  
                
                component_lst = self.map.get_component_path(self.prev_component, goal_component) 

                # if the''' 
                # for each location, 
            '''if self.curr_component is None and self.prev_component is None: 

            # Voles current location does not match the goal component location 
            goal_loc = self.map.get_location_object(component.interactable)
            if self.curr_loc != goal_loc: 
                
                # see if we are able to move freely into the location of the component we want to interact with. 
                path = self.map.get_edge_chamber_path(self.curr_loc, goal_loc) # inclusive list, so first element will be curr_loc and last element will be goal_loc
                print('path;', path)
                for l in path: 

                    if l != self.curr_loc and l != goal_loc: 
                        
                        print()
                        # for all locations in between start and goal, ensure that they are empty so vole is free to pass 
                        if len(l.get_component_list()) == 0: 
                            continue 
                    
                        else: 
                            # cannot freely pass thru this location, so cannot reach component in a single step. 
                            print(f'(Vole{self.tag}, move_next_interactable) Cannot move to {component} because need to pass other components in {l}')
                            return False
                    
            # check if we can goal component is accessible w/in the goal location ( must be on correct end of linked list )
            ok = False 
            if self.curr_loc.edge_or_chamber == "chamber": # current location is a chamber! goal location is an edge! 
                # goal loc must be an edge that touches current chamber 
                for (c,e) in self.curr_loc.connections.items(): 
                    if goal_loc == e: 
                        ok = True 
                        break 
                # goal component must be on the correct side of the edge 
                if ok: 
                    if goal_loc.v1 == self.curr_loc: 
                        clst = goal_loc.get_component_list() 
                    else: 
                        clst = goal_loc.get_component_list(reverse=True)
                    if clst[0] != component: # goal component should be the first element in the component list we made
                        print(f'(Vole{self.tag}, move_next_interactable) Cannot move to {component} because need to pass other components first. {goal_loc}')
                        return False 
                    

            else:  # current location is an edge! goal location is a chamber! 
                # goal loc must be a chamber that current edge is connected to 
                if self.curr_loc.v1 == self.curr_loc.id or self.curr_loc.v2 == self.curr_loc.id: 
                    ok = True 
            if not ok: 
                print(f'(Vole{self.tag}, move_next_interactable) Cannot move to {component} because {goal_loc.edge_or_chamber}{goal_loc.edge_or_chamber_id} does not border {self.curr_loc.edge_or_chamber}{self.curr_loc.edge_or_chamber_id}.')
                return False 
            
            
            # can freely update location to the goal location 
            self.update_location(component)
            return True 
            '''


            
GET_COMPONENT_PATH NOTES: 
        # get path will return a list of chambers that we will need to cross to reach the desired chamber/edge. 

        # collect the comonents! 
        #
        #
        #
        # important NOTE : LEAVING OFF HERE!!!!!!!!!!!! 
        # IMPORTANT NOTE : we only care about the components along the edges, because all components that matter in vole movements should be added to an edge! 
        # important ISSUE : what happens if two edges get the same component added to it??? I dont think this will matter? if i remember correctly, it gets assigned a new component object but contains the same interactable object. 
        #
        
        #
        # Wednesday May 11
        # leaving off here!!!!!! NEED TO FIGURE OUT HOW TO HANDLE WHEN OUR START AND GOAL ARE ON THE SAME EDGE (or the same chamber i guess). 
        # Cause then chamber path comes back empty. and then we add nothing. 
        #
        # ####
        # #### 


        # handle if chamber path is empty!!! this is the case if and only if start==goal, and they are of edge type. but then shouldnt the edge components get added anyways??? because we 
        # check if start and goal are of edge type, and if they are, we add those edge components?? so idk what happening.  
        
        # also case where get_path gets called with a (chamber1, edge12), then the result is just [1] (as in chamber1), since chamber1 is connected to edge12. So need to account for this as well. 
        #   actually think this is already accounted for because we wouldn't loop in the chamber path at all, we would end up just skipping down to the if type(goal) == edge, then add those edge components. 

        # basically we need to change this so its an INCLUSIVE path finding result.
        component_path = [] 

        for loc in loc_path: 
            
            if type(loc) == self.Edge: 
                # ordering matters! 
                if 

        if type(start) == self.Edge: 
            # begin with edge components if our start is an edge
            if loc_[0] == start.v1: 
                component_path.extend(start.get_component_list(reverse=False))
            else: component_path.extend(start.get_component_list(reverse=True))
        
        for idx in range(len(chamber_path)-1): # for each chamber in the chamber path 



            chamberID = chamber_path[idx] 
            chamber = self.graph[chamberID]

            # # # # 
            # HANDLE CHAMBER COMPONENTS 
            # if the ordering of components is specified in a neighboring edge (as a chamber_interactable), then use that information to decide the ordering of the chamber components to return 
            
            cc = chamber.get_component_list() # chamber component list 
            
            # for each chamber component, we want to check if it exists on the NXT edge. If we find any component on the next edge, 

            #
            #
            # # # # 


            # # Get Next Edge # # 
            adj_cid = chamber_path[idx+1] # grab the next chambers id in order to get next edge 

            # for each chamber, grab the next edge connecting current chamber and nxt chamber 
            edge = chamber.connections[adj_cid]

            # extend the component path with the new edges component list  
            if edge.v1 == adj_cid: # the nxt chamber comes first in the edge, so reverse component ordering 
                component_path.extend(edge.get_component_list(reverse=True))
            else: 
                component_path.extend(edge.get_component_list(reverse=False))
            
            idx = idx+1
        
        # Final Loop for adding the last chamber in the chamber_path (since previous loop skips its last iteration):
        final_chamberid = chamber_path[idx] 


        
        if type(goal) == self.Edge: 

            # end with edge components if our goal is an edge 
            component_path.extend(goal.get_component_list())

        return component_path


### DRAWING VOLES AND EDGES CHANGES ### 

            ''' edgeObjectList = [] 
            if len(interactables) == 0: 
                # just draw voles
                edgeObjectList = evoles 

            for idx in range(len(interactables)): 
                i = interactables[idx] 

                # check if any of the edge voles position is at interactable i
                for v in self.voles: 
                    if v.curr_component.interactable == i: 
                        # figure out which side of interactable the vole goes on
                        if v.prev_component == None: 
                            # v before i 
                            edgeObjectList.extend([v,i])
                        else: 
                            edgeObjectList.extend([i,v])
            '''

            

            '''if len(interactables) == 0: 
                # chamber without interactables. Just draw voles. 
                for v in cvoles: 
                    draw_vole(v)

            for idx in range(len(interactables)): 
                # loop thru interactables w/in the chamber
                i = interactables[idx] 
                
                voles_after_i = [] 
                voles_before_i = [] 
                
                for v in cvoles: # for each interactable, loop thru the voles w/in the same chamber and check their component location 

                    # for every vole located by the current interactable, append to list so we can draw 
                    if v.curr_component.interactable == i: 
                        
                        # figure out if vole should be drawn before or after the interactable
                        if idx == 0: 
                            # edge case to avoid out of bounds error 
                            if v.prev_component == None: 
                                # v before i 
                                voles_before_i.append(v)
                            else: 
                                # i before v 
                                voles_after_i.append(v)

                        elif v.prev_component == interactables[idx-1]: 
                            # draw v before i 
                            voles_before_i.append(v)
                        else: 
                            # draw i before v 
                            voles_after_i.append(v)
                
                # Draw! 
                for v in voles_before_i: draw_vole(v)
                draw_interactable(i)
                for v in voles_after_i: draw_vole(v)'''





                #
                # OLD Dependents Loop (this was placed w/in the watch_for_threshold_event function in InteractableABC.py)
                #
                '''for dependent in self.dependents: 
                    # if dependents are present, then before we can add an event to current interactable, we must check if the dependents have met their threshold 
                    # loop thru all the dependents, and if any dependent has not already detected a threshold_event, then the current interactable has not met its threshold. 
                    
                    #print(f'(InteractableABC.py, watch_for_threshold_event, dependents_loop) {self.name} event queue: {list(self.threshold_event_queue.queue)}')
                    #print(f'(InteractableABC.py, watch_for_threshold_event, dependents_loop) dependent of {self.name} : {dependent.name} (event queue: {list(dependent.threshold_event_queue.queue)})')

                    time.sleep(3)   

                    if dependent.active is False: 
                        # dependent is not currently active, skip over this one 
                        break 

                    # Threshold Not Reached
                    elif dependent.threshold is False:
                        # depedent did not reach its treshold, so neither does the current interactable
                        
                        # print(f"(InteractableABC.py, watch_for_threshold_event, dependents_loop) {self.name}'s dependent, {dependent.name} did not reach threshold")
                        
                        event_bool = False 
                        break  # do not need to check any remaining interactables in the list
                

                    else: 
                        # Retrieve the Event of the Current Interactable's Dependent.  
                        control_log(f"(InteractableABC.py, watch_for_threshold_event, dependents loop) Threshold Event for {self.name}'s dependent, {dependent.name}.") 
                        print(f"(InteractableABC.py, watch_for_threshold_event, dependents_loop) Threshold Event for  {self.name}'s dependent, {dependent.name}.") 
                # End of Dependents Loop '''
                    # Reset the Threshold Values of the interactable's Dependents (ok to do so now that we have confirmed that there was a threshold event)
                    # this is now getting done in the separate dependents_loop function
                    '''for dependent in self.dependents: 
                        dependent.threshold = False '''






'''def draw_vole(v):
    v = v.tag
    if len(str(v)) > 8: 
        v = str(v)[:7] + '-'
    space = 8 - len(str(v)) 
    print(f'|[{v}]' + f"{'':>{space}}" + '|')
def draw_interactable(i):
    if len(str(i)) > 8: 
        i = i[:7] + '-'
    space = 8 - len(str(i)) 
    print(f'|[{i}]' + f"{'':>{space}}" + '|')'''    
    
    
    '''OLD VERSION
    def physical_proximity_check(self, interactable): 
        if interactable.edge_or_chamber == self.edge_or_chamber and interactable.edge_or_chamber_id == self.edge_or_chamber_id: 
            # if vole position between interactables is currently next to the desired interactable, return True
            if interactable == self.curr_interactable: 
                # vole is next to interactable 
                return True 
            else: 
                print(f'(Vole.py, physical_proximity_check) vole{self.tag} is in the same {self.edge_or_chamber} as {interactable.name} but is standing next to the interactable: {self.curr_interactable}') 
        else:            
            print(f'(Vole.py, physical_proximity_check) vole{self.tag} is in {self.edge_or_chamber}{self.edge_or_chamber_id} but {interactable.name} is in {interactable.edge_or_chamber}{interactable.edge_or_chamber_id}')      
        return False 
     
        if interactable.edge_or_chamber == 'chamber': # check that the vole's location is w/in physical proximity of the interactable we are simulating an interaction with

            # vole's current chamber location must match 
            if self.current_loc != interactable.edge_or_chamber_id: 
                sim_log(f'(Vole.py, simulate_vole_interactable_interaction) Cannot simulate vole{self.tag} interaction with {interactable.name} because it is in a different chamber.')
                print(f'(Vole.py, simulate_vole_interactable_interaction) Cannot simulate vole{self.tag} interaction with {interactable.name} because it is in a different chamber.')
                return 
        else: 
            # vole's current chamber must be one of the chambers that the edge connects 
            edge = self.map.get_edge(interactable.edge_or_chamber_id)
            if (self.current_loc != edge.v1 and self.current_loc != edge.v2): 
                sim_log(f'(Vole.py, simulate_vole_interactable_interaction) Cannot simulate vole{self.tag} interaction with {interactable.name} because it is on an edge connection different chambers.')
                print(f'(Vole.py, simulate_vole_interactable_interaction) Cannot simulate vole{self.tag} interaction with {interactable.name} because it is on an edge connection different chambers.')
                return '''


{
    "door2": 
    {
        "id":2, 
        "servoPin":3, 
        "threshold_condition": { "attribute":"state", "initial_value": false, "goal_value":true }, 
        "update_goal_after_threshold_event": "lambda self: not self.state" ,
        "dependents": []
    }
}

{ 
    "lever1": 
    {
        "id":1,
        "signalPin":1, 
        "numPresses":2,  
        "threshold_condition": { "attribute": "pressed", "initial_value":0, "goal_value": 6, "reset_value": true },    
        "update_goal_after_threshold_event": "lambda self: self.threshold_condition['goal_value'] + 1"
    }
    
}



''' IMPORT STATEMENT THINGS 

# print(os.getcwd())
# dir_path = os.getcwd() + '/Control'
# sys.path.append(dir_path)
# site.addsitedir(dir_path)
# sys.path.append('/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation')




site.addsitedir('/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation')
print(sys.path)

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path)
sys.path.append('/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation')
'''      



''' 
random helpful syntax : 
__getattribute__ and __name__
res = map.get_edge(12).get_interactable_from_component('rfid1').__getattribute__('check_threshold_with_fn')
print(res.__name__)


helpful website 
https://stackoverflow.com/questions/4821104/dynamic-instantiation-from-string-name-of-a-class-in-dynamically-imported-module 
'''


''' 
OLD __main__ function that was sitting w/in the sim_attempt_move.py module, but now I am changing it so there is an actual __main__.py file w/in the Simulation Module so i don't need this anymore 


if __name__ == '__main__': 


    # instantiate map (which will also instantiate the hardware components) 
    map = Map('/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation/Classes/Configurations')

    res = map.get_edge(12).get_interactable_from_component('rfid1').__getattribute__('check_threshold_with_fn')
    print(res.__name__)


    sim_log('\n\n\n\n-----------------------------New Simulation Running------------------------------------')
    

    # instantiate the modes that you want to run
    mode1 = mode1( timeout = 15, map = map ) 
    mode2 = mode2( timeout = 15, map = map )

    
    # instantiate the Simulation, pass in the Mode objects, map, and Voles to create
    sim = SarahsSimulation( modes = [mode1, mode2], map = map  ) 
    
    sim_log(f'(sim_attempt_move.py, {__name__}) New Simulation Created: {type(sim).__name__}')

    # simulation visualizations
    sim.draw_chambers() 
    sim.draw_edges() 


    time.sleep(5) # pause before starting up the experiment 

    # indicate the simulation function to run when the mode enters timeout 
    # optional second argument: indicate the number of times to run the simulation function. If this value is not passed in, then the simulation loops until the experiment finishes its timeout interval. 
    sim.simulation_func[mode1] = (sim.mode1_timeout, 1)
    sim.simulation_func[mode2] = (sim.mode2_timeout, 1) 

    # runs simulation as daemon thread. 
    t1 = sim.run_sim() 


    # start experiment 
    mode1.enter() 
    mode1.run() 

    mode2.enter() 
    mode2.run() 
'''

      ''''
        class rfid:
            ## not sure what the normal code will look like ## 
            # Simulation Version! #  
            @threaded_fn
            def condition_for_threshold_to_get_set_to_true(): 
                # constantly looping and updating the rfid threshold val 
                if self.ping_queue gets new value: 
                    write val to output 
                    self.threshold = True 
                

        class Wheel: 
            @threaded_fn
            def condition_for_threshold_to_get_set_to_True(): 
                # constantly looping and updating the rfid threshold val 
                if self.moves is True: 
                    self.threshold = True 
                # simulation version of this function would look the same 
                # if the user specified to simulate the wheel, then the sim script will specify at what times the vole interacts with the wheel 
                # when vole interacts with the wheel, we will just directly set wheel.moves to True to "simulate" the movement. 
        class Lever: 
            @threaded_fn 
            def condition_for_threshold_to_get_set_to_true(): 
                if presses == self.required_presses: 
                    self.threshold = True 
            ## Simulation Version of this Function would look the same ##
            # if the user specified that we are simulating the lever (no physical hardware), then the user will directly specify in their simulation 
            # script that the vole should press the lever, by simply directly adding one to the self.pressed count 
            # ( or this will happen randomly if we are running a random_vole_moves() experiment ) 

        class Door: 
            @threaded_fn 
            def condition_for_threshold_to_get_set_to_true(open): 
                if open is True: # set threshold to True after successfully opening door 
                    self.open_door() 
                    self.threshold = True
                else: # set threshold to True after successfully closing door 
                    self.close_door() 
                    self.threshold = True

                    ~~~~~ simulation version of this funciton ~~~~    
                    ## If the user wants to abstract away from physical hardware, override the condition_for_threshold function ## 
                    ## ensures that we don't call any functions that interact with the rpi ## 
                    ## Simulation should Override the function condition_for_threshold_to_get_set_to_true(): 
                    def condition_for_threshold_to_get_set_to_true(open): 
                        if open is True: 
                            print('opening door')
                            self.threshold = True 
                        if open is False: 
                            print('closing door')
                            self.threshold = True 
            
            def isOpen(): 
                return state_switch # hardware! 
            def open_door(): 
                raspberry_pi_things.open # hardware
                if state_switch: # hardware! 
                    self.isOpen = True 
            def close_door(): 
                rpi.close # hardware! 
                if state_switch: #hardware!
                    self.isOpen = False         
        '''



        '''
        class rfid: 
            @threaded_fn 
            def condition_for_threshold_to_get_set_to_True(): 
                # constantly looping and updating the rfid threshold val
                if 3 items have been added to self.ping_queue: 
                    self.threshold = True 
        '''
        '''
            if self.box.rfid1.threshold is True: 
                self.box.door1.open() 
        '''



# next TODO: from Map.py, when creating the interactable or component from the info from map.json, 
# start reading in the new "threshold_condition" value so we can know what the 
# threshold attribute/value goal is for each component. Pass this info when creating 
# the interactable, and give interactables a new attribute to store this information.  
'''         _________________________________________________________________________________
            ## the simulation version reverses the order of a cause/effect reaction. 
            # Non-Simulation Version #
            # in the non-simulation version, the control software has the following cause/effect
                                            cause = some set of actions has met the threshold condition 
                                                (e.g. 2 lever presses in a row, where the threshold was defined as lever.required_presses == 2) 
                                                
                                                --> maybe in the function we can just say (if (condition) | if (simulation==True)&&(bypass==True)), go ahead and add to threshold_event_queue. 
                                                    if (simulation==True)&&(bypass==True): make sure to also wait a good num of seconds before adding to the event queue again to avoid adding an endless amount to the queue
                                            
                                            effect = add to threshold_event_queue 


                # so we are checking for if the condition has been met. 
            # Simulation Version # 
            # in the simulation version, the control software has the following cause/effect
                                        cause = something got added to the threshold_event_queue 
                                        effect = update attributes of the component to reflect the event 
                    for example, appending to an rfid queue, or changing the isOpen state of the door. 

            



            example for setting these values, with edge components (lever1, rfid1, door1, rfid2)

                # NON-SIM -- checks these attributes to see if their threshold_conditions have been met: 
                lever1.condition( lever1.required_presses == 6 )
                    def condition: 
                        if arg is True: lever1.signal_threshold() # adds to queue 
                
                class InteractableABC
                    def signal_threshold() 
                        # effect: add to queue 
                        self.threshold_event_queue.put() 
                    def threshold_attributes() 
                        # (NON-SIM) cause: check if attribute equals desired value --> set as dict of {attribute: value}
                        # (SIM) effect: set the attribute values
                        if self.condition_dict is True: self.signal_threshold() 
                class rfid1
                    ## Setting Values so it works for both Non-Sim and Sim Version 
                    self.condition_dict = { "rfidQ": True }
                class door1 
                    self.condition_dict = { "isOpen": True }
                class lever1
                    self.condition_dict = { "required_presses":6, "pressed":"required_presses" }
                class rfid2
                    self.condition_dict = { "rfidQ": True }






                door1.condition( door1.isOpen() == True ) 

                rfid1.condition( rfid1.rfidQ.added() ) 

                # SIM 
                
          _________________________________________________________________________________
'''
self = None 


# Logic to change the num presses every time the wheel is run
while self.active:
    # If the wheel has been interacted with, increase the number of required presses
    if self.box.wheel_1.threshold_event_queue.get(block=False): # if an event was added to the queue to denote that the threshold's condition was met 
        self.box.chamber_lever.required_presses += 1
    
    # if lever was pressed required number of times, open door, reset the tracked num of lever presses to 0  
    if self.box.chamber_lever.threshold_event_queue.get(block=False): # if lever's threshold queue gets new value 
        self.box.chamber_lever.presses = 0 # reset tracked num of presses to 0
        self.door.open_door() # open door 
    
    # if rfid1 and rfid2 were pinged (meaning the vole moved to the next chamber), close door 
    if self.box.rfid1.threshold.threshold_event_queue.get(block=False) and self.box.rfid2.threshold_event_queue.get(block=False): 
        self.door.close_door() # close door 


        # LEAVING OFF HERE!!! 
        # simulate attribute has now been added to all of the interactable objects for use by the simulation 
        ''''
        class interactableABC: 
            self.event_queue # any event, even if it does not meet the defined threshold condition, will get added to this queue
            self.threshold_event_queue # if threshold condition is met, then we add to this queue 

            def sim_check(): 
                # decorator thread that should be called in any function that accesses hardware parts (the rpi)
                # this function should be overriden in each interactable, and specific simulation logic should sit in this function 


            def setup_watch_for_threshold_event(): 
                if hasattr(self.simulate): 

                    if self.simulate: 

                            #   .... OR? instead of overriding the normal function should we just 
                            # write a function that forces the threshold condition to be met?? 
                            # And then the watch_for_threshold_event function will still be running so will recognize that the threshold was met
                        
                        # override the normal functionality of so it waits for stuff 
                        # to get added to the threshold_event_queue, and if stuff gets added can manually update 
                        # attributes to reflect the threshold event. 

           
           
           
           
            def watch_for_threshold_event(): 



                # if not simulating, watch the condition and add to threshold_event_queue when condition is met 


                cause = some actions has met the threshold condition 
                    (e.g. 2 lever presses in a row, where the threshold was defined as lever.required_presses == 2) 
                effect = add to threshold_event_queue 


                # function that is unique to each interactable 
                # specifies the specific conditions required to meet the threshold
                # if that condition is met then an event is added to the threshold_event_queue 
                # continue to loop and check for if the threshold condition is met 

        class rfid:
            ## not sure what the normal code will look like ## 
            # Non-Simulation Version! #  
            def watch_for_threshold_event(): 
                # constantly looping to check if the defined condition has been met 
                # once condition gets met, then append to the threshold_event_queue 
                # this one is a little weird for the rfid readers because we are just taking things from one queue and placing it in another 
                # i.e. the threshold "condition" is if there is a ping, so if anything gets added to the rfid_q then we have met the threshold 
                new_ping = self.rfid_q.get(): 
                if new_ping: 
                    self.threshold_event_queue.put(new_ping)
            
          _________________________________________________________________________________
            ## the simulation version reverses the order of a cause/effect reaction. 
            # Non-Simulation Version #
            # in the non-simulation version, cause = some actions has met the threshold condition (e.g. 2 lever presses in a row, where the threshold was defined as lever.required_presses == 2) 
                                             effect = add to threshold_event_queue 
                # so we are checking for if the condition has been met. 
                # when condition is met, the control software appends to the th
            # Simulation Version # 
            # in the simulation version, cause = something added to the threshold_event_queue 
                                         effect = update attributes of the component to reflect the event 
                                                    for example, appending to an rfid queue, or changing the isOpen state of the door. 
          _________________________________________________________________________________

        class Door: 
            @threaded_fn
            def watch_for_threshold_event(): 
                # loops over the condition that gets defined here 
                # if condition is met at any point, then append to the threshold_event_queue 
                
                # door is watching for any state change in the door 
                prev_state = self.isOpen
                if self.isOpen != prev_state: 
                    # change in door state detected, write to threshold event queue
                    self.threshold_event_queue.put(self.isOpen)
            
            ## simulation functionality ## 
                # user will just directly change is isOpen value to force door to do what they want 
                # 
            
            def sim_check(): 
                if self.simulation == True: 
                     then we don't want to actually call open/close door
                     since this call is made directly from the experiment code, we need a way to prevent that function from fully executing
                     instead, just directly update the isOpen value to reflect the desired function 
                     the watch_for_threshold_event should see this state change and will append to the threshold_event_queue
                     then return from both functions, without ever having called the open/close door function. 

            @sim_check
            def open_door() 




        class Wheel: 
            
            def watch_for_threshold_event(): 
                # constantly looping on own thread to check if the defined condition has been met. 
                # once condition gets met, then append to the threshold_event_queue
                if self.moves is True: 
                    self.threshold_event_queue.put(True)
            
            
            ## simulation functionality ## 
                # user will just directly add self.moves to True 
                # or to skip this function all together, can directly append to the threshold_event_queue


        class Lever: 

            @threaded_fn 
            def watch_for_threshold_event(): 
                # constantly looping to check if the defined condition has been met. 
                # once condition gets met, then append to the threshold_event_queue

                if presses == self.required_presses: 
                    self.threshold_event.put(True) 

            ## simulation functionality ##
            # user will just directly add 1 to self.presses
            # or can skip this function all together by directly adding to the levers threshold_event_queue


        class Door: 
            @threaded_fn 
            def condition_for_threshold_event(open): 
                if open is True: # set threshold to True after successfully opening door 
                    self.open_door() 
                    self.threshold = True
                else: # set threshold to True after successfully closing door 
                    self.close_door() 
                    self.threshold = True

                    ~~~~~ simulation version of this funciton ~~~~    
                    ## If the user wants to abstract away from physical hardware, override the condition_for_threshold function ## 
                    ## ensures that we don't call any functions that interact with the rpi ## 
                    ## Simulation should Override the function condition_for_threshold_to_get_set_to_true(): 
                    def condition_for_threshold_event(open): 
                        if open is True: 
                            print('opening door')
                            self.threshold_event.put(True, 'door opened')
                        if open is False: 
                            print('closing door')
                            self.threshold_event.put(True, 'door closed') 
            
            def isOpen(): 
                return state_switch # hardware! 
            def open_door(): 
                raspberry_pi_things.open # hardware
                if state_switch: # hardware! 
                    self.isOpen = True 
            def close_door(): 
                rpi.close # hardware! 
                if state_switch: #hardware!
                    self.isOpen = False         
        '''



        '''
        class rfid: 
            @threaded_fn 
            def condition_for_threshold_event(): 
                # constantly looping and updating the rfid threshold val
                if 3 items have been added to self.ping_queue: 
                    self.threshold = True 
        '''
        '''
            if self.box.rfid1.threshold is True: 
                self.box.door1.open() 
        '''





            ''' ____________________________________________________________________________________________'''








     def attempt_move(self, destination, validity_check=True): 
        ''' called by Vole object ''' 
        ''' attempts to executes a move. if validity_check is set to True, then we check if the move is physically valid or not. '''
        ''' GETTING the thresholds of each interactable and checking that it is True '''
        ''' if the threshold of any interactable is not True, then we cannot successfully make the move '''

        debug(f'Entering the attempt move function. Vole {self.tag} is currently in chamber {self.current_loc}. Destination: {destination}.')

        if validity_check: 
            if not self.is_move_valid(destination): 

                debug(f'attempting a move that is not physically possible according to Map layout. Skipping Move Request')

                print('attempting a move that is not physically possible according to Map layout. Skipping Move Request.')

                return False
        # retrieve edge between current location and the destination, and check threshold for each of these 
        edge = self.map.graph[self.current_loc].connections[destination]
        rfid_lst = []

        debug(f' traversing the edge: {edge} ')

        # traverse the linked list 
        for component in edge: 

            # check if component is an rfid --> if it is an rfid, then add to rfid queue
            # TODO: figure out how to handle diff. components! 
            #
            # LEAVING OFF HERE! 
            # abstract away from needing to reference specific hardware objects.
            # in particular, figure out how to avoid referencing the mode.rfid object. 
            #
            
            
            # if rfid, place in lst to iterate over later. Otherwise, check that the component's threshold is True. 
            if type(component) == mode.rfid: 
                rfid_lst.append(component) # add rfids to list so we can write to queue after checking all thresholds 

            # if not rfid, check that the threshold is True
            if component.interactable.threshold is False:
                print(f'{component.interactable} threshold is False, cannot complete the move.')
                return False  
            
        # if all interactables along the edge had true thresholds, then we are able to make the move, so we should ping the rfids to simulate the move
        ## Rfid Pings ##
        for component in rfid_lst: 

            component.to_queue(self.tag, component.id) # RFID ping: (vole tag, rfid num)


        ## Update Vole Location ## 
        self.current_loc = destination

        debug(f'Vole {self.tag} successfully moved into chamber {self.current_loc}')





            
            
            
            
            ''' ____________________________________________________________________________________________'''
            ''' This Class will actually be implemented by Control Software, so delete this after Integration '''
            ## TODO: Delete This Class once Control Software Interactable Objects have been Completed!
            class Interactable:
                def __init__(self, threshold_requirement_func = None): 
                    
                    self.ID = None
                    self.threshold = None

                    #self.initial_threshold = initial_threshold
                    #self.initial_threshold_requirement_func = threshold_requirement_func
                    #self.threshold = initial_threshold 
                    #self.threshold_requirement_func = threshold_requirement_func

                def set_threshold(self, bool): 
                    self.threshold = bool  
                def reset(self): 
                    self.__reset()
                    self.threshold = False 
                def __reset(self): 
                    raise NameError("Overwrite with unique logic")

            ''' ____________________________________________________________________________________________'''

            "rfid2":{
                "function": { 
                    "arguments": "self, vole_tag, rfid_id", 
                    "body":"self.rfidQ.append(vole_tag, rfid_id)"
                }
             }

            ''' ____________________________________________________________________________________________'''


            
class Simulation 
     # old threading stuff; functions don't work yet, just was a rough layout 

    #
    # Running the Simulation 
    #
    def threader(self, isModeActive, func_to_run): 
        ''' decorator function that is called from the function we want to run '''

        pass 


    def run_sim(self, isModeActive, func_to_run): 

        ''' This function is called from the control software each time a simulation function should be executed '''
        # LEAVING OFF HERE! 
        # TODO -- probs needs fixing! 
        # creates thread with target function 'func_to_run' 
        # returns in case that either current_mode.active is set to False (either due to external interruption or because the mode.exit() function was reached
        
        # spawn thread, check that isModeActive is True, and start thread 
        sim_thread = threading.Thread(target=func_to_run, daemon=True)
        if isModeActive: sim_thread.start() 

        # let thread run while mode is Active 
        while isModeActive: 
            time.sleep(.05)
        
        # mode is exiting, return from function, effectively stopping the simulation
        return 




class Component: 
        # thinking i should move these into Simulation.py instead! 

        def simulate(self, vole): 
            ''' simulates a Vole's interaction with the interactable -- Called by the user script that specifies what actions the vole should make leading up to a move_chamber call '''
            if self.interactable.threshold_requirement_func: 
                # execute function to meet threshold 
                self.interactable.threshold_requirement_func() 
            else: 
                # simulate by directly setting the threshold to True 
                self.interactable.set_threshold(True)
        
        def set_threshold_requirement(self, func): 
            self.interactable.threshold_requirement_func = func

        def reset(self): 
            self.interactable.reset() 





def set_action_probability( self, actionobj_probability_lst):

            # actionobj_probability_lst: list of (actionobject, new_p) 

            for a in self.action_objects: 
                if a not in actionobj_probability_lst: 
                    raise Exception(f'must set the probability value for all action objects within the chamber ({self.action_objects}). Did not find a value for {a}. ')
            

            newsum = sum(a for (a,p) in actionobj_probability_lst) 
            if newsum != 1: 
                raise Exception(f'probabilities must sum to 1, but the given probabilities added to {newsum}')
            

            for (a,p) in actionobj_probability_lst: 
                self.actionobject_probability[a] = p

            #ISSUE: what if there are only 2 action objects in a chamber and both of their isDefaults are False. Then would be impossible to adjust the probability since could never change a diff value to ensure that total probability is 100%
            # to solve this issue, for now am ridding of the use of .isDefault, and no matter what, we will adjust all the other action-objects. 

            # updates the objects probability of getting chosen, and adjusts the other probabilities to ensure that they add up to 100% 
            # if an object's isDefault==False, then it does not get adjusted. Only the objects that have isDefault==True will be updated. 
            # if probability does not sum to 100 and there are no objects that are able to be adjusted to reach 100%, throw an error


            '''adjustable_actionobjects = [ a for (a,p) in self.action_objects if a not in actionobj_probability_lst ] # put any remaining actionobject in lst 
            # total_diff = 
            for actionobj in actionobjectlst: 

                old_p = self.actionobject_probability[actionobj]
                p_diff = new_p - old_p
                # adjustable_actionobjects = [ a for a in self.action_objects if (self.actionobject_probability[a].isDefault and a != actionobj) ] # new list of adjustable objects, discluding the object of the current action-object we are trying to change the probability of 
                

                # increase/decrease the probabilities of adjustable_actionobjects such that in total the change in probability is equal to that of p_diff 
                
                num_adjustables = len(self.actionobject_probability) - len(actionobjectlst)   
                if num_adjustables < 1: raise Exception(f'cannot adjust the probability of {actionobj} to a value not equal to 100%, because it is the only action-object accessible from chamber {self.id}')
                
                adjusted_p = p_diff/num_adjustables # divide the total change in p equally amongst all of the other action_objects
                for a in self.actionobject_probability: # loop thru the action-objects that we want to adjust, and change probability value accordingly
                    self.actionobject_probability[a] = self.actionobject_probability[a] + adjusted_p
                
                self.actionobject_probability[actionobj] = new_p # update with new probability value
                new_sum = sum(v for (k,v) in self.actionobject_probability.items()) # double check that new sum is 100%
                if new_sum != 1: 
                    raise Exception(f'something went wrong in adjusting the probabilities (def set_action_probability in Map Class). the sum after changing the probability is now {new_sum}')
                

           '''
                

        class ActionObjectProbability:
            def __init__( self ): 
                
                distribution = Table().domain()
                #self.probability = probability # updated probability 
                #self.initial_p = probability # initial default probability 
                #self.isDefault = True # Boolean to represent if probability has changes from default or not 
            
            def update_probability( self, new_p ): 
                self.probability = new_p 
                self.isDefault = False 
    __________________________________________________________________________________________________________________________________________________________________________________


    Remove Chamber Note--> decided i don't need this because it makes sense that throughout experient user will want to add/remove different components, but doesn't make sense that they would want to remove an entire chamber. 
    Plus, if I do need this function, then i have to deal with ensuring that I am not removing a chamber with a vole currently in it. 
    For the same reasoning of I don't see why people would need to do this task mid-experiment, I also am not creating a remove_edge function

    def remove_chamber(self, id): 
        ''' remove Chamber object '''
        if self.get_chamber(id) is None: 
            raise Exception(f'chamber {id} does not exist, so cannot remove it from map')
        
        if self.graph[id].connections: 
            # connections dictionary is not empty; deal with edges 
            edges = self.graph[id].connections.values()
            raise Exception(f'You are trying to remove chamber {id} which is an endpoint in the following Edge objects that need to be removed first:' + str([f'{e}'for e in edges]))
        
        if self.graph[id].interactables: 
            # interactables list is not empty; deal with chamber's interactables 
            raise Exception(f'You are trying to remove chamber {id} which contains the following Interactables that need to be removed first:' + str([f'{i}'for i in self.graph[id].interactables]))

        del self.graph[id]
   
   
   def draw_map_helper(self, vertex_ids, edges): 

        # Base Case 
        if ( len(vertex_ids) == 0): return 
        else: 
            vertexid = vertex_ids.pop(0)
            chmbr = self.map.graph[vertexid]
            
            drawvoles = [] 
            drawedges = []

            for vole in self.voles: 
                if vole.current_loc == chmbr.id: drawvoles.append(vole.tag)

            for e in edges: 
                if ((e.v1 == vertexid) or (e.v1== vertexid)): 
                    # Current Chmbr has an undrawn edge; follow/draw this edge first 
                    drawedges.append(edges.remove(e)) # remove and add to edges to draw


            print(f'_____________\n|   (C{chmbr.id})    |')

            if len(drawvoles) > len(drawedges): 
                max = len(drawvoles)
            else: max = len(drawedges)

            for x in range(0,max): 
                if len(drawvoles)>0: 
                    v = drawvoles.pop() 
                space = 8 - len(str(v)) 
                if len(drawedges)>0: 
                    e = f' -------E{drawedges.pop().id}--------'
                print(f'|V[{v}]' + f"{'':>{space}}" + '|' + f'{e}')
            print(f'-------------')
    def draw_map(self): 
        ''' Recursively Prints Map and Voles '''

        edges = copy.deepcopy(self.map.edges)
        v_ids = self.map.graph.keys() 

        self.draw_map_helper(v_ids, edges)

        '''for cid in self.map.graph.keys(): 
            chmbr = self.map.graph[cid]
            cvoles = [] 
            for v in self.voles: 
                if v.current_loc == chmbr.id: cvoles.append(v.tag)
            print(f'_____________\n|   (C{chmbr.id})    |')

            for v in cvoles: 
                space = 8 - len(str(v)) 
                print(f'|V[{v}]' + f"{'':>{space}}" + '|')
            print(f'-------------')

            # Base Case: if vertices list is empty, return '''






{ 
    "chambers": [ 
        {
            "id": 1, 
            "descriptive_name": "Main Chamber", 
            "interactables": [
                {"interactable_name":"lever1", "type":"lever"},
                {"interactable_name":"water1", "type":"interactableABC"}, 
                {"interactable_name":"food1", "type":"food"}
            ] 
        }, 

        {
            "id": 2, 
            "descriptive_name": "Chamber 2", 
            "interactables": []
        }, 

        {
            "id": 3, 
            "descriptive_name": "Chamber 3",
            "interactables": [
                { "interactable_name":"wheel1", "type":"wheel" }
            ]
        }
    
    ], 

    "edges": [
        {
            "start_chamber_id":1, 
            "target_chamber_id":2, 
            "id":12, 
            "type":"shared", 
            "components":[
                { "interactable_name":"rfid1", "type":"rfid" }, 
                { "interactable_name":"door1", "type":"door" }, 
                { "interactable_name":"rfid2", "type":"rfid" }
            ]
        }, 

        { 
            "start_chamber_id":1, 
            "target_chamber_id":3, 
            "id": 13, 
            "type":"shared", 
            "components":[
                { "interactable_name":"rfid3", "type": "rfid" }, 
                { "interactable": "door2", "type": "door" }, 
                { "interactable": "rfid4", "type": "rfid" }
            ]
        }
    ]
}