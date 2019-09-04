---
title: Calculate Threadedness
---


The **Calculate Threadedness** tool calculates the degree of threadedness for a stream network.
In this case, "threadedness" is defined as the number of braids that intersect mainstem reaches
within the stream network. The tool plots intersection nodes, determines the node type, and then
calculates the number of nodes for each stream reach feature.  Three node types are plotted,
including:

* braid-to-braid
* braid-to-mainstem
* tributary confluences

![threadedness_example]({{site.baseurl}}assets/images/threadedness_example.png)

_______________________________________________________________

## Usage


### Geoprocessing Environment

* We recommend running the tool using 64-bit python geoprocessing.
* Disable Z and M values in the input stream network feature class Shape field.

### Input Parameters
 
**Input segmented stream network** (with Stream Order)

A stream network feature class previously segmented by the**Segmentation** tool, from which all braid features have been
 manually removed. New fields will appended to this dataset on completion of the processing.

**Input stream network with braids**

Stream network feature class which includes multi-threaded streams ((i.e. braid features).

**Scratch workspace**

* Can be a file geodatabase or folder, which will be used for saving temporary processing datasets.

### Output

**Output network nodes**

Point feature class representing three node types:
* braid-to-braid nodes
* braid-to-mainstem nodes
* tributary confluences

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

* Name of the Segmentation Analysis selected from a list of existing Analyses, to which the Calculate Threadedness 
analysis will be assigned.

**Attribute Analysis Name** (optional)

* Name of the new Calculate Threadedness analysis.

_______________________________________________________________

## Technical Background

### Calculation Method

#### Manual Preprocessing
1. Process stream segmentation (1000m and/or 500m).
2. Find braids in a separate stream network feature class (after topology clean-up, removal of canals, etc.).

#### Automated Processing
3. Select braids segments using IsBraided attribute field
4. Remove from selection the currently selected braid features that share a centroid with stream features in segmented 
stream network.
5. Dissolve selected braids (using "single part" parameter)
6. Self-intersect dissolved braids to get "braid-to-braid" nodes.
7. Intersect selected braids with segmented stream network - produces "braid-to-mainstem" nodes (which results in 
"Multipoints").
8. Convert braid nodes from multipart to single part
9. Add new attribute field ("node_type" = 'braid')
10. Dissolve segmented stream network (single-part)
11. Self-intersect dissolved stream network to get "tributary confluence" nodes
12. Add new attribute field ("node_type" = 'confluence')
13. Merge node datasets into new feature class
14. Spatial one-to-many join between stream segment features and braid node features.
15. Summarize by LineOID
16. Calculate count of braid nodes per stream segment
17. Spatial one-to-many spatial join between stream segment features and confluence node features
18. Summarize by LineOID
19j. Calculate count of tributary confluence nodes per stream segment