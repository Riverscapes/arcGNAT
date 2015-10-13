# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Valley Planform Tool                                           #
# Purpose:     Calculate Valley Planform Along Segments in a Stream           #
#              Also calculates Sinuosity along segments in Stream and valley  #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Jan-08                                                    #
# Version:     1.3                                                            #
# Modified:    2015-Jul-29                                                    #
#                                                                             #
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

def main(fcStreamNetwork,fcValleyCenterline,fcValleyBottomPolygon,outputFCSinuosityChannel,outputFCSinuosityValley,outputFCPlanform,workspaceTemp="In_Memory"):
    
    ## Set Workspace and Reset Modules
    reload(TransferAttributesToLine)
    reload(Sinuosity)

    ## Calculate Valley Sinuosity for each Channel Network segment
    if arcpy.Exists(outputFCSinuosityChannel):
        arcpy.Delete_management(outputFCSinuosityChannel)
    arcpy.CopyFeatures_management(fcStreamNetwork,outputFCSinuosityChannel)
    Sinuosity.main(outputFCSinuosityChannel,"Channel_Sinuosity",workspaceTemp)
    
    ## Calculate Centerline Sinuosity for each Valley centerline segment.
    if arcpy.Exists(outputFCSinuosityValley):
        arcpy.Delete_management(outputFCSinuosityValley)
    arcpy.CopyFeatures_management(fcValleyCenterline,outputFCSinuosityValley)
    Sinuosity.main(outputFCSinuosityValley,"Valley_Sinuosity",workspaceTemp)

    ## Transfer Attributes to Stream Linework
    if arcpy.Exists(outputFCPlanform):
        arcpy.Delete_management(outputFCPlanform)
    TransferAttributesToLine.main(outputFCSinuosityValley,
                                  outputFCSinuosityChannel,
                                  "",
                                  outputFCPlanform,
                                  workspaceTemp)

    ## Calculate Planform for each segment
    # Planform = channel sinuosity/valley sinuosity
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

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5],
         sys.argv[6])