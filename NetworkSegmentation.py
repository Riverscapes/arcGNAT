# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Network Segmentation                                           #
# Purpose:                                                                    #
#                                                                             #
# Author:      Kelly Whitehead                                                #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Oct-17                                                    #
# Version:     0.1          Modified:                                         #
# Copyright:   (c) Kelly Whitehead 2014                                       #                                                #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python


# # Import Modules # #
import os
import sys
import math
import arcpy
from gis_tools import *

lyrLineNetwork = "lyrLineNetwork"
outputPath = "C:\\GIS\\StreamNetwork"
outputName = "TestAngleGeodatabase06.gdb"
outputWorkspace = outputPath + "\\" + outputName + "\\"
#angleWorkspace = "C:\\GIS\\StreamNetwork\\AngleGeodatabase02.gdb\\"
tblSegments = outputWorkspace + "SegmentPoints"
tblSegmentLines = outputWorkspace + "SegmentLines"
fcRoutes = outputWorkspace + "Routes"
fcEventPoints = outputWorkspace + "Events"
fcCandidatePoints = outputWorkspace + "CandidatePoints"
evntlyrCandidateReaches = "evntlyrCandidtateReaches"
fcAngleLines = outputWorkspace + "AngleLines"
fcAngleLines0 = outputWorkspace + "AngleLines0"
fcAngleLines180 = outputWorkspace + "AngleLines180"
fcAngleMerge = outputWorkspace + "AngleLinesMerged"
fcAngleClip = outputWorkspace + "AngleLinesClipped"
fcSplitNetwork = outputWorkspace + "SplitNetwork"
tblMinValleyWidth = outputWorkspace + "MinValleyWidth"
fcAngleMinimum = outputWorkspace + "AngleMinimum"

maxValleyWidth = 3000
angleResolution = 2

def main(fcInputLineNetwork,intOutflowReachID,fcValleyPolygon,DEM,minSegmentLength,maxSegmentsPerReach,slopeThreshold,valleywidthThreshold):

    if arcpy.Exists(outputWorkspace.rstrip("\\")):
        pass
    else:
        arcpy.CreateFileGDB_management(outputPath,outputName)

    fcLineNetwork = outputWorkspace + "Network"
    resetData(fcLineNetwork)
    arcpy.CopyFeatures_management(fcInputLineNetwork,fcLineNetwork)

    ### Build Candidate Reaches ###

    # Find/Clear ReachIDField
    descLineNetwork = arcpy.Describe(fcLineNetwork)
    
    if arcpy.ListFields(fcLineNetwork,"ReachID"):
        arcpy.CalculateField_management(fcLineNetwork,"ReachID",'0',"PYTHON_9.3")
    else:
        arcpy.AddField_management(fcLineNetwork,"ReachID","LONG")
    arcpy.CalculateField_management(fcLineNetwork,"ReachID","!" + descLineNetwork.OIDFieldName + "!" ,"PYTHON_9.3")

    arcpy.AddField_management(fcLineNetwork,"From0","DOUBLE")
    arcpy.AddField_management(fcLineNetwork,"To","DOUBLE")

    arcpy.CalculateField_management(fcLineNetwork,"From0","0.0","PYTHON")
    arcpy.CalculateField_management(fcLineNetwork,"To","!shape.length!","PYTHON")


    # Create Candidate Reaches
    listCandidates = []
    with arcpy.da.SearchCursor(fcLineNetwork,["SHAPE@LENGTH","ReachID"]) as scReaches:
        for reach in scReaches:
            arcpy.AddMessage("ReachID: " + str(reach[1]))
            arcpy.AddMessage(str(reach[0]))
            if reach[0] <= float(minSegmentLength):
                segment_length = reach[0]
                arcpy.AddMessage(" Smaller Than " + str(minSegmentLength))
            elif reach[0] < float(minSegmentLength) * int(maxSegmentsPerReach):
                arcpy.AddMessage(" Fewer Segments than Max")
                segment_length = float(minSegmentLength)
            else: # reach[0] > minSegmentLength * maxSegmentsPerReach:
                segment_length = reach[0] / int(maxSegmentsPerReach)
                arcpy.AddMessage(" Max Segments. Segment Length = " + str(segment_length))

            listReachSegments = createSegments(reach[0],segment_length,minSegmentLength)
            listCandidates.append([reach[1],listReachSegments])

    # Convert Segments to Points
    ## Build Network Table
    resetData(tblSegments)
    arcpy.CreateTable_management(outputWorkspace,"SegmentPoints")
    arcpy.AddField_management(tblSegments,"ReachID","LONG")
    arcpy.AddField_management(tblSegments,"CandidateID","LONG")
    arcpy.AddField_management(tblSegments,"Distance","DOUBLE")
#    arcpy.AddField_management(tblSegments,"SegmentLength","DOUBLE")

    with arcpy.da.InsertCursor(tblSegments,["ReachID","CandidateID","Distance"]) as icTableSegments:
        for Reach in listCandidates:
            arcpy.AddMessage("Reach: " + str(Reach[0]))
            candidateIDCounter = 1
            for candidateReach in Reach[1]:
                candidateID = int(Reach[0]*1000 + candidateIDCounter)
                arcpy.AddMessage(str(candidateID))
                row = [Reach[0],int(candidateID),candidateReach]
                icTableSegments.insertRow(row)
                candidateIDCounter = candidateIDCounter + 1

    ## NetworkTable to Points
    arcpy.AddMessage("Generating Network Events...")
    arcpy.env.MDomain = "0 10000000"
    resetData(fcRoutes)
    arcpy.CreateRoutes_lr(fcLineNetwork,"ReachID",fcRoutes,"TWO_FIELDS","From0","To")

    resetData(evntlyrCandidateReaches)
    arcpy.MakeRouteEventLayer_lr(fcRoutes,"ReachID",tblSegments,"ReachID POINT Distance",evntlyrCandidateReaches,"#","NO_ERROR_FIELD","ANGLE_FIELD","NORMAL","ANGLE")
    
    resetData(fcEventPoints)
    arcpy.CopyFeatures_management(evntlyrCandidateReaches,fcEventPoints)

    ### Calculate Evaluation Values ###
    # Extract Elevation for each candidate reach point
    arcpy.AddMessage("Extracting Elevations...")
    resetData(fcCandidatePoints)
    arcpy.sa.ExtractValuesToPoints(evntlyrCandidateReaches,DEM,fcCandidatePoints,"NONE","VALUE_ONLY")

    # Find valley width at each candidate reach point (perpendicular)
    arcpy.AddMessage("Find Valley Width...")
    ###
    arcpy.AddField_management(fcCandidatePoints,"Angle0","Double")
    arcpy.AddField_management(fcCandidatePoints,"Angle180","Double")
    arcpy.AddField_management(fcCandidatePoints,"AngleDistance","Double")

    arcpy.CalculateField_management(fcCandidatePoints,"Angle0","( !LOC_ANGLE! - 90 )*(-1)","PYTHON")
    arcpy.CalculateField_management(fcCandidatePoints,"Angle180","!Angle0!+180","PYTHON")  
    arcpy.CalculateField_management(fcCandidatePoints,"AngleDistance",str(maxValleyWidth/2),"PYTHON")
    
    arcpy.AddXY_management(fcCandidatePoints)
    
    resetData(fcAngleLines0)
    resetData(fcAngleLines180)
    arcpy.BearingDistanceToLine_management(fcCandidatePoints,fcAngleLines0,"POINT_X","POINT_Y","AngleDistance","#","Angle0","DEGREES","GEODESIC","CandidateID")
    arcpy.BearingDistanceToLine_management(fcCandidatePoints,fcAngleLines180,"POINT_X","POINT_Y","AngleDistance","#","Angle180","DEGREES","GEODESIC","CandidateID")
    resetData(fcAngleMerge)
    arcpy.Merge_management([fcAngleLines180,fcAngleLines0],fcAngleMerge)

    resetData(fcAngleLines)
    arcpy.UnsplitLine_management(fcAngleMerge,fcAngleLines,"CandidateID")
    ###

    rotateAngles = range(-90,90+1,angleResolution)
    listFCAngleClipNames = []
    fcAngleName = outputWorkspace + "RotatedAngles"
    resetData(fcAngleName)

    arcpy.CopyFeatures_management(fcAngleLines,fcAngleName)
    arcpy.DeleteRows_management(fcAngleName)
    arcpy.AddField_management(fcAngleName,"Angle","DOUBLE")
    for angle in rotateAngles:
        arcpy.AddMessage("Rotating Angle: " + str(angle))
        #if angle <0:
        #    prefix = "Minus"
        #else:
        #    prefix = ""
        #fcAngleName = angleWorkspace + "AngleSet" + prefix + str(abs(angle)).replace(".",'')
        
        #resetData(fcAngleName)
        #arcpy.CopyFeatures_management(fcAngleLines,fcAngleName)
        rotateFeatures(fcAngleLines,fcAngleName,angle)
    
    arcpy.AddMessage("Starting Clip of Rotated Angles")
    resetData(fcAngleName + "_Clipped")
    arcpy.Clip_analysis(fcAngleName,fcValleyPolygon,fcAngleName + "_Clipped")

    #Clean up Clip: remove 'parts' that do not intersect with centroid?

    with arcpy.da.SearchCursor(fcAngleName + "_Clipped",["OBJECTID","CandidateID","Shape_Length"],sql_clause=(None,'ORDER BY CandidateID ASC')) as scAngleName:
        intCandidateID = 0
        listMinOID = []
        currentOID = 0
        for row in scAngleName:
            arcpy.AddMessage("CandidateID" + str(row[0]))
            if row[1] <> intCandidateID:
                intCandidateID = row[1]
                if currentOID <> 0:
                    listMinOID.append(currentOID)
                currentMin = maxValleyWidth * 2
            if row[2] < currentMin:
                 currentOID = row[0]
                 currentMin = row[2]

    resetData(fcAngleMinimum)
    where = '"OBJECTID" IN' + str(tuple(listMinOID))
    arcpy.AddMessage(where)
    arcpy.Select_analysis(fcAngleName + "_Clipped" ,fcAngleMinimum,where)

    #resetData(tblMinValleyWidth)
    #arcpy.Statistics_analysis(fcAngleName + "_Clipped",tblMinValleyWidth,[["Shape_Length","MIN"]],"CandidateID") 
    arcpy.JoinField_management(fcCandidatePoints,"CandidateID",fcAngleMinimum,"CandidateID","Shape_Length")

    ### Perpendicular Method ###
    #arcpy.AddMessage("Starting Clip of Perpendicular Angles")
    #resetData(fcAngleClip)
    #arcpy.Clip_analysis(fcAngleLines,fcValleyPolygon,fcAngleClip)
    #arcpy.JoinField_management(fcCandidatePoints,"CandidateID",fcAngleClip,"CandidateID","Shape_Length")
    ### ###


    ### Test Evaluation Values to Find SubReaches ###
    arcpy.AddMessage("Building Segment Table...")
    arcpy.AddField_management(fcCandidatePoints,"Split","LONG")
    resetData(tblSegmentLines)
    arcpy.CreateTable_management(outputWorkspace,"SegmentLines")
    arcpy.AddField_management(tblSegmentLines,"Start","LONG")
    arcpy.AddField_management(tblSegmentLines,"End","LONG")
    arcpy.AddField_management(tblSegmentLines,"Slope","DOUBLE")
    arcpy.AddField_management(tblSegmentLines,"Valley","DOUBLE")

    # Build Table of Segments

    with arcpy.da.InsertCursor(tblSegmentLines,["Start","End","Slope","Valley"]) as icSegmentTable:
        with arcpy.da.SearchCursor(fcCandidatePoints,["RASTERVALU","Distance","Shape_Length","CandidateID"],sql_clause=(None,'ORDER BY CandidateID ASC')) as scCandidatePoints:
            startPoint = scCandidatePoints.next()
            endPoint = scCandidatePoints.next()
            intFeatures = int(arcpy.GetCount_management(fcCandidatePoints).getOutput(0))
            for i in range(intFeatures-2): # Stop 1 before end
                arcpy.AddMessage(str(i) +  " StartID: " + str(startPoint[3]) + " | EndID: " + str(endPoint[3]))
                ## Find Slope
                slope = abs((startPoint[0]-endPoint[0])/(startPoint[1]-endPoint[1]))
                    
                ## Find Valley Width
                valley = endPoint[2]
                    
                ## Write to Table
                icSegmentTable.insertRow([startPoint[3],endPoint[3],slope,valley])
                    
                ## Next Segment
                startPoint  = endPoint
                if i < intFeatures - 1:
                    endPoint = scCandidatePoints.next()

    # Logic - Is candidate Reach within thresholds
    listSplitIDs = []
    with arcpy.da.SearchCursor(tblSegmentLines,['End','Slope','Valley'],sql_clause=(None,'ORDER BY End ASC')) as scSegmentLines:
        segmentA = scSegmentLines.next()
        segmentB = scSegmentLines.next()
        intFeatureCount = int(arcpy.GetCount_management(tblSegmentLines).getOutput(0))-2 # Stop 1 before end
        for i in range(intFeatureCount-1):
            if abs(segmentA[1]-segmentB[1]) > slopeThreshold:
                listSplitIDs.append(SegmentA[0]) # end point of segment ahead
            elif abs(segmentA[2]-segmentB[2]) > valleywidthThreshold:
                listSplitIDs.append(SegmentA[0])
            else:
                pass

            ## Next Segment
            segmentA = segmentB
            if i < intFeatureCount-1:
                segmentB = scSegmentLines.next()

    arcpy.AddMessage("Split Points:")
    
    if len(listSplitIDs) > 0:
        for item in listSplitIDs:
            arcpy.AddMessage(str(item))
           
        where = '"OBJECTID" IN' + str(tuple(listSplitIDs))
        arcpy.MakeFeatureLayer_management(fcCandidatePoints,"SplitLayer",where)

        ### Output SubReaches ###
        arcpy.SplitLineAtPoint_management(fcLineNetwork,"SplitLayer",fcSplitNetwork,"0.2")
    else:
        arcpy.AddMessage("No Split Segments Found")
    
    arcpy.AddMessage("Processing Complete.")
    
    return



def createSegments(totalLength,distance,minDistance):
    listSegments = []
    currentDistance = 0
    #remainingDistance = totalLength
    while totalLength > currentDistance:
        arcpy.AddMessage("  Distance: " + str(currentDistance))
        listSegments.append(currentDistance)
        currentDistance = currentDistance + distance
        #remainingDistance = remainingDistance - distance
    listSegments.append(totalLength)
    return listSegments



# # Run as Script # # 
if __name__ == "__main__":
    inputPolylineFC = sys.argv[1] # Str Feature class path
    inputOutflowReachID = sys.argv[2] # Int
    inputValleyPolygon = sys.argv[3]
    inputDEM = sys.argv[4] # Str Raster DataLayer
    minSegmentLength = sys.argv[5]# Dbl
    maxSegmentsPerReach = sys.argv[6]# Int
    slopeThreshold = sys.argv[7]# max difference between candidate reaches to become a subreach
    valleywidthThreshold = sys.argv[8]# max difference between candidate reaches to become a subreach

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5],
         sys.argv[6],
         sys.argv[7],
         sys.argv[8])