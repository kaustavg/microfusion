# microfusion
Programmatically draw 3D microfluidic chips in Fusion 360.

## Overview
This package is meant to convert python scripts into 3D microfluidic circuit designs in Fusion 360. 
We start by writing a script in python which specifies the positions and connections of elements in a microfluidic circuit. Specifying the circuit in the form of a script rather than a diagram makes it easy to make small changes to component values (such as resistances) and to copy and re-use circuit blocks multiple times in a design. This script utilizes functions and objects from this package to define the circuit components and their connections.

After creating the python script using the objects from this package, we run a special program from *within* Fusion 360, which loads our script and executes it, drawing everything on the stage. After the script has been run, the design can be further modified using the usual Fusion 360 GUI or the script itself can be tweaked and the design regenerated.

## Installation
1. Install Fusion 360 on your computer
2. 

## Annotated Example Script

## Objects
### Points
### Circuits
### Elements
