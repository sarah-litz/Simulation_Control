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

import Simulation 
cwd = os.getcwd() # current working directory
import time
from .Logging.logging_specs import sim_log
from Control.Classes.Map import Map
from Control.Classes.Timer import Visuals

# (Optional TODO) Import Your ModeABC Implementations Here using the following syntax: from Control.Scripts.your_file_name import modeName1, modeName2, etc. 
    #   the default import statement below uses the modes that are created in the __main__.py of the Control software 
from Simulation import modes # references Simulation/__init__ file to retrieve list of modes created in Control/__main__.py


# (TODO) Import your SimulationABC Implementations Here using the following syntax: from .Scripts.your_file_name import SimulationClassName
from .Scripts.OperantBoxSim import OperantSim
from .Scripts.DynamicBoxSim import DynamicBoxSimulation
from .Scripts.AirLockDoorsSim import AirLockDoorsSim


# Helper Function for creating "checkpoints" throughout the experiments execution that wait for user input before continuing with experiment execution. 
def input_before_continue(message):
    print(f'{message}')
    input(f'press the enter key to continue!')
    return 

sim_log('\n\n\n\n-----------------------------Simulation Package Started------------------------------------')


# (TODO) Instantiate the Simulation Classes that you want to run.

# SimulationScript = AirLockDoorsSim( modes = modes ) # create simulation, pass list of modes as argument 
SimulationScript = OperantSim( modes = modes )


# (TODO) Pair Each Mode with Simulation Function that should get run when the mode starts running.
SimulationScript.simulation_func[ modes[0] ] = [ SimulationScript.lever1 ]
SimulationScript.simulation_func[ modes[1] ] = [ SimulationScript.lever2 ] 
SimulationScript.simulation_func[ modes[2] ] = [ SimulationScript.foodlever ]
SimulationScript.simulation_func[ modes[3] ] = [ SimulationScript.move_request1, SimulationScript.move_request2, SimulationScript.move_request3 ]


# Nothing to change here; this code creates a table so the User can double check all of the control mode / simulation function pairings that are set in the previous "todo" 
print(f'\n Double Check that the following Control/Simulation Pairings look correct...') 
data = [ ['Control Mode', 'Simulation Scripts'] ]
for m in modes: 
    if m in SimulationScript.simulation_func.keys(): 
        data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})', f' {[*(f.__name__ for f in SimulationScript.simulation_func[m])]}  ({(str(os.path.relpath(inspect.getfile(SimulationScript.__class__))))})' ])

    else: 
        data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})'] )
Visuals.draw_table(data, cellwidth=80)
input_before_continue('')


# Start Simulation 
SimulationScript.run_sim() # starts running simulation in daemon thread ( this will transfer control between the simulation functions as the active control mode changes )

time.sleep(1) # Pause Before Starting Modes 

# Loop to Enter Modes in Given Order
for mode in modes: 
    # (TODO) Comment out call to input_before_continue if you don't want program to wait for User Input in between Modes Executing.
    input_before_continue(f'ready to start running Control Software Mode: {mode}?')
    mode.enter() 


input_before_continue('Thats All! G O O D B Y E')






