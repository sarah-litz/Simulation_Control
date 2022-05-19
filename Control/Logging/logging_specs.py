
# To Use These Specifications, place this import statement at top of file: 
# from .Logging.loggingspecs import control_log


import logging
import os
formatter = logging.Formatter('%(asctime)s %(message)s') # To Display Level Name (debug vs. info vs. etc): %(levelname)s 


## the basicConfig is currently set to filepath specific to my own file tree. 
## This is for testing purposes only. If causing errors, comment the following line out and run again. ##  
logging.basicConfig(filename='/Users/sarahlitz/Projects/Donaldson Lab/Vole Simulator Version 1/Box_Vole_Simulation/Logging/eventlogging.log' , level=logging.DEBUG )
## -- ## 

# Location of the Logging File the Control Software should write to
cwd = os.getcwd() 
control_fp=cwd+'/Control/Logging/control.log'


def setup_logger(name, log_file, level=logging.DEBUG):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    # handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    # logger.setLevel(level)
    logger.addHandler(handler)

    return logger


control_logger = setup_logger('control_logger', control_fp, level = logging.debug)

def debug(message): 
    # this one uses the basicconfig filepath 
    logging.debug(message)


def control_log(message): 
    control_logger.debug(message)





