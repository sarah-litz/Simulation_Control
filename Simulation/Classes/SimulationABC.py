"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 4/6/2022
Description: Class definition for running a simulation version of an experiment. Tracks what mode the control software is running, and then simulates a vole's behavior with a simulated (or actual) hardware interactable.

Property of Donaldson Lab at the University of Colorado at Boulder
"""

# Local Imports 
from code import interact
from Logging.logging_specs import sim_log
from .Vole import Vole

# Standard Lib Imports 
import threading, time, json, inspect
import os
cwd = os.getcwd() 


class SimulationABC: 

    def __init__(self, modes, map): 
        
        self.voles = []
        
        self.map = map

        # configure sim: updates interactables w/ simulation attributes & instantiates voles 
        self.configure_simulation(cwd + '/Simulation/Configurations/simulation.json') 

        self.simulation_func = {} # dict for pairing a mode with a simulation function 

        self.modes = modes

        self.current_mode = None # contains the Mode object that the control software is currently running. 


    #
    # Threaded Simulation Runner 
    #
    def run_in_thread(func): 
        ''' decorator function to run function on its own thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 
    

    @run_in_thread
    def run_active_mode_sim(self, current_mode): 
        ''' 
        called from run_sim() 
        starts thread to run the simulation function 
        waits for current mode's timeout to end and immediately returns, killing the simulation function as a result 
        '''

        #
        # Wait for Mode's Timeout Interval
        while not current_mode.inTimeout and current_mode.active: # active mode not in Timeout
            # while not in timeout portion of mode, loop 
            time.sleep(0.5)

        sim_log(f'(Simulation.py, run_sim) The current mode ({current_mode}) entered in timeout. Checking for if a simulation should be run. ')

        #
        # Check for if simulation function exists for the current mode 
        if current_mode not in self.simulation_func.keys(): # no simulation function specified for this mode 
            # do nothing loop until current mode is inactive 
            sim_log(f'(Simulation.py, run_sim) No simulation function for {type(current_mode)}.')
            while current_mode.active: 
                time.sleep(0.5)
            return 

   
        sim_log(f'(Simulation.py, run_sim) {current_mode} is paired with the simulation function: {self.simulation_func[current_mode]}')
        

        #
        # Run the Mode's Simulation Function in separate thread. Exit when the running mode becomes inactive or exits its timeout interval. 
        sim_fn = self.simulation_func[current_mode]

        sim_thread = threading.Thread(target = sim_fn)

        current_mode.simulation_lock.acquire()  # grab lock to denote that simulation is running 
        sim_thread.start() 

        while current_mode.inTimeout and current_mode.active: 
            
            time.sleep(1)  # let the simulation continue to run while mode is both active and in timeout


        if sim_thread.is_alive(): 

            print(f'(Simulation.py, run_sim) {current_mode} ended, simulation is completing its final iteration and then exiting.')
            sim_log(f'(Simulation.py, run_sim) {current_mode} ended, simulation is completing its final iteration and then exiting.')
            
            sim_thread.join(1000) # wait for simulation to finish 
            if sim_thread.is_alive(): 
                print(f'(Simulation.py, run_sim) simulation for {current_mode} got stuck running. Forcing exit now.')
                sim_log(f'(Simulation.py, run_sim) simulation for {current_mode} got stuck running. Forcing exit now.')
        
        current_mode.simulation_lock.release() # release lock to denote that simulation for this mode finished running  
        return
        

    @run_in_thread
    def run_sim(self): 

        sim_log('(Simulation.py, run_sim) Daemon Thread for getting the active mode, and running the specified simulation while active mode is in its timeout period.')

        ''' This Function Runs Continuously Until the Experiment Ends 
                    Runs on a separate thread 
                    Get/waits for an active mode
                    Calls the function that is paired with the currently active mode '''

        # NOTE: the function that we call should potentially also run on its own thread, so then all this function does is 
        # loop until the active mode is not in Timeout or the current mode is inactive. Basically will just allow for a more immediate 
        # stopage of the simulation when a mode gets out of timeout and/or stops running 

        while True: 
            ''' we can assume that this thread will get killed when the main thread running the modes finishes '''
            ''' so we can just keep looping and assume that we are in between modes, and that a mode will eventually become active again '''


            # Set the Currently Active Mode 
            self.current_mode = self.get_active_mode() # update the current mode 

            
            while self.current_mode is None: # if no mode is currently active 
                # wait for a mode to become active 
                time.sleep(0.5)
                self.current_mode = self.get_active_mode() # update the current mode when one becomes active 

            sim_log(f'NEW MODE: (Simulation.py, run_sim) Simulation Updating for Control Entering a New Mode: {(self.current_mode)}')

            t = self.run_active_mode_sim(self.current_mode)
            t.join() 


            



                # (NOTE) Delete This Section with the iterator check!! 
                # Check if an iterator value was specified (num of times to call the sim function) 
            '''sim_iterator = None # specifies number of times to call the simulation function (optional)
                sim_fn = None # simulation function 
                
                if type(self.simulation_func[current_mode]) is tuple: # sim_iterator specified
                    # if the value is a tuple, then there is a specified number of times to run the function 
                    sim_iterator = self.simulation_func[current_mode][1]
                    sim_fn = self.simulation_func[current_mode][0]

                    # remove sim function from dictionary since we have a set num of times to run it, we don't want to retrieve it from dict again 
                    del self.simulation_func[current_mode]
                
                else: # no sim_iterator specified
                    # if the value is not a tuple, then the function should just rerun continuously until while loop can exit 

                while current_mode.inTimeout and current_mode.active:  # active mode is in timeout                  
                    if sim_iterator is None:  
                        sim_log(f'(Simulation.py, run_sim) Simulaton is calling the function:{sim_fn}')
                        sim_fn()  # calling function continuously throught timeout interval 
                    elif sim_iterator > 0:  
                        sim_log(f'(Simulation.py, run_sim) Simulaton is calling the function:{sim_fn}')
                        sim_fn() # function call for running the simulation 
                        sim_iterator -= 1 # decrement the iterator each run                    
                    time.sleep(2)'''
            



    def get_active_mode(self): 

        '''returns the mode object that is currently running ( assumes there is never more than one active mode at a given point in time ) '''
       
        for mode in self.modes: 
            if mode.active: 
                return mode 
        
        return None
    
    
    #
    # Vole Getters and Setters 
    #
    def setup_voles(self):  raise Exception('you need to add a setup_voles() method to your simulation! This is where you should add/initialize any voles that you want to Simulate.')

        # gets voles from the simulation configuration file

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
            input(f'Would you like to skip the creating of this vole and continue running the simulation? If no, the simulation and experiment will stop running immediately. Please enter: "y" or "n". ')
            if 'y': return 
            if 'n': exit() 

        # ensure that start_chamber exists in map
        chmbr = self.map.get_chamber(start_chamber) 
        if chmbr is None: 
            sim_log(f'trying to place vole {tag} in a nonexistent chamber #{start_chamber}.')
            print(f'trying to place vole {tag} in a nonexistent chamber #{start_chamber}.')
            print(f'existing chambers: ', self.map.graph.keys())
            while chmbr is None: 
                ans = input(f'enter "q" if you would like to exit the experiment, or enter the id of a different chamber to place this vole in.\n')
                if ans == 'q': exit() 
                try: 
                    start_chamber = int(ans)
                    chmbr = self.map.get_chamber(int(start_chamber)) 
                except ValueError as e: print(f'invalid input. Must be a number or the letter q. ({e})')            

                 

        # Create new Vole 
        newVole = Vole(tag, start_chamber, self.map)
        self.voles.append(newVole)
        return newVole

        
    def remove_vole(self, tag): 
        ''' removes vole object specified by the vole's tag '''
        vole = self.get_vole(tag)
        if not vole: sim_log(f'attempting to remove vole {tag} which does not exist, so cannot be removed')
        self.voles.remove(vole)




    #
    #  Vole/Map Visualization 
    #

    def draw_helper(self, voles, interactables): 

        # arguments: 
        #   interactables are string representations of interactable names 
        #       - to retrieve the actual object, use the function

        vole_interactable_lst = [] 
        if len(interactables) == 0: 
            # chamber or edge has no interactables. just draw voles 
            for v in voles: 
                vole_interactable_lst.append('Vole'+str(v.tag))
        
        for idx in range(len(interactables)): 
            # loop thru interactales w/in the edge or chamber
            i = interactables[idx]
            

            voles_before_i = [] 
            voles_after_i = []
            
            for v in voles: # for each interactable, loop thru the voles w/in the same chamber and check their component location 

                # for every vole located by the current interactable, append to list so we can draw it 
                if v.curr_component.interactable == i: 

                    # figure out if vole should be drawn before or after the interactable
                    if idx == 0: 

                        # edge case to avoid out of bounds error
                        if v.prev_component == None: 
                            # v before i 
                            voles_before_i.append('Vole'+str(v.tag))
                        
                        else: 
                            # i before v 
                            voles_after_i.append('Vole'+str(v.tag))
                    
                    elif v.prev_component.interactable == interactables[idx-1]: 
                        # draw v before i 
                        voles_before_i.append('Vole'+str(v.tag)) # append string representation for the vole 
                    else: 
                        # draw i before v 
                        voles_after_i.append('Vole'+str(v.tag)) # append string representation for the vole 

            # On Each Component, append to vole_interactable_lst in order to make one complete list with ordered voles/interactables 
            vole_interactable_lst.extend(voles_before_i)
            vole_interactable_lst.append(i.name)
            vole_interactable_lst.extend(voles_after_i)
        
        # make list of string names rather than the objects 
        return vole_interactable_lst
    
    def draw_chambers(self): 

        for cid in self.map.graph.keys(): 
            
            chmbr = self.map.get_chamber(cid)
            cvoles = [] 

            # get chamber voles 
            for v in self.voles: 
                if v.curr_loc == chmbr: 
                    cvoles.append(v)
            print(f'_____________\n|   (C{chmbr.id})    |')

            # get chamber interactables 
            interactables = [c.interactable for c in chmbr]

            # helper function to get list of ordered voles/interactables 
            vole_interactable_list = self.draw_helper(cvoles, interactables)

            
            def draw_name(name): 
                if len(str(name)) > 8: 
                    name = name[:7] + '-'
                space = 9 - len(str(name)) 
                print(f'|[{name}]' + f"{'':>{space}}" + '|')
            
            
            # Draw! 
            for name in vole_interactable_list: 
                draw_name(name)
                    
                        
            print(f'-------------')

    
    def draw_edges(self): 
        edges = self.map.edges
        for e in edges: 
            
            # Make List of Edge Voles
            evoles = []
            for v in self.voles: 
                # get voles that are on edge e 
                if v.curr_loc == e: 
                    evoles.append(v)

            # Make List of Edge Interactables        
            interactables = [c.interactable for c in e] # creates list of the interactable names 

            vole_interactable_lst = self.draw_helper(evoles, interactables)

            print(f'({e.v1}) <---{vole_interactable_lst}----> ({e.v2})')
    

    #
    # Add Simulation Features to Map 
    #
    def configure_simulation(self, config_filepath): 
        '''function to read/parse the simulation configuration file'''
        ''' Adds a simulation attribute to all of the interactables '''

        sim_log(f"(Simulation.py, configure_simulation) reading/parsing the file {config_filepath}")


        # opening JSON file 
        f = open(config_filepath)

        # returns json object as a dictionary 
        data = json.load(f) 

        # closing JSON file
        f.close() 


        ## add a simulation boolean attribute to each component that is on an edge in the map ## 
        # if an interactable doesn't exist in the json file, print message and set simulation attribute to be False 
        for (name, i) in self.map.instantiated_interactables.items(): # loop thru interactable names 

            # check if name was specified in the config file 
            for interactable_specs in data['interactables']:

                if interactable_specs['name'] == name:  
                    # give obj new attribute to represent if we should simulate the interactable or not  
                    setattr(i, 'simulate', interactable_specs['simulate']) 

                    # if provided, set the optional function to call for simulation process
                    if 'simulate_with_fn' in interactable_specs: 
                        setattr(i, 'simulate_with_fn', eval(interactable_specs['simulate_with_fn']))
            
                    break 
            
            if not hasattr(i, 'simulate'): 
                print(f'simulation.json did not contain the interactable {name}. sim defaults to False, so this interactable will not be simulated as the simulation runs.')
                sim_log(f'simulation.json did not contain the interactable {name}. sim defaults to False, so this interactable will not be simulated as the simulation runs.')
                setattr(i, 'simulate', False) 
        

        ## add Voles ## 
        for v in data['voles']: 
            self.new_vole(v['tag'], v['start_chamber'])

        return 




    #
    # Simulate Vole-Interactable Interactations
    #









if __name__ == '__main__': 
    
    print('SimulationABC is an Abstract Base Class, meaning you cannot run it directly. In order to run a Simulation, create a subclass of SimulationABC')