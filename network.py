#   Name:           Network
#   Description:    Main class used for building and manipulating
#                   network topologies.
#   Authors:        Jesse Langdon, jesse@southforkresearch.org
#                   Matt Reimer, matt@northarrowresearch.com
#   Created:        4/6/2017
#   Revised:        12/11/2017

import os
import sys
import ogr
import osr
import networkx as nx

from memory_profiler import profile

sys.setrecursionlimit(10000)

# global variables
fid = "_FID_"
edgetype = "_edgetype_"
nodetype = "_nodetype_"
netid = "_netid_"
calclen = "_calclen_"
riverkm = "_riverkm_"
streamorder = "_strmordr_"
errorflow = "_err_flow_"
errordup = "_err_dupe_"
errorout = "_err_out_"
errorconf = "_err_conf_"

class Network:

    def __init__(self, in_shp, msgcallback=None):
        """
        Main class for processing stream networks in GNAT.
        """
        self.msgcallback = msgcallback
        self.id_field = fid
        self.features = {}
        self.cols = []

        # get spatial reference
        self.data_src = in_shp

        # Convert shapefile to NX MultiDiGraph
        self._shp_to_nx()

    def _shp_to_nx(self, simplify=True, geom_attrs=True):
        """
        Re-purposed version of read_shp from nx
        :param simplify:
        :param geom_attrs:
        :return:
        """

        self.G = nx.MultiDiGraph()
        shp = ogr.Open(self.data_src)
        layer = shp.GetLayer()
        self.srs = layer.GetSpatialRef().ExportToWkt()

        for lyr in shp:
            self.fields = [x.GetName() for x in lyr.schema]
            for f in lyr:
                geo = f.geometry()
                flddata = [f.GetField(f.GetFieldIndex(x)) for x in self.fields]
                attributes = dict(zip(self.fields, flddata))
                # Add a new _FID_ field
                fid = f.GetFID()
                attributes[self.id_field] = fid
                attributes[calclen] = geo.Length()

                # Using layer level geometry type
                geo_type = geo.GetGeometryType()
                if geo_type == ogr.wkbLineString or geo_type == ogr.wkbMultiLineString:
                    for edge in self.edges_from_line(geo, attributes, simplify, geom_attrs):
                        e1, e2, attr = edge
                        self.features[fid] = attr
                        self.G.add_edge(tuple(e1), tuple(e2), key=attr[self.id_field], attr_dict=attr)
                    self.cols = self.features[self.features.keys()[0]].keys()
                else:
                    raise ImportError("GeometryType not supported. For now we only support LineString types.")

        return

    def _nx_to_shp(self, G, out_shp, bool_node):
        """
        This is a re-purposing of the NetworkX write_shp module with some minor changes.
        :param G: networkx directional graph
        :param out_dir: directory where output shapefiles will be written
        """

        # easier to debug in python if ogr throws exceptions
        ogr.UseExceptions()

        # set spatial reference for output shapefile
        srs = osr.SpatialReference()
        srs.ImportFromWkt(self.srs)

        def netgeometry(key, data):
            if 'Wkb' in data:
                geom = ogr.CreateGeometryFromWkb(data['Wkb'])
            elif 'Wkt' in data:
                geom = ogr.CreateGeometryFromWkt(data['Wkt'])
            elif type(key[0]).__name__ == 'tuple':  # edge keys are packed tuples
                geom = ogr.Geometry(ogr.wkbLineString)
                _from, _to = key[0], key[1]
                try:
                    geom.SetPoint(0, *_from)
                    geom.SetPoint(1, *_to)
                except TypeError:
                    # assume user used tuple of int and choked ogr
                    _ffrom = [float(x) for x in _from]
                    _fto = [float(x) for x in _to]
                    geom.SetPoint(0, *_ffrom)
                    geom.SetPoint(1, *_fto)
            else:
                geom = ogr.Geometry(ogr.wkbPoint)
                try:
                    geom.SetPoint(0, *key)
                except TypeError:
                    # assume user used tuple of int and choked ogr
                    fkey = [float(x) for x in key]
                    geom.SetPoint(0, *fkey)

            return geom

        # Create_feature with new optional attributes arg (should be dict type)
        def create_feature(geometry, lyr, attributes=None):
            feature = ogr.Feature(lyr.GetLayerDefn())
            feature.SetGeometry(g)
            if attributes != None:
                # Loop through attributes, assigning data to each field
                for field, data in attributes.items():
                    feature.SetField(field, data)
            lyr.CreateFeature(feature)
            feature.Destroy()

        def build_attrb_dict(self, lyr, data, fields):
            from collections import OrderedDict
            attributes = OrderedDict()
            ordered_data = order_attributes(self, data)
            # Loop through attribute data in edges dictionary
            for key, data in ordered_data.items():
                # Reject spatial data not required for attribute table
                if (key != 'Json' and key != 'Wkt' and key != 'Wkb'
                    and key != 'ShpName'):
                    # For all edges check/add field and data type to fields dict
                    # if key not in fields:
                    if key not in fields:
                        # Field not in previous edges so add to dict
                        if type(data) in OGRTypes:
                            fields[key] = OGRTypes[type(data)]
                        else:
                            # Data type not supported, default to string (char 80)
                            fields[key] = ogr.OFTString
                        newfield = ogr.FieldDefn(key, fields[key])
                        lyr.CreateField(newfield)
                        # Store the data from new field to dict for CreateLayer()
                        attributes[key] = data
                    else:
                        # Field already exists, add data to dict for CreateLayer()
                        attributes[key] = data
            return attributes

        def order_attributes(self, attrb_dict):
            # order dictionary attributes into list based on field list from input shapefile
            from collections import OrderedDict
            ordered_attrb = OrderedDict()
            for f in self.fields:
                for k, v in attrb_dict.iteritems():
                    if k == f:
                        ordered_attrb.update({k:v})
            for k, v, in attrb_dict.iteritems():
                if k.startswith('_') and k.endswith('_'):
                    ordered_attrb.update({k:v})
            return ordered_attrb

        # Set up output shapefiles
        base_name = os.path.basename(out_shp)
        shp_name = os.path.splitext(base_name)[0]
        dir_name = os.path.dirname(out_shp)
        node_name = "{}_nodes".format(shp_name)
        edge_name = "{}_edges".format(shp_name)
        drv = ogr.GetDriverByName("ESRI Shapefile")
        shpdir = drv.CreateDataSource("{0}".format(dir_name))

        # Conversion dict between python and ogr types
        OGRTypes = {int: ogr.OFTInteger, str: ogr.OFTString, float: ogr.OFTReal}

        # Write nodes
        if bool_node:
            try:
                shpdir.DeleteLayer(node_name)
            except:
                pass
            nodes = shpdir.CreateLayer(node_name, srs, ogr.wkbPoint)
            # New edge attribute write support merged into edge loop
            n_fields = {}  # storage for field names and their data types

            # Node loop
            for n in G:
                data = G.node[n]
                g = netgeometry(n, data)
                n_attributes = build_attrb_dict(self, nodes, data, n_fields)
                create_feature(g, nodes, n_attributes)
            nodes = None

        # Write edges
        try:
            shpdir.DeleteLayer(shp_name)
        except:
            pass

        edges = shpdir.CreateLayer(shp_name, srs, ogr.wkbLineString)
        # New edge attribute write support merged into edge loop
        e_fields = {}  # storage for field names and their data types

        # Edge loop
        for u,v,k,data in G.edges_iter(data=True,keys=True):
            g = netgeometry(k, data)
            e_attributes = build_attrb_dict(self, edges, data, e_fields)
            # Create the feature with geometry, passing new attribute data
            create_feature(g, edges, e_attributes)
        edges = None
        return

    def edges_from_line(self, geom, attrs, simplify=True, geom_attrs=True):
        """
        Re-purposed from the shape helper here:
        https://github.com/networkx/networkx/blob/master/networkx/readwrite/nx_shp.py
        :return:
        """
        if geom.GetGeometryType() == ogr.wkbLineString:
            if simplify:
                edge_attrs = attrs.copy()
                last = geom.GetPointCount() - 1
                if geom_attrs:
                    edge_attrs["Wkb"] = geom.ExportToWkb()
                    edge_attrs["Wkt"] = geom.ExportToWkt()
                    #edge_attrs["Json"] = geom.ExportToJson()
                yield (geom.GetPoint_2D(0), geom.GetPoint_2D(last), edge_attrs)
            else:
                for i in range(0, geom.GetPointCount() - 1):
                    pt1 = geom.GetPoint_2D(i)
                    pt2 = geom.GetPoint_2D(i + 1)
                    edge_attrs = attrs.copy()
                    if geom_attrs:
                        segment = ogr.Geometry(ogr.wkbLineString)
                        segment.AddPoint_2D(pt1[0], pt1[1])
                        segment.AddPoint_2D(pt2[0], pt2[1])
                        edge_attrs["Wkb"] = segment.ExportToWkb()
                        edge_attrs["Wkt"] = segment.ExportToWkt()
                        #edge_attrs["Json"] = segment.ExportToJson()
                        del segment
                    yield (pt1, pt2, edge_attrs)

        elif geom.GetGeometryType() == ogr.wkbMultiLineString:
            for i in range(geom.GetGeometryCount()):
                geom_i = geom.GetGeometryRef(i)
                for edge in self.edges_from_line(geom_i, attrs, simplify, geom_attrs):
                    yield edge

    def get_subgraphs(self):
        """
        Finds all subgraphs that are disconnected.
        :param self: graph must be undirected to use this method.
        """
        list_SG = list(nx.weakly_connected_component_subgraphs(self.G, copy=True))
        return list_SG

    def calc_network_id(self, list_SG):
        """
        Assigns a unique identifier to the edges within each subgraph
        :param list_SG: list of subgraphs
        :return: new graph with network IDs added as attribute
        """
        attrb_field = netid
        try:
            subgraph_count = 1
            for SG in list_SG:
                network_id = "{0}{1:0>3}".format("net", subgraph_count)
                self.add_attribute(SG, attrb_field, network_id)
                subgraph_count += 1
            union_SG = nx.union_all(list_SG)
            return union_SG
        except:
            raise IndexError  # not sure about this... will probably change later

    def get_graph_attributes(self, G, attrb_name):
        """Returns information on a graph"""
        total_edges = G.number_of_edges()
        edge_dict = nx.get_edge_attributes(G, attrb_name)
        if len(edge_dict) > 0:
            list_summary = []
            list_summary.append("Total number of edges in network: {0}".format(total_edges))
            networks = sorted(set(val for val in edge_dict.values()))
            for network in networks:
                select_G = self.select_by_attribute(G, attrb_name, network)
                select_edges = [(u,v,k,d) for u,v,k,d in select_G.edges(data=True, keys=True)]
                select_edges_len = len(select_edges)
                list_summary.append("Network ID: {0} - Total number of edges: {1}".format(network, select_edges_len))
            return list_summary
        else:
            list_summary = []
            return list_summary

    def attribute_as_list(self, G, attrb_name):
        """Returns unique values from graph attribute as list"""
        attrb_list = [d[attrb_name] for u,v,k,d in G.edges_iter(keys=True, data=True)]
        return list(sorted(set(attrb_list)))

    def check_attribute(self, G, attrb_name):
        data = next(d for u,v,k,d in G.edges_iter(keys=True, data=True))
        if attrb_name in data:
            return True

    def add_attribute(self, G, attrb_name, attrb_value):
        """
        Add a new attribute to a graph.
        :param G: input graph
        :param attrb_name: name of the attribute to be added
        :param attrb_value: new attribute value
        """
        dict = nx.get_edge_attributes(G, attrb_name)
        if len(dict) == 0:
            nx.set_edge_attributes(G, attrb_name, attrb_value)
        return

    def delete_attribute(self, G, attrb_name):
        for u,v,k,d in G.edges_iter(keys=True, data=True):
            del d[attrb_name]

    def select_by_attribute(self, G, attrb_name, attrb_value):
        """
        Select all edges within a multigraph based on the user-supplied attribute value
        :param G: networkx graph
        :param attrb_name: name of the attribute that will be used for the selection
        :param attrb_value: attribute value to select by
        """
        select_G = nx.MultiDiGraph()
        for u, v, k, d in G.edges_iter(data=True, keys=True):
            if d[attrb_name]==attrb_value:
                keys = G.get_edge_data(u,v).keys()
                # Loop through keys if more than one (for braids)
                for ky in keys:
                    data = G.get_edge_data(u, v, key=ky)
                    select_G.add_edge(u, v, ky, data)
        return select_G
        # else:
        #     print "ERROR: Attribute not found"
        #     select_G = nx.null_graph()
        #     return select_G

    def update_attribute(self, G, attrb_name, attrb_value):
        """
        Update existing attribute with new values
        :param G: networkx graph
        :param attrb_name: name of the attribute to be updated
        :param attrb_value: new attribute value
        """
        dict = nx.get_edge_attributes(G, attrb_name)
        if len(dict) > 0:
            nx.set_edge_attributes(G, attrb_name, attrb_value)
        return

    def get_outflow_edges(self, G, attrb_field, attrb_name):
        """
        Create graph with the outflow edge attributed
        :param G: networkx graph
        :param attrb_field: name of the attribute field
        :param attrb_name: attribute value
        :return outflow_G: graph with new headwater attribute
        """
        if nx.is_directed(G):
            # find the outflow node (should have zero outgoing edges, right?)
            outflow_edges = []
            list_edges = list(G.edges_iter(data=True, keys=True))
            list_successors = []
            for u,v,k,d in list_edges:
                out_edges = G.out_edges(v)
                list_successors.append(((u,v,k,d), len(out_edges)))
            for i in list_successors:
                if i[1] == 0:
                    # get the edge that is connected to outflow node
                    outflow_edges.append(i[0])
            outflow_G = nx.MultiDiGraph(outflow_edges)
            # set reach_type attribute for outflow and headwater edges
            self.update_attribute(outflow_G, attrb_field, attrb_name)
            return outflow_G
        else:
            outflow_G = nx.MultiDiGraph()
            return outflow_G

    def get_headwater_edges(self, G, attrb_field, attrb_name):
        """
        Create graph with the headwater edges attributed
        :param G: networkx graph
        :param attrb_field: name of the attribute field
        :param attrb_name: attribute value
        :return headwater_G: graph with new headwater edge type attribute
        """
        if nx.is_directed(G) and G.number_of_nodes() > 2:
            RG = nx.reverse(G, copy=True)
            list_nodes = [n for n in RG.nodes_iter()]
            list_successors = []
            for node in list_nodes:
                list_successors.append(tuple((node, len(RG.edges(node)))))
            headwater_G = nx.MultiDiGraph()
            for i in list_successors:
                if i[1] == 0:
                    headwater_edge = RG.in_edges(i[0], data=True, keys=True)
                    headwater_G.add_edge(*(headwater_edge.pop()))
            headwater_RG = nx.reverse(headwater_G, copy=True)
            self.update_attribute(headwater_RG, attrb_field, attrb_name)
            return headwater_RG
        else:
            headwater_G = nx.MultiDiGraph()
            return headwater_G

    def get_complex_braids(self, G, attrb_field, attrb_name):
        """
        Create graph with the complex braid edges attributed
        :param G: networkx graph
        :param attrb_field: name of the attribute field
        :param attrb_name: attribute value
        :return braid_G: graph with new attribute
        """
        if nx.is_directed(G):
            UG = nx.Graph(G)
            braid_G = nx.MultiDiGraph()
            list_cycles = nx.cycle_basis(UG)
            cycle_edges = [zip(nodes, (nodes[1:] + nodes[:1])) for nodes in list_cycles]
            for edge in G.edges(data=True, keys=True):
                is_edge = self.get_edge_in_cycle(edge, cycle_edges)
                if is_edge == True:
                    braid_G.add_edge(*edge)
            self.update_attribute(braid_G, attrb_field, attrb_name)
            return braid_G
        else:
            braid_complex_G = nx.MultiDiGraph()
            return braid_complex_G

    def get_simple_braids(self, G, attrb_field, attrb_name):
        """
        Create graph with the simple braid edges attributed
        :param G: networkx graph
        :param attrb_field: name of the attribute field
        :param attrb_name: attribute value
        :return braid_G: graph with new attribute
        """
        braid_simple_G = nx.MultiDiGraph()
        parallel_edges = []
        for e in G.edges_iter():
            keys = G.get_edge_data(*e).keys()
            if keys not in parallel_edges:
                if len(keys) == 2:
                    for k in keys:
                        data = G.get_edge_data(*e, key=k)
                        braid_simple_G.add_edge(e[0], e[1], key=k, attr_dict=data)
            parallel_edges.append(keys)
        self.update_attribute(braid_simple_G, attrb_field, attrb_name)
        return braid_simple_G

    def set_mainflow(self, G, name_field):
        """
        Create graph with main flow edges attributed
        :param G: networkx graph
        :param name_field: name of the edge type attribute field
        :return: graph with new attribute
        """
        b = 'braid'
        c = 'connector'
        m = 'mainflow'
        for u,v,k,d in G.edges_iter(data=True, keys=True):
            if d[name_field] != None and d[edgetype] == b or d[name_field] != None and d[edgetype] == c:
                data = G.get_edge_data(u, v, key=k)
                data[edgetype] = m
                G.add_edge(u, v, k, data)
        return

    def get_edge_in_cycle(self, edge, cycle_edges):
        """Determines if a specific edge is found in a cycle (i.e. braid)"""
        u, v, key, d = edge
        found = False
        for cycle in cycle_edges:
            if (u, v) in cycle or (v, u) in cycle:
                found = True
        return found

    def merge_subgraphs(self, G, outflow_G, headwater_G, braid_complex_G, braid_simple_G):
        """
        Join all subgraphs with the main graph
        :param G: networkx graph
        :param outflow_G: networkx graph composed of outflow edges
        :param headwater_G: networkx graph composed of headwater edges
        :param braid_complex_G: networkx graph composed of complex braid edges
        :param braid_simple_G: networkx graph composed of simple braid edges
        :return G_compose: final graph output with all reach type attributes included
        """
        G1 = nx.compose(G, outflow_G)
        G2 = nx.compose(G1, headwater_G)
        if braid_complex_G is not None:
            G3 = nx.compose(G2, braid_complex_G)
        if braid_simple_G is not None:
            gnat_G = nx.compose(G3, braid_simple_G)
        if braid_complex_G is None or braid_simple_G is None:
            gnat_G = G2

        return gnat_G

    def find_node_with_ID(self, G, id_field, id_value):
        """
        Helper function to find a node with a given ID field and value
        :param G: MultiDiGraph
        :param id_field: OBJECTID field
        :param id_value: OBJECTID value
        :return: single edge
        """
        return next(iter([e for e in G.edges_iter(data=True,keys=True) if G.get_edge_data(*e)[id_field] == id_value]), None)

    def get_unique_attrb(self, dict):
        """Returns unique attributes found in a dictionary"""
        unique_attrbs = sorted(set(dict.values()))
        return unique_attrbs

    def error_flow(self, G, src_node, ud=None):
        """Returns the first edges that do not conform to the flow direction
        implicit in defined source node.
        :param G: target digraph
        :param src_node: source node
        :param ud: undirected graph (faster iteration with setdirection)
        :upstream_G: networkx graph
        """
        RG = nx.reverse(G, copy=True)
        flipped_G = nx.MultiDiGraph()
        upstream_list = []
        gnodes = list(nx.dfs_preorder_nodes(RG, src_node))
        if not ud:
            ud = RG.to_undirected()
        connected = RG.edges(nx.dfs_tree(ud, src_node).nodes(), data=True, keys=True)

        for edge in connected:
            start = edge[0]
            end = edge[1]
            if end in gnodes and start not in gnodes:
                upstream_list.append(edge)

        # add new "error_flow" attribute to graph
        self.add_attribute(RG, errorflow, 0)  # add 'default' value
        for u,v,key,d in RG.edges_iter(keys=True,data=True):
            if (u,v,key,d) in upstream_list:
                flipped_G.add_edge(u,v,key,d)
        if flipped_G is not None:
            self.update_attribute(flipped_G, errorflow, 1)
        nx.reverse(RG)
        upstream_G = nx.compose(RG, flipped_G)
        return upstream_G

    def error_dup(self, G):
        """Returns parallel edges with identical lengths
        :param G: target multidigraph
        return: multidigraph with new error_dup attribute field
        """
        self.add_attribute(G, errordup, 0)
        duplicates_G = nx.MultiDiGraph()
        for e in G.edges_iter():
            keys = G.get_edge_data(*e).keys()
            if len(keys) == 2:
                length_list = []
                for k in keys:
                    data = G.get_edge_data(*e, key=k)
                    length_list.append((e[0],e[1],k,data))
                if length_list[0][3][calclen] == length_list[1][3][calclen]:
                    for i in length_list:
                        duplicates_G.add_edge(i[0],i[1],i[2],i[3])
        self.update_attribute(duplicates_G, errordup, 1)
        return duplicates_G

    def error_outflow(self, G):
        """Returns graph for network with more than one (or no) outflow edge.
        :param G: target multidigraph
        return: multidigraph with new error_outflow attribute field
        """
        self.add_attribute(G, errorout, 0)
        self.add_attribute(G, edgetype, "connector")
        outflow_G = self.get_outflow_edges(G, edgetype, "outflow")
        outflow_list = []
        for u,v,k,d in outflow_G.edges(data=True, keys=True):
            outflow_list.append((u,v,k,d))
        if len(outflow_list) > 1:
            outerror_G = outflow_G
            self.update_attribute(outerror_G, errorout, 1)

            return outerror_G
        elif not outflow_list:
            outerror_G = G
            self.update_attribute(outerror_G, errorout, 0)
            return outerror_G
        else:
            outerror_G = outflow_G
            return outerror_G

    def error_confluence(self, G):
        """Returns graph with edges that are connected to a confluence with
        more than two incoming edges (e.g. a confluence with three incoming
        edges).
        :param G: multidigraph
        :return: multidigraph with new _err_conf_ attribute field.
        """
        self.add_attribute(G, errorconf, 0)
        conf_G = nx.MultiDiGraph()
        for u, v, k, d in G.edges_iter(keys=True, data=True):
            in_edges = G.in_edges((u), keys=True, data=True)
            if len(in_edges) > 2:
                conf_G.add_edge(u, v, k, d)
        if conf_G.number_of_edges() > 0:
            self.update_attribute(conf_G, errorconf, 1)
        return conf_G

    def set_node_types(self, G):
        """Calculates node types for a graph which already has edge types"""
        node_dict = {}
        type_list = []
        edge_dict = nx.get_edge_attributes(G, edgetype)
        node_list = [n for n in G.nodes_iter()]
        # build dictionary of node with predecessors and successors nodes
        for node in node_list:
            node_pred = G.predecessors(node)
            node_succ = G.successors(node)
            node_dict[node] = [node_pred, node_succ]
        # build list of nodes with associated edge types. Can be duplicate node items in list.
        for nk, nv in node_dict.items():
            for ek, ev in edge_dict.items():
                if nk in ek:
                    type_list.append([nk, ev])

        # assign a node type code for each node
        for nd in G.nodes_iter():
            type_subset = [n[1] for n in type_list if nd == n[0]]
            if 'braid' in type_subset and 'headwater' in type_subset:
                t = 'BH'
            elif 'braid' in type_subset and 'connector' in type_subset:
                t = 'BC'
            elif 'braid' in type_subset and 'mainflow' in type_subset:
                t = 'BM'
            elif 'braid' in type_subset and 'outflow' in type_subset:
                t = 'BO'
            elif all(ts == 'braid' for ts in type_subset):
                t = 'BB'
            elif len(type_subset) == 2 and 'connector' in type_subset:
                t = 'CC'
            elif len(type_subset) == 2 and 'mainflow' in type_subset:
                t = 'CC'
            elif 'connector' in type_subset and 'headwater' in type_subset:
                t = 'HC'
            elif all(ts == 'connector' for ts in type_subset):
                t = 'TC'
            elif 'headwater' in type_subset and 'mainflow' in type_subset:
                t = 'TC'
            elif 'connector' in type_subset and 'mainflow' in type_subset:
                t = 'TC'
            elif 'headwater' in type_subset and 'outflow' in type_subset:
                t = 'TC'
            elif 'connector' in type_subset and 'outflow' in type_subset:
                t = 'TC'
            elif 'mainflow' in type_subset and 'outflow' in type_subset:
                t = 'TC'
            elif all(ts == 'mainflow' for ts in type_subset):
                t = 'TC'
            elif len(type_subset) == 1 and 'headwater' in type_subset:
                t = 'H'
            elif len(type_subset) == 1 and 'outflow' in type_subset:
                t = 'O'
            else:
                t = None
            G.node[nd][nodetype] = t
        return

    def calculate_river_km(self, G):
        """Calculates distance of each edge from outflow node, in kilometers."""
        outflow_G = self.select_by_attribute(G, edgetype, 'outflow')
        outflow_node = next(v for u, v, key, data in outflow_G.edges_iter(keys=True, data=True))
        self.add_attribute(G, riverkm, -9999)
        for u, v, key, data in G.edges_iter(keys=True, data=True):
            path_len = nx.shortest_path_length(G,
                                               source=u,
                                               target=outflow_node,
                                               weight=calclen)
            km_val = path_len / 1000
            data[riverkm] = km_val
        return

    def streamorder(self, G):
        """Calculates strahler stream order for all edges within a stream network graph.
        Requires an input graph that includes an  attribute field with edge types."""

        try:
            self.add_attribute(G, streamorder, -9999)
        except:
            self.update_attribute(G, streamorder, -9999)

        # Set up initial set of reaches so that headwaters = stream order 1
        headwater_G = self.get_headwater_edges(G, edgetype, 'headwater')
        for u, v, k, d in G.edges_iter(data=True, keys=True):
            if headwater_G.has_edge(u, v, key=k):
                G.add_edge(u, v, key=k, _strmordr_=1)
        del headwater_G

        select_G = self.select_by_attribute(G, streamorder, 1)
        select_edges = [(u,v,k,d) for u,v,k,d in select_G.edges(keys=True, data=True)]
        so_G = self.streamorder_iter(G, select_edges)
        return so_G

    # def streamorder_iter(self, G, select_G):
    #     """Recursively iterates through a graph (representing a stream network) and calculates
    #      stream order."""
    #
    #     def isdup(list):
    #         """Check for duplicate values in list, see Jochen Ritzel
    #         (https://stackoverflow.com/a/10343450/1618640)"""
    #         return len(list) - 1 == len(set(list))
    #
    #     # Find all successor edges from selected edges
    #     out_G = nx.MultiDiGraph()
    #     while select_G.number_of_edges() > 0:
    #         for u, v, k, d in G.edges_iter(data=True, keys=True):
    #             if select_G.has_edge(u, v, key=k):
    #                 out_edges = G.out_edges(v, data=True, keys=True)
    #                 for out_e in out_edges:
    #                     # find all predecessor edges for this successor edge
    #                     in_strmordr = []
    #                     in_edges = G.in_edges(out_e[0], data=True, keys=True)
    #                     for in_e in in_edges:
    #                         in_strmordr.append((in_e[3][streamorder],in_e[3][edgetype]))
    #                     # stream order determined by predecessor edge stream order
    #                     if len(in_strmordr) == 2:
    #                         so = [x[0] for x in in_strmordr]
    #                         types = [x[1] for x in in_strmordr]
    #                         if isdup(so) and 'braid' not in types:
    #                             out_e[3][streamorder] = (in_strmordr[0][0] + 1)
    #                         elif isdup(types) and types[0]=='braids':
    #                             out_e[3][streamorder] = (in_strmordr[0][0])
    #                         else:
    #                             out_e[3][streamorder] = max(so)
    #                     elif len(in_edges) == 1:
    #                         out_e[3][streamorder] = (in_strmordr[0][0])
    #                     if not out_G.has_edge(out_e[0], out_e[1], out_e[2]):
    #                         out_G.add_edge(*out_e)
    #                 #print "edge TARGET_FID:{0}".format(d['TARGET_FID'])
    #                 select_G.remove_edge(u, v, key=k)
    #     # recursion
    #     if out_G.number_of_edges() > 0:
    #         print "---out_G.number_of_edges: {0}".format(out_G.number_of_edges())
    #         compose_G = nx.compose(G, out_G)
    #         del select_G
    #         self.streamorder_iter(compose_G, out_G)
    #     else:
    #         compose_G = nx.compose(G, out_G)
    #         print "Stream ordering complete!"
    #         del select_G
    #         return compose_G

    def streamorder_iter(self, G, previous_edges):
        """Recursively iterates through a graph (representing a stream network) and calculates
         stream order."""

        def isdup(list):
            """Test for duplicate values in list, see Jochen Ritzel
            (https://stackoverflow.com/a/10343450/1618640)"""
            return len(list) - 1 == len(set(list))

        # Find all successor edges from selected edges
        next_edges = []
        while previous_edges:
            for u, v, k, d in G.edges_iter(data=True, keys=True):
                if (u,v,k,d) in previous_edges:
                    out_edges = G.out_edges(v, data=True, keys=True)
                    for out_e in out_edges:
                        # find all predecessor edges for this successor edge
                        in_strmordr = []
                        in_edges = G.in_edges(out_e[0], data=True, keys=True)
                        for in_e in in_edges:
                            in_strmordr.append((in_e[3][streamorder],in_e[3][edgetype]))
                        # stream order determined by predecessor edge stream order
                        if len(in_strmordr) == 2:
                            so = [x[0] for x in in_strmordr]
                            types = [x[1] for x in in_strmordr]
                            if isdup(so) and 'braid' not in types:
                                out_e[3][streamorder] = (in_strmordr[0][0] + 1)
                            elif isdup(types) and types[0]=='braids':
                                out_e[3][streamorder] = (in_strmordr[0][0])
                            else:
                                out_e[3][streamorder] = max(so)
                        elif len(in_edges) == 1:
                            out_e[3][streamorder] = (in_strmordr[0][0])
                        if out_e not in next_edges:
                            next_edges.append(out_e)
                    previous_edges.remove((u,v,k,d))
        G.add_edges_from(next_edges)
        # recursion
        if next_edges:
            print "---next_edges: {0}".format(len(next_edges))
            return self.streamorder_iter(G, next_edges)
        print "Stream ordering complete!"
        return G