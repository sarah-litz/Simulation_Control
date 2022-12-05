
# Box_Vole_Simulation

## README Table of Contents ##

> Control Files

[Intro: Control Package](Control/README.md)
    
- The basics of running Control Software Package
- covers details on how to write modes to run in the Control Software 

[Control Configuration Files](Control/Configurations/README.md)

- configuring components so they behave a certain way when the experiment runs

[Writing (Control-Side) Scripts to Run an Experiment](Control/Scripts/README.md)

- more in depth description for creating a new script to run the experiment!

[Control Software Classes](Control/Classes/README.md)

- more in depth descriptions of the classes that build the control software: InteractableABC, Map, and ModeABC

> Simulation Files 

[Intro: Simulation Package](Simulation/README.md) 

- the basics of running and writing a simulated experiment 

[Simulation Configuration Files](Simulation/Configurations/README.md)

- defining which component(s) we want to be simulated, as well as *how* they are simulated. 

[Writing (Simulation) Scripts to Run a Simulated Experiment --> DNE]

[Simulation Software Classes](Simulation/Classes/README.md)



## Control Software and Simulation Software Communication "Channels"

### Interactables: How the code uses attr(threshold) vs attr(threshold_event_queue)


- threshold is set to TRUE by the control software. Immediately following this is a call to the method add_new_threshold_event(), where the interactable adds to its threshold_event_queue. 
- threshold is set to FALSE by a Vole, after the Vole passes this dependent (specifically, this gets done in update_location()). 
    - once threshold gets set to False again, the watch_for_threshold_event method will quit its sleep state and start looping again to check for threshold states again.

~~~
the threshold attribute is used purely for VOLE simulation needs. This value should NOT be used anywhere in User Written Scripts. Users should instead use the threshold_event_queue to check if any threshold events occur, as shown in the example below 
~~~
*( this would be within a Simulation class, which belong in the directory Simulation/Scripts ).*


~~~python
 ## Wait for Lever Press or for Simulation to become Inactive ##
while self.active: 

    event = None 
    while event is None and self.active: 
        try: event = lever1.threshold_event_queue.get_nowait() 
        # loops until something is added to the threshold_event_queue
        except queue.Empty: pass 
        time.sleep(.5)

    if event is None:  
        # timed out before lever threshold event
        return 

    else: 
        ## Lever Threshold Was Met ## 
        print(f"{self}: {event}")  


~~~

~~~python
    """        
    [summary] 

    Args:         
        arg (type) : description

    Returns:
        type : description
    """
~~~
