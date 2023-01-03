"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 12/5/2022
Property of Donaldson Lab at the University of Colorado at Boulder

Description: Example Control Modes: Use these control modes as a simple outline of how control modes should be defined. All classes should derive from ModeABC.

Please Leave This File As Is! If using these modes as a template to create a new Control mode, please copy and paste the contents into a new file before making changes. 

[Mode Classes Defined]
    OpenBox : opens all doors during setup and returns an instance of SimpleBox from its run() method, indicating that this mode should be run. 
    SimpleBox: no logic! This is a control mode in its simplest form, and provides no extra logic for how a box will operate. The box will be in this mode until SimpleBox has finished out its <timeout> interval. 
"""

## (TODO) if any extra packages are needed for defining mode logic, freely place import statements here 
from ..Classes.ModeABC import modeABC
## 


class SimpleBox(modeABC): 
    '''
    Description: No Logic! Box will operate as defined in the map configuration file. This mode will exit after <timeout> completes. 
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Simple Box'
    
    def setup(self): 
        """ setup the initial state of the box here before run() gets called """ 
    
    def run(self): 
        """ logic for how a box operates goes here (note that interactable child/parent relationships may have been defined in the map configurations) """



class OpenBox(modeABC):
    """
    Description: 
        Open Box provides free movement to vole(s); opens all doors in its setup() function. 
    """
    def __init__(self, timeout, rounds, ITI, map, output_fp=None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Open Box'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
        for (name, i) in self.map.instantiated_interactables.items(): 
            # call open on any door interactable in map. 
            if i.type == 'door': 
                i.open()
   
    def run(self):
        return SimpleBox(timeout=10, rounds=1, ITI = 5, map = self.map, output_fp = self.output_fp) 




