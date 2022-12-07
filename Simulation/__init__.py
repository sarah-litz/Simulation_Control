
'''
imports Control Package and runs its main() funciton. 
Control Package will recognize that it is not being run directly from the command line
but rather it is being imported, and it will respond by returning a list of instantiated Modes 

variable modes stores the list of control software modes that we want to run
modes is accessed by __main__ of Simulation.
'''

from Control import __main__ as controlPackage 
modes = controlPackage.main() # retrieve list of Control Modes 