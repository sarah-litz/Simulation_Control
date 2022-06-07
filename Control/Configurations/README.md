
# Control Software: Interactable Components and Configuration (.json) Files #

*file description*: this contains information on each of the interactable classes that exist. This covers how to add a new component of each type by changing its corresponding configuration file. 

*note*: For information on map class view the ReadME that is positioned in the Control directory. 

## Configuration File Overview ## 

### Step-By-Step ###

1. If it doesn't already exist, add a new .json whose file name matches the type of the interactable. For consistency purposes, this should have the same name as the class name for the interactable.

2. Add specifications for a new interactable within the configuration file of that type. For details on how to do this, keep reading this document for both general examples and examples that are specific to existing interactable types. 

3. Add to map.json in order to have the object instantiated when the experiment runs. 

4. Add name of new interactable to other configuration files to establish any relationships it has with other interactables! i.e. When needed, add the name of the interactable as a dependent to another (existing) interactable.

### template .json file ### 

~~~json 
    
    "Interactable_Name": 
    {
        "id": 1,  
        "threshold_condition": {
            "attribute": "attribute_name", "inital_value":0, "goal_value":1, "reset_value":true, 
            "onThreshold_callback_fn":"**optional** lambda function", 
            "check_threshold_with_fn": "**optional** lambda function", 
        },
        "hardware_specs": { 
            "button_specs": { }, 
            "servo_specs": { }
        }, 
        "dependents":[]
    }
~~~

## buttonInteractable ## 

### description ### 

    Button interactables refer to the override buttons to allow for human control of the opening/closing of doors. This should not be confused with the inner class Button that is defined w/in the InteractableABC class. buttonInteractable uses this inner class 'Button', but is able to add more functions and attributes that the class 'Button' on its own does not need. As a result, we are able to use buttonInteractable to listen for a press, and onPress, executes a series of actions that should most quickly stop a doors movement, and then open/close that door. 

    When adding these buttons to map.json, they are in a bit of their own category as these aren't buttons that are accessible to a vole, as they are only for human use. As a result, they should be stored within a new chamber that doesn't actually exist. We can do this because there will be no edges connecting this chamber to the rest of the box, therefore it will never be accessed in the case that a simulated vole is running. For clarity and to save time in certain simulation functions, be sure to assign this chamber an ID that is a negative number.

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
            "onThreshold_callback_fn":"list(map(lambda p: p.override('open'), self.parents))"
        },
        "check_threshold_with_fn":"lambda self: self.buttonObj.buttonQ.empty()",
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

3. **"hardware_specs"**

## door ## 

### description ### 

### configurations ### 

## lever ## 

### description ### 

### configurations ### 

## rfid ## 

### description ### 

### configurations ### 

