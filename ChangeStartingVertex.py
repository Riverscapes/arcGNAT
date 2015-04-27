# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Change Starting Vertex Tool                                    #
# Purpose:     Changes the First Vertex in a polygon(s) based on an           #
#              intersecting point(s).                                         #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     1.1                                                            #
# Modified:    2015-Jan-08                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
#import gis_tools

# # Main Function # #
def main(fcInputPoints,
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

# # Run as Script # #
if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2])