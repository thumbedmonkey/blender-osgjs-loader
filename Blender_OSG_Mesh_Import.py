#################################################################################
## Blender 2.92 - OSG mesh import 
##
## - All credits go to original creators / only porting to Blender 2.92
## - Requires "file.osgjs" and .bin files
##
## - Import addon:
##      Open the Preferences -> Add-ons -> Install... and select the file.
##      Enable add-on
##
## - Usage
##      File -> Import -> Import OSG (.osgjs/.bin) -> select folder
##
## - Animation support not implemented yet
## - UV_coordiantes processing very slow -> need rework
## Porting by: minoutitus
##
#################################################################################
##      /######   /######   /######     /#####  /###### 
##     /##__  ## /##__  ## /##__  ##   |__  ## /##__  ##
##    | ##  \ ##| ##  \__/| ##  \__/      | ##| ##  \__/
##    | ##  | ##|  ###### | ## /####      | ##|  ###### 
##    | ##  | ## \____  ##| ##|_  ## /##  | ## \____  ##
##    | ##  | ## /##  \ ##| ##  \ ##| ##  | ## /##  \ ##
##    |  ######/|  ######/|  ######/|  ######/|  ######/
##     \______/  \______/  \______/  \______/  \______/
#################################################################################






#################################################################################
##     /###### /##      /## /#######   /######  /#######  /########
##    |_  ##_/| ###    /###| ##__  ## /##__  ##| ##__  ##|__  ##__/
##      | ##  | ####  /####| ##  \ ##| ##  \ ##| ##  \ ##   | ##   
##      | ##  | ## ##/## ##| #######/| ##  | ##| #######/   | ##   
##      | ##  | ##  ###| ##| ##____/ | ##  | ##| ##__  ##   | ##   
##      | ##  | ##\  # | ##| ##      | ##  | ##| ##  \ ##   | ##   
##     /######| ## \/  | ##| ##      |  ######/| ##  | ##   | ##   
##    |______/|__/     |__/|__/       \______/ |__/  |__/   |__/  
#################################################################################
import bpy
import json
import os 
import struct
import bmesh
from itertools import chain 
from bpy.types import Operator
from mathutils import Vector, Matrix
import numpy as np
################################################################################# 



#################################################################################
##     /###### /##   /## /######## /###### 
##    |_  ##_/| ### | ##| ##_____//##__  ##
##      | ##  | ####| ##| ##     | ##  \ ##
##      | ##  | ## ## ##| #####  | ##  | ##
##      | ##  | ##  ####| ##__/  | ##  | ##
##      | ##  | ##\  ###| ##     | ##  | ##
##     /######| ## \  ##| ##     |  ######/
##    |______/|__/  \__/|__/      \______/ 
#################################################################################
bl_info = {
    "name": "Import OSG mesh to blender",
    "author": "",
    "version": (1, 0, 0),
    "blender": (2, 92, 00),
    "location": "File > Import > OSG",
    "description": "Import OSG mesh into Blender (no animation support)",
    "warning": "",
    "wiki_url": "",
    "category": "Import",
}
#################################################################################





#################################################################################
## taken from newGameLib\myLibraries\skeletonLib.py
#################################################################################
class Bone:
    def __init__(self):
        self.ID=None
        self.name=None
        self.parentID=None
        self.parentName=None
        self.quat=None
        self.pos=None
        self.matrix=Matrix()  
        self.posMatrix=None
        self.rotMatrix=None
        self.scaleMatrix=None
        self.children=[]
        self.edit=None
#################################################################################



#################################################################################
## taken from newGameLib\myLibraries\myFunction.py
#################################################################################
def Matrix4x4(data):
    return Matrix(np.reshape(data, (-1, 4),'F'))
#################################################################################



#################################################################################
## from newGameLib/meshLib.py
#################################################################################         
#def indicesToTriangles(self,indicesList,matID):
#    for m in range(0, len(indicesList), 3):
#        self.triangleList.append(indicesList[m:m+3] )
#        self.matIDList.append(matID)
def indicesToTriangles(indicesList, triangleList):
    for m in range(0, len(indicesList), 3):
        triangleList.append(indicesList[m:m+3] )
    return triangleList 

#def indicesToTriangleStrips(self,indicesList,matID):
def indicesToTriangleStrips(indicesList, triangleList):
    StartDirection = -1
    id=0
    f1 = indicesList[id]
    id+=1
    f2 = indicesList[id]
    FaceDirection = StartDirection
    while(True):
    #for m in range(len(indicesList)-2):
        id+=1
        f3 = indicesList[id]
        #print f3
        if (f3==0xFFFF):
            if id==len(indicesList)-1:break
            id+=1
            f1 = indicesList[id]
            id+=1
            f2 = indicesList[id]
            FaceDirection = StartDirection   
        else:
            #f3 += 1
            FaceDirection *= -1
            if (f1!=f2) and (f2!=f3) and (f3!=f1):
                if FaceDirection > 0:
                    #self.triangleList.append([(f1),(f2),(f3)])
                    #self.matIDList.append(matID)
                    triangleList.append([(f1),(f2),(f3)])
                else:
                    #self.triangleList.append([(f1),(f3),(f2)])
                    #self.matIDList.append(matID)
                    triangleList.append([(f1),(f3),(f2)])
                #if self.DRAW==True: 
                #    f1,f2,f3  
            f1 = f2
            f2 = f3
        if id==len(indicesList)-1:break
    return triangleList
#################################################################################



#################################################################################
## https://hackersandslackers.com/extract-data-from-complex-json-python/
#################################################################################   
def json_extract(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []
    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    arr.append(v)
                elif isinstance(v, (dict, list)):
                    extract(v, arr, key)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr
    values = extract(obj, arr, key)
    return values
#################################################################################



#################################################################################
## 
#################################################################################
def decodeQuantize(input,s,a,itemsize):
    x=[0]*len(input)
    id=0
    for r in range(int(len(input)/itemsize)):
        for l in range(itemsize):
            x[id]=s[l]+input[id]*a[l]
            id+=1
    return x
#################################################################################



#################################################################################
##
#################################################################################
def decodePredict(indices,input,itemsize):  
    t=input  
    if len(indices)>0:
        t=input  
        e=itemsize
        i=indices  
        n=int(len(t)/e)
        r=[0]*n
        a=len(i)-1
        r[i[0]]=1
        r[i[1]]=1
        r[i[2]]=1  
        s=2
        while(s<a):
            o=s-2
            u=i[o]
            l=i[o+1]
            h=i[o+2]
            c=i[o+3]
            if 1!=r[c]:
                r[c]=1
                u*=e
                l*=e
                h*=e
                c*=e      
                d=0
                while(d<e):
                    t[c+d]=t[c+d]+t[l+d]+t[h+d]-t[u+d]
                    d+=1
            s+=1
    return t
#################################################################################



#################################################################################
##
#################################################################################
def decodeVarint(binfilepath,offset,size,type):
    with open(binfilepath, "rb") as g:      
        g.seek(offset)
        n=[0]*size
        a=0
        s=0  
        while(a!=size):
            shift = 0
            result = 0
            while True: 
                #byte = g.B(1)[0]
                #data=struct.unpack(self.endian+n*'B',self.inputFile.read(n))
                byte=struct.unpack('<'+1*'B',g.read(1))[0]
                result |= (byte & 127) << shift
                shift += 7
                if not (byte & 0x80):break      
            n[a]=result    
            a+=1
        if type[0]!='U':
            l=0
            while(l<size):
                h=n[l]
                n[l]=h>>1^-(1&h)
                l+=1
        return n
#################################################################################



#################################################################################
##
#################################################################################   
def decodeDelta(t,e):
    i=e|0
    n=len(t)
    if i>=len(t):r=None
    else:r=t[i]
    a=i+1
    while(a<n):
        s=t[a]
        r=t[a]=r+(s>>1^-(1&s))
        a+=1
    return t  
#################################################################################



#################################################################################
##
#################################################################################
def decodeImplicit(input,n):
    IMPLICIT_HEADER_LENGTH=3
    IMPLICIT_HEADER_MASK_LENGTH=1
    IMPLICIT_HEADER_PRIMITIVE_LENGTH=0
    IMPLICIT_HEADER_EXPECTED_INDEX=2
    highWatermark=2
    
    t=input
    e=[0]*t[IMPLICIT_HEADER_PRIMITIVE_LENGTH]
    a=t[IMPLICIT_HEADER_EXPECTED_INDEX]
    s=t[IMPLICIT_HEADER_MASK_LENGTH]
    o=t[IMPLICIT_HEADER_LENGTH:s+IMPLICIT_HEADER_LENGTH]
    r=highWatermark
    u=32*s-len(e)
    l=1<<31
    h=0  
    while(h<s):
        c=o[h]
        d=32
        p=h*d
        if h==s-1:f=u
        else:f=0
        g1=f
        while(g1<d):
            if c&l>>g1:
                e[p]=t[n]
                n+=1  
            else:
                if r:
                    e[p]=a
                else:
                    e[p]=a
                    a+=1      
            g1+=1
            p+=1
        h+=1
    return e    
#################################################################################



#################################################################################
##
################################################################################# 
def decodeWatermark(t,e,i):
    n=i[0]
    r=len(t)
    a=0
    while(a<r):
        s=n-t[a]
        e[a]=s
        if n<=s:n=s+1
        a+=1
    return e,n
#################################################################################



#################################################################################
## 
#################################################################################  
def getIndices(itemsize,size,offset,type,binfilepath,mode,magic):
    with open(binfilepath, "rb") as g:    
        if type != "Uint8Array":
            bytes = decodeVarint(binfilepath,offset,size*itemsize,type)
        else:
            g.seek(offset)
            #bytes=list(g.B(size*itemsize))  
            n = size*itemsize
            bytes = list(struct.unpack('<'+n*'B',g.read(n)))
                  
        #log.write([magic],0)
        #log.write(bytes,0)    
        
        IMPLICIT_HEADER_LENGTH=3
        IMPLICIT_HEADER_MASK_LENGTH=1
        IMPLICIT_HEADER_PRIMITIVE_LENGTH=0
        IMPLICIT_HEADER_EXPECTED_INDEX=2
        highWatermark=2
            
        if mode=='TRIANGLE_STRIP':
                k=IMPLICIT_HEADER_LENGTH+bytes[IMPLICIT_HEADER_MASK_LENGTH]
                bytes=decodeDelta(bytes,k)  
                #log.write([magic,k],0)  
                #log.write(bytes,0)    
                bytes=decodeImplicit(bytes,k)
                #log.write([magic,k],0)  
                #log.write(bytes,0)      
                i=[magic]  
                bytes,magic=decodeWatermark(bytes,bytes,i)
                #log.write([magic],0)  
                #log.write(bytes,0)  
                
        elif mode=='TRIANGLES':
                k=0
                bytes=decodeDelta(bytes,k)
                #log.write([magic],0)  
                #log.write(bytes,0)      
                i=[magic]  
                bytes,magic=decodeWatermark(bytes,bytes,i)
                #log.write([magic],0)  
                #log.write(bytes,0)  
               
        return magic,bytes
#################################################################################



#################################################################################
## get vertex-indices
#################################################################################
#def getPrimitiveSetList(ys,PrimitiveSetList,n):
def getPrimitiveSetList(PrimitiveSetList):
    global magic
    mode = None
    magic = 0
    indiceArray = []
    
    for PrimitiveSet in PrimitiveSetList:
        PrimitiveSets = {"DrawElementsUInt" : "Uint32Array", "DrawElementsUShort" : "Uint16Array", "DrawElementsUByte" : "Uint8Array"}
        ArrayValueType = list(PrimitiveSet.keys())[0]
        for [Primitive, Type] in PrimitiveSets.items():
            if Primitive in ArrayValueType:
                values = PrimitiveSet[ArrayValueType]                        
                mode = values['Mode']      
                Size = None
                Offset = None
                Encoding = None
                ItemSize = None
                if mode != 'LINES':
                    if 'Indices' in values:
                        Indices = values['Indices']
                        ItemSize = Indices['ItemSize']
                        ArrayValueType_ = list(Indices['Array'].keys())[0] 
                        if ArrayValueType_ == Type:  
                            #log.write(['Indice:','mode:',mode,type,'Size:',Size,'Offset:',Offset,'Encoding:',Encoding,'magic:',magic],n)
                            values = Indices['Array'][ArrayValueType_]
                            Size = values['Size']
                            Offset = values['Offset']
                            if 'Encoding' in values: Encoding = values['Encoding']
                            #log.write('Indice:' + ' mode:' + str(mode) + ' ' + ArrayValueType_ + ' Size:' + str(Size) + ' Offset:' + str(Offset) + ' Encoding:' + Encoding + ' magic:' + str(magic) )
                            binfilepath = folder+os.sep+"model_file.bin"
                            if os.path.exists(binfilepath):
                                if Type == "Uint32Array":
                                  if Encoding == 'varint':
                                    magic,indices = getIndices(ItemSize,Size,Offset,Type,binfilepath,mode,magic) 
                                    indiceArray.append([indices,mode,ArrayValueType])
                                if Type == "Uint16Array":
                                    if Encoding == 'varint':
                                        magic,indices = getIndices(ItemSize,Size,Offset,Type,binfilepath,mode,magic) 
                                        indiceArray.append([indices,mode,ArrayValueType]) 
                                    else:
                                        with open(binfilepath, "rb") as g:      
                                            g.seek(Offset) 
                                            n = Size*ItemSize
                                            indices = struct.unpack('<'+n*'H',g.read(n*2))   
                                            indiceArray.append([indices,mode,ArrayValueType])
                                if Type == "Uint8Array":
                                    magic,indices = getIndices(ItemSize,Size,Offset,Type,binfilepath,mode,magic) 
                                    indiceArray.append([indices,mode,ArrayValueType]) 
                else:
                    print('LINES')
         
         
        if 'DrawArrays' in ArrayValueType:
            values = PrimitiveSet[ArrayValueType]
            Count = values['Count']
            First = values['First']
            mode = values['Mode']
            indices = list(range(First, First+Count))
            indiceArray.append([indices,mode,ArrayValueType])
                
                
    return indiceArray
#################################################################################



#################################################################################
## get vertex and texture coordinates
#################################################################################
def getVertexAttributeList(VertexAttributeList): 
    vertexArray=[]
    texArray=[]
  
    modes = ["Vertex", "TexCoord0"] # "Normal", "Tangent"
    for mode in modes: 
      if mode in VertexAttributeList:
        values = VertexAttributeList[mode]
        if 'ItemSize' in values:
            Size = None
            Offset = None
            Encoding = None
            ItemSize = None
            type = None  
            ItemSize = int(values['ItemSize'])
            ArrayValueType = list(VertexAttributeList[mode]['Array'].keys())[0]
            values = VertexAttributeList[mode]['Array'][ArrayValueType]
            File = values['File']
            Size = values['Size']
            Offset = values['Offset']
            if 'Encoding' in values: Encoding = values['Encoding']
            #log.write('Vertex:' + ' mode:' + str(mode) + ' ' + ArrayValueType + ' Size:' + str(Size) + ' Offset:' + str(Offset) + ' Encoding:' + Encoding)
              
            if ArrayValueType == 'Int32Array':
                if Encoding=='varint': 
                    binfilepath = folder+os.sep+File.split('.gz')[0]
                    if os.path.exists(binfilepath):
                        bytes = decodeVarint(binfilepath,Offset,Size*ItemSize,ArrayValueType)
                        if mode == "Vertex":
                            vertexArray.append([bytes,Encoding,ItemSize])
                        if mode == "TexCoord0":
                            texArray.append([bytes,Encoding,ItemSize])  
              
            if ArrayValueType == 'Float32Array':
                if Encoding!='varint': 
                    binfilepath = folder+os.sep+File.split('.gz')[0]
                    if os.path.exists(binfilepath): 
                        with open(binfilepath, "rb") as g:      
                            g.seek(Offset) 
                            n = Size*ItemSize
                            bytes = struct.unpack('<'+n*'f',g.read(n*4))
                            mylist = []
                            if mode == "Vertex":
                                for m in range(Size):
                                    mylist.append(bytes[m*ItemSize:m*ItemSize+ItemSize])
                                vertexArray.append([mylist,Encoding])   
                            if mode == "TexCoord0":
                                for m in range(Size):
                                    u,v = bytes[m*ItemSize:m*ItemSize+ItemSize]
                                    mylist.append([u,1-v])
                                texArray.append([mylist,Encoding])  
      
    return vertexArray,texArray                  
#################################################################################



#################################################################################
## extract the geometry 
#################################################################################
def getGeometry(parent):
    print('#'*50,'Geometry')
    mode = None
    indiceArray = []
    vertexArray = []
    texArray = []
    attributes = {}
    
    #log.write('Geometry' + str(n))
    if 'PrimitiveSetList' in parent:
        PrimitiveSetList = parent['PrimitiveSetList']
        indiceArray = getPrimitiveSetList(PrimitiveSetList)

    if 'UserDataContainer' in parent:
        UserDataContainer = parent['UserDataContainer']
        for values in UserDataContainer['Values']:
            if values['Name']: attributes[values['Name']] = values['Value']

    if 'VertexAttributeList' in parent:
        VertexAttributeList = parent['VertexAttributeList']
        vertexArray,texArray = getVertexAttributeList(VertexAttributeList)  


    # build faces, verts and uv_coordinates  
    verts = []
    faces = []
    uv_coordinates = []
    if len(indiceArray)>0:
        for [indices,mode,ArrayValueType] in indiceArray: 
            if mode == 'TRIANGLE_STRIP':
                faces = indicesToTriangleStrips(indices,faces)
            if mode == 'TRIANGLES':
                faces = indicesToTriangles(indices,faces) 
            
        indices = indiceArray[0][0]
        mode = indiceArray[0][1] 
        if len(vertexArray) == 1:
            if vertexArray[0][1] == 'varint':
                bytes = vertexArray[0][0] 
                ItemSize = vertexArray[0][2]
                if mode == 'TRIANGLE_STRIP':
                  bytes = decodePredict(indices,bytes,ItemSize)
                s1 = float(attributes['vtx_bbl_x'])
                s2 = float(attributes['vtx_bbl_y'])
                s3 = float(attributes['vtx_bbl_z'])
                s = [s1,s2,s3] 
                a1 = float(attributes['vtx_h_x'])
                a2 = float(attributes['vtx_h_y'])
                a3 = float(attributes['vtx_h_z'])
                a = [a1,a2,a3]
                floats = decodeQuantize(bytes,s,a,ItemSize)
                verts = [floats[m:m+ItemSize]for m in range(0,len(floats),3)]
            else:
                verts = vertexArray[0][0]
                  
        if len(texArray) == 1:
            if texArray[0][1] == 'varint':
                bytes = texArray[0][0]
                ItemSize = texArray[0][2]
                if mode == 'TRIANGLE_STRIP':
                    bytes = decodePredict(indices,bytes,ItemSize)
                s1 = float(attributes['uv_0_bbl_x'])
                s2 = float(attributes['uv_0_bbl_y'])
                s = [s1,s2]
                a1 = float(attributes['uv_0_h_x'])
                a2 = float(attributes['uv_0_h_y'])
                a = [a1,a2]
                floats = decodeQuantize(bytes,s,a,ItemSize)
                for m in range(0,len(floats),ItemSize):
                    u,v = floats[m:m+ItemSize]
                    uv_coordinates.append([u,v]) # uv_coordinates.append([u,1-v])
            else:
                uv_coordinates = texArray[0][0]
    

    # use name or generate one
    name_addition = ""
    if 'Name' in parent:
        name_addition = str(parent['Name'])
    else: name_addition = "mesh"    
    if 'UniqueID' in parent:
        name_addition += "__ID" + str(parent['UniqueID'])
    
    # add the new mesh
    mesh = bpy.data.meshes.new(name_addition)  

    # make a mesh from a list of vertices/edges/faces   
    mesh.from_pydata(verts,[],faces)
     
    ## calulate UV coorindates - very slow
    if uv_coordinates:
        uv_layer = mesh.uv_layers.new()
        # https://blender.stackexchange.com/questions/160157/how-to-set-uv-coordinates-for-a-mesh-in-blender-2-8x-with-script
        print('UV_coordiantes (' + str(len(uv_coordinates)) + ') processing can be very slow...')
        for face in mesh.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                uv_layer.data[loop_idx].uv = uv_coordinates[:][vert_idx]

    # create new object
    obj = bpy.data.objects.new(mesh.name, mesh)
    # if collection doesn't exist, create one
    if not 'Collection' in bpy.data.collections:
        bpy.context.scene.collection.children.link(bpy.data.collections.new("Collection"))
    # get collection and link with object 
    col = bpy.data.collections["Collection"]
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
 
    # find material info, generate and assign material to object  
    MaterialArray = json_extract(parent,'osg.Material')
    if MaterialArray: 
        for material in MaterialArray: 
            if 'Name' in material:
                material_name = material['Name']
            else:
                material_name = 'imported_material_ID' + str(material['UniqueID'])
            material_new = bpy.data.materials.new(material_name)
            material_new.use_nodes = True
            principled_node = (material_new.node_tree.nodes.get('Principled BSDF') or material_new.node_tree.nodes.new('Principled BSDF'))
            #principled_node.inputs['Ambient'].default_value = material['Ambient']
            principled_node.inputs['Base Color'].default_value = material['Diffuse']
            principled_node.inputs['Emission'].default_value = material['Emission']
            principled_node.inputs['Emission Strength'].default_value = material['Emission'][3]
            principled_node.inputs['Roughness'].default_value = material['Shininess']
            principled_node.inputs['Specular'].default_value = material['Specular'][3]
            # viewport display
            material_new.diffuse_color = [material['Diffuse'][0], material['Diffuse'][1], material['Diffuse'][2], 1]
            # Assign it to object
            if obj.data.materials:
                # assign to 1st material slot
                obj.data.materials[0] = material_new
                #obj.active_material_index = 0
            else:
                # no slots
                obj.data.materials.append(material_new)
                #obj.active_material_index = len(obj.data.materials)-1


    return obj  
#################################################################################



#################################################################################
##
#################################################################################
def getGeometryNode(parent,boneParent):
    #log.write(['Geometry'],n)
    obj = getGeometry(parent)
    
    obj.matrix_world = boneParent.matrix

    #n+=4
    if 'Children' in parent:
        getChildren(parent['Children'],boneParent) 
#################################################################################




#################################################################################
##
################################################################################# 
def getMatrixTransform(parent,boneParent):
    #log.write(['MatrixTransform'],n)
    #n+=4
    bone = Bone()
    bone.parentName = boneParent.name
    
    if 'Name' in parent:
        bone.name = parent['Name']
       
    if 'Matrix' in parent:
        floats = parent['Matrix']
        #log.write(floats,n)  
        bone.matrix = Matrix4x4(floats)
        bone.matrix = boneParent.matrix @ bone.matrix # since 2.80: Matrix multiplication previously used *, scripts should now use @

    if 'Children' in parent:
        getChildren(parent['Children'],bone) 
#################################################################################




#################################################################################
## TODO - not implemented yet
#################################################################################
def getSkeletonNode(parent,boneParent):
    #global firstmatrix
    #write(log,['Skeleton'],n)
    #n+=4
    #bone=Bone()    
    #bone.name=str(len(skeleton.boneList))
    #skeleton.boneList.append(bone)
    #bone.parentName=boneParent.name
    #
    #firstmatrix=boneParent.matrix
    #
    #Name=None
    #for child in parent.children:
    #    values=ys.values(child.header,':')
    #    Name=ys.getValue(values,'"Name"','""')
    #    if Name:
    #        Name=getSplitName(Name,'_',-1)
    #        #print Name
    #        write(log,[Name],n)
    #        #if len(Name)<25:bone.name=Name
    #        boneIndeksList[Name]=bone.name
    #
    #
    #for child in parent.children:
    #    if '"Matrix"' in child.header:
    #        floats=ys.values(child.data,'f')
    #        write(log,floats,n)
    #        bone.matrix=Matrix4x4(floats)
    #        bone.matrix*=boneParent.matrix
    #for child in parent.children:
    #    if '"Children"' in child.header:
    #        getChildren(ys,child,n,bone)
    
    getMatrixTransform(parent,boneParent)
#################################################################################




#################################################################################
## TODO - not implemented yet
#################################################################################
def getRigGeometryNode(parent,boneParent):    
    #write(log,['RigGeometry'],n)            
    #mesh=getRigGeometry(ys,parent,n)
    #if len(mesh.vertPosList)>0:
    #    model.meshList.append(mesh)
    #    mesh.matrix=boneParent.matrix
    #                    
    #n+=4
    #for child in parent.children:
    #    if '"Children"' in child.header:
    #        getChildren(ys,child,n,boneParent)
    
    
    #log.write(['RigGeometry'],n) 
    getRigGeometry(parent)
    
    if 'Children' in parent:
        getChildren(parent['Children'],bone) 
#################################################################################




#################################################################################
## TODO - not implemented yet
#################################################################################
def getBoneNode(parent,boneParent):
#    write(log,['Bone'],n)
#    bone=Bone()
#    bone.parentName=boneParent.name
#    bone.name=str(len(skeleton.boneList))
#    skeleton.boneList.append(bone)
#
#
#    n+=4
#    Name=None
#    for child in parent.children:
#        values=ys.values(child.header,':')
#        #print child.header
#        Name=ys.getValue(values,'"Name"','""')
#        if Name:
#            Name=getSplitName(Name,'_',-1)
#            write(log,[Name],n)
#            #print Name
#            #if len(Name)<25:bone.name=Name
#            boneIndeksList[Name]=bone.name
#            
#    for child in parent.children:
#        if '"Matrix"' in child.header:
#            values=ys.values(child.header,':')
#            floats=ys.values(child.data,'f')
#            bone.matrix=Matrix4x4(floats)
#            bone.matrix*=boneParent.matrix
#            
#        if '"InvBindMatrixInSkeletonSpace"' in child.header:
#            bindbone=Bone()
#            #if Name:bindbone.name=Name
#            bindbone.name=bone.name
#            bindskeleton.boneList.append(bindbone)
#            floats=ys.values(child.data,'f')
#            write(log,[floats],n+4)
#            matrix=Matrix4x4(floats).invert()
#            bindbone.matrix=matrix*firstmatrix
#            
#    for child in parent.children:
#        if '"Children"' in child.header:
#            getChildren(ys,child,n,bone)

     if 'Children' in parent:
        getChildren(parent['Children'],bone) 
#################################################################################





#################################################################################
## TODO - not implemented yet
#################################################################################
def getRigGeometry(parent):
    #print '#'*50,'RigGeometry'
    #n+=4
    #BoneMap=[0]*1000
    #bones=[]
    #weights=[]
    #mode=None
    #indiceArray=[]
    #vertexArray=[]
    #texArray=[]
    #atributes={}
    #for child in parent.children:
    #    if "BoneMap" in child.header:
    #        write(log,['BoneMap'],n)
    #        values=ys.values(child.data,':')
    #        #print values
    #        for value in values:
    #            id=ys.getValue(values,value,'i')
    #            name=value.split('"')[1]
    #            BoneMap[id]=getSplitName(name,'_',-1)
    #    if "SourceGeometry" in child.header:
    #        values=ys.values(child.data,':')
    #        PrimitiveSetList=ys.get(child,'"PrimitiveSetList"')
    #        if PrimitiveSetList:
    #            indiceArray=getPrimitiveSetList(ys,PrimitiveSetList,n)
    #            
    #        UserDataContainer=ys.get(child,'"UserDataContainer"')
    #        if UserDataContainer:
    #            for UserData in UserDataContainer:
    #                Values=ys.get(UserData,'"Values"')
    #                if Values:
    #                    for a in Values[0].children:
    #                        values=ys.values(a.data,':')
    #                        Name=ys.getValue(values,'"Name"','""')
    #                        Value=ys.getValue(values,'"Value"','""')
    #                        if Name:atributes[Name]=Value
    #                    
    #        VertexAttributeList=ys.get(child,'"VertexAttributeList"')
    #        if VertexAttributeList:
    #            vertexArray,texArray=getVertexAttributeList(ys,VertexAttributeList,n)
    #        
    #            
    #    if "UserDataContainer" in child.header:
    #        write(log,['UserDataContainer'],n)
    #        Values=ys.get(child,'"Values"')
    #        if Values:
    #            for a in Values[0].children:
    #                values=ys.values(a.data,':')
    #                for value in values:
    #                    id=ys.getValue(values,value)
    #                    write(log,[value,':',id],n+4)
    #    if "VertexAttributeList" in child.header:
    #        write(log,['VertexAttributeList'],n)
    #        Bones=ys.get(child,'"Bones"')
    #        if Bones:
    #            write(log,['Bones'],n+4)
    #            values=ys.values(Bones[0].data,':')
    #            ItemSize=ys.getValue(values,'"ItemSize"','i')
    #            write(log,['"ItemSize"',':',ItemSize],n+8)
    #            Uint16Array=ys.get(Bones[0],'"Uint16Array"')
    #            if Uint16Array:
    #                type="Uint16Array"
    #                values=ys.values(Uint16Array[0].data,':')
    #                File=ys.getValue(values,'"File"','""')
    #                Size=ys.getValue(values,'"Size"','i')
    #                Offset=ys.getValue(values,'"Offset"','i')
    #                Encoding=ys.getValue(values,'"Encoding"','""')
    #                write(log,['"File"',':',File],n+8)
    #                write(log,['"Size"',':',Size],n+8)
    #                write(log,['"Offset"',':',Offset],n+8)
    #                write(log,['"Encoding"',':',Encoding],n+8)
    #                
    #                if Encoding=='varint':
    #                    path=os.path.dirname(ys.filename)+os.sep+"model_file.bin.gz.txt"
    #                    if os.path.exists(path)==False:path=os.path.dirname(ys.filename)+os.sep+"model_file.bin"
    #                    if os.path.exists(path)==False:path=os.path.dirname(ys.filename)+os.sep+values['"File"'].split('"')[1]#+'.txt'
    #                    if os.path.exists(path)==True:
    #                        file=open(path,'rb')
    #                        g=BinaryReader(file)
    #                        list=decodeVarint(g,Offset,Size*ItemSize,type)
    #                        #write(log,list,0)
    #                        for m in range(Size):
    #                            bones.append(list[m*ItemSize:m*ItemSize+ItemSize])
    #                        file.close()
    #                
    #                
    #        Weights=ys.get(child,'"Weights"')
    #        if Weights:
    #            write(log,['Weights'],n+4)
    #            values=ys.values(Weights[0].data,':')
    #            ItemSize=ys.getValue(values,'"ItemSize"','i')
    #            write(log,['"ItemSize"',':',ItemSize],n+8)
    #            Float32Array=ys.get(Weights[0],'"Float32Array"')
    #            if Float32Array:
    #                values=ys.values(Float32Array[0].data,':')
    #                File=ys.getValue(values,'"File"','""')
    #                Size=ys.getValue(values,'"Size"','i')
    #                Offset=ys.getValue(values,'"Offset"','i')
    #                Encoding=ys.getValue(values,'"Encoding"','""')
    #                write(log,['"File"',':',File],n+8)
    #                write(log,['"Size"',':',Size],n+8)
    #                write(log,['"Offset"',':',Offset],n+8)
    #                write(log,['"Encoding"',':',Encoding],n+8)
    #                
    #                if Encoding=='varint':
    #                    path=os.path.dirname(ys.filename)+os.sep+"model_file.bin.gz.txt"
    #                    if os.path.exists(path)==False:path=os.path.dirname(ys.filename)+os.sep+"model_file.bin"
    #                    if os.path.exists(path)==False:path=os.path.dirname(ys.filename)+os.sep+values['"File"'].split('"')[1]#+'.txt'
    #                    if os.path.exists(path)==True:
    #                        file=open(path,'rb')
    #                        g=BinaryReader(file)
    #                        list=decodeVarint(g,Offset,Size*ItemSize,type)
    #                        #write(log,list,0)
    #                        file.close()
    #                else:
    #                    path=os.path.dirname(ys.filename)+os.sep+"model_file.bin.gz.txt"
    #                    if os.path.exists(path)==False:path=os.path.dirname(ys.filename)+os.sep+"model_file.bin"
    #                    if os.path.exists(path)==False:path=os.path.dirname(ys.filename)+os.sep+values['"File"'].split('"')[1]#+'.txt'
    #                    if os.path.exists(path)==True:
    #                        file=open(path,'rb')
    #                        g=BinaryReader(file)
    #                        g.seek(Offset)
    #                        list=g.f(Size*ItemSize)
    #                        #write(log,list,0)
    #                        for m in range(Size):
    #                            weights.append(list[m*ItemSize:m*ItemSize+ItemSize])
    #                        file.close()
    #                        
    #        
    #        
    ##print atributes        
    #mesh=Mesh()    
    #if len(bones)>0 and len(Weights)>0:
    #    mesh.BoneMap=BoneMap
    #    skin=Skin()
    #    mesh.skinList.append(skin)
    #    mesh.skinIndiceList=bones
    #    mesh.skinWeightList=weights
    #if len(indiceArray)>0:
    #    for [indices,mode] in indiceArray:
    #        print mode,len(indices)    
    #        mat=Mat()
    #        mesh.matList.append(mat)
    #        mat.IDStart=len(mesh.indiceList)
    #        mat.IDCount=len(indices)
    #        mesh.indiceList.extend(indices)
    #        if mode=='"TRIANGLE_STRIP"':mat.TRISTRIP=True
    #        if mode=='"TRIANGLES"':mat.TRIANGLE=True
    #        
    #    indices=indiceArray[0][0]
    #    mode=indiceArray[0][1]    
    #    if len(vertexArray)==1:
    #        if vertexArray[0][1]=='"varint"':
    #            bytes=vertexArray[0][0]                
    #            ItemSize=vertexArray[0][2]
    #            if mode=='"TRIANGLE_STRIP"':
    #                bytes=decodePredict(indices,bytes,ItemSize)
    #            s1=float(atributes['vtx_bbl_x'])
    #            s2=float(atributes['vtx_bbl_y'])
    #            s3=float(atributes['vtx_bbl_z'])
    #            s=[s1,s2,s3]            
    #            a1=float(atributes['vtx_h_x'])
    #            a2=float(atributes['vtx_h_y'])
    #            a3=float(atributes['vtx_h_z'])
    #            a=[a1,a2,a3]
    #            floats=decodeQuantize(bytes,s,a,ItemSize)
    #            mesh.vertPosList=[floats[m:m+ItemSize]for m in range(0,len(floats),3)]
    #        else:
    #            list=vertexArray[0][0]
    #            mesh.vertPosList=list
    #            
    #    if len(texArray)==1:
    #        if texArray[0][1]=='"varint"':
    #            bytes=texArray[0][0]                
    #            ItemSize=texArray[0][2]
    #            if mode=='"TRIANGLE_STRIP"':
    #                bytes=decodePredict(indices,bytes,ItemSize)
    #            s1=float(atributes['uv_0_bbl_x'])
    #            s2=float(atributes['uv_0_bbl_y'])
    #            s=[s1,s2]            
    #            a1=float(atributes['uv_0_h_x'])
    #            a2=float(atributes['uv_0_h_y'])
    #            a=[a1,a2]
    #            floats=decodeQuantize(bytes,s,a,ItemSize)
    #            #mesh.vertUVList=[floats[m:m+ItemSize]for m in range(0,len(floats),ItemSize)]
    #            for m in range(0,len(floats),ItemSize):
    #                u,v=floats[m:m+ItemSize]
    #                mesh.vertUVList.append([u,1-v])
    #        else:
    #            list=texArray[0][0]
    #            mesh.vertUVList=list
    #return mesh
    
    geometries = json_extract(parent,'osg.Geometry') 
    for geometry in geometries: 
        getGeometry(geometry)
          
#################################################################################



#################################################################################
##
#################################################################################
def getChildren(parent,boneParent):

    #print('len(parent) ', len(parent)) 
    for i in range(0, len(parent)): 
        child = parent[i]
        if 'osg.MatrixTransform' in child:
            getMatrixTransform(child['osg.MatrixTransform'],boneParent)
        if 'osg.Node' in child:
            getNode(child['osg.Node'],boneParent)
        if 'osgAnimation.Skeleton' in child:
            print('osgAnimation.Skeleton')
            getSkeletonNode(child['osgAnimation.Skeleton'],boneParent)
        if 'osgAnimation.RigGeometry' in child:
            print('osgAnimation.RigGeometry')
            getRigGeometryNode(child['osgAnimation.RigGeometry'],boneParent)
        if 'osg.Geometry' in child:
            getGeometryNode(child['osg.Geometry'],boneParent)
        if 'osg.osgAnimation' in child:
            print('osg.osgAnimation')
            getBoneNode(child['osg.osgAnimation'],boneParent)
#################################################################################



#################################################################################
## 
#################################################################################
#def getNode(parent,n,boneParent):
def getNode(parent,boneParent):
    #log.write(['Node'],n)
    #n+=4
    
    bone = Bone()    
    bone.parentName = boneParent.name
    bone.matrix = boneParent.matrix
    
    if 'Name' in parent:
        bone.name = parent['Name']
        #log.write([Name],n)
        
    if 'Children' in parent:
        getChildren(parent['Children'],bone)    
#################################################################################



#################################################################################
##
#################################################################################
def osgParser(fullpath):

    # import file
    with open(fullpath, "r") as read_file:
        data = json.load(read_file)
    
    bone = Bone()
    bone.name = 'scene'
    root_node = json_extract(data,'osg.Node')
    getNode(root_node[0], bone)
#################################################################################



#################################################################################
##     /##      /##  /######  /###### /##   /##
##    | ###    /### /##__  ##|_  ##_/| ### | ##
##    | ####  /####| ##  \ ##  | ##  | ####| ##
##    | ## ##/## ##| ########  | ##  | ## ## ##
##    | ##  ###| ##| ##__  ##  | ##  | ##  ####
##    | ##\  $ | ##| ##  | ##  | ##  | ##\  ###
##    | ## \/  | ##| ##  | ## /######| ## \  ##
##    |__/     |__/|__/  |__/|______/|__/  \__/
#################################################################################
def importOSG(fullpath):
    global folder, filename
    input = os.path.split(fullpath) 
    folder = input[0]
    filename = input[1]
    #global log
    #log=open(os.path.join(folder,'log.txt'),'w')
    os.system("cls")
    print()
    print(fullpath)
    print()
    #ext = filename.split('.')[-1].lower()
    osgParser(fullpath)
#################################################################################



#################################################################################
##     /###### /##      /## /#######   /######  /#######  /########
##    |_  ##_/| ###    /###| ##__  ## /##__  ##| ##__  ##|__  ##__/
##      | ##  | ####  /####| ##  \ ##| ##  \ ##| ##  \ ##   | ##   
##      | ##  | ## ##/## ##| #######/| ##  | ##| #######/   | ##   
##      | ##  | ##  ###| ##| ##____/ | ##  | ##| ##__  ##   | ##   
##      | ##  | ##\  $ | ##| ##      | ##  | ##| ##  \ ##   | ##   
##     /######| ## \/  | ##| ##      |  ######/| ##  | ##   | ##   
##    |______/|__/     |__/|__/       \______/ |__/  |__/   |__/ 
#################################################################################
class IMPORT_OSG_OT_objects(Operator):
    """IMPORT OSG"""          # use this as a tooltip for menu items and buttons.
    
    bl_idname = "import_osg.objects"  # unique identifier for buttons and menu items to reference.
    bl_label = "Import OSG (.osgjs/.bin)"   # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}   # enable undo for the operator.    
    
    # define this to tell 'fileselect_add' that we want a directory    name="",
    directory: bpy.props.StringProperty(maxlen=1024, subtype='FILE_PATH', options={'HIDDEN', 'SKIP_SAVE'})
    
    def execute(self, context):        # execute() is called when running the operator.
        
        print("Path imported: '" + self.directory + "'")
        
        importOSG(os.path.join(self.directory,"file.osgjs"))
        
        return {'FINISHED'}            # lets Blender know the operator finished successfully.
    
    def invoke(self, context, event):
        # open browser, take reference to 'self' read the path to selected
        # file, put path in predetermined self fields.
        # see: https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        # tells Blender to hang on for the slow user input
        return {'RUNNING_MODAL'}
#################################################################################



#################################################################################
##
##     /#######  /########  /######  /######  /######  /######## /######## /####### 
##    | ##__  ##| ##_____/ /##__  ##|_  ##_/ /##__  ##|__  ##__/| ##_____/| ##__  ##
##    | ##  \ ##| ##      | ##  \__/  | ##  | ##  \__/   | ##   | ##      | ##  \ ##
##    | #######/| #####   | ## /####  | ##  |  ######    | ##   | #####   | #######/
##    | ##__  ##| ##__/   | ##|_  ##  | ##   \____  ##   | ##   | ##__/   | ##__  ##
##    | ##  \ ##| ##      | ##  \ ##  | ##   /##  \ ##   | ##   | ##      | ##  \ ##
##    | ##  | ##| ########|  ######/ /######|  ######/   | ##   | ########| ##  | ##
##    |__/  |__/|________/ \______/ |______/ \______/    |__/   |________/|__/  |__/    
##
#################################################################################
def import_osg_objects_button(self, context):
    self.layout.operator(IMPORT_OSG_OT_objects.bl_idname, text="Import OSG (.osgjs/.bin)", icon='IMAGE_DATA')

classes = (
    IMPORT_OSG_OT_objects,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(import_osg_objects_button)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(import_osg_objects_button)
 
    for cls in classes:
        if hasattr(bpy.types, cls.__name__):
            bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    unregister()
    register()
#################################################################################







