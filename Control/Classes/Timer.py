"""
Description: Generic Timer Functions that provide the user with information on the current stage of an executing simulation and/or experiment.
"""

import time 
import sys


def countdown(timeinterval, message): 
    print("\r")
    while timeinterval:
        mins, secs = divmod(timeinterval, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        sys.stdout.write(f"\r{timer} {message}   | ")
        time.sleep(1)
        timeinterval -= 1
    print('\n')

