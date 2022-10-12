import time 
import queue

from Control.Classes.InteractableABC import rfid

from ..Classes.Timer import countdown
from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from ..Logging.logging_specs import script_log, control_log



class AirLockDoorLogic(modeABC):
    """
    Description: 
        << TODO >>

        Logic creates a 2-door airlock system, with a single rfid sensor in the center to trigger the closing of the previous door and the opening of the next door. 

        -> begins with 2 voles in chamber 1, with door1 open, leading a vole into edge 12, and with door3 open, leading a vole into edge 13


        -> if a single rfid is pinged by more than one vole, do nothing 


        -> if a single rfid is pinged by a single vole, close the door that is now behind that vole, trapping the vole in between 2 doors 
        -> wait a second... if that same rfid is ever pinged by a vole that is different from the initial vole, start over and reopen the door that we just closed. 
        -> Otherwise, we will assume that there is only a single vole in between the 2 doors, and we should procede by opening the next door so the vole can walk into the empty chamber. 

    """

    def __init__(self, timeout, map):
        super().__init__(timeout, map)

    def __str__(self): 
        return 'Airlock Doors to Separate Voles'
    
    def setup(self): 

        ''' any tasks to setup before run() gets called '''

    def run(self):

        script_log(f'------------------------ \n\n{self} is Running!')

        rfid_list = [self.map.rfid1, self.map.rfid2]

        door_levers_list = [self.map.lever_door1, self.map.lever_door2, self.map.lever_door3, self.map.lever_door4]

        def set_to_start_state(): 

            '''puts doors back to their start state '''
            if not self.map.door1.isOpen: 
                self.map.door1.open() 
            if not self.map.door3.isOpen:
                self.map.door3.open() 

            if self.map.door2.isOpen:
                self.map.door2.close() 
            if self.map.door4.isOpen:
                self.map.door4.close() 


        def num_pings_by_vole(rfid, vole_tag): 

            # sorts the rfid pings by which vole caused that ping 
            count = 0
            for e in list(rfid.threshold_event_queue.queue): 

                if e.vole_tag == vole_tag: 

                    count += 1 
            
            return count


        def check_for_move(b1, b2, wait = False): 

            ''' returns when a vole crosses over b1 and b2 w/in 3 seconds '''
            while self.active: 
                
                beam1_event = None 
                beam2_event = None 

                # Check for beam1 break followed by a beam2 break ( i.e. a vole Move )
                try: beam1_event = b1.threshold_event_queue.get_nowait()
                except queue.Empty: pass 

                if beam1_event: 

                    # waits 3 seconds for a beam2 event to follow; this is using the assumption that door1_beam1 and door1_beam2 almost act as a single unit/sensor surrounding door1. 
                    # if beam2_event does not occur within the 3 seconds, we scrap both events and start over. 
                    try: 
                        beam2_event = b2.threshold_event_queue.get(timeout = 15)
                    except queue.Empty: 
                        pass  
                
                if beam2_event: 
                    # a beam1_event and beam2_event were detected. i.e. a vole moved thru the door. 
                    return (beam1_event, beam2_event) 
                
                if wait is False: 
                    return None # if wait is false then we do not loop because we just check once to see a move occurred 
            
            return None # mode deactivated, no move ever completed. 
        

        # Begin in Start State 
        set_to_start_state()

        # As soon as there is a singular Move detected ( where Move is defined as a cross over the door entry way, based on info from the ir beams ), 
        # Close the door. Then we will monitor the rfid reader to recieve information on which vole walked thru the door, and also to double check that in fact only one vole is in the "airlocked" area. 

        while self.active: 


            # Begin checking for movement thru doors ( using the beam breaks ) 

            # for each set of beams, check for a move ( make sure we check for bidirectional movement, so need to make 2 diff calls )

            move = check_for_move(self.map.beam1_door1, self.map.beam2_door1, wait = True ) # loops until a move is detected or until the mode because inactive 


            if move is None: 
                print('No move through door1 detected.')
                return # mode became inactive while we were waiting for a vole move to occur
            

            # Move has occurred; close door1 
            print(f'Movement Through Door 1 Detected {move}|| Closing Door 1 Now...')
            self.map.door1.close()
            

            # Now that door has closed, Recheck the beams for more movements thru door1  

            if check_for_move(self.map.beam1_door1, self.map.beam2_door1) is not None: 
                # another vole moved thru the door 
                print('Another vole passed by door1 before it could shut! Voles not separated.')
                return    
            if check_for_move(self.map.beam2_door1, self.map.beam1_door1) is not None: 
                print('The vole turned around and went back thru the door before it closed. Voles not separated')
                return 
            
            # Passed the Beam Recheck! 
            # Open the next door

            self.map.door2.open()

            # Begin checking for rfid1 for pings to figure out which vole walked thru the door! 

            while self.active: 
                
                ping = None 
                try: ping = self.map.rfid1.threshold_event_queue.get_nowait()
                except queue.Empty: pass 


                if ping is not None: 

                    # rfid ping detected. Figure out which vole it was caused by 
                    print(f'Vole #{ping.vole_tag} walked through door1!')
                    return 
                
            
            return 



