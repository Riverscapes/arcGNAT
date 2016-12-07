The **Segment Stream Network** tool splits stream reaches within a network into 
segments of equal, user-defined length. The tool produces a segmented stream 
network polyline feature class, a network feature class with stream order, 
and junction points representing confluences for stream reaches with the same 
stream order value. 

Several segmentation method options are available.
![Image: Segmentation Methods](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/Images/segmentation_method.png)

##Geoprocessing Environment##

* We recommend that the Segment Stream Network tool be run using 64-bit python geoprocessing.
* Disable Z and M values in the stream network shape field.

## Input Parameters
 
**Stream Network Polyline Feature Class**  

Polyline feature class representing the stream network for the analysis area.

* Requirements: 
    * Projected coordinate system, not geographic.
    * (Optional) All appropriate lines are connected as a network. This can be checked by running [Network Connectivity Tool](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/NetworkConnectivity) and rejoining broken lines. Alternatively, the user can find unconnected networks by building a network topology table with the [Build Network Topology Table](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/BuildNetworkTopologyTable) tool, finding errors using the [Find Errors](/KellyWhitehead/geomorphic-network-and-analysis-toolbox/wiki/Tool_Documentation/FindErrors) tools, then manually correcting topology errors.
    * File geodatabase polyline feature class due to field requirements
    * The network consists of single-part features

**Segment Length (Meters)**
  
The desired length of each stream segment, using the input stream network feature class linear unit. 
> Note: Due to floating point precision and tolerance of geometric measurements, the actual `Shape_Length` of the line segments will be vary slightly from this value. 

**Downstream Reach ID**
   
Object ID value of the stream reach that represents the outflow point (i.e. furthest downstream) for the stream network.

**Stream Name Field**
  
Attribute field (i.e. GNIS_Name) in the stream network polyline feature class that will be used by the internal stream ordering and branching processes. Stream reach records with a blank (i.e. ' ') or NULL value in this field will not be dissolved in these processes.

**Segmentation Method**

Three segmentation methods are available:

1. Remaining segment at inflow (top) of stream branch

2. Remaining segment at outflow (bottom) of stream branch

3. Divide remainder between all reaches per stream branch

**Output Segmented Line Network**
  
The feature class which will store the resulting segmented stream network. In addition, stream order and junction point feature classes are also output into the same file geodatabase.

### Calculation Method

This tool uses the following processing workflow:

1. Stream order is calculated.
2. The stream network is dissolved by stream branch.  Branch IDs are calculated.
3. A search cursor loops through the reach features
	* If `"Remaining segment at in flow (top) of stream branch"` or `"Remaining segment at out flow (bottom) of stream branch"`  is selected, then positions along the stream branch are found using the specified segment length, until the end of the branch is reached. These positions are stored as `Points`.
	* If `"Divide remainder between all segments per stream branch"`is specified, then the number of "positions" that can be made are determined by dividing the total branch length by the user-defined segment length and taking the integer of the result. Next, each position is found along the branch as a ratio of the position number and the total number of positions. This incorporates the 'remainder' evenly along the length of the stream branch.
4. The line network is split by the points created in step 3 (whichever method was used) to create the new segments.
5. A unique reach ID value is added to each of the new segments.