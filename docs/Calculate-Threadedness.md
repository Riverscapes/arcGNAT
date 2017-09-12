The **Calculate Threadedness** tool calculates the degree of threadedness for a stream network. 
Values are calculated per stream segment.

![threadedness_example]({{site.baseurl}}/images/threadedness_example.png)
_______________________________________________________________

## Usage


### Geoprocessing Environment

* We recommend running the tool using 64-bit python geoprocessing.
* Disable Z and M values in the input stream network feature class Shape field.

### Input Parameters
 
**Input segmented stream network** (with Stream Order)

Stream network feature class previously segmented by the**Segmentation** tool, from which braid features have been removed. 

**Input stream network with braids**

Stream network feature class which includes multi-threaded streams ((i.e. braid features).

**Scratch workspace**

* Can be a file geodatabase or folder, which will be used for saving temporary processing datasets.
* If a workspace is not designated, the tool will use the "in_memory" workspace. Temporary files will not be accessible, but the tool's processing speed will be improved.

### Output

**Output stream network with threadedness metrics**

Polyline feature class with calculated threadedness values, including:
* node types per segment
* braid nodes per segment

**Output network nodes**

Point feature class representing three node types:
* braid-to-braid nodes
* braid-to-mainstem nodes
* tributary confluences

_______________________________________________________________

## Technical Background

### Calculation Method

#### Manual Preprocessing
1. Process stream segmentation (1000m and/or 500m).
2. Find braids in a separate stream network feature class (after topology clean-up, removal of canals, etc.).

#### Automated Processing
3. Select braids segments using IsBraided attribute field
4. Remove from selection the currently selected braid features that share a centroid with stream features in segmented stream network.
5. Dissolve selected braids (using "single part" parameter)
6. Self-intersect dissolved braids to get "braid-to-braid" nodes.
7. Intersect selected braids with segmented stream network - produces "braid-to-mainstem" nodes. (results in "Multipoints")
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