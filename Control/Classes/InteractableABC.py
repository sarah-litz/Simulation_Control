"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 4/6/2022
Description: Class definition for interacting with hardware components. This module contains the abstract class definition, as well as the subclasses that are specific to a piece of hardware.

Property of Donaldson Lab at the University of Colorado at Boulder
"""

# Standard Lib Imports 
import importlib
from cgitb import reset
import time
import threading
import queue

# Local Imports 
from Logging.logging_specs import control_log, sim_log

try: 
    import Rpi.GPIO as GPIO 
except ModuleNotFoundError as e: 
    print(e)
    GPIO = None
try: 
    import pigpio as pigpio
except ModuleNotFoundError as e: 
    print(e)
    pigpio = None
try: 
    from adafruit_servokit import ServoKit
    SERVO_KIT = ServoKit(channels=16) 
except ModuleNotFoundError as e: 
    print(e)
    SERVO_KIT = None


class interactableABC:

    def __init__(self, threshold_condition):

        ## Object Information ## 
        self.ID = None
        self.active = False # must activate an interactable to startup threads for tracking any vole interactions with the interactable
        self.name = 'OVERRIDE!'

        ## Location Information ## 
        self.edge_or_chamber = None # string to represent if this interactable sits along an edge or in a chamber
        self.edge_or_chamber_id = None # id of that edge or chamber 

        ## Threshold Tracking ## 
        self.threshold = False
        self.threshold_condition = threshold_condition  # {attribute, initial_value, goal_value} dict to specify what the attribute/value goal of the interactable is. 
        self.threshold_event_queue = queue.Queue() # queue for tracking anytime a threshold condition is met 

        ## Dependency Chain Information ## 
        self.dependents = [] # if an interactable is dependent on another one, then we can place those objects in this list. example, door's may have a dependent of 1 or more levers that control the door movements. These are interactables that are dependent on a vole's actions! 
        self.parents = [] # if an interactable is a dependent for another, then the object that it is a dependent for is placed in this list. 
        self.barrier = False # set to True if the interactable acts like a barrier to a vole, meaning we require a vole interaction of somesort everytime a vole passes by this interactable. 
        self.autonomous = False # set to True if it is not dependent on other interactables or on vole interactions (i.e. this will be True for RFIDs only )
    
    
    def __str__(self): 

        return self.name



    #
    # Hardware Subclasses: Buttons & Servos ( utilizes Rpi.GPIO and adafruit_servokit.ServoKit )
    #
    class Button:
        # Class for tracking Switch States # 
        '''subclass of interactableABC, as buttons will never be a standalone object, they are always created to control a piece of hardware
        attempts importing GPIO library. If simulation, this will fail, in which case we return and don't have a real button. 
        '''
        def __init__(self, pin, pullup_pulldown):

            self.pin = pin 
            self.pullup_pulldown = pullup_pulldown 

            def set_gpio(): 
                try: 
                    if pullup_pulldown == 'pullup':
                        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
                        return 0
                    elif pullup_pulldown == 'pulldown': 
                        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                        return 1 
                    else: 
                        raise KeyError(f'(InteractableABC.py, Button) Configuration file error when instantiating Button {self.name}, must be "pullup" or "pulldown", but was passed {pullup_pulldown}')
                        return -1
                
                except: 
                    print('(InteractableABC.py, Button) simulating gpio connection')
                    return None
            
            self.pressed_val = set_gpio()
    
    class Servo: 
        # class for managing servos 
        '''subclass of interactableABC, as servos will never be a standalone object, they are always created in order to control a piece of hardware. 
        attempts importing of adafruit library. If simulation, this will fail, in which case we return and don't have a real servo. 
        '''

        def __init__(self, ID, servo_type): 
            '''takes a positional ID on the adafruit board and the servo type, and returns a servo_kit object'''
            
            self.ID = ID

            
            def set_servo(): 
                try: 
                    if servo_type == 'positional':
                        return SERVO_KIT.servo[ID]
                    elif servo_type == 'continuous':
                        return SERVO_KIT.continuous_servo[ID]
                    else: 
                        raise KeyError(f'(InteractableABC.py, Servo) servo type was passed as {servo_type}, must be either "positional" or "continuous"')

                except ModuleNotFoundError as e: 
                    print(e)
                    return None
            
            self.servo = set_servo()
            




    def activate(self):

        print(f"(InteractableABC.py, activate) {self.name} has been activated. starting contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
        control_log(f"(InteractableABC.py, activate) {self.name} has been activated. starting contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
        
        self.threshold = False # "resets" the interactable's threshold value so it'll check for a new threshold occurence
        self.active = True 
        self.watch_for_threshold_event() # begins continuous thread for monitoring for a threshold event
        self.dependents_loop() 

    def deactivate(self): 
        print(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")        
        control_log(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
        
        self.threshold = False # "resets" the threshold value so it'll only check for a new threshold occurence in anything following its deactivation
        self.active = False 

    def reset(self): 
        self.threshold_event_queue.queue.clear() # empty the threshold_event_queue

    def isSimulation(self): 
        ''' checks if object is being simulated. 
        if it does, then it can avoid/shortcut certain functions that access hardware components. '''

        if hasattr(self, 'simulate'): 
            if self.simulate is True: 
                return True 
        return False


    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 

    def add_new_threshold_event(self): 
        # appends to the threshold event queue 

        raise Exception(f'override add_new_threshold_event')
        self.threshold_event_queue.put()

    def isThreshold(self): 
        ''' checks if interactable has reached its threshold. Returns True if yes, False otherwise. '''

    def dependents_loop(self): 
        ## DEPENDENTS LOOP ## 
        ''' if interactable has dependents, then we can trigger a threshold event to occur for the interactable iff all of its dependents are true.'''

        if len(self.dependents)>0: 
            raise Exception(f'must override dependents_loop with logic for the cause/effect of an interactables dependents')
        
        else: 
            return # don't need to run this function for interactable w/out dependents 

    @run_in_thread
    def watch_for_threshold_event(self): 
        

        while self.active: 

            # using the attribute/value pairing specified by the threshold_condition dictionary
            # if at any time the given attribute == value, append to the threshold_event_queue.

            threshold_attr_name = self.threshold_condition["attribute"]
            attribute = getattr(self, threshold_attr_name) # get object specified by the attribute name

            # control_log(f"(InteractableABC.py, watch_for_threshold_event) {self.name}: Threshold Name: {threshold_attr_name}, Threshold Attribute Obj: {attribute}")
            
            # check for attributes that may have been added dynamically 
            if hasattr(self, 'check_threshold_with_fn'): # the attribute check_threshold_with_fn is pointing to a function that we need to execute 
                attribute = attribute(self) # sets attribute value to reflect the value returned from the function call
            
            
            # Check for a Threshold Event by comparing the current threshold value with the goal value 
            if attribute == self.threshold_condition['goal_value']: # Threshold Event: interactable has met its threshold condition
                
                event_bool = True 


                #
                # Interactable Threshold Event Handling
                #             
                if event_bool and self.active: 
                    ## AN EVENT! ## 

                    # Handle Event 
                    self.threshold = True
                    self.add_new_threshold_event()
                    print(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")
                    control_log(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")


                    if len(self.dependents) > 0: 
                        # sleep while dependents (if they exist) remain in goal state, meaning current interactable is also in its goal state.
                        # because interactable is not dependent on vole's actions, we can assume that it could potentially be sitting in its goal state for extended periods of time. 
                        # as a result, we want to sleep until it is out of its goal state ( or until threshold gets set to false by simulation ).

                        while attribute == self.threshold_condition['goal_value'] and self.threshold == True: 

                            time.sleep(1) # wait for change in threshold or a change in the attribute's value to differ away from goal_value 

                    
                    # Since an event occurred, check if we should reset the attribute value 
                    # (NOTE) Delete This?? 
                    if ('reset_value' in self.threshold_condition.keys() and self.threshold_condition['reset_value'] is True): 

                        setattr( self, self.threshold_condition['attribute'], self.threshold_condition['initial_value'] )

                        control_log( f' (InteractableABC,py, watch_for_threshold_event) resetting the threshold for {self.name}  ')

                    else: 
                        # if we are not resetting the value, then to ensure that we don't endlessly count threshold_events
                        # we want to wait for some kind of state change ( a change in its attribute value ) before again tracking a threshold event 
                        pass 

                else: 
                    # no threshold event 
                    pass 
            else: 
                # no threshold event
                pass 
                
            
            time.sleep(0.75)

         
class lever(interactableABC):
    def __init__(self, ID, threshold_condition, hardware_specs ):
        # Initialize the parent class
        super().__init__(threshold_condition)

        # Initialize the given properties
        self.name = 'lever'+str(ID) 
        self.ID        = ID 
        self.signalPin = hardware_specs['signalPin']

        # Current Position Tracking # 
        self.isExtended = False 
        self.extended_angle = hardware_specs['extended_angle']
        self.retracted_angle = hardware_specs['retracted_angle']

        # Movement Controls # 
        self.servo = self.Servo(ID = self.ID, servo_type = hardware_specs['servo_type']) # positional servo to control extending/retracting lever 
        self.switch = self.Button(pin = self.signalPin, pullup_pulldown = hardware_specs['pullup_pulldown']) # button to recieve press signals thru changes in the gpio val

        ## Threshold Condition Tracking ## 
        self.pressed = self.threshold_condition["initial_value"] # counts current num of presses 
        #self.required_presses = self.threshold_condition["goal_value"] # Threshold Goal Value specifies the threshold goal, i.e. required_presses to meet the threshold
        #self.threshold_attribute = self.threshold_condition["attribute"] # points to the attribute we should check to see if we have reached goal. For lever, this is simply a pointer to the self.pressed attribute. 

        # Initialize the retrieved variables
        self.angleExtend  = None
        self.angleRetract = None


        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  


    def add_new_threshold_event(self): 

        # appends to the lever's threshold event queue 
        self.threshold_event_queue.put(f'lever{self.ID} pressed {self.pressed} times!')

        # (NOTE) if you don't want this component to be checking for a threhsold value the entire time, then deactivate here ( will be re-activated when a new mode starts thru call to activate_interactables ) 
        # self.deactivate()


    #@threader
    def extend(self):
        """Extends the lever to the correct value
        """
        control_log(f'(InteractableABC, Lever.extend) extending {self.name} ')

        if self.isExtended: 
            # already extended 
            print(f'(InteractableABC, Lever.extend) {self.name} already extended.')
            return 

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            self.isExtended = True 
            self.activate() 
            return 
        

        #
        # HARDWARE THINGS
        #



    #@threader
    def retract(self):
        """Retracts lever to the property value
        """
        control_log(f'(InteractableABC, Lever.extend) retracting {self.name} ')

        if not self.isExtended: 
            print(f'(InteractableABC, Lever.extend) {self.name} already retracted.')
            # already retracted 
            return 

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            self.isExtended = False 
            self.deactivate() 
            return 
        

        #
        # HARDWARE THINGS
        #

    def __move(self, angle):
        """This moves the lever to the specified angle. This can be any angle in the correct range, and the function will produce an error if the angle is out of range of the motor. 

        Args:
            angle (int): Servo angle to move to. This should be between 0 and 180 degrees
        """

        #  This Function Accesses Hardware => Perform Sim Check First


        pass

    def __check_state(self):
        """Instantaneously returns the state of the lever
        """
        pass

class door(interactableABC):
    """This class is the unique door type class for interactable objects to be added to the Map configuration.

    Args:
        interactableABC ([type]): [description]
    """

    def __init__(self, ID, servoPin, threshold_condition):
        # Initialize the abstract class stuff
        super().__init__(threshold_condition)
        
        # Set the input variables
        self.name = 'door'+str(ID)
        self.ID       = ID 
        self.servoPin = servoPin

        # in order for a threshold event to occur, there must have also been a threshold_event for its dependent interactable
        
        # Set the state variable, default to False (closed). (open, closed) = (True, False)
        # (NOTE) need to initialize the door's state in more accurate way 
        self.state = threshold_condition['initial_value']
        '''if threshold_condition['initial_value'] is True: # ensure that the physical door refelcts the initial state specified by the config file
            self.open() 
        else: self.close() '''

        # Set properties that will later be set
        self.currentAngle = None
        self.openAngle = None
        self.closeAngle = None

        self.barrier = True 
        self.autonomous = False 

        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  
    
    
    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 



    @run_in_thread
    def dependents_loop(self): 

        ## Logic for How To Handle Door's Dependent(s) ## 

        # if any one of door's dependents (i.e. one of the levers that is listed as its dependent) meets its threshold, then go ahead and 
        # meet the door's threshold goal by opening or closing the door 

        #
        # LEAVING OFF HERE!!!!! 
        # DOORS DONT WORK CORRECTLY IF THEY DONT HAVE A DEPENDENT!!!! 
        # need to add something to the dependents loop that accounts for this.
        #
        if len(self.dependents) < 1: # No Dependents. 

            return 

        while self.active: 

            for dependent in self.dependents: 

                if dependent.threshold == True: 

                    dependent.threshold = False # reset now that we have triggered an event occurrence

                    # check self's threshold goal 
                    if self.threshold_condition['goal_value'] == True: 

                        self.open() 

                    elif self.threshold_condition['goal_value'] == False: 

                        self.close() 
                    
                    else: 

                        raise Exception(f'(Door, dependents_loop) did not recognize {self.name} threshold_condition[goal_value] of {self.threshold_condition["goal_value"]}')




    def add_new_threshold_event(self): 
        # appends to the threshold event queue 
        self.threshold_event_queue.put(f'{self.name} isOpen:{self.state}')
        print("Door Threshold: ", self.threshold, "  Door Threshold Condition: ", self.threshold_condition)
        print(f'(Door(InteractableABC.py, add_new_threshold_event) {self.name} event queue: {list(self.threshold_event_queue.queue)}')
           

        # (NOTE) if you don't want this component to be checking for a threhsold value the entire time, then deactivate here and re-activate when a new mode starts 
        #    self.deactivate() # Since door will just sit in the goal_state, we only care to start checking again for a threshold event when it is opposite of whatever its goal_state is to ensure we only count one threshold eent per open/close.
        
        #    (NOTE TO SELF) thinking I don't actually need to deactivate?? Cause shouldn't a door threshold only occur if the lever.pressed==goal_value? And we are resetting the lever.pressed immediately after it reaches the goal value. 
        #                   except in the scenario of an open cage where the lever is inactive, then the door rlly isnt dependent on the lever in this round. 
        #                   so rlly we shouldn't leave an interactable dependent on some value of their dependent, because their dependents can change and become inactive. 
        #                   so door needs to independently have a way of only adding one event to its threshold event queue that doesn't rely on anythign else, even its own dependent. 

        # if door ever goes back to the state that is opposite than that of its goal_state, then we should reactivate it with a call to activate() 
        # maybe we can have this check w/in the open/close functions?? Or we could put w/in the isOpen() check?? 


    #@threader
    def close(self):
        """This function closes the doors fully"""

        # check if the door is already closed 
        if self.state is False: 

            # door is already closed 
            control_log('(Door(InteractableABC)) {self.name} was already Closed')
            print(f'(Door(InteractableABC)) {self.name} was already Closed')
            return 


        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation(): 
            # If door is being simulated, then rather than actually closing a door we can just set the state to False (representing a Closed state)
            print(f'(Door(InteractableABC), close()) {self.name} is being simulated. Setting state to Closed and returning.')
            self.state = False 
            return 

        # 
        # Direct Rpi to Close Door
        # 
        raise Exception(f'(Door(InteractableABC), close() ) Hardware Accessed Stuff Here to Close {self.name}')



    #@threader
    def open(self):
        """This function opens the doors fully
        """


        # check if door is already open
        if self.state is True: 

            control_log('(Door(InteractableABC)) {self.name} is Open')
            print(f'(Door(InteractableABC)) {self.name} is Open')
            return 
        

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation(): 
            # If door is being simulated, then rather than actually opening a door we can just set the state to True (representing an Open state)
            print(f'(Door(InteractableABC), open()) {self.name} is being simulated. Setting state to Open and returning.')
            self.state = True 
            return 
  

        # 
        # Direct RPI to Open Door 
        #
        raise Exception(f'(Door(InteractableABC), open() ) Hardware Accessed Stuff Here to Open {self.name}')


    def check_state(self):
        """This returns the state of whether the doors are open or closed, and also sets the state variable to the returned value
        """
        pass

    #@threader
    def __set_door(self, angle):
        """This sets the door value to any given input value.

        Args:
            angle (int): Servo angle to set the door value to.
        """

        #  This Function Accesses Hardware => Perform Sim Check First
        pass






class rfid(interactableABC):
    """This class is the unique class for rfid readers that is an interactable object. Note that this does not control the rfid readers like the other unique classes, it only deals with the handling of rfid data and its postion in the decision flow.

    Args:
        interactableABC ([type]): [description]
    """

    def __init__(self, ID, threshold_condition):
        # Initialize the parent 
        super().__init__(threshold_condition)

        self.name = 'rfid'+str(ID)
        self.ID = ID 
        self.rfidQ = queue.Queue()


        self.barrier = True # because rfid beam is unavoidable when vole runs passed interactable. 
        self.autonomous = True # operates independent of direct interaction with a vole or other interactales. 
        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  


    def add_new_threshold_event(self): 
        '''New Ping was added to rfidQ. Retrieve its value and append to the threshold event queue '''
        try: 
            ping = self.rfidQ.get() 
        except queue.Empty as e: 
            raise Exception(f'(InteractableABC.py, add_new_threshold_event) Nothing in the rfidQ for {self.name}')

        self.threshold_event_queue.put(ping)

        # do not deactivate the rfids. always monitoring for pings. 


    def from_queue(self, numEntries = 1):
        """Pulls the given number of entries from the shared rfidQ with the hardware or simulation.

        Args:
            numEntries (int, optional): Number of queue entries to pull. Defaults to 1.
        """
        pass

    def to_queue(self, data):
        """Puts the given data into the object specific queue that is initialized.

        Args:
            data (any): Data to be added to the specificQ property
        """
        pass

    def is_empty(self, queue):
        """Determines if a queue is empty or if there is information to grab. Returns a boolean

        Args:
            queue (queue): queue to query and check for emptiness.
        """
        pass

#if __name__ == "__main__":