'''
Elements classes.
'''
import adsk.core, adsk.fusion, traceback

import math

from .base import *
from .point import *
from .section import *

class Trace:
	def __init__(self,circuit,pts,secs=None,**kwargs):
		'''Constructor for a trace.'''
		self.circuit = circuit
		self.pts = [Pt(*pt) if isinstance(pt,tuple) else pt for pt in pts]
		pts = self.pts
		if secs is None: # Use default if no sections are passed
			secs = circuit.params['trace_sec']
		if isinstance(secs,Section): # Expand sections to list
			secs = [secs for i in range(len(pts))]
		self.secs = secs
		self.params = circuit.params.copy()
		for key in kwargs: # Overwrite params with kw params
			if key in self.params.keys():
				self.params[key] = kwargs[key]

		# Drawing parameters
		eps = 1e-3
		Rs = self.params['trace_R']
		if not isinstance(Rs,list):
			Rs = [Rs for i in range(len(pts))]
		# Avoid self-intersections by ensuring R>sec.span/2
		Rs = [max(Rs[i],secs[i].span/2+eps) for i in range(len(pts))]

		# Helper function to draw a loft
		def makeLoft(curve,s1,s2,n1,n2):
			# Make object collection
			skel = adsk.core.ObjectCollection.create()
			skel.add(curve)
			skel_path = circuit._comp.features.createPath(skel)
			# Prepare Loft
			loft_inp = circuit._comp.features.loftFeatures.createInput(
			adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
			# Draw the sections
			p1 = Pt(curve.startSketchPoint.geometry)
			p2 = Pt(curve.endSketchPoint.geometry)
			if n1.x*n2.y - n2.x*n1.y < 0:
				n1,n2 = n2,n1
				asec1 = s1.draw(circuit,p1,n1)
				asec2 = s2.draw(circuit,p2,n2)
				loft_inp.loftSections.add(asec2)
				loft_inp.loftSections.add(asec1)
			else:
				asec1 = s1.draw(circuit,p1,n1)
				asec2 = s2.draw(circuit,p2,n2)
				loft_inp.loftSections.add(asec1)
				loft_inp.loftSections.add(asec2)
			loft_inp.centerLineOrRails.addCenterLine(skel_path)
			loft_inp.isSolid = True
			circuit._comp.features.loftFeatures.add(loft_inp)

		# Draw the segments
		sketch = circuit._sketch
		asegs = []
		for i in range(1,len(pts)):
			asegs.append(sketch.sketchCurves.sketchLines.addByTwoPoints(
				pts[i-1].acadPoint3D,pts[i].acadPoint3D))
		# Fillet the non-colinear points and loft the arcs
		aarcs = []
		for i in range(1,len(pts)-1):
			n1 = pts[i]-pts[i-1] # TODO make this a Pt operation
			u1 = n1/n1.m
			n2 = pts[i+1]-pts[i]
			u2 = n2/n2.m
			# Fillet and loft arc only if not colinear
			if not math.isclose(abs(u1.x*u2.x + u1.y*u2.y),1):
				arc = sketch.sketchCurves.sketchArcs.addFillet(
					asegs[i-1], asegs[i-1].endSketchPoint.geometry,
					asegs[i], asegs[i].startSketchPoint.geometry,
					Rs[i]*circuit.design.units)
				makeLoft(arc,secs[i],secs[i],n1,n2)
			# Loft prior segment with new coordinates after filleting
			makeLoft(asegs[i-1],secs[i-1],secs[i],n1,n1)
		# Loft final segment
		n2 = pts[-1]-pts[-2]
		makeLoft(asegs[-1],secs[-2],secs[-1],n2,n2)

		# Set the pins
		self.P1 = pts[0]
		self.P2 = pts[-1]

class Via:
	def __init__(self,circuit,pt,zspan=None,**kwargs):
		'''Constructor for a via.'''
		self.circuit = circuit
		self.pt = Pt(*pt) if isinstance(pt,tuple) else pt
		pt = self.pt
		self.params = circuit.params.copy()
		for key in kwargs: # Overwrite params with kw params
			if key in self.params.keys():
				self.params[key] = kwargs[key]
		self.zspan = [0, self.params['via_H']] if zspan is None else zspan
		zspan = self.zspan
		
		# Drawing parameters
		R = self.params['via_R']
		start = Pt(pt.x,pt.y,zspan[0])
		end = Pt(pt.x,pt.y,zspan[1])

		# Draw the cylinder (using loft)
		sketch = circuit._sketch
		cir1 = adsk.core.ObjectCollection.create()
		cir1.add(sketch.sketchCurves.sketchCircles.addByCenterRadius(
				start.acadPoint3D, R*circuit.design.units))
		cir2 = adsk.core.ObjectCollection.create()
		cir2.add(sketch.sketchCurves.sketchCircles.addByCenterRadius(
				end.acadPoint3D, R*circuit.design.units))
		loft_inp = circuit._comp.features.loftFeatures.createInput(
			adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
		loft_inp.loftSections.add(circuit._comp.features.createPath(cir1))
		loft_inp.loftSections.add(circuit._comp.features.createPath(cir2))
		loft_inp.isSolid = True
		circuit._comp.features.loftFeatures.add(loft_inp)

		# Set the pin
		self.C = pt

class Port:
	def __init__(self,circuit,pt,zspan=None,**kwargs):
		'''Constructor for a port (a via with a barb).'''
		self.circuit = circuit
		self.pt = Pt(*pt) if isinstance(pt,tuple) else pt
		pt = self.pt
		self.params = circuit.params.copy()
		for key in kwargs: # Overwrite params with kw params
			if key in self.params.keys():
				self.params[key] = kwargs[key]
		
		# Drawing parameters
		H = self.params['via_H'] # Top of the chip
		R = self.params['via_R'] # Inner radius of barb
		R0 = 900 # Tapered outer radius of barb
		R1 = 1100 # Flared outer radius of barb
		R2 = 2250 # Space for outer radius of tubing
		taper = 1000 # How long is the taper

		# Create pointlist for the sketch (0,0 is top along centerline)
		pr = [R0, R1, R0, R0, (R0+R2)/2, R2, R2]
		pz = [0, -taper, -taper, -taper*2, -taper*2-(R2-R0)/2,-taper*2,0]
		# Flip z if zspan is negative
		if zspan is not None and (zspan[0]+zspan[1]) <0:
			pz = [-z for z in pz]
			H = -H
		pts = [pt+Pt(pr[i],0,H+pz[i]) for i in range(len(pr))]
		# Draw the sketch of the removed section
		collection = adsk.core.ObjectCollection.create()
		for i in range(len(pts)):
			collection.add(circuit._sketch.sketchCurves.sketchLines
				.addByTwoPoints(pts[i-1].acadPoint3D,pts[i].acadPoint3D))
		path = circuit._comp.features.createPath(collection)

		# Create the axis to revolve around
		ax = [pt,pt+Pt(0,0,H)] # Axis to revolve around
		axis = circuit._sketch.sketchCurves.sketchLines.addByTwoPoints(
			ax[0].acadPoint3D,ax[1].acadPoint3D)
		# Revolve
		rev_inp = circuit._comp.features.revolveFeatures.createInput(
			path, axis,
			adsk.fusion.FeatureOperations.NewComponentFeatureOperation)
		rev_inp.setAngleExtent(False,
			adsk.core.ValueInput.createByReal(2*math.pi))
		circuit._comp.features.revolveFeatures.add(rev_inp)

		# Add the lumen as a via
		circuit.V(pt,zspan=zspan,**kwargs)

		# Set the pin
		self.C = pt


class Transistor:
	def __init__(self,circuit,pt,anchor='C',rotation=0,invert=False,sec=RectSect,**kwargs):
		'''Constructor for transistor.'''
		self.circuit = circuit
		self.pt = Pt(*pt) if isinstance(pt,tuple) else pt
		pt = self.pt
		self.anchor = anchor
		self.rotation = rotation
		self.invert = invert # If true, flip in Z
		self.sec = sec if isinstance(sec,list) else [sec, sec]
		sec = self.sec
		self.params = circuit.params.copy()
		for key in kwargs: # Overwrite params with kw params
			if key in self.params.keys():
				self.params[key] = kwargs[key]

		# Drawing parameters
		slop = self.params['slop']
		L = self.params['trans_L']
		W = self.params['trans_W']
		H = self.params['trans_H']
		T = self.params['trans_T']
		H = -H if invert else H

		# Compute draw points
		points = [Pt(), Pt(0,L/2+slop), Pt(0,-L/2-slop),
			Pt(-W/2-slop,0), Pt(W/2+slop,0),
			Pt(0,L/2),Pt(0,-L/2)]
		anchors = ['C','S','D','G1','G2','P1','P2']
		a = points[anchors.index(anchor)]
		# Center over anchor
		points = [point - a for point in points]
		# Rotate and shift as needed
		points = [pt+point.rotate(rotation) for point in points]
		
		# Figure out all the sections
		Ws = W # Width at source
		Wd = T*W # Width at drain
		source_sec = sec[0](W=Ws,H=-H)
		drain_sec = sec[0](W=Wd,H=-H)
		gate_sec = sec[1](W=L,H=H)

		# Draw
		circuit.T([points[1],points[5],points[6],points[2]],
			secs=[source_sec,source_sec,drain_sec,drain_sec])
		circuit.T([points[3],points[4]],secs=[gate_sec,gate_sec])

		# Set the pins
		self.C = points[0]
		self.S = points[1]
		self.D = points[2]
		self.G1 = points[3]
		self.G2 = points[4]
		self.P1 = points[5]
		self.P2 = points[6]

		# Extra params that might be useful for drawing circuits
		self.Ws = Ws
		self.Wd = Wd

class Resistor:
	def __init__(self,circuit,pt,val,anchor='L',rotation=0,justify='left',**kwargs):
		'''Constructor for transistor.'''
		self.circuit = circuit
		self.pt = Pt(*pt) if isinstance(pt,tuple) else pt
		pt = self.pt
		self.anchor = anchor
		self.rotation = rotation
		self.params = circuit.params.copy()
		for key in kwargs: # Overwrite params with kw params
			if key in self.params.keys():
				self.params[key] = kwargs[key]
		self.val = val
		self.justify = justify

		# Drawing parameters
		MU = self.params['fluid_Mu']
		L = self.params['res_L']
		R_sec = self.params['res_sec']
		T_sec = self.params['trace_sec']
		R = R_sec.span
		T = T_sec.span

		# Compute the number of wiggles that fit
		n = (L-T)//(R*4)
		# Compute the centerline distance with minimum wiggle amplitude
		wiggle_dist = n*(2*R + math.pi*R)
		# Compute the the wedge distances for entry and exit
		wedge_dist = (L-(n*R*4))/2
		# Compute the resistance with minimum wiggle amplitude
		min_res = MU * (R_sec.res_muL*wiggle_dist
			+ (R_sec.res_muL+T_sec.res_muL)*wedge_dist)
		min_res *= 1e-18 # Convert from 1/(m^4)*Pa*s*um to kPa*s/ul
		rem_res = val - min_res # Res to be gained in wiggle amplitude
		assert rem_res > 0, "Resistance too small."
		wiggle_amp = rem_res / (MU*R_sec.res_muL*n*2) * 1e18 # um

		# Place points
		points = [Pt()]
		secs = [T_sec]
		last_pt = Pt()+((L - (n*R*4))/2 ,0)
		points.append(last_pt) # Inlet wedge
		secs.append(R_sec)
		for i in range(n):
			wiggle = [
				last_pt+(R,0),
				last_pt+(R,R+wiggle_amp),
				last_pt+(3*R,R+wiggle_amp),
				last_pt+(3*R,0),
				last_pt+(4*R,0)]
			points += wiggle # Add the new wiggle
			secs += [R_sec for i in range(len(wiggle))]
			last_pt = wiggle[-1]
		points.append(Pt(L,0)) # Outlet wedge
		secs.append(T_sec)

		# Flip if justified right
		if justify is 'right':
			points = [Pt(point.x,-point.y,point.z) for point in points]

		# Determine anchor
		anchor_pts = [Pt(), Pt(L/2,0), Pt(L,0)]
		anchors = ['L','C','R']
		a = anchor_pts[anchors.index(anchor)]
		# Center over anchor
		points = [point - a for point in points]
		# Rotate and shift as needed
		points = [pt+point.rotate(rotation) for point in points]

		# Draw
		circuit.T(points,secs=secs)

		# Set the pins
		self.L = anchor_pts[0]
		self.C = anchor_pts[1]
		self.R = anchor_pts[2]