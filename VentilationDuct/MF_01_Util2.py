import scriptcontext
import Rhino
import rhinoscriptsyntax as rs
import math
from  MF_00_Util import *


def orderSvgPaths(svgPaths, dotLayer):
	orderSvgPaths = []
	
	#Take the first path of svgPaths as starting path
	orderSvgPaths.append(svgPaths[0])
	
	#Remove it from svgPaths so it cannot be chosen again
	svgPaths.remove(svgPaths[0])
	
	#Repeat this until there isn't any path left in svgPath
	while len(svgPaths) > 0:
		#Search a path in svgPath
		for i in range(len(svgPaths)):
			
			#taking as reference the last path in orderSvgPaths
			reference = orderSvgPaths[len(orderSvgPaths)-1]
			svgPath = svgPaths[i]
			DIGITS = 3
			#test if the X and Y values of the first point of the tested path are approximately the same as the X and Y values of the last point of the reference
			if round(svgPath[0].X,DIGITS) == round(reference[len(reference)-1].X,DIGITS) and round(svgPath[0].Y,DIGITS) == round(reference[len(reference)-1].Y,DIGITS):
				#if yes, add it to orderSvgPaths
				orderSvgPaths.append(svgPath)
				#and remove it from svgPaths
				svgPaths.remove(svgPath)
				break
				
			#test if the X and Y values of the last point of the tested path are approximately the same as the X and Y values of the last point of the reference
			if round(svgPath[len(svgPath)-1].X,DIGITS) == round(reference[len(reference)-1].X,DIGITS) and round(svgPath[len(svgPath)-1].Y,DIGITS) == round(reference[len(reference)-1].Y,DIGITS):
				#if yes, flip the path,
				flipSvgPath = svgPath[::-1] #flip
				#add the flipped path to orderSvgPaths
				orderSvgPaths.append(flipSvgPath)
				#remove the unflipped path from svgPaths
				svgPaths.remove(svgPath)
				break
			
			#if there isn't any path which fill either one of the two previous conditions, 
			if i == len(svgPaths)-1:
				#add the first path from svgPaths to orderSvgPaths
				orderSvgPaths.append(svgPaths[0])
				#and remove it from svgPaths
				svgPaths.remove(svgPaths[0])
				break
				
	for i in range(len(orderSvgPaths)):
		p = orderSvgPaths[i]
		#pathDot = rs.AddTextDot(str(i), p[0])
		#rs.ObjectLayer(pathDot, dotLayer)
	return orderSvgPaths

