# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Check Network Connectivity                                     #
# Purpose:     Make sure all segments and branches are connected in a line    #
#              Network.                                                       #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2014-Oct-16                                                    # 
# Version:     1.3                                                            #
# Modified:    2015-Aug-12                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2014                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools

# # Main Function # # 
def main(fcStreamNetwork,
         strFieldID,
         intOutflowReachID):
    
    strConField = "IsCon"
    #strNetworkIDField = "NetworkID"

    lyrStreamNetwork = gis_tools.newDataset("LAYER","lyrStreamNetwork")
    arcpy.MakeFeatureLayer_management(fcStreamNetwork,lyrStreamNetwork)

    gis_tools.resetField(lyrStreamNetwork,strConField ,"LONG")
    arcpy.CalculateField_management(fcStreamNetwork,strConField,0,"PYTHON")

    #gis_tools.resetField(lyrStreamNetwork,strNetworkIDField,"LONG")

    fieldOID = arcpy.AddFieldDelimiters(fcStreamNetwork,strFieldID)
    #fieldNetworkID = arcpy.AddFieldDelimiters(fcStreamNetwork,strNetworkIDField)

    #for intOutflowReachID in list_intOutflowReachID:
    arcpy.SelectLayerByAttribute_management(lyrStreamNetwork,"NEW_SELECTION", fieldDownstreamID + " = " + str(intOutflowReachID))
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

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3])