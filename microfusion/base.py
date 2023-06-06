'''
Base Design and Circuit classes.
'''

import adsk.core, adsk.fusion, traceback

from .point import *
from .section import *
from .elements import *

def printm(message):
	app = adsk.core.Application.get()
	ui  = app.userInterface
	ui.messageBox(message)

class Design:
	def __init__(self,origin=Pt(0,0,0),params=dict()):
		'''Construct the Design object.'''
		
		self.origin = origin # Origin wrt Fusion origin
		
		# Make the params default dictionary
		self.params = { # Default values
			# Constants
			'fluid_Mu':1.01e-3, # Fluid dynamic viscosity in Pa*s
			'membrane_E': 550e3, # Membrane Young's modulus in Pa
			# CAD parameters
			'slop': 50, # Slop in alignment to space elements in UM
			# Element parameters
			'trace_sec': RectSect(W=250, H=50), # Default section
			'trace_R': 250, # Trace radius of curvature in UM
			'trace_cap': 'none', # Cap for traces
			'trans_L': 250, # Transistor length in UM
			'trans_W': 250, # Transistor width in UM
			'trans_H': 25, # Transistor height in UM
			'trans_T': 1.0, # Transistor taper ratio (Ws/Wd)
			'res_L': 1000, # Resistor bounding box length in UM
			'res_sec': RectSect(W=50, H=50), # Resistor section
			'via_R': 350, # Via radius in UM
			'via_H': 4000, # Via height (depth) in UM
			}
		for key in params: # Overwrite the defaults
			self.params[key] = params[key]

		self.units = Pt().units # Get units from Point class

		self.circuits = [] # List of all circuits

		# TBD: Clear all elements on every rerun

		# Set up the app
		self._app = adsk.core.Application.get()
		self._ui = self._app.userInterface
		self._product = self._app.activeProduct
		self._design = adsk.fusion.Design.cast(self._product)
		# Do not capture design history for speed
		self._design.designType = adsk.fusion.DesignTypes.DirectDesignType
		self._root_comp = self._design.rootComponent

	def add_circuit(self,*args,**kwargs):
		'''Add a circuit to the design.'''
		cir = Circuit(self,*args,**kwargs)
		self.circuits.append(cir)
		return cir

	def draw_substrate(self,xlen,ylen,zspan):
		'''Draw a cuboid centered at 0,0 from z[0] to z[1].'''
		circuit = self.add_circuit()
		left = Pt(-xlen/2,0,zspan[0])
		right = Pt(xlen/2,0,zspan[0])
		substrate = circuit.T([left,right],
			secs=RectSect(W=ylen,H=zspan[1]-zspan[0]))
		# Perform intersection with 

class Circuit:
	def __init__(self,design,origin=Pt(0,0,0),**kwargs):
		'''Construct the Circuit'''
		self.design = design
		self.origin = origin

		self.params = self.design.params.copy()
		for key in kwargs: # Overwrite params with kw params
			if key in self.params.keys():
				self.params[key] = kwargs[key]

		self.elements = [] # List of all elements

		# Create the circuit component and sketchplane
		self._occ = self.design._root_comp.occurrences.addNewComponent(
			adsk.core.Matrix3D.create())
		self._comp = self._occ.component
		self._sketch = self._comp.sketches.add(
			self._comp.xYConstructionPlane)
		self._sketch.isComputeDeferred = True # Saves time evaluating
		self._sketch.areProfilesShown = False # Saves time drawing

	## Elements
	def T(self,*args,**kwargs):
		'''Add a Trace to the circuit.'''
		trace = Trace(self,*args,**kwargs)
		self.elements.append(trace)
		return trace

	def V(self,*args,**kwargs):
		'''Add a Via to the circuit.'''
		via = Via(self,*args,**kwargs)
		self.elements.append(via)
		return via

	def M(self,*args,**kwargs):
		'''Add a Transistor to the circuit.'''
		trans = Transistor(self,*args,**kwargs)
		self.elements.append(trans)
		return trans

	def R(self,*args,**kwargs):
		'''Add a Resistor to the circuit.'''
		res = Resistor(self,*args,**kwargs)
		self.elements.append(res)
		return res

	def P(self,*args,**kwargs):
		'''Add a Port to the circuit.'''
		port = Port(self,*args,**kwargs)
		self.elements.append(port)
		return port