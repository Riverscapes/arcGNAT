# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Check Network Connectivity                                     #
# Purpose:                                                                    #
#                                                                             #
# Author:      Kelly Whitehead                                                #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Oct-16                                                    #
# Version:     0.2          Modified: 2014-dec-22                             #
# Copyright:   (c) Kelly Whitehead 2014                                       #                                     
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python


# # Import Modules # #
import os
import sys
import arcpy

lyrLineNetwork = "lyrLineNetwork"


def main(fcLineNetwork,intOutflowReachID):

    if arcpy.Exists(lyrLineNetwork):
        arcpy.Delete_management(lyrLineNetwork)
    arcpy.MakeFeatureLayer_management(fcLineNetwork,lyrLineNetwork)

    listFields = arcpy.ListFields(fcLineNetwork,"IsCon")
    if len(listFields) == 0:
        arcpy.AddField_management(fcLineNetwork,"IsCon","SHORT")
    arcpy.CalculateField_management(fcLineNetwork,"IsCon",0,"PYTHON")

    fieldID = arcpy.AddFieldDelimiters(fcLineNetwork,arcpy.Describe(fcLineNetwork).OIDFieldName)

    arcpy.SelectLayerByAttribute_management(lyrLineNetwork,"NEW_SELECTION", fieldID + " = " + str(intOutflowReachID))
    iPrevious = 0
    iCurrent = 1
    
    while iPrevious <> iCurrent:
        iPrevious = iCurrent
        arcpy.SelectLayerByLocation_management(lyrLineNetwork,"INTERSECT",lyrLineNetwork,'',"ADD_TO_SELECTION")
        iCurrent = int(arcpy.GetCount_management(lyrLineNetwork).getOutput(0))
        arcpy.AddMessage(str(iPrevious) + " | " + str(iCurrent))

    arcpy.CalculateField_management(lyrLineNetwork,"IsCon",1,"PYTHON")

    return


# # Run as Script # # 
if __name__ == "__main__":
    inputPolylineFC = sys.argv[1] # Str Feature class path
    inputOutflowReachID = sys.argv[2] # Int
    #boolClearTable = sys.argv[3]

    main(sys.argv[1],sys.argv[2])