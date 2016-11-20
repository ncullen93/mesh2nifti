# mesh2nifti

Convert a simNIBS/GMSH .msh file into a Nifti .nii.gz file. This is useful if you're doing TMS/tDCS experiments using simNIBS and want to actually be able to use the resulting simulation data in native space.

This code works as a standard python function, but I will be turning it into a command-line tool soon.

## Installation
Currently, there is no installation process. Simply follow these steps to use the code:
	
	- Download this repository and unzip it
	- Double click the .dmg file
	- Drag the mesh2nifti icon to the "Applications" folder in the finder
	- add the application to your path by running the following from the command line:
		- echo "PATH=$PATH:/Applications/mesh2nifti.app/Contents/MacOS/" >> ~/.bash_profile
	- test that it works by running 'mesh2nifti -h'

Now you can use the function as shown in the example below!

## Example
All you have to do is pass in the file paths to the mesh (.msh) file and the T1 (.nii.gz) file used to create the mesh file in simNIBS. 

You can pass in a `view` argument, which determines the surface to use:

	- 1 = white matter
	- 2 = gray matter
	- 3 = cerebral-spinal fluid
	- 4 = skull
	- 5 = entire head
	- 'all' = use all	


You can also pass in a `value_set` argument, which determines the stimulation value to use:

	- 'E'
	- 'normE'
	- 'J'
	- 'normJ'

This code should take ~15 minutes to run, although setting the voxel size to 2 (i.e. 2x2x2) is significantly faster.

NOTE: unfortunately, the .msh files are too large to host on github, so you'll have to down the files from the simNIBS website and run a first simulation yourself.
EXAMPLE
-------
```python
mesh2nifti -t1 ~/desktop/sandbox/simNIBS/simnibs2.0_example/almi5_T1fs_conform.nii.gz -mesh ~/desktop/sandbox/simNIBS/simnibs2.0_example/simnibs_sim/mesh.msh -view 2 -value normE -vox 1 -verbose 1 -out ~/desktop/sandbox/simNIBS/simnibs2.0_example/sim.nii.gz

freeview almi5_T1fs_conform.nii.gz almi5_T1fs_conform_from_mesh.nii.gz
```


### Generate the Application and DMG File Yourself
In the rare event you want to build the application from source, here are the steps:

First install the py2app package.

Run the following after installing the py2app package:

	- python setup.py py2app

If you get an error that says "max recursion exceeded", you'll have to go into Ipython to run the setup.py and do the following:

	- import sys
	- sys.setrecursionlimit(5000)

If you get an error about 'loader_path', follow the directions here about replacing 'loader_path' with 'loader':
	- http://stackoverflow.com/questions/31240052/py2app-typeerror-dyld-find-got-an-unexpected-keyword-argument-loader

Anyways, after successively running py2app, this will create the build/ and dist/ folders.. Finally, run the following:

	- hdiutil create mesh2nifti.dmg -srcfolder dist/mesh2nifti.app

This will create the mesh2nifti.dmg file, which can then be mounted (double clicked) to install.