

import sys


try: 
    import numpy
except:
    print "numpy could not be loaded"
    sys.exit(1)




# triangle (2) has 3 nodes
# tetrahedron (4) has 4 nodes
# hexahedron (5) has 8 nodes
# point (15) has 1 node
nr_nodes_in_elm = {2:3, 4:4, 5:8, 15:1}


# =============================================================================
# CLASSES
# =============================================================================

class Nodes:
    """class to handle the node information. Contains:
    number_of_nodes     number of nodes, should always be the same as len(node_number) = len(node_coord)
    node_number         node ID (usually from 1 till nr_nodes)
    node_coord          (x, y, z) coordinate of the node (array with nr-)
    units               string with units used for the mesh (mm / meters). Default = 'mm'
    nr                  alias for number_of_nodes
    compact             boolean if node_number has number_of_nodes entries, going from 1 till number_of_nodes
    """ 
    def __init__(self):
        # gmsh fields
        self.number_of_nodes  = 0
        self.node_number      = numpy.array([], dtype='int32')
        self.node_coord       = numpy.array([], dtype='float64')

        # simnibs fields
        self.units            = 'mm'               
        self.nr               = self.number_of_nodes  
        self.compact          = False

    def is_compact(self):
        if len(self.node_number)==self.number_of_nodes and self.node_number[0]==1 and self.node_number[-1]==self.number_of_nodes:
            self.compact = True
        else:
            print "Nodes indexes are not compact, exiting"
            sys.exit(1)



class Elements:
    """class to handle the element information. Contains:
    number_of_elements  number of elements, should always be the same as len(elm_number), len(elm_type), etc
    elm_number          element ID (usuallly from 1 till number_of_elements)
    elm_type            elm-type (2=triangle, 4=tetrahedron, etc)
    number_of_tags      number-of-tags, assumed to be 2
    tag1                first tag for each element
    tag2                second tag for each elenent
    node_number_list    4xnumber_of_element matrix of the nodes that constitute the element. For the triangles, the fourth element = 0

    nr                  alias of number_of_elements
    nr_elm_of_type      number of elements of each type. e.g. nr_elm_of_type[4] gives the number of tetrahedra
    nr_tri              alias for nr_elm_of_type[3]
    nr_tetr             alias for nr_elm_of_type[4]
    compact             boolean if elm_number has number_of_elements entries, going from 1 till number_of_elements
    """
    def __init__(self):
        #gmsh fields
        self.number_of_elements = 0
        self.elm_number         = numpy.array([], 'int32')
        self.elm_type           = numpy.array([], 'int8')
        self.number_of_tags     = 2
        self.tag1               = numpy.array([], dtype='int16')
        self.tag1               = numpy.array([], dtype='int16')
        self.node_number_list   = numpy.array([], dtype='int32')

        #simnibs fields
        self.nr                 = self.number_of_elements
        self.nr_elm_of_type     = numpy.zeros(64, dtype='int32')
        self.nr_tri             = None # self.nr_elm_of_type[2]
        self.nr_tetr            = None # self.nr_elm_of_type[4]
        self.compact            = False

    def Print(self):
        print "Elements info:"
        print "nr elements:  ", self.number_of_elements
        print "nr tetrahedra:", self.nr_elm_of_type[4]
        print "nr triangles: ", self.nr_elm_of_type[2]
        print "nodes of last elm", self.node_number_list[-1]


        self.ID      = numpy.array([], dtype='int32')
        self.type    = numpy.array([], dtype='int8')
        self.nr_tags = numpy.array([], dtype='int8')
        self.tags    = numpy.array([], dtype='int16')
        self.nodes   = numpy.array([], dtype='int16')

    def is_compact(self):
        if len(self.elm_number)==self.number_of_elements and self.elm_number[0]==1 and self.elm_number[-1]==self.number_of_elements:
            self.compact = True
        else:
            print "Elements indexes are not compact, exiting"
            sys.exit(1)



class Msh:
    """class to handle the meshes. Contains:
    nodes       Nodes class with node coordinates
    elm         Element class with element information (tags, list of nodes that compose the elements)
    nodedata    list of the $NodeData sections in the mesh file
    elmdata     list of the $ElementData sections in the mesh file
    name        basename of the mesh (base name of fn without extension)
    fn          filename of the mesh (also used to save the mesh)
    binary      wheter the mesh was loaded from binary (also used to write mesh as binary/ascii)
    """
    def __init__(self):
        self.nodes      = Nodes()
        self.elm        = Elements()
        self.nodedata   = []
        self.elmdata    = []
        self.name       = ''        
        self.fn         = ''                #file name to save msh
        self.binary     = False



# $NodeData, ElementData and all have similar fields, so 
# this class handles them all
class Data:
    def __init__(self, t):
        self.number_of_string_tags = 0
        self.string_tags = []
        self.number_of_real_tags = 0
        self.real_tags = []
        self.number_of_integer_tags = 0
        self.integer_tags = []      
        
        self.type = t.strip()
        
        if self.type=='$NodeData':
            self.node_number = numpy.array([], dtype='int32')
        elif self.type=='$ElementData':
            self.elm_number = numpy.array([], dtype='int32')
        else:
            raise RuntimeError("Unrecognized data type: " + t)
        
        self.nr = 0
        self.nr_comp = 0
        self.value = []
        

    def Print(self):
        print "type            ", self.type
        print "str_tags        ", self.number_of_string_tags, self.string_tags
        print "real_tags       ", self.number_of_real_tags, self.real_tags
        print "int_tags        ", self.number_of_integer_tags, self.integer_tags
        try:
            if self.node_number[-1]: print "node_number[-1] ", self.node_number[-1]
        except:
            pass
        try:
            if self.number_of_nodes_per_element[-1]: print "nodes_per_el[-1]", self.number_of_nodes_per_element[-1]
        except:
            pass
        try:
            if self.elm_number[-1]: print "last elm_number ", self.elm_number[-1]
        except:
            pass
        try:
            if self.value[0]: print "first value     ", self.value[0]
        except:
            pass
        try:
            if self.value[-1]: print "last value      ", self.value[-1]
        except:
            pass
        print ''

                
                
                
# =============================================================================
# functions
# =============================================================================

# 19 Mar 2014 - read meshes with numpy
def read_msh(fn):
    import time
    import os
    
    start_time = time.time()

    if fn.startswith('~'):
        fn = os.path.expanduser(fn) 
    
    if not os.path.isfile(fn):
        print(fn + ' not found')
        sys.exit(1)
        
    m = Msh()
    m.name = os.path.splitext(os.path.basename(fn))[0] # set name of the mesh as the filename with no extension
    m.fn = fn
    

    # file open
    try:
        f = open(fn, 'r')
    except:
        print fn, 'could not be opened'
        sys.exit(1)


    # check 1st line
    if f.readline() != '$MeshFormat\n':
        print fn, "must start with $MeshFormat"
        sys.exit(1)
    

    # parse 2nd line
    version_number, file_type, data_size = f.readline().split()
    
    if version_number[0] != '2':
        print("Can only handle v2 meshes")
        sys.exit(1)
        
    if file_type == '1':
        m.binary = True
        from struct import unpack
    elif file_type == '0':
        m.binary = False
    else: 
        print "file_type not recognized:", file_type
        sys.exit(1)
        
    if data_size != '8':
        print "data_size should be double (8), i'm reading:", data_size
        sys.exit(1)
    

    # read next byte, if binary, to check for endianness
    if m.binary:
        endianness = unpack('i', f.readline()[:4])[0]
    else:
        endianness = 1

    if endianness != 1:
        raise RuntimeError("endianness is not 1, is the endian order wrong?")


    # read 3rd line
    if f.readline() != '$EndMeshFormat\n': 
        print fn + " expected $EndMeshFormat"
        sys.exit(1)

    # read 4th line     
    if f.readline() != '$Nodes\n':
        print fn + " expected $Nodes"
        sys.exit(1)

    # read 5th line with number of nodes    
    try:
        m.nodes.number_of_nodes = int(f.readline())
        m.nodes.nr = m.nodes.number_of_nodes
    except:
        print fn + " something wrong with Line 5 - should be a number"
        sys.exit(1)
    
    
    if m.binary:
        txt = 'binary'
    else:
        txt = 'ascii'

    print "gmsh_numpy.py: Reading", fn, "in", txt , "with", m.nodes.nr, "nodes"
    
    
   
    # read all nodes
    if m.binary:
        # 0.02s to read binary.msh
        dt = numpy.dtype([
            ('id', numpy.int32, 1), 
            ('coord', numpy.float64, 3)])

        temp = numpy.fromfile(f, dtype=dt, count=m.nodes.nr)
        m.nodes.node_number = numpy.copy(temp['id'])
        m.nodes.node_coord = numpy.copy(temp['coord'])


        # sometimes there's a line feed here, sometimes there is not...
        LF_byte = f.read(1) # read \n
        if not ord(LF_byte) == 10:
            f.seek(-1, 1)     # if there was not a LF, go back 1 byte from the current file position
        
    else:
        # nodes has 4 entries: [node_ID x y z]
        m.nodes.node_number = numpy.empty( m.nodes.nr, dtype='int32' )
        m.nodes.node_coord  = numpy.empty( 3*m.nodes.nr, dtype='float64' )    # array Nx3 for (x,y,z) coordinates of the nodes

        # 1.1s for ascii.msh
        for ii in xrange(m.nodes.nr):
            line = f.readline().split()
            m.nodes.node_number[ii] = line[0]
            m.nodes.node_coord[3*ii] = line[1]  ## it's faster to use a linear array and than reshape
            m.nodes.node_coord[3*ii+1] = line[2]
            m.nodes.node_coord[3*ii+2] = line[3]
        m.nodes.node_coord = m.nodes.node_coord.reshape( (m.nodes.nr, 3) )

        m.nodes.is_compact()

        # other ideas: (slower)
        # dt = numpy.dtype( [ ('id', 'int32'), ('x', 'float64'), ('y', 'float64'), ('z', 'float64')] )
        # data = numpy.fromfile(line, dtype=dt, count=1, sep=' ')
        # np.loadtxt(c, delimiter=',', usecols=(0, 2), unpack=True)


    if f.readline() != '$EndNodes\n':
        print fn + " expected $EndNodes after reading " + str(m.nodes.nr) + " nodes"
        sys.exit(1)
    
    print time.time() - start_time, "seconds to read $Nodes", fn

    
    # read all elements
    if f.readline() != '$Elements\n': 
        print fn, "expected line with $Elements"
        sys.exit(1)
    
    sec_start_time = time.time()
    
    try:
        m.elm.number_of_elements = int(f.readline())
        m.elm.nr = m.elm.number_of_elements
    except:
        print fn + " something wrong when reading number of elements (line after $Elements) - should be a number"
        sys.exit(1)
        
    

    if m.binary:

        m.elm.elm_number       = []
        m.elm.elm_type         = []
        # m.elm.number_of_tags   = numpy.empty( m.elm.nr, dtype='uint8' ) # i'm assuming number of tags is always 2
        m.elm.tag1             = []
        m.elm.tag2             = []
        m.elm.node_number_list = numpy.zeros((m.elm.nr,4), dtype = 'int32')

        # each element is written in a mini structure that looks like:
        # int header[3] = {elm_type, num_elm_follow, num_tags};
        # then, data for the elementn is written. In the case of a triangle:
        # int data[6] = {num_i, physical, elementary, node_i_1, node_i_2, node_i_3};
        # but for a tetrahedron:
        # int data[7] = {num_i, physical, elementary, node_i_1, node_i_2, node_i_3, node_i_4};
        # ideally, num_elm_follow should be the number of triangles, or tetrahedra, but gmsh 
        # always considers this number to be 1, so each element has to be read individually
        #fp=f.tell()
        ii = 0 #start index
        elep = 0 #elements currently processed
        #tt=time.clock()
        nread = 9
        blocktype = 2 #assume triangle first
        binarydata=numpy.frombuffer(f.read(nread*4*m.elm.nr),dtype='i4')
        while ii<len(binarydata):
            if blocktype==2:
                nread==9 #triangle 9 bytes
            elif blocktype==4:
                #read assuming rest of elements are type 4
                ed=numpy.frombuffer(f.read((m.elm.nr-elep)*4),dtype='i4')
                binarydata=numpy.hstack((binarydata,ed))
                nread=10 #tetrahedron 10 bytes
            else:
                print "only tetrahedra and triangle supported, but I read type %i"%blocktype
            vlist=numpy.nonzero(binarydata[ii::nread]!=blocktype)[0] #violations of blocktype triangles/tetrahedron
            if len(vlist)==0:
                iin=len(binarydata[ii::nread])
            else:
                iin=numpy.min(vlist) #find first time blocktype is violated triangles/tetrahedron
            if iin>0:
                if blocktype==2:
                    print 'reading triangle block of %i triangles'%iin
                elif blocktype==4:
                    print 'reading triangle block of %i tetrahedra'%iin

            iinn=ii+iin*nread
            m.elm.elm_type.append(binarydata[ii:iinn:nread])
            m.elm.elm_number.append(binarydata[ii+3:iinn:nread])
            m.elm.tag1.append(binarydata[ii+4:iinn:nread])
            m.elm.tag2.append(binarydata[ii+5:iinn:nread])


            if blocktype==2:
                nd=numpy.vstack((binarydata[ii+6:iinn:nread],binarydata[ii+7:iinn:nread],binarydata[ii+8:iinn:nread]))
                m.elm.node_number_list[:iin,:3] = nd.T
            if blocktype==4:
                nd=numpy.vstack((binarydata[ii+6:iinn:nread],binarydata[ii+7:iinn*nread:nread],binarydata[ii+8:iinn:nread],binarydata[ii+9:iinn:nread]))
                m.elm.node_number_list[elep:elep+iin,:] = nd.T
            elep+=iin
            if iinn<len(binarydata):
                blocktype=binarydata[iinn]
                if blocktype==2:
                    #reading was too far - rewind
                    f.seek(-(m.elm.nr-elep)*4,1)
                    binarydata=binarydata[:-(m.elm.nr-elep)]
            ii=iinn
        m.elm.elm_number=numpy.hstack(m.elm.elm_number)
        m.elm.elm_type=numpy.hstack(m.elm.elm_type)
        m.elm.tag1=numpy.hstack(m.elm.tag1)
        m.elm.tag2=numpy.hstack(m.elm.tag2)
        

        # sometimes there's a line feed here, sometimes there is not...
        LF_byte = f.read(1) # read \n at end of binary
        if not ord(LF_byte)== 10:
            f.seek(-1, 1)     # if there was not a LF, go back 1 byte from the current file position
    

    else:
        
        m.elm.elm_number       = numpy.empty( m.elm.nr, dtype='int32' )
        m.elm.elm_type         = numpy.empty( m.elm.nr, dtype='int32' )
        #m.elm.number_of_tags   = numpy.empty( m.elm.nr, dtype='int8' )    # i'm assuming nr_tags is equal to 2
        m.elm.tag1             = numpy.empty( m.elm.nr, dtype='int32' )
        m.elm.tag2             = numpy.empty( m.elm.nr, dtype='int32' )
        m.elm.node_number_list = numpy.zeros((m.elm.nr,4), dtype = 'int32')

        for ii in xrange(m.elm.nr):
            line = f.readline().split()
            m.elm.elm_number[ii] = line[0]
            m.elm.elm_type[ii] = line[1]
            m.elm.tag1[ii] = line[3]
            m.elm.tag2[ii] = line[4]
            if m.elm.elm_type[ii] == 2:
                m.elm.node_number_list[ii,:3] = [int(i) for i in line[5:]]
            elif m.elm.elm_type[ii] == 4:
                m.elm.node_number_list[ii] = [int(i) for i in line[5:]]
            else:
                print "ERROR: Meshes must have only triangles and tetrahedra"
                sys.exit(1)

    m.elm.is_compact()


    if f.readline() != '$EndElements\n':
        print fn + " expected $EndElements after reading " + str(m.el.nr) + " elements"
        sys.exit(1)
    


    print time.time() - sec_start_time, "seconds to read $EndElements", fn
    

    # read the header in the beginning of a data section 
    def parse_Data():
        section = f.readline()
        if section == '': return 'EOF'
        else: data = Data(section)
        # string tags
        data.number_of_string_tags = int(f.readline())
        if data.number_of_string_tags == 1: data.string_tags.append( f.readline().split()[0].strip('"') )
        elif data.number_of_string_tags != 2:
            print "ERROR: number of strings tags = ", data.number_of_string_tags, "should be 1"
            sys.exit(1)
        # real tags     
        data.number_of_real_tags = int(f.readline())
        if data.number_of_real_tags == 1: data.real_tags.append( float(f.readline()) )
        else:
            print "number of real tags different than 1 in " + section
            print "number_of_real_tags=", data.number_of_real_tags
            sys.exit(1)
        
        # integer tags          
        data.number_of_integer_tags = int(f.readline()) # usually 3 or 4
        data.integer_tags = [int(f.readline()) for i in xrange(data.number_of_integer_tags)]
        data.nr = data.integer_tags[2]
        data.nr_comp = data.integer_tags[1]
        return data 

    def read_NodeData(data):


        if m.binary:


            dt = numpy.dtype([
                ('id', numpy.int32, 1), 
                ('values', numpy.float64, data.nr_comp)])

            temp = numpy.fromfile(f, dtype=dt, count=data.nr)
            data.node_number = numpy.copy(temp['id'])
            data.value = numpy.copy(temp['values'])

        else:
            data.node_number  = numpy.empty( data.nr, dtype='int32' )
            data.value        = numpy.empty( (data.nr,data.nr_comp), dtype='float64' )
            for ii in xrange(data.nr):
                line = f.readline().split()
                data.node_number[ii] = int(line[0])
                data.value[ii,:] = [float(v) for v in line[1:]]

        if f.readline() != '$EndNodeData\n':
            print fn + " expected $EndNodeData after reading " + str(data.nr) + " lines in $NodeData"
            sys.exit(1)
        return data
            


    def read_ElementData(data):


        if m.binary:

            dt = numpy.dtype([
                ('id', numpy.int32, 1), 
                ('values', numpy.float64, data.nr_comp)])

            temp = numpy.fromfile(f, dtype=dt, count=data.nr)
            data.elm_number = numpy.copy(temp['id'])
            data.value = numpy.copy(temp['values'])


        else:
            data.elm_number = numpy.empty( data.nr, dtype='int32' )
            data.value = numpy.empty([data.nr,data.nr_comp], dtype = 'float64')

            for ii in xrange(data.nr):
                line = f.readline().split()
                data.elm_number[ii] = int(line[0])
                data.value[ii,:] = [float(jj) for jj in line[1:]]

        if f.readline() != '$EndElementData\n':
            print fn + " expected $EndElementData\n after reading " + str(data.nr) + " lines in $ElementData"
            sys.exit(1)

        return data


    # read sections recursively
    def read_next_section():
        #sec_start_time = time.time()

        data = parse_Data()
        if data == 'EOF': return
        elif data.type == '$NodeData': m.nodedata.append( read_NodeData(data) )
        elif data.type == '$ElementData': m.elmdata.append( read_ElementData(data) )
        else: 
            print "Can't recognize section name:" + data.type
            sys.exit(1)

        #if data != 'EOF': data.Print()

        #print time.time() - sec_start_time, "seconds to read " + data.type
        read_next_section()
        return

    read_next_section()
    
    print time.time() - start_time, "seconds to read " + fn
    return m



# append a $ElementData section to an existing mesh.    
def append_elementData(fn, eD, mode='binary'):
    import numpy
    with open(fn, 'a') as f:
        write_header(f, eD)
        if mode == 'ascii':
            for ii in xrange(eD.nr):
                f.write(str(eD.elm_number[ii]) + ' ' + str(eD.value[ii]).translate(None, '[](),') + '\n')

        elif mode == 'binary':

            elm_number = eD.elm_number.astype('int32')
            value = eD.value.astype('float64')

            if eD.nr_comp == 1:
                f.write(numpy.concatenate((elm_number[:,numpy.newaxis],value.view('int32').reshape((len(eD.value),2))),axis=1).tostring())
            else:
                 f.write(numpy.concatenate((elm_number[:,numpy.newaxis],value.view('int32')),axis=1).tostring())

        f.write('$EndElementData\n') # AT 17-Mar-2015


# append a $NodeData section to an existing mesh.    
def append_nodeData(fn, nd, mode='binary'):
    import numpy
    with open(fn, 'a') as f:
        write_header(f, nd)
        if mode == 'ascii':
            for ii in xrange(nd.nr):
                f.write(str(nd.node_number[ii]) + ' ' + str(nd.value[ii]).translate(None, '[](),') + '\n')

        elif mode == 'binary':

            node_number = nd.node_number.astype('int32')
            value = nd.value.astype('float64')

            if nd.nr_comp == 1:
                f.write(numpy.concatenate((node_number[:,numpy.newaxis],value.view('int32').reshape((len(nd.value),2))),axis=1).tostring())
            else:
                f.write(numpy.concatenate((node_number[:,numpy.newaxis],value.view('int32')),axis=1).tostring())


        f.write('$EndNodeData\n')


# head for NodeData, ElementData or fields
# it's always written as text, both in binary and ascii meshes.
def write_header(f, data):
    f.write(data.type + '\n')
    # string tags
    if data.number_of_string_tags != len(data.string_tags):
        print "nr_string_tags does not check in", data.type, data.number_of_string_tags, data.string_tags
        sys.exit(1)
    f.write(str(data.number_of_string_tags) + '\n')
    for i in data.string_tags: f.write('"' + i + '"\n')
    
    # real tags
    if data.number_of_real_tags != len(data.real_tags):
        print "nr_real_tags does not check in", data.type, data.number_of_real_tags, data.real_tags
        sys.exit(1)
    f.write(str(data.number_of_real_tags) + '\n')
    for i in data.real_tags: f.write(str(i) + '\n')
    
    # integer tags
    if data.number_of_integer_tags != len(data.integer_tags):
        print "nr_int_tags does not check in", data.type, data.number_of_integer_tags, data.integer_tags
        sys.exit(1)
    f.write(str(data.number_of_integer_tags) + '\n')
    for i in data.integer_tags: f.write(str(i) + '\n')




# write msh to mesh file
def write_msh(msh, mode='binary'):
    import sys
    import time
    import numpy

    # basic mesh assertions 
    if msh.nodes.nr <= 0:
        print "ERROR: number of nodes is:", msh.nodes.nr
        sys.exit(1)

    if msh.elm.nr <= 0:
        print "ERROR: number of elements is:", msh.elm.nr
        sys.exit(1)

    if msh.nodes.nr != len(msh.nodes.node_number):
        print "ERROR: len(nodes.node_number) does not match nodes.nr:", msh.nodes.nr, len(msh.nodes.node_number)
        sys.exit(1)

    if msh.nodes.nr != len(msh.nodes.node_coord):
        print "ERROR: len(nodes.node_coord) does not match nodes.nr:", msh.nodes.nr, len(msh.nodes.node_coord)
        sys.exit(1)

    if msh.elm.nr != len(msh.elm.elm_number):
        print "ERROR: len(elm.elm_number) does not match el.nr:", msh.elm.nr, len(msh.elm.elm_number)
        sys.exit(1)



    start_time = time.time()
    fn = msh.fn

    if fn[0] == '~': 
        import os
        fn = os.path.expanduser(fn)

    if   mode == 'ascii' : f = open(fn, 'w')
    elif mode == 'binary': f = open(fn, 'wb')
    else: print "ERROR, only 'ascii' and 'binary' are allowed"

    if mode == 'binary':
        import struct

    if mode == 'ascii' : f.write('$MeshFormat\n2.2 0 8\n$EndMeshFormat\n')

    elif mode == 'binary': 
        f.write('$MeshFormat\n2.2 1 8\n')
        f.write(struct.pack('i', 1))
        f.write('\n$EndMeshFormat\n')


    # write nodes
    f.write('$Nodes\n')
    f.write(str(msh.nodes.nr) + '\n')

    if mode == 'ascii':
        for ii in xrange(msh.nodes.nr):
            f.write(str(msh.nodes.node_number[ii]) + ' ' + str(msh.nodes.node_coord[ii][0]) + ' ' + str(msh.nodes.node_coord[ii][1]) + ' ' + str(msh.nodes.node_coord[ii][2]) + '\n')
    elif mode == 'binary':
        node_number = msh.nodes.node_number.astype('int32')
        node_coord = msh.nodes.node_coord.astype('float64')
        f.write(numpy.concatenate((node_number[:,numpy.newaxis],node_coord.view('int32')),axis=1).tostring())


    f.write('$EndNodes\n')


            
    # write elements
    f.write('$Elements\n')
    f.write(str(msh.elm.nr) + '\n')

    if mode == 'ascii':
        for ii in xrange(msh.elm.nr):
            line = str(msh.elm.elm_number[ii]) + ' ' + str(msh.elm.elm_type[ii]) + ' ' + str(msh.elm.number_of_tags) + ' ' + str(msh.elm.tag1[ii]) + ' ' + str(msh.elm.tag2[ii]) + ' '
            if msh.elm.elm_type[ii] == 2:
                line += str(msh.elm.node_number_list[ii,:3]).translate(None, '[](),') + '\n'
            elif msh.elm.elm_type[ii] == 4:
                line += str(msh.elm.node_number_list[ii,:]).translate(None, '[](),') + '\n'
            else:
                print "ERROR: gmsh_numpy cant write meshes with elements of type", msh.elm.elm_type[ii] 
                sys.exit(1)
            f.write(line)

    elif mode == 'binary':

        triangles = numpy.where(msh.elm.elm_type == 2)[0]
        triangles_node_list =  msh.elm.node_number_list[triangles, :3].astype('int32')
        triangles_number = msh.elm.elm_number[triangles].astype('int32')
        triangles_tag1 = msh.elm.tag1[triangles].astype('int32')
        triangles_tag2 = msh.elm.tag2[triangles].astype('int32')
        triangles_ones = numpy.ones(len(triangles), 'int32')
        triangles_nr_tags = numpy.ones(len(triangles), 'int32')*msh.elm.number_of_tags
        triangles_elm_type = numpy.ones(len(triangles), 'int32')*2

        f.write(numpy.concatenate((triangles_elm_type[:,numpy.newaxis],triangles_ones[:,numpy.newaxis],triangles_nr_tags[:,numpy.newaxis],
           triangles_number[:,numpy.newaxis], triangles_tag1[:,numpy.newaxis], triangles_tag2[:,numpy.newaxis], triangles_node_list),axis=1).tostring())

        tetra = numpy.where(msh.elm.elm_type == 4)[0]
        tetra_node_list =  msh.elm.node_number_list[tetra].astype('int32')
        tetra_number = msh.elm.elm_number[tetra].astype('int32')
        tetra_tag1 = msh.elm.tag1[tetra].astype('int32')
        tetra_tag2 = msh.elm.tag2[tetra].astype('int32')
        tetra_ones = numpy.ones(len(tetra), 'int32')
        tetra_nr_tags = numpy.ones(len(tetra), 'int32')*msh.elm.number_of_tags
        tetra_elm_type = numpy.ones(len(tetra), 'int32')*4

        f.write(numpy.concatenate((tetra_elm_type[:,numpy.newaxis],tetra_ones[:,numpy.newaxis],tetra_nr_tags[:,numpy.newaxis],
            tetra_number[:,numpy.newaxis], tetra_tag1[:,numpy.newaxis], tetra_tag2[:,numpy.newaxis], tetra_node_list),axis=1).tostring())


    f.write('$EndElements\n')


    # write nodeData, if existent
    if len(msh.nodedata):
        for nd in msh.nodedata:
            write_header(f, nd)
            if mode == 'ascii':
                for ii in xrange(nd.nr):
                    f.write(str(nd.node_number[ii]) + ' ' + str(nd.value[ii]).translate(None, '[](),') + '\n')

            elif mode == 'binary':
                node_number = nd.node_number.astype('int32')
                value = nd.value.astype('float64')
                if nd.nr_comp == 1:
                    f.write(numpy.concatenate((node_number[:,numpy.newaxis],value.view('int32').reshape((len(nd.value),2))),axis=1).tostring())
                else:
                    f.write(numpy.concatenate((node_number[:,numpy.newaxis],value.view('int32')),axis=1).tostring())

            f.write('$EndNodeData\n')



    if len(msh.elmdata):
        for eD in msh.elmdata:
            write_header(f, eD)
            if mode == 'ascii':
                for ii in xrange(eD.nr):
                    f.write(str(eD.elm_number[ii]) + ' ' + str(eD.value[ii]).translate(None, '[](),') + '\n')
            elif mode == 'binary':
                elm_number = eD.elm_number.astype('int32')
                value = eD.value.astype('float64')
                if eD.nr_comp == 1:
                    f.write(numpy.concatenate((elm_number[:,numpy.newaxis],value.view('int32').reshape((len(eD.value),2))),axis=1).tostring())
                else:
                    f.write(numpy.concatenate((elm_number[:,numpy.newaxis],value.view('int32')),axis=1).tostring())

            f.write('$EndElementData\n')


    f.close()
    print time.time() - start_time, "seconds to write", fn






#Adds 1000 to the label of triangles, if less than 100
def create_surface_labels(msh):
    triangles = numpy.where(msh.elm.elm_type == 2)[0]
    triangles = numpy.where(msh.elm.tag1[triangles] < 1000)[0]
    msh.elm.tag1[triangles] += 1000
    msh.elm.tag2[triangles] += 1000

    return msh



