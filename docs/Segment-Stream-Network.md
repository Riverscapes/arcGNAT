---
title: Segment Stream Network
---


The **Segment Stream Network** tool splits a stream network into 
segments of equal, user-defined lengths. The tool produces a segmented stream 
network polyline feature class, a network feature class with stream order, 
and junction points representing confluences for stream reaches with the same 
stream order value. 

The tool offers three segmentation methods for handling the 'leftover' or 'slivers' of stream length that occur when a stream reach is not equally divisible by the user-provided segmentation length.  (see Segmentation Method section below).
![methods]({{site.baseurl}}/images/seg_methods.png)

_______________________________________________________________
## Tool Usage

The segmentation tool can be used in either a GNAT Project or as a stand-alone tool.

### Project Mode

1.  Make sure at least one (1) GNAT realization has been generated for the GNAT project.
2. Specify the  **project.rs.xml** file for the GNAT project.
3. Select the **Realization Name** that contains the realization that will be segmented.
4. Provide a **Segmentation Name** to uniquely identify (within the realization) the results of this segmentation run.
5. **Stream Network Polyline Feature Class**  The input feature class will be automatically selected based on the realization that is selected


3. **Segment Length (Meters)** Specify the desired length of each stream segment, using the input stream network feature class linear unit. 

   > Note: Due to floating point precision and tolerance of geometric measurements, the actual `Shape_Length` of the line segments will vary slightly from this value. 


4. **Downstream Reach ID** Specify the Object ID value of the stream reach that represents the outflow point (i.e. farthest downstream) for the stream network.

5. **Stream Name Field** Select the Attribute field (i.e. GNIS_Name) in the stream network polyline feature class that will be used to dissolve the stream network into new stream reaches before segmentation. Stream reach records with a blank (i.e. ' ') or NULL values in this field will not be dissolved.

6. **Segmentation Method** When a stream reach is segmented there is almost always a sliver of stream length that remains after segmentation occurs.  For example, if a stream reach is 3145m long and the segmentation length is 500m, 6 500m segments will be generated and there will be a 145m sliver of stream remaining.  The tool has three different methods for handling the 145m section: 

   Three segmentation methods are available:

   - Remaining segment sliver at inflow (top) of stream reach (6 500m segments and 1 145m segment)
   - Remaining segment sliver at outflow (bottom) of stream reach (6 500m segments and 1 145m segment)
   - Divide remainder sliver length between all reaches per stream reach (6 525m segments)

7. **Merge attributes and geometry from input stream network with output? (optional)** If this option is selected, the Segmentation tool will produce a stream network feature class which is the result of intersecting the original input stream network feature class with the segmented stream network polyline feature class. The resulting feature class will include the original feature attributes, and the `LineOID` attribute field produced by the segmentation process.

8. **Output Segmented Line Network** *Ignore this parameter when in Project Mode, even if the output location looks incorrect!*

9. Click OK to run the tool.

![form]({{site.baseurl}}/images/seg_form.PNG)

### Non-Project Mode

1. Leave the  **project.rs.xml**, **Realization Name** and **Segmentation Name** parameters empty.
2. **Stream Network Polyline Feature Class**  Select the polyline feature class that will need to be segmented

- Requirements: 
  - Projected coordinate system, not geographic.
  - (Optional) All appropriate lines are connected as a network. The user can find unconnected stream reaches by building a network topology table with the [Build Network Topology Table](http://gnat.riverscapes.xyz/Build-Network-Topology-Table) tool, finding errors using the [Find Network Features](http://gnat.riverscapes.xyz/Find-Network-Features) tool, then manually correcting topology errors using editing tools in ArcMap.
  - The network consists of single-part features only.

3. **Segment Length (Meters)** The desired length of each stream segment, using the input stream network feature class linear unit. 

> Note: Due to floating point precision and tolerance of geometric measurements, the actual `Shape_Length` of the line segments will vary slightly from this value. 

4. **Downstream Reach ID** The Object ID value of the stream reach that represents the outflow point (i.e. farthest downstream) for the stream network.

5. **Stream Name Field** The Attribute field (i.e. GNIS_Name) in the stream network polyline feature class that will be used to dissolve the stream network into new stream reaches before segmentation. Stream reach records with a blank (i.e. ' ') or NULL values in this field will not be dissolved.

6. **Segmentation Method** When a stream reach is segmented there is almost always a sliver of stream length that remains after segmentation occurs.  For example, if a stream reach is 3145m long and the segmentation length is 500m, 6 500m segments will be generated and there will be a 145m sliver of stream remaining.  The tool has three different methods for handling the 145m section: 

   Three segmentation methods are available:

   - Remaining segment sliver at inflow (top) of stream reach (6 500m segments and 1 145m segment)
   - Remaining segment sliver at outflow (bottom) of stream reach (6 500m segments and 1 145m segment)
   - Divide remainder sliver length between all reaches per stream reach (6 525m segments)

7. **Merge attributes and geometry from input stream network with output? (optional)** If this option is selected, the Segmentation tool will produce a stream network feature class which is the result of intersecting the original input stream network feature class with the segmented stream network polyline feature class. The resulting feature class will include the original feature attributes, and the `LineOID` attribute field produced by the segmentation process.

8. **Output Segmented Line Network** Name of the feature class which will store the resulting segmented stream network. In addition, stream order, junction point, and stream node feature classes are also output into the same workspace.


------

# About

### Outputs

**Segmented stream network feature class**

Polyline feature class representing a network segmented into user-defined lengths.

**strm_branch**

Polyline feature class representing stream branches. Generated during tool processing.

**strm_junctions**

Point feature class representing stream junctions where streams have the same stream order. 

**strm_node**

Point feature class representing confluences within the stream network.

### Methods

This tool uses the following processing workflow:

1. Determine stream order for each connected network.  If the number of networks >1, then stream order is calculated for each network section independently. 
2. The stream network is dissolved by stream branch. Branch IDs are calculated.
3. A search cursor loops through the reach features
   - If `"Remaining segment at in flow (top) of stream branch"` or `"Remaining segment at out flow (bottom) of stream branch"` is selected, then positions along the stream branch are found using the specified segment length, until the end of the branch is reached. These positions are stored as `Points`.
   - If `"Divide remainder between all segments per stream branch"`is specified, then the number of "positions" that can be made are determined by dividing the total branch length by the user-defined segment length and taking the integer of the result. Next, each position is found along the branch as a ratio of the position number and the total number of positions. This incorporates the 'remainder' evenly along the length of the stream branch.
4. The line network is split by the points created in step 3 (whichever method was used) to create the new segments.
5. A unique reach ID value is added to each of the new segments.

