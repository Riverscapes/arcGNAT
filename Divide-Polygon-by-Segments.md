The **Divide Polygons by Segments** utility tool splits a polygon (i.e. channel buffers, valley bottoms) using the segments from a stream flow or center line. This can be useful for confinement calculations.

_______________________________________________________________
## Usage 

### Geoprocessing Environments

* It is recommended to run this tool using 64-bit python geoprocessing.
* Disable Z and M geometry in the Shapfe field if topology errors are encountered.
* Input data should be in a projected spatial reference system, not geographic.
* Segment the flowline (i.e. centerline) as desired using the [Segment Stream Network](https://github.com/SouthForkResearch/gnat/wiki/Segment-Stream-Network) tool.

### Input Parameters
**Segmented Centerline of Polygon** 

Segmented stream network polyline feature class that will be used to divide the polygon into segments.

**Polygon to Segment**

Polygon feature class to be segmented by the centerline.

**Output Segmented Polygon**

File name and directory location of the output polygon feature class.

**Scratch Workspace (optional)**

File geodatabase or folder for storing temporary processing files.

**Centerline Point Density (Meters) (optional)**

Density of Thiessen polygon seed points to use within the junction buffer. Higher density should result in a finer resolution of the segmented edges in the output polygon.

**Junction Buffer (Meters) (optional)**

Buffer to limit the generation of Thiessen seed points around tributary junctions only. Can reduce processing time.

### Outputs##

**Output Polygon**

Polygon split at segment and confluence junctions.

_______________________________________________________________
## Technical Background

### Troubleshooting and Potential Bugs

* Centerline runs outside of polygon
* Overlapping polygon areas (at tributary confluences) in the output polygon
* Extraneous splits in the output polygon