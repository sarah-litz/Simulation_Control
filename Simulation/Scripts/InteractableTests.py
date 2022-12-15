
"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 11/16/2022
Description: This is a simualion script file which derives from the abstract class SimulationScriptABC. Each run() method defines what vole movements and interactions we want to simulate.

Property of Donaldson Lab at the University of Colorado at Boulder
"""


# Standard Lib Imports 
import site 
import sys
import os
import time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationScriptABC import SimulationScriptABC



class ButtonTests(SimulationScriptABC): 
    def __init__(self, mode): 
        super().__init__(mode)
    def run(self): 
        ''' goal: check if door1_override_open_button is getting created, creating a buttonObj, and listening for an event '''
        door1_override_open_button = self.map.instantiated_interactables['open_door1_button']
        print('(Simulation: InteractableTests, ButtonTest) hello!')
        print(door1_override_open_button.active)

class RfidTest(SimulationScriptABC): 
    def __init__(self, mode): 
        super().__init__(mode)
    def run(self):
        ''' goal: move passed the rfid a couple times and make sure that it pings correct num of times '''
        vole1 = self.map.get_vole(1)
        vole2 = self.map.get_vole(2)
        vole1.move_to_interactable(self.map.door2) 
        vole1.move_to_interactable(self.map.door1)

class BeamTests(SimulationScriptABC): 
    def __init__(self, mode): 
        super().__init__(mode)   

    def run(self): 
        vole1 = self.map.get_vole(1)
        beam1 = self.map.instantiated_interactables['beam1_door1']
        beam2 = self.map.beam2_door1

        vole1.move_to_interactable(self.map.lever_door1)
        vole1.simulate_vole_interactable_interaction(self.map.lever_door1) 

        vole1.move_to_interactable(beam1)
        vole1.simulate_vole_interactable_interaction(beam1)
        vole1.simulate_vole_interactable_interaction(beam1)

        vole2 = self.map.get_vole(2)
        vole2.move_to_interactable(beam1)
        vole2.simulate_vole_interactable_interaction(beam1)

        vole1.move_to_interactable(beam2)
        vole1.simulate_vole_interactable_interaction(beam2)
        return 

class LeverTests(SimulationScriptABC): 
    def __init__(self, mode): 
        super().__init__(mode)
    
    def run(self): 
        ''' 
        simulate a lever_door1 vole interaction so we trigger a threshold event 
        '''
        vole1 = self.map.get_vole(1)
        lever1 = self.map.instantiated_interactables['lever_door1']
        vole1.move_to_interactable(lever1)
        vole1.simulate_vole_interactable_interaction(lever1)
        lever2 = self.map.lever_door2
        vole1.move_to_interactable(lever2)
        vole1.simulate_vole_interactable_interaction(lever2)
        return 


class LaserTests(SimulationScriptABC): 
    def __init__(self, mode): 
        super().__init__(mode)
    ''' for testing the control mode LaserTest  '''

class DispenserTests(SimulationScriptABC): 
    def __init__(self, mode): 
        super().__init__(mode)
    def run(self): 
        ''' goal: 
        1. simulate a lever food press in order to trigger a simulated pellet dispense 
        2. simulate a direct interaction with the dispenser which will simulate a pellet retrieval
        '''
        vole1 = self.map.get_vole(1)
        food_lever = self.map.instantiated_interactables['lever_food']
        vole1.move_to_interactable(food_lever)
        vole1.simulate_vole_interactable_interaction(food_lever)
        food_trough = self.map.instantiated_interactables['food_trough'] 
        vole1.move_to_interactable(food_trough)
        vole1.simulate_vole_interactable_interaction(food_trough)



    