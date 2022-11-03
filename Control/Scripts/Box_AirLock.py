import time 
import queue

from Control.Classes.InteractableABC import rfid

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

    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Airlock Doors to Separate Voles'
    
    def setup(self): 

        ''' any tasks to setup before run() gets called '''
        if not self.map.door1.isOpen: 
            self.map.door1.open() 
        if self.map.door3.isOpen:
            self.map.door3.close() 
        if self.map.door2.isOpen:
            self.map.door2.close() 
        if self.map.door4.isOpen:
            self.map.door4.close() 

    def run(self):

        script_log(f'------------------------ \n\n{self} is Running!')

        def num_pings_by_vole(rfid, vole_tag): 
            ''' sorts the rfid pings by which vole caused that ping '''
            count = 0
            for e in list(rfid.threshold_event_queue.queue): 
                if e.vole_tag == vole_tag: 
                    count += 1      
            return count

        def check_for_move(b1, wait = False): 
            ''' returns when a vole crosses over b1 ( a beam object ) '''
            while self.active: 
                try: return b1.threshold_event_queue.get_nowait()
                except queue.Empty: pass 
                if wait is False: 
                    return None # if wait is false then we do not loop because we just check once to see a move occurred 
            return None # mode deactivated, no move ever completed. 
        
        def close_door_and_check_beam(beam, door): 
            ''' performs another beam check, closes the door, and performs another beam check to verify that voles are separate'''

        # List beams in order that we want to check them when the function executes
        beam1 = self.map.beam1_door1 # Door that starts open that we will close 
        beam2 = self.map.beam2_door2 # Door that starts closed that we will open 
        beam_checks = [ beam1, beam2 ]
        beam_idx = 0 

        # As soon as there is a singular Move detected, close the door. 
        # Then we will monitor the rfid reader to recieve information on which vole walked thru the door, and also to double check that in fact only one vole is in the "airlocked" area. 
        
        while self.active: 

            separated = False 
            
            # ensure box is put back in its start state 
            self.setup()

            while self.active and not separated: 


                if check_for_move(beam_checks[beam_idx],  wait = True ) is not None: # loops until a singular beam break occurs 
                    separated = True 
                else:  
                    print(f'No move through {beam_checks[beam_idx]} detected. Mode is now inactive.')
                    return # mode became inactive while we were waiting for a vole move to occur
                

                # Move has occurred; close door1 
                time.sleep(0.5) # Pause before door close to give vole a chance to finish moving thru... 
                print(f'Movement Through Door 1 Detected || Closing Door 1 Now...')
                self.map.door1.close() # Closing Door


                # Beam Recheck 
                if check_for_move(beam_checks[beam_idx]) is not None:  # Now that door has closed, Recheck the beams for more movements thru door1 again 
                    # another vole moved thru the door 
                    print('Another beam break detected! Voles not separated.')
                    separated = False    
                    break 

                # Pause to give vole(s) a chance to trigger RFID ...
                time.sleep(2)


                # RFID Checks
                voles_in_edge = []
                for v in self.map.voles: 

                    n = num_pings_by_vole(self.map.rfid1, v.tag)

                    if n > 0: 

                        voles_in_edge.append(v)

                if len(voles_in_edge) > 1: 

                    # More than one vole detected in the edge. 
                    print(f'More than one Vole detected by {self.map.rfid1}: {[*(str(v) for v in voles_in_edge)]}')
                    separated = False 
                    break  
                
                elif len(voles_in_edge) == 0: 

                    # rfid does not detect a vole in the edge 
                    print(f'no voles detected on the edge with {self.map.rfid1}')
                    separated = False 
                    break  
            
            else: 

                # exactly 1 vole on the edge! ( Goal Check )

                print(f'Successfully Separated Voles! Vole in Edge: {[*(str(v) for v in voles_in_edge)]}')
                self.map.draw_map()

                # Open The Next Door 
                self.map.door2.open() 

                return


        return 



