---
title: Stream Network Preparation
---


## Step 1 - Stream Network Preparation

One of the primary reasons a user may want to use GNAT will be to produce a stream network dataset that is segmented 
using the **Segment Stream Network** tool. In order for a segmentation process to be successful, that tool requires a 
stream network that is free from topological errors, with all subnetwork identified. For GNAT, we define a topological 
lean network based on the following criteria:

* No duplicate reaches
* Only one outflow per network
* All digitized flow directions are downstream

The first tool found in GNAT under `Analyze Network Attributes > Step 1 - Stream Network Preperation` is the **Find 
Subnetworks** tool. This tools is intended to be run iteratively, ultimately producing a topologically-clean stream 
network that will serve as an input for the **Generate Network Attributes** tool. The end goal of the workflow described here
is a topologically clean, attributed shapefile that can serve as an input for the **Segment Stream Network** tool.
The following steps are a suggested workflow for producing such a network.

### Suggested Workflow for Step 1

##### Identifying subnetworks and fixing topology errors

1. Create a workspace (folder or file geodatabase) that will store all interim data products.
  * ***Please Note***:  When creating or using a Riverscapes project, please ensure that all interim, working data 
  products are stored **separately** from where Riverscapes project files are stored.  Do NOT use datasets stored in 
  Riverscape project folders for active processing in the tools.
2. If this is a USGS NHD dataset, which includes an attribute field called `FType`, we recommend removing all features
where `FType = 336'`.  These features represent canals within the stream network, and can cause problems with network
topology.
3. Add the stream network shapefile as an input to the **Find Subnetworks** tool.  Ideally, this should be an NHD flowline dataset,
and include a stream name attribute field such as `GNIS_Name`.
4. Do _NOT_ choose the `Find topology errors` option.
5. Run the **Find Subnetworks** tool, which produces:
  * a new shapefile, with the following attribute fields added:
    * `_FID_` : unique identifier for each line feature
    * `_netid_` : unique identifier for each subnetwork
6. The user should no symbolize the output shapefile in ArcMap using the `_netid_` attribute field, by assigning a unique 
random color for each netid value. This will highlight all of the subnetworks found by the tool. The user must now decide 
which subnetworks are disconnected erroneously, and which subnetworks should stay disconnected (or subnetworks that can 
be discarded entirely).

![find_subnetworks_output.PNG]({{site.baseurl}}/images/find_subnetworks_output.PNG)

6. Rerun the **Find Subnetworks** tool again with the edited shapefile as input, but this time select the 
`Find topology errors` option.
7. If the `Find topology errors` option is selected, the resulting output shapefile will include an additional three
attribute fields:
  * `_err_dupe_` : boolean value indicates if the line feature is a duplicate of another feature (based on calculate length).
  * `_err_conf_` : boolean value indicates if the line feature has an upstream flow direction.
  * `_err_out_` : boolean indicates either a problem with flow direction (multiple reachs flowing to the same node) or a
subnetwork where the number of outflow features != 0.
8. Add this output to ArcMap and symblize using the error fields. By highlighting the location
of the errors, the user can then using ArcMap editing tools to manually correct these features.
9. At this point, the user can choose to continue running the **Find Subnetworks** tool until no errors are found.

##### Generate network attributes and stream order

10. Using a shapefile representing a topologically clean network with subnetworks identified, run the **Generate Network
Attributes** tool. This tool iterates through each subnetwork within the shapefile, and labels each feature with an 
'edge type'. Edge types are based on the topological context of each feature in relation to the rest of the features in
subnetwork. Edge types include:
* headwaters
* connectors
* mainflow
* braids
* outflow

![network_attrb_edges.PNG]({{site.baseurl}}/images/network_attrb_edges.PNG)

11. After processing is finished, the edge type classification of output shapefile should be reviewed in ArcMap, with symbolization based on the
`_edgetype_` attribute field.
12. Finally, the output from the **Generate Network Attributes** tool should serve as the input for the **Generate Stream
Order** tool. Stream order will be calculated separately for each subnetwork found within the network shapefile.