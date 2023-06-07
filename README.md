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
	trace1 = cir.T([tran1.D,tran1.D+(0,-500)]) # Short trace to resistor
	res1 = cir.R(trace1.P2,50,anchor='L',rotation=-90) # Resistor of 50 kPa*s/uL
	# Ports
	sup1 = cir.P(tran1.S+(0,5000)) # Supply Port
	gnd1 = cir.P(res1.R+(0,-5000)) # Ground Port
	out1 = cir.P((sup1.C%gnd1.C)+(6000,1000)) # Output Port
	inp1 = cir.P(tran1.G1+(-6000,0),zspan=[0,-cir.params['via_H']]) # Input Port
	# Traces
	cir.T([sup1.C,tran1.S])
	cir.T([res1.R,gnd1.C])
	cir.T([tran1.G1,inp1.C],secs=mf.RecSec(W=250,H=-50))
	cir.T([tran1.D+(0,-250),tran1.D+(1000,-250),out1.C],trace_R=100)
  ```
  
To run this script in Fusion 360, make sure that RunMicrofusion.py is correctly pointing to our script file. Then in Fusion 360 we navigate to Utilities > Add-Ins > Scripts and Add-Ins > RunMicrofusion.py. The drawing process should be done in a few seconds.

We now explain each line in the above example script.

```python
import microfusion as mf

def main():
	design = mf.Design()
	cir = design.add_circuit()
```
This imports microfusion and defines the function that RunMicrofusion.py will run (which must be called "main").

We start by creating a new Design object, for which you should probably have only one per file. The Design object can hold multiple circuits. You can set various default drawing parameters here (like drawing scale, trace widths, and even liquid viscosity used to calculate resistances), and these default parameters will automatically pass down to all daughter Circuits objects drawn in this Design object. For a list of these parameters, please see the end of this document.

In this Design object, we then create a new Circuit object. This is another chance to set default parameters for the drawing the circuit, and these default parameters will pass down to all daughter circuit elements that you draw within this circuit but will not affect other Circuit objects in the Design. This is useful if you want to try two versions of the same circuit, perhaps one with rounded channels and one with rectangular channels, both on the same Design. Each Circuit object will end up as a unique "Component" in Fusion 360.

```python
	# Circuit Components
	tran1 = cir.M((0,0,0),anchor='S') # Transistor
	trace1 = cir.T([tran1.D,tran1.D+(0,-500)]) # Short trace to resistor
	res1 = cir.R(trace1.P2,50,anchor='L',rotation=-90) # Resistor of 50 kPa*s/uL
```
We start by adding a transistor to our circuit using the M function. Here we specify that the transistor is drawn such that the source terminal (S) is located at the origin. Other terminals (D, G1, G2) could just as easily be specified as the anchor point. We also name this transistor object 'tran1'. Here we drew this transistor with all the default settings for length, width, height, etc. but you could easily overwrite these defaults for this particular transistor by specifying keyword arguments.

Next we draw a short trace starting at the drain of the tranistor and extending 500um down. The T function takes in a list of any number of Points in 3D space and connects them all up with a smooth trace. Note that these points can be plain tuples (as we used to define the position of the transistor) or we can use the microfusion Point object which has some useful features.
The first point in our trace is specified as the drain terminal of the transistor we made already (tran1.D). This way, if we move or modify the transistor, the trace moves along with it automatically. Internally, this first point is represented not as a tuple, but as a microfusion Point object. This means we can do intuitive operations on this point, like shifting it by 500um down by simply "adding" a tuple to it, which we have demonstrated here. Note that you can't do this with native python tuples.

We then draw a resistor connected to the endpoint of the trace we just drew (trace1.P2). We specify that the resistance should be 50 kPa s/ul, and the computer will automatically size and draw a serpentine channel to meet this desired value. Similar to the transistor, we specify that the left side of the resistor (L) is the anchor point for drawing the component. Here we also specify an optional drawing parameter, rotation, using a keyword argument.

```python
	# Ports
	sup1 = cir.P(tran1.S+(0,5000)) # Supply Port
	gnd1 = cir.P(res1.R+(0,-5000)) # Ground Port
```
Like before, we are just adding new circuit components by specifying their position relative to existing Points in the circuit. Here we see the usefullness of using microfusion Points, since we can easily add tuples to move the points around. These ports will automatically generate a barb head facing upwards for tubing.
The supply port is located above the transistor source terminal (S) and the ground port is located below the resistor right terminal (R)

```python
	out1 = cir.P((sup1.C%gnd1.C)+(6000,1000)) # Output Port
	inp1 = cir.P(tran1.G1+(-6000,0),zspan=[0,-cir.params['via_H']]) # Input Port
```
Here we see some more advanced Point operations. The % operator automatically returns the midpoint of two Points, so here we are specifying that the output port is located 6mm to the right and 1mm above the midpoint of the supply port center (C) and the ground port center (C).

The input port is a little special, because it is located on the *lower* layer of the chip and is facing downwards. We therefore modify the z-direction of the port, telling it to be drawn from z=0 to z=-4mm (the thickness of the resin substrate) instead of the default z=0 to z=4mm (facing upwards). We grab the exact value of the resin substrate thickness from the default circuit parameters.

```python
	# Traces
	cir.T([sup1.C,tran1.S])
	cir.T([res1.R,gnd1.C])
```
Like our earlier trace, we are just connecting existing element terminals, in this case the source to the supply and the resistor to the ground. For a list of circuit elements and their terminals you can refer to, see the end of this document.

```python
	cir.T([tran1.D+(0,-250),tran1.D+(1000,-250),out1.C],trace_R=100)
	cir.T([tran1.G1,inp1.C],secs=mf.RecSec(W=250,H=-50))
```
Traces can draw between any number of Points in a list. Here we also specify an optional drawing parameter for the trace, a radius-of-curvature of 100um.
The final line hints at how extensible the trace function can be. So far we had been drawing all traces using the default cross-section, which is a rectangle 250um wide and 50um tall. However, we can specify any cross-sectional shape we want to draw our traces (and even our transistors) with. These cross-sections are termed here as "Sections", and you can specify various shapes (rectangular, curved edge rectangular, trapezoidal, tubular) with different dimensions. You can even specify a list of sections to be used for every point in a trace, and the program will smoothly transition from one cross-section to another as it draws the trace between the points specified, which enables tapers or complex trace shape changes.
Here, we make a rectangular channel from the gate of the transistor to the input port. These are both on the underside of the chip and we therefore use a section that runs beneath the membrane, where the height H is negative.

## Details
### Points
Microfusion Point objects support the following operations (between a Point/Point, or a Point/Tuple, but not Tuple/Tuple)
|Symbol| Operation|
|:---:|:---|
|+ | Add in x, y, and z|
|- | Subtract in x, y, and z|
|\| | Take x of left point and y of right point|
|^ | Take x,y of left point and z of right point|
|% | Return midpoint in x and y|
|* | Multiply elementwise by a scalar|
|/ | Divide elementwise by a scalar|

### Drawing Parameters
### Elements
### Sections
