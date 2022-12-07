"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 12/5/2022
Property of Donaldson Lab at the University of Colorado at Boulder

Description: This is a simualion script file which derives from the abstract class SimulationScriptABC. Each run() method defines what vole movements and interactions we want to simulate.
Example Simulation Scripts; Use these simulation scripts as a simple outline of how simulation scripts should be defined. 

Please Leave This File As Is! If using these scripts as a template to create a new simulation script, please copy and paste the contents into a new file before making changes. 
"""

## (TODO) if any extra packages are needed for defining mode logic, freely place import statements here 
from ..Classes.SimulationScriptABC import SimulationScriptABC  
##

class SimpleScript(SimulationScriptABC): 

    def __init__(self, mode): 
        super().__init__(mode)
    def run(self): 
        """ Write Simulation Logic Here! """

    



