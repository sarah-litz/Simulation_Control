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
import signal
import sys

# Local Imports 
from Logging.logging_specs import control_log, sim_log

try: 
    import RPi.GPIO as GPIO 
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

    def __init__(self, threshold_condition, name):

        ## Object Information ## 
        self.ID = None
        self.active = False # must activate an interactable to startup threads for tracking any vole interactions with the interactable
        self.name = name # name used is the one specified in the configuration files 
        self.isSimulation = False # simulation feature: set to True if interactable is being simulated 
        self.messagesReturnedFromSetup = '' # append to with any messages that we want to display after setup, but before activating an interactable

        ## Location Information ## 
        self.edge_or_chamber = None # string to represent if this interactable sits along an edge or in a chamber
        self.edge_or_chamber_id = None # id of that edge or chamber 

        ## Threshold Tracking ## 
        self.threshold = False
        self.threshold_condition = threshold_condition  # {attribute, initial_value, goal_value} dict to specify what the attribute/value goal of the interactable is. 
        self.threshold_event_queue = queue.Queue() # queue for tracking anytime a threshold condition is met 

        ## Dependency Chain Information ## 
        # self.dependents = [] # if an interactable is dependent on another one, then we can place those objects in this list. example, door's may have a dependent of 1 or more levers that control the door movements. These are interactables that are dependent on a vole's actions! 
        self.parents = [] # if an interactable is a dependent for another, then the object that it is a dependent for is placed in this list. 
        self.barrier = False # set to True if the interactable acts like a barrier to a vole, meaning we require a vole interaction of somesort everytime a vole passes by this interactable. 
        self.autonomous = False # set to True if it is not dependent on other interactables OR on vole interactions (i.e. this will be True for RFIDs only )


    
    def __str__(self): 

        return self.name

    # ------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------
    
    #
    # InteractableABC Subclasses: Servo, PosServo(Servo), ContServo(Servo), and Button ( utilizes Rpi.GPIO and adafruit_servokit.ServoKit )
    #
    class Button:
        # Class for tracking Switch States # 
        '''subclass of interactableABC, as buttons will never be a standalone object, they are always created to control a piece of hardware
        attempts importing GPIO library. If simulation, this will fail, in which case we return and don't have a real button. 
        '''
        def __init__(self, button_specs, parentObj):

            self.parent = parentObj 

            self.pin_num = button_specs['button_pin'] 
            self.pullup_pulldown = button_specs['pullup_pulldown'] 
            self.num_pressed = 0 # number of times that button has been pressed 

            self.buttonQ = queue.Queue() # queue where we append each time a button press is detected
            
            # self.pressed_val denotes what value we should look for (0 or 1) that denotes a lever press 
            self.pressed_val = self._setup_gpio()  # defaults to -1 in scenario that gpio setup fails (including if isSimulation)

            # Setup the isSimulation attribute: isSimulation is True if we were unable to connect to gpio pin 
            if self.pressed_val < 0: self.isSimulation = True 
            else: self.isSimulation = False 

            # 
            # Setup isPressed Variable --> setup depends on if Button is a simulation or not
            if self.isSimulation: 
                self.isPressed = False # simulated buttons have a boolean isPressed 
            else: 
                self.isPressed = self.isPressedProperty # actual buttons get access to method version which checks GPIO value in order to know if isPressed is True or False

        def __str__(self): 
            return self.isPressed

        def _setup_gpio(self): 

            try: 
                if self.pullup_pulldown == 'pullup':
                    GPIO.setup(self.pin_num, GPIO.IN, pull_up_down = GPIO.PUD_UP)
                    return 0 
                elif self.pullup_pulldown == 'pulldown': 
                    GPIO.setup(self.pin_num, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                    return 1
                else: 
                    raise KeyError(f'(InteractableABC.py, Button) {self.parent.name}: Configuration file error when instantiating Button {self.name}, must be "pullup" or "pulldown", but was passed {self.pullup_pulldown}')
            except AttributeError as e: 
                # attribute error raised 
                control_log(f'(InteractableABC.py, Button) {self.parent.name}: simulating gpio connection. ErrMssg: {e}')
                self.parent.messagesReturnedFromSetup += f'simulating gpio connection. '
                return -1

        def run_in_thread(func): 
            ''' decorator function to run function on its own daemon thread '''
            def run(*k, **kw): 
                t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
                t.start() 
                return t
            return run 


        @run_in_thread
        def listen_for_event(self, timeout=None, edge=None): # detects the current pin for the occurence of some event
            ''' 
            event detection for button. On event, incrememts the buttons num_pressed value 
            ( note this does not update/check isPressed, as this is handled by the property function isPressed )
            '''

            def increment_presses(pin): 
                self.num_pressed += 1 
                self.buttonQ.put(f'press#{self.num_pressed}') # add press to parents buttonQ
                # print(f'(InteractableABC, Button.listen_for_event) {self.parent} Button Object was Pressed. num_pressed = {self.num_pressed}, buttonQ = {list(self.buttonQ.queue)}')
                control_log(f'(InteractableABC, Button.listen_for_event) {self.parent} Button Object was Pressed. num_pressed = {self.num_pressed}')
                

            #
            # Sim Check; this function accesses gpio library. If button is being simulated, call the simulation version of this function and return. 
            #
            if self.isSimulation: 

                # If button is being simulated, then we care about changes to isPressed. If isPressed == True, then increment presses
                # print(f'(InteractableABC, Button, listen_for_event) Button for {self.parent} is being simulated. Simulated Button doesnt listen for event.')  
                control_log(f'(InteractableABC, Button, listen_for_event) Button for {self.parent} is being simulated. Simulated Button doesnt listen for an event. {self.parent} will be listening for its own threshold event so will still pick up on simulated button presses.')  
                return             

            #
            # Wait For Event
            #
            if edge is None: 
                # default to the falling edge 
                GPIO.add_event_detect( self.pin_num, GPIO.FALLING, bouncetime = 400, callback = increment_presses )
            else: 
                GPIO.add_event_detect(self.pin_num, edge, bouncetime = 400, callback = increment_presses )
            

            if timeout is None: # monitor pin all while its parent interactable is active 
                
                while self.parent.active: 
                    
                    time.sleep(0.025)
                
                GPIO.remove_event_detect(self.pin_num)
                return # return from func when parent object is deactivated
                
            else: 

                # timeout interval specified 
                start = time.time() 
                while self.parent.active and (time.time() - start > timeout): 
                    
                    time.sleep(0.025) 
                
                GPIO.remove_event_detect(self.number)
                return # return from func whne parent object is deactivated or timeout interval is up

        
        @property
        def isPressedProperty(self): 
            ''' 
            returns the current boolean value of the button. If the button is being simulated 
            (denoted by the pressed_val < 0, raise an exception because this function should not be getting accessed by a simulated button. ) 
            '''
            # print(f'(InteratableABC, isPressed start value: {self.isPressed}')
            if self.pressed_val < 0: 
                raise Exception('(InteractableABC.py, Button.isPressed) cannot access gpio input value for a Button that is being simulated.')  

            ''' if not a simulation, each time isPressed gets accessed, we want to recheck the GPIO input value. set isPressed as a method that gets called each time ''' 
            
            # print(f'(InteractableABC, Button.isPressed property call)')
            if GPIO.input(self.pin_num) == self.pressed_val: 
                return True 
            else: 
                return False   
    
    class Servo: 
        # class for managing servos 
        '''subclass of interactableABC, as servos will never be a standalone object, they are always created in order to control a piece of hardware. 
        attempts importing of adafruit library. If simulation, this will fail, in which case we return and don't have a real servo. 
        '''

        def __init__(self, servo_specs, parentObj): 
            '''takes a positional ID on the adafruit board and the servo type, and returns a servo_kit object'''
            
            self.parent = parentObj

            self.pin_num = servo_specs['servo_pin']
            self.servo_type = servo_specs['servo_type']  
            self.servo = self.__set_servo()   
            
        def __set_servo(self): 
            #if SERVO_KIT is None: 
            #    # simulating servo kit
            #    return None 
            
            try: 
                if self.servo_type == 'positional':
                    return SERVO_KIT.servo[self.pin_num]
                elif self.servo_type == 'continuous':
                    return SERVO_KIT.continuous_servo[self.pin_num]
                else: 
                    raise KeyError(f'(InteractableABC.py, Servo) {self.parent.name}: servo type was passed as {self.servo_type}, must be either "positional" or "continuous"')

            except AttributeError as e: 
                # attribute error raised if we werent able to import SERVO_KIT and we try to access SERVO_KIT.servo 
                control_log(f'(InteractableABC.py, Servo) {self.parent.name}: simulating servo connection. ErrMssg: {e}')
                self.parent.messagesReturnedFromSetup += f'simulating servo connection. ' 
                return None
            


    class PosServo(Servo): 
        ''' positional servo '''
        def __init__(self, servo_specs, parentObj): 
            super().__init__(servo_specs, parentObj)
            self.angle = 0 # positional servo tracks current angle of the servo 
    
    class ContServo(Servo): 
        ''' continuous servo '''
        def __init__(self, servo_specs, parentObj): 
            super().__init__(servo_specs, parentObj)
            self.throttle = 0 # continuous servo tracks speed that wheel turns at 

        
    # ------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------------------
    
    #
    # InteractableABC methods
    #
    def validate_hardware_setup(self): 
        ''' if the interactable is not being simulated, then we must check that its hardware components have been properly connected so we can find any errors early '''
        if not self.isSimulation: 
            # Interactable is not being simulated, but it does not have a function to validate its hardware components. Throw error 
            raise Exception(f'(InteractableABC, validate_hardware_setup) Must override this function with checks that ensure the hardware components are properly connected. Please add this to the class definition for {self.name}')

    def activate_inner_objects(self): 
        ''' 
        if interactable contains any inner objects (buttons and servos)
        this function is called to ensure that they are activated for each mode
        also to check that we are simulated both the buttons and the servos in the scenario that the user is running a simulation and their parent object is being simulated
        '''
        pass 

    def activate(self):
        ''' 
        called at the start of each mode. begins tracking for thresholds for both itself as well as its dependents. 
        '''

        try: self.validate_hardware_setup() # validate that this hardware was properly setup (e.g. the button and servos ) if interactable is not being simulated
        except Exception as e: print(e), sys.exit(0)

        control_log(f"(InteractableABC.py, activate) {self.name} has been activated. starting contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
        
        self.threshold = False # "resets" the interactable's threshold value so it'll check for a new threshold occurence
        self.active = True 
        # self.activate_inner_objects()
        self.watch_for_threshold_event() # begins continuous thread for monitoring for a threshold event
        # self.dependents_loop() 
        

    def deactivate(self): 
        print(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")        
        control_log(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
        
        self.threshold = False # "resets" the threshold value so it'll only check for a new threshold occurence in anything following its deactivation
        self.active = False 

        if hasattr(self, 'stop'): 
            self.stop() # stops things that could be left running

    def reset(self): 
        self.threshold_event_queue.queue.clear() # empty the threshold_event_queue
    

    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 

    def add_new_threshold_event(self): 
        # appends to the threshold event queue 

        raise Exception(f'must override add_new_threshold_event in class definition for {self.name}')
        self.threshold_event_queue.put()


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
                attribute = self.check_threshold_with_fn(self) # sets attribute value to reflect the value returned from the function call
            
            
            # Check for a Threshold Event by comparing the current threshold value with the goal value 
            if attribute == self.threshold_condition['goal_value']: # Threshold Event: interactable has met its threshold condition
                
                control_log(f'(InteractableABC.py, watch_for_threshold_event) {self} Threshold Event Detected!')
                event_bool = True 


                #
                # Interactable Threshold Event Handling
                #             
                if event_bool and self.active: 
                    ## AN EVENT! ## 

                    # Handle Event 
                    self.threshold = True

                    self.add_new_threshold_event() 
                
                    #
                    # Callback Function (OnThresholdEvent)
                    if "onThreshold_callback_fn" in self.threshold_condition: 
                        # execute each of the callback functions in the list, in order
                        callbackfn_lst = self.threshold_condition['onThreshold_callback_fn']
                        for callbackfn in callbackfn_lst: 
                            print(f'(InteractableABC, watch_for_threshold_event) calling onThreshold_callback_fn for {self.name}: ', "parents:[", *(p.name+' ' for p in self.parents) , "]  callbackfn: ", callbackfn)
                            parent_names = {*(p.name+' ' for p in self.parents)}
                            control_log(f' (InteractableABC, watch_for_threshold_event) calling onThreshold_callback_fn for {self.name}: parents:[ {parent_names}  ]  callbackfn: , {callbackfn} ')
                            callbackfn = eval(callbackfn)

                    print(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")
                    control_log(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")


                    '''
                    FISH
                    DELETE ME EVENTUALLY:: leaving this here to confirm that it rlly isn't needed. ( Part of process of deleting things having to do with dependents. )
                    if len(self.dependents) > 0: 
                        # sleep while dependents (if they exist) remain in goal state, meaning current interactable is also in its goal state.
                        # because interactable is not dependent on vole's actions, we can assume that it could potentially be sitting in its goal state for extended periods of time. 
                        # as a result, we want to sleep until it is out of its goal state ( or until threshold gets set to false by simulation ).

                        while attribute == self.threshold_condition['goal_value'] and self.threshold == True: 

                            time.sleep(1) # wait for change in threshold or a change in the attribute's value to differ away from goal_value 
                    '''
                    
                    # Since an event occurred, check if we should reset the attribute value to its inital value
                    ''' 
                    NOT SURE THAT reset_value SHOULD EVER BE AN OPTION BECAUSE FOR EVERY INTERACTABLE THAT HAS A THRESHOLD THAT REQUIRES 'check_threshold_with_fn', that means it probs doesnt make much sense to try to directly SET the threshold attribute. 
                    if ('reset_value' in self.threshold_condition.keys() and self.threshold_condition['reset_value'] is True): 

                        setattr( self, self.threshold_condition['attribute'], self.threshold_condition['initial_value'] )
                        print( f'(InteractableABC,py, watch_for_threshold_event) resetting {self.name} threshold attribute, {self.threshold_condition["attribute"]}, to its initial value for  ')
                        control_log( f'(InteractableABC,py, watch_for_threshold_event) resetting {self.name} threshold attribute, {self.threshold_condition["attribute"]}, to its initial value for  ')
                    
                    else:''' 
                    # if we are not resetting the value, then to ensure that we don't endlessly count threshold_events
                    # we want to wait for some kind of state change ( a change in its attribute value ) before again tracking a threshold event 
                    
                    #
                    # Sleep To Avoid Double Counting Threshold Events!
                    #
                    # LEAVING OFF HERE!!!!!! 
                    while event_bool: 

                        # repeatedly upate the current value of the threshold attribute so we can check for changes in its value #
                        # check for attributes that may have been added dynamically 
                        if hasattr(self, 'check_threshold_with_fn'): # the attribute check_threshold_with_fn is pointing to a function that we need to execute 
                            attribute = self.check_threshold_with_fn(self) # sets attribute value to reflect the value returned from the function call
                        else: 
                            attribute = getattr(self, threshold_attr_name) # necessary for lever_food w/ dispenser as its parent

                        # wait for a change in the attribute value before starting to look for an event again #
                        if attribute != self.threshold_condition['goal_value']: 
                            # Note: do not set interactable.threshold to False here! Threshold attribute is specifically for communication with Simulation. So the Simulation is in charge of resetting the threshold value to false. ( we do so in update_location when a vole passes by an interactable. )
                            event_bool = False # reset event bool so we exit loop
                            self.threshold = False # BIG CHANGE!!! FISH

                        # 2nd reason to start looking for an event: if the threshold_event_queue is emptied, meaning a Control side script used some threshold event in its logic
                        elif len(self.threshold_event_queue.queue) == 0: # isEmpty! 
                            event_bool = False # reset event bool so we exit loop 

                        # 3rd reason to start looking for an event: if the threshold has been set to False, but the attribute still == self.threshold_condition['goal_value'], 
                        # meaning we successfully communicated to a vole that there was a threshold reached, and because the vole passed by this interactable it set the threshold to False 
                        # when it passed by the interactable. 
                        #
                        # LEAVING OFF HERE::: THIS SEEMS ODD 
                        # FISH
                        # i still don't love that we set the threshold to false when we pass by it! 
                        #

                        
                        else: 

                            time.sleep(0.1)

                else: 
                    # no threshold event 
                    pass 
            else: 
                # no threshold event
                pass 
                
            
            time.sleep(0.75)
            


         
class lever(interactableABC):
    def __init__(self, ID, threshold_condition, hardware_specs, name):
        # Initialize the parent class
        super().__init__(threshold_condition, name)

        # Initialize the given properties
        self.ID        = ID 

        # Current Position Tracking # 
        self.isExtended = False 
        self.extended_angle = hardware_specs['servo_specs']['extended_angle']
        self.retracted_angle = hardware_specs['servo_specs']['retracted_angle']

        # Movement Controls # 
        self.servoObj = self.PosServo(servo_specs = hardware_specs['servo_specs'], parentObj = self) # positional servo to control extending/retracting lever; we can control by setting angles rather than speeds
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self) # button to recieve press signals thru changes in the gpio val

        ## Threshold Condition Tracking ## 
        # self.pressed is a property method to ensure that num_pressed updates

        # we want Button to be updating the num_pressed value

        if self.buttonObj.pressed_val < 0: # simulating gpio connection
            self.isPressed = None 
            # self.num_pressed = 0 
        else: 
            self.isPressed = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise 
            # self.num_pressed = self.pressed
            
        #self.required_presses = self.threshold_condition["goal_value"] # Threshold Goal Value specifies the threshold goal, i.e. required_presses to meet the threshold
        #self.threshold_attribute = self.threshold_condition["attribute"] # points to the attribute we should check to see if we have reached goal. For lever, this is simply a pointer to the self.pressed attribute. 

        ## Dependency Chain values can stay as the default ones set by InteractableABC ## 
        # self.barrier = False 
        # self.autonomous = False

        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  

    @property
    def num_pressed(self): 
        '''returns the current number of presses that button object has detected'''
        return self.buttonObj.num_pressed

    def reset_press_count(self): 
        ''' sets self.buttonObj.num_pressed to start from the initial value '''
        self.buttonObj.num_pressed = self.threshold_condition['initial_value'] 

    def set_press_count(self, count): 
        ''' sets self.buttonObj.num_pressed to specified value '''
        print(f'setting the number of presses to {count}')
        self.buttonObj.num_pressed = count 
        
    def activate(self): 
        ''' activate lever as usual, and once it is active we can begin the button object listening for presses'''
        interactableABC.activate(self)
        self.buttonObj.listen_for_event()


    def validate_hardware_setup(self):
        
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return 
        
        else: 
            # not simulating door, check that the doors Movement Controllers (button and servo) have been properly setup 
            if self.buttonObj.pressed_val < 0 or self.servoObj.servo is None: 
                
                errorMsg = []
                # problem with both button and/or servo. figure out which have problems
                if self.buttonObj.pressed_val < 0: 
                    errorMsg.append('buttonObj')
                
                if self.servoObj.servo is None: 
                    errorMsg.append('servoObj')
                
                raise Exception(f'(Lever, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')

            return 


    def add_new_threshold_event(self): 

        # appends to the lever's threshold event queue 
        self.threshold_event_queue.put(f'{self} pressed {self.num_pressed} times!')
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
            # self.activate() 
            return 
        

        #
        # HARDWARE THINGS -- use the Servo object to extend 
        #
        else: 
            # wiggle lever to reduce binding and buzzing 
            modifier = 15 
            if self.extended_angle > self.retracted_angle: extend_start = self.extended_angle + modifier
            else: extend_start = self.extended_angle - modifier 
            self.servoObj.servo.angle = extend_start # change angle to wiggle 
            
            time.sleep(0.1)
            
            # set to the fully extended angle 
            self.servoObj.servo.angle = self.extended_angle
            
            self.isExtended = True 

            return 

            
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
            # self.deactivate() 
            return 
        
        #
        # HARDWARE THINGS
        #
        else: 

            # set to the fully retracted angle 
            self.servoObj.servo.angle = self.retracted_angle
            self.isExtended = False 
            return 





    def stop(self): 
        if self.isSimulation: return 
        else: 
            '''Logic here for shutting down hardware'''
            self.retract() 
            return 









# # # # # # # # # # # # 
#      doors          # 
# # # # # # # # # # # #
class door(interactableABC):
    """This class is the unique door type class for interactable objects to be added to the Map configuration.

    Args:
        interactableABC ([type]): [description]
    """

    def __init__(self, ID, threshold_condition, hardware_specs, name):
        
        super().__init__(threshold_condition, name) # init the parent class 
        
        self.ID = ID  # init the given properties 
        

        # Speed Tracking # 
        self.stop_speed = hardware_specs['servo_specs']['servo_stop_speed']
        self.open_speed = hardware_specs['servo_specs']['servo_open_speed']
        self.close_speed = hardware_specs['servo_specs']['servo_close_speed']
        self.open_time = hardware_specs['open_time'] # time it takes for a door to open 
        self.close_timeout = hardware_specs['close_timeout'] # max time we will wait for a door to close before timing out


        # Door Controls: Requires Continuous Servo and Button (aka switch) # 
        self.servoObj = self.ContServo(hardware_specs['servo_specs'], parentObj = self) # continuous servo to control speed of opening and closing door
        self.buttonObj = self.Button(hardware_specs['button_specs'], parentObj = self) 
        
        ## Threshold Condition Tracking ## 
        if self.buttonObj.pressed_val < 0: 
            self.isOpen = threshold_condition['initial_value'] # if simulating gpio connection, then we want to leave isPressed as an attribute value that we can manually set
        else: # if not simulating gpio connection, then isPressed should be a function call that checks the GPIO input/output value each call
            self.isOpen = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise 
        
        # Set Doors Starting state to its Initial Open/Close Position
        # --> need to do this open/close startingstate AFTER isSimulation has been set. ( maybe just have people do this in the setup() function of the actual script )
        '''if self.isOpen != threshold_condition['initial_value']: 
            if threshold_condition['initial_value'] == True: 
                self.open() 
            else: 
                self.close()'''


        ## Dependency Chain Information ## 
        self.barrier = True # set to True if the interactable acts like a barrier to a vole, meaning we require a vole interaction of somesort everytime a vole passes by this interactable. 
        self.autonomous = False # False because doors are dependent on other interactables or on vole interactions ( i.e. doors are dependent on lever press )

        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  
    
    
    def override(self, open_or_close): 
        ''' if override button gets pressed we call this function on the door '''

        # immediately stop door movement 
        self.stop() 

        # reset door to stop execution of current door actions
        self.deactivate()
        self.activate() 

        if open_or_close == 'open': 

            self.open() 

        else: 

            self.close() 
        
    def validate_hardware_setup(self):
        
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return 
        
        else: 
            # not simulating door, check that the doors Movement Controllers (button and servo) have been properly setup 
            if self.buttonObj.pressed_val < 0 or self.servoObj.servo is None: 
                
                errorMsg = []
                # problem with both button and/or servo. figure out which have problems
                if self.buttonObj.pressed_val < 0: 
                    errorMsg.append('buttonObj')
                
                if self.servoObj.servo is None: 
                    errorMsg.append('servoObj')
                
                raise Exception(f'(Door, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')

            return 


    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 


    def add_new_threshold_event(self): 
        # appends to the threshold event queue 
        self.threshold_event_queue.put(f'{self.name} isOpen:{self.isOpen}')
        print("Door Threshold: ", self.threshold, "  Door Threshold Condition: ", self.threshold_condition)
        print(f'(Door(InteractableABC.py, add_new_threshold_event) {self.name} event queue: {list(self.threshold_event_queue.queue)}')
           
    #@threader
    def close(self):
        """This function closes the doors fully"""

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            # If door is being simulated, then rather than actually closing a door we can just set the state to False (representing a Closed state)
            print(f'(Door(InteractableABC), close()) {self.name} is being simulated. Setting state to Closed and returning.')
            self.isOpen = False 
            return 

        # check if the door is already closed 
        if self.isOpen is False: 

            # door is already closed 
            control_log('(Door(InteractableABC)) {self.name} was already Closed')
            print(f'(Door(InteractableABC)) {self.name} was already Closed')
            return 

        # 
        # Direct Rpi to Close Door
        # 
        self.servoObj.servo.throttle = self.close_speed 

        start = time.time() 
        while time.time() < ( start + self.close_timeout ): 
            # wait for door to close or bail if we timeout 
            if self.isOpen is False: 
                # door successfully closed 
                self.stop() # stop door movement 
                return 
            else:
                time.sleep(0.005)
        
        # Close Unsuccessful 
        self.stop() # stop door movement 
        control_log(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')
        print(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')
        # raise Exception(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')



    #@threader
    def open(self):
        """This function opens the doors fully
        """
        

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            # If door is being simulated, then rather than actually opening a door we can just set the state to True (representing an Open state)
            print(f'(Door(InteractableABC), open()) {self.name} is being simulated. Setting switch val to Open (True) and returning.')
            self.isOpen = True 
            return 
        
        # check if door is already open
        if self.isOpen is True: 

            control_log('(Door(InteractableABC)) {self.name} is Open')
            print(f'(Door(InteractableABC)) {self.name} is Open')
            return 
  

        # 
        # Direct RPI to Open Door 
        #
        self.servoObj.servo.throttle = self.open_speed 

        start = time.time() 
        while time.time() < ( start + self.open_time ): 
            #wait for the door to open -- we just have to assume this will take the exact same time of <open_time> each time, since we don't have a switch to monitor for if it opens all the way or not. 
            time.sleep(0.005) 
        
        self.stop() # stop door movemnt 

        # check if successful by checking the switch (button) val 
        if self.isOpen: 
            # successful 
            return 
        else: 
            control_log(f'(Door(InteractableABC), open() ) There was a problem opening {self.name}')
            print(f'(Door(InteractableABC), open() ) There was a problem opening {self.name}')
            # raise Exception(f'(Door(InteractableABC), open() ) There was a problem opening {self.name}')

    def stop(self): 
        ''' sets servo speed to stop speed '''
        # Function Accesses Hardware! Perform Simulation Check 
        if self.isSimulation: return 
        self.servoObj.servo.throttle = self.stop_speed 
        return 









class rfid(interactableABC):
    """This class is the unique class for rfid readers that is an interactable object. Note that this does not control the rfid readers like the other unique classes, it only deals with the handling of rfid data and its postion in the decision flow.

    Args:
        interactableABC ([type]): [description]
    """

    def __init__(self, ID, threshold_condition, name):
        # Initialize the parent 
        super().__init__(threshold_condition, name)
        self.ID = ID 
        self.rfidQ = queue.Queue()


        self.barrier = False # if rfid doesnt reach threshold, it wont prevent a voles movement
        self.autonomous = True # operates independent of direct interaction with a vole or other interactales. This will ensure that vole interacts with rfids on every pass. 
        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  


    def add_new_threshold_event(self): 
        '''New Ping was added to rfidQ. Retrieve its value and append to the threshold event queue '''
        try: 
            ping1 = self.rfidQ.get() 
            ping2 = self.rfidQ.get() 
            latency = ping2[2] - ping1[2] # calculates time difference between the 1st and 2nd ping
        except queue.Empty as e: 
            raise Exception(f'(InteractableABC.py, add_new_threshold_event) Nothing in the rfidQ for {self.name}')

        self.threshold_event_queue.put((ping1,ping2,latency))

        # do not deactivate the rfids. always monitoring for pings. 
    
    def validate_hardware_setup(self):
        ''' ensures that hardware was setup correctly '''
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return
        
        else: 
            # not simulating rfid. Check that connections occurred correctly 
            # 
            #  (TODO) setup RFID hardware things here! 
            #
            # print('rfid hardware doesnt exist yet!')
            return 

    def stop(self): 
        ''' '''
        if self.isSimulation: return 
        else: 
            '''Logic here for shutting down hardware'''
            return 


class buttonInteractable(interactableABC):
    ''' **this class should not be confused with the Button class which connects with/operates the GPIO boolean pins** 
        buttonInteractable is used for the buttons that control the open/closing of doors; if a door is in movement, these buttons override that movement immediately 
    '''

    def __init__(self, ID, threshold_condition, hardware_specs, name ): 
         # Initialize the parent class
        super().__init__(threshold_condition, name)

        # Initialize the given properties
        self.ID = ID 

        # Button # 
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self) # button to recieve press signals thru changes in the gpio val

        ## Threshold Condition Tracking ## 
        # self.pressed is a property method to ensure that num_pressed updates 
        self.buttonQ = queue.Queue()
        # we want Button to be updating the num_pressed value. notify 

        if self.buttonObj.pressed_val < 0: # simulating gpio connection
            self.isPressed = None 
        else: 
            self.isPressed = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise 
    
    # (NOTE - don't think i need this, as this should be handled by Button class now.)
    # @property
    # def pressed(self): 
    #    '''returns the current number of presses that button object has detected'''
    #    return self.buttonObj.num_pressed

    def activate(self): 
        ''' activate button as usual, and once it is active we can begin the button object listening '''
        interactableABC.activate(self)
        self.buttonObj.listen_for_event()

    def validate_hardware_setup(self):
        
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return 
        
        else: 
            # not simulating door, check that the doors Movement Controllers (button and servo) have been properly setup 
            if self.buttonObj.pressed_val < 0: 
                
                errorMsg = []
                # problem with both button and/or servo. figure out which have problems
                if self.buttonObj.pressed_val < 0: 
                    errorMsg.append('buttonObj')
                
                raise Exception(f'(buttonInteractable, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')

            return 
    
    def add_new_threshold_event(self):
        '''New [Press] was added to the buttonQ. Retrieve its value and append to the threshold event queue '''
        try: 
            press = self.buttonObj.buttonQ.get() 
        except queue.Empty as e: 
            raise Exception(f'(InteractableABC.py, add_new_threshold_event) Nothing in the buttonQ for {self.name}')

        # append to event queue 
        self.threshold_event_queue.put(press)
    



class dispenser(interactableABC): 

    def __init__(self, ID, threshold_condition, hardware_specs, name ): 

        # Initialize the parent class
        super().__init__(threshold_condition, name)

        self.ID = ID 

        # Movement Controls # 
        self.servoObj = self.PosServo(servo_specs = hardware_specs['servo_specs'], parentObj = self) # positional servo to control extending/retracting lever; we can control by setting angles rather than speeds
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self)  # Button/Sensor for detecting if pellet successfully dispensed # 

        ## Current Position/State Tracking ## 
        self.stop_speed = hardware_specs['servo_specs']['stop_speed']
        self.dispense_speed = hardware_specs['servo_specs']['dispense_speed']
        self.dispense_time = hardware_specs['dispense_time']
            
        # Threshold Tracking with isPressed attribute #
        if self.buttonObj.pressed_val < 0:  # simulating gpio connection, simulate the isPressed Value
            self.isPressed = self.threshold_condition['initial_value'] 
        else: # not simulating, use the actual buttonObj i/o value to get current state  
            self.isPressed = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise 

        '''if self.isPressed: # pellet is already present
            self.pellet_state = True 
            self.monitor_for_retrieval = True '''

        ## Use the Threshold Attribute to set pellet_state and monitor_for_retrieval ## 
        if self.isPressed: # pellet is already present
            initial = True 
        else: initial = False 
        self.pellet_state =  initial # True if pellet is in trough 
        self.monitor_for_retrieval = initial # gets set to True only once we first confirm that a pellet is present in the trough. When we set this True, then we will start recording threshold events ( i.e. waiting for the pellet state to get set back to false, due to a vole retrieval ) If trough is initially empty, this prevents watch_for_threshold_event from recording this empty state as the occurrence of a pellet retrieval.

        ## Dependency Chain ## 
        self.barrier = False # does not block a voles movement 
        self.autonomous = False # is dependent on a lever press in order to trigger a dispense


    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run    

    def validate_hardware_setup(self): 
        
        if self.isSimulation: 
            # we should make sure that the button and servo will also be simulated! 
            # Basically checks to make sure that they were not properly set up! 
            self.isPressed = self.threshold_condition['initial_value'] # ensures that we wont access the button object value version of the button gpio!

            return 
        
        else: 
            # not simulating dispenser, check that the dispenser Movement Controllers (button and servo) have been properly setup 
            if self.buttonObj.pressed_val < 0 or self.servoObj.servo is None: 
                errorMsg = []
                # problem with both button and/or servo. figure out which have problems
                if self.buttonObj.pressed_val < 0: 
                    errorMsg.append('buttonObj')
                if self.servoObj.servo is None: 
                    errorMsg.append('servoObj')
                raise Exception(f'(Dispenser, validate_hardware_setup) {self} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')
            return 

    def activate_inner_objects(self): 
        ''' overriding the function from InteractableABC! 
            this method gets called upon interactable activation 
            we are able to handle 
        '''
    def add_new_threshold_event(self):
        if self.monitor_for_retrieval: 
            self.threshold_event_queue.put(f'Pellet Retrieval')
            print('PELLET RETRIEVAL!')
            self.monitor_for_retrieval = False # reset since we recorded a single pellet retrieval.
        else: 
            control_log(f'(InteratableABC.py, {self}, add_new_threshold_event) not monitoring for retrieval at the moment')
            print(f'(InteratableABC.py, {self}, add_new_threshold_event)not monitoring for retrieval at the moment')
            return
        
    def start(self): 
        self.servoObj.servo.throttle = self.dispense_speed 
        print('hopefully servo is moving')
    def stop(self): 
        if self.isSimulation: 
            return 
        self.servoObj.servo.throttle = self.stop_speed
    
    @run_in_thread
    def dispense(self): 

        # Edge Case: if there is already a pellet in the trough, we don't want to dispense again ( this likely means vole did not take pellet on a previous dispense )
        if self.isPressed is True:     
            print('(InteractableABC, dispenser) Already a pellet in trough; previous pellet not retrieved')
            control_log(f'(InteractableABC, dispenser.dispense()) Already a pellet in trough; Previous pellet not retrieved.')
            return 

        # Simulation Check
        if self.isSimulation: 
            
            print('(InteractableABC, dispenser.dispense()) (simulated) Pellet Dispensed! ')
            control_log(f'(InteractableABC, dispenser.dispense()) (simualted) Pellet Dispensed! setting the isPressed value to True to simulate that a pellet was dispensed.  Monitoring for a pellet retrieval from {self}!')

            self.isPressed = True 
            self.monitor_for_retrieval = True 
            return 
        
        # Dispense a Pellet using Servos 
        self.start() # starts servo moving at dispense speed 

        # wait for the dispense timeout period. Check to see if pellet dispense was successful during this time. 
        dispenses_read = 0 
        start = time.time() 
        while time.time() < ( start + self.dispense_time ): 
            # Accuracy Check: check that we read isPressed as True at least twice in a row before confirming that there was a pellet dispensed. 
            if self.isPressed: 
                dispenses_read += 1 
            if dispenses_read > 2: 
                # Pellet was dispensed! 
                self.stop() 
                self.pellet_state = True # note that a pellet was dispensed 
                self.monitor_for_retrieval = True 
                print(f'(InteractableABC, Dispenser) {self}: Pellet Dispensed!')
                control_log(f'(InteractableABC, Dispenser) {self}: Pellet Dispensed!')
                return  
            time.sleep(0.005) 
        
        # On Failure: Stop dispenser and notify user.
        self.stop()
        print(f'(InteractableABC, Dispenser) {self}: A problem was encountered -- Pellet Dispensing Unsuccessful')
        control_log(f'(InteractableABC, Dispenser) {self}: A problem was encountered -- Pellet Dispensing Unsuccessful')
        return 





        
        



