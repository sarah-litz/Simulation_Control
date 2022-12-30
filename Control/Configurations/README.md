
# Control Package Configurations

    Control/Configurations should contain only json files, where each file contains configurations for a specific interactable type or for a specific map layout.

*Control/Configurations/Examples directory contains an interactable and map configuration file that can be referenced when creating a new config file. For more information on how to decide what data to place in these files, reference the Control Package documentation.*

## Interactable Configurations

    Each interactable config file is specific to an interactable type. Each config file for a specific interactable type can contain an unlimited number of uniquely named and configured interactables of that same type. It is important that each receive a unique name so if an interactable is referenced in a map layout, there won't be any naming conflicts.

## Map Configurations

    Each unique map layout requires its own unique config file that defines it.
