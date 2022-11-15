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
from .Scripts.Operant_NewFormat import Lever1_Clicks, Lever2_Clicks, LeverFood_Clicks
from .Scripts.AirLockSimClasses import MoveTo2, MoveTo1

from .Classes.SimulationABC import SimulationABC


# (TODO) 
CONTROL_SIM_PAIRS = { 
    "Lever1": Lever1_Clicks, 
    "Lever2": Lever2_Clicks, 
    "LeverFood": LeverFood_Clicks, 
    # "Chamber1Access": MoveTo2, 
    # "Edge12Access": MoveTo2, 
    "Chamber2Access": MoveTo1 
}

def main(): 

    ''' 
    passes <modes> to SimulationABC the simulation parent package 
    '''

# Helper Function for creating "checkpoints" throughout the experiments execution that wait for user input before continuing with experiment execution. 
def input_before_continue(message):
    print(f'{message}')
    input(f'press the enter key to continue!')
    return 

sim_log('\n\n\n\n-----------------------------Simulation Package Started------------------------------------')


# (TODO) Instantiate the Simulation Classes that you want to run.

# airlock_sim = AirLockDoorsSim( modes = modes ) # create simulation, pass list of modes as argument 
# operant_sim = OperantSim( modes = modes )
simulation = SimulationABC( modes = modes )

# (TODO) Update the list of simulation scripts. They will be paired with a control mode based on the order that they are written below.
# simulation_script = [ operant_sim ]


# (TODO) Pair Each Mode with Simulation Function that should get run when the mode starts running.
# operant_sim.simulation_func[ modes[0] ] = [ operant_sim.lever1 ]
# airlock_sim.simulation_func[ modes[1] ] = [ airlock_sim.non_threaded_vole_movements ] 
# SimulationScript.simulation_func[ modes[2] ] = [ SimulationScript.foodlever ]
# SimulationScript.simulation_func[ modes[3] ] = [ SimulationScript.move_request1, SimulationScript.move_request2, SimulationScript.move_request3 ]


# Nothing to change here; this code creates a table so the User can double check all of the control mode / simulation function pairings that are set in the previous "todo" 
print(f'\n Double Check that the following Control/Simulation Pairings look correct...') 
data = [ ['Control Mode', 'Simulation Scripts'] ]
'''for m in modes: 
    for SimulationScript in simulation_script: 
        if m in SimulationScript.simulation_func.keys(): 
            data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})', f' {[*(f.__name__ for f in SimulationScript.simulation_func[m])]}  ({(str(os.path.relpath(inspect.getfile(SimulationScript.__class__))))})' ])

        else: 
            data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})'] )'''

for m in modes: 
    # find each mode in CONTROL_SIM_PAIRS 
    print(m.__class__.__name__)
    if m.__class__.__name__ in CONTROL_SIM_PAIRS: 
        sim = CONTROL_SIM_PAIRS[m.__class__.__name__]
        simulation.simulation_func[m] = sim(m) # creates simulation and pairs it with control mode in simulation manager

simulation.control_sim_pairs = CONTROL_SIM_PAIRS # give copy of dictionary to simulation for runtime creation of modes 

for m in modes: 
    if m in simulation.simulation_func.keys(): 
        data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})', simulation.simulation_func[m]]) # f' {[*(f.__name__ for f in simulation.simulation_func[m])]}  ({(str(os.path.relpath(inspect.getfile(SimulationScript.__class__))))})' ])
    else: 
        data.append( [str(m) + f' ({str(os.path.relpath(inspect.getfile(m.__class__)))})'] ) 


Visuals.draw_table(data, cellwidth=80)
input_before_continue('')


# Start Simulation 
simulation.run_sim() # starts running simulation in daemon thread ( this will transfer control between the simulation functions as the active control mode changes )

time.sleep(1) # Pause Before Starting Modes 

# Loop to Enter Modes in Given Order
for mode in modes: 
    # (TODO) Comment out call to input_before_continue if you don't want program to wait for User Input in between Modes Executing.
    input_before_continue(f'ready to start running Control Software Mode: {mode}?')
    mode.enter() 


input_before_continue('Thats All! G O O D B Y E')






