""" 
This is an example scenario that someone would run for the home_cage experiment. This is written mostly with pseudocode but includes function names and classes where possible
"""
import os, sys
import time
import threading 
import queue
import importlib
from tkinter import Button


from ..Classes.Timer import countdown
from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from ..Classes.InteractableABC import interactableABC
Button = interactableABC.Button # button class (nested w/in interactableABC)

from Logging.logging_specs import control_log 




#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
class ButtonInteractableTests(modeABC): 
    '''
    Description: 
        OVERRIDE BUTTON TESTING 
        directly sets up a singular Door (door1) which has an override button declared as one of its dependents
    '''
    def __init__(self, timeout, map): 
        super().__init__(timeout, map)
    
    def __str__(self): 
        return 'button ineractable tests (aka override buttons)'
    
    def setup(self): 
        '''any tasks to setup before run() gets called'''
    
    def run(self): 

        # directly call listen for event on the override button's button object 

        # get button interactable 
        door1_override_open_button = self.map.instantiated_interactables['open_door1_button']

        # listen for an override press 
        door1_override_open_button.buttonObj.listen_for_event() 
        print(door1_override_open_button.isPressed)
        countdown(10, '                                                  button is listening for press')
        # listen for event for 10 seconds 
        print(door1_override_open_button.isPressed)



class ButtonTests(modeABC): 

    '''
    Description: 
        BUTTON TESTING 
        directly sets up a button and then calls listen_for_event() on the button at which point the hardware functionality can be tested. 
        Then, attempts setting up a lever which will in turn set up a button. Try to mimic the listen_for_event() from the lever. 
    '''

    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Button Tests'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
    
    def run(self): 

        ''' using 'door1_override_open_button' @ gpio pin #25 ( referenced LITZ_RPIOPERANT, operant_cage_settings_default.py)
        directly setup a button 
        required specifications: 
           button_specs = dict containing (button_pin) and (pullup_pulldown) 
           parentObj 
        '''

        class FakeParent: # Simulated Parent object in order to isolate Button Testing
            def __init__(self): 
                self.active = True 
        fakeParent = FakeParent() 
        
        button_specs = { 'button_pin': 25, 'pullup_pulldown': 'pullup' }
        door1_override_open_button = Button(button_specs = button_specs, parentObj = fakeParent) 

        print('button object created:', door1_override_open_button)
        # call listen_for_event() on the button --> run in a daemon thread
        door1_override_open_button.listen_for_event()
        print(door1_override_open_button.isPressed)
        countdown(10, '                                                  button is listening for press')
        # listen for event for 10 seconds 
        print(door1_override_open_button.isPressed)
        fakeParent.active = False # should cause listen_for_event to exit
        
        return  




        #
        # TEST 2 - SIMULATED BUTTON 
        #
        # in order to simulate a button, we can set its pressed_val = self.isPressed; this simulates the button currently being in a pressed state. 

class LeverTests(modeABC):
    
    """
    Description: 
        LEVER TESTING 
        extends and retracts levers
        
    """

    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Lever Tests'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''

          
    def run(self):
        # Run code of the class. This basically waits for the timeout

        lever_food = self.map.instantiated_interactables['lever_food']
        lever_door1 = self.map.instantiated_interactables['lever_door1']
        lever_door2 = self.map.instantiated_interactables['lever_door2']
        
        # Food Lever Tests 
        print("extending food lever")
        lever_food.extend() 
        time.sleep(3)
        print("retracting food lever")
        lever_food.retract() 

        time.sleep(3)

        # Door1 Lever Tests
        print("extending door1 lever")
        lever_door1.extend() 
        time.sleep(3)
        print("retracting door1 lever")
        lever_door1.retract() 

        time.sleep(3)

        # Door2 Lever Tests
        print("extending door2 lever")
        lever_door2.extend() 
        time.sleep(3)
        print("retracting door2 lever")
        lever_door2.retract() 

        return 




class DoorTests(modeABC):
    """
    Description: 
        DOOR TESTING
    """
    
    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Door Tests'


    def setup(self): 

        '''' any tasks to setup before run() gets called '''
        pass 

    def run(self):

        ## Timeout Logic ## 

        control_log('NEW MODE: Door Tests ')

        door2 = self.map.instantiated_interactables['door2']
        door1 = self.map.instantiated_interactables['door1']



        # Door 1 Tests
        print("opening door2 // current switch value: ", door2.isOpen)
        door2.open() 
        
        
        return 





class mode3(modeABC):
    """
    Description: 
        Closed Door -- lever1 requires set number of presses to open door1. Each time the vole presses the required number of times, then the nubmer of required lever presses is increased by 1. 
    
    Args:
        modeABC (class object): Inherited abstract base class
        timeout (int): amount of time that experiment runs. Begins after setup is completed. 
        map (class object): Map object that contains the hardware objects and where they are positioned in the layout of the box. 
        
    """
    
    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Mode 3'


    def setup(self): 

        '''' any tasks to setup before run() gets called '''
        pass 

    def run(self):

        ## Timeout Logic ## 

        self.inTimeout = True

        control_log('NEW MODE: Mode 3')

        # Logic to change the num presses every time the wheel is run  
        # if lever was pressed required number of times, open door, reset the tracked num of lever presses to 0  
        while self.active: 

            ## Timeout Logic ## 
            door1 = self.map.get_edge(12).get_interactable_from_component('door1') 
            lever1 = door1.dependents[0] 


            ## Wait for Lever Press or Timeout ## 

            event = None 
            while event is None and self.active: 
                
                try: event = lever1.threshold_event_queue.get_nowait() # loops until something is added. If nothing is ever added, then will just exit once timeout ends ( can add a timeout arg to this call if needed )
                except queue.Empty: pass 
                time.sleep(.5)

            if event is None:  # timed out before lever threshold event

                return 
            
            ## Lever Threshold Met ## 
            print(f"(mode3, run()) Threshold Event for lever1, event: {event}" )
            lever1.threshold_condition['goal_value'] += 1 # increase required number of presses by 1
            print(f"(mode3, run()) New Lever1 Threshold (required presses): {lever1.threshold_condition['goal_value']}")



