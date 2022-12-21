
"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 4/6/2022
Description: Abstract Class for creating a script that contains the logic for running a simulation. 
This very simple class ensures that each simulation script created has a run() function and recieves the control mode object that it will run alongside of. 

Property of Donaldson Lab at the University of Colorado at Boulder
"""

    
# Local Imports 
from code import interact
from Logging.logging_specs import sim_log
from Simulation.Logging.logging_specs import vole_log, clear_log
from .Vole import SimVole

# Standard Lib Imports 
import threading, time, json, inspect, random, sys
from abc import abstractmethod, ABCMeta
import os
cwd = os.getcwd() 


class SimulationScriptABC(metaclass=ABCMeta): 

    def __init__(self, mode):
        """
        Args: 
            mode (ModeABC) : the mode class that inherits from ModeABC that the SimulationScriptABC child class will run alongside of.
        """
        self.mode = mode # the mode that this simulation script is paired with  
        self.map = self.mode.map 
        self.event_manager = self.map.event_manager
    
    @abstractmethod
    def run(self): 
        ''' override with logic '''
        return 
        raise NameError("This function must be overwritten with specific mode logic")
    
    
