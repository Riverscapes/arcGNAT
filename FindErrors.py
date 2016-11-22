# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Find Topology Errors                                           #
# Purpose:     Generates a table of stream network topology errors.           #
#                                                                             #
# Author:      Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc.                                      #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2016-Aug-19                                                    #
# Version:     0.1                                                            #
# Modified:                                                                   #
#                                                                             #
# Copyright:   (c) Jesse Langdon 2016                                         #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# Import arcpy module
import itertools
from itertools import *
import arcpy
from arcpy.sa import *
import gis_tools

# Set environmental variables
arcpy.env.overwriteOutput = True

#Error Codes
# 0 - no errors
# 1 - dangle (redacted)
# 2 - potential braid
# 3 - duplicate
# 4 - overlap
# 5 - crossed
# 6 - disconnected
# 7 - flipped flow direction
# 8 - other potential errors



# Find braided reach errors
def braids(in_network_fc, tmp_network_tbl):
    arcpy.AddMessage("...braids")
    in_network_fc_lyr = "in_network_fc_lyr"
    arcpy.MakeFeatureLayer_management(in_network_fc, in_network_fc_lyr)

    # Set global variables
    ERROR_CODE = 2

    # Create temporary in_memory version of input stream network
    tmp_network_fc = r"in_memory\tmp_network_fc"
    #arcpy.FeatureClassToFeatureClass_conversion(in_network_fc_lyr, "in_memory", "tmp_network_fc")
    arcpy.FeatureClassToFeatureClass_conversion(in_network_fc_lyr, "in_memory", "tmp_network_fc")
    arcpy.MakeFeatureLayer_management(r"in_memory\tmp_network_fc", "tmp_network_fc_lyr")

    # Select reaches based on "IsBraided" attribute field
    expr = """"{0}" = {1}""".format("IsBraided", 1)
    arcpy.SelectLayerByAttribute_management("tmp_network_fc_lyr", "NEW_SELECTION", expr)
    arcpy.FeatureClassToFeatureClass_conversion("tmp_network_fc_lyr", "in_memory", "braids")
    arcpy.MakeFeatureLayer_management(r"in_memory\braids", "braids_lyr")

    # Add error values to network table
    arcpy.AddJoin_management(tmp_network_tbl, "ReachID", "braids_lyr", "ReachID", "KEEP_COMMON")
    arcpy.CalculateField_management(tmp_network_tbl, "ERROR_CODE", ERROR_CODE, "PYTHON_9.3")
    arcpy.RemoveJoin_management(tmp_network_tbl)

    # Clean up
    arcpy.Delete_management(tmp_network_fc)

    return


# Find duplicate reaches
def duplicates(in_network_fc, tmp_network_tbl):
    arcpy.AddMessage("...duplicate reaches")
    in_network_fc_lyr = "in_network_fc_lyr"
    arcpy.MakeFeatureLayer_management(in_network_fc, in_network_fc_lyr)

    # Set global variables
    ERROR_CODE = 3

    # Create temporary in_memory version of in_network_fc
    tmp_network_fc = r"in_memory\tmp_network_fc"
    arcpy.FeatureClassToFeatureClass_conversion(in_network_fc_lyr, "in_memory", "tmp_network_fc")
    arcpy.AddField_management(tmp_network_fc, "IsDuplicate", "SHORT")
    arcpy.AddField_management(tmp_network_fc, "Reach_Length", "DOUBLE")
    arcpy.MakeFeatureLayer_management(tmp_network_fc, "tmp_network_fc_lyr")
    arcpy.CalculateField_management("tmp_network_fc_lyr", "Reach_Length", "!shape.length@meters!", "PYTHON_9.3" )

    # Find identical reaches based on length field
    with arcpy.da.SearchCursor("tmp_network_fc_lyr", ["Reach_Length"]) as length_cursor:
        lengths = [r[0] for r in length_cursor]
    with arcpy.da.UpdateCursor("tmp_network_fc_lyr", ["Reach_Length", "IsDuplicate"]) as cursor:
        for row in cursor:
            if lengths.count(row[0]) > 1:
                row[1] = 1
            else:                row[1] = 0
            cursor.updateRow(row)

    # Select duplicate records
    expr = """"{0}" = {1}""".format("IsDuplicate", 1)
    arcpy.SelectLayerByAttribute_management("tmp_network_fc_lyr","NEW_SELECTION", expr)
    arcpy.FeatureClassToFeatureClass_conversion("tmp_network_fc_lyr", "in_memory", "duplicates_only")
    arcpy.MakeFeatureLayer_management("in_memory\\duplicates_only", "duplicates_only_lyr")

    # Add error values to network table
    arcpy.AddJoin_management(tmp_network_tbl, "ReachID", "duplicates_only_lyr", "ReachID", "KEEP_COMMON")
    arcpy.CalculateField_management(tmp_network_tbl, "ERROR_CODE", ERROR_CODE, "PYTHON_9.3")
    arcpy.RemoveJoin_management(tmp_network_tbl)

    # Clean up
    arcpy.Delete_management(tmp_network_fc)
    arcpy.Delete_management("tmp_network_fc_lyr")
    arcpy.Delete_management("in_memory\\duplicates_only")
    arcpy.Delete_management("duplicates_only_lyr")

    return


## Find overlapped or crossed segments
def reach_pair_errors(in_network_fc, tmp_network_tbl, reach_id):
    arcpy.AddMessage("...overlap/crossing errors")
    in_network_fc_lyr = "in_network_fc_lyr"
    arcpy.MakeFeatureLayer_management(in_network_fc, in_network_fc_lyr)

    # Create a list with reach ID and associated upstream ID
    field_name_list = ['ReachID', 'UpstreamID', 'ERROR_CODE']
    with arcpy.da.SearchCursor(tmp_network_tbl, field_name_list) as scursor:
        for srow in scursor:
            reach_pair = [srow[0], srow[1]]

            # Select reach and its upstream buddy
            expr = """"{0}" = {1} or "{0}" = {2}""".format("ReachID", reach_pair[0], reach_pair[1])
            arcpy.SelectLayerByAttribute_management(in_network_fc_lyr, "NEW_SELECTION", expr)
            arcpy.CopyFeatures_management(in_network_fc_lyr, r"in_memory\sel_rch")
            arcpy.MakeFeatureLayer_management(r"in_memory\sel_rch", "sel_rch_lyr")
            #arcpy.FeatureClassToFeatureClass_conversion("sel_rch_lyr", r"C:\JL\Testing\GNAT\BuildNetworkTopology\YF.gdb", "sel_rch")

            # Send temporary reach feature class to error functions
            result_cross = cross("sel_rch_lyr")
            result_overlap = overlap("sel_rch_lyr")

            # Update record in network table
            if result_overlap != 0:
                with arcpy.da.UpdateCursor(tmp_network_tbl, ["ReachID", "ERROR_CODE"], expr) as ucursor:
                    for urow in ucursor:
                        urow[1] = result_overlap
                        ucursor.updateRow(urow)
            elif result_cross != 0:
                with arcpy.da.UpdateCursor(tmp_network_tbl, ["ReachID", "ERROR_CODE"], expr) as ucursor:
                    for urow in ucursor:
                        urow[1] = result_cross
                        ucursor.updateRow(urow)
            else:
                with arcpy.da.UpdateCursor(tmp_network_tbl, ["ReachID", "ERROR_CODE"], expr) as ucursor:
                    for urow in ucursor:
                        if urow[1] != 0:
                            pass
                        else:
                            urow[1] = 0
                            ucursor.updateRow(urow)

            # Clean up
            del urow, ucursor
            arcpy.Delete_management("sel_rch_lyr")
            arcpy.Delete_management("in_memory\sel_rch")

    return


def overlap(tmp_network_fc):
    # Set global constant
    ERROR_CODE = 4

    with arcpy.da.SearchCursor(tmp_network_fc, ['ReachID', 'SHAPE@']) as cursor:
        for r1,r2 in itertools.combinations(cursor, 2):
            if r1[1].overlaps(r2[1]):
                return ERROR_CODE
            else:
                return 0


def cross(tmp_network_fc):
    # Set global constant
    ERROR_CODE = 5

    with arcpy.da.SearchCursor(tmp_network_fc, ['ReachID', 'SHAPE@']) as cursor:
        for r1,r2 in itertools.combinations(cursor, 2):
            if r1[1].crosses(r2[1]):
                return ERROR_CODE
            else:
                return 0


# Disconnected reaches error
def disconnected(in_network_fc, tmp_network_tbl):
    arcpy.AddMessage("...disconnected reaches")

    ERROR_CODE = 6

    in_network_fc_lyr = "in_network_fc_lyr"
    arcpy.MakeFeatureLayer_management(in_network_fc, in_network_fc_lyr)

    # join topology table to stream network feature class, and select reaches not found in the topology table
    arcpy.AddJoin_management(in_network_fc_lyr, "ReachID", tmp_network_tbl, "ReachID", "KEEP_ALL")
    for field in arcpy.ListFields(in_network_fc_lyr, "*UpstreamID"):
        upstream_field = field.name
    expr = """"{0}" IS NOT NULL""".format(upstream_field)
    arcpy.SelectLayerByAttribute_management(in_network_fc_lyr, "NEW_SELECTION", expr)
    arcpy.SelectLayerByAttribute_management(in_network_fc_lyr, "SWITCH_SELECTION")
    arcpy.RemoveJoin_management(in_network_fc_lyr)

    # copy selected reaches to a temporary table and append to tmp_network_tbl
    arcpy.CopyRows_management(in_network_fc_lyr, r"in_memory\disconnected_reaches")
    arcpy.MakeTableView_management(r"in_memory\disconnected_reaches", "disconnected_view")
    arcpy.AddField_management("disconnected_view", "UpstreamID", "LONG")
    arcpy.AddField_management("disconnected_view", "TO_NODE", "DOUBLE")
    arcpy.AddField_management("disconnected_view", "FROM_NODE", "DOUBLE")
    arcpy.AddField_management("disconnected_view", "ERROR_CODE", "SHORT")
    with arcpy.da.SearchCursor("disconnected_view", ["ReachID", "UpstreamID", "TO_NODE", "FROM_NODE", "ERROR_CODE"]) as scursor:
        with arcpy.da.InsertCursor(tmp_network_tbl, ["ReachID", "UpstreamID", "TO_NODE", "FROM_NODE", "ERROR_CODE"]) as icursor:
            for srow in scursor:
                icursor.insertRow(srow)
        #del srow, scursor
        #del icursor

    arcpy.SelectLayerByAttribute_management(tmp_network_tbl, "NEW_SELECTION", """"UpstreamID" IS NULL""")
    with arcpy.da.UpdateCursor(tmp_network_tbl, ["ERROR_CODE"]) as ucursor:
        for urow in ucursor:
            if urow[0] == None:
                urow[0] = ERROR_CODE
                ucursor.updateRow(urow)
        #del urow, ucursor

    # clean up
    arcpy.SelectLayerByAttribute_management(tmp_network_tbl, "CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management(in_network_fc_lyr, "CLEAR_SELECTION")


# Find flow direction errors
def flow_direction(tmp_network_tbl):
    arcpy.AddMessage("...flow direction")

    ERROR_CODE = 7

    upstream_fields = ["UpstreamID","FROM_NODE","TO_NODE"]
    val_dict = {r[0]:(r[1:]) for r in arcpy.da.SearchCursor(tmp_network_tbl, upstream_fields)}
    update_fields = ["OID@","ReachID","UpstreamID","FROM_NODE","ERROR_CODE"]

    with arcpy.da.UpdateCursor(tmp_network_tbl, update_fields) as ucursor:
        for urow in ucursor:
            key_val = urow[1]
            if key_val in val_dict:
                if urow[1] != val_dict[key_val]:
                    if urow[3] == val_dict[key_val][0]:
                        urow[4] = ERROR_CODE
                        ucursor.updateRow(urow)
    return


# find potential miscellaneous errors
def other_errors(tmp_network_tbl):
    arcpy.AddMessage("...other potential issues")

    # Set global variables
    ERROR_CODE = 8

    # Select records UpstreamID == -11111
    expr = """"{0}" = {1}""".format("UpstreamID", -11111)
    arcpy.SelectLayerByAttribute_management(tmp_network_tbl,"NEW_SELECTION", expr)

    # Add error values to network table
    arcpy.CalculateField_management(tmp_network_tbl, "ERROR_CODE", ERROR_CODE, "PYTHON_9.3")
    arcpy.SelectLayerByAttribute_management(tmp_network_tbl, "CLEAR_SELECTION")


def main(in_network_fc, in_network_table, outflow_id):
    arcpy.AddMessage("Searching for errors: ")

    # Get file geodatabase from input stream network feature class
    file_gdb_path = arcpy.Describe(in_network_fc).path

    # Create temporary, in_memory version of stream network table
    if arcpy.Exists("in_network_fc"):
        arcpy.Delete_management("in_network_fc")
    if arcpy.Exists("in_network_table"):
        arcpy.Delete_management("in_network_table")
    if arcpy.Exists("tmp_memory_table"):
        arcpy.Delete_management("tmp_memory_table")
    arcpy.MakeTableView_management(in_network_table, "in_network_table_view")
    arcpy.CopyRows_management("in_network_table_view", r"in_memory\tmp_network_table")
    arcpy.MakeTableView_management(r"in_memory\tmp_network_table", "tmp_network_table_view")

    # add required fields
    list_fields = arcpy.ListFields("tmp_network_table_view", "ERROR_CODE")
    if len(list_fields) != 1:
        arcpy.AddField_management("tmp_network_table_view", "ERROR_CODE", "LONG")
        arcpy.CalculateField_management("tmp_network_table_view", "ERROR_CODE", "0", "PYTHON_9.3")

    # Find errors
    flow_direction("tmp_network_table_view")
    braids(in_network_fc, "tmp_network_table_view")
    duplicates(in_network_fc, "tmp_network_table_view")
    reach_pair_errors(in_network_fc, "tmp_network_table_view", outflow_id)
    disconnected(in_network_fc, "tmp_network_table_view")
    other_errors("tmp_network_table_view")

    # Clean up and write final error table
    oid_field = arcpy.Describe("tmp_network_table_view").OIDFieldName
    keep_fields = [oid_field, "ReachID", "ERROR_CODE"]
    list_obj = arcpy.ListFields("tmp_network_table_view")
    tmp_field_names = [f.name for f in list_obj]
    for field_name in tmp_field_names:
        if field_name not in keep_fields:
            arcpy.DeleteField_management("tmp_network_table_view", field_name)
    expr = """"{0}" > {1}""".format("ERROR_CODE", "0")
    arcpy.SelectLayerByAttribute_management("tmp_network_table_view", "NEW_SELECTION", expr)
    arcpy.CopyRows_management("tmp_network_table_view", file_gdb_path + "\NetworkErrors")