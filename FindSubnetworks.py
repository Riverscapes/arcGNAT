# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Find Subnetworks                                               #
# Purpose:     This tool finds disconnected subnetworks within a stream       #
#              network, then assigns a network identifier value to each       #
#              to each stream feature within the subnetwork.                  #
#                                                                             #
# Authors:     Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2017-Nov-27                                                    #
# Version:     0.1                                                            #
# Revised:     2017-Nov-27                                                    #
# Released:                                                                   #
#                                                                             #
# License:     MIT License                                                    #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

#Import modules
import os.path
import arcpy
import network as net

error_msg = "{0} module not installed. Please install {0} before executing the {1} tool."\
    .format('ogr', "Find Subnetworks")

try:
    import ogr
except ImportError:
    arcpy.AddError(error_msg)



def main(in_shp, out_workspace):
    """
    The main processing module for the Find Subnetworks tool.
    :param in_shp: Stream network polyline feature class.
    :param out_workspace: Directory where tool output will be stored
    """
    arcpy.AddMessage("FSN: Finding and labeling subnetworks...")
    # remove NetworkID field if it already present
    for f in arcpy.ListFields(in_shp):
        if f.name == "NetworkID":
            arcpy.AddMessage("FSN: Deleting and replacing existing network ID field...")
            arcpy.DeleteField_management(in_shp, f.name)

    # calculate network ID
    theNetwork = net.Network(in_shp)
    list_SG = theNetwork.get_subgraphs()
    id_G = theNetwork.calc_network_id(list_SG)
    theNetwork._nx_to_shp(id_G, out_workspace)

    return
