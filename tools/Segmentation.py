# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        GNAT Segmentation Tool                                         #
# Purpose:     Segment the Stream Network using distance Intervals            #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Sept-15                                                   #
# Version:     2.1                                                            #
# Modified:    2018-Feb-6                                                     #
#                                                                             #
# Copyright:   (c) Kelly Whitehead, Jesse Langdon                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import os
import arcpy
from tools.FCT import def__SLEM as dS
from lib import ClearInMemory, gis_tools
from decimal import *

listStrSegMethod = ["Remaining segment at inflow (top) of stream branch",
                    "Remaining segment at outflow (bottom) of stream branch",
                    "Divide remainder between all reaches per stream branch"]

# Set environmental variables
arcpy.env.outputMFlag = "Disabled"
arcpy.env.outputZFlag = "Disabled"
arcpy.env.overwriteOutput = True


def getNetworkNodes(inStreamNetwork, scratchWorkspace="in_memory"):
    # Preprocess network
    fcNetworkDissolved = gis_tools.newGISDataset(scratchWorkspace, "GNAT_SO_NetworkDissolved")
    arcpy.Dissolve_management(inStreamNetwork, fcNetworkDissolved, multi_part="SINGLE_PART",
                              unsplit_lines="DISSOLVE_LINES")

    fcNetworkIntersectPoints = gis_tools.newGISDataset(scratchWorkspace, "GNAT_SO_NetworkIntersectPoints")
    arcpy.Intersect_analysis(fcNetworkDissolved, fcNetworkIntersectPoints, "ALL", output_type="POINT")
    arcpy.AddXY_management(fcNetworkIntersectPoints)
    fcNetworkNodes = gis_tools.newGISDataset(scratchWorkspace, "GNAT_SO_NetworkNodes")
    arcpy.Dissolve_management(fcNetworkIntersectPoints, fcNetworkNodes, ["POINT_X", "POINT_Y"], "#", "SINGLE_PART")
    del fcNetworkDissolved
    del fcNetworkIntersectPoints
    return fcNetworkNodes

def cleanLineGeom(inLine, streamID, segID, lineClusterTolerance):
    lyrs = []
    inLineName = arcpy.Describe(inLine).name
    oidFieldName = arcpy.Describe(inLine).oidFieldName

    # Add new field to store field length values (replaces the "Shape_Length" or "Shape_Leng" fields)
    arcpy.AddField_management(inLine, "SegLen", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED")
    arcpy.CalculateField_management(inLine, "SegLen", "!shape.length@meters!", "PYTHON_9.3")

    # Separate short and long lines into different layers, then select all longs that touch shorts
    shortLines = arcpy.MakeFeatureLayer_management(inLine, 'shortLines', "SegLen" + ' <= ' + str(lineClusterTolerance))
    lyrs.append(shortLines)
    longLines = arcpy.MakeFeatureLayer_management(inLine, 'longLines', "SegLen" + ' > ' + str(lineClusterTolerance))
    lyrs.append(longLines)
    arcpy.SelectLayerByLocation_management(longLines, "BOUNDARY_TOUCHES", shortLines, '', "NEW_SELECTION")

    # Make a dictionary relating shortLine streamID/segID pairs to their origin- and endpoint coordinate pairs
    shortDict = {}
    rows = arcpy.SearchCursor(shortLines)
    for row in rows:
        shp = row.Shape
        shortDict[(row.getValue(streamID), row.getValue(segID))] = [(shp.firstPoint.X, shp.firstPoint.Y),
                                                                    (shp.lastPoint.X, shp.lastPoint.Y)]
    del rows

    # Make a dictionary relating longLine origin and endpoint coordinate pairs to segID values.
    longDict = {}
    rows = arcpy.SearchCursor(longLines)
    for row in rows:
        shp = row.Shape
        firstCoords = (shp.firstPoint.X, shp.firstPoint.Y)
        lastCoords = (shp.lastPoint.X, shp.lastPoint.Y)
        longDict[firstCoords] = (row.getValue(streamID), row.getValue(segID))
        longDict[lastCoords] = (row.getValue(streamID), row.getValue(segID))
    del rows

    # Create new dictionary relating shortLine segIDs to longLine segIDs that share a point
    dissolveDict = {}
    # If a shortLine's coordinate pair matches an entry in longDict, and the longLine's streamID matches,
    # add their segIDs to dissolveDict
    for ids, coordPairs in shortDict.iteritems():
        for coords in [coordPairs[0], coordPairs[1]]:
            if coords in longDict.iterkeys():
                if longDict[coords][0] == ids[0]:
                    dissolveDict[ids[1]] = longDict[coords][1]

    # Give all longLines a 'dissolve' value equal to their segID
    arcpy.AddField_management(inLine, 'dissolve', 'LONG')
    arcpy.SelectLayerByAttribute_management(longLines, "CLEAR_SELECTION")
    # arcpy.CalculateField_management(longLines,'dissolve','[{0}]'.format(segID),'VB')
    arcpy.CalculateField_management(longLines, 'dissolve', "!" + segID + "!", 'Python_9.3')

    # If shortLine in dissolveDict, give it a 'dissolve' value equal to the dissolveDict value,
    # otherwise give it its own segID value.
    urows = arcpy.UpdateCursor(shortLines, '', '', segID + ';dissolve')
    for urow in urows:
        if dissolveDict.get(urow.getValue(segID)):
            urow.dissolve = dissolveDict[urow.getValue(segID)]
        else:
            urow.dissolve = urow.getValue(segID)
        urows.updateRow(urow)
    del urows

    arcpy.Dissolve_management(inLine, r'in_memory\seg_clean', 'dissolve', '', 'MULTI_PART')
    cleaned = arcpy.JoinField_management(r'in_memory\seg_clean', 'dissolve', inLine, segID, [segID, streamID])
    arcpy.DeleteField_management(cleaned, 'dissolve')

    return cleaned


def segOptionA(in_hydro, seg_length, outFGB, outSegmentIDField="SegmentID", scratchWorkspace="in_memory"):
    """Segment the input stream network feature class using 'remainder at inflow of reach' method."""
    arcpy.AddMessage("Segmenting process using the remainder at stream branch inflow method...")
    DeleteTF = "true"

    # Segmentation of the polyline using module from Fluvial Corridors toolbox.
    splitLine = dS.SLEM(in_hydro, seg_length, scratchWorkspace + r"\splitLine", DeleteTF)

    outSort = scratchWorkspace + r"\segments_sort"
    arcpy.Sort_management(splitLine, outSort, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])

    arcpy.AddField_management(outSort, "Rank_DGO", "LONG", "", "", "", "","NULLABLE", "NON_REQUIRED")
    fieldname = [f.name for f in arcpy.ListFields(outSort)]
    arcpy.CalculateField_management(outSort, "Rank_DGO", "!" + str(fieldname[0]) + "!", "PYTHON_9.3")

    # Merges adjacent stream segments if less than 75% length threshold.
    clusterTolerance = float(seg_length) * 0.25
    clean_stream = cleanLineGeom(outSort, "Rank_UGO", "Rank_DGO", clusterTolerance)
    arcpy.AddField_management(clean_stream, outSegmentIDField, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED")
    arcpy.CalculateField_management(clean_stream, outSegmentIDField, '"!OBJECTID!"', "PYTHON_9.3")
    arcpy.DeleteField_management(clean_stream, "Rank_UGO")
    arcpy.DeleteField_management(clean_stream, "Rank_DGO")

    # Clean up
    del splitLine
    del outSort

    return clean_stream


def segOptionBC(fcDissolvedStreamBranch,
         inputDistance,
         segMethod,
         fcTempStreamNetwork=r"in_memory\temp_network",
         outSegmentIDField="SegmentID",
         scratchWorkspace=r"in_memory"):
    """Segment the input stream network feature class using one of two methods:

    1. Remainder at the outflow of each stream reach
    2. Remainder is divided amongst each stream segment
    """

    gis_tools.resetData(fcTempStreamNetwork)
    listPoints = []

    if segMethod == "Remaining segment at outflow (bottom) of stream branch":
        arcpy.AddMessage("Segmenting using the remainder at stream branch outflow method...")
    else:
        arcpy.AddMessage("Segmenting using the segment remainder division method...")

    with arcpy.da.SearchCursor(fcDissolvedStreamBranch,["SHAPE@","SHAPE@LENGTH"]) as scBranches:
        for row in scBranches:
            gLine = row[0]
            dblPointPosition = 0
            if segMethod == "Remaining segment at outflow (bottom) of stream branch":
                while dblPointPosition < row[1]:
                    listPoints.append(gLine.positionAlongLine(dblPointPosition))
                    dblPointPosition += Decimal(inputDistance)
            else:
                intNumberOfPositions = int(Decimal(row[1])/Decimal(inputDistance))
                for intPosition in range(intNumberOfPositions):
                    
                    dblProportionalPosition = float(intPosition)/intNumberOfPositions
                    listPoints.append(gLine.positionAlongLine(dblProportionalPosition,True))

    fcSplitPoints = gis_tools.newGISDataset(scratchWorkspace, "GNAT_SEG_SplitPoints")
    arcpy.CreateFeatureclass_management(scratchWorkspace,"GNAT_SEG_SplitPoints","POINT",spatial_reference=fcDissolvedStreamBranch)

    with arcpy.da.InsertCursor(fcSplitPoints,["SHAPE@"]) as icSplitPoints:
        for point in listPoints:
            icSplitPoints.insertRow([point])
    arcpy.SplitLineAtPoint_management(fcDissolvedStreamBranch,fcSplitPoints,fcTempStreamNetwork,"1 Meters")
    gis_tools.addUniqueIDField(fcTempStreamNetwork, outSegmentIDField)

    # Remove unnecessary fields
    fieldObjects = arcpy.ListFields(fcTempStreamNetwork)
    oidField = arcpy.Describe(fcTempStreamNetwork).OIDFieldName
    shapeField = arcpy.Describe(fcTempStreamNetwork).shapeFieldName
    lengthField = arcpy.Describe(fcTempStreamNetwork).lengthFieldName
    keepFields = [oidField, shapeField, lengthField, outSegmentIDField]
    for field in fieldObjects:
        if field.name not in keepFields:
            arcpy.DeleteField_management(fcTempStreamNetwork, [field.name])

    # Clean up
    del fcSplitPoints

    return fcTempStreamNetwork


# # Main Function # #
def main(inputFCStreamNetwork, inputDistance, strmIndex, segMethod, boolNode, boolMerge, outputFCSegments):
    """Segment a stream network into user-defined length intervals."""

    # Get output workspace from output feature class
    out_wspace = os.path.dirname(outputFCSegments)

    # process terminates if input requirements not met
    gis_tools.checkReq(inputFCStreamNetwork)

    lyrStreamNetwork = gis_tools.newGISDataset("LAYER", "GNAT_SEGMENT_StreamNetwork")
    arcpy.MakeFeatureLayer_management(inputFCStreamNetwork, lyrStreamNetwork)

    strm_nodes = getNetworkNodes(lyrStreamNetwork)
    strm_dslv = r"in_memory\strm_dslv"
    arcpy.Dissolve_management(lyrStreamNetwork, strm_dslv, "BranchID", "", "SINGLE_PART", "DISSOLVE_LINES")

    # Split dissolved network at intersection nodes before segmentation, if option is chosen by user
    if boolNode == "true":
        strm_split_node = r"in_memory\strm_split_node"
        arcpy.SplitLineAtPoint_management(strm_dslv, strm_nodes, strm_split_node, "0.0001 Meters")
    else:
        strm_split_node = strm_dslv

    # Segment using method with remainder at inflow of each stream reach (i.e. Jesse's method)
    if segMethod == "Remaining segment at inflow (top) of stream branch":
        strm_seg = segOptionA(strm_split_node, inputDistance, out_wspace)
    # Segment using method with remainder at outflow, or divided remainder (i.e. Kelly's method)
    else:
        strm_seg = segOptionBC(strm_split_node, inputDistance, segMethod)

    if boolMerge == 'true':
        arcpy.AddMessage("Merging attributes and geometry from " + inputFCStreamNetwork + " with segmented stream network...")
        arcpy.Intersect_analysis([inputFCStreamNetwork, strm_seg], outputFCSegments)
    else:
        arcpy.CopyFeatures_management(strm_seg, outputFCSegments)

    # Finalize the process
    ClearInMemory.main()
    arcpy.AddMessage("GNAT: Segmentation process complete!")

    return
