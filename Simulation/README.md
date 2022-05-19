
# Simulation Package

Property of Donaldson Lab at the University of Colorado at Boulder

## Overview

    description! 

## Commands for Running the Simulation Package on top of an experiment

If your experiment and simulation specifications have been completed (see [Writing Your Own Simulation] for steps to do this), position yourself in the directory 'Box_Vole_Simulation' and run the following command in the terminal:

`python3 -m Simulation`

**note**: *if upon running this command you recieve an "ImportError", double check that you are running this command from the 'Box_Vole_Simulation' directory.*

# Writing Your Own Simulation

## Configuring a Simulation

The following configuration file should exist in the Configurations directory:

> Simulation/Configurations/simulation.json

    This json file is where you will be specifying two aspects for how your simulation should run.

    1. "interactables" which is where you can specify which interactables you would like to simulate. (To see what interactables will be setup in the Map, reference the Map.json configuration file.) 
    2. "voles" which specifies the voles that you would like to simulate. 
 *It is important to take note of the vole tags that you specify here, because you can reference a specific vole from your simulation's script by using its tag value that is set by this configuration file.*

The following code block is an example of what this configuration file could look like.

~~~json
{
    "interactables": [
        {"name":"rfid1", 
            "simulate":true, 
            "simulate_with_fn": "lambda self, vole: self.rfidQ.put( (vole, self.ID) )" 
        }, 
        {"name":"door1", 
            "simulate":false
        }, 
        {"name":"rfid2", 
            "simulate":true, 
            "simulate_with_fn": "lambda self, vole: self.rfidQ.put( (vole, self.ID) )"  
        }, 
        {"name":"lever1", 
            "simulate":true
        }  
    ],
    "voles": [
        { "tag":1, "start_chamber":1 }, 
        { "tag":2, "start_chamber":2 }, 
        { "tag":3, "start_chamber":1 }
    ]
}
~~~

In the above  example, the user specifies that they would like to simulate rfid1, rfid2, and lever1, which likely means that these hardware pieces are not physically present in the box. The user specifies that they do not want to simulate door1, however, so we can assume that the user has a functional door in their box.

The user also specified the optional attribute "simulate_with_fn" for rfid1 and rfid2. This field is an anonymous function (or an inline funciton) written in python, which specifies how this interactable should be simulated. This replaces the default simulation behavior of an interactable, in which a specific object attribute is changed to meet its "goal value" to trigger a threshold event (reference the Control README for more information on this).

Finally, the user specified 3 different voles to instantiate when running the experiment, and also provided what chamber the vole should initially be created in.

## Writing a Simulation Script

    create a new file in the Simulation/Scripts directory. Within this file, you will implement a single new subclass of SimulationABC. 

## Linking a Simulation with an Experiment

    __main.py__ contains (TODO) markers for where you import and instantiate your implementations of simulation and your experiment. 
