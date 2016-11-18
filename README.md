# mesh2nifti

Convert a simNIBS/GMSH .msh file into a Nifti .nii.gz file. This is useful if you're doing TMS/tDCS experiments using simNIBS and want to actually be able to use the resulting simulation data in native space.

This code works as a standard python function, but I will be turning it into a command-line tool soon.

## Installation
Currently, there is no installation process. Simply follow these steps to use the code:
	
	- download this repository and unzip it
	- change directories to this repository
		- e.g. 'cd mesh2nifti-master'
	- open a python interpreter
		- e.g. type 'python' in the command line on a mac
	- run the following line:
		- `from mesh2nifti import mesh2nifti`

Now you can use the function as shown in the example below!

## Example
All you have to do is pass in the file paths to the mesh (.msh) file and the T1 (.nii.gz) file used to create the mesh file in simNIBS. You can pass in a `view` argument, which determines the surface to use (1=very small grey matter, ... , 5=entire head, .. 'all'=all). You can also pass in a `value_set` argument, which determines the stimulation value to use ('E','normE','J','normJ').

This code should take ~15 minutes to run, although setting the voxel size to 2 (i.e. 2x2x2) is significantly faster.

NOTE: unfortunately, the .msh files are too large to host on github, so you'll have to down the files from the simNIBS website and run a first simulation yourself.

```python
	from mesh2nifti import mesh2nifti

	t1_file = 'examples/almi5_T1fs_conform.nii.gz'
	msh_file= 'examples/mesh.msh'
	out_file= 'examples/output.nii.gz'

	mesh2nifti(mesh=msh_file, t1=t1_file, view=2, value_set='normE',
				voxel_size=1, output_file=out_file, verbose=1)
```
