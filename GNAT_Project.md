# GNAT Project

## Concepts

The concepts here are based on the two-step process for generating a confinement Project. 

![](https://docs.google.com/drawings/d/1Y2zYp1tdWn-FWincxK55xr-zfW4yJCfg7Nw4UEpONRk/pub?w=1326&h=722)

### Project

MetaData
- Region
- Watershed
- User/Operator

### Inputs

The only input the GNAT project is a stream network.

MetaData

- Source or type (NHD+ V02, 
- Scale?

### Realization

A GNAT realization represents steps 1 and 2 in the current GNAT workflow.
 
1. Initial Network Topology Table is Generated 
2. Network Attributes and Errors are identified
3. Network Errors are Cleaned up
4. Regenerate Topology table, if needed.

Params/Metadata

-

Outputs
-GNAT Network
-GNAT Network Table

### Analyses

An "Analysis" represents a Segmented or Stream Branch processed network. These can be fed into other Geomorphic Attribute Projects as inputs. Several Analyses can be associated with a realization, but if the realization changes or is updated, new analyses must be generated from this.

#### Segmented Network

Network split by segments with original attributes retained. Segmentation is identified by a SegmentID Field.

Params:
-SegID Field
- Pre-Segmentation Dissolve Options (None, Stream Branches)
- Segmentation Distance
- Segmentation Direction ("Move Upstream", "Move Downstream")
- Segmentation Remainder Option ("End","Proportional")

Outputs
-Segmented GNAT Network
-Gnat network table

#### Stream Branch

Network with a Stream Branch ID field applied. Original attributes are retained.

-GNAT Network with Stream Branch ID's
-Gnat network table

#### Other Analysis types?

## Example Project File

<script src="https://gist.github.com/KellyMWhitehead/8a198d59ed3e1df69c4c39733e865327.js"></script>

