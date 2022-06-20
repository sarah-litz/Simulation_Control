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

                    # # # # # # # # # # # # # # # # 
                    # # SIMPLE BOX EXPERIMENTS  # # 
                    # # # # # # # # # # # # # # # # 

# Map Instantiation (which will also instantiate the hardware components) 
simpleMap = Map(cwd+'/Control/Configurations', map_file_name = 'map_for_tests.json')

sim_log('\n\n\n\n-----------------------------New Simulation Running------------------------------------')

#
# CONTROL SCRIPTS 
#
# (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
simpleMapMode1 = ClosedBox( timeout = 40, map = simpleMap ) 
simpleMapMode2 = OpenBox( timeout = 40, map = simpleMap )
simpleMapMode3 = BasicBox( timeout = 40, map = simpleMap ) ## TODO-today: 


#
# SIMULATION SCRIPTS
#
# (TODO) instantiate the Simulation, pass in the Mode objects and map -- this should be using the class you imported in the second "todo"
# (TODO) in the modes argument, pass a list of all of the modes that you instantiated above. These should get passed in in the same order that they will run in.
simplemapSim = SimpleMapVole( modes = [simpleMapMode1, simpleMapMode2, simpleMapMode3] ) ## TODO-today: 

time.sleep(3) # pause before starting up the experiment 


# (TODO)
# indicate the simulation function to run when the mode enters timeout. Function will only run once, and if the mode ends its timeout period before simulation can end, then the simulation will be forced to exit at this point
simplemapSim.simulation_func[simpleMapMode1] = (simplemapSim.moveToDoor1)
simplemapSim.simulation_func[simpleMapMode2] = (simplemapSim.attemptMoveToChamber2)
simplemapSim.simulation_func[simpleMapMode3] = (simplemapSim.renameThis) ## TODO-today: 


# (TODO) calls to start the experiment and the Simulations 
simplemapSim.run_sim() # runs simulation as daemon thread. 
time.sleep(2) # Pause before starting
input_before_continue('Begin running Mode 1 of the Simple Map Experiment? Paired with the simulation function moveToDoor1 ')
#simpleMapMode1.enter() # follow sim start by entering the first mode!
input_before_continue('simpleMapMode1 finished. begin mode 2 of simple map experiment? Paired with the simulation function attemptMoveToChamber2')
simpleMapMode2.enter() 
input_before_continue('simpleMapMode2 finished. begin simpleMapMode3? Paired with no simulation function. Nothing will happen.')
simpleMapMode3.enter()

                    # # # # # # # # # # # # # # # # 
                    # # OPERANT BOX EXPERIMENTS # # 
                    # # # # # # # # # # # # # # # # 

# Map Instantiation (which will also instantiate the hardware components) 
operantMap = Map(cwd+'/Control/Configurations') 

sim_log('\n\n\n\n-----------------------------New Simulation Running------------------------------------')

#
# CONTROL SCRIPTS
#
# (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
operantMapMode1 = ClosedBox( timeout = 40, map = operantMap)
operantMapMode2 = OpenBox( timeout = 40, map = operantMap )
operantMapMode3 = BasicBox( timeout = 40, map = operantMap ) ## TODO-today: 


#
# SIMULATION SCRIPTS
#
# (TODO) instantiate the Simulation, pass in the Mode objects and map -- this should be using the class you imported in the second "todo"
# (TODO) in the modes argument, pass a list of all of the modes that you instantiated above. These should get passed in in the same order that they will run in.
operantmapSim = OperantMapVole( modes = [operantMapMode1, operantMapMode2, operantMapMode3] ) ## TODO-today: 


time.sleep(3) # pause before starting up the experiment 


# (TODO)
# indicate the simulation function to run when the mode enters timeout. Function will only run once, and if the mode ends its timeout period before simulation can end, then the simulation will be forced to exit at this point
operantmapSim.simulation_func[operantMapMode1] = (operantmapSim.attemptMoveToChamber2)
## TODO-today: add another function in the OperantMapVole class that we can run during the other modes!


# (TODO) calls to start the experiment and the Simulations 
operantmapSim.run_sim() # runs simulation as daemon thread. 
time.sleep(2) # Pause before starting
input_before_continue('Begin running operantMapMode1? ( Paired with the simulation function attemptMoveToChamber2')
operantMapMode1.enter() 
input_before_continue('operantMapMode1 has finished. Begin running operantMapMode2? Paired with no simulation funciton.')
operantMapMode2.enter() 
input_before_continue('operantMapMode2 has finished. Begin running operantMapMode3? Paired with no simulation function')
operantMapMode3.enter() 


print('G O O D B Y E')




