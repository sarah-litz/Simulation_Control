
''' 

Class: OperantSim 

contains a series of simulation functions for testing/running all aspects of an operant box

'''

from ..Classes.SimulationABC import SimulationABC


class OperantSim(SimulationABC): 
    ''' tests for the operant box ''' 

    def __init__(self, modes):
        super().__init__(modes) 
        self.modes = modes 
    
    def move_request1(self): 
        vole1 = self.get_vole(1)
        vole1.attempt_move(1) 
    def move_request2(self): 
        vole2 = self.get_vole(2)
        vole2.attempt_move(2)
    def move_request3(self): 
        vole3 = self.get_vole(3)
        vole3.attempt_move(1)


    def button_test(self): 
        ''' goal: check if door1_override_open_button is getting created, creating a buttonObj, and listening for an event '''
        door1_override_open_button = self.map.instantiated_interactables['open_door1_button']
        print('(Simulation: InteractableTests, ButtonTest) hello!')
        print(door1_override_open_button.active)
    
    def beam_test(self): 
        vole1 = self.get_vole(1)
        beam1 = self.map.instantiated_interactables['beam1_door1']
        beam2 = self.map.beam2_door1

        vole1.move_to_interactable(self.map.lever_door1)
        vole1.simulate_vole_interactable_interaction(self.map.lever_door1)
    
        vole1.move_to_interactable(beam1)
        vole1.simulate_vole_interactable_interaction(beam1)
        vole1.simulate_vole_interactable_interaction(beam1)

        vole2 = self.get_vole(2)
        vole2.move_to_interactable(beam1)
        vole2.simulate_vole_interactable_interaction(beam1)

        vole1.move_to_interactable(beam2)
        vole1.simulate_vole_interactable_interaction(beam2)
        return 

    def lever1(self): 
        ''' 
        simulate a lever vole interaction so we trigger a threshold event 
        '''

        print('running lever1 simulation')
        vole1 = self.get_vole(1)
        lever1 = self.map.instantiated_interactables['lever_door1']
        vole1.move_to_interactable(lever1)
        vole1.simulate_vole_interactable_interaction(lever1)
        print('finished lever1 simulation')

        return 

    def lever2(self):

        '''
        Lever2_door2 test
        '''
        lever2 = self.map.instantiated_interactables['lever_door2']
        vole1.move_to_interactable(lever2)
        vole1.simulate_vole_interactable_interaction(lever2)

        return 

    def foodlever(self):

        '''
        food_lever test
        '''
        foodlever = self.map.instantiated_interactables['food_lever']
        vole1.move_to_interactable(foodlever)
        vole1.simulate_vole_interactable_interaction(foodlever)

        return 

    