
""" 
Modes used for testing individual interactables. 
"""
import time
import queue

from ..Classes.ModeABC import modeABC

from Logging.logging_specs import control_log 

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
class Lever1(modeABC): 
    '''
    description: extends and retracts lever 1
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp=None):
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

        try: pressed = self.map.lever_door1.threshold_event_queue.get_nowait() 
        except queue.Empty: pressed = None 
        
        if pressed is not None: 
            # Pass Control to different mode :: Runtime Mode Creation
            return LeverFood(self.timeout, self.rounds, self.ITI, self.map, self.output_fp)            
        else: 
            return 

class Lever2(modeABC): 
    '''
    description: extends and retracts lever 2
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
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
    description: extends and retracts food lever 
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
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
    [description] opens and closes every door. 
    """
    
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Door Tests'


    def setup(self): 

        '''' any tasks to setup before run() gets called '''
        pass 

    def run(self):
        door_lst = []
        for (name, item) in self.map.instantiated_interactables.items(): 
            if item.type == 'door': 
                door_lst.append(item) 
        
        for d in door_lst:         
            d.open()
            time.sleep(8)
            d.close()




class LeverDoorConnectionTests(modeABC): 
    """
    [description] lever/door relationship testing
        everytime that lever1 meets threshold, reset the recorded number of presses to 0 and increment the required number of presses to open the door. 
        (should not have to manually open door, as this is an automated call set in the configuration file by the attribute threshold_callback_fn) 
    
    """
    
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
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

    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)
    
    def __str__(self): 
        return 'Dispenser Tests'
    
    def setup(self): 
        pass 

    def run(self): 
        
        # Goal: Dispense a Pellet 
        food_dispenser = self.map.instantiated_interactables['food_dispenser']
        food_dispenser.dispense() 