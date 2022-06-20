# Configuring a Simulation # 

    the config file for a simulation is very simple, with only one or two attributes that we need to worry about: 
        (1) simulate (true or false): Do you want this interactable to be simulated as the experiment runs? 
        (2) simulate_with_fn (optional lambda function): When this interactable IS being simulated, how should it be simulated? ( If not specified, the component is simulated by setting its threshold attribute to its goal value )

*For anything else regarding an interactables behavior, the [README](Control/Configurations/README.md) for configuring an interactable in the Control Package should be referenced.*

> Example Configuration for 4 different components for 4 different interactable types ( rfid, lever, door, buttonInteractable ) : 

~~~json 
    {"name":"rfid2", 
        "simulate":true, 
        "simulate_with_fn": "lambda self, vole: self.rfidQ.put( (vole, self.ID) )"  
    }, 
    {"name":"lever_food", 
        "simulate":true, 
        "simulate_with_fn":"lambda self, vole: self.set_press_count( self.threshold_condition['goal_value'] )"
    }, 
    {"name":"door2", 
        "simulate":false
    }, 
    {"name":"open_door1_button", 
        "simulate":false
    }
~~~


## How do I know if I need to specify the optional "simulate_with_fn" attribute? ## 

**Component Types that Need "simulate_with_fn" specified**

    - RFID 
    - Levers

**Component Types that do Not need "simulate_with_fn" specified**

    - Door 
    - buttonInteractables