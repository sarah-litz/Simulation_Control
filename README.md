
# Box_Vole_Simulation


## Control Software and Simulation Software Communication "Channels"

### Interactables: attr(threshold) vs attr(threshold_event_queue)


- set to TRUE by the control software 
- SET to FALSE by a Vole, after the Vole passes this dependent (specifically, this gets done in update_location()). 
    - once threshold gets set to False again, the watch_for_threshold_event method will quit its sleep state and start looping again to check for threshold states again.

~~~
the threshold attribute is used purely for VOLE simulation needs. This value should NOT be used anywhere in User Written Scripts. Users should instead use the threshold_event_queue to check if any threshold events occur, as shown in the example below 
~~~
*( this would be within a SimulationABC class, which belong in the directory Simulation/Scripts ).*


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
