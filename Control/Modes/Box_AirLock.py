import time 
import queue
import threading

from Control.Classes.InteractableABC import rfid

from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from ..Logging.logging_specs import script_log, control_log

'''
Home Cage's Airlock Logic 

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
'''
        
class Chamber1Access(modeABC): 
    def __init__(self, timeout, rounds, ITI, map, output_fp=None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Start: Both Voles In Chamber 1'
    
    def setup(self): 
        ''' '''
        self.map.rfid1.threshold_event_queue.queue.clear()
        self.map.beam1_door1.threshold_event_queue.queue.clear()

        if not self.map.door1.isOpen: self.map.door1.open()
        if self.map.door2.isOpen: self.map.door2.close()
    
    def run(self): 
        ''' allow only one vole at a time to travel into chamber 2'''

        def num_pings_by_vole(rfid, vole_tag): 
            ''' sorts the rfid pings by which vole caused that ping '''
            count = 0
            for e in list(rfid.threshold_event_queue.queue): 
                if e.vole_tag == vole_tag: 
                    count += 1      
            return count

        def check_for_move(b, wait = False): 
            ''' returns when a vole crosses over b1 ( a beam object ) '''
            while self.active: 
                try: return b.threshold_event_queue.get_nowait()
                except queue.Empty: pass 
                if wait is False: 
                    return None # if wait is false then we do not loop because we just check once to see a move occurred 
            return None # mode deactivated, no move ever completed. 
        
       
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

                return Edge12Access(timeout=self.timeout, rounds=self.rounds, ITI = self.ITI, map = self.map, output_fp = self.output_fp)
                 
        return 


class Edge12Access(modeABC): 
    ''' voles were successfuly separated in the airlock movement mode
    this mode procedes with allowing a singular vole time in chamber2 and tracking its movement between edge12 and chamber2 '''
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Edge12Access'
    
    def setup(self): 
        ''' '''
    
    def run(self):

        # Open The Door to allow vole access into chamber2
        self.map.door2.open() 

        # wait for a beam break to occur to confirm that the vole travels into chamber2 
        def check_for_move(b, wait = False): 
            ''' returns when a vole crosses over b1 ( a beam object ) '''
            while self.active: 
                try: return b.threshold_event_queue.get_nowait()
                except queue.Empty: pass 
                if wait is False: 
                    return None # if wait is false then we do not loop because we just check once to see a move occurred 
            return None # mode deactivated, no move ever completed.        
        

        move = check_for_move(self.map.beam2_door2, wait=True)
        if move is None: 
            # experiment timed out
            print('Returning None')
            return 
        else: 
            print('Returning Mode: Chamber2Access')
            return Chamber2Access(timeout=self.timeout, rounds=self.rounds, ITI = self.ITI, map = self.map, output_fp = self.output_fp)
        
class Chamber2Access(modeABC): 
    def __init__(self, timeout, rounds, ITI, map, output_fp):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Voles in separate chambers'

    def setup(self):
        ''' reset rfid threshold event queue so we can only look for new ones (all pings will remain in the rfid's ping_history 
            reset beam threshold event queue so we can only look for new ones (all breaks will remain in the rfid's break_history ''' 
        self.map.rfid1.threshold_event_queue.queue.clear()
        self.map.beam1_door1.threshold_event_queue.queue.clear()

        if self.map.door1.isOpen: self.map.door1.close()
        if not self.map.door2.isOpen: self.map.door2.open()

    def run(self): 
        ''' 
        one vole in chamber 1 (food chamber) and one vole is either in edge 12 or chamber 2 (wheel chamber) 
        only allow vole movement from chamber 2 into chamber 1 to prevent both voles from being in chamber 2
        an rfid ping ( that is not followed by a beam2 break ) 
        '''

        def num_pings_by_vole(rfid, vole_tag): 
            ''' sorts the rfid pings by which vole caused that ping '''
            count = 0
            for e in list(rfid.threshold_event_queue.queue): 
                if e.vole_tag == vole_tag: 
                    count += 1      
            return count

        def check_for_move(b, wait = False): 
            ''' returns when a vole crosses over b ( a beam object or an rfid object ) '''
            while self.active: 
                try: return b.threshold_event_queue.get_nowait()
                except queue.Empty: pass 
                if wait is False: 
                    return None # if wait is false then we do not loop because we just check once to see a move occurred 
            return None # mode deactivated, no move ever completed. 


        # track rfid1 for pings. 
        #   If the ping comes from the vole that we know to be in chamber2/edge12, procede with closing door2 to allow the vole back into chamber1 
        #   If the ping comes from the vole that we thought was in chamber1, then close door2 and call the configuring mode to figure out where the voles are. 
        
        # figure out which vole should be in edge12/chamber2
        track_v = None 
        for v in self.map.voles: 
            if v.curr_loc != self.map.get_chamber(1): 
                if track_v is None: 
                    track_v = v
                else: 
                    raise Exception('More than one vole has its location set to either chamber2/edge12')
        if track_v is None: 
            raise Exception('All voles have their location set to chamber 1.')
        

        while self.active: 
            
            self.setup() # puts box back in this mode's start state 

            while self.active: 

                # begin checking beam2_door2 for breaks 
                move = check_for_move(self.map.beam2_door2, wait=True) # waits until a beam break occurs 
                if move is None: 
                    return 
                

                # vole triggered a new beam break; begin closing door2 to start airlock move process 
                self.map.door2.close() # close door2 behind the vole so it cannot access beam2 again 

                # Check for new beam2 breaks
                move = check_for_move(self.map.beam2_door2, wait=False)
                if move is not None: 
                    print('vole traveled back into chamber2 before door could close. open door 2 again')
                    break 
                    
                
                # begin checking rfid1 for pings 
                ping = check_for_move(self.map.rfid1, wait=True) # waits until a ping occurs
                if ping is None: 
                    return 
                if ping.vole_tag != track_v.tag: 
                    raise Exception('More than one vole has its location set to either chamber2/edge12')

                self.map.door1.open() # Open The Door to allow vole access into chamber2
                return Chamber1Access(timeout=self.timeout, rounds=self.rounds, ITI = self.ITI, map = self.map, output_fp = self.output_fp)




