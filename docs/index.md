The **Geomorphic Network and Analysis Toolbox (GNAT)** is a set of ArcGIS geoprocessing scripts used to generate geomorphic attributes for a spatially-explicit stream network dataset, such as NHD or NWI.  Specifically, it is written in Python as an ArcGIS Python Toolbox for ArcGIS 10.1. Currently, [efforts](https://github.com/SouthForkResearch/pyGNAT) are underway to move GNAT to use open source resources exclusively.

arcGNAT was originally developed to support the geomorphic attribute analysis and modeling efforts of the Integrated Status and Effectiveness Monitoring Program ([ISEMP](http://isemp.org)) and Columbia Habitat Monitoring Program ([CHaMP](https://www.champmonitoring.org)). However, the tools found within GNAT are flexible enough to be used in a wide variety of data processing and analysis efforts revolving around stream networks, such as:

* Stream network preparation
* Attribute management
* Segmentation of stream networks
* Model geomorphic attributes


## Download

**[Version 2.2.03](Downloads/arcGNAT_2.1.12.zip")** 2017 AUG 14

``` * Fixed minor issue with how a field was populated in the Commit Stream Network tool.```

[Previous Versions and Release Notes](releases)

### Installation

The arcGNAT Toolbox is provided as a zip file containing a .pyt file and supporting script files. 

1. Unzip the contents to your computer (keep all files together).
2. Open ArcGIS.
3. Add the .pyt file to Arc toolbox as you would any other Geoprocesssing Toolbox.

# Usage

[About GNAT Projects](GNAT_Project)

Tools

- Project Management
  - [Create New GNAT Project](Project_NewGNATProject)
  - [Load Network to Project](Project_LoadNetwork)
  - [Commit Network to Realization](Project_CommitRealization)
- Main
  - Step 1 - [Stream Network Preparation](Stream-Network-Prep)
    - [Build Network Topology Table](Build-Network-Topology-Table)
    - [Find Network Features](Find-Network-Features)
  - Step 2 - Stream Network Segmentation
    - [Segment Stream Network](Segment-Stream-Network)
  - Step 3 - Geomorphic Attributes
    - [Stream Sinuosity and Planform](Stream-Sinuosity-and-Planform)
- Utilities
  - [Calculate Stream Order](Calculate-Stream-Order)
  - [Centerline Tool](Centerline-Tool)
  - [Combine Attributes](CombineAttributes)

##  Support

GNAT is developed and maintained by [South Fork Research, Inc](http://southforkresearch.org).