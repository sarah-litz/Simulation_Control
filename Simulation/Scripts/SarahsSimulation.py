
# Standard Lib Imports 
import site 
import sys
import os
import time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC



class SarahsSimulation(SimulationABC): 

    def __init__(self, modes, map):
        
        super().__init__(modes, map) 



        '''Interactable Behavior: 
        - in running a simulation, we will automatically add an attribute to each interactable that allows 
        - default behavior ( if left unchanged )
        '''

        ## Set Interactable Behavior ## 
        # map.instantiated_interactables[]: 

    def mode1_timeout(self): 

        #
        # Script to specify what should happen when we enter mode1's timeout interval
        #
        sim_log(f'(SarahsSimulation.py, SarahsSimulation, mode1_timeout) Running the Mode 1 Simulation')
        print('Running the Mode 1 Simulation ')

        chmbr1 = self.map.graph[1]
        
        vole1 = self.get_vole(1)

        vole1.attempt_move(destination = 2)

        time.sleep(5)

        # self.simulate_interactable(chmbr1.interactables['door1'].dependent['lever1'].simulate(vole=1))

        print('Exiting the Mode 1 Simulation')

    def mode2_timeout(self): 

        #
        # Script to specify what should happen when mode2 enters its timeout interval
        #

        # In this Mode, the vole attempts to move from chamber 2->1, but this will fail because the door is closed
        # and the lever that controls the door is in chamber 1. 

        sim_log(f'(SarahsSimulation.py, SarahsSimulation, mode2_timeout) Running the Mode 2 Simulation')

        print('Running the Mode 2 Simulation')

        vole1 = self.get_vole(1)

        vole1.attempt_move(destination=1)

        time.sleep(5)

        print('Exiting the Mode 2 Simulation')

        return 
    
    def mode3_timeout(self): 

        #
        # Script to specify what should happen when mode3 enters its timeout interval 
        #

        #
        # This sim will run on the same box setup as mode2 did. 
        # Except this time We will simulate this vole3's interaction with the lever in order to open the door, since vole3 is the only vole in chamber 1 with the lever.
        # Then, vole1 will again attempt to move from chamber 2->1, this time where the door has already been opened by vole3. 
        #  

        sim_log(f'(SarahsSimulation.py, SarahsSimulation, mode3_timeout) Running the Mode 3 Simulation')

        print('Running the Mode 3 Simulation')

        vole1 = self.get_vole(1)

        # Add a New Vole to Chamber 1 
        vole3 = self.get_vole(3)

        # Get Lever 
        lever1 = self.map.instantiated_interactables['lever1']

        # Interact with the Lever 
        vole3.simulate_vole_interactable_interaction(lever1)

        # Vole 1 attempts to move into chamber 1
        vole1.attempt_move(destination=1)

        time.sleep(5)

        print('Exiting the Mode 3 Simulation')
        return         





    
