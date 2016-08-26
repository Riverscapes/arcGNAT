# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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
import sys
import arcpy
import gis_tools
from decimal import *

listStrRemainderRules = ["Leave Remainder as Segment","Divide Remainder Proportionally"]

# # Main Function # #
def main(inputFCStreamNetwork,
         inputDistance,
         inputRemainderRule,
         inputBranchField,
         outputSegmentIDField,
         fcOutputStreamNetwork,
         scratchWorkspace):

    gis_tools.resetData(fcOutputStreamNetwork)

    listPoints = []
    if inputBranchField:
        arcpy.AddMessage(" Dissolving by " +str(inputBranchField))
        fcDissolvedStreamBranch = gis_tools.newGISDataset(scratchWorkspace,"GNAT_SEG_DissolveByStreamBranch")
        arcpy.Dissolve_management(inputFCStreamNetwork,fcDissolvedStreamBranch,inputBranchField,multi_part="SINGLE_PART")
    else:
        fcDissolvedStreamBranch = inputFCStreamNetwork

    with arcpy.da.SearchCursor(fcDissolvedStreamBranch,["SHAPE@","SHAPE@LENGTH"]) as scBranches:
        for row in scBranches:
            #arcpy.AddMessage(" New Line Length: " + str(row[1]))
            gLine = row[0]
            dblPointPosition = 0

            if inputRemainderRule == "Leave Remainder as Segment":
                while dblPointPosition < row[1]:
                    listPoints.append(gLine.positionAlongLine(dblPointPosition))
                    dblPointPosition += Decimal(inputDistance)
                    #arcpy.AddMessage(str(dblPointPosition))
            else:
                intNumberOfPositions = int(Decimal(row[1])/Decimal(inputDistance))
                for intPosition in range(intNumberOfPositions):
                    
                    dblProportionalPosition = float(intPosition)/intNumberOfPositions
                    arcpy.AddMessage(" Position: " + str(intPosition) + " of " + str(intNumberOfPositions) + " | " + str(dblProportionalPosition))
                    listPoints.append(gLine.positionAlongLine(dblProportionalPosition,True))
                    
    arcpy.AddMessage(" Out of Line Cursor" )            
    fcSplitPoints = gis_tools.newGISDataset(scratchWorkspace,"GNAT_SEG_SplitPoints")
    arcpy.CreateFeatureclass_management(scratchWorkspace,"GNAT_SEG_SplitPoints","POINT",spatial_reference=inputFCStreamNetwork)

    with arcpy.da.InsertCursor(fcSplitPoints,["SHAPE@"]) as icSplitPoints:
        for point in listPoints:
            icSplitPoints.insertRow([point])
    arcpy.AddMessage(" Out of Point Insert Cursor")
    arcpy.SplitLineAtPoint_management(fcDissolvedStreamBranch,fcSplitPoints,fcOutputStreamNetwork,"1 Meters")
    gis_tools.addUniqueIDField(fcOutputStreamNetwork,outputSegmentIDField)




    return