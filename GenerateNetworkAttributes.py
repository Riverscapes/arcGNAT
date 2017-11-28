# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Generate Network Attributes                                    #
# Purpose:     The Generate Network Attributes tool generates a series of     #
#              attributes that describe a stream network.                     #
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

# Import modules
import arcpy
import network as net


def main(in_shp, out_workspace):
    """
    Iterates through all identified subnetworks and generates network attributes
    which are added as new attribute fields.
    :param in_shp: input stream network shapefile
    :param out_workspace: directory where output files will be written
    """
    arcpy.AddMessage("Generating network attributes...")
    theNetwork = net.Network(in_shp)
    # get list of network ID values
    net_ids = theNetwork.attribute_as_list(theNetwork.G, "NetworkID")

    # iterate through list of network IDs and generate attributes
    if theNetwork.gnat_G is None:
        for id in net_ids:
            subnet_G = theNetwork.select_by_attribute(theNetwork.G, "NetworkID", id)
            theNetwork.add_attribute(subnet_G, "edge_type", "connector")
            outflow_G = theNetwork.get_outflow_edges(subnet_G, "edge_type", "outflow")
            headwater_G = theNetwork.get_headwater_edges(subnet_G, "edge_type", "headwater")
            braid_complex_G = theNetwork.get_complex_braids(subnet_G, "edge_type", "braid")
            braid_simple_G = theNetwork.get_simple_braids(subnet_G, "edge_type", "braid")
            gnat_G = theNetwork.merge_subgraphs(subnet_G,
                                                outflow_G,
                                                headwater_G,
                                                braid_complex_G,
                                                braid_simple_G)
            fields = arcpy.ListFields(in_shp, "GNIS_Name")
            if len(fields) != 0:
                theNetwork.set_mainflow(gnat_G, "GNIS_Name")
            theNetwork.set_node_types()
            theNetwork._nx_to_shp(theNetwork.gnat_G, out_workspace)

    return
