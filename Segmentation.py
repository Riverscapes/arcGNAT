﻿# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        GNAT Segmentation Tool                                         #
# Purpose:     Segment the Stream Network using distance Intervals            #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Sept-15                                                    #
# Version:     1.3                                                            #
# Modified:    2015-Sept-15                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import os
import arcpy
import gis_tools
import def__SLEM as dS
import ClearInMemory
import StreamOrder
import GenerateStreamBranches
from decimal import *

listStrSegMethod = ["Remaining segment at inflow (top) of stream branch",
                    "Remaining segment at outflow (bottom) of stream branch",
                    "Divide remainder between all reaches per stream branch"]


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


def segOptionA(in_hydro, seg_length, outFGB):
    """Segment the input stream network feature class using 'remainder at inflow of reach' method."""
    arcpy.AddMessage("Segmenting process using the remainder at stream branch inflow method...")
    DeleteTF = "true"

    # Segmentation of the polyline using module from Fluvial Corridors toolbox.
    splitLine = dS.SLEM(in_hydro, seg_length, r"in_memory\splitLine", DeleteTF)

    outSort = r"in_memory\segments_sort"
    arcpy.Sort_management(splitLine, outSort, [["Rank_UGO", "ASCENDING"], ["Distance", "ASCENDING"]])

    arcpy.AddField_management(outSort, "Rank_DGO", "LONG", "", "", "", "","NULLABLE", "NON_REQUIRED")
    fieldname = [f.name for f in arcpy.ListFields(outSort)]
    arcpy.CalculateField_management(outSort, "Rank_DGO", "!" + str(fieldname[0]) + "!", "PYTHON_9.3")

    # Merges adjacent stream segments if less than 75% length threshold.
    clusterTolerance = float(seg_length) * 0.25
    clean_stream = cleanLineGeom(outSort, "Rank_UGO", "Rank_DGO", clusterTolerance)
    arcpy.AddField_management(clean_stream, "LineOID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED")
    arcpy.CalculateField_management(clean_stream, "LineOID", '"!OBJECTID!"', "PYTHON_9.3")
    arcpy.DeleteField_management(clean_stream, "Rank_UGO")
    arcpy.DeleteField_management(clean_stream, "Rank_DGO")

    return clean_stream


def segOptionBC(fcDissolvedStreamBranch,
         inputDistance,
         segMethod,
         fcOutputStreamNetwork,
         outputSegmentIDField="LineOID",
         scratchWorkspace=r"in_memory"):
    """Segment the input stream network feature class using one of two methods:

    1. Remainder at the outflow of each stream reach
    2. Remainder is divided amongst each stream segment
    """

    gis_tools.resetData(fcOutputStreamNetwork)
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
                    #arcpy.AddMessage(" Position: " + str(intPosition) + " of " + str(intNumberOfPositions) + " | " + str(dblProportionalPosition))
                    listPoints.append(gLine.positionAlongLine(dblProportionalPosition,True))

    fcSplitPoints = gis_tools.newGISDataset(scratchWorkspace,"GNAT_SEG_SplitPoints")
    arcpy.CreateFeatureclass_management(scratchWorkspace,"GNAT_SEG_SplitPoints","POINT",spatial_reference=fcDissolvedStreamBranch)

    with arcpy.da.InsertCursor(fcSplitPoints,["SHAPE@"]) as icSplitPoints:
        for point in listPoints:
            icSplitPoints.insertRow([point])
    arcpy.SplitLineAtPoint_management(fcDissolvedStreamBranch,fcSplitPoints,fcOutputStreamNetwork,"1 Meters")
    gis_tools.addUniqueIDField(fcOutputStreamNetwork,outputSegmentIDField)

    # Remove unnecessary fields
    fieldObjects = arcpy.ListFields(fcOutputStreamNetwork)
    oidField = arcpy.Describe(fcOutputStreamNetwork).OIDFieldName
    shapeField = arcpy.Describe(fcOutputStreamNetwork).shapeFieldName
    lengthField = arcpy.Describe(fcOutputStreamNetwork).lengthFieldName
    keepFields = [oidField, shapeField, lengthField, "LineOID"]
    for field in fieldObjects:
        if field.name not in keepFields:
            arcpy.DeleteField_management(fcOutputStreamNetwork, [field.name])

    return fcOutputStreamNetwork


# # Main Function # #
def main(inputFCStreamNetwork, inputDistance, reachID, strmIndex, segMethod, outputFCSegments):
    """Segment a stream network into user-defined length intervals."""

    # Get output workspace from output feature class
    outFGB = os.path.dirname(outputFCSegments)
    outFile = os.path.basename(outputFCSegments)

    # Data pre-processing, includes calculating stream order and branch ID using GNAT modules
    spatial_join_fc = r"in_memory\spatial_join_fc"
    strm_order_fc_out = outFGB + r"\strm_order"
    strm_junc_fc_out = outFGB + r"\strm_junctions"
    strm_branch_fc_out = outFGB + r"\strm_branch"
    strm_order_fc_lyr = "strm_order_fc_lyr"
    strm_branch_fc_lyr = "strm_branch_fc_lyr"
    spatial_join_fc_lyr = "spatial_join_fc_lyr"

    # TODO The stream ordering and branching process should be placed in a try/except structure to trap '99999' errors
    strm_order_fc, junctions_fc = StreamOrder.main(inputFCStreamNetwork, reachID, strm_order_fc_out, strm_junc_fc_out)
    strm_branch_fc = GenerateStreamBranches.main(strm_order_fc, junctions_fc, strmIndex,
                                 "Stream_Order", strm_branch_fc_out, "true", "in_memory")
    arcpy.MakeFeatureLayer_management(strm_order_fc, strm_order_fc_lyr)
    arcpy.MakeFeatureLayer_management(strm_branch_fc, strm_branch_fc_lyr)

    # Field mapping for the spatial join
    fms = arcpy.FieldMappings()
    fms.addTable(strm_order_fc)
    fms.addTable(strm_branch_fc)

    # Join the branch ID output back to the stream order output feature class
    arcpy.SpatialJoin_analysis(strm_order_fc, strm_branch_fc, spatial_join_fc,
                               "JOIN_ONE_TO_ONE", "KEEP_ALL", fms, "HAVE_THEIR_CENTER_IN")
    arcpy.MakeFeatureLayer_management(spatial_join_fc, spatial_join_fc_lyr)
    strm_dslv = r"in_memory\strm_dslv"
    arcpy.Dissolve_management(spatial_join_fc_lyr, strm_dslv, "BranchID", "", "SINGLE_PART", "DISSOLVE_LINES")

    # Segment using method with remainder at inflow of each stream reach (i.e. Jesse's method)
    if segMethod == "Remaining segment at outflow (bottom) of stream branch":
        strm_seg = segOptionA(strm_dslv, inputDistance, outFGB)
        arcpy.FeatureClassToFeatureClass_conversion(strm_seg, outFGB, outFile)
    # Segment using method with remainder at outflow, or divided remainder (i.e. Kelly's method)
    else:
        strm_seg = segOptionBC(strm_dslv, inputDistance, segMethod, outputFCSegments)

    # Finalize the process
    ClearInMemory.main()
    arcpy.AddMessage("Segmentation process complete!")


# # TESTING
# inputFCStreamNetwork = r"C:\JL\Testing\GNAT\Segmentation_Refactor\lemhi\strm_network_huc6.shp"
# inputDistance = 200
# reachID = 13
# strmIndex = "GNIS_Name"
# segMethod = r"Divide remainder proportionally between reaches"
# outputFCSegments = r"C:\JL\Testing\GNAT\Segmentation_Refactor\lemhi\lemhi.gdb\segments_optionC"
#
# main(inputFCStreamNetwork, inputDistance, reachID, strmIndex, segMethod, outputFCSegments)