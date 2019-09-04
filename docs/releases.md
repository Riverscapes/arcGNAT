---
title: Installation
---

1. Install the GDAL Windows binaries
2. Install NetworkX using pip
3. Install GNAT

## GDAL

The [Geospatial Data Abstraction Library (GDAL)](http://gdal.org/index.html) must be installed and configured correctly
 prior to running GNAT tools. Although ArcGIS 10.x products are installed with a custom version of GDAL, it is not 
 generally accessible to developers or third-party tools. GDAL binaries for Windows PCs must be installed separately. 
 The following instructions outline how to install and configure GDAL binaries for Windows 7.
 
If you do not already have GDAL installed, we recommend installing the binaries maintained by Tamas Szekeres at 
[GISInternals](http://www.gisinternals.com/).

Detailed installation instructions are available [here](GDAL-install).

## NetworkX

The [NetworkX](https://networkx.github.io/documentation/networkx-1.11/) python package (specifically version 1.11) is 
required by several GNAT tools, but it must be installed separately. We highly recommend using 
[pip](https://pypi.python.org/pypi/pip) to install NetworkX on your system. 
**pip** is the recommended package management system for installing all third-party Python packages. Fortunately, a 
**pip** executable file is included in the Python installation for ArcGIS, versions 10.4 and higher.

1. Within the directory where Python is installed on you computer, find the filepath to the `Scripts` subdirectory.
If you have version ArcGIS 10.4 (or higher) installed, it will most likely be something like 
`C:\Python27\ArcGIS10.4\Scripts`
2. Open your Windows command prompt and type the following (make sure the file path matches your Python install):
`C:\Python27\ArcGIS10.4\Scripts\pip.exe install networkx==1.11`'
3. In ArcMap, open the Python interpreter, and type `import networkx`.  If there are no error messages returned, then the
NetworkX 1.11 package was successfully installed.

## GNAT

GNAT is provided as a zip file containing a .pyt file and supporting Python script files. 

1. Download the zipfile and unzip the contents to your computer (keep all files together).
2. Open ArcGIS.
3. Add the .pyt file to Arctoolbox as you would any other Geoprocessing Toolbox.

# Download    

The latest release of GNAT is available for download [here](https://github.com/Riverscapes/arcGNAT/releases).
