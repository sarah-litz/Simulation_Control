"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 12/5/2022
Property of Donaldson Lab at the University of Colorado at Boulder

Description: This is a simualion script file which derives from the abstract class SimulationScriptABC. Each run() method defines what vole movements and interactions we want to simulate.
Example Simulation Scripts; Use these simulation scripts as a simple outline of how simulation scripts should be defined. 

"""

## (TODO) if any extra packages are needed for defining mode logic, freely place import statements here 
from ..Classes.SimulationScriptABC import SimulationScriptABC  
##
import time

class RandomVoleMovements(SimulationScriptABC): 

    def __init__(self, mode): 
        super().__init__(mode)
    def run(self): 

        """ Write Simulation Logic Here! """
        vole1 = self.map.get_vole(tag=1)

        ## Set likelihood of vole sleeping to 100% 
        vole1.set_action_probability((vole1.attempt_move,8), 75)
        vole1.set_action_probability((time.sleep, 2), 1)

        for _ in range(0,5): 
            print('new random......\n\n\n\n')
            vole1.attempt_random_action()
