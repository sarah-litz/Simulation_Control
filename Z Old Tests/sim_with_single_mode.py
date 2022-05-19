
# Standard Lib Imports 
import time 

# Local Imports 
from Simulation import SimulationABC
from Map import Map
from ryan_example1 import mode1

# 
# This is just an example --> Doesn't actually run yet. (config_testing.py has a more working version)
# 
class SarahsSimulation(SimulationABC): 

    def __init__(self, modes, map, vole_dict={}):
        
        super().__init__(modes, map, vole_dict) 

  

    def mode1_timeout(self): 

        #
        # Script to specify what should happen when we enter mode1's timeout interval
        #
        
        print('Running the Mode 1 Simulation ')

        chmbr1 = self.map.graph[1]
        
        # chmbr1.interactables['wheel1'].simulate(vole=1)
        #self.simulate_interactable(chmbr1.interactables['wheel1'], vole=1) 

        vole1 = self.get_vole(1)

        # vole1.attempt_move(destination = 2)

        time.sleep(5)

        # self.simulate_interactable(chmbr1.interactables['door1'].dependent['lever1'].simulate(vole=1))

        print('Exiting the Mode 1 Simulation')

    def mode2_timeout(self): 

        #
        # Script to specify what should happen when mode2 enters its timeout interval
        #
        print('this shouldnt be getting called atm')
        return 




if __name__ == '__main__': 


    # instantiate map (which will also instantiate the hardware components) 
    map = Map('/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation/Classes/Configurations')

    
    # instantiate the modes that you want to run
    mode1 = mode1( timeout = 15, map = map ) 

    
    # instantiate the Simulation, pass in the Mode objects, map, and Voles to create
    sim = SarahsSimulation( modes = [mode1], map = map, vole_dict = { 1:1, 2:1 }  ) 

    # indicate the simulation function to run when the mode enters timeout 
    sim.simulation_func[mode1] = sim.mode1_timeout 

    
    # runs simulation as daemon thread 
    t1 = sim.run_sim() 


    # start experiment 
    mode1.enter() 
    mode1.run() 
    
