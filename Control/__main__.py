
# Imports
import os 
cwd = os.getcwd()
from .Logging.logging_specs import control_log
from .Classes.Map import Map 

# (TODO) Import Your ModeABC Implementations here using the following syntax: from Scripts.your_file_name import mode_name_1, mode_name_2, etc.
from .Scripts.ModeScripts1 import mode1, mode2 
from .Scripts.HardwareTesting import LaserTests, LeverTests, DoorTests, ButtonTests, ButtonInteractableTests, LeverDoorConnectionTests, DispenserTests
from .Scripts.StaticBox import ClosedBox, OpenBox, SimpleBox
from .Scripts.DynamicBox import WaitFiveSecondsBeforeRetractOrClose, IteratorBox, ReactiveBox
from .Scripts.AirLockBox import AirLockDoorLogic

def main(): 

    # Helper Function for creating "checkpoints" throughout the experiments execution that wait for user input before continuing with experiment execution. 
    def input_before_continue(message):
        print(f'{message}')
        input(f'press the enter key to continue!')
        return 

    control_log(f'\n\n\nrunning {__name__}: New Experiment! ')


    # (TODO) Map Instantiation (which will also instantiate the hardware components) 
    map = Map(cwd+'/Control/Configurations') # optional argument: map_file_name to specify filepath to a different map configuration file 


    # (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
    airlockBox = AirLockDoorLogic(timeout = 120, map = map)
    intervalBox = WaitFiveSecondsBeforeRetractOrClose(timeout = 15, map = map)
    iteratorBox = IteratorBox(timeout = 15, map = map)
    reactiveBox = ReactiveBox(timeout = 30, map = map )

    # (TODO) Update the list of control mode scripts with each of the scripts you want to run, in the order that you want them to run in! 
    mode_scripts = [ airlockBox ]


    if __name__ != '__main__': # falls into this if the simulation package imported this module
        # (TODO) Add Any Modes that you want to get passed to the Simulation Package in the list here 
        # The modes will run in the order that they are placed in the list
        return mode_scripts

    # Visualizations 
    print('\n')
    map.print_interactable_table()
    print('\n')
    map.print_dependency_chain()
    map.draw_map()


    # loop thru specified control scripts and start the experiment
    for mode in mode_scripts: 
        # (TODO) Comment out call to input_before_continue if you don't want program to wait for User Input in between Modes Executing.
        input_before_continue(f'ready to start running Control Software Mode: {mode}?')
        mode.enter() 


if __name__ is '__main__': 
    main() 




