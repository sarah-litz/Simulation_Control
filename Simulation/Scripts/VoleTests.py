import sys, time

# Local Imports
from ..Logging.logging_specs import sim_log
from ..Classes.SimulationABC import SimulationABC


# Map Instantiation 


# Control Scripts (Modes)
# (TODO) instantiate the modes that you want to run 
from Control.Scripts.StaticBox import ClosedBox, OpenBox, BasicBox




class OperantMapVole(SimulationABC): 
    
    
    def __init__(self, modes):
        
        super().__init__(modes) 

        self.modes = modes 
    
    def __str__(self): 

        return 'OperantMapVole'
   
    def chamberComponentSetTesting(self): 
        
        # for testing the potential switch from Chamber Components to a Chamber ComponentSet where we have a list of interactables stored in a single Component
        vole1 = self.get_vole(1)
        print("\n attempting move to food trough!")
        food = self.map.instantiated_interactables['food_trough']
        vole1.move_to_interactable(food)

    def moveToDoor1(self): 
        print(f'|||||  {self} Simulation moveToDoor1 is Running!   |||||')

        vole1 = self.get_vole(1)
        door1 = self.map.instantiated_interactables['door1']
        vole1.move_to_interactable(door1)
        
        self.get_vole(1).simulate_vole_interactable_interaction(self.map.instantiated_interactables['door1'])

        time.sleep(2)

        # Attempt at turning around... 
        vole1.move_to_interactable(self.map.instantiated_interactables['lever_door1'])
        
        print(f'{self} is O V E R ! ')
    
    def attemptMoveToChamber2(self): 

        self.get_vole(1).attempt_move(2)

    def attemptMoveToChamber1(self): 

        self.get_vole(1).attempt_move(1)
    
    def moveToChamber3(self): 

        self.get_vole(1).attempt_move(destination = 3) # vole attempts to move into chamber 3
        
        self.get_vole(1).move_to_interactable(self.map.instantiated_interactables['open_door2_button'])
    
    def voleInteractsWithDispenser(self): 
        '''
        this mode is used for testing basic functional of the food dipenser throughout its code building process!
        '''

        ''' goal: 
        1. simulate a lever food press in order to trigger a simulated pellet dispense 
        2. simulate a direction interaction with the dispenser which will simulate a pellet retrieval
        3. Simulate 2 lever presses in a row 
        4. simulate 2 pellet retrievals in a row 


        Results: 
        In total, this should sum to recording 3 lever presses and 2 retrievals. 
        This is because in step #3 when we simulate 2 lever presses in a row, we skip the second dispense because there is already a pellet in the trough at this point. 
        As a result, when we follow with 2 pellet retrieval simulations, only one of them will result in a pellet retrieval recording since there is only a single pellet in the trough. 
        '''
        
        # Retrieve Objects: vole #1, the lever that controls the food dispensing, and the food dispener/trough itself
        vole1 = self.get_vole(1)
        food_lever = self.map.instantiated_interactables['lever_food']     
        dispenser = self.map.instantiated_interactables['food_trough']


        # Lever press to trigger dispense 
        vole1.move_to_interactable(food_lever)
        print('______________LeverPress (1/3)______________')
        vole1.simulate_vole_interactable_interaction(food_lever)

        # pellet retrieval 
        vole1.move_to_interactable(dispenser)
        print('______________Pellet Retrieval (1/3)______________')
        vole1.simulate_vole_interactable_interaction(dispenser)

        # 2 lever presses in a row --> This requires pausing for a moment to allow the callback function to reset the press count to 0. If it is 2 presses super quick in a row, that will just be recorded as a single threshold event.
        vole1.move_to_interactable(food_lever)
        print('______________LeverPress (2/3)______________')
        vole1.simulate_vole_interactable_interaction(food_lever) # sets number of food_lever presses = required num of presses to trigger a dispense
        time.sleep(3) # allow a second for the callback function reset_presses() to get called.
        print('______________LeverPress (3/3)______________')
        vole1.simulate_vole_interactable_interaction(food_lever) # Edge Case: 2 disenses in a row. Should not work because a pellet is already in the trough. 

        # 2 Pellet retrievals in a row
        vole1.move_to_interactable(dispenser)
        print('______________Pellet Retrieval (2/3)______________')
        vole1.simulate_vole_interactable_interaction(dispenser) 
        print('______________Pellet Retrieval (3/3)______________')
        vole1.simulate_vole_interactable_interaction(dispenser) # Edge Case: 2 retrievals in a row. Should not work the second time because no pellet is present. 



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




