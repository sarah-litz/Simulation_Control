import unittest 
unittest.TestLoader.sortTestMethodsUsing = None
from Map import Map
from Simulation import Simulation


#
# Methods for Removing Interactables from Edges and Chambers
#
class RemovalMethodTestCase(unittest.TestCase): 
    sim = Simulation(Map())
    map = sim.map 

    #
    # Adding Components so we can test removing them 
    #
    def test1_add_stuff(self): 
        chamber1 = self.map.new_chamber(1)
        chamber2 = self.map.new_chamber(2)
        chamber3 = self.map.new_chamber(3)
        edge12 = self.map.new_shared_edge(12,1,2)
        edge13 = self.map.new_shared_edge(13,1,3)
        try: self.map.new_shared_edge(13,1,3)
        except Exception as e: print('Exception Caught: ', e)
        edge12.new_component('water')
        edge12.new_component('wheel')
        edge12.new_component('couch')
        edge12.new_component('bed')
        chamber1.new_interactable('C1Food')
        self.sim.new_vole(1,1)
        self.sim.new_vole(2,1)
        self.sim.draw_chambers() 
        self.sim.draw_edges()
    
    def test2_remove_component(self): 
        # Removes Interactable on an Edge
        edge12 = self.map.get_edge(12)
        print(edge12)
        edge12.remove_component('couch')
        edge12.remove_component('water')
        edge12.remove_component('bed')
        print(edge12)
        
        edge13 = self.map.get_edge(13)
        print(edge13)
        try: edge13.remove_component('dne')
        except Exception as e : print("Exception Caught: ", e)
    
    def test3_remove_interactable(self): 
        # Removes Interactable from a Chamber 
        print('\n')
        chamber1 = self.map.graph[1]
        chamber1.remove_interactable('C1Food')
        self.sim.draw_chambers()
#
# Map and Simulation Testing 
#
class MapSimTestCase(unittest.TestCase): 

    sim = Simulation(Map())
    map = sim.map

    #
    # Adding Chambers, Edges, Components, and Interactables to Map Instance
    #
    def test1_new_chamber(self): 
        self.sim.map.new_chamber(1) 
        self.map.new_chamber(2)
        self.map.new_chamber(3)
        self.map.new_chamber(4)


    def test2_new_edge(self): 
        self.sim.map.new_shared_edge(12,1,2)
        self.sim.map.new_shared_edge(13,1,3)
        self.sim.map.new_shared_edge(14,1,4)
    

    def test3_new_component(self): 

        edge14 = self.sim.map.graph[1].connections[4] # grabs the shared edge w/ id 14 that goes from 1<->4

        # Add Components
        edge14.new_component('food')
        edge14.new_component('water')
        edge14.new_component('wheel')


        # Different Method of getting an Edge: 
        edge12 = self.sim.map.get_edge(12)
        edge12.new_component('wheel')    

    def test9a_new_component_after(self):
        edge14 = self.sim.map.get_edge(14)
        print(edge14.new_component_after('bed', 'water'))
        print(edge14.new_component_after('new head', None))
        
        # Error Check
        try: 
            result = edge14.new_component_after('error test', 'component that does not exist')
        except Exception as e:
            print("Exception Caught: ", e) 


    def test6_new_interactable(self): 
        # Adding Interactable directly to a Chamber (rather than an edge)
        chmbr1 = self.sim.map.graph[1]
        chmbr1.new_interactable('wheel2')

        chmbr2 = self.sim.map.graph[2]
        chmbr2.new_interactable('spinning wheel')    

    #
    # Adding Voles to Simulation Instance
    #
    def test7_new_vole(self): 
        self.sim.new_vole(101, 1)
        self.sim.new_vole(102, 1)
        self.sim.new_vole(103, 2)
        self.sim.new_vole(200012345432343, 4)


    #
    # Retrieving Map Information
    # 
    def test4_get_component(self): 
        edge12 = self.sim.map.get_edge(12)
        print('edge 12: ', edge12)
        print('Wheel Located? ', edge12.get_component('wheel') ) 
        print('Door located? ', edge12.get_component('door'))

        edge14 = self.sim.map.get_edge(14)
        print('edge 14: ', edge14)
        print('Water Located? ', edge14.get_component('water'))

        result = edge14.get_component('DNE')
        print('DNE Located? ', result)
    

    def test5_get_path(self): 
        print('(test5) Get Path from 3->4 returned:', self.sim.map.get_path(3, 4))

    #
    # Retrieving Simulation Information
    #

    def test8_get_vole(self): 
        vol101 = self.sim.get_vole(101)
        print("(test8) Get Vole 101 Returned: ", vol101.tag)
    
    def test9b_drawing_methods(self): 
        print('\n\n')
        self.sim.draw_chambers() 
        self.sim.draw_edges() 
        print('\n\n')
        self.sim.map.print_graph_info()

    

if __name__ == '__main__': 
    unittest.main()
