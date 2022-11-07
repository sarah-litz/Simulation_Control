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


from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from ..Classes.InteractableABC import interactableABC, door, lever, buttonInteractable, rfid
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


class Lever1(modeABC): 
    '''
    description: extends and retracts levers
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Lever Tests: Lever 1'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''

    def run(self):
        ''' control script logic '''
        self.map.lever_door1.extend()
        time.sleep(10)
        self.map.lever_door1.retract()

class Lever2(modeABC): 
    '''
    description: extends and retracts levers
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Lever Tests: Lever 2'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''

    def run(self):
        ''' control script logic '''
        self.map.lever_door2.extend()
        time.sleep(10)
        self.map.lever_door2.retract()

class LeverFood(modeABC): 
    '''
    description: extends and retracts levers
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Lever Tests: Food Lever'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''

    def run(self):
        ''' control script logic '''
        self.map.lever_food.extend()
        time.sleep(10)
        self.map.lever_food.retract()



class DoorTests(modeABC):
    """
    Description: 
        DOOR TESTING
    """
    
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Door Tests'


    def setup(self): 

        '''' any tasks to setup before run() gets called '''
        pass 

    def run(self):
        door_lst = []
        for (name, item) in self.map.instantiated_interactables.items(): 
            if type(item) == door: 
                door_lst.append(item) 
        
        for d in door_lst:         
            d.open()
            time.sleep(8)
            d.close()




class LeverDoorConnectionTests(modeABC): 
    """
    
    Description: 
        lever/door relationship testing

        everytime that lever1 meets threshold, reset the recorded number of presses to 0 and increment the required number of presses to open the door. 
        (should not have to manually open door, as this is an automated call set in the configuration file by the attribute threshold_callback_fn) 
    
    """
    
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Lever-Door Tests'
    
    def setup(self): 
        pass 

    def run(self): 
        '''goal: everytime that lever1 meets threshold, increment the required number of presses to open the door'''
        lever1 = self.map.instantiated_interactables['lever_door1']
        door1 = self.map.instantiated_interactables['door1']

        # Extend Lever 
        lever1.extend() 

        ## Wait for Lever Press or Timeout ## 
        while self.active: 

            event = None 
            while event is None and self.active: 
                
                try: event = lever1.threshold_event_queue.get_nowait() # loops until something is added. If nothing is ever added, then will just exit once timeout ends ( can add a timeout arg to this call if needed )
                except queue.Empty: pass 
                time.sleep(.5)

            if event is None:  # timed out before lever threshold event

                return 

            else: 
                ## Lever Threshold Met ## 
                print(f"{self}: {event}")  

                lever1.reset_press_count() # manually reset the number of lever presses to 0 so we start over 

                lever1.threshold_condition['goal_value'] += 1 # increase required number of presses by 1

                print(f"(mode2, run()) New Lever1 Threshold (required presses): {lever1.threshold_condition['goal_value']}")
            
        lever1.retract() 
    


class DispenserTests(modeABC):

    '''
    this mode is used for testing basic functional of the food dipenser throughout its code building process!
    '''

    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)
    
    def __str__(self): 
        return 'Dispenser Tests'
    
    def setup(self): 
        pass 

    def run(self): 
        
        # Goal: Dispense a Pellet 
        food_dispenser = self.map.instantiated_interactables['food_dispenser']
        food_dispenser.dispense() 



class LaserTests(modeABC): 

    '''
    used for testing basic functionality of the Lasers throughout its code building process!
    '''

    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)
    
    def __str__(self): 
        return 'Laser Tests'
    
    def setup(self): 
        
        # Assign Lasers to patterns that we want to run for this control mode! 

        laser1 = self.map.instantiated_interactables['laser_1']
        laser1.set_dutycycle_pattern = laser1.dutycycle_patterns['cycle1'] # sets the dutycyle pattern that we want to run in the coming mode 

        #laser2 = self.map.instantiated_interactables['laser_2']
        #laser2.set_dutycycle_pattern = laser2.dutycycle_patterns['cycle1']

    def run(self): 

        # Goal: mess with how we can do the dutycycle_pattern pairing with a mode

        # This Script is aware of what mode we are in! 

        # When do we want to trigger these laser events?? 

        print(f'{self} control mode is running!')


