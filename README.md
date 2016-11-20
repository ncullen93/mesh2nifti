# mesh2nifti

Convert a simNIBS/GMSH .msh file into a Nifti .nii.gz file. This is useful if you're doing TMS/tDCS experiments using simNIBS and want to actually be able to use the resulting simulation data.

This code works as a Mac application, although you can certainly just use it directly in Python if necessary.

## Installation as Application
The easiest way to use this code is to get the apre-built application folder. For this, email me at `ncullen.th at dartmouth.edu`. The other method is to build the application from source on your own (see below).

## Installation from Source
Steps:	
	- Download this repository and unzip it
	- cd to `mesh2nifti-master/`
	- run `python setup.py py2app`
	- copy the `mesh2nifti.app/` folder from the newly created `dist/` folder into your local `Applications/` folder
	- add the application to your path with `echo "PATH=$PATH:/Applications/mesh2nifti.app/Contents/MacOS/" >> ~/.bash_profile`
	- test that it works by running 'mesh2nifti -h'

See the section below for common errors when doing this.

## Installation with Python
If you want to use this code directly in Python, there is no installation process. Simply call `python mesh2nifti.py` with the same args as below. Of course, you'll have to make sure the mesh2nifti.py file and its one local dependency (gmsh_numpy.py) are imported.


## Usage

```
mesh2nifti.py [-h] -mesh MESH -t1 T1 [-view VIEW] [-field FIELD]
                     [-voxel VOXEL] [-out OUT] [--verbose]
optional arguments:
  -h, --help    show this help message and exit
  -mesh MESH    mesh file from simNIBS simulation
  -t1 T1        reference T1 image
  -view VIEW    volume/surface to use
  -field FIELD  simulation field values to use
  -voxel VOXEL  resolution of voxelized image
  -out OUT      path to resulting image
  --verbose     whether to print status
 ```

The code generally takes ~10 minutes to run, although setting the voxel size to 2 (i.e. 2x2x2) is significantly faster.


## EXAMPLE

```
mesh2nifti -t1 ~/desktop/sandbox/simNIBS/simnibs2.0_example/almi5_T1fs_conform.nii.gz -mesh ~/desktop/sandbox/simNIBS/simnibs2.0_example/simnibs_sim/mesh.msh -view 2 -field normE -voxel 1 -out ~/desktop/sandbox/simNIBS/simnibs2.0_example/sim.nii.gz --verbose

freeview almi5_T1fs_conform.nii.gz sim.nii.gz
```


## Common Errors with py2app

If you get an error that says "max recursion exceeded", you'll have to go use ipython to run the setup.py and do the following:

	- import sys
	- sys.setrecursionlimit(5000)
	- run setup.py py2app

If you get an error about 'loader_path', it is a known bug and you should follow the directions here about replacing 'loader_path' with 'loader':
	- http://stackoverflow.com/questions/31240052/py2app-typeerror-dyld-find-got-an-unexpected-keyword-argument-loader

If you get an error about "cant find sklearn", then you probably need to upgrade Scipy.

