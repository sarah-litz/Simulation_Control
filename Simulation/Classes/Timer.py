"""
Description: Generic Timer Functions that provide the user with information on the current stage of an executing simulation and/or experiment.
"""


import sys 
import time

from Control.Classes.Timer import PRINTING_MUTEX
from Control.Classes.Timer import COUNTDOWN_MUTEX
from Control.Classes.Timer import EventManager



class SimulationEventsManager(EventManager): 
    def __init__(self, simulation_class): 
        super().__init__(mode = simulation_class)
    


