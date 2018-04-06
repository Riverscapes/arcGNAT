# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Geometry Functions Module                                      #
# Purpose:     Support components for GNAT                                    #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Aug-27                                                   #
# Version:     1.3                                                            #
# Modified:    2015-Aug-12                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import math
import arcpy
import gis_tools

def rotateFeatures(inFeatureClass,outFeatureClass,angle=0,units="DEGREES",anchor="CENTROID"):

    with arcpy.da.SearchCursor(inFeatureClass,["SHAPE@","SHAPE@XY","CandidateID"]) as scRotateFC:
        with arcpy.da.InsertCursor(outFeatureClass,["SHAPE@","CandidateID","Angle"]) as icRotatedFC:
            for feature in scRotateFC:
                newShapeArray = arcpy.Array()
                for part in feature[0]:
                    newPartArray = arcpy.Array()
                    for point in part:
                        newx,newy = rotatePoint(point.X,point.Y,feature[1][0],feature[1][1],angle)
                        newPartArray.add(arcpy.Point(newx,newy))
                    newShapeArray.add(newPartArray)
                icRotatedFC.insertRow([arcpy.Polyline(newShapeArray),scRotateFC[2],angle])
    
    return

def rotatePoint(x,y,xc=0,yc=0,angle=0,units="DEGREES"):
    #import math
    x = x-xc
    y = y-yc

    angle = angle * -1
    if units == "DEGREES":
        angle = math.radians(angle)

    xr = (x * math.cos(angle)) - (y * math.sin(angle)) + xc
    yr = (x * math.sin(angle)) + (y * math.cos(angle)) + yc
    
    return xr,yr

def calculatePerpendicularAngles(inputFeatureClass,outputFCLines,angleField,maxDistance,fieldID):
    
    #tempPoints = "in_memory\\TempPoints" #C:\\GIS\\StreamNetworkConfinementOutputGeodatabase01.gdb
    fcAngleLines0 = "in_memory\\Angle0"
    fcAngleLines180 = "in_memory\\Angle180"
    fcAngleMerge = "in_memory\\AngleMerge"

    #resetData(tempPoints)
    #arcpy.CopyFeatures_management(inputFeatureClass,tempPoints)
    arcpy.AddField_management(inputFeatureClass,"Angle0","Double")
    arcpy.AddField_management(inputFeatureClass,"Angle180","Double")
    arcpy.AddField_management(inputFeatureClass,"AngleDistance","Double")

    arcpy.CalculateField_management(inputFeatureClass,"Angle0","( !" + angleField + "! - 90 )*(-1)","PYTHON")
    arcpy.CalculateField_management(inputFeatureClass,"Angle180","!Angle0!+180","PYTHON")  
    arcpy.CalculateField_management(inputFeatureClass,"AngleDistance",str(maxDistance/2),"PYTHON")

    #arcpy.AddXY_management(inputFeatureClass)
    
    resetData(fcAngleLines0)
    resetData(fcAngleLines180)
    arcpy.BearingDistanceToLine_management(inputFeatureClass,fcAngleLines0,"POINT_X","POINT_Y","AngleDistance","#","Angle0","DEGREES","GEODESIC",fieldID)
    arcpy.BearingDistanceToLine_management(inputFeatureClass,fcAngleLines180,"POINT_X","POINT_Y","AngleDistance","#","Angle180","DEGREES","GEODESIC",fieldID)
    
    resetData(fcAngleMerge)
    arcpy.Merge_management([fcAngleLines180,fcAngleLines0],fcAngleMerge)

    resetData(outputFCLines)
    arcpy.UnsplitLine_management(fcAngleMerge,outputFCLines,fieldID)
    
    return

def findSegmentJunctions(inputFCCenterline,strOutputJunctionPointsFC,strType="TRIBS"):

    scratchWorkspace = arcpy.env.scratchWorkspace

    tempfcDanglePoints = newGISDataset(scratchWorkspace,"GISTOOLS_DanglePoints")
    arcpy.FeatureVerticesToPoints_management(inputFCCenterline,tempfcDanglePoints,"DANGLE")

    mergeList=[]
    
    if strType == "SEGMENTS" or strType == "ALL":   
        tempfcSegmentBothEndPoints = newGISDataset(scratchWorkspace,"GISTOOLS_SegmentBothEndPoints")
        arcpy.FeatureVerticesToPoints_management(inputFCCenterline,tempfcSegmentBothEndPoints,"BOTH_ENDS")

        lyrSegmentBothEndPoints = newGISDataset("Layer","lyrSegmentBothEndPoints")
        arcpy.MakeFeatureLayer_management(tempfcSegmentBothEndPoints,lyrSegmentBothEndPoints)

        arcpy.SelectLayerByLocation_management(lyrSegmentBothEndPoints,"INTERSECT",tempfcDanglePoints,selection_type="NEW_SELECTION")
        arcpy.SelectLayerByAttribute_management(lyrSegmentBothEndPoints,"SWITCH_SELECTION")

        mergeList.append(lyrSegmentBothEndPoints)

    if strType == "TRIBS" or strType == "ALL":
        tempfcDissolvedCenterline = newGISDataset(scratchWorkspace,"GISTOOLS_CenterlineDissolved")
        arcpy.Dissolve_management(inputFCCenterline,tempfcDissolvedCenterline,multi_part="MULTI_PART",unsplit_lines="UNSPLIT_LINES")
        tempfcMPtoSPCenterline = newGISDataset(scratchWorkspace,"GISTOOLS_CenterlineMPtoSP")
        arcpy.MultipartToSinglepart_management(tempfcDissolvedCenterline,tempfcMPtoSPCenterline)
    
        tempfcTribBothEndPoints = newGISDataset(scratchWorkspace,"GISTOOLS_BothEndPoints")
        arcpy.FeatureVerticesToPoints_management(tempfcMPtoSPCenterline,tempfcTribBothEndPoints,"BOTH_ENDS")
    
        lyrTribBothEndPoints = newGISDataset("Layer","lyrTribBothEndPoints")
        arcpy.MakeFeatureLayer_management(tempfcTribBothEndPoints,lyrTribBothEndPoints)

        arcpy.SelectLayerByLocation_management(lyrTribBothEndPoints,"INTERSECT",tempfcDanglePoints,selection_type="NEW_SELECTION")
        arcpy.SelectLayerByAttribute_management(lyrTribBothEndPoints,"SWITCH_SELECTION")

        mergeList.append(lyrTribBothEndPoints)

    if strType == "ALL":
        lyrDanglePoints = newGISDataset("Layer","lyrDanglePoints")
        arcpy.MakeFeatureLayer_management(tempfcDanglePoints,lyrDanglePoints)

        mergeList.append(lyrDanglePoints)

    arcpy.Merge_management(mergeList,strOutputJunctionPointsFC)

    return strOutputJunctionPointsFC

def pointsAlongLine(fcInputLineNetwork,
                    dblDistance,
                    fcOutputPoints):
    """Generate Points along a line network.

    Generate a series of point along a line network based on a specified 
    distance or specified number of points (equally spaced). If set distance 
    is used, the last section (remainder) will be smaller than the set 
    distance. For this reason, line direction is important. 

    Points at the ends of the lines are also included.

    Arguments:
    fcInputLineNetwork -- line network to generate points along. This should be
    dissolved as needed, since this tool will generate a new set of points per
    line feature.
    inDistanceOrNumberofPoints -- the distance or number of points to use.
    """

    resetData(fcOutputPoints)

    arrayNewPoints = []
    arrayAttributes = []
    with arcpy.da.SearchCursor(fcInputLineNetwork,["OID@","SHAPE@","SHAPE@LENGTH"]) as scLineNetwork:
        for line in scLineNetwork:
            lineFeat = line[1]
            lengthCurrent = 0
            pointPosition = 0
            while lengthCurrent < line[2]:
                arrayNewPoints.append(lineFeat.positionAlongLine(lengthCurrent))
                arrayAttributes.append([line[0],pointPosition])
                lengthCurrent = lengthCurrent + dblDistance
                pointPosition = pointPosition + 1

            arrayNewPoints.append(arcpy.PointGeometry(lineFeat.lastPoint))
            arrayAttributes.append([line[0],pointPosition])

    arcpy.CopyFeatures_management(arrayNewPoints,fcOutputPoints)

    arcpy.AddField_management(fcOutputPoints,"LineID","LONG")
    arcpy.AddField_management(fcOutputPoints,"Position","LONG")

    with arcpy.da.UpdateCursor(fcOutputPoints,["LineID","Position"]) as ucOutputPoints:
        i = 0
        for row in ucOutputPoints:
            row[0] = arrayAttributes[i][0]
            row[1] = arrayAttributes[i][1]
            ucOutputPoints.updateRow(row)
            i=i+1

    return arrayAttributes

def changeStartingVertex(fcInputPoints,
                         fcInputPolygons):
    
    ## Create Geometry Object for Processing input points.
    g = arcpy.Geometry()
    geomPoints = arcpy.CopyFeatures_management(fcInputPoints,g)

    listPointCoords = []
    for point in geomPoints:
        listPointCoords.append([point.centroid.X,point.centroid.Y])
        #arcpy.AddMessage(str(point.centroid.X) + ","+ str(point.centroid.Y))

    with arcpy.da.UpdateCursor(fcInputPolygons,["OID@", "SHAPE@"]) as ucPolygons:
        for featPolygon in ucPolygons:
            vertexList = []
            #arcpy.AddMessage("Feature: " + str(featPolygon[0]))
            i = 0
            iStart = 0
            for polygonVertex in featPolygon[1].getPart(0): # shape,firstpart
                if polygonVertex:
                    #arcpy.AddMessage(' Vertex:' + str(i))
                    vertexList.append([polygonVertex.X,polygonVertex.Y])
                    if [polygonVertex.X,polygonVertex.Y] in listPointCoords:
                        #arcpy.AddMessage("  Point-Vertex Match!")
                        iStart = i
                    else:
                        pass
                        #arcpy.AddMessage("  No Match")
                i = i + 1
            if iStart == 0:
                newVertexList = vertexList
                #arcpy.AddMessage("No Change for: " + str(featPolygon[0]))
            else:
                #arcpy.AddMessage("Changing Vertex List for: " + str(featPolygon[0]))
                newVertexList = vertexList[iStart:i]+vertexList[0:iStart]
                for v in newVertexList:
                    arcpy.AddMessage(str(v[0]) + "," +str(v[1]))
                #listVertexPointObjects = []
                newShapeArray = arcpy.Array()
                for newVertex in newVertexList:
                    #arcpy.AddMessage("Changing Vertex: " + str(newVertex[0]) + ',' + str(newVertex[1]))
                    newShapeArray.add(arcpy.Point(newVertex[0],newVertex[1]))
                    #listVertexPointObjects.append(arcpy.Point(newVertex[0],newVertex[1]))
                #newShapeArray = arcpy.Array(listVertexPointObjects)
                newPolygonArray = arcpy.Polygon(newShapeArray)

                ucPolygons.updateRow([featPolygon[0],newPolygonArray])

    return