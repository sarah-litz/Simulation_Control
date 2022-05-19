
# To Use These Specifications, place this import statement at top of file: 
# from .Logging.logging_specs import sim_log


import logging
import os
formatter = logging.Formatter('%(asctime)s %(message)s') # To Display Level Name (debug vs. info vs. etc): %(levelname)s 

## the basicConfig is currently set to filepath specific to my own file tree. 
## This is for testing purposes only. If causing errors, comment the following line out and run again. ##  
logging.basicConfig(filename='/home/pi/Litz/Litz_Simulation/Logging/eventlogging.log' , level=logging.DEBUG )
## -- ## 
cwd = os.getcwd() 
simulation_fp=cwd+'/Simulation/Logging/simulation.log'


def setup_logger(name, log_file, level=logging.DEBUG):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    # handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    # logger.setLevel(level)
    logger.addHandler(handler)

    return logger


simulation_logger = setup_logger('simulation_logger', simulation_fp, level = logging.debug)


def debug(message): 
    # this one uses the basicconfig filepath 
    logging.debug(message)


def sim_log(message): 
    simulation_logger.debug(message)







