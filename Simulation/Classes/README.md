# Classes

## Simulation

    Singleton parent class that is created to oversee that control modes and their paired simulation script begin and end in unison. 

## SimulationScriptABC

    SimulationScriptABC is an abstract base class for building logic scripts that will simulate vole movements by sending signals and creating interactable threshold events.

## SimVole

    The SimVole class is important to get to know, because the methods of this class  are used in order to simulate vole behavior in a Simulation script. SimVole provides a number of methods that when called, will simulate a vole making some movement within the provided map layout.