
# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC


# Map Instantiation 


# Control Scripts (Modes)
# (TODO) instantiate the modes that you want to run 
from Control.Scripts.StaticBox import ClosedBox, OpenBox, BasicBox




class OperantMapVole(SimulationABC): 
    
    '''
    Current Description: 
        - Currently Running on top of the Control Mode 'ClosedBox' for 20 seconds, with a simpleMap (2 chambers, 1 edge, an rfid and door component only)
    Goal Description: 
    '''
    
    def __init__(self, modes):
        
        super().__init__(modes) 

        self.modes = modes 
    
    def __str__(self): 

        return 'OperantMapVole'
   
    
    def moveToDoor1(self): 
        
        print(f'{self} Simulation moveToDoor1 is Running!')

        vole1 = self.get_vole(1)
        door1 = self.map.instantiated_interactables['door1']
        vole1.move_to_interactable(door1)
    
    def attemptMoveToChamber2(self): 

        self.get_vole(1).attempt_move(2)

    def attemptMoveToChamber1(self): 

        self.get_vole(1).attempt_move(1)
    
    def moveToChamber3(self): 

        self.get_vole(1).attempt_move(destination = 3) # vole attempts to move into chamber 3

    def renameThis(self): 

        print(f' << {self}: TODO SIMULATION in VoleTests.py >> ')
        return 
    


    

class ErrorCases(SimulationABC): 

    def __init__(self, modes):
        
        super().__init__(modes) 

        self.modes = modes 
    
    def run(self): 
        
        print('ErrorCases(SimulationABC) This is the run function!')

        # Test: New Vole Placed In the Chamber that is just for containing the Override Buttons 
        # Goal of Test: Shouldnt be able to place a vole in this chamber. We should get an error that this chamber does not exist. 
        self.new_vole(4,-1)



