import scriptcontext
import Rhino
import rhinoscriptsyntax as rs
import math
from  MF_00_Util import *
from  MF_01_Util2 import *


def writeSvgHeader5mm():	
	txt = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
	<svg
	   xmlns:dc="http://purl.org/dc/elements/1.1/"
	   xmlns:cc="http://creativecommons.org/ns#"
	   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
	   xmlns:svg="http://www.w3.org/2000/svg"
	   xmlns="http://www.w3.org/2000/svg"
	   height="600mm" width="1000mm"
	   viewBox="0 0 1000 600">
	  <g id="layer1">
	'''
	return txt


def writeSvgCurves(elements, dotLayer, offsetX, offsetY):
	txt = []
	for curves in elements:
		txt.append('<path d="')
		allCps = []
		for curve in curves:
			cps = rs.CurvePoints(curve)
			if len(cps) > 4 or len(cps) == 3:
				segments, remainder = divmod(len(cps) - 1, 3)
				if remainder > 0:
					rs.RebuildCurve(curve, 3, (segments + 1) * 3 + 1)
					cps = rs.CurvePoints(curve)

				count = 0
				currentCps = []
				allCps.append(currentCps)
				for i in range(len(cps)):
					currentCps.append(cps[i])
					if count == 3:
						count = 1
						currentCps = []
						allCps.append(currentCps)
						currentCps.append(cps[i])
					else:
						count += 1
			else:
				allCps.append(cps)
		
		svgPaths = []
		for cp in allCps:
			count = 0
			if len(cp) == 1: 
				continue
			if len(cp) == 3: 
				cp = [cp[0], cp[1], cp[1], cp[2]]
			if len(cp) > 4: 
				continue
			svgPaths.append(cp)
		
		orderedSvgPaths = orderSvgPaths(svgPaths, dotLayer)
		
		for cp in orderedSvgPaths:
			count = 0
			for p in cp:				
				if count == 0: txt.append('M')
				txt.append(x(p[0],offsetX)) 
				txt.append(',')
				txt.append(y(p[1],offsetY))
				txt.append(' ')
				count += 1
				if count == 1: 
					if len(cp) == 2:
						txt.append('L')
					else:
						txt.append('C')
		txt.append('" stroke-width="0.5" stroke="black" fill="none"/>')
	return ''.join(txt)


def writeSvgCircles(offsetX, offsetY, layerCircle):
	svg = []
	layers = layerCircle
	for l in layers:
		circles = rs.ObjectsByLayer(l, False)
		for circle in circles:
			pos = rs.CircleCenterPoint(circle)
			radius = rs.CircleRadius(circle)
			svg.append('<circle cx="' + x(pos[0], offsetX) + '" cy="' + y(pos[1], offsetY) + '" r="' + str(radius) + '" stroke-width="0.5" stroke="black" fill="none"/>')
	return ''.join(svg)

def x(value, offsetX):
	value += offsetX
	return str(round(value, 2))

def y(value, offsetY):
	value += offsetY
	return str(round(value, 2))

def writeSvgText(offsetX, offsetY, layerText):
	svgs = []
	layers = layerText
	for l in layers:
		elements = rs.ObjectsByLayer(l, False)
		for text in elements:
			pos = rs.TextObjectPoint(text)
			t = rs.TextObjectText(text)
			svgs.append('<text x="' + x(pos[0], offsetX) + '" y="' + y(pos[1], offsetY) + '" fill="none" text-anchor="middle" baseline-shift="-30%" font-size="9px" stroke="blue" stroke-width="0.3">' + t + '</text>')
	return ''.join(svgs)


def writeTestRectangles():
	svgs = []
	points = [[5, 5], [1000, 5], [5, 590], [1000, 590]]
	for p in points:
		for x in range(2):
			for y in range(2):
				px = p[0] + x * 10
				py = p[1] + y * 10
				svgs.append('<rect  x="' + str(px) + '" y="' + str(py) + '" width="5" height="5" fill="none" stroke-width="0.5" stroke="red"/>')
	return ''.join(svgs)


def writeCoverStripes(offsetX, offsetY):
	txt = []
	for stripePolyLine in rs.ObjectsByLayer("MF_56_Stripes", False):
		txt.append('<path d="')
		cps = rs.CurvePoints(stripePolyLine)
		cps.append(cps[0])

		for i in range(len(cps)-1):
			txt.append('M')
			txt.append(x(cps[i][0],offsetX)) 
			txt.append(',')
			txt.append(y(cps[i][1],offsetY))
			txt.append(' ')
			txt.append('L')
			txt.append(x(cps[i+1][0],offsetX)) 
			txt.append(',')
			txt.append(y(cps[i+1][1],offsetY))
			txt.append(' ')
		txt.append('" stroke-width="0.5" stroke="black" fill="none"/>')
	return ''.join(txt)

def doStuff():
	makeLayers(["MF_60_Works", "MF_60_PathDots"])
	txt = writeSvgHeader5mm()
	dotLayer = "MF_60_PathDots"
	offsetX = 1000
	offsetY = 0

	elements = []
	layers = ["MF_10_Parts"]
	[elements.extend(rs.ObjectsByLayer(l, False)) for l in layers]
	elements = [rs.DuplicateEdgeCurves(e) for e in elements]
	txt += writeSvgCurves(elements, dotLayer, offsetX, offsetY)

	#write all the rest
	layerText = ["MF_10_Texts"]
	layerCircle = ["MF_10_Circles"]
	txt += writeSvgText(offsetX, offsetY, layerText)
	txt += writeSvgCircles(offsetX, offsetY, layerCircle)	
	txt += writeTestRectangles()
	
	txt += '</g></svg>'	
	print txt
	
	f = open('C:/Users/Kevin/Desktop/VentilationDuct.svg', 'w')
	f.write(txt)
	f.close()
	rs.CurrentLayer("Default")
	rs.LayerVisible(dotLayer, False)
	rs.PurgeLayer("MF_60_Works")

doStuff()