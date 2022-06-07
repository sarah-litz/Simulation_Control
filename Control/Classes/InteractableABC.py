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

            # isSimulation is True if we were unable to connect to gpio pin 
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
                print(f'(InteractableABC.py, Button) {self.parent.name}: simulating gpio connection. ErrMssg: {e}')
                return -1

        def run_in_thread(func): 
            ''' decorator function to run function on its own daemon thread '''
            def run(*k, **kw): 
                t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
                t.start() 
                return t
            return run 

        @run_in_thread
        def simulated_listen_for_event(self, timeout = None): 
            ''' listener for a simulated button 
            '''

        @run_in_thread
        def listen_for_event(self, timeout=None, edge=None): # detects the current pin for the occurence of some event
            ''' 
            event detection for button. On event, incrememts the buttons num_pressed value 
            ( note this does not update/check isPressed, as this is handled by the property function isPressed )
            '''

            def increment_presses(pin): 
                self.num_pressed += 1 
                self.buttonQ.put(f'press#{self.num_pressed}') # add press to parents buttonQ
                print(f'(InteractableABC, Button.listen_for_event) {self.parent} Button Object was Pressed. num_pressed = {self.num_pressed}, buttonQ = {list(self.buttonQ.queue)}')
                control_log(f'(InteractableABC, Button.listen_for_event) {self.parent} Button Object was Pressed. num_pressed = {self.num_pressed}')
                

            #
            # Sim Check; this function accesses gpio library. If button is being simulated, call the simulation version of this function and return. 
            #
            if self.isSimulation: 

                # If button is being simulated, then we care about changes to isPressed. If isPressed == True, then increment presses

                print(f'(InteractableABC, Button, list_for_event) Button for {self.parent} is being simulated. Calling simulated_listen_for_event instead.')  
                control_log(f'(InteractableABC, Button, list_for_event) Button for {self.parent} is being simulated. Calling simulated_listen_for_event instead.')  
                return             

            #
            # Wait For Event
            #
            if edge is None: 
                # default to the falling edge 
                GPIO.add_event_detect( self.pin_num, GPIO.FALLING, bouncetime = 200, callback = increment_presses )
            else: 
                GPIO.add_event_detect(self.pin_num, edge, bouncetime = 200, callback = increment_presses )
            

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
            
            print(f'(InteractableABC, Button.isPressed property call)')
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
                print(f'(InteractableABC.py, Servo) {self.parent.name}: simulating servo connection. ErrMssg: {e}' )
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
        if interactable contains any inner objects (buttons and servos), this function is called to 
        ensure that they are activated for each mode 
        '''
        pass 

    def activate(self):
        ''' 
        called at the start of each mode. begins tracking for thresholds for both itself as well as its dependents. 
        '''

        try: self.validate_hardware_setup() # validate that this hardware was properly setup (e.g. the button and servos ) if interactable is not being simulated
        except Exception as e: print(e), sys.exit(0)

        print(f"(InteractableABC.py, activate) {self.name} has been activated. isSimulation: {self.isSimulation}. starting contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
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
                attribute = self.check_threshold_with_fn(self) # sets attribute value to reflect the value returned from the function call
            
            
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
                
                    #
                    # Callback Function (OnThresholdEvent)
                    if "onThreshold_callback_fn" in self.threshold_condition: 
                        # call call back function 
                        print(f'(InteractableABC, watch_for_threshold_event) calling onThreshold_callback_fn for {self.name}')
                        callbackfn = self.threshold_condition['onThreshold_callback_fn']
                        print("parents:[", *(p.name+' ' for p in self.parents) , "]  callbackfn: ", callbackfn)
                        callbackfn = eval(callbackfn)


                    print(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")
                    control_log(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")



                    if len(self.dependents) > 0: 
                        # sleep while dependents (if they exist) remain in goal state, meaning current interactable is also in its goal state.
                        # because interactable is not dependent on vole's actions, we can assume that it could potentially be sitting in its goal state for extended periods of time. 
                        # as a result, we want to sleep until it is out of its goal state ( or until threshold gets set to false by simulation ).

                        while attribute == self.threshold_condition['goal_value'] and self.threshold == True: 

                            time.sleep(1) # wait for change in threshold or a change in the attribute's value to differ away from goal_value 

                    
                    # Since an event occurred, check if we should reset the attribute value to its inital value
                    if ('reset_value' in self.threshold_condition.keys() and self.threshold_condition['reset_value'] is True): 

                        setattr( self, self.threshold_condition['attribute'], self.threshold_condition['initial_value'] )
                        print( f'(InteractableABC,py, watch_for_threshold_event) resetting {self.name} threshold attribute, {self.threshold_condition["attribute"]}, to its initial value for  ')
                        control_log( f'(InteractableABC,py, watch_for_threshold_event) resetting {self.name} threshold attribute, {self.threshold_condition["attribute"]}, to its initial value for  ')

                    else: 
                        # if we are not resetting the value, then to ensure that we don't endlessly count threshold_events
                        # we want to wait for some kind of state change ( a change in its attribute value ) before again tracking a threshold event 
                        #
                        # Sleep To Avoid Double Counting Threshold Events!
                        #
                        # LEAVING OFF HERE!!!!!! 
                        while event_bool: 

                            # check for attributes that may have been added dynamically 
                            if hasattr(self, 'check_threshold_with_fn'): # the attribute check_threshold_with_fn is pointing to a function that we need to execute 
                                attribute = self.check_threshold_with_fn(self) # sets attribute value to reflect the value returned from the function call
                            
                            # wait for a change in the attribute value before starting to look for an event again
                            if attribute != self.threshold_condition['goal_value']: 
                                event_bool = False # reset event bool so we exit loop
                            
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
        self.pressed = self.buttonObj.num_pressed # returns total number of presses that the buttonObj has counted

        # we want Button to be updating the num_pressed value. notify 

        if self.buttonObj.pressed_val < 0: # simulating gpio connection
            self.isPressed = None 
        else: 
            self.isPressed = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise 
            
        #self.required_presses = self.threshold_condition["goal_value"] # Threshold Goal Value specifies the threshold goal, i.e. required_presses to meet the threshold
        #self.threshold_attribute = self.threshold_condition["attribute"] # points to the attribute we should check to see if we have reached goal. For lever, this is simply a pointer to the self.pressed attribute. 

        ## Dependency Chain values can stay as the default ones set by InteractableABC ## 
        # self.barrier = False 
        # self.autonomous = False

        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  

    
    
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
                
                raise Exception(f'(Lever, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead.')

            return 


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


    def __move(self, angle):
        """This moves the lever to the specified angle. This can be any angle in the correct range, and the function will produce an error if the angle is out of range of the motor. 

        Args:
            angle (int): Servo angle to move to. This should be between 0 and 180 degrees
        """

        #  This Function Accesses Hardware => Perform Sim Check First
        pass



    def stop(self): 
        if self.isSimulation: return 
        else: 
            '''Logic here for shutting down hardware'''
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
        if self.isOpen != threshold_condition['initial_value']: 
            if threshold_condition['initial_value'] == True: 
                self.open() 
            else: 
                self.close()


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
                
                raise Exception(f'(Door, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead.')

            return 


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
                    '''if self.threshold_condition['goal_value'] == True: 

                        self.open() 

                    elif self.threshold_condition['goal_value'] == False: 

                        self.close() 
                    
                    else: 

                        raise Exception(f'(Door, dependents_loop) did not recognize {self.name} threshold_condition[goal_value] of {self.threshold_condition["goal_value"]}')
                    '''



    def add_new_threshold_event(self): 
        # appends to the threshold event queue 
        self.threshold_event_queue.put(f'{self.name} isOpen:{self.buttonObj}')
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

    def __init__(self, ID, threshold_condition, name):
        # Initialize the parent 
        super().__init__(threshold_condition, name)
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
    
    def validate_hardware_setup(self):
        ''' ensures that hardware was setup correctly '''
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return
        
        else: 
            # not simulating rfid. Check that connections occurred correctly 
            print('rfid hardware does not yet exist. Cant setup a connection. pls simulate instead.')

    def stop(self): 
        ''' '''
        if self.isSimulation: return 
        else: 
            '''Logic here for shutting down hardware'''
            return 


class buttonInteractable(interactableABC):
    ''' **should not be confused with the Button class which connects with/operates the GPIO boolean pins 
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
        # elf.pressed = self.buttonObj.num_pressed # returns total number of presses that the buttonObj has counted
        self.buttonQ = queue.Queue()
        # we want Button to be updating the num_pressed value. notify 

        if self.buttonObj.pressed_val < 0: # simulating gpio connection
            self.isPressed = None 
        else: 
            self.isPressed = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise 
    
    @property
    def pressed(self): 
        '''returns the current number of presses that button object has detected'''
        return self.buttonObj.num_pressed

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
                
                raise Exception(f'(buttonInteractable, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead.')

            return 
    
    def add_new_threshold_event(self):
        '''New [Press] was added to the buttonQ. Retrieve its value and append to the threshold event queue '''
        try: 
            press = self.buttonObj.buttonQ.get() 
        except queue.Empty as e: 
            raise Exception(f'(InteractableABC.py, add_new_threshold_event) Nothing in the buttonQ for {self.name}')

        # append to event queue 
        self.threshold_event_queue.put(press)
        