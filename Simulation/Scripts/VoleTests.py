
# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC


# Map Instantiation 


# Control Scripts (Modes)
# (TODO) instantiate the modes that you want to run 
from Control.Scripts.StaticBox import ClosedBox, OpenBox, BasicBox




class SimpleMapVole(SimulationABC): 
    
    '''
    Current Description: 
        - Currently Running on top of the Control Mode 'ClosedBox' for 20 seconds, with a simpleMap (2 chambers, 1 edge, an rfid and door component only)
    Goal Description: 
    '''
    
    def __init__(self, modes):
        
        super().__init__(modes) 

        self.modes = modes 
    
    def __str__(self): 

        return 'Simulation.VoleTests.SimpleMapVole'
   
    def moveToDoor1(self): 
        
        print('SimpleMapVole(SimulationABC) Simulation moveToDoor1 is Running!')

        vole1 = self.get_vole(1)
        door1 = self.map.instantiated_interactables['door1']
        vole1.move_to_interactable(door1)
    
    def attemptMoveToChamber2(self): 

        print('SimpleMapVole(SimulationABC) Simulation moveToChamber2 is Running!')

        door1 = self.map.instantiated_interactables['door1']
        print( 'Door1 State: ', door1.isOpen ) 

        vole1 = self.get_vole(1)
        vole1.attempt_move(2)


    
    def renameThis(self): 

        print(' << SimpleMapVole: TODO SIMULATION in VoleTests.py >> ')

        return 
    



class OperantMapVole(SimulationABC): 

    def __init__(self, modes): 

        super().__init__(modes)

        self.modes = modes 

        print('MODES: ', modes )
    
    def __str__(self): 

        return 'VoleTests, AttemptMoveVole' 

    def attemptMoveToChamber2(self): 

        print('OperantMapVole(SimulationABC) Simulation attemptMoveToChamber2 is Running!')

        vole1 = self.get_vole(1) 
        print(f'Vole{vole1.tag} Starting Location: {vole1.curr_loc}, Starting Component Location: (',vole1.prev_component,', ', vole1.curr_component, ')')
        vole1.attempt_move(2) 

    

class ErrorCases(SimulationABC): 

    def __init__(self, modes):
        
        super().__init__(modes) 

        self.modes = modes 
    
    def run(self): 
        
        print('ErrorCases(SimulationABC) This is the run function!')

        # Test: New Vole Placed In the Chamber that is just for containing the Override Buttons 
        # Goal of Test: Shouldnt be able to place a vole in this chamber. We should get an error that this chamber does not exist. 
        self.new_vole(4,-1)




