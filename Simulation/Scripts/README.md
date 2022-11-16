
# Simulation Scripts #

~~~python

from ..Classes.SimulationScriptABC import SimulationScriptABC

class Name_Of_Simulation_Script(SimulationScriptABC): 

    def __init__(self, mode): 
        super().__init__(mode)

    def run(self): 
        ''' logic goes here '''
~~~