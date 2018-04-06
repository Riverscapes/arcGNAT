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
# Version:     0.2                                                            #
# Revised:     2017-Jan-8                                                     #
# Released:                                                                   #
#                                                                             #
# License:     MIT License                                                    #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

#Import modules
import arcpy
import networkx as nx
from lib import network as net

error_msg = "{0} module not installed. Please install {0} before executing the {1} tool."\
    .format('ogr', "Find Subnetworks")

try:
    import ogr
except ImportError:
    arcpy.AddError(error_msg)

arcpy.env.overwriteOutput = True


def find_errors(theNetwork, G):
    """
    This function attempt to find potential topology errors in the stream network.
    :param theNetwork:
    :param G: multidgraph
    :return:
    """
    net_ids = theNetwork.attribute_as_list(G, "_netid_")
    # iterate through list of network IDs generate attributes, and produce a subnetwork graph
    list_subnets = []
    for id in net_ids:
        arcpy.AddMessage("Finding errors for subnet {0}...".format(id))
        subnet_G = theNetwork.select_by_attribute(G, "_netid_", id)
        duplicates_G = theNetwork.error_dup(subnet_G)
        outflow_G = theNetwork.error_outflow(subnet_G)
        conf_G = theNetwork.error_confluence(subnet_G)
        # merge all error graphs
        error_G = nx.compose_all([subnet_G, duplicates_G, conf_G, outflow_G])
        list_subnets.append(error_G)
        arcpy.AddMessage("Subnetwork #{} complete...".format(id))

    # Union all subnetwork graphs
    union_G = nx.union_all(list_subnets)
    if theNetwork.check_attribute(union_G, "_edgetype_"):
        theNetwork.delete_attribute(union_G, "_edgetype_")
    return union_G


def main(in_shp, out_shp, bool_error=False):
    """
    The main processing module for the Find Subnetworks tool.
    :param in_shp: Stream network polyline feature class.
    :param out_workspace: Directory where tool output will be stored
    """
    arcpy.AddMessage("FSN: Finding and labeling subnetworks...")
    # remove GNAT fields if present
    for f in arcpy.ListFields(in_shp):
        if f.name[:1] == "_" and f.name[1:] == "_":
            arcpy.AddMessage("FSN: Deleting and replacing existing GNAT fields...")
            arcpy.DeleteField_management(in_shp, f.name)

    # calculate network ID
    theNetwork = net.Network(in_shp)
    list_SG = theNetwork.get_subgraphs()
    id_G = theNetwork.calc_network_id(list_SG)

    # find topology errors
    if bool_error:
        arcpy.AddMessage("FSN: Finding network topology errors...")
        error_G = find_errors(theNetwork, id_G)
        final_G = error_G
    else:
        final_G = id_G

    arcpy.AddMessage("FSN: Writing networkx graph to shapefile...")
    theNetwork._nx_to_shp(final_G, out_shp, bool_node = False)

    return
