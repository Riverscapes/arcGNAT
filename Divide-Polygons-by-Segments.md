This utility tool divides a polygon (such as a channel buffer) using the segments from a flow or center line. This is useful for confinement calculations.

### Usage 
Make sure data is projected.
Segment the Flowline (i.e. centerline) as desired.


### Parameters

**Segmented Network Line of Polygon** 

Network Line of the polygon that will be used to divide the polygon into segments.

**Polygon to Segment**

Polygon that will be segmented by the centerline.

**Output Polygons**

Name and location of the output polygon feature class

**Scratch Workspace**

Create a file GDB to store temporary processing files

**Centerline Point Density (Meters)**

Density of Thiessen polygon seed points to use within the Junction Buffer. Higher density should result in a finer resolution of the segmented edges in the output polygon

**Junction Buffer (Meters)**

Buffer to limit the generation of Thiessen seed points around tributary junctions only. This is to reduce the amount of processing time.

### Geoprocessing Environments
* It is recommended to run this tool in 64-bit python geoprocessing.
* Disable Z and M if you encounter a topology error,.
___
### Technical Background

### Outputs##
Output Polygon
Polygon split at all segment and confluence junctions.


### Troubleshooting and Potential Bugs
Centerline runs outside of polygon
Overlapping polygon areas (at trib junctions) in the output polygon
Extra splits in the output polygon

### References and Resources