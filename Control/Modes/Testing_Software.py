""" 
HardwareTesting.py 
Tests that were used as hardware components were getting built up. Note that many of these test will not work now,
because they are calling functions that are now automated w/in the interactable. 
"""
import os, sys
import time
import threading 
import queue
import importlib
from tkinter import Button

from ..Classes.EventManager import EventManager
from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from ..Classes.InteractableABC import interactableABC
Button = interactableABC.Button # button class (nested w/in interactableABC)

from Logging.logging_specs import control_log 




#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------



class EventManagerTests(modeABC): 

    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'event manager tests '
    
    def setup(self): 
        '''any tasks to setup before run() gets called'''
    
    def run(self): 

        print(f'(SoftwareTesting.py, EventManagerTests, run())')
        time.sleep(3)
        print('\n')
        self.event_manager.new_countdown('Countdown', 10)
        self.event_manager.new_timestamp('Event_1', time=time.time())
        time.sleep(1)
        self.event_manager.new_timestamp('Event_2', time=time.time())
        print('All Done')
        return 
        



