'''
Title: Simulation Executable
description:this file links a specified simulation class (a file w/in the Simulation/Scripts directory) 
            to run on top of a specified experimental class (a file w/in the Control/Scripts directory).
            
            If you want to change the script that will execute for the simulation and/or experiment, you will need to change the 
            import statements and the statements where the simulation and mode classes are instantiated. 
            This file contains a (TODO) to denote each of the places that these updates should be made. 
'''


# Imports
import os 
cwd = os.getcwd() # current working directory
import time
from .Logging.logging_specs import sim_log
from Control.Classes.Map import Map



# (TODO) Import Your ModeABC Implementations Here using the following syntax: from Control.Scripts.your_file_name import modeName1, modeName2, etc. 
from Control.Scripts.ModeScripts_RandomVoles import mode1, mode2, mode3

# (TODO) Import your SimulationABC Implementations Here using the following syntax: from .Scripts.your_file_name import SimulationClassName
from .Scripts.SarahsSimulation import SarahsSimulation
from .Scripts.RandomVoles import RandomVoles
from .Scripts.ping_shared_rfidQ import SimulatePings


# Map Instantiation (which will also instantiate the hardware components) 
map = Map(cwd+'/Control/Configurations')


sim_log('\n\n\n\n-----------------------------New Simulation Running------------------------------------')


# (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
mode1 = mode1( timeout = 60, map = map ) 
mode2 = mode2( timeout = 60, map = map )
mode3 = mode3( timeout = 60, map = map )


# (TODO) instantiate the Simulation, pass in the Mode objects and map -- this should be using the class you imported in the second "todo"
# (TODO) in the modes argument, pass a list of all of the modes that you instantiated above. These should get passed in in the same order that they will run in.
sim = SimulatePings( modes = [mode1, mode2, mode3], map = map  ) 

sim_log(f'(sim_attempt_move.py, {__name__}) New Simulation Created: {type(sim).__name__}')

# simulation visualizations
sim.draw_chambers() 
sim.draw_edges() 


time.sleep(5) # pause before starting up the experiment 

# (TODO)
# indicate the simulation function to run when the mode enters timeout. Function will only run once, and if the mode ends its timeout period before simulation can end, then the simulation will be forced to exit at this point
sim.simulation_func[mode1] = (sim.mode1_timeout)
sim.simulation_func[mode2] = (sim.mode2_timeout) 
# sim.simulation_func[mode3] = (sim.mode3_timeout)

# runs simulation as daemon thread. 
sim.run_sim() 

# (TODO) calls to start the experiment 

mode1.enter() 

mode2.enter() 

mode3.enter()




