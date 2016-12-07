Copy Stream BranchID Tool
=========================

This tool is used to move the BranchID from one stream network to another. The stream networks may be the same geometry, or similar geometry (i.e. Stream Network to Valley Bottom Centerline).

![](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/Images/CopyBranchID01.png)

> Figure: Stream Network BranchID's (blue) transferred to a Valley Centerline with similar (but not the same) geometry. The Valley Centerline now has the same BranchID (black).

This step is required if using the "Transfer by Branch" method in the [Transfer Line Attributes Too](), as both networks will need to have common Stream Branches.

_______________________________________________________________
## Usage
### Parameters

**Input Stream Network with BranchID**

This is the line network that contains the Stream BranchID _to be transferred_. This network should already have a [Stream BranchID](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Workflow/StreamBranches).

Requirements Include: 

* Features should be in a Projected Coordinate System, not Geographic.
* all appropriate lines are connected as a network.  This can be checked by running [Network Connectivity Tool](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/NetworkConnectivity) and rejoining broken lines
* no braids. Braids will cause the tool to get stuck in a loop.  Braids can be identified and isolated by running the [Find Braids in Network Tool](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/FindBraids).  Only one braid section should be identified as the main channel and retained.  The connector segments and side channel should be removed.  (GNIS name can be used as a guide to identify the main channel, too).  
* a File GDB Polyline Feature Class due to field requirements
* is NOT be Z or M enabled.
* (Untested) Singlepart features

**Stream BranchID Field**

Field that contains the Stream Branch ID. The default output from the Generate Stream Branch tool is `BranchID`.

**Input Target Line Network**

This is the line network that the Stream BranchID _will be transferred to_. 

Requirements Include: 

* in a Projected Coordinate System, not Geographic.
* all appropriate lines are connected as a network.  This can be checked by running [Network Connectivity Tool](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/NetworkConnectivity) and rejoining broken lines
* no braids. Braids will cause the tool to get stuck in a loop.  Braids can be identified and isolated by running the [Find Braids in Network Tool](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/FindBraids).  Only one braid section should be identified as the main channel and retained.  The connector segments and side channel should be removed.  (GNIS name can be used as a guide to identify the main channel, too).  
* a File GDB Polyline Feature Class due to field requirements
* is NOT be Z or M enabled.
* (Untested) Singlepart features

**Output Line Network with BranchID**

This is the name and location (in a fgdb) of the new line feature class that contains the transferred Stream Branch ID. The field name will be the same as the Stream BranchID field of the Input.

**Scratch Workspace**

You may use:

1. Create a new file GDB to save temporary processing files (useful for debugging).
3. If a workspace is not designated, the tool will use the "in_memory" workspace. You will not be able to view the temporary files, _but the processing speed will be much faster_.


### Geoprocessing Environments
 
* It is recommended to run this tool in 64-bit python geoprocessing.
* Geoprocessing Environments:
	* Disable Z and M if you encounter a topology error.


## Technical Background

### Calculation Method
The tool uses the following calculation method to copy the Stream Branch ID.


### Troubleshooting and Potential Issues

* This tool is currently set up around a specific workflow for generating stream branches. Skipping a workflow step or clean up process may result in erroneous results or tool failure.

### References and Resources