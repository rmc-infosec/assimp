#!/usr/bin/env python3
"""
Generate minimal valid seed files for low-coverage binary format fuzzers.

Formats covered:
  1. Unreal 3D (_d.3d + _a.3d)
  2. NDO (Nendo .ndo)
  3. Q3BSP (.pk3 containing .bsp)

Each seed is crafted by reading the importer source code and constructing
the minimum binary data that will exercise the maximum number of code paths.
"""

import struct
import os
import zipfile
import io

###############################################################################
# 1. Unreal 3D (_d.3d data file + _a.3d animation file)
#
# From UnrealLoader.cpp:
#   _d.3d format:
#     uint16 numTris
#     uint16 numVert
#     44 bytes padding (skipped)
#     Per triangle (16 bytes each):
#       3x uint16  vertex indices
#       int8       type (mesh flag)
#       1 byte     padding (skipped via IncPtr(1))
#       3x 2 bytes UV coords (mTex[3][2], each uint8)
#       uint8      textureNum
#       1 byte     padding (skipped via IncPtr(1))
#
#   _a.3d format:
#     uint16 numFrames
#     uint16 frameSize (should == numVert * 4)
#     Per frame, per vertex: int32 compressed vertex
#
#   The importer also requires the file naming convention:
#     prefix_d.3d (data) and prefix_a.3d (animation)
#   It derives paths from the filename: prefix = everything before last '_'
#
#   The fuzzer feeds data via ReadFileFromMemory with the _d.3d extension,
#   but the real importer tries to Open() both _d.3d and _a.3d from IOSystem.
#   For fuzzing seeds we just create the _d.3d file since the fuzzer
#   only feeds one file. The importer will fail at opening _a.3d, but the
#   _d.3d parsing code is what we want to cover.
#
#   Actually, looking more carefully: the Unreal fuzzer feeds the file to
#   ReadFileFromMemory which creates a MemoryIOSystem. The importer then
#   tries to construct both _d.3d and _a.3d paths from the filename and
#   open them. With a single memory blob, it won't be able to open _a.3d.
#   The _d.3d file parsing happens first though, so let's maximize coverage
#   of _d.3d parsing. The crash will happen at "Unable to open _a file".
#
#   For the fuzzer to get past the _a.3d open, both files need to be
#   available. Since fuzzers typically feed a single file, we focus on
#   making _d.3d as complete as possible.
###############################################################################

def generate_unreal_d_3d(out_dir):
    """Generate a minimal _d.3d data file with 1 triangle and 3 vertices."""
    os.makedirs(out_dir, exist_ok=True)

    numTris = 1
    numVert = 3

    data = bytearray()
    # Header: numTris, numVert
    data += struct.pack('<HH', numTris, numVert)
    # 44 bytes of padding (skipped by d_reader.IncPtr(44))
    data += b'\x00' * 44

    # One triangle (16 bytes):
    #   3x uint16 vertex indices
    data += struct.pack('<HHH', 0, 1, 2)
    #   int8 type (0 = MF_NORMAL_OS)
    data += struct.pack('b', 0)
    #   1 byte padding
    data += b'\x00'
    #   3x2 bytes UV coords: mTex[0]=(0,0), mTex[1]=(255,0), mTex[2]=(0,255)
    data += struct.pack('BBBBBB', 0, 0, 255, 0, 0, 255)
    #   uint8 textureNum
    data += struct.pack('B', 0)
    #   1 byte padding
    data += b'\x00'

    filepath = os.path.join(out_dir, 'seed_minimal_d.3d')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")
    return filepath


def generate_unreal_a_3d(out_dir, numVert=3):
    """Generate a minimal _a.3d animation file matching the _d.3d file."""
    os.makedirs(out_dir, exist_ok=True)

    numFrames = 1
    frameSize = numVert * 4  # each vertex is a compressed int32

    data = bytearray()
    # Header: numFrames, frameSize
    data += struct.pack('<HH', numFrames, frameSize)

    # One frame of vertices: 3 compressed vertices
    # Unreal vertex compression packs X(11 bits), Y(11 bits), Z(10 bits) into int32
    # Simple vertices at small integer coords
    for i in range(numVert):
        # Pack simple vertex: x=i*10, y=0, z=0
        # Bit layout: X is lowest 11 bits, Y is next 11 bits, Z is top 10 bits
        x = i * 10
        y = 0
        z = 0
        val = (x & 0x7FF) | ((y & 0x7FF) << 11) | ((z & 0x3FF) << 22)
        data += struct.pack('<i', val)

    filepath = os.path.join(out_dir, 'seed_minimal_a.3d')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")
    return filepath


###############################################################################
# 2. NDO (Nendo) format
#
# From NDOLoader.cpp:
#   Magic: "nendo 1.x" (9 bytes, where x can be 0, 1, or 2)
#   Check: SearchFileHeaderForToken checks for "nendo" in first 5+ bytes
#
#   Reading (Big Endian - StreamReaderBE):
#     9 bytes: magic "nendo 1.x"
#     2 bytes: flags (skipped via IncPtr(2))
#     If file_format >= 12 (version 1.2): 2 more bytes skipped
#     1 byte (uint8): number of objects
#
#     Per object:
#       1 byte (int8): active flag (0 = skip this object)
#       If active:
#         Name length: uint32 (v1.2) or uint16 (v1.0/1.1)
#         Name data + 76 bytes unknown (skipped)
#
#         Edge count: uint32 (v1.2) or uint16
#         Per edge:
#           8x uint32 (v1.2) or uint16: edge indices
#           1 byte (v1.1+): hard flag
#           8x uint8: color
#
#         Face count: uint32 (v1.2) or uint16
#         Per face:
#           uint32 (v1.2) or uint16: elem
#
#         Vertex count: uint32 (v1.2) or uint16
#         Per vertex:
#           uint32 (v1.2) or uint16: num
#           3x float32: x, y, z position
#
#         UV count 1: uint32 (v1.2) or uint16
#         Per UV: uint32 (v1.2) or uint16 (skipped)
#
#         UV count 2: uint32 (v1.2) or uint16
#         Per UV: uint32 (v1.2) or uint16 (skipped)
#
#         1 byte: has texture flag
#         If has texture:
#           uint16 x, uint16 y (dimensions)
#           RLE pixel data until x*y pixels read:
#             uint8 repeat, uint8 r, uint8 g, uint8 b
###############################################################################

def generate_ndo(out_dir):
    """Generate a minimal valid NDO (Nendo) file with one object containing
    a simple triangle (3 vertices, 3 edges, 2 faces)."""
    os.makedirs(out_dir, exist_ok=True)

    data = bytearray()

    # Magic: "nendo 1.2" (9 bytes)
    data += b'nendo 1.2'

    # 2 bytes flags (skipped)
    data += struct.pack('>H', 0)

    # 2 more bytes for version >= 1.2
    data += struct.pack('>H', 0)

    # Number of objects: 1
    data += struct.pack('B', 1)

    # Object 0:
    # Active flag: 1 (active)
    data += struct.pack('b', 1)

    # Name length (uint32 BE for v1.2)
    name = b'TestObj'
    data += struct.pack('>I', len(name))
    # Name data
    data += name
    # 76 bytes of unknown data (skipped)
    data += b'\x00' * 76

    # Edge table
    # We need edges that form valid face traversals.
    # Simple triangle: 3 edges connecting vertices 0-1, 1-2, 2-0
    # Each edge has 8 uint32 values: edge[0..7]
    # edge[0], edge[1] = vertex indices for each side
    # edge[2], edge[3] = face keys for each side
    # edge[4], edge[5] = next edge for each side
    # edge[6], edge[7] = presumably more connectivity
    #
    # For the face traversal in ProcessFaceEdgesAndVertices:
    #   if key == edge[3]: next_edge = edge[5], next_vert = edge[1]
    #   else:              next_edge = edge[4], next_vert = edge[0]
    #
    # Let's create 3 edges for a triangle with 2 faces (front/back):
    # Face 0 (key=0): edges 0->1->2->0
    # Face 1 (key=1): edges 0->2->1->0

    num_edges = 3
    data += struct.pack('>I', num_edges)

    # Edge 0: connects verts 0,1; faces 0,1; next edges for face 0: edge1, for face 1: edge2
    # edge[0]=vert0(0), edge[1]=vert1(1), edge[2]=face_key_A(0), edge[3]=face_key_B(1),
    # edge[4]=next_edge_for_A(1), edge[5]=next_edge_for_B(2), edge[6]=0, edge[7]=0
    edges = [
        # Edge 0: verts 0,1; faces 0,1
        (0, 1, 0, 1, 1, 2, 0, 0),
        # Edge 1: verts 1,2; faces 0,1
        (1, 2, 0, 1, 2, 0, 0, 0),
        # Edge 2: verts 2,0; faces 0,1
        (2, 0, 0, 1, 0, 1, 0, 0),
    ]

    for edge in edges:
        for val in edge:
            data += struct.pack('>I', val)
        # hard flag (1 byte, version >= 1.1)
        data += struct.pack('B', 0)
        # 8x uint8 color
        data += b'\xff' * 8

    # Face table
    # Each face stores an edge index (face.elem = starting edge for traversal)
    # face_table maps edge[2] and edge[3] to edge indices
    # Face 0 uses key=0, Face 1 uses key=1
    num_faces = 2
    data += struct.pack('>I', num_faces)
    data += struct.pack('>I', 0)  # Face 0: elem = edge 0
    data += struct.pack('>I', 0)  # Face 1: elem = edge 0

    # Vertex table
    num_verts = 3
    data += struct.pack('>I', num_verts)

    # Vertex 0: (0, 0, 0)
    data += struct.pack('>I', 0)  # num
    data += struct.pack('>fff', 0.0, 0.0, 0.0)

    # Vertex 1: (1, 0, 0)
    data += struct.pack('>I', 1)  # num
    data += struct.pack('>fff', 1.0, 0.0, 0.0)

    # Vertex 2: (0, 1, 0)
    data += struct.pack('>I', 2)  # num
    data += struct.pack('>fff', 0.0, 1.0, 0.0)

    # UV count 1: 0
    data += struct.pack('>I', 0)

    # UV count 2: 0
    data += struct.pack('>I', 0)

    # Has texture: 0 (no texture)
    data += struct.pack('B', 0)

    filepath = os.path.join(out_dir, 'seed_minimal.ndo')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")
    return filepath


###############################################################################
# 3. Q3BSP (.pk3 file = ZIP containing a .bsp at maps/xxx.bsp)
#
# From Q3BSPFileParser.cpp and Q3BSPFileData.h:
#
#   BSP header (sQ3BSPHeader):
#     char strID[4] = "IBSP"
#     int32 iVersion = 46
#
#   Then 17 lumps (kMaxLumps = 17), each sQ3BSPLump:
#     int32 iOffset
#     int32 iSize
#
#   Lump indices (eLumps):
#     0  = kEntities
#     1  = kTextures
#     2  = kPlanes
#     3  = kNodes
#     4  = kLeafs
#     5  = kLeafFaces
#     6  = kLeafBrushes
#     7  = kModels
#     8  = kBrushes
#     9  = kBrushSides
#     10 = kVertices
#     11 = kMeshVerts
#     12 = kShaders
#     13 = kFaces
#     14 = kLightmaps
#     15 = kLightVolumes
#     16 = kVisData
#
#   sQ3BSPVertex (44 bytes):
#     vec3f vPosition (12)
#     vec2f vTexCoord (8)
#     vec2f vLightmap (8)
#     vec3f vNormal (12)
#     uint8 bColor[4] (4)
#
#   sQ3BSPFace (104 bytes):
#     int iTextureID, iEffect, iType
#     int iVertexIndex, iNumOfVerts
#     int iFaceVertexIndex, iNumOfFaceVerts
#     int iLightmapID
#     int iLMapCorner[2], iLMapSize[2]
#     vec3f vLMapPos
#     vec3f vLMapVecs[2]
#     vec3f vNormal
#     int patchWidth, patchHeight
#
#   sQ3BSPTexture (72 bytes):
#     char strName[64]
#     int iFlags
#     int iContents
#
#   The importer:
#     1. Opens .pk3 as ZipArchiveIOSystem
#     2. Looks for .bsp files inside under "maps/" directory
#     3. Reads the BSP, validates "IBSP" magic
#     4. Reads all lumps, then parses vertices, indices, faces, textures, lightmaps, entities
###############################################################################

def generate_q3bsp(out_dir):
    """Generate a minimal .pk3 (ZIP) file containing a valid Q3 BSP with
    one textured triangle face."""
    os.makedirs(out_dir, exist_ok=True)

    # Build BSP binary data
    bsp = bytearray()

    # Header: "IBSP" + version 46
    bsp += b'IBSP'
    bsp += struct.pack('<i', 46)

    # We need to calculate offsets for each lump.
    # Header = 8 bytes
    # 17 lumps * 8 bytes each = 136 bytes
    # Total header area = 8 + 136 = 144 bytes
    header_size = 8 + 17 * 8

    # Lump data we'll create:
    # - kEntities (0): empty string
    # - kTextures (1): 1 texture entry (72 bytes)
    # - kVertices (10): 3 vertices (3 * 44 = 132 bytes)
    # - kMeshVerts (11): 3 indices (3 * 4 = 12 bytes)
    # - kFaces (13): 1 face (104 bytes)
    # - All others: empty (offset=0, size=0)

    # Entity data: a minimal entity string
    entity_data = b'{ "classname" "worldspawn" }\x00'

    # Texture data (sQ3BSPTexture = 72 bytes)
    tex_name = b'textures/base/test'
    tex_data = tex_name + b'\x00' * (64 - len(tex_name))  # pad name to 64
    tex_data += struct.pack('<ii', 0, 0)  # iFlags, iContents

    # Vertex data (sQ3BSPVertex = 44 bytes each)
    # 3 vertices forming a triangle
    def make_vertex(px, py, pz, u, v, nx, ny, nz):
        vert = struct.pack('<fff', px, py, pz)     # vPosition (12)
        vert += struct.pack('<ff', u, v)            # vTexCoord (8)
        vert += struct.pack('<ff', 0.0, 0.0)        # vLightmap (8)
        vert += struct.pack('<fff', nx, ny, nz)     # vNormal (12)
        vert += struct.pack('BBBB', 255, 255, 255, 255)  # bColor (4)
        return vert

    vert_data = bytearray()
    vert_data += make_vertex(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    vert_data += make_vertex(64.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    vert_data += make_vertex(0.0, 64.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0)

    # MeshVerts (indices): 3 int32 indices (relative to face's iVertexIndex)
    meshvert_data = struct.pack('<iii', 0, 1, 2)

    # Face data (sQ3BSPFace = 104 bytes)
    # iType=1 (Polygon) to trigger createTriangleTopology
    face_data = struct.pack('<i', 0)         # iTextureID = 0
    face_data += struct.pack('<i', -1)       # iEffect = -1
    face_data += struct.pack('<i', 1)        # iType = 1 (Polygon)
    face_data += struct.pack('<i', 0)        # iVertexIndex = 0
    face_data += struct.pack('<i', 3)        # iNumOfVerts = 3
    face_data += struct.pack('<i', 0)        # iFaceVertexIndex = 0
    face_data += struct.pack('<i', 3)        # iNumOfFaceVerts = 3
    face_data += struct.pack('<i', -1)       # iLightmapID = -1
    face_data += struct.pack('<ii', 0, 0)    # iLMapCorner[2]
    face_data += struct.pack('<ii', 0, 0)    # iLMapSize[2]
    face_data += struct.pack('<fff', 0, 0, 0)  # vLMapPos
    face_data += struct.pack('<fff', 1, 0, 0)  # vLMapVecs[0]
    face_data += struct.pack('<fff', 0, 1, 0)  # vLMapVecs[1]
    face_data += struct.pack('<fff', 0, 0, 1)  # vNormal
    face_data += struct.pack('<ii', 0, 0)    # patchWidth, patchHeight

    assert len(face_data) == 104, f"Face data is {len(face_data)} bytes, expected 104"

    # Calculate offsets
    offset = header_size

    # Lump 0: Entities
    entity_offset = offset
    entity_size = len(entity_data)
    offset += entity_size

    # Lump 1: Textures
    tex_offset = offset
    tex_size = len(tex_data)
    offset += tex_size

    # Lumps 2-9: empty
    # Lump 10: Vertices
    vert_offset = offset
    vert_size = len(vert_data)
    offset += vert_size

    # Lump 11: MeshVerts
    meshvert_offset = offset
    meshvert_size = len(meshvert_data)
    offset += meshvert_size

    # Lump 12: Shaders (empty)

    # Lump 13: Faces
    face_offset = offset
    face_size = len(face_data)
    offset += face_size

    # Lumps 14-16: empty

    # Build lump directory (17 entries)
    lumps = []
    for i in range(17):
        lumps.append((0, 0))  # default: offset=0, size=0

    lumps[0] = (entity_offset, entity_size)    # kEntities
    lumps[1] = (tex_offset, tex_size)          # kTextures
    lumps[10] = (vert_offset, vert_size)       # kVertices
    lumps[11] = (meshvert_offset, meshvert_size)  # kMeshVerts
    lumps[13] = (face_offset, face_size)       # kFaces

    # Now assemble the BSP
    bsp_data = bytearray()
    # Header
    bsp_data += b'IBSP'
    bsp_data += struct.pack('<i', 46)

    # Lump directory
    for lump_offset, lump_size in lumps:
        bsp_data += struct.pack('<ii', lump_offset, lump_size)

    # Lump data (must match offsets calculated above)
    assert len(bsp_data) == header_size, f"Header is {len(bsp_data)}, expected {header_size}"

    bsp_data += entity_data
    bsp_data += tex_data
    bsp_data += vert_data
    bsp_data += meshvert_data
    bsp_data += face_data

    # Create .pk3 (ZIP file) containing the BSP at maps/test.bsp
    pk3_path = os.path.join(out_dir, 'seed_minimal.pk3')
    with zipfile.ZipFile(pk3_path, 'w', zipfile.ZIP_STORED) as zf:
        zf.writestr('maps/test.bsp', bytes(bsp_data))

    pk3_size = os.path.getsize(pk3_path)
    print(f"  Created {pk3_path} ({pk3_size} bytes, BSP inside: {len(bsp_data)} bytes)")
    return pk3_path


###############################################################################
# Main
###############################################################################

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("=== Generating Unreal 3D seeds ===")
    unreal_dir = os.path.join(base, 'test', 'models', '3D', 'fuzz_seeds')
    generate_unreal_d_3d(unreal_dir)
    generate_unreal_a_3d(unreal_dir)

    print("\n=== Generating NDO seeds ===")
    ndo_dir = os.path.join(base, 'test', 'models', 'NDO', 'fuzz_seeds')
    generate_ndo(ndo_dir)

    print("\n=== Generating Q3BSP seeds ===")
    q3bsp_dir = os.path.join(base, 'test', 'models', 'Q3BSP', 'fuzz_seeds')
    generate_q3bsp(q3bsp_dir)

    print("\n=== Done! ===")


if __name__ == '__main__':
    main()
