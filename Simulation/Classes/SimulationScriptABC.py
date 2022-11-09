
"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 4/6/2022
Description: Class definition for running a simulation version of an experiment. Tracks what mode the control software is running, and then simulates a vole's behavior with a simulated (or actual) hardware interactable.

Property of Donaldson Lab at the University of Colorado at Boulder
"""

    
# Local Imports 
from code import interact
from Logging.logging_specs import sim_log
from Simulation.Logging.logging_specs import vole_log, clear_log
from .Vole import Vole

# Standard Lib Imports 
import threading, time, json, inspect, random, sys
import os
cwd = os.getcwd() 


class SimulationScriptABC: 

    def __init__(self, mode):

        self.mode = mode # the mode that this simulation script is paired with  
        self.map = self.mode.map 
        
    def run(self): 
        ''' override with logic '''
        raise NameError("This function must be overwritten with specific mode logic")
    
    
