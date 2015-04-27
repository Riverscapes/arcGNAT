# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Build Stream Network Topology                                  #
# Purpose:     Generate a table of stream network segment topology            #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Sept-08                                                   #
# Version:     1.1                                                            #
# Modified:    2014-Sept-08                                                   #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2014                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

#Overview:
# Script to build the network table.
# Start at outflow and populate the network database table.
#
#Inputs:
# Line feature class
# Feature ID of outflow reach.
#
#Algorithm
# Start at outflow reach
# Select all features within buffer distance (0.05)
# Loop over touching features (ignoring those already processed)
# Store touching features in network table.
# Optional: Store headwater attribute for reaches that have no neighbours
#
#Requirements:
# Need to anticipate running when no network table exists in File GDB
# Need to anticipate running when existing network table is populated (i.e. clear table first)
# Probably should compact GDB after running.
# Consider status bar updates (processing could be slow)
#
#Output Data Format
# Store in new table in File GDB called "NetworkTable" Fields:
# ReachID (long int)
# UpstreamID (long int)
# Add IsHeadwater bit (yes/no) field to main feature class

# # Import Modules # #
import os
import sys
import arcpy

# # Script Parameters # #
listReachPairs = [] ## Reach-Pairs written to NetworkTable
listHeadwaterIDs = [] ## Reaches identified as headwaters, written to 
listReachesDone = [] ## Reaches processed
listJunctions = [] ## Reaches that are part of a junction, to ignore as an upstream reach.
intTotalFeatures = [] ## Total number of features to be processed
listBraidedReaches = [] ## Reaches part of a braided system

# # Functions # #

def network_tree(inputID,tblNetwork,fcLines):

    checkcount()

    if inputID in listReachesDone:
        pass #return

    else:
        listReachesDone.append(inputID)

        if arcpy.Exists("InputReach"):
            arcpy.Delete_management("InputReach")
        if arcpy.Exists("SelectedReaches"):
            arcpy.Delete_management("SelectedReaches")
        if arcpy.Exists("lyrCurrentReachBraidedPoint"):
            arcpy.Delete_management("lyrCurrentReachBraidedPoint")
        if arcpy.Exists("lyrSelectedBraidedReaches"):
            arcpy.Delete_management("lyrSelectedBraidedReaches")
        arcpy.SelectLayerByAttribute_management("lyrBraidedReachStartPoints","CLEAR_SELECTION")

        # Select Adjacent Features
        listSelected = []
        arcpy.MakeFeatureLayer_management(fcLines,"InputReach",""" "OBJECTID" = """ + str(inputID))
        arcpy.MakeFeatureLayer_management(fcLines,"SelectedReaches")

        if inputID in listBraidedReaches:
            arcpy.SelectLayerByAttribute_management("lyrBraidedReachStartPoints","CLEAR_SELECTION")
            arcpy.MakeFeatureLayer_management("lyrBraidedReachStartPoints","lyrCurrentReachBraidedPoint",""" "ORIG_FID" = """ + str(inputID))
            arcpy.SelectLayerByLocation_management("SelectedReaches","WITHIN_A_DISTANCE","lyrCurrentReachBraidedPoint","0.1","NEW_SELECTION")

            arcpy.SelectLayerByLocation_management("lyrBraidedReachStartPoints","WITHIN_A_DISTANCE","lyrCurrentReachBraidedPoint","0.1","NEW_SELECTION")
            arcpy.AddMessage("Braided" + str(int(arcpy.GetCount_management("lyrBraidedReachStartPoints").getOutput(0))))
            arcpy.SelectLayerByAttribute_management("lyrBraidedReachStartPoints","REMOVE_FROM_SELECTION",""" "ORIG_FID" = """ + str(inputID))
            arcpy.SelectLayerByAttribute_management("SelectedReaches","REMOVE_FROM_SELECTION",""" "OBJECTID" = """ + str(inputID))
            if int(arcpy.GetCount_management("lyrBraidedReachStartPoints").getOutput(0)) == 1:
                with arcpy.da.SearchCursor("lyrBraidedReachStartPoints",["ORIG_FID"]) as scBraided:
                    for row in scBraided:
                        arcpy.SelectLayerByAttribute_management("SelectedReaches","REMOVE_FROM_SELECTION",""" "OBJECTID" = """ +str(row[0]))
                del scBraided
            descSelectedReaches = arcpy.Describe("SelectedReaches")
            listSelected = descSelectedReaches.FIDset.split("; ")

        else:
            arcpy.SelectLayerByLocation_management("SelectedReaches","WITHIN_A_DISTANCE","InputReach","0.1","NEW_SELECTION")
            arcpy.SelectLayerByAttribute_management("SelectedReaches","REMOVE_FROM_SELECTION",""" "OBJECTID" = """ + str(inputID))
            arcpy.SelectLayerByLocation_management("lyrBraidedReachStartPoints","WITHIN_A_DISTANCE","InputReach","0.1","NEW_SELECTION")
            listSelectedBraidedReaches = []
            if int(arcpy.GetCount_management("lyrBraidedReachStartPoints").getOutput(0)) > 0:
                with arcpy.da.SearchCursor("lyrBraidedReachStartPoints",["ORIG_FID"]) as scBraided:
                    for row in scBraided:
                        listSelectedBraidedReaches.append(str(row[0]))
                del scBraided

                arcpy.AddMessage("   Selected Braided Reaches: " + str(listSelectedBraidedReaches))

            descSelectedReaches = arcpy.Describe("SelectedReaches")
            listSelected = descSelectedReaches.FIDset.split("; ")
            for item in listReachesDone:
                if str(item) in listSelected:
                    listSelected.remove(str(item))

            for item in listSelectedBraidedReaches:
                if str(item) in listSelected:
                    listSelected.remove(str(item))
        
        for item in listJunctions:
            if str(item) in listSelected:
                listSelected.remove(str(item))
    
        # Recursion Cases
        if len(listSelected) == 1: # Move Along Stream
            #Write Output to Table
            arcpy.AddMessage("  Single Reach")
            listReachPairs.append([inputID,listSelected[0]])
            network_tree(listSelected[0],tblNetwork,fcLines) 
            pass

        elif len(listSelected) == 0: # Headwater
            if inputID in listBraidedReaches:
                pass
            else:
                listHeadwaterIDs.append(int(inputID))
                arcpy.AddMessage("  Headwater")
            return # Return to Next Junction

        else: # Recurse through Multiple Junctions
            arcpy.AddMessage("  Junction")
            for item in listSelected:
                listJunctions.append(item)
            for selectedID in listSelected:
                listReachPairs.append([inputID,selectedID])
                network_tree(selectedID,tblNetwork,fcLines)
 
def checkcount():
    #arcpy.AddMessage str(len(listReachesDone)) + " | " + str(intTotalFeatures[0]) 
    if len(listReachesDone) > 0:
        for percent in range(1,11):
            if len(listReachesDone) == int(intTotalFeatures[0] * 0.1 * percent):
                arcpy.AddMessage(str(10*percent) + "%  complete.")
    return

def main(fcStreamNetwork,intOutflowReachID,boolClearTable):

    # Data Paths
    descStreamNetwork = arcpy.Describe(fcStreamNetwork)
    fileGDB = descStreamNetwork.path
    tableNetwork = fileGDB + "\\StreamNetworkTable"

    # NetworkTable Prep
    if arcpy.Exists(tableNetwork):
        # Clear contents of table
        if boolClearTable:
            arcpy.DeleteRows_management(tableNetwork)
    else:
        # Create new network Table
        arcpy.CreateTable_management(fileGDB,"StreamNetworkTable")
        arcpy.AddField_management(tableNetwork,"ReachID","LONG")
        arcpy.AddField_management(tableNetwork,"UpstreamID","LONG")

    # Polyline Prep
    listFields = arcpy.ListFields(fcStreamNetwork,"IsHeadwater")
    if len(listFields) is not 1:
        arcpy.AddField_management(fcStreamNetwork,"IsHeadwater","SHORT")

    intTotalFeatures.append(int(arcpy.GetCount_management(fcStreamNetwork).getOutput(0)))

    # Populate Braided List
    if arcpy.Exists("lyrBraidedReaches"):
        arcpy.Delete_management("lyrBraidedReaches")
    whereBraidedReaches = """ "IsBraidedReach" = 1 """
    arcpy.MakeFeatureLayer_management(fcStreamNetwork,"lyrBraidedReaches")
    arcpy.SelectLayerByAttribute_management("lyrBraidedReaches","NEW_SELECTION",whereBraidedReaches)
    descLyrBraidedReaches = arcpy.Describe("lyrBraidedReaches")
    for item in descLyrBraidedReaches.FIDset.split("; "):
        listBraidedReaches.append(item)

    if arcpy.Exists("in_memory\\BraidedReachStartPoints"):
        arcpy.Delete_management("in_memory\\BraidedReachStartPoints")
    arcpy.FeatureVerticesToPoints_management("lyrBraidedReaches","in_memory\\BraidedReachStartPoints","START")
    if arcpy.Exists("lyrBraidedReachStartPoints"):
        arcpy.Delete_management("lyrBraidedReachStartPoints")
    arcpy.MakeFeatureLayer_management("in_memory\\BraidedReachStartPoints","lyrBraidedReachStartPoints")

    # Process
    network_tree(intOutflowReachID,tableNetwork,fcStreamNetwork)
    checkcount()

    # Write Outputs
    with arcpy.da.InsertCursor(tableNetwork,["ReachID","UpstreamID"]) as icNetworkTable:
        for pair in listReachPairs:
            icNetworkTable.insertRow([pair[0],pair[1]])

    if arcpy.Exists("LineLayer"):
        arcpy.Delete_management("LineLayer")
    arcpy.MakeFeatureLayer_management(fcStreamNetwork,"LineLayer")
    arcpy.CalculateField_management(fcStreamNetwork,"IsHeadwater",0,"PYTHON") #clear field
    where = '"OBJECTID" IN' + str(tuple(listHeadwaterIDs))
    #print(where)
    arcpy.SelectLayerByAttribute_management("LineLayer","NEW_SELECTION",where)
    arcpy.CalculateField_management("LineLayer","IsHeadwater",1,"PYTHON")

    # Cleanup

    ##arcpy.Compact_management(fileGDB)

    return

# # Run as Script # # 
if __name__ == "__main__":
    inputPolylineFC = sys.argv[1] # Str Feature class path
    inputOutflowReachID = sys.argv[2] # Int
    boolClearTable = sys.argv[3]

    main(inputPolylineFC,inputOutflowReachID,boolClearTable)