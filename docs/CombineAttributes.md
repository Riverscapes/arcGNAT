The **Combine Attributes** tool merges feature attributes from two or more polyline feature classes into a single feature class.  

_______________________________________________________________
## Usage

### Geoprocessing Environment
* We recommend that the tool be run using 64-bit python geoprocessing.
* Disable Z and M geometry in the stream network Shape field.

### Input Parameters

[[images/combine_attributes_frm.png]]

**Input polyline feature classes**

Polyline feature classes representing linear stream networks.  Multiple inputs are allowed. 

**Bounding or buffer polygon feature class**

Polygon feature class that provides a spatial boundary for processing, which should geographically contain all input networks. The polygon will contain the Thiessen polygons used to split the the “To” line network based on the “From” networks. Stream networks that are located outside of this polygon boundary will not have attributes transferred.

**Is polygon segmented?** (optional)

`Checked`: the bounding polygon is divided based on the “From” line network (i.e. using the [Divide Polygon by Segments](https://github.com/SouthForkResearch/gnat/wiki/Divide-Polygon-by-Segments) tool). This will reduce the amount of processing needed to run the tool.

`Unchecked`: divide the bounding polygon into segments as part of the processing.

**Output polyline feature class**

Polyline feature class which includes all merged attributes.

_______________________________________________________________
## Technical Background

### Calculation Method

The **Combine Attributes** tool sends all input polyline feature classes in sequence to the [Transfer Line Attributes](https://github.com/SouthForkResearch/gnat/wiki/Transfer-Line-Attributes) tool.  The first polyline feature class in the list will have attributes transferred to it from all remaining feature classes in the list.