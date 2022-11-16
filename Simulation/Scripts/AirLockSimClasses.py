
"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 11/16/2022
Description: This is a simualion script file which derives from the abstract class SimulationScriptABC. Each run() method defines what vole movements and interactions we want to simulate.

Property of Donaldson Lab at the University of Colorado at Boulder
"""

import threading 

from ..Classes.SimulationScriptABC import SimulationScriptABC

class MoveTo2(SimulationScriptABC): 

    def __init__(self, mode): 
        super().__init__(mode)
    def run(self): 
        vole1 = self.map.get_vole(1)
        vole1.attempt_move(2)
        return 

class MoveTo1(SimulationScriptABC): 
    def __init__(self,mode): 
        super().__init__(mode)
    def run(self): 
        vole1 = self.map.get_vole(1)
        vole1.attempt_move(1)
        return
    



