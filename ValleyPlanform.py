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

def main(fcStreamNetwork,fcValleyCenterline,fcValleyBottomPolygon,outputFCSinuosityChannel,outputFCSinuosityValley,outputFCPlanform,workspaceTemp="in_memory"):
    
    # Set Workspace and Reset Modules
    reload(TransferAttributesToLine)
    reload(Sinuosity)

    # Calculate valley sinuosity for each channel network segment
    if arcpy.Exists(outputFCSinuosityChannel):
        arcpy.Delete_management(outputFCSinuosityChannel)
    Sinuosity.main(fcStreamNetwork, outputFCSinuosityChannel, "C_Sin", workspaceTemp)
    
    # Calculate centerline sinuosity for each valley centerline segment.
    if arcpy.Exists(outputFCSinuosityValley):
        arcpy.Delete_management(outputFCSinuosityValley)
    Sinuosity.main(fcValleyCenterline, outputFCSinuosityValley, "V_Sin", workspaceTemp)

    # Transfer attributes to stream network polyline feature class
    if arcpy.Exists(outputFCPlanform):
        arcpy.Delete_management(outputFCPlanform)
    TransferAttributesToLine.main(outputFCSinuosityValley,
                                  outputFCSinuosityChannel,
                                  outputFCPlanform,
                                  workspaceTemp)

    # Calculate planform for each segment
    # Planform = channel sinuosity/valley sinuosity
    fieldPlanform = gis_tools.resetField(outputFCPlanform,"Planform","DOUBLE")
    codeblock = """def calculatePlanform(channel,valley):
        if valley == 0:
            return -9999 
        else:
            return channel/valley """

    arcpy.CalculateField_management(outputFCPlanform,
                                    fieldPlanform,
                                    "calculatePlanform(!C_Sin!,!V_Sin!)",
                                    "PYTHON",
                                    codeblock
                                    )

    keepFields = [arcpy.Describe(outputFCPlanform).OIDFieldName,
                  arcpy.Describe(outputFCPlanform).shapeFieldName,
                  "Planform"]
    dropFields = [dropField.name for dropField in arcpy.ListFields(outputFCPlanform)]
    arcpy.MakeTableView_management(outputFCPlanform, "fcOutputView")
    for dropField in dropFields:
        if dropField not in keepFields:
            arcpy.DeleteField_management("fcOutputView", dropField)


    return

if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5],
         sys.argv[6])