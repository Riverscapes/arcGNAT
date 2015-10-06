# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Generate Branches for Stream Network                           #
# Purpose:     Dissolve by Stream Order and Stream Name                       #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Aug-11                                                    # 
# Version:     1.3                                                            #
# Modified:    2015-Aug-11                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import os
import sys
import arcpy
import gis_tools

# # Main Function # # 
def main(
    fcLineNetwork,
    fcSplitPoints,
    fieldStreamName,
    fieldStreamOrder,
    fcOutputStreamNetwork,
    boolDissolve,
    tempWorkspace):

    reload(gis_tools)

    # Preprocessing
    gis_tools.resetData(fcOutputStreamNetwork)
    listfcMerge = []

    # Make Feature Layer for 
    lyrStreamSelection = gis_tools.newGISDataset("LAYER","GNAT_BRANCHES_SelectByName")
    arcpy.MakeFeatureLayer_management(fcLineNetwork,lyrStreamSelection)
    
    # Dissolve by Stream (GNIS) Name
    where = arcpy.AddFieldDelimiters(fcLineNetwork,fieldStreamName) + " <> '' "
    arcpy.SelectLayerByAttribute_management(lyrStreamSelection,"NEW_SELECTION",where)
    fcDissolveByName = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_DissolveByName")
    arcpy.Dissolve_management(lyrStreamSelection,fcDissolveByName,fieldStreamName)
    listfcMerge.append(fcDissolveByName)
    
    # Dissolve by Stream Order
    arcpy.SelectLayerByAttribute_management(lyrStreamSelection,"SWITCH_SELECTION")

    if fieldStreamOrder:
        if len(arcpy.ListFields(fcLineNetwork,fieldStreamOrder)) == 1:
            fcDissolveByStreamOrder = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_DissolveByStreamOrder")
            arcpy.Dissolve_management(lyrStreamSelection,fcDissolveByStreamOrder,fieldStreamOrder)

    # Split Stream Order Junctions
        if arcpy.Exists(fcSplitPoints):
            fcDissolveByStreamOrderSplit = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_DissolveByStreamOrderSplit")
            arcpy.SplitLineAtPoint_management(fcDissolveByStreamOrder,fcSplitPoints,fcDissolveByStreamOrderSplit,"1 METER")
            listfcMerge.append(fcDissolveByStreamOrderSplit)
        else:
            listfcMerge.append(fcDissolveByStreamOrder)
    else:
        fcNoStreamOrder = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_NoStreamOrderOrStreamName")
        arcpy.Dissolve_management(lyrStreamSelection,fcNoStreamOrder,multi_part="SINGLE_PART")
        listfcMerge.append(fcNoStreamOrder)
    
    # Merge Dissolved Networks
    fcMerged = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_MergedDissolvedNetworks")
    arcpy.Merge_management(listfcMerge,fcMerged)

    # Add Branch ID
    arcpy.AddField_management(fcMerged,"BranchID","LONG")
    gis_tools.addUniqueIDField(fcMerged,"BranchID")


    # Final Output
    if boolDissolve == "true":
        arcpy.AddMessage("Dissolving " + str(boolDissolve))
        arcpy.CopyFeatures_management(fcMerged,fcOutputStreamNetwork)
    else:
        ## Delete remaining fields from fcMerged not BranchID, or Requried Fields fieldStreamName,fieldStreamOrder,
        descFCMerged = arcpy.Describe(fcMerged)
        for field in descFCMerged.fields:
            if field.name not in ["BranchID",descFCMerged.OIDFieldName,descFCMerged.shapeFieldName,"Shape_Length"]:
                arcpy.DeleteField_management(fcMerged,field.name)

        arcpy.AddMessage("NOT Dissolving " + str(boolDissolve))
        arcpy.Intersect_analysis([fcMerged,fcLineNetwork],fcOutputStreamNetwork,"ALL")

    return

if __name__ == "__main__":

    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
        sys.argv[5],
        sys.argv[6],
        sys.argv[7],
        sys.argv[8])