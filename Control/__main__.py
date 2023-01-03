
# Imports
import os 
cwd = os.getcwd()
from .Logging.logging_specs import control_log
from .Classes.Map import Map 



### (TODO) Import Your ModeABC Implementations here using the following syntax: from Scripts.your_file_name import mode_name_1, mode_name_2, etc.
from .Modes.Testing_Hardware import Lever1, Lever2, LeverFood, DoorTests, LeverDoorConnectionTests, DispenserTests
from .Modes.Example import OpenBox, SimpleBox
from .Modes.Box_Dynamic import WaitFiveSecondsBeforeRetractOrClose, IteratorBox, ReactiveBox
from .Modes.Box_AirLock import Chamber1Access
from .Modes.Testing_Software import EventManagerTests



def main(): 
    # control_log(f'\n\n\nrunning {__name__}: New Experiment! ')

    ### (TODO) Map Instantiation (which will also instantiate the hardware components) 
    map = Map(cwd+'/Control/Configurations', 'map_operant.json') # optional argument: map_file_name to specify filepath to a different map configuration file 
    
    ### (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
    lever1 = Lever1(timeout = 20, rounds = 2, ITI = 10, map = map)
    simplebox = SimpleBox(timeout = 15, rounds = 1, ITI = 10, map = map)
    openbox = OpenBox(timeout = 15, rounds = 1, ITI = 10, map = map)
    airlockBox = Chamber1Access(timeout = 60, rounds = 1, ITI = 30, map = map)

    ### (TODO) Update the list <modes> with each of the scripts you may want to run ( can be conditionally ran as well )
    modes = [ lever1, simplebox, openbox, airlockBox ] # the specified modes will run in the order that they are placed in the list 


    #### END OF REQUIRED USER TODOs



    if __name__ != '__main__': 
        # called from Simulation Package; return instantiated modes 
        return modes

    # Visualizations 
    print('\n')
    map.print_interactable_table()
    print('\n')
    map.print_dependency_chain()
    map.draw_map()

    def input_before_continue(message): # Helper Function for creating "checkpoints" throughout the experiments execution that wait for user input before continuing with experiment execution. 
        print(f'{message}')
        input(f'press the enter key to continue!')
        return 
    for mode in modes: # loop thru specified control scripts and start the experiment
        # Optional (TODO): Comment out call to input_before_continue if you don't want program to wait for User Input in between Modes Executing.
        input_before_continue(f'ready to start running Control Software Mode: {mode}?')
        mode.enter() 

if __name__ == '__main__': 
    main() 




