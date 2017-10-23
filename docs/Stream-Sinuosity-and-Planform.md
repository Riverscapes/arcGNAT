---
title: Stream Sinousity and Planform
---


Sinuosity is a ratio of the sinuous length of stream or valley reach the to straight-line distance for that same reach. 
 Planform is a ratio of the sinuosity of a stream reach to the length of the encompassing valley segment. The **Stream Sinuosity 
and Planform** tool calculates sinuosity (per polyline feature) for valley centerline and stream network features. The 
tool also transfers the valley sinuosity to the stream network and calculates river planform attribute.

![sinuosity_example]({{site.baseurl}}/images/sinuosity_example.png)

_______________________________________________________________
## Usage

### Geoprocessing Environments ###
* All inputs must be in the same projected coordinate system.
* We recommended running this tool with 64-bit python geoprocessing.
* Disable Z and M geometry in the Shape field if topology errors are encountered.

### Input Parameters

![sinuosityplanform_form]({{site.baseurl}}/images/sinuosityplanform_form.png)

**Input Segmented Stream Network**

Segmented stream network polyline feature class (i.e. flowline, centerline, etc). Stream sinuosity values will be 
calculated for each segment.  New channel sinuosity, valley sinousity, and planform attribute fields will appended
to this dataset on completion of the processing.

**Input Segmented Valley Centerline**

Segmented valley bottom centerline polyline feature class. Valley sinuosity values will be calculated for each segment.

**Input Valley Bottom Polygon**

Valley bottom polygon feature class of the stream network. This can also serve as input to the 
[Transfer Line Attribute](http://gnat.riverscapes.xyz/Transfer-Line-Attributes) tool.

### Outputs

**Output Valley Centerline with Sinuosity Attribute**

Output polyline feature class includes calculated sinuosity as an attribute.

*Please note*: If this analysis is part of Riverscapes project, the `Input Stream Network` will automatically
 be switched to the stream network feature class associated with the Realization Analysis found in the project.rs.xml
 file, which the user selects in the `Riverscape Project Management` parameters of this tool.

### Riverscapes Project Management

**Is this a Riverscapes Project?** (optional)

* Check box indicating whether this analysis is part of an existing Riverscapes project.

**GNAT Project XML** (optional)

* XML file (should be named `project.rs.xml`) which stores information on the associated Riverscapes project.

**Realization Name** (optional)

* Name of the project Realization selected from a list of existing Realizations. Only one Realization can be selected.

**Segmentation Name** (optional)

* Name of the Segmentation Analysis selected from a list of existing Analyses, to which the Sinuosity and Planform
analysis will be assigned.

**Attribute Analysis Name** (optional)

* Name of the new Sinuosity and Planform analysis.

_______________________________________________________________

## Technical Background

### Calculation Method

1. Use [Sinuosity By Segment Tool](http://gnat.riverscapes.xyz/Sinuosity-by-Segment) for stream and valley centerlines
  * Convert segment ends to points
  * Find straight-line distance
  * Calculate sinuosity (segment distance/straight-line distance)
2. Transfer valley bottom sinuosity to stream centerline using the 
[Transfer Line Attributes](http://gnat.riverscapes.xyz/Transfer-Line-Attributes) tool
3. Calculate the planform metric for each divided segment