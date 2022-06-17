# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC


class ThresholdTests(SimulationABC): 

    def __init__(self, modes): 

        super().__init__(modes)

        self.modes = modes 
    
    def __str__(self): 
        'threshold tests'
    
    def mode1_timeout(self): 

        ''' continuously '''