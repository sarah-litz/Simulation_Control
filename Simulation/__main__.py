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
from Control.Scripts.StaticBox import ClosedBox, OpenBox

# (TODO) Import your SimulationABC Implementations Here using the following syntax: from .Scripts.your_file_name import SimulationClassName
from .Scripts.SarahsSimulation import SarahsSimulation
from .Scripts.VoleTests import RandomVoles
from .Scripts.RFID_Simulation_Tests import SimulatePings
from .Scripts.InteractableTests import LeverTests, ButtonTests


# Map Instantiation (which will also instantiate the hardware components) 
map = Map(cwd+'/Control/Configurations', map_file_name = 'map_for_tests.json')


sim_log('\n\n\n\n-----------------------------New Simulation Running------------------------------------')

## Control Classes (Modes) ## 
# (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
mode1 = ClosedBox( timeout = 20, map = map ) 
mode2 = OpenBox( timeout = 20, map = map )
# mode3 = mode3( timeout = 60, map = map )



## Simulation Classes ##
# (TODO) instantiate the Simulation, pass in the Mode objects and map -- this should be using the class you imported in the second "todo"
# (TODO) in the modes argument, pass a list of all of the modes that you instantiated above. These should get passed in in the same order that they will run in.
sim1 = RandomVoles( modes = [mode1], map = map  ) 
# sim2 = ButtonTests( modes = [mode2], map = map )


# simulation visualizations
sim1.draw_chambers() 
sim1.draw_edges() 


time.sleep(5) # pause before starting up the experiment 

# (TODO)
# indicate the simulation function to run when the mode enters timeout. Function will only run once, and if the mode ends its timeout period before simulation can end, then the simulation will be forced to exit at this point
sim1.simulation_func[mode1] = (sim1.run)
# sim2.simulation_func[mode2] = (sim2.mode1_timeout)
# sim.simulation_func[mode2] = (sim.mode2_timeout) 
# sim.simulation_func[mode3] = (sim.mode3_timeout)



# (TODO) calls to start the experiment and the Simulations 

sim1.run_sim() # runs simulation as daemon thread. 

mode1.enter() # follow sim start by entering the first mode!

print('Sim1')
sim1.draw_chambers()
sim1.draw_edges() 

print(f'\nSim2')
sim2.draw_chambers() 
sim2.draw_edges() 

sim2.run_sim()

mode2.enter() 

mode3.enter()




