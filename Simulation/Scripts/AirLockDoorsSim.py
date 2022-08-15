import sys, time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC


class AirLockDoorsSim(SimulationABC): 

    def __init__(self, modes): 
        
        super().__init__(modes) 

        self.modes = modes 
    
    def __str__(self): 

        return 'Simulation for running with the Map Containing a 2-door Airlock System'
    

    
    def vole1_move_to_chamber2(self): 

        #
        # leaving off here --> next test should be with threaded voles, where 2 voles are attempting at the same time!! 
        # can maybe start by getting both voles to just go sit in front of door2 to see if the code works. 
        #
        vole1 = self.get_vole(1)

        vole2 = self.get_vole(2)

        vole1.attempt_move(2)

        vole2.attempt_move(2)

    def vole2_move_to_chamber2(self): 

        vole2 = self.get_vole(2)

        vole2.attempt_move(2)