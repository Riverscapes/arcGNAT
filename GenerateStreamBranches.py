# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Generate Branches for Stream Network                           #
# Purpose:     Dissolve by Stream Order and Stream Name                       #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Aug-11                                                    # 
# Version:     1.4                                                            #
# Modified:    2018-Feb-6                                                     #
#                                                                             #
# Copyright:   (c) Kelly Whitehead, Jesse Langdon                             #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import arcpy
import gis_tools

arcpy.env.overwriteOutput = True


def get_fields(inFC):
    """
    Returns a list of attribute fields found in the feature class.
    :param inFC: input feature class
    :return: list of attribute field names
    """
    field_list = []
    fields = arcpy.ListFields(inFC)
    for field in fields:
        field_list.append(field.name)
    return field_list


def test_field(inFC, field_name):
    """
    Check if an attribute field is present in a feature class."
    :param inFC: input feature class
    :param field_name: attribute field name
    :return:
    """
    field_names = get_fields(inFC)
    if field_name in field_names:
        arcpy.AddMessage("...{0} was found in {1}".format(field_name, inFC))
    else:
        arcpy.AddError("{0} not found in {1}. {0} is a required attribute field.".format(field_name, inFC))
    return


def get_trib_confluences(fcInputPoints):
    """
    Find and selects network nodes that are tributary confluences and separates these points out
    into a new point shapefile.
    :param fcInputPoints: point shapefile (nodes from stream network)
    :return: point shapefile representing only tributary confluences
    """
    test_field(fcInputPoints, "_nodetype_")
    sql = "{0} = 'TC' OR {0} = 'HC'".format(arcpy.AddFieldDelimiters(fcInputPoints, "_nodetype_"))
    arcpy.SelectLayerByAttribute_management(fcInputPoints, "NEW_SELECTION", sql)
    nodesTC = "in_memory\\nodes_tc"
    arcpy.CopyFeatures_management(fcInputPoints, nodesTC)
    return nodesTC


def main(
    fcLineNetwork,
    fcNetworkNodes,
    fieldStreamName,
    fieldStreamOrder,
    fcOutputStreamNetwork,
    boolDissolve,
    tempWorkspace):

    reload(gis_tools)

    # Preprocessing
    gis_tools.resetData(fcOutputStreamNetwork)
    listfcMerge = []

    # Check for required attribute fields
    test_field(fcLineNetwork, "GNIS_Name")
    test_field(fcLineNetwork, "_strmordr_")

    # Make Feature Layer for 
    lyrStreamSelection = gis_tools.newGISDataset("LAYER","GNAT_BRANCHES_SelectByName")
    arcpy.MakeFeatureLayer_management(fcLineNetwork,lyrStreamSelection)
    
    # Dissolve by Stream (GNIS) Name
    where = arcpy.AddFieldDelimiters(fcLineNetwork,fieldStreamName) + " <> '' "
    arcpy.SelectLayerByAttribute_management(lyrStreamSelection,"NEW_SELECTION",where)
    fcDissolveByName = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_DissolveByName")
    arcpy.Dissolve_management(lyrStreamSelection, fcDissolveByName, fieldStreamName,multi_part="SINGLE_PART",unsplit_lines="DISSOLVE_LINES")
    listfcMerge.append(fcDissolveByName)

    # Select tributary conflences from network nodes
    lyrNetworkNodes = gis_tools.newGISDataset("LAYER", "GNAT_BRANCHES_NetworkNodes")
    arcpy.MakeFeatureLayer_management(fcNetworkNodes, lyrNetworkNodes)
    fcNodesTC = get_trib_confluences(lyrNetworkNodes)

    # Dissolve by Stream Order
    arcpy.SelectLayerByAttribute_management(lyrStreamSelection,"SWITCH_SELECTION")

    if fieldStreamOrder:
        if len(arcpy.ListFields(fcLineNetwork,fieldStreamOrder)) == 1:
            fcDissolveByStreamOrder = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_DissolveByStreamOrder")
            arcpy.Dissolve_management(lyrStreamSelection,fcDissolveByStreamOrder,fieldStreamOrder,multi_part="SINGLE_PART",unsplit_lines="DISSOLVE_LINES")

    # Split Stream Order Junctions
        if arcpy.Exists(fcNodesTC):
            fcDissolveByStreamOrderSplit = gis_tools.newGISDataset(tempWorkspace,"GNAT_BRANCHES_DissolveByStreamOrderSplit")
            arcpy.SplitLineAtPoint_management(fcDissolveByStreamOrder,fcNodesTC,fcDissolveByStreamOrderSplit,"1 METER")
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
        ## Delete remaining fields from fcMerged not BranchID, or required fields fieldStreamName,fieldStreamOrder,
        descFCMerged = arcpy.Describe(fcMerged)
        for field in descFCMerged.fields:
            if field.name not in ["BranchID",descFCMerged.OIDFieldName,descFCMerged.shapeFieldName,"Shape_Length"]:
                arcpy.DeleteField_management(fcMerged,field.name)

        arcpy.AddMessage("NOT Dissolving " + str(boolDissolve))
        arcpy.Intersect_analysis([fcMerged,fcLineNetwork],fcOutputStreamNetwork,"ALL")

    return fcOutputStreamNetwork
