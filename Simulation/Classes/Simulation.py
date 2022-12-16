"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 12/1/2022
Description: Class definition for running a simulation version of an experiment. Tracks what mode the control software is running, and then simulates a vole's behavior with a simulated (or actual) hardware interactable.

Property of Donaldson Lab at the University of Colorado at Boulder
"""

# Standard Lib Imports 
import threading, time, json, sys
import random # Do Not Delete. Necessary for lambda function in rfid config file.
import os
cwd = os.getcwd() 

# Local Imports 
from Logging.logging_specs import sim_log
from Simulation.Logging.logging_specs import vole_log, clear_log
from .Vole import SimVole


class Simulation: 

    def __init__(self, modes, config_filename = None): 

        """ Class that manages/runs the Simulation package. 
        Args: 
            modes ([ModeABC]) : an ordered list of control modes that will run 
        """
        
        print(f'\n Simulation Created: {self}')
                
        self.map = modes[0].map # default to the map of the first mode in the list. We will update map to the active modes map throughout experiemnt. 

        self.voles = self.map.voles # get any non-simulated voles that were setup by data from the map config file ( appends Simulated Voles to this list in the configure_simulation method )

        self.event_manager = self.map.event_manager # get event manager object from map 

        if config_filename is None: 
            
            self.configure_simulation(cwd + '/Simulation/Configurations/simulation.json') # configure sim: updates interactables w/ simulation attributes & instantiates voles 

        else: 

            self.configure_simulation(cwd + '/Simulation/Configurations/' + config_filename)

        self.simulation_func = {} # dict for pairing a mode with a simulation function ( or list of simulation functions )

        self.control_sim_pairs = {} # dict (assigned in __main__) that pairs a Mode Name with a Simulation Class

        self.modes = modes # Control modes that will run

        self.current_mode = None # contains the Mode object that the control software is currently running. 

    def __str__(self): 
        return __name__

    def run_in_thread(func): 
        ''' decorator function to run function on its own thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.name = func.__name__
            t.start() 
            return t
        return run 

    @run_in_thread
    def run_active_mode_sim(self, current_mode): 

        ''' called from run_sim() 
        Grabs the SimulationScript that is paired with the actively running Control Mode. 
        Starts the thread to run the simulation function, waits for current mode's timeout to end, and awaits the simulation function to return. 

        Args: 
            current_mode (ModeABC) : the control mode that is currently running 
        '''

        #
        # Wait for Mode's Timeout Interval
        while not current_mode.inTimeout and current_mode.active: # active mode not in Timeout
            # while not in timeout portion of mode, loop 
            time.sleep(0.5)

        # sim_log(f'(Simulation.py, run_active_mode_sim) The current mode ({current_mode}) entered in timeout. Checking for if a simulation should be run. ')

        #
        # Check for if simulation function exists for the current mode 
        if current_mode not in self.simulation_func.keys(): # no simulation function specified for this mode 
            
            # Check dictionary to make sure a simulation wasn't specified there 
            if current_mode.__class__.__name__ in self.control_sim_pairs: 
                
                # create the simulation and run it!
                sim = self.control_sim_pairs[current_mode.__class__.__name__]
                self.simulation_func[current_mode] = sim(self.current_mode)
            
            else: 

                # do nothing loop until current mode is inactive 
                # sim_log(f'(Simulation.py, run_sim) No simulation function for {type(current_mode)}.')
                print(f'(Simulation.py, run_sim) No simulation function for {type(current_mode)}.')      
                while current_mode.active: 
                    time.sleep(0.5)
                return 

   
        # sim_log(f'(Simulation.py, run_sim) {current_mode} is paired with the simulation function:  {self.simulation_func[current_mode]}') # {[*(f.__name__ for f in self.simulation_func[current_mode])]}')

        # print(f'(Simulation.py, run_sim) Running Simulation: {self.simulation_func[current_mode]}')
        # vole_log(f'(Simulation.py, run_sim) Running Simulation: {self.simulation_func[current_mode]}')


        # Activate Voles 
        for v in self.voles: 
            v.active = True 

        #
        # Run the Mode's Simulation Function in separate thread. Exit when the running mode becomes inactive or exits its timeout interval. 
        # sim_fn_list = self.simulation_func[current_mode]
        
        sim = self.simulation_func[current_mode]

        with current_mode.simulation_lock: # grab lock to denote that simulation is running 
            '''for sim_fn in sim_fn_list: 
                self.map.event_manager.print_to_terminal(f'\n     (Simulation.py, run_sim) New Simulation Function Running: {sim_fn.__name__}')
                sim_thread = threading.Thread(target = sim_fn, daemon=True)
                sim_thread.name = 'run sim function'
                sim_thread.start() '''
            if sim is not None: 
                self.map.event_manager.print_to_terminal(f'\n     (Simulation.py, run_sim) New Simulation Function Running: {sim}')
                sim_thread = threading.Thread(target = sim.run, daemon=True)
                sim_thread.name = 'simulations run function'
                sim_thread.start()

                while current_mode.inTimeout and current_mode.active and sim_thread.is_alive(): 
                    
                    time.sleep(1)  # let the simulation continue to run while mode is both active and in timeout

                if current_mode.inTimeout is False or current_mode.active is False: 
                    # mode ended, don't finish running other sim_fn
                    # break 
                    pass   
                        
            # If current mode ended before the current simulation, try to exit from simulation cleanly.... 
            if sim_thread.is_alive(): 
                # sim_thread.join(5) # see if simulation will stop running on its own     
                self.map.event_manager.print_to_terminal(f'(Simulation.py, run_sim) Control Mode <{current_mode}> ended with simulation still running.')
                # sim_log(f'(Simulation.py, run_sim) Control Mode <{current_mode}> ended with simulation still running.')
                
            if not current_mode.active: 
                self.map.event_manager.print_to_terminal(f'(Simulation.py, run_sim) Control Mode ended, final simulation function that ran was {sim}.') #  ( Full List of Functions set to run: {[fn.__name__ for fn in sim_fn_list]} )')
            if not current_mode.inTimeout: 
                self.map.event_manager.print_to_terminal(f'(Simulation.py, run_sim) Control Modes Timeout ended, final simulation function that ran was {sim}.') # ( Full List of Functions set to run: {[fn.__name__ for fn in sim_fn_list]} )')
            if not sim_thread.is_alive(): 
                self.map.event_manager.print_to_terminal(f'(Simulation.py, run_sim) Finished all simulations assigned to mode {current_mode}. ') # Sim Functions that completed this mode: {[fn.__name__ for fn in sim_fn_list]}')
            
            # Set Voles to Inactive 
            for v in self.voles: 
                v.active = False 

            sim_thread.join()
            # print(f'RETURNING FROM RUN_ACTIVE_MODE_SIM(). Sim Thread {sim_thread.name} // isAlive:', sim_thread.is_alive())
        
        return sim_thread
        
    @run_in_thread
    def run_sim(self): 

        ''' This Function Runs Continuously Until the Experiment Ends 
                Waits for a control mode to become active. When a control mode becomes active, calls run_sim() to execute a SimulationScript that is paired with the active mode. 
                Waits for the control mode to finish, and then repeats this process until all control modes have ran.
        
        Args : None 
        Returns : None
        '''

        self.map.print_interactable_table()
        print('\n')
        self.map.print_dependency_chain()
        self.map.draw_map(voles = self.voles)
        
        # sim_log('(Simulation.py, run_sim) Daemon Thread for getting the active mode, and running the specified simulation while active mode is in its timeout period.')


                       
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
                time.sleep(1)
                self.current_mode = self.get_active_mode() # update the current mode when one becomes active 

            # update the map to match the new current mode map; if the current map does not match the previous map, this may cause errors, so we should raise Exception explaining that a different instance of Simulation should get created to run for a different MAP instance 
            self.prevmap = self.map
            self.map = self.current_mode.map 

            if self.prevmap != self.map: 
                raise Exception(f'Modes Have Different Maps! The control modes that are running have different maps. Please create unique instances of the Simulation class for every unique Map instance that the Control Modes is running to avoid errors. Not running the simulation for this mode.')


            # sim_log(f'NEW MODE: (Simulation.py, run_sim) Simulation Updating for Control Entering a New Mode: {(self.current_mode)}')

            t = self.run_active_mode_sim(self.current_mode)
            t.name = 'run_active_mode_sim'
            t.join() 

            
            # print(f'BACK FROM RUNNING THE ACTIVE MODE SIM! THREAD STATE: {t.name}, {t.is_alive}')

            # if the current mode is still active, wait here until it finishes so we don't run a mode's simulation more than once. 
            while self.current_mode.active: 
                time.sleep(0.5)

    def get_active_mode(self): 
        ''' Retrieves the active mode from the event manager. (If a mode is running, it gets registered with the event_manager.)
        Args: None 
        Returns: 
            (ModeABC | None) : if there is an active mode, then returns that mode object. Otherwise, returns None to denote that there is not a currently active mode. 
        
        '''

        if self.event_manager.mode is not None and self.event_manager.mode.active: 
            print('Active Mode: ', self.event_manager.mode)
            return self.event_manager.mode 
        return None

    def configure_simulation(self, config_filepath): 
        '''function to read/parse the simulation configuration file. Sets interactable's isSimulation attribute accordingly. 
            Creates simulated vole objects (SimVole) and updates the list of voles to contain them. 
        
        Args: 
            config_filepath (string) : filepath to the simulation.json file containing the configurations for creating the Simulation
        
        Returns: 
            None 
        '''

        # sim_log(f"(Simulation.py, configure_simulation) reading/parsing the file {config_filepath}")


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
            set = False 
            for interactable_specs in data['interactables']: # find the instantiated interactables in the list of interactable specs
                if interactable_specs['name'] == name:  
                    
                    # set isSimulation value based on true/false val set in the config file
                    i.isSimulation = interactable_specs['simulate']
                    set = True 

                    # if provided, set the optional function to call for simulation process
                    if 'simulate_with_fn' in interactable_specs: 
                        setattr(i, 'simulate_with_fn', eval(interactable_specs['simulate_with_fn']))
            
                    break   

            if not set: # Simulation.json missing a config specification
                # no configurations for interactable i in simulation.json. Default isSimulation to True and print to screen to let user know.
                i.messagesReturnedFromSetup+=f'[simulation.json did not contain the interactable {name}. Defaults to True]'
                # sim_log(f'simulation.json did not contain the interactable {name}. sim defaults to True, so this interactable will be simulated as the simulation runs.')
                i.isSimulation = True 
            
            ''' if an object is set to be a Simulation, then automatically will set any Button and Servo Objects that it uses to be a simulation also. '''
            if i.isSimulation is True: 
                # ensure both buttonObj and servoObj are begin simulated
                if i.buttonObj is not None and i.buttonObj.isSimulation is False: 
                    i.buttonObj.isSimulation = True
                    i.buttonObj.pressed_val = -1 # -1 represents a simulated button
                    i.buttonObj.isPressed = False # set to Boolean value ( as apposed to calling method if it were initially not set to be a simulation )
                    # i.messagesReturnedFromSetup += f' simulating GPIO button. '
                if i.servoObj is not None and i.servoObj.isSimulation is False: 
                    i.servoObj.isSimulation = True
                    i.servoObj.servo = None
                    # i.messagesReturnedFromSetup += f' simulating servo.'


        ## add Voles ## 
        for v in data['voles']: 
            self.new_vole(v['tag'], v['start_chamber'], v['rfid_id'])
        return 

    #
    # Vole Getters and Setters 
    #
    def get_vole(self, tag): 
        '''searches list of voles and returns vole object w/ the specified tag
        Args: 
            tag (int) : tag id number assigned to the vole that will be searched for 
        Returns: 
            (Vole | SimVole) : vole object with <tag>. If it does not exist, returns None.
        '''
        for v in self.voles: 
            if v.tag == tag: return v  
        return None
    
    def get_vole_by_rfid_id(self, rfid_id): 
        ''' searches list of voles and returns vole object w/ the specified rfid id 
        Args: 
            rfid_id ( hex | int ) : the rfid chip (hex) value that was inserted in that vole. if vole does not have an rfid chip, then the rfid_id value is set to the same (int) value as the vole's tag. 
        Returns: 
            (Vole | SimVole) : vole object with <rfid_id>. If it does not exist, returns None.
        '''
        for v in self.voles: 
            if v.rfid_id == rfid_id: return v
        return None 

    def new_vole(self, tag, start_chamber, rfid_id): 
        ''' creates a new Vole object and adds it to the list of voles. 
        Args: 
            tag (int) : id assigned to a vole for simplicity. 
            start_chamber (int) : the id of the chamber that the vole is starting in. 
            rfid_id (hex|int) : the rfid chip's (hexidecimal) identifier. if value was not provided for rfid_id, then this value defaults to the same number as the vole's tag (int).  
        Returns: 
            (Vole|SimVole) : vole object on success '''

        if rfid_id is None: 
            # for simulated voles, if no rfid_id was specified then match this value to the tag value. This way, when we simulate an rfid ping, the Map class's rfidListener will still be able to search for the vole using the rfid_id
            rfid_id = tag 

        # ensure vole does not already exist 
        if self.get_vole(tag) is not None: 
            # sim_log(f'vole with tag {tag} already exists')
            print(f'you are trying to create a vole with the tag {tag} twice')
            inp = input(f'Would you like to skip the creating of this vole and continue running the simulation? If no, the simulation and experiment will stop running immediately. Please enter: "y" or "n". ')
            if inp == 'y': return 
            if inp == 'n': sys.exit(0)
            else: sys.exit(0)
        
        # ensure vole with same rfid_id does not already exist 
        if rfid_id is not None and self.get_vole_by_rfid_id(rfid_id) is not None: 
            # sim_log(f'vole with rfid_id {rfid_id} already exists')
            print(f'you are trying to create a vole with the rfid_id {rfid_id} twice')
            inp = input(f'Would you like to skip the creating of this vole and continue running the simulation? If no, the simulation and experiment will stop running immediately. Please enter: "y" or "n". ')
            if inp == 'y': return 
            if inp == 'n': sys.exit(0)
            else: sys.exit(0)        
        
        # ensure that start_chamber exists in map
        chmbr = self.map.get_chamber(start_chamber) 
        if chmbr is None: 
            # sim_log(f'trying to place vole {tag} in a nonexistent chamber #{start_chamber}.')
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
        newVole = SimVole(tag, start_chamber, rfid_id, self.map)
        self.voles.append(newVole)
        return newVole
    
    def remove_vole(self, tag): 
        ''' removes vole object specified by the vole's tag 
        Args: 
            tag (int) : vole's id assigned to the Vole that will be removed.
        Returns: 
            None 
        '''
        vole = self.get_vole(tag)
        if not vole: 
            # sim_log(f'attempting to remove vole {tag} which does not exist, so cannot be removed')
            return 
        else: 
            self.voles.remove(vole)    
    
    
if __name__ == '__main__': 
    
    print('Simulation is an Abstract Base Class, meaning you cannot run it directly. In order to run a Simulation, create a subclass of Simulation')