""" 
This is an example scenario that someone would run for the home_cage experiment. This is written mostly with pseudocode but includes function names and classes where possible
"""
import os
import time
import threading 
import queue

from ..Classes.Timer import countdown
from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from Logging.logging_specs import control_log 




#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
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



