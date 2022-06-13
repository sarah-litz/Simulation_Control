""" 
HardwareTesting.py 
Tests that were used as hardware components were getting built up. Note that many of these test will not work now,
because they are calling functions that are now automated w/in the interactable. 
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


# # # 
# Old Test: ButtonInteractableTests; this won't work anymore because now the call for 
# listen_for_event() for the button is automated, and errors get thrown if we call it twice 
# since we cant add GPIO.add_event_detect twice for the same pin number
# # # 
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

        print(f'(HardwareTesting.py, ButtonInteractableTests, run()) Returning immediately because the test ({self}) is an out-of-date test.')
        return 
        
        # directly call listen for event on the override button's button object 

        # get button interactable 
        door1_override_open_button = self.map.instantiated_interactables['open_door1_button']

        # listen for an override press 
        door1_override_open_button.buttonObj.listen_for_event() 
        print(door1_override_open_button.isPressed)
        countdown(10, 'button is listening for press')
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

        print(f'(HardwareTesting.py, ButtonTests, run()) Returning immediately because the test ({self}) is an out-of-date test.')
        return 

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
        time.sleep(5)
        print("retracting food lever")
        lever_food.retract() 

        time.sleep(2)

        # Door1 Lever Tests
        print("extending door1 lever")
        lever_door1.extend() 
        time.sleep(5)
        print("retracting door1 lever")
        lever_door1.retract() 

        time.sleep(2)

        # Door2 Lever Tests
        print("extending door2 lever")
        lever_door2.extend() 
        time.sleep(5)
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


class LeverDoorConnectionTests(modeABC): 
    """
    Description: 
        lever/door relationship testing
    """
    
    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Lever-Door Tests'
    
    def setup(self): 
        pass 

    def lever1door1(self): 
        '''goal: everytime that lever1 meets threshold, increment it'''


    
