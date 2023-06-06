# microfusion
Programmatically draw 3D microfluidic chips in Fusion 360.

## Overview
This package converts python scripts into 3D microfluidic circuit designs in Fusion 360. 

We start by writing a script in python which specifies the positions and connections of elements in a microfluidic circuit. Python objects from this package are used to define the circuit components and their connections in the script. Specifying the circuit in the form of a script rather than a diagram makes it easy to make small changes to component values (such as resistances) and to copy and re-use circuit blocks multiple times in a design. 

After creating the python script using the objects from this package, we run a special program from within Fusion 360, which loads our script and executes it, drawing everything on the stage. After the script has been run, the design can be further modified using the usual Fusion 360 GUI or the script itself can be tweaked and the design regenerated from scratch. It can then be exported as an STL file for 3D printing.

## Installation
1. Install Fusion 360 on your computer
2. Place this python package in a folder accessible to PYTHONPATH in your computer, just like any other python package you install. This allows the computer to find the new package when you write programs with it. If you want to add a new location to your computer's PYTHONPATH, you can also run the following python command:
```python
import sys
sys.path.append(r'C:\Your\Folder\Here\microfusion')
```
3. Place the file "RunMicrofusion.py" in the "Scripts" folder of your Fusion 360 installation. This is typically located in "C:\Users\YourUserNameHere\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\Scripts\". This is the program that will be run from within Fusion 360 to generate the design.

## Annotated Example Script
As an example we will be drawing a simple common-source amplifier consisting of one transistor, one resistor, and four ports. The entire script to generate this design is given below:
```python
import microfusion as mf

def main():
	design = mf.Design()
	cir = design.add_circuit()
  # Circuit Components
	tran1 = cir.M((0,0,0),anchor='S') # Transistor
	res1 = cir.R(tran1.D,50,anchor='L',rotation=-90) # Resistor of 20 kPs*s/uL

	sup1 = cir.P(tran1.S+(0,5000)) # Supply Port
	gnd1 = cir.P(res1.R-(0,5000)) # Ground Port
  out1 = cir.P((sup1.C%gnd1.C)+(6000,0),zspan) # Output Port
	inp1 = cir.P(tran1.G-(6000,0),zspan=[0,-cir.params['via_H']]) # Input Port
  

	cir.T([sup1.C,tran1.S])
	cir.T([res1.R,gnd1.C])
  
	cir.T([tran1.G1,inp1.C|tran1.G1,inp1.C],secs=mf.RectSect(W=250,H=-50))
  ```
  


## Objects
### Points
### Circuits
### Elements
