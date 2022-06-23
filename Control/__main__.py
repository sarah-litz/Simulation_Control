
# Imports
import os 
cwd = os.getcwd()
from .Logging.logging_specs import control_log
from .Classes.Map import Map 

# (TODO) Import Your ModeABC Implementations here using the following syntax: from Scripts.your_file_name import mode_name_1, mode_name_2, etc.
from .Scripts.ModeScripts1 import mode1, mode2 
from .Scripts.HardwareTesting import LeverTests, DoorTests, ButtonTests, ButtonInteractableTests, LeverDoorConnectionTests
from .Scripts.StaticBox import ClosedBox, OpenBox, BasicBox, IteratorBox, SimpleBox


def main(): 

    control_log(f'\n\n\nrunning {__name__}: New Experiment! ')

    # Map Instantiation (which will also instantiate the hardware components) 
    map = Map(cwd+'/Control/Configurations')
    # simpleMap =  Map(cwd+'/Control/Configurations', map_file_name = 'map_for_tests.json')

    # (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
    closedbox = ClosedBox(timeout = 30, map = map)
    openbox = OpenBox(timeout= 30, map = map)
    basicbox = BasicBox(timeout = 30, map = map)
    iteratorbox = IteratorBox(timeout = 30, map = map)
    simplebox = SimpleBox(timeout=30, map = map)


    if __name__ is not '__main__': # falls into this if the simulation package imported this module
        # (TODO) Add Any Modes that you want to get passed to the Simulation Package in the list here 
        # The modes will run in the order that they are placed in the list
        return [ closedbox, openbox, basicbox, iteratorbox, simplebox ]

    # (TODO) start experiment
    closedbox.enter()
    openbox.enter()
    basicbox.enter() 
    iteratorbox.enter() 
    simplebox.enter()


if __name__ is '__main__': 
    main() 




