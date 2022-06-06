# Control Package

Property of Donaldson Lab at the University of Colorado at Boulder

## Description

    the control package contains the classes, configurations, and scripts used in running an experiment.  

## Command for Running an Experiment

`python3 -m Control`

# Writing Your Own Experiment

## Configuring an Experiment with Map.json

    A file in Configurations directory should contain an entry for every interactable that you plan to add to the Map class. The map.json file is where ordering/layout of the different hardware interactables is defined. In order to ensure that all interactables are instantiated by the control software, make sure that it gets referenced somewhere in the Map class. 

    The only configuration file that is technically required is "map.json". If any components are specified within map.json, then it is required that we have configuration files for objects of that interactable type. These config files should be .json files, and get added to the same directory that map.json sits in. Ensure that the name of the file matches the "type" field for the object in map.json.

## Component Dependency Chain

The terms specified below are 4 attributes assigned to every Interactable that classifies an interactables behavior. The attributes "dependents" and "parents" are lists that get added based on the information provided in map.json. The attributes "barrier" and "autonomous" are booleans that default to Fales, but can/should be specified as True for specific interactables when it applies.

**dependents**
: list containing the "child" interactables belonging to the current interactable. Dependents are specified in a particular object's configuration dictionary within the "dependents" field. The example below would be found in the configuration file door.json. Here, we have assigned 1 dependent to door1 called lever_door1. We assigned lever_door1 as a dependent to door1 because a vole does not go up to a door and open it itself. Rather, the door1 movement is *dependent* on lever_door1. The vole will need to press lever_door1 some number of times in order to have the effect of opening door1.

    If an interactable has dependents assigned to it, all of its dependents must have already met their thresholds before the parent interactable can meet its own threshold. i.e. An interactable's dependents list should contain other interactables in the map that they depend on. 

    The interactable that specifies an object as its dependent will be added to the dependent interactable's "parents" attribute. 

~~~json 
{
    "door1": 
    {
        "id":1, 
        "threshold_condition": { "attribute":"isOpen", "initial_value": null, "goal_value": true },
        "dependents": ["lever_door1"] 
    } 
}
~~~


    As we can see, the threshold condition for lever_door1 has an attribute "onThreshold_callback_fn" which gets called when lever_door1 meets its threshold_condition. We can see, that this onThreshold_callback_fn is further defining the lever's relationship with its parent interactable, door1, by specifying the callback function that calls open() on door1. 

~~~json 
    "lever_door1": 
    {
        "threshold_condition": { 
            "attribute": "pressed", 
            "initial_value":0, "goal_value": 4, "reset_value": true,
            "onThreshold_callback_fn": "list(map(lambda p: p.open(), self.parents))"
        }    
    }
~~~


**parents** (list)
: if an interactable is a dependent for another, then the object that it is a dependent for is placed in this list

**barrier** (boolean)
: defaults to False. Set to True if the interactable acts like a barrier to a vole, whether the vole is aware of it or not. (This is set to True for RFIDs and Doors, since each time a vole passes an RFID there will be a ping, and each time a vole passes a Door we need to check that the door was open, and throw errors if the state of the Door was closed when the vole moved across it.)

**autonomous** (boolean)
: defaults to False. Set to True if it the interactable is not dependent on other interactables or on a vole interaction. (This is set to True for RFIDs) 


## Adding Interactables to the Map 

### Chamber Components 

Components that exist in a chamber should be specified in the components list of a chamber. The ordering of interactables in a chamber are assumed to not be important. If ordering is important, chamber interactables can be referenced along an edge in order to specify a specific order that a vole would pass/interact with each of these interactables in. 

~~~json
{
    "components": [
        { "interactable_name":"lever_food", "type":"lever"},
        { "interactable_name":"lever_door1", "type":"lever"}
    ] 
}
~~~


### Edge Components

The list of edge components can be made up of { interactable_name , type } dictionaries for interactables that actually live in this edge. We can also specify { chamber_interactable } for any interactable that actually exists in a bordering chamber. 

> Chamber Interactables on an Edge 

It is important to specify chamber_interactable for any chamber interactable that plays a role in a voles movements. Conversely, the only interactables that we should not place on an edge as a chamber_interactable are interactables that do not have any relationships with other interactables (i.e. no parent or dependent interactables), and are also not considered an autonomous interactable (meaning a vole would have to make a conscious decision to choose to interact with it.)

~~~json 
{
    "components":[
        { "chamber_interactable": "lever_food"},
        { "chamber_interactable": "lever_door1"},

        { "interactable_name":"rfid1", "type":"rfid" }, 
        { "interactable_name":"door1", "type":"door" },

        { "interactable_name":"lever_door2", "type":"lever" }, 
        { "interactable_name":"door2", "type":"door" },
        { "interactable_name":"rfid2", "type":"rfid" }

    ]
} 
~~~


## Writing an Experiment Script

    Scripts are written by creating subclasses of ModeABC. A single experiment can be made up of as many ModeABC subclasses as needed, where each subclass/mode represents a portion of the experiment with slightly different constraints than the other modes. 
    To add a new script, create a new file within the Scripts directory. 

    To link your new script with the rest of the program, follow the marked (TODOs) that are in the Control/__main__.py file.