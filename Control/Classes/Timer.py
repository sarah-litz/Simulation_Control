"""
Description: Generic Timer Functions that provide the user with information on the current stage of an executing simulation and/or experiment.
"""
import time 
import sys
import threading
import queue 
import csv

PRINTING_MUTEX = threading.Lock()
COUNTDOWN_MUTEX = threading.Lock() # Lower Priority for Printing
TIMESTAMP_EVENT_MUTEX = threading.Lock() # Highest Priority for Printing


class EventManager: 

    ''' EventManager records events and the times that they happened at. 
        Provides the option to log messages, print to terminal, and/or record data in an output csv file '''
    
    def __init__(self, mode): 
        print('(Timer.py, EventManager.__init__) New Event Manager created for Control Mode:', type(mode))
        self.mode = mode 
        self.active = False 
        self.write_queue = queue.Queue() # items get added here to be written to output csv file 
        self.output_fp = self.mode.output_fp
        self.setup_output_file()
    
    def activate(self): 
        self.active = True 
        self.watch_write_queue()
    def deactivate(self): 
        self.active = False 
        self.finish() # Finishes writing any items left in the write_queue
    @property
    def modeActive(self): 
        return self.mode.active
    
    #
    # CSV Output File
    # 
    def setup_output_file(self): 
        with open(self.output_fp, 'w') as file:  # w - mode start at the BEGINNING of a file, so will overwrite any existing contents if the file already existed.
            spacer = []
            title = [f'Control Mode', str(self), type(self)]
            header = ['Round', 'Event', 'Interactable', 'Modal Time', 'Time', 'In Timeout?']
            csv_writer = csv.writer(file, delimiter = ',')
            csv_writer.writerow(spacer)
            csv_writer.writerow(title)
            csv_writer.writerow(header)
            print('done output file setup')
            return 


    def run_in_thread(func): 
        ''' decorator function to run function on its own daemon thread '''
        def run(*k, **kw): 
            t = threading.Thread(target = func, args = k, kwargs=kw, daemon=True)
            t.start() 
            return t
        return run 
    
    def finish(self): 
        '''finishes writing anything in the queue to the output csv file '''
        if len(self.write_queue.queue) > 0 and len(self.write_queue.queue) < 20: 
            # Finish Writing Output if it is left in queue 
            f = open(self.output_fp, 'a')
            csv_writer = csv.writer(f, delimiter=',')
            while len(self.write_queue.queue) > 0: 
                item = self.write_queue.get() 
                csv_writer.writerow([None, item.event, None, item.modal_time, item.time, item.inTimeout])
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
                    item_round = None 
                    item_event = item.event
                    item_interactable = None 
                    item_mode_time = item.modal_time
                    item_raw_time = item.time
                    item_in_timeout = item.inTimeout
                    csv_writer.writerow([item_round, item_event, item_interactable, item_mode_time, item_raw_time, item_in_timeout])
                    file.flush() 
            
            file.close() 
        return     
    
    #
    # Event Creation 
    # 
    def new_timestamp(self, event_description, time, print_to_screen = True ):
        # Streamlined way of marking an event and when it happened! Creates a timestamp and then sends to queues where it will be recorded in the csv file and possibly printed to the terminal 
        ts = self.Timestamp(event_description, mode_start_time=self.mode.startTime, inTimeout = self.mode.inTimeout, time = time)
        if print_to_screen: 
            ts.print_timestamp()
        # Add to Queue so timestamp is written to output csv file 
        self.write_queue.put(ts)
        return ts
    
    def new_countdown(self, event_description, duration, primary_countdown = False): 
        # creates a new Countdown object and adds to priority queue, where the event that will finish the soonest has the highest priority/will be printed to the screen.
        return self.Countdown(event_description, duration, mode = self.mode, primary_countdown = primary_countdown)


    
    class Timestamp:
        ''' Specific/Instantaneous Event Occurrence'''
        def __init__( self, event_description, mode_start_time, inTimeout, time = time.time()): 
            self.event = event_description
            self.time = time 
            self.modal_time = round(time - mode_start_time, 2)
            self.inTimeout = inTimeout
        def __str__(self): 
            return f'{self.event} : {self.modal_time}'
        def print_timestamp(self): 
            # Grab the timestamp mutex and print 
            TIMESTAMP_EVENT_MUTEX.acquire()
            print(self)
            TIMESTAMP_EVENT_MUTEX.release()


    class Countdown: 
        ''' event that occurs over a measurable period of time '''
        def __init__(self, event_description, duration, mode, start_time = None, primary_countdown = False): 
            self.event = event_description
            self.mode = mode
            self.primary_countdown = primary_countdown # Round Countdown; will pause for other countdowns
            if start_time is not None: self.start_time = start_time 
            else: self.start_time = time.time()
            self.end_time = self.start_time + duration 
            self.print_countdown() 

        @property
        def active(self): 
            return self.mode.active

        def print_countdown(self):    
            if self.primary_countdown: 
                # ROUND COUTNDOWN: sent to background if needed # 
                while self.end_time > time.time() and self.active: 
                    ## Primary countdown is usually the Round Countdown, and therefore has the lowest priority so will only print if all mutexes are free. 
                    if not COUNTDOWN_MUTEX.locked(): 
                        timeinterval = int(round(self.end_time,2) - round(time.time(),2)) # calculate time remaining
                        mins, secs = divmod(timeinterval, 60) # Format Time for displaying 
                        if not TIMESTAMP_EVENT_MUTEX.locked(): timer = '{:02d}:{:02d}'.format(mins, secs) 
                        sys.stdout.write(f'\r{timer} {self.event}   |')    
                    time.sleep(1)
                
                return 

            if not self.primary_countdown: 
                while self.end_time > time.time() and self.active:
                    if not COUNTDOWN_MUTEX.locked(): # gives terminal printing priority to specific events that need to print to terminal
                        COUNTDOWN_MUTEX.acquire()
                        while self.end_time > time.time() and self.active: 
                            timeinterval = int(self.end_time - time.time()) # calculate time remaining
                            mins, secs = divmod(timeinterval, 60) # Format Time for displaying 
                            timer = '{:02d}:{:02d}'.format(mins, secs) 
                            if not TIMESTAMP_EVENT_MUTEX.locked(): sys.stdout.write(f'\r{timer} {self.event}   |')
                        COUNTDOWN_MUTEX.release()  
                    time.sleep(1)
                
                return 
            
            if not self.active: 
                print('(Timer.py, print_countdown) Mode Inactivated before Countdown could finish.')
            
            return 
        


def countdown(): 
    print(' countdown does nothing  ')
'''def countdown(timeinterval, message, primary_message = False): 
    print("\r")
    
    if not primary_message: 
        if not COUNTDOWN_MUTEX.locked(): 
            COUNTDOWN_MUTEX.acquire() 
            while timeinterval:
                mins, secs = divmod(timeinterval, 60)
                timer = '{:02d}:{:02d}'.format(mins, secs)

                if not PRINTING_MUTEX.locked(): 
                    sys.stdout.write(f"\r{timer} {message}   | ")
                
                time.sleep(1)
                timeinterval -= 1 
            COUNTDOWN_MUTEX.release()
            print('\n')
            return 


    while timeinterval:
        mins, secs = divmod(timeinterval, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        
        if not primary_message: 
            if not PRINTING_MUTEX.locked() and not COUNTDOWN_MUTEX.locked(): 
                # get the countdown mutex and then print
                COUNTDOWN_MUTEX.acquire()
                sys.stdout.write(f"\r{timer} {message}   | ")
                COUNTDOWN_MUTEX.release()

        if not PRINTING_MUTEX.locked() and not COUNTDOWN_MUTEX.locked(): 
            # only print time remaining if the Printing Lock AND Countdown Lock is free
            sys.stdout.write(f"\r{timer} {message}   | ")

        time.sleep(1)
        timeinterval -= 1
    print('\n')'''



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