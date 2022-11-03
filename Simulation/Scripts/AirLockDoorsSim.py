import sys, time, threading
import concurrent.futures
import random

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

        vole1 = self.get_vole(1)
        vole2 = self.get_vole(2)

        v1_success = vole1.attempt_move(2) 
        v2_success = vole2.attempt_move(2)

        if not v1_success or not v2_success: 

            for n in range(1): 

                if not self.current_mode.active: # and not v2_success 

                    return 
                
                else: 
                    
                    # 3 attempts to succeed on attempted move into chamber 2

                    if not v1_success: 

                        # Second Attempt 
                        v1_success = vole1.attempt_move(2)
                    
                    if not v2_success: 

                        v2_success = vole2.attempt_move(2)

        return 

    def threaded_vole_movements(self): 

        vole1 = self.get_vole(1)
        vole2 = self.get_vole(2)
        
        #
        # Voles will attempt to make a move at the same time. Goal Result: This should Fail the Recheck and door2 should not open!
        #

        print('\n\n    Both Voles Attempt Move into Chamber 2')
        v1 = threading.Thread(target = vole1.attempt_move, args=(2,), daemon=True) # attempt move into chamber 2
        v2 = threading.Thread(target = vole2.attempt_move, args=(2,), daemon=True) # attempt move into chamber 2

        v1.start()
        v2.start()

        v1.join() 
        v2.join()


        #
        # Move voles Back into Chamber 1 to "reset"
        #
        print('\n\n    Moving Both Voles Back Into Chamber 1')
        v1 = threading.Thread(target = vole1.attempt_move, args=(1,), daemon=True) # attempt move into chamber 1
        v2 = threading.Thread(target = vole2.attempt_move, args=(1,), daemon=True) # attempt move into chamber 1

        v1.start()
        v2.start()

        v1.join()
        v2.join()

        #
        # Vole 2 attempts a move into chamber 2, while Vole 1 interacts with the food lever. Goal Result: This should pass the recheck and door1 should close and door2 should open! 
        #
        print('\n\n    Vole 1 Interacts with lever_food while Vole 2 Attempts Move into Chamber 2')
        v1 = threading.Thread(target = vole1.simulate_move_and_interactable, args=(self.map.lever_food,), daemon=True) # interact with the food lever 
        v2 = threading.Thread(target = vole2.attempt_move, args=(2,), daemon=True) # attempt move into chamber 2

        v1.start()
        v2.start()

        print('\n\n    Vole2Attempt2 Move into Chamber 2')
        if vole2.curr_loc == self.map.get_chamber(2): 
            pass
        else: 
            # reattempt the move into chamber 2 
            vole2.attempt_move(2)    
        
        # Final Visual before Sim Finishes
        self.map.draw_map()
    


    def three_threaded_voles(self): 
        ''' 3 voles make moves at same time '''

        vole1 = self.map.get_vole(1)
        vole2 = self.map.get_vole(2)
        vole3 = self.map.get_vole(3)

        

        # 
        # LEAVING OFF HERE:: figure out a way to automate the idea that a vole is running on its own thread?! 
        # probably add a wrapper that gets called when certain vole methods get called 
        # wrapper should create a thread 
        # not super sure where to place the .join() call tho.... 
        # 
        
        executor = concurrent.futures.ThreadPoolExecutor()
        v1_future = executor.submit(vole1.attempt_move, random.randint(1,4))
        v2_future = executor.submit(vole2.attempt_move, random.randint(1,4))
        v3_future = executor.submit(vole3.attempt_move, random.randint(1,4))


        #with concurrent.futures.ThreadPoolExecutor() as executor:
        #    executor.map(, )
