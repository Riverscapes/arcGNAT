The **Stream Sinuosity and Planform** tool calculates sinuosity (per polyline feature) for valley centerline and stream network features. The tool also transfers the valley sinuosity to the stream network and calculates river planform attribute.

_______________________________________________________________
## Usage

### Geoprocessing Environments ###
* All inputs must be in the same projected coordinate system.
* We recommended running this tool with 64-bit python geoprocessing.
* Disable Z and M geometry in the Shape field if topology errors are encountered.

### Input Parameters

**Input Segmented Stream Network**

Segmented stream network polyline feature class (i.e. flowline, centerline, etc). Stream sinuosity values will be calculated for each segment.

**Input Segmented Valley Centerline**

Segmented valley bottom centerline polyline feature class. Valley sinuosity values will be calculated for each segment.

**Input Valley Bottom Polygon**

Valley bottom polygon feature class of the stream network. This can also serve as input to the [Transfer Line Attribute](http://gnat.riverscapes.xyz/Transfer-Line-Attributes) tool.

> This required input will be deprecated in future versions of this tool.

**Output Stream Network with Sinuosity Attribute**

Output polyline feature class. Represents a stream network with calculated sinuosity.

**Output Valley Centerline with Sinuosity Attribute**

Output polyline feature class includes calculated sinuosity as an attribute.

**Output Stream Network with Planform Attribute**

Output polyline feature class, representing the stream centerline with calculated planform attribute.

**Scratch Workspace** (optional)

File geodatabase or folder to store temporary data produced during the processing. If no workspace is selected, the tool will use "in_memory" workspace.

### Outputs

**Output Stream Centerline With Sinuosity**

**Output Valley Centerline with Sinuosity**

**Output Planform Network**

_______________________________________________________________
## Technical Background

### Calculation Method

1. Use [Sinuosity By Segment Tool](http://gnat.riverscapes.xyz/Sinuosity-by-Segment) for stream and valley centerlines
  * Convert segment ends to points
  * Find straight-line distance
  * Calculate sinuosity (segment distance/straight-line distance)
2. Transfer valley bottom sinuosity to stream centerline using the [Transfer Line Attributes](http://gnat.riverscapes.xyz/Transfer-Line-Attributes) tool
3. Calculate the planform metric for each divided segment