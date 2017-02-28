# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Generate Stream Order                                          #
# Purpose:     Generate stream order for a stream network                     #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     2.0 beta                                                       #
# Modified:    2017-Feb-22                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead, Jesse Langdon 2017                        #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import os
import sys
import arcpy
import gis_tools
import ClearInMemory

def main(inputFCPolylineNetwork,
         inputDownstreamID,
         outputFCPolylineStreamOrder,
         outputFCIntersectPoints,
         outputFCJunctionPoints,
         scratchWorkspace= "in_memory"):

    # Set processing environments
    arcpy.env.outputMflag = "Disabled"
    arcpy.env.outputZflag = "Disabled"

    # Initialize stream order
    intCurrentOrder = 1

    if arcpy.Exists(outputFCPolylineStreamOrder):
       arcpy.Delete_management(outputFCPolylineStreamOrder)
    if arcpy.Exists(outputFCIntersectPoints):
        arcpy.Delete_management(outputFCIntersectPoints)

    # Preprocess network
    fcNetworkDissolved = gis_tools.newGISDataset(scratchWorkspace, "GNAT_SO_NetworkDissolved")
    arcpy.Dissolve_management(inputFCPolylineNetwork, fcNetworkDissolved, multi_part="SINGLE_PART",
                             unsplit_lines="DISSOLVE_LINES")
    
    fcNetworkIntersectPoints = gis_tools.newGISDataset(scratchWorkspace, "GNAT_SO_NetworkIntersectPoints")
    arcpy.Intersect_analysis(fcNetworkDissolved, fcNetworkIntersectPoints, "ALL", output_type="POINT")
    arcpy.AddXY_management(fcNetworkIntersectPoints)
    fcNetworkNodes = gis_tools.newGISDataset(scratchWorkspace, "GNAT_SO_NetworkNodes")
    arcpy.Dissolve_management(fcNetworkIntersectPoints,fcNetworkNodes, ["POINT_X", "POINT_Y"], "#", "SINGLE_PART")

    listFields = arcpy.ListFields(fcNetworkDissolved,"strm_order")
    if len(listFields) == 0:
        arcpy.AddField_management(fcNetworkDissolved,"strm_order","LONG")
    arcpy.CalculateField_management(fcNetworkDissolved,"strm_order",0,"PYTHON")

    lyrA = gis_tools.newGISDataset("LAYER","lyrA")
    lyrB = gis_tools.newGISDataset("LAYER","lyrB")
    lyrCalculate = gis_tools.newGISDataset("LAYER","lyrCalculate")
    
    arcpy.MakeFeatureLayer_management(fcNetworkDissolved,lyrA)
    arcpy.MakeFeatureLayer_management(fcNetworkDissolved,lyrB)
    arcpy.MakeFeatureLayer_management(fcNetworkDissolved,lyrCalculate)

    # Determine order 1 streams as initial condition
    fcDangles = gis_tools.newGISDataset(scratchWorkspace,"GNAT_SO_Dangles")
    arcpy.FeatureVerticesToPoints_management(inputFCPolylineNetwork,fcDangles,"DANGLE")
    lyrDangles = gis_tools.newGISDataset("LAYER","lyrDangles")
    where = '"ORIG_FID" <> ' + str(inputDownstreamID)
    arcpy.MakeFeatureLayer_management(fcDangles,lyrDangles,where)

    arcpy.SelectLayerByLocation_management(lyrA,"INTERSECT",lyrDangles,selection_type="NEW_SELECTION")
    arcpy.CalculateField_management(lyrA,"strm_order",intCurrentOrder,"PYTHON")
    
    fcStreamOrderTransistionPoints = gis_tools.newGISDataset(scratchWorkspace,"GNAT_SO_StreamOrderTransistionPoints")

    # Iterate through stream orders
    arcpy.AddMessage("Evaluating Stream Order: " + str(intCurrentOrder))
    arcpy.SelectLayerByAttribute_management(lyrCalculate,"NEW_SELECTION",'"strm_order" = 0')
    intFeaturesRemaining = int(arcpy.GetCount_management(lyrCalculate).getOutput(0))
    intIteration = 1
    listPairsRetired = []
    while intFeaturesRemaining <> 0:
        arcpy.AddMessage("    Iteration: " + str(intIteration) + " |Features Remaining: " + str(intFeaturesRemaining))

        listPairs = newListPairs(intCurrentOrder)
        for pair in listPairs:
            if pair not in listPairsRetired:
                fcIntersectPoints = gis_tools.newGISDataset(scratchWorkspace,"GNAT_SO_IntersectPoints_" + str(intIteration) + "_Pair_" + str(pair[0]) + "_" + str(pair[1]) + "_Order_" + str(intCurrentOrder))
                lyrIntersectPoints = gis_tools.newGISDataset("LAYER","lyrIntersectPoints" + str(intIteration) + str(pair[0]) + str(pair[1]))
                if pair[0] == pair[1]:
                    arcpy.SelectLayerByAttribute_management(lyrA,"NEW_SELECTION",'"strm_order" = ' + str(pair[0]))
                    arcpy.Intersect_analysis(lyrA,fcIntersectPoints,output_type="POINT")
                    arcpy.MakeFeatureLayer_management(fcIntersectPoints,lyrIntersectPoints)
                    arcpy.SelectLayerByAttribute_management(lyrCalculate,"NEW_SELECTION",'"strm_order" = 0')
                    arcpy.SelectLayerByLocation_management(lyrIntersectPoints,"INTERSECT",lyrCalculate,selection_type="NEW_SELECTION")
                    if arcpy.Exists(fcStreamOrderTransistionPoints):
                        arcpy.Append_management(lyrIntersectPoints,fcStreamOrderTransistionPoints)
                    else:
                        arcpy.CopyFeatures_management(lyrIntersectPoints,fcStreamOrderTransistionPoints)
                    arcpy.SelectLayerByLocation_management(lyrCalculate,"INTERSECT",fcIntersectPoints,selection_type="SUBSET_SELECTION")
                    if int(arcpy.GetCount_management(lyrCalculate).getOutput(0)) > 0 and pair[0] == intCurrentOrder:
                        intCurrentOrder = intCurrentOrder + 1
                        arcpy.AddMessage("New Stream Order: " + str(intCurrentOrder))
                    arcpy.CalculateField_management(lyrCalculate,"strm_order",int(intCurrentOrder),"PYTHON")

                else:
                    arcpy.SelectLayerByAttribute_management(lyrA,"NEW_SELECTION",'"strm_order" = ' + str(pair[0]))
                    arcpy.SelectLayerByAttribute_management(lyrB,"NEW_SELECTION",'"strm_order" = ' + str(pair[1]))
                    arcpy.Intersect_analysis([lyrA,lyrB],fcIntersectPoints,output_type="POINT")
                    arcpy.SelectLayerByAttribute_management(lyrCalculate,"NEW_SELECTION",'"strm_order" = 0')
                    arcpy.SelectLayerByLocation_management(lyrCalculate,"INTERSECT",fcIntersectPoints,selection_type="SUBSET_SELECTION")
                    arcpy.CalculateField_management(lyrCalculate,"strm_order",int(max(pair)),"PYTHON")

        # Set up next round
        arcpy.SelectLayerByAttribute_management(lyrCalculate,"NEW_SELECTION",'"strm_order" = 0')
        intFeaturesCurrent = int(arcpy.GetCount_management(lyrCalculate).getOutput(0))
        if intFeaturesRemaining == intFeaturesCurrent:
            arcpy.AddError("The number of features remaining (" + str(intFeaturesCurrent) + " is the same as the last iteration.")
            break
        else:
            intFeaturesRemaining = intFeaturesCurrent
        intIteration = intIteration + 1

    # Outputs
    arcpy.Intersect_analysis([fcNetworkDissolved,inputFCPolylineNetwork],outputFCPolylineStreamOrder)
        
    arcpy.DeleteIdentical_management(fcStreamOrderTransistionPoints, "Shape")
    arcpy.CopyFeatures_management(fcNetworkNodes, outputFCIntersectPoints)
    arcpy.CopyFeatures_management(fcNetworkIntersectPoints, outputFCJunctionPoints)

    ClearInMemory.main()

    return outputFCPolylineStreamOrder, outputFCIntersectPoints


def newListPairs(number):
    list = []
    for i1 in range(1,number + 1):
        for i2 in range(i1,number + 1):
            list.append(tuple([i1,i2]))
    return list


if __name__ == "__main__":
    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5])