'''

CONTROL SCRIPT

'''

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
class ClosedBox(modeABC): 
    def __init__(self, timeout, map): 
        super().__init__(timeout,map)
    
    def __str__(self): 
        return 'Closed Box'
    
    def setup(self):
        door1 = self.map.instantiated_interactables['door1']
        

    def run(self):
        pass
        


class OpenBox(modeABC):
    """
    Description: (Need To Implement!)
        Open Cage -- vole is free to roam in box. The door sits open the entire time. Lever presses have no effect on door functionality.
    """
    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Open Box'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
        # self.map.instantiated_interactables['door1'].open() # open the door
   
    def run(self):
        pass 


class BasicBox(modeABC):
    """
    Description: 
        << TODO >> 
    """
    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Basic Box'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
        pass   
  
    def run(self):
        print('Extending Levers!')
        lever1 = self.map.instantiated_interactables['lever_door1']
        lever2 = self.map.instantiated_interactables['lever_door2']
        lever_food = self.map.instantiated_interactables['lever_food'] 
        
        lever_list = [lever2, lever2, lever_food]

        for l in lever_list: 
            l.extend() 

        while self.active: 

            # Retract Lever if there is a threshold event! # 
            for l in lever_list: 
                
                if len(l.threshold_event_queue.queue) > 0: 

                    l.retract() 

                    lever_list.remove(l)



class IteratorBox(modeABC): 
    '''
    Description: 
        << operant map. Each time a lever gets pressed we increment the goal number of presses >>
    '''
    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Iterator Box'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
        pass  
    
    def run(self): 
        ''' when lever presses reaches threshold, increment required number of presses '''
        pass 

class SimpleBox(modeABC): 
    '''
    Description: 
        << utilizes a simple map with 2 chambers and 1 edge, where there is a single rfid and door along the edge >> 
    '''
    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Simple Box'
    
    def setup(self): 
        pass 
    
    def run(self): 
        ''' simple map version! '''
        print('Fill In With Extra Logic for How We Want Box To Run!')
        pass 
