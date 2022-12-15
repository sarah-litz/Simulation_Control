
# To Use These Specifications, place this import statement at top of file: 
# from .Logging.logging_specs import # sim_log


import logging
import os
formatter = logging.Formatter('%(asctime)s %(message)s') # To Display Level Name (debug vs. info vs. etc): %(levelname)s 

## specify filepaths for logging ## 
cwd = os.getcwd() 
logging.basicConfig(filename=f'{cwd}/Logging/eventlogging.log' , level=logging.DEBUG, filemode='w' )
simulation_fp=cwd+'/Simulation/Logging/simulation.log'
volepaths_fp=cwd+'/Simulation/Logging/volepaths.log'


def setup_logger(name, log_file, level=logging.DEBUG, mode = None):
    """To setup as many loggers as you want"""

    if mode is None: 
        handler = logging.FileHandler(log_file)        
    else: 
        handler = logging.FileHandler(log_file, mode = mode)
    # handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    # logger.setLevel(level)
    logger.addHandler(handler)

    return logger


simulation_logger = setup_logger('simulation_logger', simulation_fp, level = logging.debug)
volepath_logger = setup_logger('volepath_logger', volepaths_fp, level =  logging.debug, mode='w')


def debug(message): 
    # this one uses the basicconfig filepath 
    logging.debug(message)


def sim_log(message): 
    simulation_logger.debug(message)

def vole_log(message): 
    volepath_logger.debug(message)
    simulation_logger.debug(message)

def clear_log(logger): 
    with open(f'{logger}', 'w'): 
        pass 







