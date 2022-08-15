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
            setattr(self, str(d), d)

        lever1 = self.map.instantiated_interactables['lever_door1']
        lever2 = self.map.instantiated_interactables['lever_door2']
        lever3 = self.map.instantiated_interactables['lever_door3']
        lever4 = self.map.instantiated_interactables['lever_door4']
        lever_food = self.map.instantiated_interactables['lever_food'] 
        lever_list = [lever1, lever2, lever3, lever4, lever_food]

        for l in lever_list: 
            setattr(self, str(l), l)
            l.deactivate() # we don't want levers to effect door states for this round.

        rfid1 = self.map.instantiated_interactables['rfid1']
        rfid2 = self.map.instantiated_interactables['rfid2']
        rfid_list = [rfid1, rfid2]

        for r in rfid_list: 
            setattr(self, str(r), r)


        # we want to begin with door1 and door3 open! 
        door1.open() 
        door3.open()    



    def run(self):

        script_log(f'------------------------ \n\n{self} is Running!')

        rfid_list = [self.rfid1, self.rfid2]

        

        def set_to_start_state(): 

            '''puts doors back to their start state '''
            self.door1.open() 
            self.door3.open() 

            self.door2.close() 
            self.door4.close() 


        def num_pings_by_vole(rfid, vole_tag): 

            # sorts the rfid pings by which vole caused that ping 
            count = 0
            for e in list(rfid.threshold_event_queue.queue): 

                if e[0][0] == vole_tag: 

                    count += 1 
            
            return count
        



        while self.active: 

            # for each rfid, tally up how many each vole has caused
            
            for r in rfid_list: 

                voles_in_edge = []
                for v in self.map.voles: 
                    
                    # tally up how many pings each vole has caused for a single rfid 

                    number = num_pings_by_vole(r, v.tag)

                    if number%2 != 0: 

                        voles_in_edge.append(v)
                

                if len(voles_in_edge) == 1: 

                    # only 1 vole has caused an odd number of pings, meaning that 1 vole is in the location of rfid <r> 
                    # close the door that is associated with <r> 
                    if r.ID == 1: 

                        # edge12 (doors 1 and 2)
                        if self.door1.isOpen: 

                            self.door1.close() 
                            next_door_to_open = self.door2
                        
                        if self.door2.isOpen: 

                            self.door2.close() 
                            next_door_to_open = self.door1
                    
                    else: 

                        # edge 13 (doors 3 and 4)
                        if self.door3.isOpen: 

                            self.door3.close() 
                            next_door_to_open = self.door4
                        
                        if self.door4.isOpen: 

                            self.door4.close() 
                            next_door_to_open = self.door3
                    
                    #
                    # Recheck this rfid that only one vole is in each edge by re-checking the number of rfid pings each vole has caused for this particular rfid
                    voles_in_edge = []
                    for v in self.map.voles: 
                        
                        # tally up how many pings each vole has caused for a single rfid 

                        number = num_pings_by_vole(r, v.tag)

                        if number%2 != 0: 

                            voles_in_edge.append(v)
                    
                    if len(voles_in_edge) != 1: 

                        # Failed the Recheck. Reset 
                        set_to_start_state() 
                    
                    else: 

                        # Passed the Recheck. Procede with opening the next door.
                        next_door_to_open.open()

                        # Return now that we have separated the voles. 
                        return 


                elif len(voles_in_edge): 

                    # Either No Voles are in the edge, or more than one vole are in the edge. Open the door to allow voles back into initial chamber. 

                    # Reset to the Start State where door1 and door3 are open, and door2&door4 are closed.
                    set_to_start_state()



                    # # At This Point, we have hopefully trapped a single vole in between 2 doors. 
                    # # # Double check this by looping once more 
                        
                        #
                        # LEAVING OFF HERE!!! 
                        #

                        ## In this case, where we know that the following door is shut, 
                        # an odd number of pings means that the vole is in the edge, 
                        # even number means the vole is in the chamber 

                        ## If a single vole has an odd number of pings, and every other vole has caused an even number of pings or 0 pings, 
                        # then we know that a single vole is isolated in the edge, and we should procede with shutting the door to trap the single vole between the 2 doors 



                    #   --> EVEN number of pings for a specific vole tells us that the vole is NOT in the edge, but rather back in the chamber. 
                    #   --> ODD number of pings for a specific vole tells us that the vole IS in the edge. 



'''
            if self.active: 

                # there was an rfid ping! 


                ping_event = pinged_rfid.threshold_event_queue.get_nowait() # includes 2 pings to represent the latency of the ping

                # Close Door immediately!! 

                if pinged_rfid.ID == 1: 

                    # the rfid that is sitting on Edge12, between door1 and door2. Close whichever of these doors is currently Open 
                    if self.door1.isOpen: 
                        
                        door = self.door1
                        self.door1.close() 

                    else: 
                        door = self.door2
                        self.door2.close() 


                elif r.ID == 2: 

                    # the rfid is sitting on Edge13, between door3 and door4. Close whichever of these doors is currently Open
                    if self.door3.isOpen: 
                        door = self.door3
                        self.door3.close() 
                    
                    else: 
                        door = self.door4
                        self.door4.close()


                # figure out which vole passed by the rfid 

                # EDGE CASE: check if more than one ping occurred! 
                #   --> either the vole walked out of airlock area, or the other vole walked in also

                voleID_event = ping_event[0][0] # grab the vole id 
                print('PING EVENT!!...', ping_event)
                print(pinged_rfid.ID)

'''

