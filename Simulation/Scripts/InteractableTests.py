# Standard Lib Imports 
import site 
import sys
import os
import time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC

class LeverTests(SimulationABC): 

    def __init__(self, modes, map):
        
        super().__init__(modes, map) 

        self.modes = modes 
    

    def mode1_timeout(self): 

        ''' 
        goal: test the onThreshold_callback_fn for lever_door1 

        simulate a lever_door1 vole interaction so we trigger a threshold event 
        
        '''
        vole1 = self.get_vole(1)

        lever1 = self.map.instantiated_interactables['lever_door1']

        vole1.move_to_interactable(lever1)
        vole1.simulate_vole_interactable_interaction(lever1)

        
        '''
        Lever2_door2 test
        '''
        lever2 = self.map.instantiated_interactables['lever_door2']

        vole1.move_to_interactable(lever2)
        vole1.simulate_vole_interactable_interaction(lever2)

        return 


