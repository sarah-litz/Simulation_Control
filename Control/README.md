# Control Package

Property of Donaldson Lab at the University of Colorado at Boulder

## Description

    the control package contains the classes, configurations, and scripts used in running an experiment.  

## Command for Running an Experiment

`python3 -m Control`

# Writing Your Own Experiment

## Configuring an Experiment

    A file in Configurations directory should contain an entry for every interactable that you plan to add to the Map class. The map.json file is where ordering/layout of the different hardware interactables is defined. In order to ensure that all interactables are instantiated by the control software, make sure that it gets referenced somewhere in the Map class. 

## Writing an Experiment Script

    Scripts are written by creating subclasses of ModeABC. A single experiment can be made up of as many ModeABC subclasses as needed, where each subclass/mode represents a portion of the experiment with slightly different constraints than the other modes. 
    To add a new script, create a new file within the Scripts directory. 

    To link your new script with the rest of the program, follow the marked (TODOs) that are in the Control/__main__.py file.