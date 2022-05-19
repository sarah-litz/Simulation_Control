import unittest 
unittest.TestLoader.sortTestMethodsUsing = None
from Control.Classes.Map import Map

import os 
cwd = os.getcwd() # current working directory



class VoleTests(unittest.TestCase): 

    #
    # Initalize Map and Voles 
    #
    def test1_add_stuff(self): 
        chamber1 = self.map.new_chamber(1)
        chamber2 = self.map.new_chamber(2)
        chamber3 = self.map.new_chamber(3)
        
        edge12 = self.map.new_shared_edge(12,1,2)
        edge13 = self.map.new_shared_edge(13,1,3)

        
        edge12.new_component('water')
        edge12.new_component('wheel')
        edge12.new_component('couch')
        edge12.new_component('bed')

        print('---- EDGE 12 ------')
        for c in edge12: 
            print(c)
        
        chamber1.new_interactable('C1Food')
        chamber1.new_interactable('C1Water')
        
        self.sim.new_vole(1,1)
        self.sim.new_vole(2,1)
        self.sim.new_vole(3,2)

        self.sim.draw_chambers() 
        self.sim.draw_edges()
    
    def test2_move_validity_check(self): 

        print('Move Request Result: ',self.sim.get_vole(1).is_move_valid(destination=2))
        print('Move Request Result: ', self.sim.get_vole(3).is_move_valid(destination=3))
    
    def test3_attempt_move(self): 

        vole1 = self.sim.get_vole(1)
        vole1.attempt_move(2) 

    def est4_remove_vole(self): 
        print([i.tag for i in self.sim.voles])
        self.sim.remove_vole(tag=1)
        print([i.tag for i in self.sim.voles]) 
    
    def test5_random_voles(self): 
        vole4 = self.sim.new_vole(4,1)
        vole4.random_action() # LEAVING OFF HERE; don't think this function is entirely working
    

    # LEAVING OFF HERE! 
    def test6_add_action_probabilities(self): 

        c1food = self.sim.map.graph[1].get_interactable('C1Food')
        c1water = self.sim.map.graph[1].get_interactable('C1Water')
        e12 = self.sim.map.get_edge(12)
        e13 = self.sim.map.get_edge(13)

        chamber1 = self.sim.map.graph[1]
        chamber1.add_action_probabilities({'sleep':.1, c1food:.1, c1water:.1, e12:.1, e13:.1})
        # add probabilities to vole actions 
        # then update vole.random_action() so it first checks for probabilities. If action_probabilities==None, then call possible_actions() and choose randomly (using a uniform distribution)


def map_testing(): 
    
    map = Map(cwd+'/Control/Configurations')

    for id in map.graph.keys():

        chamber = map.graph[id] 

        print(chamber)


    edge = map.get_edge(12)

    print(edge)


    
    

if __name__ == '__main__': 

    # unittest.main()

    map_testing() 
    