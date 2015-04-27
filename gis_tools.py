# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        GIS Tools Module                                               #
# Purpose:     Support components for Riverstyles and Stream Network Toolbox  #
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
import math
import arcpy

scratchWorkspace = arcpy.env.scratchWorkspace

# # Functions # #
def resetData(inputDataset):
    if arcpy.Exists(inputDataset):
        arcpy.Delete_management(inputDataset)

    return

def newGISDataset(workspace, inputDatasetName):
    #arcpy.AddMessage("New GeoDataset: " + str(workspace) + " " + str(inputDatasetName))
    if workspace == "Layer":
        inputDataset = inputDatasetName
        if arcpy.Exists(inputDataset):
            arcpy.Delete_management(inputDataset)
    else:
        inputDataset = workspace + "\\" + inputDatasetName
        if arcpy.Exists(inputDataset):
            arcpy.Delete_management(inputDataset)

    return inputDataset

def getGISDataset(workspace,inputDatasetName):
    if workspace == "Layer":
        inputDataset = inputDatasetName
        if arcpy.Exists(inputDataset):
            return inputDatset
    else:
        inputDataset = workspace + "\\" + inputDatasetName
        if arcpy.Exists(inputDataset):
            return inputDataset

def resetField(inTable,FieldName,FieldType,TextLength=0):
    
    if arcpy.Describe(inTable).dataType == "ShapeFile":
        FieldName = FieldName[:10]

    if len(arcpy.ListFields(inTable,FieldName))==1:
        if FieldType == "TEXT":
            arcpy.CalculateField_management(inTable,FieldName,"''","PYTHON")
        else:
            arcpy.CalculateField_management(inTable,FieldName,"0","PYTHON")
        #arcpy.DeleteField_management(inTable,FieldName) #lots of 999999 errors 
    
    else: #Create Table if does not exist
        if FieldType == "TEXT":
            arcpy.AddField_management(inTable,FieldName,"TEXT",field_length=TextLength)
        else:
            arcpy.AddField_management(inTable,FieldName,FieldType)
    return str(FieldName) 

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

if __name__ == "__main__":
    print("gis_tools.py is not an executable python script.")