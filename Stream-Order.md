The **Stream Order** tool calculates Strahler stream order for all reaches in a stream network polyline feature class. The output is a polyline network feature class that is dissolved by sections between stream confluences.  These attributes can then be transferred to any Strahler is a useful attribute for improving line network routes. 

![](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/Images/StreamOrder01.png)

### Geoprocessing Environment
 
* It is recommended to run this tool in 64-bit python geoprocessing.
* Disable Z and M geometry in the Shape filed when encountering topology errors in ArcMap.
_______________________________________________________________
## Input Parameters

**Input Stream Network**

This is the line network needs to be dissolved by stream order. 

Requirements Include: 

* Projected Coordinate System, not Geographic.
* All appropriate lines are connected as a network.  This can be checked by running [Network Connectivity Tool](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/NetworkConnectivity) and rejoining broken lines.
* All braids removed. Braids will cause the tool to get stuck in a loop.  Braids can be identified and isolated by running the [Find Braids in Network Tool](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/FindBraids).  Only one braid section should be identified as the main channel and retained.  The connector segments and side channel should be removed.  (GNIS name can be used as a guide to identify the main channel, too).  
* File GDB Polyline Feature Class (due to field requirements)
* is NOT be Z or M enabled.

**Downstream Reach ID**

`ObjectID` of the downstream outlet reach.

**Output Line Network with Stream Order**

This is the name and location (in a fgdb) of the new line feature class that contains the stream order.

**Output Junction Points**

This is the name and location (in a fgdb) of the new point feature class of the locations of stream order transitions (used for splitting tributaries, see post processing step).

**Scratch Workspace** (Optional)

You may use:

1. Create a new file GDB to save temporary processing files (useful for debugging).
3. If a workspace is not designated, the tool will use the "in_memory" workspace. You will not be able to view the temporary files, _but the processing speed will be much faster_.

## Outputs

**Output Line Network with Stream Order**

This output will contain the same attributes as the Input Stream Network, with the addition of a `StreamOrder` Field.

**Output Junction Points**


##Calculation Method
This tool uses the following calculation method to generate Stream Order:

1. Dissolve the Line Network by Junctions
	1. Ignore Braided sections (should have been removed in manual preprocessing)
	1. Multipart to SinglePart
	1. unsplit lines
1. Find headwaters (as initial stream order = 1)
	1. Dangles
	1. Ignore downstream id segment
1. while features.getCount(Stream_Order=0) not = total number of features
	1. Cycle through stream order “pairs”
		1. Intersect each set of pairs
		1. Intersect this selection with features Stream_Order=0
			1. Find the largest number in the pair
			1. Calculate field based on pair.
	1. Update the Current Stream Order

## Recommended Post Processing Steps

The stream order tool generates a stream order for each segment/section of the stream. This can be used (along with other attributes, such as NHD GNIS_name) to generate Stream Branches. 

Use the [Generate Stream Branches Tool]() to generate Stream Branch ID's for each stream branch.

## Troubleshooting and Potential Issues

- Disconnected network
	- Must be connected by definition. Run Check Connectivity tool prior and return error if not all connected.
 	- Will cause incorrect order number (order will reset to ‘1’ at all disconnected reaches)
- Braids
	- WILL CAUSE THE TOOL TO GET STUCK IN A LOOP
	- Treat Braids as Multipart features?
	- Also depends on how segmentation will work
- "Line Number" is the same as the last iteration           
        - Cancel the process

        - Run the Find Dangles and Remove Duplicates tool to remove any duplicate line segments

        - Run the Find Crossing Network Lines tool to make sure you do not have more than 3 lines meeting

        - Review the lines in which fall in the Stream Order section (New Stream Order 1, 2 etc.)
- Only generates Strahler order. Do we need/want the other method as well (not sure how long it would take to add this in)?
- It took 16min to run the MFJD. The tool is optimized for processing the upper reaches, but slows way down as you move downstream. I feel like it might take much longer for 1) bigger datasets with more junctions and 2) every order of stream magnitude added. I can try to optimize it if we find the processing painfully slow.

## References and Resources

* [http://spatial-analyst.net/ILWIS/htm/ilwisapp/drainage_network_ordering_functionality.htm](http://spatial-analyst.net/ILWIS/htm/ilwisapp/drainage_network_ordering_functionality.htm)