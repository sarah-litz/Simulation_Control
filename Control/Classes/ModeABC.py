"""
Authors: Ryan Cameron
Date Created: 1/24/2022
Date Modified: 1/24/2022
Description: This is the class file for the mode classes which contain all the information for the control software of the Homecage project to move between different logic flows. Each mode of operation has a different flow of logic, and this file contains the base class and any extra classes that are necessary to manage that.

Property of Donaldson Lab at the University of Colorado at Boulder
"""

# Imports
from multiprocessing import Event
from posixpath import split
import inspect
from Logging.logging_specs import control_log
import time
import threading
from threading import Thread
import queue 
import traceback
from .InteractableABC import rfid
from ..Classes.Timer import EventManager
import signal
import sys



# Classes
class modeABC:
    """This is the base class, each mode will be an obstantiation of this class.
    """

    def __init__(self, timeout = None, rounds = None, ITI = None, map = None, output_fp = None, startTime = time.time(), enterFuncs = None, exitFuncs = None, bypass = False, **kwargs):
        

        # Set the givens
        self.map     = map
        self.threads = None
        self.active  = False
        self.timeout = timeout
        self.rounds = rounds
        self.current_round = 0 
        self.ITI = ITI # inter-trial interval
        self.optional = kwargs
        self.inTimeout = False 
        self.output_fp = output_fp
        self.startTime = startTime
        self.event_manager = self.map.event_manager
        self.canbus = self.map.canbus


        # Shared rfidQ ( if no rfids present, this will just sit idle )
        self.shared_rfidQ = self.canbus.shared_rfidQ # if any of the rfids are pinged, a message will be added to this queue 
                                        # listener is activated in the modes activate function

        # Set variables as the enter and exit strings
        self.enterStrings = enterFuncs
        self.exitStrings  = exitFuncs

        # Simulation only 
        self.simulation_lock = threading.Lock() # locked while a simulation is actively running

        # Set Interrupt Handler for Clean Exit
        signal.signal(signal.SIGINT, self._interrupt_handler) # Ctrl-C
        signal.signal(signal.SIGTSTP, self._interrupt_handler) # Ctrl-Z


    def __str__(self): 
        return __name__


    def threader(func):
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 
    

    #
    # Called prior to running a Mode to ensure everything gets setup properly before a script starts running
    #

    def enter(self, initial_enter = True):
        try: 
            """This method runs when the mode is entered from another mode. Essentially it is the startup method. This differs from the __init__ method because it should not run when the object is created, rather it should run every time this mode of operation is started. 
            """

            if initial_enter: 

                #
                # Parent Mode: Set attributes and activate interactables before runnning mode. 
                # 

                # Set Start Time now that Mode has been entered and interactables activated 
                self.startTime = time.time()

                print(f'\nnew mode entered: {self}') # print to console 
                control_log(f'New Mode Entered: {self}')

                self.map.activate_interactables() # ensure that interactables are running for the new mode 

                rounds = self.rounds 

                # Startup Event Manager
                self.event_manager.activate(new_mode = self, initial_enter=True) # Start Tracking for Mode Events 
            
            else:
        
                #                         
                # This Mode was Created at Runtime  
                #    
                                     
                print(f'\nInner mode entered: {self}') # print to console 
                control_log(f'Inner Mode Entered: {self}')

                rounds = 1

                self.event_manager.activate(new_mode = self, initial_enter=False) # Start Tracking for Mode Events 
            

            #
            # Start Running Mode ( begins with Mode Setup )
            #
            self.event_manager.new_timestamp(event_description='Mode_Setup', time=time.time())
            
            # Mode Prep ( Run in Separate Thread so we can still catch any Interrupts )
            try: self.setup()
            except Exception as e: 
                print('(ModeABC.py, enter()) Exception Thrown in call to mode setup()): ', e)
            
            self.active = True # mark this mode as being active, triggering a simulation to start running, if a simulation exists
            self.rfidListener() # starts up listener that checks the shared_rfidQ ( if no rfids are present, returns immediately ) --> Relies on the mode being active! 

            for idx in range(1, rounds+1): # Initial mode of the round dictates how many rounds there will be. Any "inner" mode will run once each round. 

                if initial_enter: 
                    # Parent Mode iterates its index, and will dictate the round number for all child modes. 
                    self.current_round = idx 

                print(f'Mode {self} Starting Round {self.current_round}')
                control_log(f'Mode {self} Starting Round {self.current_round}')

                # Starting Mode Timeout and Running the Start() Method of the Mode Script!
                self.inTimeout = True 
                try: 
                    next_mode = self.run() # Run the Mode 
                    # self.event_manager.new_countdown(event_description = f"Mode_Timeout_Round_{self.current_round}", duration = self.timeout, primary_countdown = True)
                    self.exit() 
                except Exception as e: 
                    print(e)
                    print(f'{str(self)} encountered an error during its run() or exit() function. Returning now.')
                    return 

                if next_mode is not None: 
                    
                    # Create the next mode! 
                    # next_mode(map = self.map, output_fp = self.output_fp, startTime = self.startTime)
                    next_mode.startTime = self.startTime

                    print(f'MODE W/IN A MODE: Transferring Control to {str(next_mode)} for round {idx}')
                    next_mode.current_round = idx # to keep round numbers consistent, manually set the round number. ( Otherwise round will be set back to 1 in the output file )
                    next_mode.enter(initial_enter=False) # Recursively call enter() on next mode! 
            
                if initial_enter is False: 
                    # if Inner mode, only run once so break out of loop immediately. 
                    return  # Acts as a Base Case to Recursive Call! the top level call ( the initial mode entered ) will call final_exit. 

                # countdown for the specified timeout interval 
                # self.event_manager.new_countdown(event_description = f"Mode_Timeout_Round_{self.current_round}", duration = self.timeout, primary_countdown = True)
                
                self.event_manager.activate(new_mode = self, initial_enter=False)

                if idx < self.rounds: 
                    # Prep for next round ( does not include the final round )
                    self.new_round()

        
            if initial_enter: self.final_exit() # Deactivates Interactables 
            else: return # Acts as a Base Case to Recursive Call! the top level call ( the initial mode entered ) will call final_exit. 


        except Exception as e: 
            ''' if any errors/exceptions get raised, code will fall into this except statement where we can ensure nothing gets left running '''
            print(e) # printing exception message
            traceback.print_exc() # printing stack trace 
            self._except_handler()


    #
    # Exiting/Cleanup Functions
    #
    def pause_mode(self): 
        ''' called in between rounds of the same mode to pause mode execution '''
        self.inTimeout = False # should cause simulation to exit 
        self.simulation_lock.acquire() # Ensure Simulation Thread ( if it exists ) Cleanly Exits Before we continue 
        self.simulation_lock.release()

        # ensure that mode finishes 
    def new_round(self, mode_thread=None): 
        ''' called inbetween rounds of the same mode to pause for a inter trial interval '''
        self.inTimeout = False # should cause simulation to exit 
        self.active = False # should cause mode to exit 

        # Ensure Simulation Thread ( if it exists ) Cleanly Exits Before we continue 
        self.simulation_lock.acquire() 
        self.simulation_lock.release()

        # Ensure Mode Thread Cleanly Exits before we continue 
        if mode_thread is not None: mode_thread.join()

        ''' Inter-Trial Time Pauses Here '''
        self.event_manager.new_countdown(event_description = f'Inter-Trial Interval', duration = self.ITI, primary_countdown = True)

        self.inTimeout=True 
        self.active = True 

    def exit(self): 
        """This function is run when the mode exits and another mode begins. It closes down all the necessary threads and makes sure the next mode is setup and ready to go. 
        """
        print(f"{self} finished its Timeout Period and is now Exiting")
        self.inTimeout = False # Should cause simulation to exit 
        self.active = False 

        # Waits on Sim to reach clean exiting point # 
        self.simulation_lock.acquire() # if sim is running, wait for lock to ensure that it exits cleanly
        self.simulation_lock.release() # immediately release so next sim can use it 

        return 
    
    def final_exit(self): 
        
        print(f"{self} finished its Timeout Period and is now Exiting")
        self.inTimeout = False # Should cause simulation to exit 
        self.active = False 

        # Waits on Sim to reach clean exiting point # 
        self.simulation_lock.acquire() # if sim is running, wait for lock to ensure that it exits cleanly
        self.simulation_lock.release() # immediately release so next sim can use it 
        # Deactivate Interactables and Event Manager
        self.map.deactivate_interactables(clear_threshold_queue = True) # empties the interactable's threshold event queue and sets active = False
        self.event_manager.deactivate() # Stop Event Tracking for this Mode 

    def _interrupt_handler(self, signal, frame): 
        ''' catches interrupt, notifies threads, attempts a clean exit ''' 

        # In a different thread, handle shutting down the event manager. In the calling thread, continue execution to deactivate interactables. 
        event_interrupt_thread = threading.Thread(target=self.event_manager.interrupt, daemon=True)
        event_interrupt_thread.start()
        print(f'(ModeABC, _interrupt_handler) Deactivating Interactables')
        self.map.deactivate_interactables() # shuts off all of the hardware interactables
        event_interrupt_thread.join()
        sys.exit(0)

    def _except_handler(self): 
        ''' if exception/error occurs, attempts to shutoff any components before exiting '''
        print(f'(ModeABC, _except_handler) ')
        self.map.deactivate_interactables() # shuts off all the hardware interactables 
        sys.exit(0)

    #
    # rfid listener --> manages the queue that is shared amongst all RFID readers in a box  
    #
    @threader
    def rfidListener(self):
        """This method listens to the rfid queue and waits until something is added there. (running as daemon thread)
        """
        rfid_objects = {} # dictionary to store all of the rfid objects { tag : object } that were added to Map 

        # Get RFID Objects # 
        for n in self.map.instantiated_interactables.keys(): 
            
            i = self.map.instantiated_interactables[n]
            # check each interactable to see if it is of RFID type. Compile list of all rfid objects in the box. 

            if type(i) ==  rfid: # if interactable is an rfid object 
                
                rfid_objects[i.ID] =  i # add to dictionary to keep track of rfids 

                if not i.isSimulation: 
                    # ensure that canbus class will add messages to this rfid to the shared_rfidQ 
                    self.canbus.watch_RFIDs.append(i.ID)

                setattr(rfid_objects[i.ID], 'shared_rfidQ', self.shared_rfidQ)  # assign all rfid objects the same instance of shared_rfidQ

        # Exit if No RFIDs Present # 
        if len(rfid_objects.keys()) == 0: 
            # if there are no rfid objects, exit now
            return 
        
        self.canbus.listen() # Runs in its own DAEMON thread while ModeABC is active!

        # Distribute Pings to specific RFIDs 
        # Wait For Pings and Notify Specific RFIDs if Pinged # 
        while self.active: 

            # while mode is active, loop thru the shared_rfidQ to wait for pings. signal the corresponding rfid object as pings come in. 
            
            ping = None 
            while self.active and ping is None: 

                try: 
                    ping = self.shared_rfidQ.get(block = False) # waits to see if anything is added to Queue 
                except queue.Empty: 
                    ping = None 
                    time.sleep(.25)


            # Mode Deactivated #
            if not self.active: 
                # while loop was exited because self.active was set to False # 
                break 
            

            # Handle New Ping # 
            else: 
                # # ping added to shared queue. send to specific rfid object # # 

                # # we want to prioritize the passing of a ping from the shared_rfidQ to the individual rfidQ where the handling of a ping will happen # # 
                # In order to do this, before allowing an indivual rfid to pull from its rfidQ, we want to empty out the shared_rfidQ # 
                
                id = ping[1] # parse the ping information 

                rfid_interactable = rfid_objects[id] # retrieve the corresponding rfid object 

                rfid_interactable.rfidQ.put( (ping) ) 

                # # # the Map's Vole Location Tracking relies on the RFIDs for making any location updates # # # 
                # # Make Updates to Voles Location in the Map Class # # 
                self.map.update_vole_location( tag = ping[0], loc = self.map.get_location_object(rfid_interactable) )


        # Mode Inactivated 
        self.canbus.stop_listen()
        return 

   #
   # Running Modal Scripts 
   #   
    def setup(self): 
        ''' any tasks for setting up box before run() gets called '''
        raise NameError(f'{__name__} this function should be overriden')


    def threader(func):
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 

    @threader
    def countdown_to_exit(self): 
        self.event_manager.new_countdown(event_description = f"Mode_Timeout_Round_{self.current_round}", duration = self.timeout, primary_countdown = True)
        self.exit() # exit the mode upon timeout ending

    def run(self):
        """This is the main method that contains the logic for the specific mode. It should be overwritten for each specific mode class that inherits this one. Because of that, if this function is not overwritten it will raise an error on its default. 
        """
        # If not overwritten, this function will throw the following error
        raise NameError("This function must be overwritten with specific mode logic")

    #
    # Finding functions & subclasses ( Not in Use at the moment )
    # 
    def __find_func(self, functionName):
        """This function takes a given string and returns a function object that has the name of the given string. For example: If there was a class called "car" with a function called "get_miles" that returned the amount of miles the car has drive, this would look like __fund_func('car.get_miles'), and it would return the function object.
        Args:
            functionName (string): Name of subclass and method in form <objectName>.<methodName>
        Raises:
            NameError: Error is returned if no matching subclass and method is found
        Returns:
            object: actual function object of the subclass
        """
        # Find the object this function is from
        # Search for subclasses of modeABC
        subClasses = self.__find_subclasses(modeABC)

        # Break the functionName into subclass name and the function name
        nameList     = functionName.split('.')
        subClassName = nameList[0]
        methodName   = nameList[1]

        # Loop through the subclasses and find the right function
        for iSubClass in range(len(subClasses)):
            thisSub = subClasses[iSubClass]

            # Check to see if its the right subClass
            if thisSub.__name__ == "subClassName":
                # If its the right sublcass, return the function
                functionObject = getattr(thisSub, methodName)
                
                # Return the function once its found
                return functionObject
        
        # If its never found, rasie an error
        raise NameError("Error: subclass method not found")

    def __find_subclasses(self, module, classObj):
        """This searches through and finds all valid subclasses of the given class. This will include itself in the return.

        Args:
            module (python module): _description_
            classObj (class): _description_

        Returns:
            list: List of subclass objects
        """
        return [
            cls
                for name, cls in inspect.getmembers(module)
                    if inspect.isclass(cls) and issubclass(cls, classObj)
        ]

