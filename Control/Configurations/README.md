
# Control Software: Interactable Components and Configuration (.json) Files #

*file description*: this contains information on each of the interactable classes that exist. This covers how to add a new component of each type by changing its corresponding configuration file. 

*note*: For information on map class view the ReadME that is positioned in the Control directory. 

## Configuration File Overview ## 

### Step-By-Step: Configurations for a Newly Added Interactable ###

1. If it doesn't already exist, add a new .json whose file name matches the type of the interactable. The file name should have the same name as the class name for the interactable, and should always be a '.json' file.

2. Add specifications for a new interactable within the configuration file of that type. For details on how to do this, keep reading this document for both general examples and examples that are specific to existing interactable types. 

3. Add to map.json in order to have the object instantiated when the experiment runs. 

4. Add name of new interactable to other configuration files to establish any relationships it has with other interactables! i.e. When needed, add the name of the interactable as a dependent to another interactable's "dependents" field.

5. If this was a brand new type of interactable (meaning that you created a new json file for this interactable), then there we must make some additions in other places within the code. Navigate to the last section of this README file for details on steps to complete this! 


> template .json file: 

~~~json 
    
    "Interactable_Name": 
    {
        "id": 1,  
        "threshold_condition": {
            "attribute": "attribute_name", "inital_value":0, "goal_value":1,
            "onThreshold_callback_fn":[ "**optional** list of lambda function" ], 
            "check_threshold_with_fn": "**optional** lambda function", 
        },
        "hardware_specs": { 
            "button_specs": { }, 
            "servo_specs": { }
        }, 
        "dependents":["list of names of interactable that this interactable will be dependent/controlled by "]
    }
~~~

## buttonInteractable ## 

### description ### 

    buttonInteractables refer to the override buttons to allow for human control of the opening/closing of doors. This should NOT be confused with InteractableABC's inner class called Button. As we will see, buttonInteractable *uses* the inner class 'Button' to track for physical button presses, but layers more methods and functionality that the Button class on its own does not provide. As a result, we are able to use buttonInteractable to listen for a press, and onPress, executes a series of actions that should most quickly stop a doors movement, and then open/close that door. 

    When adding these buttons to map.json, they are in a bit of their own category as these aren't buttons that are accessible to a vole, as they are only for human use. As a result, they should be stored within a new chamber that doesn't actually exist. We can do this because there will be no edges connecting this chamber to the rest of the box, therefore it will never be accessed in the case that a simulated vole is running. For clarity and to save time in certain simulation functions, be sure to assign this chamber an ID that is a negative number.

> example map.json chamber for holding buttonInteractable objects
> this creates 4 buttonInteractables and places them in our Fake Chamber 

~~~json 
{ 
    "id": -1, 
    "descriptive_name": "Fake Chamber for Storing Override Buttons", 
    "components": [
        { "interactable_name":"open_door1_button", "type":"buttonInteractable" }, 
        { "interactable_name":"close_door1_button", "type":"buttonInteractable" }, 
        { "interactable_name":"open_door2_button", "type":"buttonInteractable" }, 
        { "interactable_name":"close_door2_button", "type":"buttonInteractable" }
    ]
}
~~~


### configurations ### 

 > example configuration for a single buttonInteractable's specifications. 
 > Details for each of these fields is described below the example.

~~~json 
    "open_door1_button": 
    { 
        "id":1, 
        "dependency_chain": { 
            "parents": [ ], 
            "children": [ ]  
        },  
        "threshold_condition": {
            "attribute":"check_threshold_with_fn", 
            "initial_value":true, "goal_value":false, 
            "check_threshold_with_fn":"lambda self: self.buttonObj.buttonQ.empty()", 
            "onThreshold_callback_fn":[ "list(map(lambda p: p.override('open'), self.parents))" ]
        },
        "hardware_specs": {
            "button_specs": { 
                "button_pin":24, 
                "pullup_pulldown":"pullup"
            }
        }
    }
~~~

1. **"open_door1_button"** is assigning the name of this buttonInteractable. When referencing this button in map.json or in other config files, refer to the buttonInteractable with this name.  

2. **"threshold_condition"** 

    i. "attribute": "check_threshold_with_fn" tells the code that we want to call the function defined by check_threshold_with_fn in order to recieve a value for the threshold attribute 
    
    ii. "initial_value" is the starting value of the attribute. Because our threshold condition is whether or not the queue is empty, the initial_value here is relatively useless because we can assume the queue will always initially be empty since it was just created. But we want to put this here anywasy because if we ever want to reset all thresholds to their initial values, this attribute would come in handy. 

    iii. "goal_value" is defining what the value our attribute should return to have met the threshold condition. In this case, if our attribute returns False, then we know that something exists in the buttonQ, denoting that the button was pressed. 

    iv. "check_threshold_with_fn" is the actual lambda function that the threshold attribute references. This function asks if the button objects queue is Empty or not. If it is empty, the lambda function returns True, otherwise it will return False. 

    v. "onThreshold_callback_fn" is the function that we want to have called everytime the threshold condition gets met. As we can see, the purpose of the button shown in the above example is to call override('open') on its parent interactable. In particular, this button was assigned as a dependent to door1, so it has a singular parent, which is door1. 

        The final functionality of this button, as defined by the threshold_condition, is whenever this button gets pressed, door1 will stop anything else that it is doing ( as defined by the override() function ), and immediately open. 

3. **"hardware_specs"** is defining specifications for setting up a Button object. As we can see here, buttonInteractables do not need a Servo object to operate, so we only need to define the attributes for a Button object. 

## door ## 

### description ### 

    doors are the doors in the box! Through the door configurations, we can allow for a large variety of door behaviors by altering a doors dependents.
    By changing a doors dependents, we are changing what interactables have access to control the doors functionality. 

    If we want a door to sit idle for an experiment, we have 2 options that will both have the same effect: (1) we can get rid of certain (or all) dependents so nothing will trigger a change in the doors state. (2) from our experiment script, during mode setup, we can deactive the door so it will not be able to move until it gets reactivated. 
    Each of these options has pros and cons. If we choose option #1, then we can get rid of certain dependents like a lever that opens the door, but leave the override buttons to allow for human control still. The con of this option is that once we change the configuration file, all of the modes that we are running will read in this same configuration file, so all of the modes will not have a lever that allows a vole to control the door, unless we manually add in this dependent at the start of each new mode script. 
    If we choose option #2, there is much more flexibiltiy in how long the door sits in its idle state for, because we can just reactivate/deactivate a door as needed from our mode scripts. 

### configurations ### 

> example door.json contents for defining a singular door object 

~~~json 
    "door1": 
    {
        "id":1, 
        "threshold_condition": { "attribute":"isOpen", "initial_value": null, "goal_value": true },

        "dependents": ["lever_door1", "open_door1_button", "close_door1_button"], 
        "hardware_specs": {
            "button_specs": { 
                "button_pin": 4, 
                "pullup_pulldown":"pullup"
            }, 
            "servo_specs": { 
                "servo_pin":0, 
                "servo_type":"continuous",
                "servo_stop_speed":0.13, 
                "servo_open_speed":0.8, 
                "servo_close_speed":-0.1 
            }, 
            "open_time": 5, 
            "close_timeout":8
            
        }
    }
~~~

1. **"door1"** is assigning a name for our door that will be used throughout the experiment. When referencing this button in map.json or in other config files, refer to the door with this name.

2. **"threshold_condition"** doors have the most simple threshold_condition to define, because we don't have to define an onThreshold_callback_fn or a check_threshold_with_fn as we do for some of the other interactables. We don't need to define onThreshold_callback_fn because it has no parent interactables (i.e. door does not get assigned as a dependent to another interactable), so we don't need to trigger an event in a parent when the doors meets its threshold. And to simplify it even more, we are able to directly reference its threshold attribute, so we don't have to a call a function for checking the attribute value. 

i. "attribute" 

ii. "initial_value"

iii. "goal_value"

3. **"hardware_specs"**

## lever ## 

### description ### 

### configurations ### 

> example

~~~json 
~~~

1. **"the name of the object"** is assigning a name for our [] that will be used throughout the experiment. When referencing this button in map.json or in other config files, refer to the [] with this name.

2. **"threshold_condition"** 

3. **"hardware_specs"**

## rfid ## 

### description ### 

### configurations ### 

> example 

~~~json 
~~~

1. **"name of the object"** is assigning a name for our [] that will be used throughout the experiment. When referencing this button in map.json or in other config files, refer to the [] with this name.

2. **"threshold_condition"** 

3. **"hardware_specs"**



## Adding a New Type of Interactable ## 

> Additions to Map Class

We must add the actual object instantiation into the Map Class. To do this, navigate to the file Map.py. First, import your new interactable (this is done at the top of the file where the rest of the interactable classes get imported). Next, within the function instantiate_interactable_hardware, locate the section of the function that is commented  # Instantiate New Interactable. You should see a series of if/elif/elif...etc. that is checking for each type of interactable. Add in a new elif statement that checks for your new interactable type, and if an object is of this type, we will create that object!


> Override functions from the interactable abstract class (InteractableABC)

Write the functions that InteractableABC requires to be overriden! The Methods that need to be overriden are as follows: 
    
1. validate_hardware_setup: this function can pretty much be copied from existing versions. This is just a function that once we have confirmed that an interactable is NOT being simulated, we will execute a couple steps to check that the hardware components that makeup the given interactable ( servos and buttons ) managed to be setup correctly. If they were not setup correctly, but the user did not request that we simulate this interactable, then we should throw an error. 

2. add_new_threshold_event: format the **event** variable and then put the new **event** onto the threshold_event_queue
