
# Imports
import os 
cwd = os.getcwd()
from .Logging.logging_specs import control_log
from .Classes.Map import Map 

# (TODO) Import Your ModeABC Implementations here using the following syntax: from Scripts.your_file_name import mode_name_1, mode_name_2, etc.
from .Scripts.ModeScripts1 import mode1, mode2 
from .Scripts.HardwareTesting import LeverTests, DoorTests, ButtonTests, ButtonInteractableTests, LeverDoorConnectionTests
from .Scripts.StaticBox import ClosedBox, OpenBox


control_log(f'\n\n\nrunning {__name__}: New Experiment! ')

# Map Instantiation (which will also instantiate the hardware components) 
map = Map(cwd+'/Control/Configurations')

# (TODO) instantiate the modes that you want to run -- this should use the classes that you imported in the first "todo"
closedbox = ClosedBox(timeout = 30, map = map)
openbox = OpenBox(timeout= 30, map = map)
doorTests = DoorTests(timeout=30, map=map)
leverTests = LeverTests(timeout = 20, map = map)
leverdoorconnectiontests = LeverDoorConnectionTests(timeout = 40, map = map)


# (TODO) start experiment
leverdoorconnectiontests.enter() 
leverTests.enter()
closedbox.enter()
openbox.enter()




