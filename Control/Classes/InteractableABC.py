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
import random
import threading
import queue
import signal
import sys

# Local Imports 
from Logging.logging_specs import control_log, sim_log
from .Timer import Visuals

try: 
    import RPi.GPIO as GPIO 
except Exception as e: 
    print(e)
    GPIO = None
try: 
    import pigpio as pigpio
except Exception as e: 
    print(e)
    pigpio = None
try: 
    from adafruit_servokit import ServoKit
    SERVO_KIT = ServoKit(channels=16) 
except Exception as e: 
    print(e)
    SERVO_KIT = None




class interactableABC:

    def __init__(self, threshold_condition, name, event_manager):

        ## Shared Among Interactables ## 
        self.event_manager = event_manager

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


        ## Servo and Button Objects ( Attibutes will be Overriden in the Derived Classes if they use a Button or a Servo )
        self.buttonObj = None 
        self.servoObj = None 

    
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
            

            # Setup the isSimulation attribute: isSimulation is True if we were unable to connect to gpio pin 
            self.isSimulation = False 

            # self.pressed_val denotes what value we should look for (0 or 1) that denotes a lever press 
            self.pressed_val = self._setup_gpio()  # defaults to -1 in scenario that gpio setup fails (including if isSimulation)


            # 
            # Setup isPressed Variable --> setup depends on if Button is a simulation or not
            if self.isSimulation: 
                self.isPressed = False # simulated buttons have a boolean isPressed that manually will get set to True/False by a simulation script.
            else: 
                self.isPressed = self.isPressedProperty # actual buttons get access to method version which checks GPIO value in order to know if isPressed is True or False


        def __str__(self): 
            return self.isPressed

        def _setup_gpio(self): 

            if self.parent.isSimulation: 
                control_log(f'(InteractableABC.py, Button) {self.parent.name}: simulating gpio connection.')
                self.parent.messagesReturnedFromSetup += f'simulating gpio connection. '
                return -1

            try: 
                if self.pullup_pulldown == 'pullup':
                    GPIO.setup(self.pin_num, GPIO.IN, pull_up_down = GPIO.PUD_UP)
                    return 0 
                elif self.pullup_pulldown == 'pulldown': 
                    GPIO.setup(self.pin_num, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
                    return 1
                else: 
                    raise KeyError(f'(InteractableABC.py, Button) {self.parent.name}: Configuration file error when instantiating Button {self.name}, must be "pullup" or "pulldown", but was passed {self.pullup_pulldown}')
            
            except Exception as e: 
                # attribute error raised 
                control_log(f'(InteractableABC.py, Button) {self.parent.name}: simulating gpio connection. ErrMssg: {e}')
                self.parent.messagesReturnedFromSetup += f' simulating GPIO button. '
                self.isSimulation = True
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
            self.isSimulation = False 
            
        def __set_servo(self): 
            if SERVO_KIT is None: 
                # simulating servo kit
                return None 
            
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
                self.parent.messagesReturnedFromSetup(f' simulating servo. ')
                self.isSimulation = True 
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

    def activate(self, initial_activation = True ):
        ''' 
        called at the start of each mode. begins tracking for thresholds for both itself as well as its dependents. 
        '''

        if initial_activation: 
            try: self.validate_hardware_setup() # validate that this hardware was properly setup (e.g. the button and servos ) if interactable is not being simulated
            except Exception as e: print(e), sys.exit(0)

        control_log(f"(InteractableABC.py, activate) {self.name} has been activated. starting contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
        
        self.threshold = False # "resets" the interactable's threshold value so it'll check for a new threshold occurence
        self.active = True 
        self.watch_for_threshold_event() # begins continuous thread for monitoring for a threshold event
        

    def deactivate(self): 
        
        self.threshold = False # "resets" the threshold value so it'll only check for a new threshold occurence in anything following its deactivation
        self.active = False 

        if hasattr(self, 'stop'): 
            self.stop() # stops things that could be left running

        self.event_manager.print_to_terminal(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")        
        control_log(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
    
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
                        if callbackfn_lst is not None: 
                            for callbackfn in callbackfn_lst: 
                                # print(f'(InteractableABC, watch_for_threshold_event) calling onThreshold_callback_fn for {self.name}: ', "parents:[", *(p.name+' ' for p in self.parents) , "]  callbackfn: ", callbackfn)
                                parent_names = {*(p.name+' ' for p in self.parents)}
                                control_log(f' (InteractableABC, watch_for_threshold_event) calling onThreshold_callback_fn for {self.name}: parents:[ {parent_names}  ]  callbackfn: , {callbackfn} ')
                                callbackfn = eval(callbackfn)

                    self.event_manager.print_to_terminal(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")
                    control_log(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")
                else: 
                    # not active, don't record the threshold event 
                    pass 
            else: 
                # no threshold event, ensure that threshold is False 
                self.threshold = False 

 
class lever(interactableABC):
    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager):
        # Initialize the parent class
        super().__init__(threshold_condition, name, event_manager)

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

        '''if self.buttonObj.pressed_val < 0: # simulating gpio connection
            self.isPressed = None 
            # self.num_pressed = 0 
        else: 
            self.isPressed = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise 
            # self.num_pressed = self.pressed'''
            
        #self.required_presses = self.threshold_condition["goal_value"] # Threshold Goal Value specifies the threshold goal, i.e. required_presses to meet the threshold
        #self.threshold_attribute = self.threshold_condition["attribute"] # points to the attribute we should check to see if we have reached goal. For lever, this is simply a pointer to the self.pressed attribute. 

        ## Dependency Chain values can stay as the default ones set by InteractableABC ## 
        # self.barrier = False 
        # self.autonomous = False

        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  
    
    def __str__(self): 
        return f'{self.name}(isExtended:{self.isExtended})'

    @property 
    def isPressed(self): 
        '''True if the button object is in a pressed state, false otherwise'''
        return self.buttonObj.isPressed 

    @property
    def num_pressed(self): 
        '''returns the current number of presses that button object has detected'''
        return self.buttonObj.num_pressed

    def reset_press_count(self): 
        ''' sets self.buttonObj.num_pressed to start from the initial value '''
        print('RESETTING BUTTON OBJECT NUM PRESSED')
        self.buttonObj.num_pressed = self.threshold_condition['initial_value'] 

    def set_press_count(self, count): 
        ''' sets self.buttonObj.num_pressed to specified value '''
        self.buttonObj.num_pressed = count 
        
    def activate(self, initial_activation = True ): 
        ''' activate lever as usual, and once it is active we can begin the button object listening for presses'''
        if self.active: 
            return # was already active. This is to avoid calling buttonObj.listen_for_event multiple times, as it is a threaded funciton.
        if self.isExtended: 
            interactableABC.activate(self, initial_activation)
            self.buttonObj.listen_for_event() # Threaded fn call 


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
        event = f'{self}_{self.num_pressed}_Presses'

        # add threshold event to queue 
        self.threshold_event_queue.put(event)

        # add timestamp 
        self.event_manager.new_timestamp(event, time=time.time())

        # wait for lever to reach unpressed state
        # while self.num_pressed == self.threshold_condition['goal_value'] and self.active: 
        #    ''' ''' 
        #     print('..')
        #    time.sleep(0.3)
        

    #@threader
    def extend(self):
        """Extends the lever to the correct value
        """
        control_log(f'(InteractableABC, Lever.extend) extending {self.name} ')
        self.activate(initial_activation=False)

        if self.isExtended: 
            # already extended 
            self.event_manager.print_to_terminal(f'(InteractableABC, Lever.extend) {self.name} already extended.')
            self.activate(initial_activation=False)
            return 


        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            self.isExtended = True 
            self.activate(initial_activation=False)
        

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

        return self.event_manager.new_timestamp(f'{self}_Extend', time.time())
        

            
    #@threader
    def retract(self):
        """Retracts lever to the property value
        """
        control_log(f'(InteractableABC, Lever.retract) retracting {self.name} ')

        if not self.isExtended: 
            self.event_manager.print_to_terminal(f'(InteractableABC, Lever.retract) {self.name} already retracted.')
            self.event_manager.new_timestamp(f'{self}_Already_Retracted', time.time())
            self.deactivate()
            return 

        
        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            self.isExtended = False 
            self.event_manager.new_timestamp(f'{self}_Retract', time.time())
            self.deactivate()
            return 
        
        #
        # HARDWARE THINGS
        #
        else: 
            # set to the fully retracted angle 
            self.servoObj.servo.angle = self.retracted_angle
            self.isExtended = False 
            self.deactivate()
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

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager):
        
        super().__init__(threshold_condition, name, event_manager) # init the parent class 
        
        self.ID = ID  # init the given properties 
        

        # Speed Tracking # 
        self.stop_speed = hardware_specs['servo_specs']['servo_stop_speed']
        self.open_speed = hardware_specs['servo_specs']['servo_open_speed']
        self.close_speed = hardware_specs['servo_specs']['servo_close_speed']
        self.open_timeout = hardware_specs['open_time'] # time it takes for a door to open 
        self.close_timeout = hardware_specs['close_timeout'] # max time we will wait for a door to close before timing out


        # Door Controls: Requires Continuous Servo and Button (aka switch) # 
        self.servoObj = self.ContServo(hardware_specs['servo_specs'], parentObj = self) # continuous servo to control speed of opening and closing door
        self.buttonObj = self.Button(hardware_specs['button_specs'], parentObj = self) 
        
        ## Dependency Chain Information ## 
        self.barrier = True # set to True if the interactable acts like a barrier to a vole, meaning we require a vole interaction of somesort everytime a vole passes by this interactable. 
        self.autonomous = False # False because doors are dependent on other interactables or on vole interactions ( i.e. doors are dependent on lever press )

        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  
    
    def __str__(self):
        return self.name+f'(Open:{self.isOpen})'

    @property
    def isOpen(self): 
        return self.buttonObj.isPressed 
    def sim_open(self): 
        if self.isSimulation: 
            self.buttonObj.isPressed = True 
            self.event_manager.new_countdown(f'sim_{self.name}_open', self.open_timeout)
    def sim_close(self): 
        if self.isSimulation: 
            self.event_manager.new_countdown(f'sim_{self.name}_close', self.close_timeout)
            self.buttonObj.isPressed = False 



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
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable. 
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
        state = self.isOpen
        if self.isOpen: event = f'{self.name}_Open'
        else: event = f'{self.name}_Close'

        self.threshold_event_queue.put(event)
        self.event_manager.new_timestamp(event, time=time.time())


        self.event_manager.print_to_terminal(f"{self.name} Threshold:  {self.threshold} Threshold Condition: {self.threshold_condition}")
        self.event_manager.print_to_terminal(f'(Door(InteractableABC.py, add_new_threshold_event) {self.name} event queue: {list(self.threshold_event_queue.queue)}')

        # To avoid overloading a door with threshold events, we can sleep here until a state change occurs 
        while self.isOpen == state and self.active: 
            if len(self.threshold_event_queue.queue) == 0: # isEmpty!
                # control side "used" the added threshold event, so even if there hasn't been a state change, break out of while loop so we can add another threshold event 
                return  
            time.sleep(.5)
        return 
        
           
    #@threader
    def close(self):
        """This function closes the doors fully"""

        # check if the door is already closed 
        if self.isOpen is False: 
            # door is already closed 
            control_log('(Door(InteractableABC)) {self.name} was already Closed')
            self.event_manager.print_to_terminal(f'(Door(InteractableABC)) {self.name} was already Closed')
            return 

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            self.event_manager.print_to_terminal(f'(Door(InteractableABC), close()) {self.name} is being simulated. setting state to Closed and returning.')
            self.sim_close() 
            return 

        # 
        # Direct Rpi to Close Door
        # 
        ts_start = self.event_manager.new_timestamp(f'{self}_close_Start', time = time.time())
        self.servoObj.servo.throttle = self.close_speed 

        start = time.time() 
        while time.time() < ( start + self.close_timeout ): 
            # wait for door to close or bail if we timeout 
            if self.isOpen is False: 
                # door successfully closed 
                self.stop() # stop door movement 
                t = time.time()
                self.event_manager.new_timestamp(f'{self}_close_Finish', time=t, duration = t - ts_start.time)
                return 
            else:
                time.sleep(0.005)
        
        # Close Unsuccessful 
        self.stop() # stop door movement 
        t = time.time()
        self.event_manager.new_timestamp(f'{self}_close_Failure', time=t, duration = t - ts_start.time)
        control_log(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')
        self.event_manager.print_to_terminal(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')
        return 
        # raise Exception(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')


    #@threader
    def open(self):
        """This function opens the doors fully
        """
        

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            # If door is being simulated, then rather than actually opening a door we can just set the state to True (representing an Open state)
            self.event_manager.print_to_terminal(f'(Door(InteractableABC), open()) {self.name} is being simulated. Setting switch val to Open (True) and returning.')
            self.sim_open()
            return 
        
        # check if door is already open
        if self.isOpen is True: 
            control_log('(Door(InteractableABC)) {self.name} is Open')
            self.event_manager.print_to_terminal(f'(Door(InteractableABC)) {self.name} is Open')
            return 
  

        # 
        # Direct RPI to Open Door 
        #
        self.servoObj.servo.throttle = self.open_speed 

        start = time.time() 
        while time.time() < ( start + self.open_timeout ): 
            #wait for the door to open -- we just have to assume this will take the exact same time of <open_time> each time, since we don't have a switch to monitor for if it opens all the way or not. 
            time.sleep(0.005) 
        
        self.stop() # stop door movemnt 

        # check if successful by checking the switch (button) val 
        if self.isOpen: 
            # successful 
            return 
        else: 
            control_log(f'(Door(InteractableABC), open() ) There was a problem opening {self.name}')
            self.event_manager.print_to_terminal(f'(Door(InteractableABC), open() ) There was a problem opening {self.name}')
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

    def __init__(self, ID, threshold_condition, name, event_manager):
        # Initialize the parent 
        super().__init__(threshold_condition, name, event_manager)
        self.ID = ID 
        self.rfidQ = queue.Queue()

        
        # self.shared_rfidQ: after initialization, assinged a shared_rfidQ attribute in ModeABC. This is a shared queue among all of the rfids. 

        self.ping_history = [] # exhaustive list of all the pings that have occurred, independent of phase/mode 

        self.barrier = False # if rfid doesnt reach threshold, it wont prevent a voles movement
        self.autonomous = True # operates independent of direct interaction with a vole or other interactales. This will ensure that vole interacts with rfids on every pass. 
        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  

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


    def sim_ping(self, vole): 
        # simulates an RFID ping by adding to the shared rfidQ 
        # self.shared_rfidQ.put((vole, self.ID, (time.time() + (random.randint(1,3) - random.random())) ))
        [self.shared_rfidQ.put((vole, self.ID, (time.time() + ( i - random.random() )))) for i in range (1,3)]


    class Ping: 
        ''' class for packaging rfid pings into pairs in order to represent the time that a vole first scanned an the rfid reader, 
        to the time that the vole left that rfid reader '''
        def __init__(self, ping1, ping2 = None, latency = None): 
            self.vole_tag = ping1[0]
            self.rfid_id = ping1[1]
            self.ping1 = ping1
            self.ping2 = ping2
            self.latency = latency 
        
        def set_ping2(self, ping2): 
            ''' updates ping2 with new ping2 value, and sets the threshold value '''
            if self.ping2 is not None: 
                raise Exception(f'(InteractableABC.py) rfid{self.rfid_id} already contains a value for ping2')
            else: 
                self.ping2 = ping2
                self.latency = ping2[2] - self.ping1[2]
        
        def __str__(self): 
            return f'({self.vole_tag}, {self.rfid_id}, {self.latency})'
        
        def __repr__(self): 
            return f'({self.vole_tag}, {self.rfid_id}, {self.latency})'
        
        def __iter__(self): 
            return [{self.vole_tag}, {self.rfid_id}, {self.latency}]
    
        
    def add_new_threshold_event(self): 
        '''New Ping was added to rfidQ. Retrieve its value and append to the threshold event queue '''
        try: 
            ping = self.rfidQ.get() 
            self.event_manager.print_to_terminal('PING: ', ping)
            # Check if the new ping is the 2nd ping ( a vole leaving an rfid reader ) or a first ( a vole arriving at the rfid reader )
            # Starting at the end of the end of the ping history list ( so the most recent pings ), look for a ping from this vole
            voletag = ping[0]
            newEntry = True 
            for idx in range(len(self.ping_history)-1, -1, -1): 
                p = self.ping_history[idx]
                if p.vole_tag == voletag: 
                    # check to see if a 2nd ping was recorded 
                    if p.ping2 is None: 
                        # The new ping should be recorded as the 2nd ping in this Ping Object! Do not add a new threshold event. 
                        # Update Existing Ping Object
                        p.set_ping2(ping) # sets ping2 and calculates latency 

                        # Record Timestamp for Ping 2 
                        self.event_manager.new_timestamp(f'rfid{p.rfid_id}_ping2_vole{p.vole_tag}', time=p.ping2[2], duration = p.latency)

                        newEntry = False 
                        return 
                    else: 
                        newEntry = True 
                        break 
            if newEntry: 
                # create new Ping object and add to threshold event queue! 
                ping2 = None
                latency = None 
                newPing = self.Ping(ping, ping2, latency)
                self.ping_history.append(newPing)
                self.threshold_event_queue.put(newPing)
                # Record Timestamp for Ping 1 
                ping1_timestamp = self.event_manager.new_timestamp(f'rfid{newPing.rfid_id}_ping1_vole{newPing.vole_tag}', time=newPing.ping1[2])

            
        
        except queue.Empty as e: 
            raise Exception(f'(InteractableABC.py, add_new_threshold_event) Nothing in the rfidQ for {self.name}')

        # do not deactivate the rfids. always monitoring for pings. 
    

    def stop(self): 
        ''' '''
        if self.isSimulation: return 
        else: 
            '''Logic here for shutting down hardware'''
            return 



class dispenser(interactableABC): 

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager): 

        # Initialize the parent class
        super().__init__(threshold_condition, name, event_manager)

        self.ID = ID 

        # Movement Controls # 
        self.servoObj = self.PosServo(servo_specs = hardware_specs['servo_specs'], parentObj = self) # positional servo to control extending/retracting lever; we can control by setting angles rather than speeds
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self)  # Button/Sensor for detecting if pellet successfully dispensed # 

        ## Current Position/State Tracking ## 
        self.stop_speed = hardware_specs['servo_specs']['stop_speed']
        self.dispense_speed = hardware_specs['servo_specs']['dispense_speed']
        self.dispense_time = hardware_specs['dispense_time']
            
        # Threshold Tracking with isPressed attribute #
        '''  This should now be handled by the Button Class!! Just access buttonObj.isPressed no matter what. 
        if self.buttonObj.pressed_val < 0:  # simulating gpio connection, simulate the isPressed Value
            self.isPressed = self.threshold_condition['initial_value'] 
        else: # not simulating, use the actual buttonObj i/o value to get current state  
            self.isPressed = self.buttonObj.isPressed # True if button is in a pressed state, false otherwise '''

        ## Use the Threshold Attribute to set if we should immediately monitor_for_retrieval ## 
        if self.buttonObj.isPressed: # pellet is already present
            initial = True 
        else: initial = False 
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
            # self.isPressed = self.threshold_condition['initial_value'] # ensures that we wont access the button object value version of the button gpio!

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

    @property 
    def isPressed(self): 
        return self.buttonObj.isPressed 
    @property
    def isPelletRetrieved(self): 
        # returns True if no pellet in trough, returns False if pellet in trough
        return not self.isPressed


    def sim_press(self): 
        if self.isSimulation: 
            self.buttonObj.isPressed = True
    def sim_unpress(self): 
        if self.isSimulation: 
            self.buttonObj.isPressed = False 
    def sim_dispense(self): 
        ''' '''
        self.event_manager.print_to_terminal('(InteractableABC, dispenser.sim_dispense()) (simulated) Pellet Dispensed! ')
        control_log(f'(InteractableABC, dispenser.sim_dispense()) (simualted) Pellet Dispensed! setting the isPressed value to True to simulate that a pellet was dispensed.  Monitoring for a pellet retrieval from {self}!')
        self.sim_press() # simulates a dispense by setting button object to a pressed state 
        return 
    def sim_vole_retrieval(self): 
        ''' '''
        self.event_manager.print_to_terminal('(InteractableABC, dispenser.sim_vole_retrieval) Pellet Retrieved!')
        control_log(f'(InteractableABC, dispenser.sim_vole_retrieval) Pellet Retrieved! Stopped monitoring for a pellet retrieval.')
        self.sim_unpress() # simulates a retrieval by setting button object to an unpressed state 
        return 




    def activate_inner_objects(self): 
        ''' overriding the function from InteractableABC! 
            this method gets called upon interactable activation 
            we are able to handle 
        '''
    def add_new_threshold_event(self):

        if self.monitor_for_retrieval: 
            self.threshold_event_queue.put(f'Pellet Retrieval')
            self.event_manager.new_timestamp(f'{self.name}_pellet_retrieved', time = time.time())
            self.monitor_for_retrieval = False # reset since we recorded a single pellet retrieval.
        else: 
            control_log(f'(InteratableABC.py, {self}, add_new_threshold_event) not monitoring for retrieval at the moment')
            self.event_manager.print_to_terminal(f'(InteratableABC.py, {self}, add_new_threshold_event) not monitoring for retrieval at the moment')

        # To avoid overloading a food trough sensor with threshold events for when the food trough is empty, we can sleep here until a state change occurs 
        while not self.monitor_for_retrieval and self.active: 
            ''' wait for monitor for retrieval to get set to True! '''
            time.sleep(.5)
        

    def start(self): 
        self.servoObj.servo.throttle = self.dispense_speed 
        # print('(InteractableABC.py, dispense.start()) Started Servo')
    def stop(self): 
        if self.isSimulation: 
            return 
        self.servoObj.servo.throttle = self.stop_speed
    
    @run_in_thread
    def dispense(self): 

        # Edge Case: if there is already a pellet in the trough, we don't want to dispense again ( this likely means vole did not take pellet on a previous dispense )
        if self.isPressed is True:    

            self.event_manager.print_to_terminal('(InteractableABC, dispenser) Already a pellet in trough; previous pellet not retrieved')
            control_log(f'(InteractableABC, dispenser.dispense()) Already a pellet in trough; Previous pellet not retrieved.')
            self.monitor_for_retrieval = True 
            return 

        # Simulation Check
        if self.isSimulation: 
            self.sim_dispense()
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
                self.monitor_for_retrieval = True 
                self.event_manager.print_to_terminal(f'(InteractableABC, Dispenser) {self}: Pellet Dispensed!')
                control_log(f'(InteractableABC, Dispenser) {self}: Pellet Dispensed!')
                return  
            time.sleep(0.005) 
        
        # On Failure: Stop dispenser and notify user.
        self.stop()
        self.event_manager.print_to_terminal(f'(InteractableABC, Dispenser) {self}: A problem was encountered -- Pellet Dispensing Unsuccessful')
        control_log(f'(InteractableABC, Dispenser) {self}: A problem was encountered -- Pellet Dispensing Unsuccessful')
        return 



class buttonInteractable(interactableABC):
    ''' **this class should not be confused with the Button class which connects with/operates the GPIO boolean pins** 
        buttonInteractable is used for the buttons that control the open/closing of doors; if a door is in movement, these buttons override that movement immediately 
    '''

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager ): 
         # Initialize the parent class
        super().__init__(threshold_condition, name, event_manager)

        # Initialize the given properties
        self.ID = ID 

        # Button # 
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self) # button to recieve press signals thru changes in the gpio val

    
    def activate(self): 
        ''' activate button as usual, and once it is active we can begin the button object listening '''
        interactableABC.activate(self)
        self.buttonObj.listen_for_event()

    def validate_hardware_setup(self):
        
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return 
        
        else: 
            # not simulating button, check that the button object has been properly setup 
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
        self.event_manager.new_timestamp(f'{self.name}_pressed', time = time.time())


class beam(interactableABC): 

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager): 

         # Initialize the parent class
        super().__init__(threshold_condition, name, event_manager)

        self.ID = ID 

        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self)

        ## Threshold Condition Tracking ## 
        if self.buttonObj.pressed_val < 0: 
            self.isBroken = threshold_condition['initial_value'] # if simulating gpio connection, then we want to leave isPressed as an attribute value that we can manually set
        else: # if not simulating gpio connection, then isPressed should be a function call that checks the GPIO input/output value each call
            self.isBroken = self.buttonObj.isPressed # True if button is in a pressed state --> represents beam being broken 
        self.break_history = [] # exhaustive list of all the timestamps of the beam breaks that have occurred for this beam 
        
        self.barrier = False # if beam doesnt reach threshold, it wont prevent a voles movement
        self.autonomous = True # operates independent of direct interaction with a vole or other interactales. This will ensure that vole interacts with beams on every pass. 

    # # Button Object # # 
    @property 
    def num_breaks(self): 
        ''' return the current number of breaks that have been recorded'''
        # Button Object updates the num_pressed object 
        return self.buttonObj.num_pressed

    def reset_break_count(self): 
        ''' used as a callback function set by the beam config file '''
        self.buttonObj.num_pressed = self.threshold_condition['initial_value']


    def validate_hardware_setup(self):
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return 
        else: 
            # not simulating beam, check that the beam's button was setup correctly
            if self.buttonObj.pressed_val < 0:  
                errorMsg = []
                if self.buttonObj.pressed_val < 0: 
                    errorMsg.append('buttonObj') 
                raise Exception(f'(beam, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')
            return 
    
    def activate(self): 
        ''' activate as usual, and once it is active we can begin the button object listening '''
        interactableABC.activate(self)
        self.buttonObj.listen_for_event()
    
    def add_new_threshold_event(self):

        '''New [Press] was added to the buttonQ. Retrieve its value and append to the threshold event queue '''

        # append to event queue 
        self.threshold_event_queue.put(f'{self.name} beam broken {self.num_breaks} times')

        # Timestamp Break
        ts = self.event_manager.new_timestamp(f'{self.name}_beam_break', time = time.time())

        # Wait for Beam to Unbreak and Timestamp
        while self.isBroken: 
            ''' wait for beam to be unbroken '''
        t = time.time()
        if ts is not None: 
            self.event_manager.new_timestamp(f'{self.name}_beam_unbroken', time=t, duration = t - ts.time)

        # To avoid overloading a beam with threshold events, we can sleep here until a state change occurs 
        ''' while (self.threshold_attribute == self.threshold_goal_value) and self.active: 
            if len(self.threshold_event_queue.queue) == 0: # isEmpty!
                # control side "used" the added threshold event, so even if there hasn't been a state change, break out of while loop so we can add another threshold event 
                return  
            time.sleep(.5) '''
        return 

    
    # # Simulation Use Only # # 
    def simulate_break(self): 
        self.isBroken = True # describes the current state of the button object 
        self.buttonObj.num_pressed += 1
    def simulate_unbroken(self): 
        self.isBroken = False 
    def simulate_break_for_n_seconds(self, n): 
        if not self.isSimulation: 
            self.event_manager.print_to_terminal(f'(beam, simulate_break_for_n_seconds) {self.name} is not being simulated. Cannot complete function call')
        else:   
            # self.event_manager.print_to_terminal('simulating beam break')  
            self.isBroken = True 
            self.buttonObj.num_pressed += 1
            time.sleep(n)
            self.isBroken = False 
        return 
    def set_num_breaks(self, n): 
        ''' manually sets how many beam breaks the button object has recorded ( used in simulation ) '''
        self.buttonObj.num_pressed = n
    


class laser(interactableABC): 

    def __init__(self, ID, threshold_condition, hardware_specs, name, dutycycle_definitions, event_manager): 

         # Initialize the parent class
        super().__init__(threshold_condition, name, event_manager)

        self.ID = ID    

        self.pin_num = hardware_specs['pin_num']

        self.pi = self._setup_pigpio()

        # Dutycycle # 
        # Attributes for managing how the laser should distribute its time being On vs Off 
        self.dutycycle_pattern_definitions = dutycycle_definitions # breakdown of what each pattern is in its HIGH/LOW voltage format
        self.dutycycle_patterns = hardware_specs['dutycycle_patterns'] # patterns chained together
        

    
    #
    # Initializing Laser Object Methods
    #
    def _setup_pigpio(self): 
        ''' method for setting up access to the local pi's GPIO '''
        try: 
            return pigpio.pi()         
        except AttributeError as e: 
            # attribute error raised 
            control_log(f'(InteractableABC,py, Laser) {self}: simulating pigpio connection. ErrMssg: {e}')
            self.messagesReturnedFromSetup += f'simulating pigpio connection. '
            return None
        
    def validate_hardware_setup(self):  
        # if laser is being simulated, doesn't matter if the hardware has been setup or not if we are simulating the interactable     
        if not self.isSimulation: # laser is NOT simulated; ensure that we were able to access the pigpio library and access the laser's gpio pin 
            if self.pi is None: 
                raise Exception(f'(Laser, validate_hardware_setup) {self} failed to setup correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')
        return 
    
    def validate_dutycycle_patterns(self): 

        ''' ensures that the configuration file contains valid entries for the dutycycle fields '''

        # confirm that any pattern that is referenced in dutycycle_patterns can be found in the dutycycle_pattern_defintions 

        for (patternName, patternList) in self.dutycycle_patterns: 

            for dutycycle in patternList: 

                if dutycycle not in self.dutycycle_pattern_definitions: 

                    raise Exception(f'(Laser, validate_dutycycle_patterns) {self} contains an unknown reference within {patternName}, to the dutycycle: {dutycycle}')


        # confirm that a single mode isn't assigned a pattern chain more than once 

        # confirm that the referenced modes exist

        # 



    #
    # Simple Methods to turn laser On/Off 
    #
    def turn_on_and_wait(self, wait_time): 
        ''' turns the laser on and waits for specified number of seconds and then returns '''
        self.turn_on()
        time.sleep(wait_time)
        return 
    def turn_off_and_wait(self, wait_time): 
        ''' turns the laser off and waits for specified number of seconds and then returns '''
        self.turn_off() 
        time.sleep(wait_time)
        return 

    def turn_on(self): 
        ''' sets laser to high voltage '''
        if not self.isSimulation: self.pi.set_PWM_dutycycle(self.pin_num, 3.3)
    def turn_off(self): 
        ''' sets laser to low voltage '''
        if not self.isSimulation: self.pi.set_PWM_dutycycle(self.pin_num, 0)
    

    #
    # Dutycycle Pattern Execution 
    #
    def play_pattern(pattern): 
        ''' executes the passed in pattern. Pattern in a dictionary of strings. We can reference the pattern definitions '''
    



    






        
        



