
from ..Classes.SimulationScriptABC import SimulationScriptABC
    
class MoveTo2(SimulationScriptABC): 

    def __init__(self, mode): 
        super().__init__(mode)
    def run(self): 
        vole1 = self.map.get_vole(1)
        vole1.attempt_move(2)
        return 

class MoveTo1(SimulationScriptABC): 
    def __init__(self,mode): 
        super().__init__(mode)
    def run(self): 
        vole1 = self.map.get_vole(1)
        vole1.attempt_move(1)
        return