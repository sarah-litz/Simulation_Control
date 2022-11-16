"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 11/16/2022
Description: This is a simualion script file which derives from the abstract class SimulationScriptABC. Each run() method defines what vole movements and interactions we want to simulate.

Property of Donaldson Lab at the University of Colorado at Boulder
"""



from ..Classes.SimulationScriptABC import SimulationScriptABC


class Lever1_Clicks(SimulationScriptABC): 
    ''' Simulates Lever 1 Clicks '''

    def __init__(self, mode):
        super().__init__(mode) 
    
    def run(self): 
        ''' pair with control mode Lever1
        simulate move to lever1 and click '''
        print('running lever1 simulation')
        vole1 = self.map.get_vole(1)
        lever1 = self.map.instantiated_interactables['lever_door1']
        vole1.move_to_interactable(lever1)
        vole1.simulate_vole_interactable_interaction(lever1)
        print('finished lever1 simulation')
        return 

class Lever2_Clicks(SimulationScriptABC): 
    ''' Simulates Lever 2 Clicks '''

    def __init__(self, mode): 
        super().__init__(mode)
    
    def run(self): 
        ''' pair with control mode Lever2
        simulate move to lever2 and click '''
        
        print('running lever 2 simulation')
        vole1 = self.map.get_vole(1)
        vole1.move_to_interactable(self.map.lever_door2)
        vole1.simulate_vole_interactable_interaction(self.map.lever_door2)
        print('finished lever 2 simulation')

class LeverFood_Clicks(SimulationScriptABC): 
    ''' Simulates Food Lever Clicks '''

    def __init__(self, mode): 
        super().__init__(mode)
    
    def run(self): 
        ''' pair with control mode FoodLever 
        simulate move to food lever and click '''

        print('running lever food simulation')
        vole1 = self.map.get_vole(1)
        foodlever = self.map.instantiated_interactables['lever_food']
        vole1.move_to_interactable(foodlever)
        vole1.simulate_vole_interactable_interaction(foodlever)
        print('finished lever food simulation')
        return 
