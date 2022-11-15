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
import asyncio 
import time

''' class for recieving data from RFIDs
'''

class CANBus: 

    def __init__(self, isserial=False): 
        
        try: 
            self.isSimulation = self.config_canbus(isserial)
        except OSError as e: 
            print(e)
            self.isSimulation = True # simulating CANBus

        self.shared_rfidQ = queue.Queue() # queue shared among the rfids 

        self.watch_RFIDs = [] # ModeABC adds any non-simulated rfids to this list so CANBus can perform quick cleaning and trash unimportant messages that it recieves

        self.active = True 
    
    class MessageListener(can.Listener): 
        def __init__(self, shared_rfidQ, watch_RFIDs): 
            super().__init__(self)

            self.shared_rfidQ = shared_rfidQ
            self.watch_RFIDs = watch_RFIDs

        
        def on_message_received(self,msg): 
            # registered as a listener. when a message is recieved, this fnctn gets called 

            #
            # FILTER MESSAGES HERE ( trash messages that are for an rfid we are not tracking )
            #
            if msg.arbitration_id not in self.watch_RFIDs: 

                # do nothing 
                return 

            # format for shared_rfidQ || Tuple: ( vole_id, rfid_id, timestamp )
            print('Raw Message: ', msg)
            print('Raw Data: ', msg.data)
            print('Hex Data: ', msg.data.hex()) 
            print('Decode Byte Array Data: ', msg.data.decode('utf-16'))
            print('Formatted Message: ', (msg.data.hex(), msg.arbitration_id, msg.timestamp), '\n')
            return 
            formatted_msg = (msg.data, msg.arbitration_id, msg.timestamp)
             
            # REFORMAT MESSAGES FOR THE SHARED_RFIDQ HERE 

            self.shared_rfidQ.put(formatted_msg)

            return 

    def config_canbus(self, isserial):

        if can is None or serial is None: 
            print('cannot setup CAN Bus without the can and serial module')
            return True 

        print('initializing can bus')
        try: 
            os.system('sudo /sbin/ip link set can0 up type can bitrate 125000')
            print("CANBus init ok")
        except: 
            raise OSError('CANBus init failed')
            return True 
        
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
        return False 
    

    def listen(self):
        """This function creates a listener on its own thread and listens for messages sent over the serial connection, it uses the can Notifier base class to listen. 
        """

        # Create notifier
        self.active = True 
        notiThread = threading.Thread(target=self.__listen)
        notiThread.start()
    
    def stop_listen(self): 
        self.active = False 

    def __listen(self):
        """Internal method for the listen method to call that actually has all the functionality and can be threaded.
        """
        # activated when a mode is activated 
        if not self.active: return 

        print("Listening...")

        # Create Notifier 
        listener = self.MessageListener(self.shared_rfidQ, self.watch_RFIDs)
        notifier = can.Notifier(bus=self.bus,listeners=[listener]) # listeners are the callback functions!

        while self.active: 
            # deactivated when a mode is deactivated
            time.sleep(0.5)

        notifier.stop() # cleanup 
