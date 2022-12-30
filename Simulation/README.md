# Simulation Package

In order to run the simulation package, the Control Package directory must already exist with the modes and configurations that you want to run the simulation package on top of. (Reference "User Documentation: Control Package" for more information on setting up the control package.)

1. Create a Simulation Script
    - use Simulation/Scripts/Example.py as a template for creating a simulation script (copy and paste the file contents into a new file).
2. Make changes to Simulation/__main__.py 
    - pair the simulation script with a control mode.
    - follow along with the TODO's that are commented throughout Simulation's __main__ module. No changes should be made to code in the control directory.
3. Run the simulation package!
    - positioned just outside of the Simulation directory, run python3 -m Simulation from the terminal

## License

Property of Donaldson Lab at the University of Colorado at Boulder
