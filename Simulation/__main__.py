'''
Title: Simulation Executable
description:this file links a specified simulation class (a file w/in the Simulation/Scripts directory) 
            to run on top of a specified experimental class (a file w/in the Control/Scripts directory).
            
            If you want to change the script that will execute for the simulation and/or experiment, you will need to change the 
            import statements and the statements where the simulation and mode classes are instantiated. 
            This file contains a (TODO) to denote each of the places that these updates should be made. 
'''


# Imports
import inspect
import os 
cwd = os.getcwd() # current working directory
import time
from .Logging.logging_specs import sim_log
from Control.Classes.Map import Map


# (Optional TODO) Import Your ModeABC Implementations Here using the following syntax: from Control.Scripts.your_file_name import modeName1, modeName2, etc. 
    #   the default import statement below uses the modes that are created in the __main__.py of the Control software 
from Simulation import modes # references Simulation/__init__ file to retrieve list of modes created in Control/__main__.py


# (TODO) Import your SimulationABC Implementations Here using the following syntax: from .Scripts.your_file_name import SimulationClassName
from .Scripts.VoleTests import OperantMapVole
from .Scripts.InteractableTests import LeverTests, ButtonTests, RfidSimulatedPings


# Helper Function for creating "checkpoints" throughout the experiments execution that wait for user input before continuing with experiment execution. 
def input_before_continue(message):
    print(f'{message}')
    input(f'press the enter key to continue!')
    return 

sim_log('\n\n\n\n-----------------------------Simulation Package Started------------------------------------')


# (TODO) Instantiate the Simulation Classes that you want to run.
operantSim = OperantMapVole( modes = modes ) # create simulation, pass list of modes as argument 


# Pair Each Mode with Simulation Function that should get run when the mode starts running.
operantSim.simulation_func[ modes[0] ] = ( operantSim.attemptMoveToChamber2 ) # left most chamber
operantSim.simulation_func[ modes[1] ] = ( operantSim.attemptMoveToChamber1 ) # middle chamber
operantSim.simulation_func[ modes[2] ] = ( operantSim.moveToChamber3 ) # right most chamber
operantSim.simulation_func[ modes[3] ] = ( operantSim.renameThis ) # nothing happens




print(f'Double Check that the following looks correct...') 
for m in modes: 
    if m in operantSim.simulation_func.keys(): 
        input_before_continue(f' Control Mode: {m} is paired with Simulation {operantSim.simulation_func[m]}')
    else: 
        input_before_continue(f' Control Mode: {m} is not paired with a Simulation Funciton.')
# Start Simulation 
operantSim.run_sim() # starts running simulation in daemon thread

time.sleep(4) # Pause Before Starting Modes 

# Loop to Enter Modes in Given Order
# (TODO) Comment out calls to input_before_continue if you don't want program to wait for User Input in between Modes Executing.
for mode in modes: 
    input_before_continue(f'ready to start running Control Software Mode: {mode}?')
    mode.enter() 
    input_before_continue(f'{mode} finished running')


input_before_continue('Thats All! G O O D B Y E')






