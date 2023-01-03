''' These Tests should not be run with the Simulation Package '''

import time 

from ..Classes.InteractableABC import door, lever
from ..Classes.ModeABC import modeABC
 

class LeverTest_Control(modeABC):
    
    """
    Description: 
        LEVER TESTING for control software only. Do not run simulation with this class.
        extends and retracts levers
        
    """

    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Lever Tests: Do not run with the Simulation Package! This is for purely hardware (control) tests only. Run LeverTests for a simulation-compatable lever test mode instead. '
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''

      
    def run(self):
        # Don't run this code with a Simulation. This is for hardware testing.
        # Run code of the class. This basically waits for the timeout

        lever_lst = []
        for (name, item) in self.map.instantiated_interactables.items(): 
            if type(item) == lever: 
                lever_lst.append(item)
        
        for l in lever_lst: 
            print(f'Testing {str(l)}.... ')
            inp = input(f'\n | press enter to extend {str(l)} (extended angle is {l.extended_angle}) | \n')
            l.extend()
            time.sleep(1)
            inp = input(f'\n | press enter to retract {str(l)} (retracted angle is {l.retracted_angle}) | \n')
            suc = l.retract()
            time.sleep(1)
        
        for l in lever_lst: 
            print(f"extending {str(l)} and will retract if {l.threshold_condition['attribute']} reaches {l.threshold_condition['goal_value']}.")
            l.extend()
            l.threshold_event_queue.get()
            l.retract()

        print('all done!')
        return 


class DoorTests_Control(modeABC):
    """
    Description: 
        DOOR TESTING
    """
    
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Door Tests'


    def setup(self): 

        '''' any tasks to setup before run() gets called '''
        pass 

    def run(self):

        ## Timeout Logic ## 

        # control_log('NEW MODE: Door Tests ')

        door_lst = []
        for (name, item) in self.map.instantiated_interactables.items(): 
            if type(item) == door: 
                door_lst.append(item) 
        

        for d in door_lst: 
            print(f'Testing {str(d)}.... ')
            inp = input(f'\n | press enter to open {str(d)} (sets speed to {d.open_speed}) | \n')
            d.open()
            time.sleep(1)
            inp = input(f'\n | press enter to close {str(d)} (sets speed to {d.close_speed}) | \n')
            suc = d.close()
            time.sleep(1)
            inp = input(f'\n | press enter to stop {str(d)} (sets speed to {d.stop_speed}) | \n')
            d.stop()
            time.sleep(1)

        print('all done')
        return