# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Moving Window Analysis for Line Network                        #
# Purpose:     Run a generic moving window analysis for a variable along a    #
#              line network.                                                  #
#                                                                             #
# Author:      Kelly Whitehead (kelly@southforkresearch.org)                  #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2015-May-05                                                    # 
# Version:     1.2                                                            #
# Modified:    2015-May-05                                                    #
#                                                                             #
# Copyright:   (c) Kelly Whitehead 2015                                       #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

# # Import Modules # #
import os
import sys
import arcpy
import gis_tools

# # Main Function # # 
def main(
    fcLineNetwork,
    fieldStreamID,
    fieldAttribute,
    dblSeedDistance,
    dblWindowSize,
    boolOverlap=False,
    tempWorkspace=arcpy.env.scratchWorkspace):
    """Perform a Moving Window Analysis on a Line Network."""

    fcLineNetworkDissolved = gis_tools.newGISDataset(tempWorkspace,"GNAT_MWA_LineNetworkDissolved")
    arcpy.Dissolve_management(fcLineNetwork,fcLineNetworkDissolved,fieldStreamID,multi_part=False,unsplit_lines=True)

    fcSeedPoints = gis_tools.pointsAlongLine(tempWorkspace,"GNAT_MWA_SeedPoints")
    gis_tools.pointsAlongLine(fcLineNetworkDissolved,dblSeedDistance,fcSeedPoints)

    


    #fcLineSections = gis_tools.newGISDataset(tempWorkspace,"GNAT_MWA_LineSections")
    #arcpy.SplitLineAtPoint_management(fcLineNetworkDissolved,fcSeedPoints,fcLineSections,"1 METERS")

    gis_tools.addUniqueIDField(fcLineSections,"SectionID")
    
    fcLineSectionsAttributed = gis_tools.newGISDataset(tempWorkspace,"GNAT_MWA_LineSectionsAttributed")
    arcpy.Intersect_analysis([fcLineNetwork,fcLineSections],fcLineSectionsAttributed,"ALL",output_type="LINE")

    ## Build Window Table
    ## for StreamID in line network
    ##     create feature layer only on streamID
    ##     for point in seed points, 
    ##         select intersect line sections
    ##         write interation 1 ids
    ##         for iteration in number of iterations based on window size,
    ##             select intersect based on current selection in line sections (i.e. expand selection on lines)
    ##             write iteration n ids
    ##         clear selection

    ## Moving Window calculations
    tblSummaryStats = gis_tools.newGISDataset(tempWorkspace,"GNAT_MWA_SummaryStats")
    arcpy.Statistics_analysis(fcLineSectionsAttributed, tblSummaryStats,"Shape_Length SUM","SectionID;IsConfined")
    tblSummaryStatsPivot = gis_tools.newGISDataset(tempWorkspace,"GNAT_MWA_SummaryStatsPivot")
    arcpy.PivotTable_management(tblSummaryStats,"SectionID","IsConfined","SUM_Shape_Length",tblSummaryStatsPivot)
    

    return

if __name__ == "__main__":

    main(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4],
        sys.argv[5],
        sys.argv[6],
        sys.argv[7],
        sys.argv[8])