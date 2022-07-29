import sys, time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC


class DynamicBoxSimulation(SimulationABC): 

    def __init__(self, modes): 
        
        super().__init__(modes) 

        self.modes = modes 
    
    def __str__(self): 

        return 'Simulation for the Control Scripts in DynamicBox.py'
 
    def vole1_AttemptMoveToChamber2(self): 
        ''' 
        vole 1 presses lever that opens door 1
        vole 1 moves from chamber 1 -> chamber 2
        '''
        vole1 = self.get_vole(1)

        # Interactables
        lever_door1 = self.map.instantiated_interactables['lever_door1']
        lever_door2 = self.map.instantiated_interactables['lever_door2']
        door1 = self.map.instantiated_interactables['door1']
        rfid2 = self.map.instantiated_interactables['rfid2']
        door2 = self.map.instantiated_interactables['door2']
        rfid1 = self.map.instantiated_interactables['rfid1']
        rfid3 = self.map.instantiated_interactables['rfid3']


        vole1.move_to_interactable(lever_door1)
        vole1.simulate_vole_interactable_interaction(lever_door1)
        print('ATTEMPT MOVE')
        vole1.attempt_move(2)

        print('Simulation Over: Vole 1 simulates lever_door1 press and attempts a move into chamber 2.')
    
    def vole2_AttemptMoveToChamber2(self): 

        '''
        vole 2 presses lever that open door 1
        vole 2 moves from chamber 1 -> chamber 2 
        '''

        vole2 = self.get_vole(2)
        lever_door1 = self.map.instantiated_interactables['lever_door1']

        
        vole2.move_to_interactable(lever_door1)
        vole2.simulate_vole_interactable_interaction(lever_door1)
        vole2.attempt_move(2)





