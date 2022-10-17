"""
Description: Generic Timer Functions that provide the user with information on the current stage of an executing simulation and/or experiment.
"""

import time 
import sys
import threading

PRINTING_MUTEX = threading.Lock()
COUNTDOWN_MUTEX = threading.Lock()


class TimestampManager: 
    pass 

class Latency: 
    pass 



def printer(messageQ): 
    while True: 
        if not PRINTING_MUTEX.locked(): 
            message = messageQ.get()
            print(message)
    

def countdown(timeinterval, message, secondary_message = False): 
    print("\r")
    
    if secondary_message: 
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
        
        if secondary_message: 
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
    print('\n')



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