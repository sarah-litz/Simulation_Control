'''

[Title] Simulation Executable

[description] this file links a specified simulation class (a file w/in the Simulation/Scripts directory) 
            to run on top of a specified experimental class (a file w/in the Control/Scripts directory).
            
            If you want to change the script that will execute for the simulation and/or experiment, you will need to change the 
            import statements and the statements where the simulation and mode classes are instantiated. 
            This file contains a (TODO) to denote each of the places that these updates should be made. 

'''

# Standard Lib Imports
import inspect
import os
cwd = os.getcwd() # current working directory
import time

# Local Imports 
import Simulation 
from .Logging.logging_specs import sim_log
from Control.Classes.Map import Map
from Control.Classes.EventManager import EventManager
from Simulation import modes # references Simulation/__init__ file to retrieve list of modes created in Control/__main__.py
from .Classes.Simulation import Simulation


###### USER TODOs 

# (TODO) Import your Simulation Implementations Here using the following syntax: from .Scripts.your_file_name import SimulationClassName
from .Scripts.ThreadedVoleMovements import ThreadedMovements, ThreadedMovements_ThreeVoles
from .Scripts.OperantBox import Lever1_Clicks, Lever2_Clicks, LeverFood_Clicks
from .Scripts.AirLockSimClasses import MoveTo2, MoveTo1
from .Scripts.InteractableTests import RfidTest 
from .Scripts.Example import SimpleScript
from .Scripts.RandomVoleMovements import RandomVoleMovements

# (TODO) Pair Each Mode with Simulation Function that should get run when the mode starts running.
CONTROL_SIM_PAIRS = { 
    # "Mode_ClassName": Simulation_Script_ClassName
    "Lever1": Lever1_Clicks, 
    "Lever2": Lever2_Clicks, 
    "LeverFood": LeverFood_Clicks, 
    "Chamber1Access": MoveTo2, 
    "Edge12Access": MoveTo2, 
    "Chamber2Access": MoveTo1, 
    "OpenBox": RfidTest, 
    "SimpleBox": RandomVoleMovements
}

###### END OF REQUIRED USER TODOs


def main(): 

    ''' 
    passes <modes> to Simulation the simulation parent package 
    '''

    # Helper Function for creating "checkpoints" throughout the experiments execution that wait for user input before continuing with experiment execution. 
    def input_before_continue(message):
        print(f'{message}')
        input(f'press the enter key to continue!')
        return 

    # sim_log('\n\n\n\n-----------------------------Simulation Package Started------------------------------------')
    simulation = Simulation( modes = modes ) # Creates the Simulation Container to hold the Simulation Scripts. This should stay the same.  

    # this code creates a table so the User can double check all of the control mode / simulation function pairings that are set in the previous "todo" 
    print(f'\n Double Check that the following Control/Simulation Pairings look correct...') 
    data = [ ['Control Mode', 'Simulation Scripts'] ]
    for m in modes: 
        if m.__class__.__name__ in CONTROL_SIM_PAIRS: # find each mode in CONTROL_SIM_PAIRS 
            sim = CONTROL_SIM_PAIRS[m.__class__.__name__]
            simulation.simulation_func[m] = sim(m) # creates simulation and pairs it with control mode in simulation manager
    simulation.control_sim_pairs = CONTROL_SIM_PAIRS # give copy of dictionary to simulation for runtime creation of modes 
    for m in modes: 
        if m in simulation.simulation_func.keys(): 
            data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})', simulation.simulation_func[m]]) 
        else: 
            data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})'] ) 
    EventManager.draw_table(data, cellwidth=80)
    input_before_continue('')



    # Start Simulation 
    simulation.run_sim() # starts running simulation in daemon thread ( this will transfer control between the simulation functions as the active control mode changes )
    time.sleep(1) # Pause Before Starting Modes 
    
    # Loop to Enter Modes in Given Order
    for mode in modes: 
        # Optional (TODO): Comment out call to input_before_continue if you don't want program to wait for User Input in between Modes Executing.
        input_before_continue(f'ready to start running Control Software Mode: {mode}?')
        mode.enter() 

    input_before_continue('Thats All! G O O D B Y E')

main()






