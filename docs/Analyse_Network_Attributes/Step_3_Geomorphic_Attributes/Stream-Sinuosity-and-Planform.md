---
title: Sinuosity Attributes Tool
---

In general Sinuosity is a ratio of the sinuous length of stream or valley reach the to straight-line distance for that same reach. This tool generates three different sets of sinuosity attributes for each segment within a particular stream network and its associated valley centerline:

* `Planform Sinuosity`  ratio of channel segment length / channel segment dist
* `Channel Sinuosity` ratio of channel segment length / Valley Bottom Length
* `Valley Sinuosity` ratio of valley bottom segment length / valley bottom segment distance

![sinuosity_example]({{site.baseurl}}assets/images/sinuosity_example.png)

_______________________________________________________________
## Usage

### Input Parameters

![sinuosityplanform_form]({{site.baseurl}}assets/images/sinuosityplanform_form.png)

**Input Segmented Stream Network**

Segmented stream network polyline feature class (i.e. flowline, centerline, etc). Stream sinuosity values will be 
calculated for each segment.  New channel sinuosity, valley sinuosity, and planform sinuosity attribute fields will appended
to this dataset on completion of the processing.

**Input Segmented Valley Centerline**

Segmented valley bottom centerline polyline feature class. Valley sinuosity values will be calculated for each segment.

**Segment ID Field**

SegmentID field.

**Temporary Workspace**

Saves temporary processing files. Leave blank to use "in_memory" workspace.

**(Optional) SegmentFilter Field**

Use this parameter to filter lines to include in the calculation as an Integer field that will ignore lines with "0" and calculate lines with "1".

### Outputs

***No Outputs. This tool modifies the original input data***

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

* Name of the new Sinuosity Attribute analysis.

_______________________________________________________________

## Technical Background

### Calculation Method

1. Find endpoints of the line segments
2. Use Near Analysis to find points on valley bottom centerline nearest to the endpoints.
3. Generate Valley Bottom centerline segments  and straight lines from near points.
4. Generate Selection Polygons used to associate valley bottom segments with stream network segments.
5. Generate length values and distances used in sinuosity calculations.
6. Calculate the sinuosity metrics for each segment

# Release Notes

* `version 2.0.1` 2018-03-01
  * Major rewrite of this tool, including new attribute definitions, and valley bottom centerline transfer method.