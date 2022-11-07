'''

SIMULATION SCRIPT

'''

# Standard Lib Imports 
import site 
import sys
import os
import time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC






    
class ButtonTests(SimulationABC): 

    def __init__(self, modes): 

        super().__init__(modes)

        self.modes = modes 
    
    def __str__(self): 

        return 'Button Tests Simulation'

    def mode1_timeout(self): 

        ''' goal: check if door1_override_open_button is getting created, creating a buttonObj, and listening for an event '''

        door1_override_open_button = self.map.instantiated_interactables['open_door1_button']

        print('(Simulation: InteractableTests, ButtonTest) hello!')
        print(door1_override_open_button.active)


class BeamTests(SimulationABC): 

    def __init__(self, modes): 

        super().__init__(modes) 

        self.modes = modes     

    def mode1(self): 

        vole1 = self.get_vole(1)

        beam1 = self.map.instantiated_interactables['beam1_door1']
        beam2 = self.map.beam2_door1

        vole1.move_to_interactable(self.map.lever_door1)
        vole1.simulate_vole_interactable_interaction(self.map.lever_door1)
        
        vole1.move_to_interactable(beam1)
        vole1.simulate_vole_interactable_interaction(beam1)
        vole1.simulate_vole_interactable_interaction(beam1)


        vole2 = self.get_vole(2)
        vole2.move_to_interactable(beam1)
        vole2.simulate_vole_interactable_interaction(beam1)


        vole1.move_to_interactable(beam2)
        vole1.simulate_vole_interactable_interaction(beam2)
        return 

class LeverTests(SimulationABC): 

    def __init__(self, modes):
        
        super().__init__(modes) 

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




class LaserTests(SimulationABC): 
    ''' for testing the control mode LaserTest  '''
class DispenserTests(SimulationABC): 

    '''testing a vole interaction with dispenser and/or dispenser dependent '''

    def __init__(self, modes):
        
        super().__init__(modes) 

        self.modes = modes 
    

    def dispenser_interaction(self): 
        ''' goal: 
        1. simulate a lever food press in order to trigger a simulated pellet dispense 
        2. simulate a direction interaction with the dispenser which will simulate a pellet retrieval
        '''

        vole1 = self.get_vole(1)
        
        food_lever = self.map.instantiated_interactables['lever_food']

        vole1.move_to_interactable(food_lever)
        vole1.simulate_vole_interactable_interaction(food_lever)

        food_trough = self.map.instantiated_interactables['food_trough'] 

        vole1.move_to_interactable(food_trough)
        vole1.simulate_vole_interactable_interaction(food_trough)



    