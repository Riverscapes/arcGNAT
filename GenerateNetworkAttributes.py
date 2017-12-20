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
import os.path
import arcpy
import networkx as nx
import network as net
import gis_tools

import_msg = "{0} module not installed. Please install {0} before executing the {1} tool."\
    .format('ogr', "Generate Network Attributes")

try:
    import ogr
except ImportError:
    arcpy.AddError(import_msg)

def check_field(in_shp, field_name):
    fieldnames = [field.name for field in arcpy.ListFields(in_shp)]
    if field_name in fieldnames:
        return True

# def get_fieldmap(in_network, in_gnis_pnt):
#     fm = arcpy.FieldMappings()
#
#     # Add all fields from inputs.
#     fm.addTable(in_network)
#     fm.addTable(in_gnis_pnt)
#
#     # Name of field to keep
#     keep = ["GNIS_Name"]
#
#     # Remove all output fields you don't want.
#     for field in fm.fields:
#         if field.name not in keep:
#             fm.removeFieldMap(fm.findFieldMapIndex(field.name))
#
#     return fm
#
# def prep_network(in_shp, temp_wspace):
#     # Preprocess network
#     network_dslv = gis_tools.newGISDataset(temp_wspace, "GNAT_SO_NetworkDissolved")
#     gnis_pnt = gis_tools.newGISDataset(temp_wspace, "GNAT_SO_NetworkDslv_pnt")
#     network_gnis = gis_tools.newGISDataset(temp_wspace, "GNAT_SO_NetworkDslv_GNIS_join")
#     arcpy.Dissolve_management(in_shp, network_dslv, multi_part="SINGLE_PART",
#                               unsplit_lines="DISSOLVE_LINES")
#     if check_field(in_shp, "GNIS_Name"):
#         arcpy.FeatureToPoint_management(in_shp, gnis_pnt,"INSIDE")
#         fieldmapping = get_fieldmap(network_dslv, gnis_pnt)
#         arcpy.SpatialJoin_analysis(network_dslv, gnis_pnt, network_gnis,"JOIN_ONE_TO_ONE","KEEP_ALL",
#                                    fieldmapping,"WITHIN_A_DISTANCE", "1 Meters", "#")
#         return network_gnis
#     else:
#         arcpy.AddError("{0} attribute field not found in {1}".format("GNIS_Name", os.path.basename(in_shp)))

def main(in_shp, riverkm_bool, out_shp, temp_workspace):
    """
    Iterates through all identified subnetworks and generates network attributes
    which are added as new attribute fields.
    :param in_shp: input stream network shapefile
    :param out_workspace: directory where output files will be written
    """

    # attribute fields
    edgetype = "_edgetype_"
    netid = "_netid_"
    streamname = "GNIS_Name"

    arcpy.AddMessage("GNA: Generating network attributes...")
    arcpy.AddMessage("GNA: Converting shapefile to a NetworkX graph...")
    #prep_shp = prep_network(in_shp, temp_workspace)
    theNetwork = net.Network(in_shp)
    arcpy.AddMessage("GNA: Getting list of network IDs...")

    if theNetwork.check_attribute(theNetwork.G, netid):
        net_ids = theNetwork.attribute_as_list(theNetwork.G, netid)
    else:
        net_ids = []
        arcpy.AddError("ERROR: {} attribute field not found! The network should first be processed through"
                       "the Find Subnetworks Tool.".format(netid))


    if theNetwork.check_attribute(theNetwork.G, edgetype):
        theNetwork.delete_attribute(theNetwork.G, edgetype)

    # iterate through list of network IDs generate attributes, and produce a subnetwork graph
    list_subnets = []
    for id in net_ids:
        subnet_G = theNetwork.select_by_attribute(theNetwork.G, netid, id)
        theNetwork.add_attribute(subnet_G, edgetype, "connector")
        arcpy.AddMessage("GNA: Finding the outflow...")
        outflow_G = theNetwork.get_outflow_edges(subnet_G, edgetype, "outflow")
        arcpy.AddMessage("GNA: Finding headwaters...")
        headwater_G = theNetwork.get_headwater_edges(subnet_G, edgetype, "headwater")
        arcpy.AddMessage("GNA: Finding complex braids...")
        braid_complex_G = theNetwork.get_complex_braids(subnet_G, edgetype, "braid")
        arcpy.AddMessage("GNA: Finding simple braids...")
        braid_simple_G = theNetwork.get_simple_braids(subnet_G, edgetype, "braid")
        arcpy.AddMessage("GNA: Merging all edge types...")
        gnat_G = theNetwork.merge_subgraphs(subnet_G,
                                            outflow_G,
                                            headwater_G,
                                            braid_complex_G,
                                            braid_simple_G)
        stream_field = arcpy.ListFields(in_shp, streamname)
        if len(stream_field) != 0:
            theNetwork.set_mainflow(gnat_G, streamname)
        theNetwork.set_node_types(gnat_G)

        # River kilometers
        if riverkm_bool == True:
            arcpy.AddMessage("GNA: Calculating river kilometers...")
            theNetwork.calculate_river_km(gnat_G)

        # # Stream order
        # arcpy.AddMessage("GNA: Calculating stream order...")
        # theNetwork.streamorder(gnat_G)

        list_subnets.append(gnat_G)
        arcpy.AddMessage("Network ID {0} processed...".format(id))

    # Union all subnetwork graphs
    arcpy.AddMessage("GNA: Merging all subnetworks...")
    theNetwork.G = nx.union_all(list_subnets)

    # Convert graph to shapefile and write to disk
    arcpy.AddMessage("GNA: Writing to shapefile...")
    theNetwork._nx_to_shp(theNetwork.G, out_shp, bool_node=True)

    return
