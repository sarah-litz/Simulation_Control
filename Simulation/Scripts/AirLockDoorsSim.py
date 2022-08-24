import sys, time, threading

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC


class AirLockDoorsSim(SimulationABC): 

    def __init__(self, modes): 
        
        super().__init__(modes) 

        self.modes = modes 
    
    def __str__(self): 

        return 'Simulation for running with the Map Containing a 2-door Airlock System'


    
    def non_threaded_vole_movements(self): 


        #
        # the Non-Parallel Execution of the Vole Movements works OK. 
        #

        #
        # leaving off here --> next test should be with threaded voles, where 2 voles are attempting at the same time!! 
        # can maybe start by getting both voles to just go sit in front of door2 to see if the code works. 
        #

        vole1 = self.get_vole(1)
        vole2 = self.get_vole(2)

        vole1.move_to_interactable(self.map.door1)
        vole2.move_to_interactable(self.map.door1)

        vole1.attempt_move(2) 
        vole2.attempt_move(2)

    def threaded_vole_movements(self): 

        vole1 = self.get_vole(1)
        vole2 = self.get_vole(2)
        
        vole1.move_to_interactable(self.map.lever_door1)
        vole1.simulate_vole_interactable_interaction(self.map.lever_door1)
        vole1.simulate_vole_interactable_interaction(self.map.lever_door1)
        print('lever_door1 THRESHOLD QUEUE after 2 interactions with lever_door1: ', self.map.lever_door1.threshold_event_queue.queue)
        
        #
        # Voles will attempt to make a move at the same time.
        #
        v1 = threading.Thread(target = vole1.attempt_move, args=(2,), daemon=True) # attempt move into chamber 2
        v2 = threading.Thread(target = vole2.attempt_move, args=(2,), daemon=True) # attempt move into chamber 2

        v1.start()
        v2.start()

        v1.join() 
        v2.join()