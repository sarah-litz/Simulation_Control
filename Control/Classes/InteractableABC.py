"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 11/28/2022
Description: Class definition for interacting with hardware components. This module contains the abstract class definition, as well as the subclasses that are specific to a piece of hardware.
            Includes the following class definitions: 
                Inner classes of InteractableABC: button, servo 
                Child Classes that inherit from InteractableABC: lever, door, rfid, dispenser, buttonInteractable, beam 

Property of Donaldson Lab at the University of Colorado at Boulder
"""

# Standard Lib Imports 
import time, random, sys, queue, threading

# Third Party Imports 
from abc import abstractmethod, ABCMeta


# Local Imports 
from Logging.logging_specs import control_log

try: 
    import RPi.GPIO as GPIO 
except Exception as e: 
    print(e)
    GPIO = None
'''DELETE ME?? 
try: 
    import pigpio as pigpio
except Exception as e: 
    print(e)
    pigpio = None'''
try: 
    from adafruit_servokit import ServoKit
    SERVO_KIT = ServoKit(channels=16) 
except Exception as e: 
    print(e)
    SERVO_KIT = None

class interactableABC(metaclass = ABCMeta):

    def __init__(self, ID, threshold_condition, name, event_manager, type):

        ## Shared Among Interactables ## 
        self.event_manager = event_manager

        ## Object Information ## 
        self.ID = ID
        self.active = False # must activate an interactable to startup threads for tracking any vole interactions with the interactable
        self.name = name # name used is the one specified in the configuration files 
        self.type = type # string representation of type of interactable
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
        self.parents = [] # if an interactable is a dependent for another, then the object that it is a dependent for is placed in this list. 

        # Barrier / Autonomous: 
        self.barrier = None # Derived Classes must specify attribute: barrier (boolean) # set to True if the interactable acts like a barrier to a vole, meaning we require a vole interaction of somesort everytime a vole passes by this interactable. 
        self.autonomous = None # Derived Classes must specify attribute: autonomous (boolean) # set to True if it is not dependent on other interactables OR on vole interactions (i.e. this will be True for RFIDs and Beams )


        ## Servo and Button Objects ( Attibutes will be Overriden in the Derived Classes if they use a Button or a Servo )
        self.buttonObj = None 
        self.servoObj = None 

    def __str__(self): 
        return self.name

    # ---------------------------------------------------------------------------------------------------------------------------------------------------------
    #         InteractableABC Inner Classes Servo, PosServo(Servo), ContServo(Servo), and Button ( uses Rpi.GPIO and adafruit_servokit.ServoKit )
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------

    class Button:
        '''[Description] 
        Subclass of interactableABC, as buttons will never be a standalone object, they are always created to control a piece of hardware
        Will attempt importing GPIO library. If simulation, this will fail, and we will simulate the button. 
        Class is used for tracking Switch States of doors, if a lever is in a pressed state, etc. 
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
            """
            [summary] method for connecting with the GPIO library. 
            If the Interactable object that is using this Button obj is being simulated, then we default to simulating the Button as well. 
            If there is not a successful connection to the GPIO, then will automatically simulate the Button object and notify the parent. 
            Args: None 
            Returns: 
                (-1 | 0 | 1) : (0 or 1) value returned represents the "pressed" value of the button. If button is getting simulated, a -1 is returned.
            """
            if self.parent.isSimulation: 
                # control_log(f'(InteractableABC.py, Button) {self.parent.name}: simulating gpio connection.')
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
                # control_log(f'(InteractableABC.py, Button) {self.parent.name}: simulating gpio connection. ErrMssg: {e}')
                self.parent.messagesReturnedFromSetup += f' simulating GPIO button. '
                self.isSimulation = True
                return -1

        def run_in_thread(func): 
            ''' decorator function to run function on its own daemon thread '''
            def run(*k, **kw): 
                t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
                t.name = func.__name__
                t.start() 
                return t
            return run 

        @run_in_thread
        def listen_for_event(self, timeout=None, edge=None): # detects the current pin for the occurence of some event
            ''' 
            [summary] event detection for button. On event (aka a button press), incrememts the button's num_pressed value 
            ( note this does not update/check isPressed, as this is handled by the property function isPressed )
            Args: 
                timeout (int, optional): amount of time we should wait for event. If timeout is None, waits indefinetely for an event to occur. 
                edge (string, optional): arg to designate if we should look for event on the FALLING or RISING edge. 
            Returns: 
                None 
            '''
            def increment_presses(pin): 
                self.num_pressed += 1 
                self.buttonQ.put(f'press#{self.num_pressed}') # add press to parents buttonQ
                # print(f'(InteractableABC, Button.listen_for_event) {self.parent} Button Object was Pressed. num_pressed = {self.num_pressed}, buttonQ = {list(self.buttonQ.queue)}')
                # control_log(f'(InteractableABC, Button.listen_for_event) {self.parent} Button Object was Pressed. num_pressed = {self.num_pressed}')
                
            #
            # Sim Check; this function accesses gpio library. If button is being simulated, call the simulation version of this function and return. 
            #
            if self.isSimulation: 

                # If button is being simulated, then we care about changes to isPressed. If isPressed == True, then increment presses
                # print(f'(InteractableABC, Button, listen_for_event) Button for {self.parent} is being simulated. Simulated Button doesnt listen for event.')  
                # control_log(f'(InteractableABC, Button, listen_for_event) Button for {self.parent} is being simulated. Simulated Button doesnt listen for an event. {self.parent} will be listening for its own threshold event so will still pick up on simulated button presses.')  
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
            [summary] directly checks the gpio pin value to see if button is currently in a pressed state. If button is being simulated, this function should not have been called so throws an error. 
            Args: None 
            Returns: 
                (Boolean) : the current value of the button. (True if in a pressed state, False otherwise)
            '''
            if self.pressed_val < 0: 
                raise Exception('(InteractableABC.py, Button.isPressed) cannot access gpio input value for a Button that is being simulated.')  

            ''' if not a simulation, each time isPressed gets accessed, we want to recheck the GPIO input value. set isPressed as a method that gets called each time '''             
            
            if GPIO.input(self.pin_num) == self.pressed_val: 
                return True 
            else: 
                return False   
    
    class Servo: 
        '''[Description]
        Class for Managing Servos
        Inner class of interactableABC, as servos will never be a standalone object, they are always created in order to control a piece of hardware. 
        attempts importing of adafruit library. If simulation, this will fail, in which case we simulate the servo.
        '''
        
        def __init__(self, servo_specs, parentObj): 
            '''
            [summary] takes a positional ID on the adafruit board and the servo type, and returns a servo_kit object
            Args: 
                servo_specs (string) : Values necessary for connecting with the physical servo. Data is grabbed from the parent object's configuration file ( initially written in json format ). 
                parentObj (InteractableABC) : all classes that derive from InteractableABC have access to this class. The object that creates the servo gets passed in as parentObj.
            '''
            self.parent = parentObj
            self.pin_num = servo_specs['servo_pin']
            self.servo_type = servo_specs['servo_type']  
            self.isSimulation = False 
            self.servo = self.__set_servo()   
            
        def __set_servo(self): 
            """
            [summary] Sets up the initial connection with adafruit library for servo controls. 
            Args: None 
            Returns: 
                (SERVO_KIT.servo) : on a successful adafruit connection, returns a servo object provided by the adafruit_servokit.ServoKit library. On unsuccessful connection, returns False. 
            """
            if SERVO_KIT is None: 
                # simulating servo kit
                self.parent.messagesReturnedFromSetup += f' simulating servo.'
                return False 
            
            try: 
                if self.servo_type == 'positional':
                    return SERVO_KIT.servo[self.pin_num]
                elif self.servo_type == 'continuous':
                    return SERVO_KIT.continuous_servo[self.pin_num]
                else: 
                    raise KeyError(f'(InteractableABC.py, Servo) {self.parent.name}: servo type was passed as {self.servo_type}, must be either "positional" or "continuous"')

            except AttributeError as e: 
                # attribute error raised if we werent able to import SERVO_KIT and we try to access SERVO_KIT.servo 
                # control_log(f'(InteractableABC.py, Servo) {self.parent.name}: simulating servo connection. ErrMssg: {e}')
                # self.parent.messagesReturnedFromSetup += f' simulating servo. '
                self.isSimulation = True 
                return False
            
    class PosServo(Servo): 
        ''' [Description] positional servo 
        can control the angle that servo rotates to, but cannot control the speed that servo does so. 
        Provides a more accurate movement for smaller movements. Used in lever extension/retraction.
        '''
        def __init__(self, servo_specs, parentObj): 
            super().__init__(servo_specs, parentObj)
            self.angle = 0 # positional servo tracks current angle of the servo 
    
    class ContServo(Servo): 
        ''' [Description] continuous servo 
        can control the speed the servo rotates at, but has less control on final positioning that we rotate to. 
        Provides ability for bigger movements, but with less accuracy than PosServo. Used in door opening/closing. 
        '''
        def __init__(self, servo_specs, parentObj): 
            super().__init__(servo_specs, parentObj)
            self.throttle = 0 # continuous servo tracks speed that wheel turns at 

        
    # ------------------------------------------------------------------------------------------------------------
    #           InteractableABC Methods 
    # ------------------------------------------------------------------------------------------------------------
    def default_validation(self): 
        """[summary] validation checks that are required and not specific to an interactable """
        if self.barrier != True and self.barrier != False: 
            raise Exception(f'{self} must override the interactableABC attribute barrier with a boolean value.')
        if self.autonomous != True and self.autonomous != False: 
            raise Exception(f'{self} missing must override the interactableABC attribute autonomous with a boolean value.')

    def validate_hardware_setup(self): 
        """ 
        [summary] Validates that if any hardware is being used it was setup correctly. 
        If the interactable utilizes any of the Inner Classes in InteractableABC (Button or Servo), then it must validate that these objects were set up successfully. 
        Specifically, we must do this error check for every interactable that is NOT being simulated. 
            If the Button/Servos were not set up correctly, then we would run into errors once the experiment starts running. This attempts to catch those errors early. 
        However, if we are simulating the Interactable, it does not matter if button and servo were set up, in which case we can return from this validation check. 
        
        Args: None 
        Returns: None 
        """
        if self.isSimulation: 
            return 
        
        errorMsg = []
        if self.buttonObj != None: 
            ''' validate Button object setup '''
            if self.buttonObj.pressed_val < 0: 
                errorMsg.append('buttonObj')
        
        if self.servoObj != None: 
            ''' validate Servo object setup '''
            if self.servoObj.servo is False: 
                errorMsg.append('servoObj')

        if len(errorMsg) > 0:  
            raise Exception(f'{self} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')


        if not self.isSimulation: 
            # Interactable is not being simulated, but it does not have a function to validate its hardware components. Throw error 
            raise Exception(f'(InteractableABC, validate_hardware_setup) Must override this function with checks that ensure the hardware components are properly connected. Please add this to the class definition for {self.name}')

    def activate(self, initial_activation = True ):
        ''' 
        [summary] called at the start of each mode. Begins tracking for threshold events. 
                  On the very first mode, calls validate_hardware_setup. 
        Args: 
            initial_activation (Boolean, optional) : an interactable is repeatedly deactivated/reactivated throughout an experiment. 
                                                        On the very first activation at the start of an experiment, intial_activation is True. 
                                                        On all activations that follow, the mode class calls activation with initial_activation set to False. 
        Returns: None 
        '''

        if initial_activation: 
            try: 
                self.default_validation() #checks that required attributes were specified 
                self.validate_hardware_setup() # validate that this hardware was properly setup (e.g. the button and servos ) if interactable is not being simulated
            except Exception as e: print(e), sys.exit(0)

        # control_log(f"(InteractableABC.py, activate) {self.name} has been activated. starting contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
        
        self.threshold = False # "resets" the interactable's threshold value so it'll check for a new threshold occurence
        self.active = True 
        self.watch_for_threshold_event() # begins continuous thread for monitoring for a threshold event
        
    def deactivate(self): 
        """ 
        [summary] shuts off an interactable. called when a mode finishes running, or if an early interrupt occurs.
        Args: None 
        Returns: None 
        """
        self.threshold = False # "resets" the threshold value so it'll only check for a new threshold occurence in anything following its deactivation
        self.active = False 

        if hasattr(self, 'stop'): 
            self.stop() # stops things that could be left running

        self.event_manager.print_to_terminal(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")        
        # control_log(f"(InteractableABC.py, deactivate) {self.name} has been deactivated. Final contents of the threshold_event_queue are: {list(self.threshold_event_queue.queue)}")
    
    def reset(self): 
        '''[summary] empties the interactable's threshold event queue '''
        self.threshold_event_queue.queue.clear() # empty the threshold_event_queue
    
    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.name = func.__name__
            t.start() 
            return t
        return run 

    @abstractmethod
    def add_new_threshold_event(self): 
        """ 
        [summary] METHOD OVERRIDE REQUIRED 
        append relevant data to the threshold event queue. 
        This method needs to be overriden as different interactables require a slightly different 
            process to accurately format the data that gets placed on the event queue. 
        """
        # appends to the threshold event queue 
        raise Exception(f'must override add_new_threshold_event in class definition for {self.name}')
        self.threshold_event_queue.put()

    @run_in_thread
    def watch_for_threshold_event(self): 
        """
        [summary] 
            called upon activation, this method runs in its own thread while the interactable is active. 
            Using the threshold condition defined in the interactable's configurations, method repeatedly checks for if the threshold condition has been reached. 
            If any of the optional arguments were provided in the configuration file, will call the method designated by the optional args: check_threshold_with_fn and onThreshold_callback_fn
            Everytime threshold is reached, calls the interactable's add_new_threshold_event function. 
        Args: None 
        Returns: None 
        """

        while self.active: 

            # using the attribute/value pairing specified by the threshold_condition dictionary
            # if at any time the given attribute == value, append to the threshold_event_queue.

            threshold_attr_name = self.threshold_condition["attribute"]
            attribute = getattr(self, threshold_attr_name) # get object specified by the attribute name

            # # control_log(f"(InteractableABC.py, watch_for_threshold_event) {self.name}: Threshold Name: {threshold_attr_name}, Threshold Attribute Obj: {attribute}")
            
            # check for attributes that may have been added dynamically 
            if hasattr(self, 'check_threshold_with_fn'): # the attribute check_threshold_with_fn is pointing to a function that we need to execute 
                attribute = self.check_threshold_with_fn(self) # sets attribute value to reflect the value returned from the function call
            
            
            # Check for a Threshold Event by comparing the current threshold value with the goal value 
            if attribute == self.threshold_condition['goal_value']: # Threshold Event: interactable has met its threshold condition
                
                # control_log(f'(InteractableABC.py, watch_for_threshold_event) {self} Threshold Event Detected!')
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
                                # control_log(f' (InteractableABC, watch_for_threshold_event) calling onThreshold_callback_fn for {self.name}: parents:[ {parent_names}  ]  callbackfn: , {callbackfn} ')
                                callbackfn = eval(callbackfn)

                    self.event_manager.print_to_terminal(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")
                    # control_log(f"(InteractableABC.py, watch_for_threshold_event) Threshold Event for {self.name}. Event queue: {list(self.threshold_event_queue.queue)}")
                else: 
                    # not active, don't record the threshold event 
                    pass 
            else: 
                # no threshold event, ensure that threshold is False 
                self.threshold = False 

class template(interactableABC): 
    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager, type):
        # Initialize the parent class
        super().__init__(ID, threshold_condition, name, event_manager, type)
        self.barrier = False 
        self.autonomous = True

    def add_new_threshold_event(self):
        self.threshold_event_queue.put(f'{self}: Threshold True')
    
    def reset_attribute(self): 
        # resets threshold attr to its initial value 
        setattr(self, self.threshold_condition['attribute'], self.threshold_condition['initial_value']) 

class lever(interactableABC):
    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager, type):
        # Initialize the parent class
        super().__init__(ID, threshold_condition, name, event_manager, type)

        # Current Position Tracking # 
        self.isExtended = False 
        self.extended_angle = hardware_specs['servo_specs']['extended_angle']
        self.retracted_angle = hardware_specs['servo_specs']['retracted_angle']

        # Movement Controls # 
        self.servoObj = self.PosServo(servo_specs = hardware_specs['servo_specs'], parentObj = self) # positional servo to control extending/retracting lever; we can control by setting angles rather than speeds
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self) # button to recieve press signals thru changes in the gpio val

        ## Dependency Chain Values ## 
        self.barrier = False 
        self.autonomous = False

        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  
    
    def __str__(self): 
        return f'{self.name}(isExtended:{self.isExtended})'

    @property 
    def isPressed(self): 
        '''[summary] True if the button object is in a pressed state, false otherwise'''
        return self.buttonObj.isPressed 

    @property
    def num_pressed(self): 
        '''[summary] returns the current number of presses that button object has detected'''
        return self.buttonObj.num_pressed

    def reset_press_count(self): 
        ''' [summary] sets self.buttonObj.num_pressed to start from the initial value '''
        self.buttonObj.num_pressed = self.threshold_condition['initial_value'] 

    def set_press_count(self, count): 
        ''' [summary] sets self.buttonObj.num_pressed to specified value '''
        self.buttonObj.num_pressed = count 
        
    def activate(self, initial_activation = True ): 
        ''' [summary] activate lever as usual, and once it is active we can begin the button object listening for presses'''
        if self.active: 
            return # was already active. This is to avoid calling buttonObj.listen_for_event multiple times, as it is a threaded funciton.
        if self.isExtended: 
            interactableABC.activate(self, initial_activation)
            self.buttonObj.listen_for_event() # Threaded fn call 

    """def validate_hardware_setup(self):
        ''' [summary] if lever is not being simulated, ensures the lever's Button and Servo objects were set up '''
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return 
        else: 
            # not simulating door, check that the doors Movement Controllers (button and servo) have been properly setup 
            if self.buttonObj.pressed_val < 0 or self.servoObj.servo is False: 
                
                errorMsg = []
                # problem with both button and/or servo. figure out which have problems
                if self.buttonObj.pressed_val < 0: 
                    errorMsg.append('buttonObj')
                
                if self.servoObj.servo is False: 
                    errorMsg.append('servoObj')
                
                raise Exception(f'(Lever, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')
            return """

    def add_new_threshold_event(self): 
        """ [summary] grabs data that we care about for a lever threshold event, and adds it to the lever's threshold event queue """
        
        # appends to the lever's threshold event queue 
        event = f'{self}_{self.num_pressed}_Presses'

        # add threshold event to queue 
        self.threshold_event_queue.put(event)

        # add timestamp 
        self.event_manager.new_timestamp(event, time=time.time())

    #@threader
    def extend(self):
        """ [summary] extends the lever and activates (activation triggers the tracking for lever presses reaching its threshold value) """
        # control_log(f'(InteractableABC, Lever.extend) extending {self.name} ')
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
        """[summary] retracts lever and deactivates (deactivation stops the thread that is waiting for threshold events)"""
        # control_log(f'(InteractableABC, Lever.retract) retracting {self.name} ')

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
        
        # # HARDWARE THINGS
        else: 
            # set to the fully retracted angle 
            self.servoObj.servo.angle = self.retracted_angle
            self.isExtended = False 
            self.deactivate()
            return 

    def stop(self): 
        """[summary] hardware stop: retracts the lever and returns"""
        if self.isSimulation: return 
        else: 
            '''Logic here for shutting down hardware'''
            self.retract() 
            return 

class door(interactableABC):
    """[Description] This class is the unique door type class for interactable objects to be added to the Map configuration."""

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager, type):
        
        super().__init__(ID, threshold_condition, name, event_manager, type) # init the parent class 
                

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
        '''[summary] accesses Button object to check if the state switch is in a pressed state 
            Returns: (Boolean) : True if door is open, False otherwise. '''
        return self.buttonObj.isPressed 
    
    def sim_open(self): 
        '''[summary] simulates a door opening by changing attributes and starting countdown to designate when door starts and ends the opening process'''
        if self.isSimulation: 
            self.buttonObj.isPressed = True 
            self.event_manager.new_countdown(f'sim_{self.name}_open', self.open_timeout)
    
    def sim_close(self): 
        '''[summary] simulates a door closing by changing attributes and starting countdown to designate when door starts and ends the closing process '''
        if self.isSimulation: 
            self.event_manager.new_countdown(f'sim_{self.name}_close', self.close_timeout)
            self.buttonObj.isPressed = False 

    def override(self, open_or_close): 
        ''' 
        [summary] if override button gets pressed we call this function on the door 
        Args: 
            open_or_close (String) : string that designates which override button was pressed (i.e. the button to open the door or close the door)
        '''
        # immediately stop door movement 
        self.stop() 
        # reset door to stop execution of current door actions
        self.deactivate()
        self.activate() 
        if open_or_close == 'open': 
            self.open() 
        else: 
            self.close() 
        
    """def validate_hardware_setup(self):
        '''[summary] Checks that the door's Button and Servo objects were successfully setup when the door is not being simulated '''
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
                if self.servoObj.servo is False: 
                    errorMsg.append('servoObj')              
                raise Exception(f'(Door, validate_hardware_setup) {self.name} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')
            return """

    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.name = func.__name__
            t.start() 
            return t
        return run 

    def add_new_threshold_event(self): 
        """[summary] adds to the threshold_event_queue, then sleeps until the door's state changes to prevent an overload of threshold events while the door sits in this state. 
                will also break out of sleep if the event_queue is emptied (meaning a mode script 'used' the the threshold event in its logic, so we should check again to see what the door state is) """

        # appends to the threshold event queue 
        state = self.isOpen
        if self.isOpen: event = f'{self.name}_Open'
        else: event = f'{self.name}_Close'

        self.threshold_event_queue.put(event)
        self.event_manager.new_timestamp(event, time=time.time())

        # Uncomment to print detailed door threshold messages: 
        # self.event_manager.print_to_terminal(f"{self.name} Threshold:  {self.threshold} Threshold Condition: {self.threshold_condition}")
        # self.event_manager.print_to_terminal(f'(Door(InteractableABC.py, add_new_threshold_event) {self.name} event queue: {list(self.threshold_event_queue.queue)}')

        # To avoid overloading a door with threshold events, we can sleep here until a state change occurs 
        while self.isOpen == state and self.active: 
            if len(self.threshold_event_queue.queue) == 0: # isEmpty!
                # control side "used" the added threshold event, so even if there hasn't been a state change, break out of while loop so we can add another threshold event 
                return  
            time.sleep(.5)
        return 
               
    #@threader
    def close(self):
        """[summary] this function closes the doors fully"""

        # check if the door is already closed 
        if self.isOpen is False: 
            # door is already closed 
            # control_log('(Door(InteractableABC)) {self.name} was already Closed')
            self.event_manager.print_to_terminal(f'(Door(InteractableABC)) {self.name} was already Closed')
            return 

        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            # self.event_manager.print_to_terminal(f'(Door(InteractableABC), close()) {self.name} is being simulated. setting state to Closed and returning.')
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
        # control_log(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')
        self.event_manager.print_to_terminal(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')
        return 
        # raise Exception(f'(Door(InteractableABC), close() ) There was a problem closing {self.name}')

    #@threader
    def open(self):
        """[summary] this function opens the doors fully"""
        
        #  This Function Accesses Hardware => Perform Sim Check First
        if self.isSimulation: 
            # If door is being simulated, then rather than actually opening a door we can just set the state to True (representing an Open state)
            # self.event_manager.print_to_terminal(f'(Door(InteractableABC), open()) {self.name} is being simulated. Setting switch val to Open (True) and returning.')
            self.sim_open()
            return 
        
        # check if door is already open
        if self.isOpen is True: 
            # control_log('(Door(InteractableABC)) {self.name} was already Open')
            self.event_manager.print_to_terminal(f'(Door(InteractableABC)) {self.name} was already Open')
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
            # control_log(f'(Door(InteractableABC), open() ) There was a problem opening {self.name}')
            self.event_manager.print_to_terminal(f'(Door(InteractableABC), open() ) There was a problem opening {self.name}')
            
    def stop(self): 
        ''' [summary] HARDWARE STOP: sets servo speed to stop speed '''
        # Function Accesses Hardware! Perform Simulation Check 
        if self.isSimulation: return 
        self.servoObj.servo.throttle = self.stop_speed 
        return 

class rfid(interactableABC):
    """[Description] This class is the unique class for rfid readers/antennas that is an interactable object. 
    Note that this does not control the rfid readers like the other unique classes, it only deals with the handling of rfid data and its postion in the decision flow.
    Dynamically recieves a shaed_rfidQ attribute from ModeABC. shared_rfidQ is a queue shared among all of the rfid readers and the CAN Bus. 
    """

    def __init__(self, ID, threshold_condition, name, event_manager, type):

        super().__init__(ID, threshold_condition, name, event_manager, type)

        self.rfidQ = queue.Queue()
        self.ping_history = [] # exhaustive list of all the pings that have occurred, independent of phase/mode 

        self.barrier = False # if rfid doesnt reach threshold, it wont prevent a voles movement
        self.autonomous = True # operates independent of direct interaction with a vole or other interactales. This will ensure that vole interacts with rfids on every pass. 
        # (NOTE) do not call self.activate() from here, as the "check_for_threshold_fn", if present, gets dynamically added, and we need to ensure that this happens before we call watch_for_threshold_event()  

    """def validate_hardware_setup(self):
        ''' [summary] ensures that hardware was setup correctly '''
        if self.isSimulation: 
            # doesn't matter if the hardware has been setup or not if we are simulating the interactable
            return
        
        else: 
            # not simulating rfid. Check that CANBUS was connected correctly!! 
            #   
            #   COME BACK TO THIS!
            #  (TODO) setup RFID hardware things here! 
            #
            # print('rfid hardware doesnt exist yet!')
            return """

    def sim_ping(self, vole): 
        ''' [summary] simulates an RFID ping by adding to the shared rfidQ. Only called for a simulated rfid!!'''
        [self.shared_rfidQ.put((vole, self.ID, (time.time() + ( i - random.random() )))) for i in range (1,3)]

    class Ping: 
        ''' [Description] class for packaging rfid pings into pairs in order to represent the time that a vole first scanned an the rfid reader, 
        to the time that the vole left that rfid reader '''
        def __init__(self, ping1, ping2 = None, latency = None): 
            self.vole_tag = ping1[0] # the rfid chip id 
            self.rfid_id = ping1[1] # the rfid antenna id 
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
        '''
        [summary] called if a ping was added to rfidQ. 
        figures out if the ping is the first or second ping in the pair belonging to a Ping object 
        if it is the first ping, then creates a new Ping object. Otherwise, sets the new ping as the second ping for the existing Ping object. 
        Adds the Ping object to the threshold event queue
        '''
        try: 
            ping = self.rfidQ.get() 
            self.event_manager.print_to_terminal('PING: ', ping)
            # Check if the new ping is the 2nd ping ( a vole leaving an rfid reader ) or a first ( a vole arriving at the rfid reader )
            # Starting at the end of the end of the ping history list ( so the most recent pings ), look for a ping from this vole

            ## if a voletag is None, then we can assume that if the most recent ping has a voletag recorded and does NOT have a ping2 that pairs with it yet, we should pair this ping with it. 
            voletag = ping[0]
            newEntry = True 

            if not voletag:
                newEntry = False 
                # check the latest ping 
                

            for idx in range(len(self.ping_history)-1, -1, -1): # decrements by step sizes of -1 until the last position of -1 ( not inclusive, so all check at position 0 )
                p = self.ping_history[idx]
                if not voletag: 
                    if p.ping2 is None: 
                        # pairs with the most recent ping that does not have a ping2 and returns
                        p.set_ping2(ping)
                        # Record Timestamp for Ping 2 
                        self.event_manager.new_timestamp(f'rfid{p.rfid_id}_ping2_vole{p.vole_tag}', time=p.ping2[2], duration = p.latency)
                        return 

                elif p.vole_tag == voletag: 
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

            if not voletag: 
                # Error: Unknown Vole Signal Sent. Was Unable to Pair with a Previous Ping
                raise Exception(f'(RFID, add_new_threshold_event) Unknown Ping {ping} sent from CANBus. Not recording this ping.')

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
        ''' [summary] HARDWARE STOP: rfid antenna cannot shut itself down, as this is controlled by the CAN Bus '''
        return 
        if self.isSimulation: return 
        else: '''Logic here for shutting down hardware'''

class dispenser(interactableABC): 

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager, type): 

        # Initialize the parent class
        super().__init__(ID, threshold_condition, name, event_manager, type)

        # Movement Controls # 
        self.servoObj = self.PosServo(servo_specs = hardware_specs['servo_specs'], parentObj = self) # positional servo to control extending/retracting lever; we can control by setting angles rather than speeds
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self)  # Button/Sensor for detecting if pellet successfully dispensed # 

        ## Current Position/State Tracking ## 
        self.stop_speed = hardware_specs['servo_specs']['stop_speed']
        self.dispense_speed = hardware_specs['servo_specs']['dispense_speed']
        self.dispense_time = hardware_specs['dispense_time']
            
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
            t.name = func.__name__
            t.start() 
            return t
        return run    

    """def validate_hardware_setup(self): 
        '''[summary] ensures that dispener's Button and Servo object were successfully setup if the dispenser is not being simulated '''
        if self.isSimulation: 
            return 
        
        else: 
            # not simulating dispenser, check that the dispenser Movement Controllers (button and servo) have been properly setup 
            if self.buttonObj.pressed_val < 0 or self.servoObj.servo is None: 
                errorMsg = []
                # problem with both button and/or servo. figure out which have problems
                if self.buttonObj.pressed_val < 0: 
                    errorMsg.append('buttonObj')
                if self.servoObj.servo is False: 
                    errorMsg.append('servoObj')
                raise Exception(f'(Dispenser, validate_hardware_setup) {self} failed to setup {errorMsg} correctly. If you would like to be simulating any hardware components, please run the Simulation package instead, and ensure that simulation.json has {self} simulate set to True.')
            return """

    @property 
    def isPressed(self): 
        ''' [summary] accesses the gpio pin stored in the button object to check the pressed or unpressed state 
        Returns: (Boolean) : True represents a pressed state, meaning there is at least one Pellet present in the dispenser's trough '''
        return self.buttonObj.isPressed 
    
    @property
    def isPelletRetrieved(self): 
        '''[summary] checks if a pellet was retrieved from the trough 
        Returns (Boolean) : True if no pellet in trough, False if pellet in trough '''
        return not self.isPressed

    def sim_press(self): 
        '''[summary] Simulation Use Only: simulates a press by changing the simulated pin value to True '''
        if self.isSimulation: 
            self.buttonObj.isPressed = True
    
    def sim_unpress(self): 
        '''[summary] Simulation Use Only: simulates an unpress by changing the simulated pin value to False '''
        if self.isSimulation: 
            self.buttonObj.isPressed = False 
    
    def sim_dispense(self): 
        ''' [summary] Simulation Use Only: simulates a pellet dispense by calling sim_press '''
        self.event_manager.print_to_terminal('(InteractableABC, dispenser.sim_dispense()) (simulated) Pellet Dispensed! ')
        # control_log(f'(InteractableABC, dispenser.sim_dispense()) (simualted) Pellet Dispensed! setting the isPressed value to True to simulate that a pellet was dispensed.  Monitoring for a pellet retrieval from {self}!')
        self.sim_press() # simulates a dispense by setting button object to a pressed state 
        return 
    
    def sim_vole_retrieval(self): 
        ''' [summary] Simulation Use Only: simulates a pellet being retrieved from the trough by calling sim_unpress '''
        if self.isPelletRetrieved: 
            return # No Pellet in trough to retrieve!
        self.event_manager.print_to_terminal('(InteractableABC, dispenser.sim_vole_retrieval) Pellet Retrieved!')
        # control_log(f'(InteractableABC, dispenser.sim_vole_retrieval) Pellet Retrieved! Stopped monitoring for a pellet retrieval.')
        self.sim_unpress() # simulates a retrieval by setting button object to an unpressed state 
        return 

    def add_new_threshold_event(self):
        """
        [summary] checks that the monitor_for_retrieval has been set to True ( this occurs after a pellet is dispensed ) before proceding with adding a threshold event. 
        this precaution is taken because we only care about marking a threshold event when the trough goes from a pressed->unpressed state. If it simply begins in an unpressed state, 
        that is because the trough is initially empty in an experiment, but this should not be recorded as a vole retrieving a pellet. 
        """
        if self.monitor_for_retrieval: 
            self.threshold_event_queue.put(f'Pellet Retrieval')
            self.event_manager.new_timestamp(f'{self.name}_pellet_retrieved', time = time.time())
            self.monitor_for_retrieval = False # reset since we recorded a single pellet retrieval.
        else: 
            pass 
            # control_log(f'(InteratableABC.py, {self}, add_new_threshold_event) not monitoring for retrieval at the moment')
            # self.event_manager.print_to_terminal(f'(InteratableABC.py, {self}, add_new_threshold_event) not monitoring for retrieval at the moment')

        # To avoid overloading a food trough sensor with threshold events for when the food trough is empty, we can sleep here until a state change occurs 
        while not self.monitor_for_retrieval and self.active: 
            ''' wait for monitor for retrieval to get set to True! '''
            time.sleep(.5)
        
    def start(self): 
        '''[summary] turns the dispener's servo on in order to dispense a pellet '''
        self.servoObj.servo.throttle = self.dispense_speed 

    def stop(self): 
        ''' [summary] Hardware Stop: stops the dispener's servo movement '''
        if self.isSimulation: 
            return 
        self.servoObj.servo.throttle = self.stop_speed
    
    @run_in_thread
    def dispense(self): 
        ''' [summary] goes thru series of error checks and then procedes with dispensing a pellet. Runs on its own thread. '''
        # Edge Case: if there is already a pellet in the trough, we don't want to dispense again ( this likely means vole did not take pellet on a previous dispense )
        if self.isPressed is True:    

            self.event_manager.print_to_terminal('(InteractableABC, dispenser) Already a pellet in trough; previous pellet not retrieved')
            # control_log(f'(InteractableABC, dispenser.dispense()) Already a pellet in trough; Previous pellet not retrieved.')
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
                # control_log(f'(InteractableABC, Dispenser) {self}: Pellet Dispensed!')
                return  
            time.sleep(0.005) 
        
        # On Failure: Stop dispenser and notify user.
        self.stop()
        self.event_manager.print_to_terminal(f'(InteractableABC, Dispenser) {self}: A problem was encountered -- Pellet Dispensing Unsuccessful')
        # control_log(f'(InteractableABC, Dispenser) {self}: A problem was encountered -- Pellet Dispensing Unsuccessful')
        return 

class buttonInteractable(interactableABC):
    ''' [Description]
        **this class should not be confused with the Button class which connects with/operates the GPIO boolean pins** 
        buttonInteractable is used for the override buttons that control the open/closing of doors; if a door is in movement, these buttons override that movement immediately 
        this is pretty much just a Button object itself, except it must derive from interactableABC in order to have threshold checks that will trigger a threshold callback event ( to override a door movement )
    '''

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager, type ): 
         # Initialize the parent class
        super().__init__(ID, threshold_condition, name, event_manager, type)

        # Button # 
        self.buttonObj = self.Button(button_specs = hardware_specs['button_specs'], parentObj = self) # button to recieve press signals thru changes in the gpio val

        self.barrier = False 
        self.autonomous = False 

    def activate(self): 
        ''' [summary] activate button as usual, and once it is active we can begin the button object listening '''
        interactableABC.activate(self)
        self.buttonObj.listen_for_event()

    """def validate_hardware_setup(self):
        '''[summary] ensure's that the buttonInteractable's Button object was set up properly if the buttonInteractable is not being simulated '''
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

            return """ 
    
    def add_new_threshold_event(self):
        '''[summary] New <button press> was added to the buttonQ. Retrieve its value and append to the threshold event queue '''
        try: 
            press = self.buttonObj.buttonQ.get() 
        except queue.Empty as e: 
            raise Exception(f'(InteractableABC.py, add_new_threshold_event) Nothing in the buttonQ for {self.name}')

        # append to event queue 
        self.threshold_event_queue.put(press)
        self.event_manager.new_timestamp(f'{self.name}_pressed', time = time.time())

class beam(interactableABC): 

    def __init__(self, ID, threshold_condition, hardware_specs, name, event_manager, type): 

        super().__init__(ID, threshold_condition, name, event_manager, type)

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
        ''' [summary] return the current number of breaks that have been recorded'''
        # Button Object updates the num_pressed object 
        return self.buttonObj.num_pressed

    def reset_break_count(self): 
        ''' [summary] used as a callback function set by the beam config file '''
        self.buttonObj.num_pressed = self.threshold_condition['initial_value']

    """def validate_hardware_setup(self):
        ''' [summary] ensures that the beam's Button object has been set up properly if the beam is not being simulated '''
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
            return """
    
    def activate(self): 
        ''' [summary] activates as usual, and once it is active we can begin the button object listening '''
        interactableABC.activate(self)
        self.buttonObj.listen_for_event()
    
    def add_new_threshold_event(self):

        '''[summary] New <button press> was added to the buttonQ. Retrieve its value and append to the threshold event queue '''

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
        '''[summary] Simulation Use Only: simulates a beam break by setting beam state to broken'''
        self.isBroken = True # describes the current state of the button object 
        self.buttonObj.num_pressed += 1
    
    def simulate_unbroken(self): 
        '''[summary] Simulation Use Only: sets beam state to unbroken'''
        self.isBroken = False 
    
    def simulate_break_for_n_seconds(self, n): 
        '''[summary] Simulation Use Only: simulates a beam break for <n> number of seconds. (breaks beam, sleeps for <n> seconds, and unbreaks beam)
        Args:
            n (int) : number of seconds that the simulated beam will be in a broken state 
        '''
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
        ''' [summary] Simulation Use Only: manually sets how many beam breaks the button object has recorded '''
        self.buttonObj.num_pressed = n
    

    



    






        
        



