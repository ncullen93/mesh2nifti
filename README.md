
Overview
---------
The 'msh2nifti' function converts a .msh file that was output from a simNIBS
simulation run back into a .nii.gz file. Users can specify a specific View 
(1=WM, 2=GM, 3=CSF, 4=Skull, 5=Head), a specific Field (E,normE,J,normJ),
and a specific voxel size (1,2,..).

This allows users to use the simulated fields seamlessly with structural/functional
nifti files collected during real TMS/tDCS experimentation.


Specific Instructions
----------------------
- uninstall simnibs (see below for exact commands)
  - sudo rm -r -f $SIMNIBSDIR
  - sed -i.bak '/SIMNIBS/d' ~/.bash_profile
- download and unpack simnibs files again
- Before installation:
  - add msh2nifti.py file to simnibs_X.X.X/fem_efield/src_python/
  - add install_simnibs_NCC.sh to simnibs_X.X.X/
- install using './install_simnibs_NCC.sh' instead of 'install_simnibs.sh'
  - run 'chmod u+x install_simnibs_NCC.sh' if you cant use the file at first


USAGE
-----
usage: msh2nifti [-h] -mesh MESH -t1 T1 [-view VIEW] [-field FIELD]
                 [-voxel VOXEL] [-out OUT] [--verbose]

optional arguments:
  -h, --help    show this help message and exit
  -mesh MESH    mesh file from simNIBS simulation
  -t1 T1        reference T1 conform image
  -view VIEW    volume/surface to use
  -field FIELD  simulation field values to use
  -voxel VOXEL  resolution of voxelized image
  -out OUT      path to resulting image
  --verbose     whether to print status




Detailed Instructions
---------------------
0. Uninstall current simNIBS application:
	- run 'sudo rm -r -f $SIMNIBSDIR' (add 'sudo' at beginning if you get an error)
	- run 'sed -i.bak '/SIMNIBS/d' ~/.bash_profile'
1. Download simNIBS tar file again from the website http://simnibs.de/version2/installation
	- move file to desktop or keep in downloads folder.. doesn't matter
2. Uncompress folder by double clicking or run 'tar -zxvf simnibs_X.X.X.tar.gz'
3. Open the command line terminal and run 'cd ~/downloads/simnibsX.X.X'
4. copy msh2nifti.py file to simnibs_X.X.X/fem_efield/msh2nifti.py
5. copy install_simnibs_NCC.sh to simniibs_2.0.1/install_simnibs.sh
6. run 'cd simnibs_2.0.1'
7. run 'chmod u+x install_simnibs_NCC.sh'
8. run './install_simnibs.sh'
9. Follow the rest of the instructions.. It installs exactly as before.

