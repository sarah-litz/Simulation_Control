
"""
Authors: Sarah Litz, Ryan Cameron
Date Created: 1/24/2022
Date Modified: 12/1/2022
Description: EventManager contains the class definitions for EventManager 
            EventManager class recieves printing and output file write requests from different threads and executes these in a thread-safe way. 

Property of Donaldson Lab at the University of Colorado at Boulder
"""

# Standard Library Imports 
import time 
import sys
import threading
import queue 
import csv

# Global
PRINTING_MUTEX = threading.Lock()
COUNTDOWN_MUTEX = threading.Lock() # Lower Priority for Printing
TIMESTAMP_EVENT_MUTEX = threading.Lock() # Highest Priority for Printing

class EventManager: 

    ''' EventManager manages printing to the terminal and writing to the output csv file in a thread-safe fashion. Contains the inner classes Timestamp and Countdown '''
    
    def __init__(self, mode=None): 
        self.mode = mode 
        self.active = False 
        self.write_queue = queue.Queue() # items get added here to be written to output csv file 
        self.print_queue = queue.Queue()
        self.stop_messages = False # gets set to True to finish printing and exit thread. should only happen once
        self.watch_print_queue()      
        if mode is not None: 
            self.output_fp = self.mode.output_fp
            self.setup_output_file()
    
    def update_for_new_mode(self, mode, initial_enter = True ): 
        ''' map contains 1 instance of event manager that will be shared among all the modes. 
        this gets called when one mode ends and another starts running '''
        self.mode = mode
        if initial_enter: 
            # if multiple modes are chained together, then we want to keep writing to the same output file. 
            # we only perform the following actions if it is the first mode in a series of modes to run. 
            self.output_fp = mode.output_fp 
            self.setup_output_file()

    def activate(self, new_mode = None, initial_enter = True):
        if new_mode is not None: 
            self.update_for_new_mode(new_mode, initial_enter) 
        self.active = True 
        self.watch_write_queue()
        return 
    def deactivate(self): 
        self.active = False 
        self.mode = None
    def isActive(self): 
        return self.active 
    @property
    def modeActive(self): 
        return self.mode.active
    def interrupt(self): 
        ''' called if an interrupt signal is sent by user '''
        self.new_timestamp(event_description='Early_Interrupt_Caused_Exit', time=time.time())
        self.stop_messages = True 
        self.deactivate()
        self.finish() # finishes writing remaining events to the csv file 
        print('Messages remaining in the Print Queue:', list(self.print_queue.queue))

    #
    # CSV Output File
    # 
    def setup_output_file(self): 
        with open(self.output_fp, 'w+') as file:  
            # w  mode start at the BEGINNING of a file, so will overwrite any existing contents if the file already existed.
            # w+ mode will append to file. Creates file if it does not already exist. 
            spacer = []
            title = [f'Control Mode', str(self.mode), type(self.mode)]
            header = ['Round', 'Event', 'Modal Time', 'Time', 'Duration', 'In Timeout?', 'Mode Name']
            csv_writer = csv.writer(file, delimiter = ',')
            csv_writer.writerow(spacer)
            csv_writer.writerow(header)
            return 
    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.name = func.__name__
            t.start() 
            return t
        return run    
    def finish(self): 
        '''finishes writing anything in the queue to the output csv file '''
        ''' finishes printing anything in the print queue '''
        if len(self.write_queue.queue) > 0 and len(self.write_queue.queue) < 20: 
            # Finish Writing Output if it is left in queue 
            f = open(self.output_fp, 'a')
            csv_writer = csv.writer(f, delimiter=',')
            while len(self.write_queue.queue) > 0: 
                item = self.write_queue.get() 
                csv_writer.writerow([item.round, item.event, item.modal_time, item.time, item.duration, item.inTimeout, item.mode])
            f.close()
            return 
        if len(self.write_queue.queue) > 19: 
            print(f'Skipping the finish() writing to write_queue due to there being {len(self.write_queue.queue)} present in the queue. Q Contents: {list(self.write_queue.queue)}')
        return  
    @run_in_thread
    def watch_write_queue(self): 
        ''' manages writing to an output csv file so multiple threads will not interfere with one another '''
        with open(self.output_fp, 'a') as file: # a-mode appends to the file so will not overwrite existing contents of a file if file already existed
            csv_writer = csv.writer(file, delimiter=',')
            while self.active: 
                item = None 
                while self.active and item is None: 
                    try: item = self.write_queue.get_nowait()
                    except queue.Empty: pass 
                
                if item is not None: 
                    # write to csv file 
                    item_round = item.round 
                    item_event = item.event
                    item_mode_time = item.modal_time
                    item_raw_time = item.time
                    item_duration = item.duration
                    item_in_timeout = item.inTimeout
                    item_mode = item.mode
                    csv_writer.writerow([item_round, item_event, item_mode_time, item_raw_time, item_duration, item_in_timeout, item_mode])
                    file.flush() 
            
            file.close() 
        return     
    @run_in_thread
    def watch_print_queue(self): 
        ''' grabs from print queue and prints to terminal at a time where it won't conflict with other statements '''
        
        while not self.stop_messages: 
            item = None 
            while item is None: 
                try: item = self.print_queue.get_nowait()
                except queue.Empty: time.sleep(0.2)
                if self.stop_messages: 
                    print('EXITING THE WATCH_PRINT_QUEUE (1)')
                    return 

            # Item Recieved; Print Item
            while PRINTING_MUTEX.locked(): 
                ''' wait '''
                if self.stop_messages: 
                    print('EXITING THE WATCH PRINT QUEUE (2)')
                    return 
                time.sleep(0.5)
            
            if self.stop_messages: 
                print('EXITING THE WATCH PRINT QUEUE (3)')
                return 

            with TIMESTAMP_EVENT_MUTEX: 
                for i in item: 
                    print(i)
    
    #
    # Event Creation 
    # 
    def print_to_terminal(self, *message): 
        # sends to message instance 
        try: self.print_queue.put_nowait(message)
        except queue.Full as e: print('(TIMER.PY, PRINT_TO_TERMINAL EXCEPTION)', e), print(f'{message}')
    def new_timestamp(self, event_description, time, print_to_screen = True, duration = None ):
        # Streamlined way of marking an event and when it happened! Creates a timestamp and then sends to queues where it will be recorded in the csv file and possibly printed to the terminal 
        
        if self.mode is None: 
            print(f'Skipping timestamp creation for {event_description} because no mode is currently active.')
            return None

        ts = self.Timestamp(mode = str(self.mode), round_num=self.mode.current_round, event_description=event_description, mode_start_time=self.mode.startTime, inTimeout = self.mode.inTimeout, time = time, duration = duration)
        if print_to_screen: 
            ts.print_timestamp()
        # Add to Queue so timestamp is written to output csv file 
        self.write_queue.put(ts)
        return ts    
    def new_countdown(self, event_description, duration, primary_countdown = False, create_start_and_end_timestamps = True): 
        # creates a new Countdown object and adds to priority queue, where the event that will finish the soonest has the highest priority/will be printed to the screen.
        return self.Countdown(event_description, duration, mode = self.mode, new_timestamp = self.new_timestamp, checkEventManagerActive = self.isActive, start_time = None, primary_countdown = primary_countdown, create_timestamps=create_start_and_end_timestamps)
    class Timestamp:
        ''' Specific/Instantaneous Event Occurrence'''
        def __init__( self, mode, round_num, event_description, mode_start_time, inTimeout, time = time.time(), duration = None): 
            self.mode = mode
            self.round = round_num 
            self.event = event_description
            self.time = time 
            self.modal_time = round(time - mode_start_time, 2)
            self.inTimeout = inTimeout
            self.duration = duration
    
        def __str__(self): 
            return f'{self.event} : {self.modal_time}'
        
        def run_in_thread(func): 
            ''' decorator function to run function on its own daemon thread '''
            def run(*k, **kw): 
                t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
                t.name = func.__name__
                t.start() 
                return t
            return run 

        @run_in_thread
        def print_timestamp(self): 
            # wait to ensure that the printing mutex is not in use ( meaning a map is getting printed )
            while PRINTING_MUTEX.locked(): 
                ''' wait here until printing mutex is not in use'''
            
            # Grab the timestamp mutex and print 
            with TIMESTAMP_EVENT_MUTEX: 
                print(self)
            
            return            
    class Countdown: 
        ''' event that occurs over a measurable period of time '''
        def __init__(self, event_description, duration, mode, new_timestamp, checkEventManagerActive, start_time = None, primary_countdown = False, create_timestamps = True): 
            
            self.event = event_description
            # self.mode = mode
            self.primary_countdown = primary_countdown # Round Countdown; will pause for other countdowns
            self.checkEventManagerActive = checkEventManagerActive # Function Call that returns if the event manager is active or not.

            # Start and End Time # 
            if start_time is not None: self.start_time = start_time 
            else: self.start_time = time.time()
            self.end_time = self.start_time + duration 

            # Create Start and Finish Countdowns
            if create_timestamps: ts1 = new_timestamp(event_description = self.event+'_Start', time = time.time()) # Timestamp Countdown Start
            cd_completed = self.print_countdown() 
            if create_timestamps and cd_completed: 
                t = time.time()
                new_timestamp(event_description = self.event+'_Finish', time = t, duration = t - ts1.time) # Timestamp Countdown End

        @property
        def active(self): 
            return self.checkEventManagerActive()
        
        def print_countdown(self):    
            if not self.active: 
                print('(Timer.py, print_countdown) Skipping Countdown because event manager is not active.')
                return False     
            if self.primary_countdown: 
                # ROUND COUTNDOWN: sent to background if needed # 
                while self.end_time > time.time() and self.active: 
                    ## Primary countdown is usually the Round Countdown, and therefore has the lowest priority so will only print if all mutexes are free. 
                    if not COUNTDOWN_MUTEX.locked(): 
                        timeinterval = int(round(self.end_time,2) - round(time.time(),2)) # calculate time remaining
                        mins, secs = divmod(timeinterval, 60) # Format Time for displaying 
                        timer = '{:02d}:{:02d}'.format(mins, secs) 
                        if not TIMESTAMP_EVENT_MUTEX.locked() and not PRINTING_MUTEX.locked(): 
                            if self.active: 
                                sys.stdout.write(f'\r{timer} {self.event}   |')    
                    time.sleep(1)
                if not self.active: return False 
                else: return True

            if not self.primary_countdown: 
                while self.end_time > time.time() and self.active:
                    if not COUNTDOWN_MUTEX.locked(): # gives terminal printing priority to specific events that need to print to terminal
                        COUNTDOWN_MUTEX.acquire() # Aquires the Countdown Mutex, which will prevent the primary countdown from printing while this countdown prints. 
                        try: 
                            while self.end_time > time.time() and self.active: 
                                timeinterval = int(self.end_time - time.time()) # calculate time remaining
                                mins, secs = divmod(timeinterval, 60) # Format Time for displaying 
                                timer = '{:02d}:{:02d}'.format(mins, secs) 
                                if not TIMESTAMP_EVENT_MUTEX.locked() and not PRINTING_MUTEX.locked(): 
                                    if self.active: 
                                        sys.stdout.write(f'\r{timer} {self.event}   |')
                                time.sleep(1)
                        finally: 
                            COUNTDOWN_MUTEX.release()  
                            if not self.active: 
                                return False 
                            return True
            return False 

    #
    # Visuals
    # 
    def draw_table(data=[], cellwidth = 12): 
        for i, d in enumerate(data):
            line = '|'.join(str(x).ljust(cellwidth) for x in d)
            print(line)
            if i == 0:
                print('-' * len(line))
            ''' Example For Creating the Table: 
            draw_table( 
                data=[ 
                    ['row1col1', 'row1col2', 'row1col3'], 
                    ['row2col1', 'row2col2', 'row2col3'], 
                    ['row3col1', 'row3col2', 'row3col3']
                ]
            )'''

