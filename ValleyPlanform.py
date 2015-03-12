# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Valley Planform Tool                                           #
# Purpose:     Calculate Sinuosity Along Segments in a Stream                 #
#                                                                             #
# Author:      Kelly Whitehead                                                #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     0.1          Modified: 2015-Jan-08                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python


# # Import Modules # #
import sys
import arcpy
import gis_tools
import Sinuosity
import TransferAttributesToLine

def main(fcStreamCenterline,fcValleyCenterline,fcValleyBottomPolygon,outputFCSinuosityChannel,outputFCSinuosityValley,outputFCPlanform):
    
    tempWorkspace=arcpy.env.scratchWorkspace
    reload(TransferAttributesToLine)

    ## Calculate Valley Sinuosity for each Channel centerline segment
    if arcpy.Exists(outputFCSinuosityChannel):
        arcpy.Delete_management(outputFCSinuosityChannel)
    arcpy.CopyFeatures_management(fcStreamCenterline,outputFCSinuosityChannel)
    Sinuosity.main(outputFCSinuosityChannel,"Channel_Sinuosity")
    
    ## Calculate Centerline Sinuosity for each Valley centerline segment.
    if arcpy.Exists(outputFCSinuosityValley):
        arcpy.Delete_management(outputFCSinuosityValley)
    arcpy.CopyFeatures_management(fcValleyCenterline,outputFCSinuosityValley)
    Sinuosity.main(outputFCSinuosityValley,"Valley_Sinuosity")

    intRows = arcpy.GetCount_management(fcValleyBottomPolygon)
    #if intRows == 1:
    #    bool_IsSegmented = False
    #else:
    #    bool_IsSegmented = True
    bool_IsSegmented = False
    if arcpy.Exists(outputFCPlanform):
        arcpy.Delete_management(outputFCPlanform)

    ## Transfer Attributes to Stream Linework.
    TransferAttributesToLine.main(outputFCSinuosityValley,
                                  outputFCSinuosityChannel,
                                  fcValleyBottomPolygon,
                                  bool_IsSegmented,
                                  outputFCPlanform)

    ## Calculate Valley Planform for each segment
    fieldPlanform = gis_tools.resetField(outputFCPlanform,"Planform","DOUBLE")
    codeblock = """def calculatePlanform(channel,valley):
        if valley == 0:
            return -9999 
        else:
            return channel/valley """

    arcpy.CalculateField_management(outputFCPlanform,
                                    fieldPlanform,
                                    "calculatePlanform(!Channel_Sinuosity!,!Valley_Sinuosity!)",
                                    "PYTHON",
                                    codeblock
                                    )

    return





if __name__ == "__main__":


    main(sys.argv[1],sys.argv[2])