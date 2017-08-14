# file name:	clear_inmem.py
# description:	This python module finds and deletes all feature classes and tables
#				that are stored in the in_memory space.
# author:		Jesse Langdon
# dependencies: ESRI arcpy module
# notes:        This module is derived from a code snippet posted by jamesfreddyc on geonet.esri.com
#               on September 15, 2014. https://geonet.esri.com/thread/90555.

import arcpy

def main():
    arcpy.env.workspace = r"in_memory"
    arcpy.AddMessage("Deleting in_memory data...")

    list_fc = arcpy.ListFeatureClasses()
    list_tbl = arcpy.ListTables()

    ### for each FeatClass in the list of fcs's, delete it.
    for f in list_fc:
        arcpy.Delete_management(f)
        ### for each TableClass in the list of tab's, delete it.
    for t in list_tbl:
        arcpy.Delete_management(t)