# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Transfer Line Branch ID Tool                                   #
# Purpose:     Transfer Line Branch ID from one line layer to another         #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-Aug-20                                                    #
# Version:     1.3                                                            #
# Modified:    2015-Aug-20                                                   #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import sys
import arcpy
import gis_tools

# # Main Function # #
def main(inputStreamBranchNetwork,
         inputBranchIDFieldName,
         inputTargetLineNetwork,
         outputTransferredNetwork,
         scratchWorkspace):

    gis_tools.resetData(outputTransferredNetwork)
    arcpy.Copy_management(inputTargetLineNetwork,outputTransferredNetwork)

    if len(arcpy.ListFields(outputTransferredNetwork,inputBranchIDFieldName)) == 1:
        arcpy.DeleteField_management(outputTransferredNetwork,inputBranchIDFieldName)

    fcCentroids = gis_tools.newGISDataset(scratchWorkspace,"GNAT_CBID_Centroids")
    arcpy.FeatureVerticesToPoints_management(outputTransferredNetwork,fcCentroids,"MID")

    arcpy.Near_analysis(fcCentroids,inputStreamBranchNetwork)

    arcpy.JoinField_management(fcCentroids,
                               "Near_FID",
                               inputStreamBranchNetwork,
                               arcpy.Describe(inputStreamBranchNetwork).OIDFieldName,
                               inputBranchIDFieldName)

    arcpy.JoinField_management(outputTransferredNetwork,
                               arcpy.Describe(outputTransferredNetwork).OIDFieldName,
                               fcCentroids,
                               "ORIG_FID",
                               inputBranchIDFieldName)

    return

# # Run as Script # #
if __name__ == "__main__":

    main(sys.argv[1],
         sys.argv[2],
         sys.argv[3],
         sys.argv[4],
         sys.argv[5])