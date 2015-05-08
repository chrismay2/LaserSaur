import scriptcontext
import Rhino
import rhinoscriptsyntax as rs
import System.Array
from System.Collections.Generic import List
from Rhino.Geometry import Point3d


#PARAMETERS
SCALE = 1 / 1
TARGETFACE = 2  				#the modul ID for which the lattices are created
LATTICE_HEIGHT = 50 * SCALE		#the height of the lattices in mm
BORDER_LATTICE_HEIGHT = 100 * SCALE		#the height of the lattices in mm
LATTICE_THICKNESS_NORMAL = 4 * SCALE	#the thickness of the lattices
LATTICE_THICKNESS_BORDER = 12 * SCALE	#the thickness of the border lattices
LATTICE_THICKNESS_FOR_BORDER_CUT = 4.5 * SCALE	#the width for creating the lattice cuts at the border lattices
LATTICES_TIGHT = [3, 4]
TRIANGLE_THICKNESS = 12 * SCALE
TRIANGLE_SIZE = 180 * SCALE
COVER_THICKNESS = 3 * SCALE		#the thickness of the covers
COVER_GAP = 0.5 * SCALE			#gap between the cover and the lattices
COVER_GRID = 80
HIGH_END_LATTICES = [[0, 4], [2, 8]]
JOINTS_HOLE_DIAMETER = 6 * SCALE
CONNECTOR_DIAMETER = 5 * SCALE
CONNECTOR_DIAMETER_TIGHT = 4.7 * SCALE
CORNER_CUT_COUNT = 12
SHEET_SIZE_LATTICES = [1000, 600]
SHEET_SIZE_BORDER_LATTICES = [1000, 600]
MIN_HEIGHT_FROM_BOTTOM = 40
MIN_HEIGHT_FROM_BOTTOM_THRESHOLD = 250
CENTER_LATTICE_U = False
CENTER_LATTICE_V = True
COVER_STRIPE_WIDTH = 20
COVER_BRIDGE_CUTS_COUNT = 9


#CONSTANTS####################################################################
#tier constants
TIER_SURFACE = 0       #constant for the lower edge of the lattices
TIER_MIDDLE_CUTTER = 1       #constant for the center-line of the lattices (where the slots meet)
TIER_LATTICE_EDGE = 2      #constant for the upper edge of the lattices
TIER_HEAD_SUB = 3       #constant for the nodes/curves below head
TIER_HEAD = 4         #constant for the head nodes/curves
TIER_HEIGHTS = [0, LATTICE_HEIGHT*0.56, LATTICE_HEIGHT, BORDER_LATTICE_HEIGHT*0.8, BORDER_LATTICE_HEIGHT] 
TIERS_COUNT = 5

FACEPLATE_TIER_1 = 0
FACEPLATE_TIER_2 = 1
FACEPLATE_TIER_3 = 2
FACEPLATE_TIER_4 = 3
FACEPLATE_TIER_HEIGHTS = [60, 70, 125, 135]
FACEPLATE_DISTANCE = 12
FACEPLATE_THICKNESS = 5 * SCALE

#Cardinals
CARDINAL_NORTH = 0
CARDINAL_WEST = 1
CARDINAL_SOUTH = 2
CARDINAL_EAST = 3
CARDINALS_COUNT = 4

CORNER_NORTH_EAST = 0

#Orientation
ORIENTATION_U = 0 # -> North to South
ORIENTATION_V = 1 # -> West to East
ORIENTATIONS_COUNT = 2


class MayForm():
	def __init__(self, id):
		self.id = id
		self.metaDataHolder = None
		self.surfaceGuids = []
		self.cornerNodes = [[], [], [], []]        # -> [cardinal][tier]
		self.latticeEndPoints = [[], [], [], []]  # -> [cardinal][tier][pos]
		self.cornerDivisionPoints = [[], [], [], []] # -> [cardinal][counter]
		self.lattices = [[], []]                   # -> [orientation][pos]
		self.borderLattices = []
		self.innerCurves = [[], []]                # -> [orientation][tier][pos]
		self.borderCurves = [[], [], [], []]
		self.cutters = [[], []]
		self.cuttingPlanes = []                    # -> [cardinal]
		self.cuttingPlanesTmp = []                 # -> [cardinal]
		self.covers = []                           # -> [posU][posV]
		self.facePlates = [[], [], [], []]         # -> [cardinal][index]
		self.segments = [0, 0]                     # -> [orientation]
		self.triangles = []                        # -> [cardinal]


class MayCover():
	def __init__(self, u, v):
		self.id = id
		self.coverObject = None
		self.coverObjectMoved = None
		self.dot = None
		self.u = u  #vertical position
		self.v = v  #horizontal position
		self.borderPoints = [None, None, None, None]     #GUIDs, by cardinal 
		self.outerPoints = [None, None, None, None]      #GUIDs, by cardinal
		self.innerPoints = [] 	 #GUIDs, can be 3, 4 or 5 points
		#self.latticeIndex = [None, None, None, None]     #u/v index of lattice, by cardinal  
		#self.latticesPerSide = [None, None, None, None]  #GUIDs, by cardinal
		self.exists = True			#some fragmented covers do not exist, so the cover is just a placeholder
		self.uAxis = None
		self.vAxis = None
		self.zAxis = None
		self.dockingPoints = None

	#Here we order the points at the corners of the cover. We call them 
	# cardinal points, which are a combination of border and outer points
	# but ordered according to cardinals.
	def getCardinalPoint(self, cardinal):
		cardinalPoint = self.outerPoints[cardinal]
		if not cardinalPoint:
			cardinalPoint = self.borderPoints[cardinal]
		if not cardinalPoint:
			cardinalPoint = self.borderPoints[plus4(cardinal, 3)]
		return cardinalPoint
		
	
	
	
	
def readTargetMayForm():
	metaDataHolder = rs.ObjectsByName("TARGET_META_DATA_HOLDER")
	mayForm = readMayForm(metaDataHolder[0])
	return mayForm


def readMayForm(metaDataHolder):
	mayFormId = int(rs.GetUserText(metaDataHolder, "ID"))
	mayForm = MayForm(mayFormId)
	mayForm.metaDataHolder = metaDataHolder

	#read basic data
	for tier in range(TIERS_COUNT):
		mayForm.surfaceGuids.append(rs.GetUserText(metaDataHolder, "Surface_Guids_" + str(tier)))

	#read number of segments
	if rs.GetUserText(metaDataHolder, "Segments_U"):
		mayForm.segments[ORIENTATION_U] = int(rs.GetUserText(metaDataHolder, "Segments_U"))
		mayForm.segments[ORIENTATION_V] = int(rs.GetUserText(metaDataHolder, "Segments_V"))

	#read border lattices and corner nodes
	for cardinal in range(CARDINALS_COUNT):
		borderLattice = rs.GetUserText(metaDataHolder, "Border_Lattice_" + str(cardinal))
		mayForm.borderLattices.append(borderLattice)
		
		for tier in range(TIERS_COUNT):
			node = rs.GetUserText(metaDataHolder, "Corner_Node_" + str(cardinal) + "_" + str(tier))
			mayForm.cornerNodes[cardinal].append(node)
			mayForm.latticeEndPoints[cardinal].append([])
			for pos in range(mayForm.segments[getCrossOrientation(cardinal)] -1):
				bcp = rs.GetUserText(metaDataHolder, "Border_Cross_Point_" + str(cardinal) + "_" + str(tier) + "_" + str(pos))
				#coordinates = rs.PointCoordinates(bcp) if bcp else None
				mayForm.latticeEndPoints[cardinal][tier].append(bcp)

	#read lattices and cut planes
	for orientation in range(2):
		for pos in range(mayForm.segments[orientation] - 1):
			lattice = rs.GetUserText(metaDataHolder, "Lattice_" + str(orientation) + "_" + str(pos))
			mayForm.lattices[orientation].append(lattice)
	
	#read inner curves
	for orientation in range(2):
		for tier in range(TIERS_COUNT):
			mayForm.innerCurves[orientation].append([])
			for pos in range(mayForm.segments[orientation] - 1):
				innerCurve = rs.GetUserText(metaDataHolder, "Inner_Curve_" + str(orientation) + "_" + str(tier) + "_" + str(pos))
				mayForm.innerCurves[orientation][tier].append(innerCurve)

	#read border curves
	for cardinal in range(CARDINALS_COUNT):
		for tier in range(TIERS_COUNT):
			borderCurve = rs.GetUserText(metaDataHolder, "Border_Curve_" + str(cardinal) + "_" + str(tier))
			mayForm.borderCurves[cardinal].append(borderCurve)
	
	#read cutting planes
	for cardinal in range(CARDINALS_COUNT):
		cuttingPlane = rs.GetUserText(metaDataHolder, "Cutting_Plane_" + str(cardinal))
		mayForm.cuttingPlanes.append(cuttingPlane)
	
					
	#read faceplates
	for cardinal in range(CARDINALS_COUNT):
		for i in range(len(HIGH_END_LATTICES[getOrientation(cardinal)])):
			facePlate = rs.GetUserText(metaDataHolder, "Faceplate_" + str(cardinal) + "_" + str(i))
			mayForm.facePlates[cardinal].append(facePlate)
	
	#read triangles
	for cardinal in range(CARDINALS_COUNT):
		triangle = rs.GetUserText(metaDataHolder, "Triangle_" + str(cardinal))
		mayForm.triangles.append(triangle)
	
	return mayForm


def readCoversMetaData(mayForm, readInnerPoints = True):
	#cover ids
	dotObjects = rs.ObjectsByLayer("MF_29_CoverDots")
	coverMap = {}
	for target in dotObjects:
		u = int(rs.GetUserText(target, "U"))
		v = int(rs.GetUserText(target, "V"))
		mayCover = MayCover(u, v)
		mayCover.dot = target
		coverMap[str(u) + "_" + str(v)] = mayCover

		#read cover object
		coverObject = rs.GetUserText(target, "Cover_Object")
		mayCover.coverObject = coverObject
		coverObjectMoved = rs.GetUserText(target, "Cover_Object_Moved")
		mayCover.coverObjectMoved = coverObjectMoved

		for cardinal in range(CARDINALS_COUNT):
			#read outer points
			outerPoint = rs.GetUserText(target, "Outer_Point_" + str(cardinal))
			if outerPoint != "None":
				outerPoint = rs.PointCoordinates(outerPoint)
				mayCover.outerPoints[cardinal] = outerPoint
			#read border points
			borderPoint = rs.GetUserText(target, "Border_Point_" + str(cardinal))
			if borderPoint != "None":
				borderPoint = rs.PointCoordinates(borderPoint)
				mayCover.borderPoints[cardinal] = borderPoint

		#read inner points
		if readInnerPoints:
			for i in range(5):
				innerPoint = rs.GetUserText(target, "Inner_Point_" + str(i))
				if innerPoint and not innerPoint == "None":
					coords = rs.PointCoordinates(innerPoint)
					mayCover.innerPoints.append(coords)

	coversSorted = []
	for u in range(mayForm.segments[ORIENTATION_U]):
		coversSorted.append([])
		for v in range(mayForm.segments[ORIENTATION_V]):
			mayCover = coverMap.get(str(u) + "_" + str(v))
			if not mayCover:
				#create a placeholder instance
				mayCover = MayCover(u, v)
				mayCover.exists = False
			coversSorted[u].append(mayCover)
	return coversSorted
	

def makeLayers(layers):
	rs.CurrentLayer("Default")
	for layer in layers:
		if rs.IsLayer(layer): 
			rs.PurgeLayer(layer)
		rs.AddLayer(layer)
	rs.CurrentLayer(layers[0])


def trimCurveGuids(curve, p1Guid, p2Guid):
	p1Coords = rs.coercegeometry(p1Guid).Location
	p2Coords = rs.coercegeometry(p2Guid).Location
	return trimCurve(curve, p1Coords, p2Coords)


#cut a curve between the 2 specified points
def trimCurve(curve, p1Coords, p2Coords, doFlip=False):
	points = []
	points.append(rs.CurveClosestPoint(curve, p1Coords))
	points.append(rs.CurveClosestPoint(curve, p2Coords))
	if points[0] == points[1]: 
		return None
	flip = points[0] > points[1]
	if flip or doFlip: 
		points = points[::-1] #flip values
	trimmedCurve = rs.TrimCurve( curve, points, False)
	return [flip, trimmedCurve]
	
	
def plus4(i, j):
	i += j
	if i > 3: i -= 4
	return i
	
	
def getLargestPiece(pieces):
	maxSize = 0
	maxPiece = None
	for piece in pieces:
		#rs.SurfaceArea is very slow, compare the diagonals of the
		#bounding box instead
		box = rs.BoundingBox(piece)
		if not box: 
			print "Ups, no box!!!!"
			return piece #???
		size = rs.VectorLength(box[0]-box[6]) + rs.VectorLength(box[1]-box[7])
		if size > maxSize:
			 maxSize = size
			 maxPiece = piece
	return maxPiece


#re-implementation of SplitBrep() because this has a lot of issues...
#1.) allow to set a custom toleranc
#2.) deletePbject does not work properly
#3.) Return just the largest object
def cutInsets(brepId, cutterId):
	dotCount = rs.GetUserText(brepId, "Dot_Marker_Count")
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
	
	if dotCount:
		rs.SetUserText(newBrep, "Dot_Marker_Count", dotCount)
		for i in range(int(dotCount)):
			dotText = rs.GetUserText(brepId, "Dot_Marker_" + str(i)) 
			rs.SetUserText(newBrep, "Dot_Marker_" + str(i), str(dotText))
			
	
	
	dotCount1 = rs.GetUserText(newBrep, "Dot_Marker_Count")
	if dotCount1:
		for i in range(int(dotCount1)):
			dotText = rs.GetUserText(newBrep, "Dot_Marker_" + str(i)) 
			a=1
	
	rs.DeleteObject(brepId)
	rs.GetUserText
	scriptcontext.doc.Views.Redraw()
	
	return str(newBrep)


#flatten a polyline into the middle plane
def flattenPolyline(polyline, p1, p2, p3, p4):
	origin = (p1 + p2 + p3 + p4) / 4
	xPoint1 = (p3 + p2) / 2
	xPoint2 = (p4 + p1) / 2
	yPoint1 = (p3 + p4) / 2
	yPoint2 = (p1 + p2) / 2		
	xaxis = rs.VectorUnitize(xPoint1 - xPoint2)
	yaxis = rs.VectorUnitize(yPoint1 - yPoint2)	
	plane = rs.PlaneFromFrame(origin, xaxis, yaxis)
	xform = rs.XformPlanarProjection(plane)
	flatPolyline = rs.TransformObjects(polyline, xform)
	return flatPolyline


#flatten a polyline into the middle plane
def flattenPolyline3(polyline, origin, xAxis, yAxis):
	plane = rs.PlaneFromFrame(origin, xAxis, yAxis)
	xform = rs.XformPlanarProjection(plane)
	flatPolyline = rs.TransformObjects(polyline, xform)
	return flatPolyline


#orientation is north-south (=0) or west-east (=1)  
def getOrientation(cardinal):
	if cardinal == 0: return 0
	if cardinal == 1: return 1
	if cardinal == 2: return 0
	if cardinal == 3: return 1


#convert from C# objects (PanelingTool) to regular python objects
def convertToArrayPoint3d(points):
	pArray = System.Array.CreateInstance(Rhino.Geometry.Point3d, len(points))
	arrPoints = List[System.Array[Point3d]]([pArray])
	for i in range(len(points)):
		pArray[i] = rs.coerce3dpoint(points[i])
	return arrPoints


#orientation is north-south (=0) or west-east (=1)  
def getCardinalShortname(cardinalId):
	if cardinalId == 0: return "N"
	if cardinalId == 1: return "W"
	if cardinalId == 2: return "S"
	if cardinalId == 3: return "E"


def getNormalLine(mayForm, cardinal, pos1, pos2, tier1, tier2):
	points = []
	points.append(mayForm.latticeEndPoints[cardinal][tier2][pos1])
	points.append(mayForm.latticeEndPoints[cardinal][tier1][pos1])
	points.append(mayForm.latticeEndPoints[cardinal][tier1][pos2])
	points.append(mayForm.latticeEndPoints[cardinal][tier2][pos2])
	points.append(mayForm.latticeEndPoints[cardinal][tier2][pos1])
	points = [rs.coercegeometry(point).Location for point in points]
	
	polyline = rs.AddPolyline(points)
	flatPolyline = flattenPolyline(polyline, points[0], points[1], points[2], points[3])[0]
	normal = rs.CurveNormal(flatPolyline)
	rs.DeleteObject(polyline)
	
	normal = rs.VectorScale(normal, 100)
	centerPoint = ( points[0] + points[1] + points[2] + points[3]) / 4
	point1 = rs.PointAdd(centerPoint, normal)
	point2 = rs.PointAdd(centerPoint, -normal)
	line = rs.AddLine(point1, point2)
	return line	
	
	
def addMarkerDot(targetObject, text, position, layer):
	maxCounter = rs.GetUserText(targetObject, "Dot_Marker_Count")
	if maxCounter:
		maxCounter = int(maxCounter)
	else:
		maxCounter = 0
	dotText = rs.AddTextDot(text, position)
	rs.ObjectLayer(dotText, layer)
	rs.SetUserText(targetObject, "Dot_Marker_" + str(maxCounter), str(dotText))
	rs.SetUserText(targetObject, "Dot_Marker_Count", str(maxCounter + 1))


def convertMarkerDot(dotMarker, workId):
	p = rs.TextDotPoint(dotMarker)
	coords = [p[0], p[1], 0]
	t = rs.TextDotText(dotMarker)
	if t.startswith("D"):
		diameter = int(t[1:])
		o = rs.AddCircle(coords, diameter/2)
		rs.ObjectLayer(o, "MF_" + workId + "_Circles")
	elif t.startswith("T"):
		o = rs.AddText(t[1:], coords, 5, 'Arial', 0, 131074)
		rs.ObjectLayer(o, "MF_" + workId + "_Texts")
	elif t.startswith("M"):
		#MAYFORMS logo
		o = rs.AddText(t[1:], coords, 10, 'Verdana', 0, 131074)
		rs.ObjectLayer(o, "MF_" + workId + "_Texts")
	rs.DeleteObject(dotMarker)
	return o

	
def isHighEndLattice(orientation, pos):
	highEnds = HIGH_END_LATTICES[orientation]
	for i in highEnds:
		if i == pos: return True
		if i + 1 == pos: return True
	return False


def isPointCloseToObject(surface, testPoint):
	testPoint = rs.PointCoordinates(testPoint)
	otherPoint = rs.BrepClosestPoint(surface, testPoint)[0]
	distance = rs.Distance(testPoint, otherPoint)
	return distance < 0.2


def isOnCurve(curve, point):
	if not point: 
		return False
	param = rs.CurveClosestPoint(curve, point)
	p = rs.EvaluateCurve(curve, param)
	distance = rs.Distance(p, point)
	return distance < 0.2

	
def getCrossOrientation(orientation):
	return 1 if orientation == 0 or orientation == 2 else 0


def assertNone(actualValue):
	if actualValue:
		raise Exception("Value is not None: " + str(actualValue))


def assertEquals(actualValue, expectedValue):
	if not actualValue == expectedValue:
		raise Exception("Value are not equals: " + str(actualValue) + " != " + str(expectedValue))


def getFarthestEndPoint(curve, point, lattice):
	dist1 = rs.Distance(rs.CurveStartPoint(curve), point)
	dist2 = rs.Distance(rs.CurveEndPoint(curve), point)
	if dist1 < dist2:
		farthestEndPoint = rs.CurveEndPoint(curve)
	else: 
		farthestEndPoint = rs.CurveStartPoint(curve)
	return farthestEndPoint


def getClosestEndPoint(curve, point, lattice):
	dist1 = rs.Distance(rs.CurveStartPoint(curve), point)
	dist2 = rs.Distance(rs.CurveEndPoint(curve), point)
	if dist1 < dist2:
		closestEndPoint = rs.CurveEndPoint(curve)
	else: 
		closestEndPoint = rs.CurveStartPoint(curve)
	return closestEndPoint