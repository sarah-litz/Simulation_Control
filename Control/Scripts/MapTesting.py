# Imports
import os,sys 
cwd = os.getcwd()

# print(os.getcwd())
dir_path = os.getcwd() + '/Control'
sys.path.append(dir_path)
# site.addsitedir(dir_path)
sys.path.append('/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation')
from Classes.Map import Map 


map = Map(cwd+'/Control/Configurations') # optional argument: map_file_name to specify filepath to a different map configuration file 
