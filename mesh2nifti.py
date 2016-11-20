#! /usr/bin/env python
"""
Converts .msh file to .nifti

Algorithm for checking if an XYZ coordinate is inside a tetrahedron
-------------------------------------------------------------------
A point is in a tetrahedron if the following five determinants 
all have the same sign:

             |x1 y1 z1 1|
        D0 = |x2 y2 z2 1|
             |x3 y3 z3 1|
             |x4 y4 z4 1|

             |x  y  z  1|
        D1 = |x2 y2 z2 1|
             |x3 y3 z3 1|
             |x4 y4 z4 1|

             |x1 y1 z1 1|
        D2 = |x  y  z  1|
             |x3 y3 z3 1|
             |x4 y4 z4 1|

             |x1 y1 z1 1|
        D3 = |x2 y2 z2 1|
             |x  y  z  1|
             |x4 y4 z4 1|

             |x1 y1 z1 1|
        D4 = |x2 y2 z2 1|
             |x3 y3 z3 1|
             |x  y  z  1|

"""
__author__ = """Nicholas Cullen"""

import sys
import os
import time
import nibabel as nib
import nilearn
import nilearn.image
import numpy as np
import gmsh_numpy


def pt_in_tetra(pt, tetra):
	"""
	Determines if a point is inside a tetrahedron.

	This function clocks at ~40 microseconds and is
	one major bottleneck of the code. It probably can't
	be improved any further without using C++, etc.

	pt : np array , shape = (3,)
	tetra : np array, shape = (4,3)
	"""
	vals 		= np.ones((5,4))
	vals[0,:3] 	= pt
	vals[1:,:3] = tetra

	idxs = [[1,2,3,4],
			[0,2,3,4],
			[1,0,3,4],
			[1,2,0,4],
			[1,2,3,0]]

	dets = np.linalg.det(vals[idxs,:])
	return np.all(dets > 0) if dets[0] > 0 else np.all(dets < 0)


def mesh2nifti(mesh, t1, view=2, value_set='normE', voxel_size=1,
	output_file=None, verbose=1):
	"""
	Convert a simNIBS/GMSH .mesh file into a NIFTI image.

	Arguments
	---------
	mesh 	: string
		path to the .msh file
	
	t1 		: string
		path to t1 file used by simNIBS.

	view 	: integer
		which surface/volume to use
		possible values:
			1 = white matter
			2 = gray matter
			3 = cerebral-spinal fluid
			4 = skull?
			5 = entire head?
			'all' = use all

	value_set	: string
		which simulation values to use
		possible values:
			['E','normE','J','normJ']

	voxel_size 	: integer
		how big to sample the mesh image in Millimeters (or other units)
		possible values:
			[1,2,3,...]
		Generally want this to be the same as T1 image (1mm)

	output_file : string
		file path to save resulting nifti image. Should include image name
		e.g. '~/desktop/img.nii.gz'
		If output_file=None, it will save with same name/folder as T1 image,
		but with 'from_mesh_..' at the beginning

	Outputs
	-------
	None

	Effects
	-------
	- saves a new Nifti file to disk

	"""
	############
	### IO 
	############
	t1_file 	= t1
	mesh_file 	= mesh

	if output_file is None:
		t1_split = t1_file.split('.nii.gz')
		output_file = t1_split[0]+'_from_mesh.nii.gz'
	# load t1 -- needed to make new image
	t1 = nib.load(t1_file)
	# load mesh
	mesh = gmsh_numpy.read_msh(mesh_file)
	#mesh = read_msh(mesh_file)
	assert (len(mesh.elmdata) > 0), 'You appear to have passed in a regular T1 mesh file.\n\
	This code only works on mesh files resulting from a simNIBS simulation run..'

	#############
	### end IO 
	#############

	#########################
	### Gather Mesh data
	#########################

	# get elements from View in {1,2,3,4,5} from small (gray matter) to large (head)
	if view == 'all':
		# if view is None, take all views
		min_view = 0
		max_view = 5
	else:
		min_view = np.min([view])
		max_view = np.max([view])

	gray_elm_idx = np.where(\
		 (mesh.elm.tag1 >= min_view)\
		&(mesh.elm.tag1 <= max_view))[0]

	if verbose > 0:
		sys.stdout.write('Found %i relevant elements' % len(gray_elm_idx))

	# get nodes belonging to each element
	gray_nodes = mesh.elm.node_number_list[gray_elm_idx]

	# get coordinates of the nodes for each element
	if verbose > 0:
		sys.stdout.write('Getting mesh data..')
	rc = []
	for i in xrange(gray_nodes.shape[0]):
		for j in xrange(gray_nodes.shape[1]):
			rc.append([i,j])
	rc = np.array(rc)
	gray_coords = mesh.nodes.node_coord[gray_nodes[rc[:,0],rc[:,1]]-1,:]
	gray_coords = gray_coords.reshape(gray_coords.shape[0]/4,4,3)
	
	##########################
	### end gather mesh data
	##########################


	###############################################
	#### INVERSE TRANSFORM DATA BACK TO INDEX SPACE
	###############################################
	## NOTE: While the diagonals (e.g. -1's) are needed, it seems that the
	## simNIBS just uses t1.shape / 2 (128) as offset bias instead of the affine values
	## e.g. to get to index space, do 'coord + 128' and multiply by -1 if the
	## corresponding diagonal in the t1 affine is -1.. meaning that dim is flipped.
	if verbose > 0:
		print 'Applying inverse transform to Mesh coordinates..'
	affine = t1.affine.copy()
	
	## swaping dims if necessary
	if t1.affine[0,0] < 0:
		print 'Swaping X orientation because of negative diag in T1 affine..'
		gray_coords[:,:,0] *= -1
		#affine[0,0] *= -1
		#affine[0,-1] *= -1
	if t1.affine[1,1] < 0:
		print 'Swaping Y orientation because of negative diag in T1 affine..'
		gray_coords[:,:,1] *= -1
		#affine[1,1] *= -1
		#affine[1,-1] *= -1
	if t1.affine[2,2] < 0:
		print 'Swaping Z orientation because of negative diag in T1 affine..'
		gray_coords[:,:,2] *= -1
		#affine[2,2] *= -1
		#affine[2,-1] *= -1
	
	## adding affine bias
	gray_coords[:,:,0] += 128#np.abs(t1.affine[0,-1])
	gray_coords[:,:,1] += 128#np.abs(t1.affine[1,-1])
	gray_coords[:,:,2] += 128#np.abs(t1.affine[2,-1])

	###############################################
	#### end inverse transform
	###############################################

	##################################
	## begin pre-mapping of indices ##
	##################################

	# get min and max XYZ coords for each element, for easier sorting
	mins = np.min(gray_coords,axis=1)
	maxs = np.max(gray_coords,axis=1)
	
	# get complete range of XYZ coords for all nodes
	x_min = int(np.min(mins[:,0]))
	x_max = min(int(np.max(maxs[:,0]))+1,256)
	y_min = int(np.min(mins[:,1]))
	y_max = min(int(np.max(maxs[:,1]))+1,256)
	z_min = int(np.min(mins[:,2]))
	z_max = min(int(np.max(mins[:,2]))+1,256)
	print 'min/max X coordinate: ', x_min,x_max
	print 'min/max Y coordinate: ', y_min,y_max
	print 'min/max Z coordinate: ', z_min,z_max


	if verbose > 0:
		print 'Pre-mapping candidate elements for each voxel..'
		
	candidates = dict([((a,b,c),set()) for a in range(x_min,x_max+2) \
		for b in range(y_min,y_max+2)\
		for c in range(z_min,z_max+2)])
	
	for i in range(mins.shape[0]):
		xmin,ymin,zmin = mins[i,:]
		xmax,ymax,zmax = maxs[i,:]
		for x in xrange(int(xmin),int(xmax)+1):
			for y in xrange(int(ymin),int(ymax)+1):
				for z in xrange(int(zmin),int(zmax)+1):
					candidates[(x,y,z)].update({i})
	###################
	# end pre-mapping #
	###################

	##################################
	# get values belonging to the given value set
	##################################
	if value_set == 'E':
		gray_vals	= mesh.elmdata[0].value[gray_elm_idx]
	elif value_set == 'normE':
		gray_vals	= mesh.elmdata[1].value[gray_elm_idx]
	elif value_set == 'J':
		gray_vals	= mesh.elmdata[2].value[gray_elm_idx]
	elif value_set == 'normJ':
		gray_vals	= mesh.elmdata[3].value[gray_elm_idx]
	else:
		print 'Value_set argument not understood.. using normE as default'
		gray_vals	= mesh.elmdata[1].value[gray_elm_idx]

	##################################
	# end get simulation values
	##################################

	##################################
	#### VOXELIZE THE MESH - Actually map voxels to intensities
	##################################
	if verbose > 0:
		print 'Voxelizing the Mesh at size %i%s^2'%(voxel_size,mesh.nodes.units)
	data 	= np.zeros(t1.shape)
	vox 	= voxel_size
	new		= -1
	for x in xrange(x_min,x_max,vox):
		if x != new:
			if verbose > 0:
				print 100*np.round(((x-x_min) / float(x_max-x_min)),3) , '%'
			new= x
		for y in xrange(y_min,y_max,vox):
			for z in xrange(z_min,z_max,vox):
				for cand_idx in list(candidates[(x,y,z)]):
					if pt_in_tetra((x,y,z),gray_coords[cand_idx,:,:]):
						data[x:(x+vox),y:(y+vox),z:(z+vox)] = gray_vals[cand_idx]
						break
	##################################
	# end voxelize mesh
	##################################

	##################################
	### SAVE THE IMAGE 
	##################################
	if verbose > 0:
		print 'Saving NIFTI image..'
	new_img = nilearn.image.new_img_like(t1,data,affine=affine)
	#new_img = t1
	#new_img.set_data(data)
	try:
		nib.save(new_img, output_file)
	except:
		print 'Output file wasnt valid.. saving to T1 image directory instead'
		t1_split = t1_file.split('.nii.gz')
		output_file = t1_split[0]+'_from_mesh.nii.gz'
		nib.save(new_img,output_file)

if __name__=='__main__':
	args = np.array(sys.argv[1:])
	sys.stderr.write('TESTING TESTING')
	if '-h' in args or '-help' in args or len(args)==0:
		sys.stdout.write("""Usage:
		mesh2nifti.py -mesh /path/to/msh -t1 /path/to/t1 [-view (1,2,3,4,5)]\
		[-value (E,normE,J,normJ)] [-vox voxel size] [-out /path/to/output] [-v verbosity]
		""")
	else:
		# get verbosity
		try:
			verbose = args[np.where((args=='-v')|(args=='-verbose')\
				|(args=='--v')|(args=='--verbose'))[0]+1][0]
			try:
				verbose = int(verbose)
			except:
				verbose = 0
		except:
			verbose = 0

		# get mesh file
		try:
			mesh_file = args[np.where((args=='-mesh')|(args=='-msh')\
				|(args=='--mesh')|(args=='--msh'))[0]+1][0]
			#if mesh_file[0] != '/':
			#	mesh_file = os.path.join(os.getcwd(),mesh_file)
			if verbose > 0:
				print 'Mesh file : %s' % mesh_file
		except IndexError:
			raise Exception('Must pass in .msh file with argument -mesh')
		
		# get t1 file
		try:
			t1_file = args[np.where((args=='-t1')|(args=='-T1')\
				|(args=='--t1')|(args=='--T1'))[0]+1][0]
			#if t1_file[0] != '/':
			#	t1_file = os.path.join(os.getcwd(),t1_file)
			if verbose > 0:
				print 'T1 file : %s' % t1_file
		except IndexError:
			raise Exception('Must pass in T1 .nii.gz file with argument -t1')

		# get view
		try:
			view = args[np.where((args=='-view')|(args=='-View')\
				|(args=='--view')|(args=='--View'))[0]+1][0]
			try:
				view = int(view)
			except:
				if view == 'all':
					pass
				else:
					print 'Invalid View argument.. using View=2'
					view=2
			if verbose > 0:
				print 'View: ' , view
		except:
			if verbose > 0:
				print 'Using Default View=2'
			view = 2

		# get value set
		try:
			value_set = args[np.where((args=='-value')|(args=='-value_set')\
				|(args=='-Value')|(args=='--value')\
				|(args=='--value_set')|(args=='--Value'))[0]+1][0]
			if value_set not in ['E','normE','J','normJ']:
				print value_set
				print 'Value set not in {E, normE,J,normJ}..Using normE as default'
				value_set = 'normE'
			if verbose > 0:
				print 'Value Set: ' , value_set
		except:
			if verbose > 0:
				print 'Using Default Value Set = normE'
			value_set = 'normE'

		# get voxel size
		try:
			voxel_size = args[np.where((args=='-vox')|(args=='-voxel')\
				|(args=='-voxel_size')|(args=='--vox')\
				|(args=='--voxel')|(args=='--voxel_size'))[0]+1][0]
			try:
				voxel_size = int(voxel_size)
			except:
				print 'Voxel size arg not an integer..using Default = 1'
				voxel_size=1
			if verbose > 0:
				print 'Voxel Size: ', voxel_size
		except:
			if verbose > 0:
				print 'Using Default Voxel Size = 1'
			voxel_size=1

		# get output file
		try:
			output_file = args[np.where((args=='-out')|(args=='-output')\
				|(args=='-output_file')|(args=='--out')\
				|(agrs=='--output')|(args=='--output_file'))[0]+1][0]
			if verbose>0:
				print 'Output File: ' , output_file
		except:
			output_file=None
		
		# run the conversion
		mesh2nifti(mesh=mesh_file, t1=t1_file, view=view, 
			value_set=value_set, voxel_size=voxel_size,
			output_file=output_file, verbose=verbose)