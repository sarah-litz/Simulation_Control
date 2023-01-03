import time 
import queue

from Control.Classes.InteractableABC import rfid

from ..Classes.Map import Map
from ..Classes.ModeABC import modeABC

from ..Logging.logging_specs import script_log, control_log


class WaitFiveSecondsBeforeRetractOrClose(modeABC): 
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)
    
    def __str__(self): 
        return '5 Sec Intervals b4 Close/Retract'
    
    def setup(self):

        setattr(self, 'door1', self.map.instantiated_interactables['door1'])
        setattr(self, 'lever_door1', self.map.instantiated_interactables['lever_door1'])

        door_list = [self.map.door1, self.map.door2, self.map.door3, self.map.door4]
        for d in door_list: 
            if d.isOpen: 
                d.close() # begin with all doors closed!

    def run(self):

        script_log(f'------------------------\n\n{self} is Running!')        

        while self.active: 


            if self.lever_door1.isExtended: 

                # wait 5 seconds and then retract the lever 

                time.sleep(5)

                self.lever_door1.retract() 

            if self.door1.isOpen: 

                # wait 5 seconds and reclose the door 

                time.sleep(10)
                
                self.door1.close() 


class IteratorBox(modeABC): 
    '''
    Description: 
        << operant map. Each time a lever gets pressed we increment the goal number of presses >>
    '''
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Iterator Box'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
        lever1 = self.map.instantiated_interactables['lever_door1']
        lever2 = self.map.instantiated_interactables['lever_door2']
        lever_food = self.map.instantiated_interactables['lever_food'] 
        lever_list = [lever1, lever2, lever_food]

        setattr(self, 'lever_list', lever_list)


          
    
    def run(self): 
        ''' when lever presses reaches threshold, increment required number of presses '''
        script_log(f'------------------------\n\n{self} is Running!')

        while self.active: 
            
            ## Wait for Any Lever Press or Timeout ## 
            for l in self.lever_list: 

                event = None 
                try: event = l.threshold_event_queue.get_nowait() # loops until something is added 
                except queue.Empty: pass 

                if event: 

                    # increment the required presses everytime a lever's threshold gets met! 
                    l.threshold_condition['goal_value'] += 1 
                    script_log(f'Incrementing Required Presses for {l} to {l.threshold_condition["goal_value"]} ')
        
        # When mode becomes inactive, reset the required presses back to the initial goal value of 1.
        script_log(f'Mode ended -> Resetting the required number of presses to 1 for all levers!') 
        for l in self.lever_list: 
            l.threshold_condition['goal_value'] = 1

        

            
class ReactiveBox(modeABC):
    """
    Description: 
        << TODO >>

        Logic is added that is dependent on threshold events occuring! 
        These are vole triggered events that we are defining for the box.  
        
        -> will only retract a lever once a vole has pressed it the required number of times.
        -> will only close a door once a vole has passed thru that door ( as picked up by the rfid readers )
    """
    def __init__(self, timeout, rounds, ITI, map, output_fp = None):
        super().__init__(timeout, rounds, ITI, map, output_fp)

    def __str__(self): 
        return 'Reactive Box'
    
    def setup(self): 
        ''' any tasks to setup before run() gets called '''
        pass 

    def run(self):

        script_log(f'------------------------ \n\n{self} is Running!')


        lever1 = self.map.instantiated_interactables['lever_door1']
        lever2 = self.map.instantiated_interactables['lever_door2']
        lever_food = self.map.instantiated_interactables['lever_food'] 
        
        lever_list = [lever1, lever2, lever_food]


        door1 = self.map.instantiated_interactables['door1']
        door2 = self.map.instantiated_interactables['door2']

        door_list = [door1, door2]


        rfid1 = self.map.instantiated_interactables['rfid1']
        rfid2 = self.map.instantiated_interactables['rfid2']
        rfid3 = self.map.instantiated_interactables['rfid3']
        rfid4 = self.map.instantiated_interactables['rfid4']

        rfid_list = [rfid1, rfid2, rfid3, rfid4]

        script_log('Extending All Levers!')
        
        for l in lever_list: 
            l.extend() 

        while self.active: 

            # Retract Lever if there is a threshold event! # 
            for l in lever_list: 
                
                if len(l.threshold_event_queue.queue) > 0: 

                    script_log(f'Retracting Lever! {l}.')
                    l.retract() 

                    lever_list.remove(l)
        
            
            for d in door_list: 
                    
                if d.isOpen: # a door is open!

                    # Wait for a vole to pass thru this door! ( perform rfid checks )

                    # grab the rfids that exist on the same edge as the current door. Check them both to see if they both are pinged, meaning a vole passed by them both
                    e = self.map.get_location_object(d) # gets the edge that the chamber is on 
                    doors_rfids = [] 
                    for c in e: 
                        if type(c) is self.map.Edge.Component: 
                            if type(c.interactable) is rfid: 
                                doors_rfids.append(c.interactable)
                    

                    vole_passed = False 
                    while self.active and vole_passed is False: 
                        for r in doors_rfids: 

                            # if ALL rfids have recorded at least one new ping, then we can assume the vole passed thru the door. 
                            if len(r.threshold_event_queue.queue) > 0: 

                                vole_passed = True 
                            
                            else: 

                                vole_passed = False 
                        
                        if vole_passed: 

                            # Vole passed through the door 
                            script_log(f'Vole passed through {d}! Closing {d}.')
                            print(f'Vole passed through {d}! Closing {d}.')

                            d.close() 

                            # retrieve the rfid pings 
                            for r in doors_rfids: 

                                r.threshold_event_queue.get_nowait() 

                    if not self.active: 

                        return # escape route so it doesn't finish looping thru the doors 





                    '''
                    # check which rfid recieved threshold event ( this also determines which door we are watching for the vole to pass through )
                    for r in rfid_list: 

                        if len(r.threshold_event_queue.queue) > 0: 
                            
                            
                            def retrieve_queue_contents(q):

                                # only remove from the queue if all three queues have an item that we can remove
                                # if len(q1.queue) > 0 and len(q2.queue) > 0 and len(q3.queue) > 0:
                                #    return ( q1.get_nowait(), q2.get_nowait(), q3.get_nowait() )
                                
                                # else: return  

                                try: print('FOUND: ', q.get_nowait())
                                except queue.Empty: raise Exception(f'Odd discrepency?? Queue contents: {list(q.queue)}')

                            # event! 
                            if r.ID < 3: 
                                # at Door 1 
                                if r.ID == 1: 

                                    # Vole passed rfid1. check rfid2 for a threshold event 
                                    if len(rfid2.threshold_event_queue.queue) > 0: 
                                        
                                        script_log(f'Vole passed through door1! Closing door1.')
                                        # Vole passed thru door1! Close Door! 
                                        door1.close() 

                                        # Remove the threshold events so we don't count it twice 
                                        retrieve_queue_contents(rfid1.threshold_event_queue) # , door1.threshold_event_queue, rfid2.threshold_event_queue)
                                        retrieve_queue_contents(door1.threshold_event_queue)
                                        retrieve_queue_contents(rfid2.threshold_event_queue)
                                        break; 

                                else: 
                                    # At Door 1 
                                    # Vole passed rfid2. Check rfid1 for a threshold event 
                                    if len(rfid1.threshold_event_queue.queue) > 0: 
                                        
                                        # Vole passed thru door1! Close Door! 
                                        door1.close() 

                                        # Remove the threshold events so we don't count it twice 
                                        retrieve_queue_contents(rfid2.threshold_event_queue)
                                        retrieve_queue_contents(door1.threshold_event_queue)
                                        retrieve_queue_contents(rfid1.threshold_event_queue)
                                        break; 
                            
                            else: # rfid ID is either 3 or 4, meaning we are watching for the vole to pass thru door2

                                # at Door 2 
                                if r.ID == 3: 

                                    # vole already passed rfid3, so check rfid4 for threshold event 
                                    if len(rfid4.threshold_event_queue.queue) > 0: 

                                        script_log(f'Vole passed through door2! Closing door2.')
                                        # Vole passed thru door1! Close Door! 
                                        door2.close() 

                                        # Remove the threshold events so we don't count it twice 
                                        retrieve_queue_contents(rfid3.threshold_event_queue)
                                        retrieve_queue_contents(door2.threshold_event_queue)
                                        retrieve_queue_contents(rfid4.threshold_event_queue)
                                        break; 
                                else: 

                                    # vole already passed rfid4, so check rfid3 for threshold event 
                                    if len(rfid3.threshold_event_queue.queue) > 0: 
                                        
                                        script_log(f'Vole passed through door2! Closing door2.')
                                        # Vole passed thru door1! Close Door! 
                                        door2.close() 

                                        # Remove the threshold events so we don't count it twice 
                                        retrieve_queue_contents(rfid4.threshold_event_queue)
                                        retrieve_queue_contents(door2.threshold_event_queue)
                                        retrieve_queue_contents(rfid3.threshold_event_queue)
                                        break; '''
                                

                                # LEAVING OFF HERE!!! # 


                    
            



