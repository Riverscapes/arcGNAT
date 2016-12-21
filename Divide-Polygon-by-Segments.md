The **Divide Polygons by Segments** utility tool splits a polygon (i.e. channel buffers, valley bottoms) using the segments from a stream flow or center line. This can be useful for confinement calculations.

_______________________________________________________________
## Usage 

### Geoprocessing Environments

* We recommended running this tool with 64-bit python geoprocessing.
* Disable Z and M geometry in the Shape field if topology errors are encountered.
* Input data should be in a projected spatial reference system, not geographic.
* Segment the flowline (i.e. centerline) as desired using the [Segment Stream Network](https://github.com/SouthForkResearch/gnat/wiki/Segment-Stream-Network) tool.

### Input Parameters

[[images/divide_polygon_by_segments_form.PNG]]

**Segmented Polyline Feature Class** 

Segmented stream network or centerline polyline feature class that will be used to divide the polygon into segments.

**Polygon Feature Class to Segment**

Polygon feature class to be segmented by the segmented polyline feature class.

**Output Segmented Polygon Feature Class**

File name and directory location of the output segmented polygon feature class.

**Scratch Workspace (optional)**

File geodatabase or folder for storing temporary processing data files.  

**Centerline Point Density (Meters) (optional)**

Density of Thiessan polygon seed point use within the junction buffer. Higher density should result in a finer resolution of the segmented edges in the output polygon feature class.

**Junction Buffer Distance (Meters) (optional)**

Buffer to limit the generation of Thiessen seed points around tributary junctions only. This parameter can reduce processing time.

### Outputs##

**Output Polygon**

Polygon feature class with splits at segment and confluence junctions.

_______________________________________________________________
## Technical Background

### Troubleshooting and Potential Bugs

* Centerline runs outside of polygon
* Overlapping polygon areas (at tributary confluences) in the output polygon
* Extraneous splits in the output polygon