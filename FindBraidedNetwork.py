# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Find Braided Reaches in Stream Network                         #
# Purpose:                                                                    #
#                                                                             #
# Author:      Kelly Whitehead                                                #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Sept-30                                                   #
# Version:     0.1          Modified:                                         #
# Copyright:   (c) Kelly Whitehead 2014                                       #                                                #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

#Overview:
# Script to find reaches in a braided network
# User needs to ensure that flow direction is correct for braided reaches before building network table.
#
#Inputs:
# Line feature class
#
#Algorithm
#
#Requirements:
#
#Output Data Format
# Add IsBraidedReach bit (yes/no) field to main feature class

# # Import Modules # #
import os
import sys
import arcpy

# # Script Parameters # #
listBraidedReaches = [] ## Reaches part of a braided system

# # Functions # #
def findBraidedReaches(fcLines):
    # Clear temp data
    if arcpy.Exists("in_memory//DonutPolygons"):
        arcpy.Delete_management("in_memory//DonutPolygons")
    if arcpy.Exists("lyrDonuts"):
        arcpy.Delete_management("lyrDonuts")
    if arcpy.Exists("lyrBraidedReaches"):
        arcpy.Delete_management("lyrBraidedReaches")
        
    # Find Donut reaches
    arcpy.FeatureToPolygon_management(fcLines,"in_memory/DonutPolygons")
    arcpy.MakeFeatureLayer_management(fcLines,"lyrBraidedReaches")
    arcpy.MakeFeatureLayer_management("in_memory/DonutPolygons","lyrDonuts")
    arcpy.SelectLayerByLocation_management("lyrBraidedReaches","SHARE_A_LINE_SEGMENT_WITH","lyrDonuts",'',"NEW_SELECTION")
    arcpy.CalculateField_management("lyrBraidedReaches","IsBraidedReach",1)

def main(fcStreamNetwork):

    # Data Paths
    descStreamNetwork = arcpy.Describe(fcStreamNetwork)
    fileGDB = descStreamNetwork.path

    # Validation
    

    # PolylinePrep
    listFields = arcpy.ListFields(fcStreamNetwork,"IsBraidedReach")
    if len(listFields) is not 1:
        arcpy.AddField_management(fcStreamNetwork,"IsBraidedReach","SHORT")
    else:
        arcpy.CalculateField_management(fcStreamNetwork,"IsBraidedReach",0) #clear field

    # Process
    findBraidedReaches(fcStreamNetwork)


    # Cleanup

    return

# # Run as Script # # 
if __name__ == "__main__":
    inputPolylineFC = sys.argv[1] # Str Feature class path

    main(inputPolylineFC)