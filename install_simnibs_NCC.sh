#!/bin/bash
set -e

echo ''
echo "The default installation directory is:"
echo "$HOME/simnibs_2.0.1"
echo ""
echo "  -  Press ENTER to confirm the location"
echo "  -  Press CTR-C to abort the installation"
echo "  -  Or specify another location below"
echo ""

read -r -p "[$HOME/simnibs_2.0.1/] >>> " response
if [ -z "$response" ]; then
	TARGET_DIR="$HOME/simnibs_2.0.1/"
    echo ''
else
	TARGET_DIR=$response
fi

if [ ! -d "$TARGET_DIR" ]; then
	mkdir -p $TARGET_DIR
fi

echo "Installing SimNIBS 2.0.1 in: $TARGET_DIR"


#Change to where the bash is located
cd "$( dirname "${BASH_SOURCE[0]}" )" 




echo ''
echo 'Installing Miniconda. Please review the EULA at https://docs.continuum.io/anaconda/eula'
read -r -p "Do you agree? [y/N] " response
case $response in
    [yY][eE][sS]|[yY] ) 
    echo ''
    ;;
    * )
    echo 'Cannot Proced'
    exit 1
    ;;
esac



case `uname` in
    Linux )
        if [ `uname -m` != "x86_64" ]; then
            echo 'Intallation only automated on 64 bit systems'
            exit 1
        fi

        if hash wget 2>/dev/null; then 
            wget "https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh"
        elif hash curl 2>/dev/null; then
            curl "https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh" \
                -o "Miniconda2-latest-Linux-x86_64.sh"
        else 
            echo "ERROR: SimNIBS installer needs either the curl of wget packages"
            exit 1; 
        fi

        bash Miniconda2-latest-Linux-x86_64.sh -b -f -p $TARGET_DIR/miniconda2

        ;;
    Darwin )
        curl "https://repo.continuum.io/miniconda/Miniconda2-latest-MacOSX-x86_64.sh" \
            -o "Miniconda2-latest-MacOSX-x86_64.sh"
        bash Miniconda2-latest-MacOSX-x86_64.sh -b -f -p $TARGET_DIR/miniconda2
        ;;
    * )
        echo "SimNIBS is only avaliable for Linux and MacOSX Systems"
        exit 1
        ;;
esac

#Install packages - nibabel and nilearn added by NCC
$TARGET_DIR/miniconda2/bin/conda create -n simnibs_env nomkl nibabel nilearn numpy=1.11.1 scipy=0.17.0 pyopengl=3.1.1a1 pyopengl-accelerate=3.1.1a1 pyqt=4.11.4 qt=4.8

$TARGET_DIR/miniconda2/envs/simnibs_env/bin/pip install nibabel

rm Miniconda*
cp -r ./ $TARGET_DIR

echo 'Changing Gmsh default configuration to SimNIBS standard'
cp $TARGET_DIR/gmsh-options_simnibsdefault ~/.gmsh-options

cd $TARGET_DIR/fem_efield/src_python
sed -i.bak "s|#!.*|#!$TARGET_DIR/miniconda2/envs/simnibs_env/bin/python2.7 -u|" *.py
rm *.py.bak

chmod +x crop_and_append.py
chmod +x merge_labels_WM.py
chmod +x simnibs.py
chmod +x nifti2msh.py
chmod +x simnibs_gui.py
chmod +x msh2nifti.py # added by NCC

cd $TARGET_DIR/fem_efield
ln -s -f src_python/crop_and_append.py crop_and_append
ln -s -f src_python/merge_labels_WM.py merge_labels_WM
ln -s -f src_python/simnibs.py simnibs
ln -s -f src_python/nifti2msh.py nifti2msh
ln -s -f src_python/simnibs_gui.py simnibs_gui
ln -s -f src_python/msh2nifti.py msh2nifti # added by NCC

test `uname`  == 'Linux' && {
    ln -s -f src_python/simnibs_gui.py Simnibs
	cd ../bin
	ln -s -f `which expr` expr
	ln -s -f `which getopt` getopt
	cd ../fem_efield
}

echo ""
case `uname` in
    Linux )
		echo 'Modifing ~/.bashrc'
		if grep -Fq "SIMNIBSDIR" ~/.bashrc ; then 
			echo "Another SIMNIBS installation detected, overwriting \$SIMNIBSDIR in the .bashrc file"
			sed -i.simnibs.bak -e "s|export SIMNIBSDIR=.*|export SIMNIBSDIR=$TARGET_DIR|" ~/.bashrc
			sed -i.simnibs.bak -e "s|source \$SIMNIBSDIR/.*|source \$SIMNIBSDIR/simnibs_conf.sh|" ~/.bashrc
		else
		    echo "">> ~/.bashrc
		    echo "export SIMNIBSDIR=$TARGET_DIR">> ~/.bashrc
		    echo "source \$SIMNIBSDIR/simnibs_conf.sh">> ~/.bashrc
		fi
    ;;
    Darwin )
		echo 'Modifing ~/.bash_profile'
		if grep -Fq "SIMNIBSDIR" ~/.bash_profile ; then 
			echo "Another SIMNIBS installation detected, overwriting \$SIMNIBSDIR in the .bash_profile file"
			sed -i.simnibs.bak -e "s|export SIMNIBSDIR=.*|export SIMNIBSDIR=$TARGET_DIR|" ~/.bash_profile
			sed -i.simnibs.bak -e "s|source \$SIMNIBSDIR/.*|source \$SIMNIBSDIR/simnibs_conf.sh|" ~/.bash_profile
		else
			echo "">> ~/.bash_profile
			echo "export SIMNIBSDIR=$TARGET_DIR">> ~/.bash_profile
		        echo "source \$SIMNIBSDIR/simnibs_conf.sh">> ~/.bash_profile
		fi
    ;;
esac

if [ -z "$FSL_DIR" ]; then
    echo ""
    echo "Could not find FSL installation"
    echo "mri2mesh will not work"

fi


if [ -z "$FREESURFER_HOME" ]; then
    echo ""
    echo "Could not find FreeSurfer installation"
    echo "mri2mesh will not work"

fi

echo ""
echo "SimNIBS 2.0.1 sucefully installed"
echo "You can start the GUI by opening a new terminal window and typing simnibs_gui"

exit 0
