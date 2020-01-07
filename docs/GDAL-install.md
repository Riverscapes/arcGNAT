---
title: GDAL Installation on Windows
---

GDAL is a useful command line to process spatial data, and the installed Python libraries allow for the 
use of GDAL tools directly in Python code.

GDAL can used to:

  * Create contours from a DEM
  * Reproject between coordinate systems
  * Convert between rasters and vector data types
  * Build image mosaics

Each of these tasks can be run from the command line, or imported as a Python function.

This tutorial outlines the steps involved in installing GDAL on a Windows PC. Note, in the tutorial we
 are assuming the use of **Windows 7**. Installing GDAL on a Mac is covered [here](http://sandbox.idre.ucla.edu/?p=779).


## Step 1: Check Python version

Python is required for GDAL, and in this tutorial, we assume that you already have Python 2.7 installed,
most likely as part of your ArcGIS Desktop installation.

To find out what version of Python you have installed:

1. Go to Python -> IDLE (Python GUI) in your Start menu

    ![gdal-PythonIdleMenu.png]({{site.baseurl}}assets/images/gdal-PythonIdleMenu.png)

2. Make a note of the number that shows the version of your installed Python in the
top right, as highlighted below:

    ![gdal-PythonIdleShell.png]({{site.baseurl}}assets/images/gdal-PythonIdleShell.png)

*Please Note:* `MSV v.1500` may differ based on your different Python installation.  If it does,
please make a note of that number.  Also, if you installed the 64-bit version of Python, for the 
rest of the tutorial please remove the (x86) from the paths.

## Step 2: Install GDAL

1. Go to Tamas Szekeres' GIS Internals site, and click on **Stable Releases**, to download the appropriate 
GDAL binaries (i.e. installers).

    For this tutorial, we assume you are using ArcGIS 10.4 or greater, so you will most likely be using
    the MSC v.1500 on a 32-bit system. The image below illustrates how the the GDAL version with your 
    installed Python version.  The blue highlight indicates whether you should look for 32-bit or 64-bit
    systems, and the green highlight indicates the release-1500 number which should match the number from
    IDLE in step 1 above.

    ![gdal-VersionList.png]({{site.baseurl}}assets/images/gdal-VersionList.png)

2. Click the appropriate link, which will take you to the list of packages to download.

    ![gdal-PackageList.png]({{site.baseurl}}assets/images/gdal-PackageList.png)

3. Locate and download the "core" installer, which has most of the GDAL components.

    ![gdal-PackageList-core.png]({{site.baseurl}}assets/images/gdal-PackageList-core.png)

4. After downloading your version of the `core.msi` installer, install GDAL with standard settings.

5. Next, return to the list of GDAL binaries, locate and download the Python bindings for your version
of Python, which should be 2.7.

    ![gdal-PackageList-python.png]({{site.baseurl}}assets/images/gdal-PackageList-python.png)

6. After downloading the Python bindings, install them.

## Step 3: Adding environment path variables

We need to tell your Windows operating system where the GDAL installations are located, so we need
to add some Windows environment system variables. 

1. Click on the Windows Start button ![gdal-WindowsButton.png]({{site.baseurl}}assets/images/gdal-WindowsButton.png) 
and in the "Search programs and files" text box, type in "System Environment Variables", then select 
"Edit the system environment variables".

    ![gdal-PathVariable-search.png]({{site.baseurl}}assets/images/gdal-PathVariable-search.png)

2. Once the "System Properties" dialog is open, click the "Environment Variables" button.

    ![gdal-PathVariable-SystemProperties.png]({{site.baseurl}}assets/images/gdal-PathVariable-SystemProperties.png)

3. In the "Environment Variables" dialog, under the "System variables" pane, select the "Path" variables,
then click the "Edit" button.

    ![gdal-PathVariable-EnvironmentVariables.png]({{site.baseurl}}assets/images/gdal-PathVariable-EnvironmentVariables.png)

4. In the "Edit System Variable" dialog, in the "Variable value" text box, go to the end of the text string, and
copy and paste the following:

        ;C:\Program Files (x86)\GDAL

    *Please Note: For the 64-bit GDAL installation, you would simple remove the (x86) after Program Files.*

5. In the "Environment Variables" -> "System variables" pane, click the "New..." button, and then add the following
in the dialog box:

    Variable name: `GDAL_DATA`
    
    Variable value: `C:\Program Files(x86)\GDAL\gdal-data`

    ![gdal-PathVariable-NewSystemVariable.png]({{site.baseurl}}assets/images/gdal-PathVariable-NewSystemVariable.png)
    
    Click "OK"

## Step 4: Testing the GDAL install

1. Open the Windows command line, by going to the Start menu ->Run -> type in `cmd` and press "Enter". 

2. At the command line prompt, type in `gdalinfo --version`.

3. If you get the following result, congratulations!  Your GDAL installation is complete!

     ![gdal-CommandLineCheck.PNG]({{site.baseurl}}assets/images/gdal-CommandLineCheck.PNG)
        



*This walkthrough is derived from Albert Kochaphum's [tutorial](https://sandbox.idre.ucla.edu/sandbox/tutorials/installing-gdal-for-windows)
at **UCLA Sandbox**, including some text and images.*