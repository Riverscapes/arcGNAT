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
# Revised:     2017-Dec-8                                                     #
# Released:                                                                   #
#                                                                             #
# License:     MIT License                                                    #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

#Import modules
import arcpy
import networkx as nx
import network as net

error_msg = "{0} module not installed. Please install {0} before executing the {1} tool."\
    .format('ogr', "Find Subnetworks")

try:
    import ogr
except ImportError:
    arcpy.AddError(error_msg)


def find_errors(theNetwork, G, oid_field):
    """
    This function attempt to find potential topology errors in the stream network.
    :param theNetwork:
    :param G:
    :param oid_field:
    :return:
    """
    net_ids = theNetwork.attribute_as_list(G, "_netid_")
    # iterate through list of network IDs generate attributes, and produce a subnetwork graph
    list_subnets = []
    for id in net_ids:
        subnet_G = theNetwork.select_by_attribute(G, "_netid_", id)
        duplicates_G = theNetwork.error_dup(subnet_G)
        outflow_G = theNetwork.error_outflow(subnet_G)
        outflow_edge = list((u,v,k,d) for u,v,k,d in outflow_G.edges_iter(data=True,keys=True)
                            if d['_edgetype_']=='outflow' and d['_err_out_']==0)
        if len(outflow_edge) == 1:
            source_node = outflow_edge[0][1]
            upstream_G = theNetwork.error_flow(subnet_G, source_node)
        else:
            upstream_G = nx.MultiDiGraph()
        # merge all error graphs
        erroronly_G = nx.compose_all([duplicates_G, upstream_G, outflow_G])
        error_G = nx.compose(subnet_G, erroronly_G)
        list_subnets.append(error_G)
        arcpy.AddMessage("Subnetwork #{} complete...".format(id))

    # Union all subnetwork graphs
    union_G = nx.union_all(list_subnets)
    return union_G



def main(in_shp, out_shp, bool_error=False):
    """
    The main processing module for the Find Subnetworks tool.
    :param in_shp: Stream network polyline feature class.
    :param out_workspace: Directory where tool output will be stored
    """
    arcpy.AddMessage("FSN: Finding and labeling subnetworks...")
    # remove NetworkID field if it already present
    for f in arcpy.ListFields(in_shp):
        if f.name == "_netid_":
            arcpy.AddMessage("FSN: Deleting and replacing existing network ID field...")
            arcpy.DeleteField_management(in_shp, f.name)

    # calculate network ID
    theNetwork = net.Network(in_shp)
    list_SG = theNetwork.get_subgraphs()
    id_G = theNetwork.calc_network_id(list_SG)

    # find topology errors
    if bool_error:
        arcpy.AddMessage("FSN: Finding network topology errors...")
        error_G = find_errors(theNetwork, id_G, "_FID_")
        final_G = nx.compose(id_G, error_G)
    else:
        final_G = id_G

    arcpy.AddMessage("FSN: Writing networkx graph to shapefile...")
    theNetwork._nx_to_shp(final_G, out_shp, bool_node = False)

    return
