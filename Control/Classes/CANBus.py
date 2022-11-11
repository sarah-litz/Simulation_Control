""" 
Date Created : 9/2/2021
Date Modified: 11/18/2021
Author: Ryan Cameron
Description: is the file that contains all of the necessary classes and functions to read data coming in through a CAN-bus line on the raspberry pi and send/store it for reference.
Property of Donaldson Lab, University of Colorado Boulder, PI Zoe Donaldson
http://www.zdonaldsonlab.com/
Code located at - 
"""

try: 
    import can 
    from can.interfaces.serial.serial_can import *
except Exception as e: 
    print(e)
    can = None 
try: 
    import serial 
except Exception as e: 
    print(e)
    serial = None 
import queue
import os
import threading


class CANBus: 

    def __init__(self, isserial=False): 
        
        try: self.config_canbus(isserial)
        except OSError as e: 
            print(e)
            print('Simu')

        self.shared_rfidQ = queue.Queue() # queue shared among the rfids 

    
    def config_canbus(self, isserial):

        print('initializing can bus')
        try: 
            os.system('sudo /sbin/ip link set can0 up type can bitrate 125000')
            print("CANBus init ok")
        except: 
            raise OSError('CANBus init failed')
        
        # Check if its a serial bus
        if isserial:
            print("Seting up serial bus...")
            self.bus = SerialBus(channel = "/dev/tty1")
            print("Serial bus created")
        else:
            print("Setting up CAN bus...")
            self.bus = can.interface.Bus(channel = "can0", bustype='socketcan') # Should auto configure the bus, make sure that this is interface.Bus NOT 
            print("Bus created")
        

        print('CANBus Created')