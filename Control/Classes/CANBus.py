""" 
Date Created : 9/2/2021
Date Modified: 12/1/2021
Author: Sarah Litz, Ryan Cameron
Description: This file contains the class definition for CANBus, the object containing the methods to read data coming in through a CAN-bus line on the raspberry pi and send/store it for reference.
Property of Donaldson Lab, University of Colorado Boulder, PI Zoe Donaldson
http://www.zdonaldsonlab.com/
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

class CANBus: 
    """ class for recieving data from RFIDs"""

    def __init__(self, isserial=False): 
        
        try: 
            self.isSimulation = self.config_canbus(isserial)
        except OSError as e: 
            print(e)
            self.isSimulation = True # simulating CANBus

        self.shared_rfidQ = queue.Queue() # queue shared among the rfids 

        self.watch_RFIDs = [] # ModeABC adds any non-simulated rfids to this list so CANBus can perform quick cleaning and trash unimportant messages that it recieves

        self.active = True 

    def config_canbus(self, isserial):
        """
        [summary] Attempts connecting to the CAN bus and creating a Bus wrapper (provided by python-can) that provides utilities for simple recieving and sending of data on the CAN Bus. 
                    If connection to the hardware fails, the CANBus will automatically be simulated.
        Args: 
            isserial (Boolean) : if True, sets up a serial method of communication, otherwise sets up a parallel method of communication (allowing for serveral bits at a time to be transmitted)
        """

        if can is None or serial is None: 
            # print('cannot setup CAN Bus without the can and serial module')
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
        print('CAN :', self.bus)
        attrs = vars(self.bus)
        print(', '.join("%s: %s" % item for item in attrs.items()))
        return False

    def listen(self):
        """ Called from the rfidListener method in ModeABC
        This function runs __listen() on its own thread which will handle incoming data recieved on the CAN Bus. 
        """
        # Creates notifier on its own thread and returns immediately so rfidListener can continue running
        self.active = True 
        notiThread = threading.Thread(target=self.__listen)
        notiThread.name = 'CANBus.__listen'
        notiThread.start()
    
    def stop_listen(self): 
        """ Causes the __listen thread to break out of its loop. Stops the Bus Notifier object so data will not be recieved. """
        self.active = False 

    def __listen(self):
        """Called by the listen() method. Runs on its own thread. Activated and Deactivated at the same time a Mode is activated/deactivated. 
        Creates a Listener object that waits for data sent on the CAN Bus and places incoming data on the shared_rfidQ. 
        """

        # activated when a mode is activated 
        if not self.active: return 

        if self.isSimulation: 
            if len(self.watch_RFIDs)>0: 
                    raise Exception(f'(CANBus.py, SimulatedMessageListener) Must simulate all RFIDs because can bus connection was not successful.')
            time.sleep(20)
            return 


        class MessageListener(can.Listener): 
            """ Inherits from python-can Listener Class. Overrides on_message_recieved method to define how incoming data is handled."""
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

                # convert msg data to a vole_id 


                # format for shared_rfidQ || Tuple: ( vole_id, rfid_id, timestamp )
                # print('CANBus Pinged: ', msg)
                # print('Hex Data: ', msg.data.hex()) 
                # print(int.from_bytes(msg.data, byteorder='big', signed=False))
                print('CANBus Pinged: ', (msg.data.hex(), msg.arbitration_id, msg.timestamp), '\n')
                formatted_msg = (msg.data.hex(), msg.arbitration_id, msg.timestamp)
                
                # REFORMAT MESSAGES FOR THE SHARED_RFIDQ HERE 
                self.shared_rfidQ.put(formatted_msg)
                return 

        print("Listening...")

        # Create Notifier 
        listener = MessageListener(self.shared_rfidQ, self.watch_RFIDs)
        notifier = can.Notifier(bus=self.bus,listeners=[listener]) # listeners are the callback functions!

        while self.active: 
            # deactivated when a mode is deactivated
            time.sleep(0.5)

        notifier.stop() # cleanup 

    


