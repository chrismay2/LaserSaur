import scriptcontext
import Rhino
import rhinoscriptsyntax as rs
from  MF_00_Util import *


def ajustLattices(uLattices, vLattices, vCutters, mid = False, ajust = True):
	uCutters = []
	midPointS = []
	for u in range(len(uLattices)):
		points1 = []
		points2 = []
		midPoints = []
		for v in range(len(vLattices)):
			intersection = rs.IntersectBreps(uLattices[u], vLattices[v])
			if ajust:
				
				a = 1
			midPoint = rs.DivideCurve(intersection, 2, True, True)[1]
			length = rs.CurveLength(intersection)
			
			if ajust:
				offset = length / 2
			else:
				offset = 20
				
			startPoint = rs.CurveEndPoint(intersection)
			endPoint = rs.CurveStartPoint(intersection)
			vector1 = rs.VectorCreate(endPoint, startPoint)
			vector1 = rs.VectorUnitize(vector1)

			
			if u == 0 or u == 2:
				point1 = rs.PointAdd(midPoint, offset * vector1)
				if ajust:
					point2 = rs.PointAdd(midPoint, -20 * vector1)
				else:	
					point2 = rs.PointAdd(midPoint, -20 * vector1)
			else:
				if ajust:
					point1 = rs.PointAdd(midPoint, 20 * vector1)
				else:	
					point1 = rs.PointAdd(midPoint, 20 * vector1)
				p1 = rs.AddPoint(point1)
				
				point2 = rs.PointAdd(midPoint, -offset * vector1)
				p2 = rs.AddPoint(point2)
				
				
			points1.append(point1)
			points2.append(point2)
			
			if ajust :
				if v == 0:
					point3 = rs.PointAdd(midPoint, -offset * vector1)
					p = (midPoint + point3) / 2
					text = "T" + "U" + str(u)
					addMarkerDot(vLattices[0], text, p, "MF_10_Dots")
					rs.ObjectLayer(vLattices[0], "Layer 05")
		
			
			if ajust:
				if not len(midPoints) == 0:
					point3 = midPoints[len(midPoints) - 1]
					point4 = (midPoint + point3) / 2
					
					if u == 0 or u == 2:
						a = -3
					else:
						a = -3
			
					vector2 = rs.VectorCreate(point4, point3)
					vector2 = rs.VectorUnitize(vector2)
					vectorAxis = rs.VectorCrossProduct (vector1, vector2)
					normalVector = rs.VectorRotate(vector2, -90, vectorAxis)
					normalVector = rs.VectorUnitize(normalVector)
					point5 = rs.PointAdd(point4, -1 * vector2)
					point5 = rs.PointAdd(point5, -a * normalVector)
					point6 = rs.PointAdd(point4, 1 * vector2)
					point6 = rs.PointAdd(point6, a * normalVector)
					midPoints.append(point5)
					midPoints.append(point6)
					
			midPoints.append(midPoint)
		
		points = []
		
		for i in range(len(points1)):
			points.append(points1[i])
		points2 = points2[::-1]
		for i in range(len(points2)):
			points.append(points2[i])
		points.append(points[0])
		
		if mid:
			midPointS.append(points[2])
			midPointS.append(points[33])
		
		polyline = rs.AddPolyline(points)
		surface = rs.AddPlanarSrf(polyline)
		
		
		lattice = rs.OffsetSurface(surface, 0, None, False, False) #convert into brep
		rs.DeleteObject(surface)
		uLattices[u] = lattice
		if ajust:
			rs.ObjectLayer(uLattices[u], "Layer 05")
			makeUCutters(uLattices, vLattices, points1, points2, midPoints, uCutters, u)
			
			
		
	if ajust:
		cutULattices(uLattices, vCutters)
		#alignLattices(uLattices)
		for i in range(len(vLattices)):
			cutVLattices(vLattices[i], uCutters, i, vLattices)
			#alignLattices(vLattices[i])
	
	if mid:
		return midPointS
	else:
		return uLattices
	
	

def cutVLattices(lattice, uCutters, i, vLattices):
	for j in range(len(uCutters)):
		lattice = cutInsets(lattice, uCutters[j])
	vLattices[i] = lattice
	rs.ObjectLayer(vLattices[i], "Layer 05")


def cutInsets(brepId, cutterId):
	brep = rs.coercebrep(brepId, True)
	cutter = rs.coercebrep(cutterId, True)
	tolerance = 0.5
	pieces = brep.Split(cutter, tolerance)
	if not pieces: 
		return brepId
	newBrep = getLargestPiece(pieces)
	newBrep = scriptcontext.doc.Objects.AddBrep(newBrep)
	if str(newBrep).startswith("00000000"):
		return brepId	
	rs.DeleteObject(brepId)
	scriptcontext.doc.Views.Redraw()
	return str(newBrep)	
	
	
def makeUCutters(uLattices, vLattices, points1, points2, midPoints, uCutters, u):
	startPoints = midPoints
	
	if u == 0 or u == 2:
		endPoints = points2
	else: 
		endPoints = points1
	
	curve = rs.ExtendCurveLength(rs.AddCurve(endPoints, 3), 0, 2, 10)
	
	endPoints = []
	endPoints = rs.DivideCurve(curve, 100)
	
	
	
	points = []
	for i in range(len(startPoints)):
		p = rs.AddPoint(startPoints[i])
		#rs.SelectObject(p)
		points.append(startPoints[i])
		
	if u == 1 or u == 3:	
		endPoints = endPoints[::-1]
	

	for i in range(len(endPoints)):
		points.append(endPoints[i])
	points.append(points[0])
		
	polyline = rs.AddPolyline(points)
	surface = rs.AddPlanarSrf(polyline)
	rs.DeleteObject(polyline)
	cutter = rs.OffsetSurface(surface[0], 1.5, None, True, True) #convert into brep
	rs.DeleteObject(surface[0])
	uCutters.append(cutter)
	
	
def cutULattices(lattices, cutters):
	for i in range(len(lattices)):
		for j in range(len(cutters)):
			lattices[i] = cutInsets(lattices[i], cutters[j])
			rs.ObjectLayer(lattices[i], "Layer 05")
	

def addVMarkers(lattices, txt, q):

	points = rs.SurfacePoints(lattices)
	points1 = []
	points2 = []
	for p in range(len(points)):
		if not p%2 == 0:
			points1.append(points[p])
			
		else:
			points2.append(points[p])		
	points3 = []	
	for i in range(int(len(points1))):
		p3 = (points1[i] + points2[i]) / 2
		points3.append(p3)
		
	curve = rs.AddCurve(points3)

	midPoint = rs.DivideCurve(curve, 2, True, True)[1]
	text = "T" + txt + "-" + str(q)
	addMarkerDot(lattices, text, midPoint, "MF_10_VDots")
	#rs.ObjectLayer(lattices, "Layer 05")
	
def addUMarkers(midPoints, lattices, txt, v):
	
	
	if v == 0:
		midPoint = (midPoints[0] + midPoints[1]) / 2
	if v == 1:
		midPoint = (midPoints[2] + midPoints[3]) / 2
	if v == 2:
		midPoint = (midPoints[4] + midPoints[5]) / 2
	if v == 3:
		midPoint = (midPoints[6] + midPoints[7]) / 2

	text = "T" + txt + "-" + str(v)
	addMarkerDot(lattices, text, midPoint, "MF_10_UDots")
	rs.ObjectLayer(lattices, "Layer 05")


def alignLattices(midPoints, lattices, c = False, u = False):
	deltaX = 1
	deltaY = 0
	#latticeGuid = lattices
		
	for v in range(len(lattices)):
		latticeGuid = lattices[v]
		
		if c == True:
			addVMarkers(latticeGuid, "V", v)
		
		if u == True:
			addUMarkers(midPoints, latticeGuid, "U", v)
		
		dotMarker = rs.GetUserText(latticeGuid, "Dot_Marker_" + str(0))
		
		unrollResult = rs.UnrollSurface(latticeGuid, False, [dotMarker])
		
		lattice = unrollResult[0][0]
		latticeElement = [lattice]
		
		o = convertMarkerDot(unrollResult[1], "10")
		latticeElement.append(o)
		dotObjects = o
	
		#scale objects
		factor = 1
		rs.ScaleObjects(latticeElement, [0, 0, 0], [factor, factor, factor])
	
		#move objects
		box = rs.BoundingBox(latticeElement)
		
		rs.MoveObjects(latticeElement, [deltaX, deltaY, 0])
		deltaX +=(box[1][0] - box[0][0]) + 2
					
		#create group and convert dot markers
		groupName = rs.AddGroup()
		rs.AddObjectToGroup(lattice, groupName)
		rs.AddObjectsToGroup(dotObjects, groupName)
		rs.ObjectLayer(lattice, "MF_10_Parts")


def doStuff():
	makeLayers(["MF_10_Works", "MF_10_Cutters", "Layer 05", "MF_10_Dots", "MF_10_UDots", "MF_10_VDots", "MF_10_Circles", "MF_10_Texts", "MF_10_Parts"])
	dotObjects = []
	vCutters = []
	layers = ["Layer 06"]
	[vCutters.extend(rs.ObjectsByLayer(l, False)) for l in layers]
	for v in range(len(vCutters)):
		vCutters[v] = rs.OffsetSurface(vCutters[v], 1.5, None, True, True) #convert into brep
		rs.ObjectLayer(vCutters[v], "MF_10_Cutters")
		
	vLattices = []
	layers = ["Layer 03"]
	[vLattices.extend(rs.ObjectsByLayer(l, False)) for l in layers]
	for v in range(len(vLattices)):
		vLattices[v] = rs.OffsetSurface(vLattices[v], 0, None, False, False) #convert into brep
		rs.ObjectLayer(vLattices[v], "Layer 05")
	
	
	
	uLattices = []
	uCurves = []
	uCurvesPairs = [[], [], [], []]
	layers = ["Layer 01"]
	[uCurves.extend(rs.ObjectsByLayer(l, False)) for l in layers]
	j = 0
	for i in range(len(uCurves)):
		if i%2 == 0:
			uCurvesPairs[j].append(uCurves[i])
			uCurvesPairs[j].append(uCurves[i + 1])
			j += 1
	
	for i in range(len(uCurvesPairs)):
		points = []
		for j in range(len(uCurvesPairs[i])):
			if j%2 == 0:
				point = rs.DivideCurve(uCurvesPairs[i][j], 100)
				for p in range(len(point)):
					points.append(point[p])
			else:
				points = rs.DivideCurve(uCurvesPairs[i][j], 100)[::-1]
				for p in range(len(point)):
					points.append(point[p])
		points.append(points[0])
		polyline = rs.AddPolyline(points)
		surface = rs.AddPlanarSrf(polyline)
		rs.DeleteObject(polyline)
		lattice = rs.OffsetSurface(surface, 0, None, False, False) #convert into brep
		uLattices.append(lattice)
		
	uLattices = ajustLattices(uLattices, vLattices, vCutters, False, False)
	midPoints = ajustLattices(uLattices, vLattices, vCutters, True, False)
	uLattices = ajustLattices(uLattices, vLattices, vCutters, False, True)
	
	
	alignLattices(midPoints, vLattices, True, False)
	alignLattices(midPoints, uLattices, False, True)	
		
	
	
	
	rs.CurrentLayer("Default")
	rs.LayerVisible("MF_10_Cutters", False)
	rs.PurgeLayer("MF_10_Works")
	a=2
				

doStuff()
