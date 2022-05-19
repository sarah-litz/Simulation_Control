
# Standard Lib Imports 
import site 
import sys
import os
import time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC



class RandomVoles(SimulationABC): 

    def __init__(self, modes, map):
        
        super().__init__(modes, map) 

        self.modes = modes 
    

    def mode1_timeout(self): 

        ## Logic for when Mode 1 Control Software Enters Timeout ## 
        ## Control Software Mode 1: Open Cage ## 
        

        # 
        # Simulation Goal: 1 Vole that makes random moves throughout the timeout
        # 

        # (NOTE) need to implement vole function that while in timeout, the vole just makes random moves 

        vole1 = self.get_vole(1)
        vole2 = self.get_vole(2)
        vole3 = self.get_vole(1)
        rfid1 = self.map.instantiated_interactables['rfid1']
        rfid2 = self.map.instantiated_interactables['rfid2']
        lever1 = self.map.instantiated_interactables['lever1']
        lever2 = self.map.instantiated_interactables['lever2']
        #door1 = self.map.instantiated


        # Chamber Traversal # 
        vole1.attempt_move(2) # success 
        vole1.attempt_move(1) # ISSUE: should succeed, because we never closed door1 again. 

        # vole2.simulate_vole_interactable_interaction(lever1)

        # vole1.attempt_move(1)
        

        # while self.modes[0].inTimeout: 
        '''vole1.simulate_vole_interactable_interaction(rfid1) # vole1 on edge side of rfid1
            vole1.simulate_vole_interactable_interaction(rfid1) # vole1 on chamber side of rfid1
            vole2.simulate_vole_interactable_interaction(rfid1)'''
            # if the rfids on an edge have unequal lengths, then we know vole did not complete move 
            # if the rfids on an edge have equal lengths, then vole did complete move 
            # but whole point is that we are abstracting away from any specific interactable types... 

            # maybe to interrupt the simulation we send an interrupt signal that we can catch from the simulation side?? 
            # then if we catch this signal, we can try to exit more cleanly somehow?? 


            # time.sleep(3)

            # vole1.attempt_random_action() # vole 1 makes random actions while in timeout '''


    def mode2_timeout(self): 
        ## Logic for when Mode 2 Control Software Enters Timeout ## 
        ## Control Software Mode 2: Closed Cage, Lever1 Opens Door1, then lever.required_presses increases by 1 ## 

        #
        # Simulation Goal: Lever is inactive, but vole eventually succeeds in making a move anyways thru use of attempt_random_action, rather than thru attempt_move function setting the lever value
        #
        vole1 = self.get_vole(1)
        
        # Start Vole in Chamber 1 or 2 
        if vole1.curr_loc > 2: # if vole is in chamber 3, position vole into chamber 1  to start
            vole1.attempt_move(1) 
        
        # Based on current location, get destination to move to 
        if vole1.curr_loc == 2: 
            destination = 1
        else: 
            destination = 2
        

        # Attempt 1 => Should Fail! 
        vole1.attempt_move(destination) # this move will not work because lever1 is not currently being simulated

        # manual simulation of a lever press 
        lever1 = self.map.instantiated_interactables['lever1']
        lever1.pressed += 1 

        # Attempt 2 => Should Succeed! 
        vole1.attempt_move(destination) # this move will work because we have manually increased the number of lever presses 
   


        #
        #   LEAVING OFF HERE!!!!!! 
        #   come up w/ a better system to reach the goal of this simulation

        # interactable.active if we want the watch_for_threshold_event to be running
        # interactable.simulate if we want the Simulation software to reach the threshold goal of the interactable
        # 
        # neither of these allow for us to reach a threshold thru means of trial and error in the random_action() function
        # basically want a way of calling attempt_move where we simulate everything except for lever1. 
        # instead, we would want to reach the lever1 threshold thru repeated calls to random_action, which would eventually call the function to simulate vole and lever interaction 
        # as a result we dont want to set lever1.simulate to False, because we do want to simulate it, just thru the means of random_action not thru attempt_move function call. 
        # 


    def mode3_timeout(self): 
        # Control Software Mode3: same as Mode2. Closed box, lever1 will open door1. 

        #
        # Simulation Goal: 2 Voles that make a move at the same exact time (need to implement threading for the voles) 
        #

        pass 