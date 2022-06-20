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



# (TODO) Import Your ModeABC Implementations Here using the following syntax: from Control.Scripts.your_file_name import modeName1, modeName2, etc. 
from Control.Scripts.StaticBox import ClosedBox, OpenBox, BasicBox

# (TODO) Import your SimulationABC Implementations Here using the following syntax: from .Scripts.your_file_name import SimulationClassName
from .Scripts.SarahsSimulation import SarahsSimulation
from .Scripts.VoleTests import SimpleMapVole, OperantMapVole
from .Scripts.RFID_Simulation_Tests import SimulatePings
from .Scripts.InteractableTests import LeverTests, ButtonTests


def input_before_continue(message):
    print(f'{message}')
    input(f'press the enter key to continue!')
    return 


sim_log('\n\n\n\n-----------------------------Simulation Package Started------------------------------------')

from Simulation import modes # references Simulation/__init__ file to retrieve list of modes created in Control/__main__.py
operantSim = OperantMapVole( modes = modes ) # create simulation, pass list of modes as argument 
simpleMapSim = SimpleMapVole( modes = modes )

# Pair Each Mode with Simulation Function that should get run when the mode starts running.
simpleMapSim.simulation_func[ modes[0] ] = ( simpleMapSim.moveToDoor1 )
simpleMapSim.simulation_func[ modes[1] ] = ( simpleMapSim.attemptMoveToChamber2 )
# LEAVING OFF HERE! (at the following TODO marked in the next line)
simpleMapSim.simulation_func[ modes[2] ] = ( operantSim.attemptMoveToChamber2 ) # TODO! DON'T ALLOW SOMEONE TO PASS IN FUNCITON FROM A DIFFERENT CLASS BECAUSE THEN THE BOX BASICALLY RESETS AKA IT WONT RECALL WHERE THE VOLES LEFT OFF!

print(f'Double Check that the following looks correct...') 
for (k, v) in simpleMapSim.simulation_func.items(): 
    input_before_continue(f' Control Mode: {k} is paired with Simulation {v}')

# Start Simulation 
simpleMapSim.run_sim() # starts running simulation in daemon thread

time.sleep(4) # Pause Before Starting Modes 

# Loop to Enter Modes in Given Order
# (TODO) Comment out calls to input_before_continue if you don't want program to wait for User Input in between Modes Executing.
for mode in modes: 
    input_before_continue(f'ready to start running Control Software Mode: {mode}? Paired with simulation funciton: {simpleMapSim.simulation_func[ mode ]}')
    mode.enter() 
    input_before_continue(f'{mode} finished running')


input_before_continue('Thats All! G O O D B Y E')






