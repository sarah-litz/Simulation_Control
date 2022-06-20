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
        pass        
    def run(self):
        return 

        


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
        self.map.instantiated_interactables['door1'].open() # open the door
   
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
        print('Fill In With Extra Logic for How We Want Box To Run!')
        pass 