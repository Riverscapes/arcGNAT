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

# # Import Modules # #
import arcpy
import FindBraidedNetwork as braid

# # Script Parameters # #
listReachPairs = [] ## Reach-Pairs written to NetworkTable
listHeadwaterIDs = [] ## Reaches identified as headwaters, written to 
listReachesDone = [] ## Reaches processed
listJunctions = [] ## Reaches that are part of a junction, to ignore as an upstream reach.
intTotalFeatures = [] ## Total number of features to be processed
listBraidedReaches = [] ## Reaches part of a braided system

# # Environmental parameters # #
arcpy.env.overwriteOutput = True

# # Functions # #

def network_tree(inputID,tblNetwork,fcLines,fcNodePoint):

    checkcount()

    # Get OID field names
    oid_fcLines = arcpy.Describe(fcLines).OIDFieldName

    if inputID in listReachesDone or inputID == "":
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

        # Make Layers
        listSelected = [] #FIXME is this being used?  If not, delete
        arcpy.MakeFeatureLayer_management(fcLines,"InputReach", oid_fcLines + " = " + str(inputID))
        arcpy.MakeFeatureLayer_management(fcLines,"SelectedReaches")

        # Select Adjacent Features
        if inputID in listBraidedReaches:
            arcpy.SelectLayerByAttribute_management("lyrBraidedReachStartPoints","CLEAR_SELECTION")
            arcpy.MakeFeatureLayer_management("lyrBraidedReachStartPoints","lyrCurrentReachBraidedPoint",""" "ORIG_FID" = """ + str(inputID))
            arcpy.SelectLayerByLocation_management("SelectedReaches","WITHIN_A_DISTANCE","lyrCurrentReachBraidedPoint","0.1","NEW_SELECTION")

            arcpy.SelectLayerByLocation_management("lyrBraidedReachStartPoints","WITHIN_A_DISTANCE","lyrCurrentReachBraidedPoint","0.1","NEW_SELECTION")
            arcpy.AddMessage("Braided " + str(int(arcpy.GetCount_management("lyrBraidedReachStartPoints").getOutput(0))))
            arcpy.SelectLayerByAttribute_management("lyrBraidedReachStartPoints","REMOVE_FROM_SELECTION",""" "ORIG_FID" = """ + str(inputID))
            arcpy.SelectLayerByAttribute_management("SelectedReaches","REMOVE_FROM_SELECTION",oid_fcLines + " = " + str(inputID))
            if int(arcpy.GetCount_management("lyrBraidedReachStartPoints").getOutput(0)) == 1:
                with arcpy.da.SearchCursor("lyrBraidedReachStartPoints",["ORIG_FID"]) as scBraided:
                    for row in scBraided:
                        arcpy.SelectLayerByAttribute_management("SelectedReaches","REMOVE_FROM_SELECTION",oid_fcLines + " = " + str(row[0]))
                del scBraided
            descSelectedReaches = arcpy.Describe("SelectedReaches")
            listSelected = descSelectedReaches.FIDset.split("; ")

        else:
            arcpy.SelectLayerByLocation_management("SelectedReaches","WITHIN_A_DISTANCE","InputReach","0.1","NEW_SELECTION")
            arcpy.SelectLayerByAttribute_management("SelectedReaches","REMOVE_FROM_SELECTION",oid_fcLines + " = " + str(inputID))
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
            arcpy.AddMessage("  Single Reach, " + str(inputID))
            listReachPairs.append([inputID,listSelected[0]])
            network_tree(listSelected[0],tblNetwork,fcLines,fcNodePoint)
            pass

        elif len(listSelected) == 0: # Headwater
            if inputID in listBraidedReaches:
                pass
            else:
                listHeadwaterIDs.append(int(inputID))
                listReachPairs.append([inputID, u'-99999']) # include headwater reaches in StreamNetworkTable
                arcpy.AddMessage("  Headwater, " + str(inputID))
            return # Return to Next Junction

        else: # Recurse through Multiple Junctions
            arcpy.AddMessage("  Junction, " + str(inputID))
            for item in listSelected:
                listJunctions.append(item)
            for selectedID in listSelected:
                listReachPairs.append([inputID,selectedID])
                network_tree(selectedID,tblNetwork,fcLines,fcNodePoint)

        return


def checkcount():
    #arcpy.AddMessage str(len(listReachesDone)) + " | " + str(intTotalFeatures[0]) 
    if len(listReachesDone) > 0:
        for percent in range(1,11):
            if len(listReachesDone) == int(intTotalFeatures[0] * 0.1 * percent):
                arcpy.AddMessage(str(10*percent) + "%  complete.")
    return


def calcNodes(fcStreamNetwork):
    arcpy.AddMessage("Calculating stream network nodes...")
    arcpy.MakeFeatureLayer_management(fcStreamNetwork, "StreamNetwork_lyr")
    descStreamNetwork = arcpy.Describe(fcStreamNetwork)
    fileGDBpath = descStreamNetwork.path
    # create table blank table to hold vertex coordinates
    networkVrtx = fileGDBpath + "\\networkVrtx"
    arcpy.CreateFeatureclass_management(fileGDBpath, "networkVrtx", "POINT", "", "DISABLED", "DISABLED", fcStreamNetwork)
    arcpy.AddField_management(networkVrtx, "ReachID", "LONG")
    arcpy.AddField_management(networkVrtx, "PointType", "TEXT")
    arcpy.AddField_management(networkVrtx, "TO_X_Coord", "DOUBLE")
    arcpy.AddField_management(networkVrtx, "TO_Y_Coord", "DOUBLE")
    arcpy.AddField_management(networkVrtx, "FROM_X_Coord", "DOUBLE")
    arcpy.AddField_management(networkVrtx, "FROM_Y_Coord", "DOUBLE")
    arcpy.AddField_management(networkVrtx, "TO_NODE", "TEXT")
    arcpy.AddField_management(networkVrtx, "FROM_NODE", "TEXT")

    # plot start and end vertices and populate TO and FROM fields in vertex table
    pointTypes = ["START", "END"]
    for type in pointTypes:
        networkVrtx_lyr = "networkVrtx_" + type + "_lyr"
        tmpVrtx = r"in_memory\vrtx" + type
        arcpy.FeatureVerticesToPoints_management("StreamNetwork_lyr", tmpVrtx, type)
        arcpy.MakeFeatureLayer_management(tmpVrtx, "tmpVrtx_"+type)
        arcpy.Append_management("tmpVrtx_"+type, networkVrtx, "NO_TEST")
        if type == "START":
            arcpy.MakeFeatureLayer_management(networkVrtx, networkVrtx_lyr)
            arcpy.SelectLayerByAttribute_management(networkVrtx_lyr, "NEW_SELECTION", """"PointType" IS NULL""")
            arcpy.CalculateField_management(networkVrtx, "PointType", "'" + type + "'", "PYTHON_9.3")
            arcpy.CalculateField_management(networkVrtx, "FROM_X_Coord", "!SHAPE.CENTROID.X!", "PYTHON_9.3")
            arcpy.CalculateField_management(networkVrtx, "FROM_Y_Coord", "!SHAPE.CENTROID.Y!", "PYTHON_9.3")
            arcpy.CalculateField_management(networkVrtx, "FROM_NODE", """str('!FROM_X_Coord!') + "_" + str(round(float('!FROM_Y_Coord!'),4))""",
                                            "PYTHON_9.3")
            arcpy.Delete_management(networkVrtx_lyr)
            del tmpVrtx
        else:
            arcpy.MakeFeatureLayer_management(networkVrtx, networkVrtx_lyr)
            arcpy.SelectLayerByAttribute_management(networkVrtx_lyr, "NEW_SELECTION", """"PointType" IS NULL""")
            arcpy.CalculateField_management(networkVrtx_lyr, "PointType", "'" + type + "'", "PYTHON_9.3")
            arcpy.CalculateField_management(networkVrtx_lyr, "TO_X_Coord", "!SHAPE.CENTROID.X!", "PYTHON_9.3")
            arcpy.CalculateField_management(networkVrtx_lyr, "TO_Y_Coord", "!SHAPE.CENTROID.Y!", "PYTHON_9.3")
            arcpy.CalculateField_management(networkVrtx_lyr, "TO_NODE", """str('!TO_X_Coord!') + "_" + str(round(float('!TO_Y_Coord!'),4))""",
                                            "PYTHON_9.3")
            arcpy.Delete_management(networkVrtx_lyr)
            del tmpVrtx
    return networkVrtx


def queryNodes(inputID, fcNodePoint):
    fcNodePoint_lyr = "fcNodePoint_lyr"
    arcpy.MakeFeatureLayer_management(fcNodePoint, fcNodePoint_lyr)
    expr = """"{0}" = {1}""".format("ReachID", inputID)
    nodeDict = {}
    with arcpy.da.SearchCursor(fcNodePoint_lyr, ['ReachID','PointType','FROM_NODE','TO_NODE'], where_clause=expr) as cursor:
        for row in cursor:
            if row[1] == 'START':
                nodeDict = {'FROM_NODE': row[2]}
            if row[1] == 'END':
                nodeDict['TO_NODE'] = row[3]
    arcpy.Delete_management(fcNodePoint_lyr)
    del cursor
    return nodeDict


def main(fcNetwork,intOutflowReachID,boolClearTable):

    # Data Paths
    descStreamNetwork = arcpy.Describe(fcNetwork)
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
        arcpy.AddField_management(tableNetwork,"FROM_NODE", "STRING")
        arcpy.AddField_management(tableNetwork,"TO_NODE", "STRING")

    # Polyline Prep
    fcStreamNetwork = "fcStreamNetwork_lyr"
    arcpy.MakeFeatureLayer_management(fcNetwork, fcStreamNetwork)

    add_fields = ["IsHeadwater", "ReachID"]
    list_fields = arcpy.ListFields(fcStreamNetwork)
    name_fields = [f.name for f in list_fields]
    oid_field = arcpy.Describe(fcStreamNetwork).OIDFieldName
    if add_fields[0] in name_fields: # add IsHeadwater field
        arcpy.DeleteField_management(fcStreamNetwork, add_fields[0])
    arcpy.AddField_management(fcStreamNetwork, add_fields[0], "SHORT")
    if add_fields[1] in name_fields:
        arcpy.DeleteField_management(fcStreamNetwork, add_fields[1])
    arcpy.AddField_management(fcStreamNetwork, add_fields[1], "LONG") # add ReachID field
    arcpy.CalculateField_management(fcStreamNetwork, "ReachID", "!" + oid_field + "!", "PYTHON_9.3")

    intTotalFeatures.append(int(arcpy.GetCount_management(fcStreamNetwork).getOutput(0)))

    # Populate Braided List
    if arcpy.Exists("lyrBraidedReaches"):
        arcpy.Delete_management("lyrBraidedReaches")
    braided_field = arcpy.ListFields(fcStreamNetwork, "IsBraided")
    if len(braided_field) > 0:
        arcpy.DeleteField_management(fcStreamNetwork, "IsBraided")
    braid.main(fcStreamNetwork) # find braids, add to "IsBraided" field if it hasn't been done already
    whereBraidedReaches = """ "IsBraided" = 1 """
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
    fcNodePoint = calcNodes(fcStreamNetwork) # Build the node point feature class
    network_tree(intOutflowReachID,tableNetwork,fcStreamNetwork,fcNodePoint)
    checkcount()

    # Write Outputs
    arcpy.AddMessage("Writing to table...")
    with arcpy.da.InsertCursor(tableNetwork,["ReachID","UpstreamID","FROM_NODE","TO_NODE"]) as icNetworkTable:
        try:
            for pair in listReachPairs:
                nodeDict = queryNodes(pair[0], fcNodePoint) # query node points feature class
                icNetworkTable.insertRow([pair[0],pair[1],nodeDict['FROM_NODE'], nodeDict['TO_NODE']])
        except RuntimeError as e:
            print "Runtime error: {0}".format(e)

    if arcpy.Exists("LineLayer"):
        arcpy.Delete_management("LineLayer")
    arcpy.MakeFeatureLayer_management(fcStreamNetwork,"LineLayer")
    arcpy.CalculateField_management(fcStreamNetwork,"IsHeadwater",0,"PYTHON") #clear field
    if len(listHeadwaterIDs) > 1:
        where = oid_field + ' IN ' + str(tuple(listHeadwaterIDs))
    else:
        where = oid_field + ' = ' + str(listHeadwaterIDs[0]) # corner case of one headwater
    arcpy.SelectLayerByAttribute_management("LineLayer","NEW_SELECTION", where)
    arcpy.CalculateField_management("LineLayer","IsHeadwater",1,"PYTHON")

    # Cleanup
    ##arcpy.Compact_management(fileGDB)

    return

# # Run as Script # # 
# if __name__ == "__main__":
# # TESTING main FUNCTION
#     inputPolylineFC = r"C:\JL\Projects\RCAs\Methow\_2Preprocess\topo_check.gdb\Methow_NHDFlowline"
#     inputOutflowReachID = 3210
#     boolClearTable = "True"
#
#     main(inputPolylineFC,inputOutflowReachID,boolClearTable)