The **Calculate Stream Order** tool calculates the Strahler stream order for all reaches in a stream network polyline feature class. The output is a polyline feature class that is dissolved by sections between stream confluences. The stream order ttributes can then be transferred to other stream network datasets. Strahler order is also a useful attribute for improving line network routes. 

![](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/Images/StreamOrder01.png)

_______________________________________________________________
## Usage

### Geoprocessing Environment
 
* We recommended running this tool using 64-bit python geoprocessing.
* Disable Z and M geometry in the input stream network feature class Shape field when encountering topology errors.

### Input Parameters

**Input Stream Network**

Stream network polyline feature class that will be dissolved by stream order. 

Data requirements: 

* Projected coordinate system, not geographic.
* All appropriate polylines are connected as a network. This can be checked with the [Build Network Topology Table](https://github.com/SouthForkResearch/gnat/wiki/Build-Network-Topology-Table) and [Find Network Errors](https://github.com/SouthForkResearch/gnat/wiki/Find-Network-Errors) tools. The user can then manually rejoin disconnected stream reaches using editing tools in ArcMap.
* All braids removed. Braids can be identified and isolated by running the [Find Braids in Stream Network](https://github.com/SouthForkResearch/gnat/wiki/Find-Braids-in-Stream-Network) tool, or by the aforementioned [Find Network Errors](https://github.com/SouthForkResearch/gnat/wiki/Find-Network-Errors) tool. Only one braid segment should be identified as the main channel and retained. Connector segments and side channels should be removed. GNIS names can be used as a guide to identify the main channel.  
* File geodatabase polyline feature class (due to field requirements)
* Z and M geometry disabled for the Shape field.

**Downstream Reach ID**

`ObjectID` value of the downstream outlet reach.

**Output Line Network with Stream Order**

File name and directory location (in a file geodatabase) of the output polyline feature class that will include the stream order as an attribute.

**Output Junction Points**

File name and directory location (in a file geodatabase) of the output point feature class which includes locations of stream order transitions (used for splitting tributaries, see post processing step).

**Scratch Workspace** (Optional)

File geodatabase or folder to store temporary processing files. If a workspace is not designated, the tool will use the "in_memory" workspace. The temporary files will not be available for review, but the processing speed will be greatly improved.

### Outputs

**Output Line Network with Stream Order**

Output polyline feature class containing the same attributes as the input stream network, with the addition of a `StreamOrder` attribute field.

**Output Junction Points**

Output point feature class representing stream junctions of streams with the same Strahler order value.

_______________________________________________________________
## Technical Background

### Calculation Method

1. Dissolve the polyline network by junction points
  * Ignore braided stream reaches (should have been removed in manual preprocessing)
  * Convert multi-part to single-part
  * Unsplit polylines
2. Find headwaters (as initial `Stream_Order = 1`)
  * Identify as dangle
  * Ignore downstream ID segment
3. While features.getCount(`Stream_Order = 0`) not = total number of features
  * Cycle through stream order “pairs”
  * Intersect each set of pairs
  * Intersect this selection with features where `Stream_Order = 0`
  * Find the largest number in the pair
  * Calculate field based on pair
4. Update the current stream order

### Recommended Post-processing

The **Calculate Stream Order** tool generates a stream order for each segment/section of the stream. This can be used (along with other attributes, such as NHD GNIS_name) to generate stream branches. 

Use the [Generate Stream Branches ](https://github.com/SouthForkResearch/gnat/wiki/Generate-Stream-Branches) tool to generate stream branch ID values for each stream branch.

### Troubleshooting and Potential Issues

* Disconnected networks will result in an incorrect order number (order will reset to ‘1’ at all disconnected reaches)
* Braided reaches will cause the tool to loop, and terminate the process prematurely.

### References and Resources

* [http://spatial-analyst.net/ILWIS/htm/ilwisapp/drainage_network_ordering_functionality.htm](http://spatial-analyst.net/ILWIS/htm/ilwisapp/drainage_network_ordering_functionality.htm)