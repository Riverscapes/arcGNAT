---
title: Stream Network Preparation
---


## Step 1 - Stream Network Preparation

Generally, the primary reason a user will want to use GNAT will be to produce a stream network dataset that is segmented using the **Segment Stream Network** tool.  In order for a segmentation process to be successful, that tool requires a stream network that is free from topological errors. For GNAT, we define a topological clean network based on the following criteria:

* No disconnected stream networks or reaches
* No braids
* No duplicate reaches
* No overlapping reaches
* No crossed reaches (i.e. a canal that crosses over a stream)
* All digitized flow directions are downstream

The first two tools found in GNAT under `Step 1 - Stream Network Preperation` - **Build Network Topology Table** and **Find Network Features** - are intended to be used iteratively, ultimately producing a topologically-clean stream network that will serve as an input to the **Segment Stream Network** tool.  The following steps are a suggested workflow for producing such a network.

### Suggested Workflow for Step 1

##### Pre-processing and Building Network Topology

1. Create a workspace (folder or file geodatabase) that will store all interim data products.
  * ** *Please Note* ** - When creating or using a Riverscapes project, please ensure that all interim, working data products are stored **separately** from where Riverscapes project files are stored.  Do NOT use datasets stored in Riverscape project folders for active processing in the tools.
2. Add the stream network polyline feature class (shapefile or file geodatabase feature class) that will serve as the data source to an ArcMap.
3. Determine the stream reach feature within this network feature class that is the downstream or "outflow" segment in the network, and find that feature's `ObjectID` or `FID` value. If the user is unfamiliar with the geography of the stream network, symbolize the stream network using errors to determine flow direction, or use a digital elevation model (DEM) for visual context 
4. Run the **Build Network Topology** tool, which produces:
  * New polyline feature class, with the a suffix "run01" appended to the input dataset name
  * _StreamNetwork_ table.
5. Run the **Find Network Features** tool
  * Supply the aforementioned outputs from the **Build Network Topology** tool. Do NOT use the original network feature class input.  ONLY use the output dataset with the 
"run01" suffix.
  * Produces _NetworkFeatures_ table.

##### Finding and Fixing Topology Errors
1. In ArcMap, add the processed stream network polyline feature class (with the "run01" suffix) and the _NetworkFeatures_ table.  Join the _NetworkFeatures_ to the processed network, based on the common `ReachID` attribute field.
2. Symbolize the processed stream network polyline feature class using the `feature_code`.
3. Manually edit topological errors, including:
	- connect disconnected stream reaches
	- remove duplicates
	- edit vertices of overlapping reaches
	- flip direction of reaches with upstream flow
4. After manually editing the processed stream network feature class, rerun the **Build Network Topology** using the edited stream network feature class.
5. The resulting network feature class with have a suffix of "run02" appended to the dataset net.  Go back to set 1 of this section, find and fix remaining errors.  Multiple iterations of this process may be required.