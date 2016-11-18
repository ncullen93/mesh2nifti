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

import os
import time
import itertools as it
import nibabel as nib
import nilearn
import nilearn.image
import numpy as np
import gmsh_numpy

def pt_in_tetra(pt, tetra):
	"""
	Determines if a point is inside a tetrahedron

	pt : np array , shape = (3,)
	tetra : np array, shape = (4,3)
	"""
	vals 		= np.empty((5,4))
	vals[0,:3] 	= pt
	vals[1:,:3] = tetra
	vals[:,3] 	= 1

	idxs = [[1,2,3,4],
			[0,2,3,4],
			[1,0,3,4],
			[1,2,0,4],
			[1,2,3,0]]

	det0 	= np.sign(np.linalg.det(vals[idxs[-1],:]))
	is_in 	= True
	for i in range(0,len(idxs)-1):
		sign 	= np.sign(np.linalg.det(vals[idxs[i],:]))
		if sign!= det0:
			is_in=False
			break
	return is_in


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
			[1, 2, 3, 4, 5] or 'all'
			where 1 = very small gray matter and 5 = entire head

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
	if output_file is None:
		t1_split = t1_file.split('.nii.gz')
		output_file = t1_split[0]+'_from_mesh.nii.gz'
	# load t1 -- needed to make new image
	t1 = nib.load(t1_file)
	# load mesh
	mesh = gmsh_numpy.read_msh(mesh_file)

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

	# get nodes belonging to each element
	gray_nodes = mesh.elm.node_number_list[gray_elm_idx]

	# get coordinates of the nodes for each element
	if verbose > 0:
		print 'Getting node coordinates..'
	rc = np.array(list(it.product(np.arange(gray_nodes.shape[0]),np.arange(gray_nodes.shape[1]))))
	gray_coords = mesh.nodes.node_coord[gray_nodes[rc[:,0],rc[:,1]]-1,:]
	gray_coords = gray_coords.reshape(gray_coords.shape[0]/4,4,3)

	# get min and max XYZ coords for each element, for easier sorting
	mins = np.min(gray_coords,axis=1)
	maxs = np.max(gray_coords,axis=1)
	
	# get complete range of XYZ coords for all nodes
	x_min = int(np.min(mins[:,0]))
	x_max = int(np.max(maxs[:,0])+1)
	y_min = int(np.min(mins[:,1]))
	y_max = int(np.max(maxs[:,1])+1)
	z_min = int(np.min(mins[:,2]))
	z_max = int(np.max(mins[:,2])+1)

	##################################
	## begin pre-mapping of indices ##
	##################################
	if verbose > 0:
		print 'Performing pre-mapping..'
	xd = dict([(i,[]) for i in range(int(np.min(mins[:,0])),int(np.max(maxs[:,0]))+1)])
	yd = dict([(i,[]) for i in range(int(np.min(mins[:,1])),int(np.max(maxs[:,1]))+1)])
	zd = dict([(i,[]) for i in range(int(np.min(mins[:,2])),int(np.max(maxs[:,2]))+1)])
	for i in range(mins.shape[0]):
		xmin,ymin,zmin = mins[i,:]
		xmax,ymax,zmax = maxs[i,:]
		for x in np.arange(int(xmin+1),int(xmax)+1):
			xd[x].append(i)
		for y in np.arange(int(ymin+1),int(ymax)+1):
			yd[y].append(i)
		for z in np.arange(int(zmin+1),int(zmax)+1):
			zd[z].append(i)

	for k in xd.keys():
		xd[k] = frozenset(xd[k])
	for k in yd.keys():
		yd[k] = frozenset(yd[k])
	for k in zd.keys():
		zd[k] = frozenset(zd[k])
	###################
	# end pre-mapping #
	###################

	# get values belonging to the given value set
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

	if verbose > 0:
		print 'Voxelizing the Mesh..'
	data = np.zeros(t1.shape)
	bias = int(t1.shape[0] / 2.)
	new = -1
	for x in xrange(x_min,x_max,voxel_size):
		if x != new:
			if verbose > 0:
				print 100*round((x-x_min) / float(np.abs(x_min)+np.abs(x_max)),3) , '%'
			new= x
		for y in xrange(y_min,y_max,voxel_size):
			for z in xrange(z_min,z_max,voxel_size):
				candidates = list(xd[x]&yd[y]&zd[z])
				for cand_idx in candidates:
					if pt_in_tetra((x,y,z),gray_coords[cand_idx,:,:]):
						x_idx = range((x+bias),(x+bias+voxel_size))
						y_idx = range((y+bias),(y+bias+voxel_size))
						z_idx = range((z+bias),(z+bias+voxel_size))
						data[x_idx,y_idx,z_idx] = gray_vals[cand_idx]
						break

	if verbose > 0:
		print 'Saving NIFTI image..'
	new_img = nilearn.image.new_img_like(t1,data,affine=t1.affine)
	try:
		nib.save(new_img, output_file)
	except:
		print 'Output file wasnt valid.. saving to T1 image directory instead'
		t1_split = t1_file.split('.nii.gz')
		output_file = t1_split[0]+'_from_mesh.nii.gz'
		nib.save(new_img,output_file)



