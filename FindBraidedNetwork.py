# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Find Braided Reaches in Stream Network                         #
# Purpose:     Find Braided Reaches as part of network preprocessing steps.   #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Sept-30                                                   #
# Version:     1.1                                                            #
# Modified:    2015-Apr-27                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2014                                       #
#                                                                             #
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

# # Main Function # #
def main(fcStreamNetwork):

    # Data Paths
    descStreamNetwork = arcpy.Describe(fcStreamNetwork)
    fileGDB = descStreamNetwork.path

    # PolylinePrep
    listFields = arcpy.ListFields(fcStreamNetwork,"IsBraided")
    if len(listFields) is not 1:
        arcpy.AddField_management(fcStreamNetwork,"IsBraided","SHORT")
    arcpy.CalculateField_management(fcStreamNetwork,"IsBraided",0,"PYTHON") #clear field

    # Process
    findBraidedReaches(fcStreamNetwork)

    return

# # Other Functions # #
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
    arcpy.CalculateField_management("lyrBraidedReaches","IsBraided",1,"PYTHON")

# # Run as Script # # 
if __name__ == "__main__":

    main(sys.argv[1])