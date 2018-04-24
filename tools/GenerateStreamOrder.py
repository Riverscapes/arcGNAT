# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Name:        Generate Stream Order                                          #
# Purpose:     Calculates Strahler stream order for a stream network polyline #
#              feature class                                                  #
#                                                                             #
# Author:      Jesse Langdon (jesse@southforkresearch.org)                    #
#              South Fork Research, Inc                                       #
#              Seattle, Washington                                            #
#                                                                             #
# Created:     2017-Dec-29                                                    #
# Modified:    2017-Dec-29                                                    #
#                                                                             #
# License:     MIT                                                            #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#!/usr/bin/env python

import os
import gc
import arcpy
import networkx as nx
from lib import gis_tools, network as net
import FindSubnetworks
import GenerateNetworkAttributes

arcpy.env.overwriteOutput = True


def check_field(in_shp, field_name):
    fieldnames = [field.name for field in arcpy.ListFields(in_shp)]
    if field_name in fieldnames:
        return True


def get_fieldmap(in_network, in_gnis_pnt, name_field):
    fm = arcpy.FieldMappings()

    # Add all fields from inputs.
    fm.addTable(in_network)
    fm.addTable(in_gnis_pnt)

    # Name of field to keep
    keep = [name_field]

    # Remove all output fields you don't want.
    for field in fm.fields:
        if field.name not in keep:
            fm.removeFieldMap(fm.findFieldMapIndex(field.name))

    return fm

def dslv_network(in_shp, name_field, temp_wspace):
    # Preprocess network
    network_dslv = gis_tools.newGISDataset(temp_wspace, "GNAT_SO_NetworkDissolved")
    gnis_pnt = gis_tools.newGISDataset(temp_wspace, "GNAT_SO_NetworkDslv_pnt")
    network_gnis = gis_tools.newGISDataset(temp_wspace, "GNAT_SO_NetworkDslv_GNIS_join")
    arcpy.Dissolve_management(in_shp, network_dslv, multi_part="SINGLE_PART", unsplit_lines="DISSOLVE_LINES")
    if check_field(in_shp, name_field):
        arcpy.FeatureToPoint_management(in_shp, gnis_pnt,"INSIDE")
        fieldmapping = get_fieldmap(network_dslv, gnis_pnt, name_field)
        arcpy.SpatialJoin_analysis(network_dslv, gnis_pnt, network_gnis,"JOIN_ONE_TO_ONE","KEEP_ALL",
                                   fieldmapping,"WITHIN_A_DISTANCE", "1 Meters", "#")
        return network_gnis
    else:
        arcpy.AddError("{0} attribute field not found in {1}".format("GNIS_Name", os.path.basename(in_shp)))


def main(in_shp, name_field, out_shp, temp_wspace):
    """Main function to calculate Strahler stream order for an input stream network.
    :param in_shp: Shapefile output, which is the output from Find Subnetworks tool.
    :param temp_wspace: Temporary workspace to store intermediate datasets.
    :param out_shp: Stream network shapefile with stream order attribute field.
    """

    gc.enable()
    arcpy.AddMessage("SO: Initiating Generate Stream Order tool...")

    # Empty the temporary workspace
    temp_files = os.listdir(temp_wspace)
    for temp_file in temp_files:
        os.remove("{0}\\{1}".format(temp_wspace, temp_file))

    # Dissolve the network and split at intersections
    arcpy.AddMessage("SO: Dissolving input shapefile...")
    dslv_shp = dslv_network(in_shp, name_field, temp_wspace)

    # Find subnetworks
    subnet_shp = "{0}\\{1}".format(temp_wspace, "GNAT_SO_subnetworks.shp")
    FindSubnetworks.main(dslv_shp, subnet_shp, False)

    # Generate network attributes
    attrb_shp = "{0}\\{1}".format(temp_wspace, "GNAT_SO_attributed_network.shp")
    GenerateNetworkAttributes.main(subnet_shp, name_field, attrb_shp, False)

    # Calculate stream order
    arcpy.AddMessage("SO: Calcuating stream order...")
    arcpy.AddMessage("SO: Converting shapefile to a NetworkX graph...")
    theNetwork = net.Network(attrb_shp)

    # Iterate through subnetworks
    arcpy.AddMessage("SO: Getting list of network IDs...")
    net_ids = theNetwork.attribute_as_list(theNetwork.G, "_netid_")
    list_subnets = []
    for id in net_ids:
        subnet_G = theNetwork.select_by_attribute(theNetwork.G, "_netid_", id)
        streamorder_G = theNetwork.streamorder(subnet_G)
        list_subnets.append(streamorder_G)
    arcpy.AddMessage("SO: Merging all subnetworks...")
    theNetwork.G = nx.union_all(list_subnets)

    streamorder_shp = "{0}\\{1}".format(temp_wspace, "GNAT_SO_streamorder.shp")
    theNetwork._nx_to_shp(theNetwork.G, streamorder_shp, bool_node=False)
    # Intersect stream order output shapefile with original network shapefile
    fields = arcpy.ListFields(streamorder_shp)
    keep_fields = [f.name for f in fields if f.type == "OID" or f.type == "Geometry" or f.name == "_strmordr_"]
    for f in fields:
        if f.name not in keep_fields:
            arcpy.DeleteField_management(streamorder_shp, f.name)
    arcpy.Intersect_analysis([in_shp, streamorder_shp], out_shp, "NO_FID")

    return
