
from ftplib import FTP_PORT
from Map import Map 
from Simulation import SimulationABC 
from sim_attempt_move import SarahsSimulation
from ryan_example1 import mode1



# Map Configuration Filepath
fd = '/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation/Classes/Configurations'
fp = '/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation/Classes/Configurations/map.json'

#
# Setup Simulation w/ Map Specifications
#

# setup map 
map = Map(fd) 


# setup simulation
sim2 = SimulationABC(modes = [], map = map, vole_dict={1:1, 2:2, 3:3})


#
# Visualize Map after Setup
# 
# map.print_graph_info()
sim2.draw_chambers() 
sim2.draw_edges()





