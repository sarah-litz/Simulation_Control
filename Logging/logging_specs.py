
# To Use These Specifications, place this import statement at top of file: 
# from Logging.logging_specs import debug


import logging
import os
formatter = logging.Formatter('%(asctime)s %(message)s') # To Display Level Name (debug vs. info vs. etc): %(levelname)s 

cwd = os.getcwd() 
logging.basicConfig(filename=cwd + '/Logging/eventlogging.log' , level=logging.DEBUG, filemode='w' )
control_fp=cwd+'/Control/Logging/control.log'
simulation_fp=cwd+'/Simulation/Logging/simulation.log'


def setup_logger(name, log_file, level=logging.DEBUG ):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file, mode='w')        
    # handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    # logger.setLevel(level)
    logger.addHandler(handler)

    return logger



control_logger = setup_logger('# control_logger', control_fp, level = logging.debug)
simulation_logger = setup_logger('simulation_logger', simulation_fp, level = logging.debug)


def debug(message): 
    # this one uses the basicconfig filepath 
    logging.debug(message)


def sim_log(message): 
    simulation_logger.debug(message)

def control_log(message): 
    control_logger.debug(message)




