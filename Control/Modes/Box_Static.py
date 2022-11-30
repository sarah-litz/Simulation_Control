'''

        Static Boxes: Control Scripts 
These boxes have no logic in their run function! Each has a different initial setup, 
but then they just sit idle until timeout finishes. All logic for box controls will 
be coming from the configuration files. 
'''

import os
import time
import threading 
import queue

from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from Logging.logging_specs import control_log 

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
class ClosedBox(modeABC): 
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)
    
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
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Open Box'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
        self.map.door1.open() 
        self.map.door2.open()
   
    def run(self):

        while self.active: 
            time.sleep(1)
        return SimpleBox(timeout=10, rounds=1, ITI = 5, map = self.map, output_fp = self.output_fp) 



class SimpleBox(modeABC): 
    '''
    Description: 
        << utilizes a simple map with 2 chambers and 1 edge, where there is a single rfid and door along the edge >> 
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Simple Box'
    
    def setup(self): 
        pass 
    
    def run(self): 
        ''' simple map version! '''
        print('Fill In With Extra Logic for How We Want Box To Run!')
        pass 
