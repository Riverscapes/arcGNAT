The **Transfer Line Attributes** tool transfers attributes between stream network polyline feature classes, using a segmented polygon approach. The segmented polygons are generated using Thiessen polygons in the **Divide Polygons by Segment** tool. Alternatively, this tool can use BranchID's from both networks to better manage tributary junctions. 

## Usage

* Make sure both input datasets are in (the same) **Projected** Coordinate System.
* Make sure From network is segmented (the "To" network may also be segmented) and attributed as desired.

### Parameters
**Input “From” Line Network**

The line network whose attributes will be transferred from. This network is used to ‘resegment’ the “To” line network.

**Input “To” Line Network**

The line network that will receive the attributes from the “From” line network. This line network will retain its segmentation and attributes, but will also be resegmented based on the transfer of the “From” line network. This allows both the new and original attributes to exist on the line network.

**Bounding or “Buffer” Polygon**

A polygon that contains both line networks (i.e. the valley bottom polygon). This is used to contain the thiessen polygons used to split the the “To” line network based on the “From” network. [Note: this may be depreciated in the future if determined it is not needed.]

**Is Polygon Segmented?**

True: The polygon is segmented based on the “From” line network (i.e. using the Divide Polygon by Segments Tool). This will reduce the amount of processing needed to run the tool.
False: This Tool will Divide the Polygon into segments as part of the processing.

**Output Line Network**

Polyline Feature class (in FGDB) that will contain the output line network with transferred (and original) attributes.

### Geoprocessing Environments

* It is recommended to run this tool in 64-bit python geoprocessing.
* Disable Z and M if you encounter a topology error.
____
## Technical Background
### Calculation Method

1. Divide polygon into Segments based on segmentation/junctions (See Divide polygon by segments tool) based on the “From” line network.
2. Split “To” line network based on the intersection of the Divided polygons.
3. Transfer “From” network OID’s to Polygon Segments, then to the “To” line network
4. Join table of “From” network to the “To” network  based on OID

### Potential Issues and Bugs
* Trib Junctions
* Null (Thiessen Polygon issue?)
* Outside of ‘Boundary” polygon