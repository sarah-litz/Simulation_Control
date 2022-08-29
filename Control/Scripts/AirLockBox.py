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
        door1 = self.map.instantiated_interactables['door1']
        door2 = self.map.instantiated_interactables['door2']
        door3 = self.map.instantiated_interactables['door3']
        door4 = self.map.instantiated_interactables['door4']
        door_list = [door1, door2, door3, door4]

        for d in door_list: 
            setattr(self, d.name, d)

        lever1 = self.map.instantiated_interactables['lever_door1']
        lever2 = self.map.instantiated_interactables['lever_door2']
        lever3 = self.map.instantiated_interactables['lever_door3']
        lever4 = self.map.instantiated_interactables['lever_door4']
        lever_food = self.map.instantiated_interactables['lever_food'] 
        lever_list = [lever1, lever2, lever3, lever4, lever_food]

        for l in lever_list: 
            setattr(self, l.name, l)
            # l.deactivate() # we don't want levers to effect door states for this round.

        rfid1 = self.map.instantiated_interactables['rfid1']
        rfid2 = self.map.instantiated_interactables['rfid2']
        rfid_list = [rfid1, rfid2]

        for r in rfid_list: 
            setattr(self, r.name, r)


    def run(self):

        script_log(f'------------------------ \n\n{self} is Running!')

        rfid_list = [self.rfid1, self.rfid2]

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
        

        # Begin in Start State 
        set_to_start_state()


        while self.active: 

            # for each rfid, tally up how many each vole has caused
            
            for r in rfid_list: 
                
                if len(r.threshold_event_queue.queue) == 0: 

                    # No Pings Detected. Move onto next rfid
                    break 
                    
                else: 
                    
                    # Pings exist! 
                    # print([*(str(ele) for ele in r.threshold_event_queue.queue)]) # to print contents of the rfid's threshold event queue, uncomment this line! (kinda floods the terminal tho)

                    voles_in_edge = []
                    for v in self.map.voles: 
                        
                        # tally up how many pings each vole has caused for a single rfid 

                        number = num_pings_by_vole(r, v.tag)

                        if (number%2) != 0: # Odd Number of Pings => Vole in Edge

                            voles_in_edge.append(v)
                    

                    if len(voles_in_edge) == 1: 

                        # only 1 vole has caused an odd number of pings, meaning that 1 vole is in the location of rfid <r> 
                        # close the door that is associated with <r> 
                        if r.ID == 1: 

                            # edge12 (doors 1 and 2)
                            if self.map.door1.isOpen: 

                                self.map.door1.close() 
                                next_door_to_open = self.door2
                            
                            if self.door2.isOpen: 

                                self.map.door2.close() 
                                next_door_to_open = self.map.door1
                        
                        else: 

                            # edge 13 (doors 3 and 4)
                            if self.door3.isOpen: 

                                self.door3.close() 
                                next_door_to_open = self.door4
                            
                            if self.door4.isOpen: 

                                self.door4.close() 
                                next_door_to_open = self.door3
                        
                        # current issue: Recheck is begginning BEFORE the second PING (by vole2) is processed by the rfidListener in Mode.py, which grabs from the shared rfid Q and adds pings to the specific rfids threshold_event_queue
                        time.sleep(3) # Pause Before Recheck to ensure Accuracy 
                        # Recheck this rfid that only one vole is in each edge by re-checking the number of rfid pings each vole has caused for this particular rfid
                        print('R E C H E C K')
                        print('threshold event queue for the recheck:', list(r.threshold_event_queue.queue))
                        time.sleep(5)
                        voles_in_edge = []
                        for v in self.map.voles: 
                            
                            # tally up how many pings each vole has caused for a single rfid 

                            number = num_pings_by_vole(r, v.tag)

                            if number%2 != 0: 

                                voles_in_edge.append(v)
                        
                        if len(voles_in_edge) != 1: 

                            # Failed the Recheck. Reset 
                            print('FAILED THE RECHECK! MORE THAN ONE VOLE GOT INTO THE EDGE OR 0 VOLES IN EDGE. RESET.')
                            set_to_start_state() 
                        
                        else: 

                            # Passed the Recheck. Procede with opening the next door.
                            print(f'PASSED THE RECHECK! voles_in_edge: {[*(v.tag for v in voles_in_edge)]}')
                            next_door_to_open.open()

                            # Return now that we have separated the voles. 
                            return 


                    else: 

                        # Number of Voles in the Edge is Not Equal to 1 Vole! Leave Box as is until a single vole is isolated. 
                        # continue loopoing so we can recheck for when only 1 vole is in the edge.
                        
                        time.sleep(1)


