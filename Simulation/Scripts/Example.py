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

        ## Retrieve Vole Objects 
        vole1 = self.map.get_vole(tag = 1)  # retrieves vole1 
        
        ## Retrieve Interactable Objects
        lever1 = self.map.instantiated_interactables['lever_door1'] # (syntax option 1) retrieves the interactable object named lever_door1
        lever2 = self.map.lever_door2 # (syntax option 2) retrieves the interactable with the name lever_door2

        ## Call Methods on the Vole object to Simulation Vole Movements and Interactable Interactions 
        vole1.move_to_interactable(lever1) # simulate a vole1 movement from its current position to the location of lever1
        vole1.simulate_vole_interactable_interaction(lever1) # simulates vole1 pressing lever1 to cause a threshold event 
        vole1.simulate_move_and_interactable(lever2) # simulates a movement to lever2 and an interaction with lever2 

    



