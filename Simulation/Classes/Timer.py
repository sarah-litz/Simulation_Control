"""
Description: Generic Timer Functions that provide the user with information on the current stage of an executing simulation and/or experiment.
"""


import sys 
import time

from Control.Classes.Timer import PRINTING_MUTEX
from Control.Classes.Timer import COUNTDOWN_MUTEX
from Control.Classes.Timer import EventManager

class SimulationEventsManager(EventManager): 
    def __init__(self): 
        pass 
    


def countdown(timeinterval, message, secondary_message = False): 
    print("\r")
    print("\n")

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

            print('\n')
            return 

            
    while timeinterval:
        mins, secs = divmod(timeinterval, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)

        if secondary_message: 
            if not PRINTING_MUTEX.locked(): 
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
