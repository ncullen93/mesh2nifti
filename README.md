
Overview
---------
The 'msh2nifti' function converts a .msh file that was output from a simNIBS
simulation run back into a .nii.gz file. Users can specify a specific View 
(1=WM, 2=GM, 3=CSF, 4=Skull, 5=Head), a specific Field (E,normE,J,normJ),
and a specific voxel size (1,2,..).

This allows users to use the simulated fields seamlessly with structural/functional
nifti files collected during real TMS/tDCS experimentation.

Detailed Instructions
---------------------
0. Uninstall current simNIBS application:
  - run 'sudo rm -r -f $SIMNIBSDIR' (add 'sudo' at beginning if you get an error)
  - run 'sed -i.bak '/SIMNIBS/d' ~/.bash_profile'
1. Download simNIBS tar file again from the website http://simnibs.de/version2/installation
  - move folder wherever you want... doesnt matter
2. Uncompress folder by double clicking or run 'tar -zxvf simnibs_X.X.X.tar.gz'
3. Open the command line terminal and run 'cd ~/downloads/simnibsX.X.X'
4. copy msh2nifti.py file to simnibs_X.X.X/fem_efield/src_pythonmsh2nifti.py
5. copy install_simnibs_NCC.sh to simnibs_X.X.X/install_simnibs_NCC.sh
6. run 'cd simnibs_X.X.X'
8. run './install_simnibs_NCC.sh'
  - if you get an error about permissions, run `chmod u+x install_simnibs_NCC.sh`
9. Follow the rest of the simnibs instructions.. It installs exactly as before.


USAGE
-----
usage: msh2nifti [-h] -mesh MESH -t1 T1 [-view VIEW] [-field FIELD]
                 [-voxel VOXEL] [-out OUT] [--verbose]

optional arguments:<br>
  -h, --help    show this help message and exit<br>
  -mesh MESH    mesh file from simNIBS simulation filepath<br>
  -t1 T1        reference T1 conform image filepath<br>
  -view VIEW    integer from 1-5 -> which volume/surface to use (default = 2)<br>
  -field FIELD  string -> simulation field values to use (default='normE')<br>
  -voxel VOXEL  integer -> resolution of voxelized image (default=1)<br>
  -out OUT      filepath to resulting output nifti image<br>
  --verbose     whether to print status<br>

EXAMPLE
-------
msh2nifti -mesh /Users/user-name/desktop/testfiles/mymeshfile.msh \
          -t1 /Users/ncullen/desktop/testfiles/T1_conform.nii.gz \
          -view 2 \
          -field normE \
          -voxel 1 \
          -out /Users/user-name/desktop/testfiles/myniftifile.nii.gz \
          --verbose




