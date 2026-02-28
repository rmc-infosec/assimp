#!/usr/bin/env python3
"""Generate Ogre binary mesh seed files for fuzzing.

Creates seeds that exercise:
- M_POSES with hasNormals true/false
- M_ANIMATIONS with morph and pose keyframes
- M_EDGE_LISTS with edge groups
- M_MESH_LOD with generated LOD
"""

import struct
import os

# Chunk IDs (from OgreBinarySerializer.h)
M_HEADER                        = 0x1000
M_MESH                          = 0x3000
M_SUBMESH                       = 0x4000
M_SUBMESH_OPERATION             = 0x4010
M_GEOMETRY                      = 0x5000
M_GEOMETRY_VERTEX_DECLARATION   = 0x5100
M_GEOMETRY_VERTEX_ELEMENT       = 0x5110
M_GEOMETRY_VERTEX_BUFFER        = 0x5200
M_GEOMETRY_VERTEX_BUFFER_DATA   = 0x5210
M_MESH_BOUNDS                   = 0x9000
M_MESH_LOD                      = 0x8000
M_MESH_LOD_USAGE                = 0x8100
M_MESH_LOD_GENERATED            = 0x8120
M_EDGE_LISTS                    = 0xB000
M_EDGE_LIST_LOD                 = 0xB100
M_EDGE_GROUP                    = 0xB110
M_POSES                         = 0xC000
M_POSE                          = 0xC100
M_POSE_VERTEX                   = 0xC111
M_ANIMATIONS                    = 0xD000
M_ANIMATION                     = 0xD100
M_ANIMATION_BASEINFO            = 0xD105
M_ANIMATION_TRACK               = 0xD110
M_ANIMATION_MORPH_KEYFRAME      = 0xD111
M_ANIMATION_POSE_KEYFRAME       = 0xD112
M_ANIMATION_POSE_REF            = 0xD113

MSTREAM_OVERHEAD = 6  # uint16 id + uint32 length

VET_FLOAT3 = 2
VES_POSITION = 1
VES_NORMAL = 4


def write_chunk(chunk_id, data):
    length = MSTREAM_OVERHEAD + len(data)
    return struct.pack('<HI', chunk_id, length) + data


def write_string(s):
    return s.encode('ascii') + b'\n'


def write_geometry(vertices, normals=None):
    vertex_count = len(vertices) // 3
    data = struct.pack('<I', vertex_count)

    decl_data = b''
    elem = struct.pack('<HHHHH', 0, VET_FLOAT3, VES_POSITION, 0, 0)
    decl_data += write_chunk(M_GEOMETRY_VERTEX_ELEMENT, elem)

    vertex_size = 12
    if normals:
        elem = struct.pack('<HHHHH', 0, VET_FLOAT3, VES_NORMAL, 12, 0)
        decl_data += write_chunk(M_GEOMETRY_VERTEX_ELEMENT, elem)
        vertex_size = 24

    data += write_chunk(M_GEOMETRY_VERTEX_DECLARATION, decl_data)

    vbuf_data = struct.pack('<HH', 0, vertex_size)
    raw = b''
    for i in range(vertex_count):
        raw += struct.pack('<fff', vertices[i*3], vertices[i*3+1], vertices[i*3+2])
        if normals:
            raw += struct.pack('<fff', normals[i*3], normals[i*3+1], normals[i*3+2])
    vbuf_data += write_chunk(M_GEOMETRY_VERTEX_BUFFER_DATA, raw)
    data += write_chunk(M_GEOMETRY_VERTEX_BUFFER, vbuf_data)

    return write_chunk(M_GEOMETRY, data)


def write_submesh(material_name, indices, vertex_data):
    data = write_string(material_name)
    data += struct.pack('<B', 0)  # usesSharedVertexData = false
    data += struct.pack('<I', len(indices))
    data += struct.pack('<B', 0)  # indexes32Bit = false
    for idx in indices:
        data += struct.pack('<H', idx)
    data += vertex_data
    # Add operation type = OT_TRIANGLE_LIST (4)
    data += write_chunk(M_SUBMESH_OPERATION, struct.pack('<H', 4))
    return write_chunk(M_SUBMESH, data)


def write_bounds():
    data = struct.pack('<fffffff', -1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.732)
    return write_chunk(M_MESH_BOUNDS, data)


def generate_pose_anim_seed():
    vertices = [-1.0, 0.0, 0.0,  1.0, 0.0, 0.0,  0.0, 1.0, 0.0]
    normals =  [0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 0.0, 1.0]

    geom = write_geometry(vertices, normals)
    submesh = write_submesh("Material1", [0, 1, 2], geom)

    poses_data = b''

    # Pose 0: without normals (target=1 means submesh 0)
    pose0_data = write_string("Pose0")
    pose0_data += struct.pack('<H', 1)  # target = 1 (submesh index 0+1)
    pose0_data += struct.pack('<B', 0)  # hasNormals = false
    pv0 = struct.pack('<I', 0) + struct.pack('<fff', 0.0, 0.5, 0.0)
    pose0_data += write_chunk(M_POSE_VERTEX, pv0)
    pv1 = struct.pack('<I', 1) + struct.pack('<fff', 0.0, 0.3, 0.0)
    pose0_data += write_chunk(M_POSE_VERTEX, pv1)
    poses_data += write_chunk(M_POSE, pose0_data)

    # Pose 1: with normals (target=1 means submesh 0)
    pose1_data = write_string("Pose1")
    pose1_data += struct.pack('<H', 1)  # target = 1 (submesh index 0+1)
    pose1_data += struct.pack('<B', 1)  # hasNormals = true
    pv2 = struct.pack('<I', 2) + struct.pack('<fff', 0.0, -0.5, 0.0) + struct.pack('<fff', 0.0, 1.0, 0.0)
    pose1_data += write_chunk(M_POSE_VERTEX, pv2)
    poses_data += write_chunk(M_POSE, pose1_data)

    # Animations with pose keyframes + baseinfo
    anims_data = b''
    anim_data = write_string("PoseAnim")
    anim_data += struct.pack('<f', 2.0)

    baseinfo = write_string("") + struct.pack('<f', 0.0)
    anim_data += write_chunk(M_ANIMATION_BASEINFO, baseinfo)

    track_data = struct.pack('<HH', 2, 1)  # type=pose, target=1 (submesh 0)
    kf0 = struct.pack('<f', 0.0)
    kf0 += write_chunk(M_ANIMATION_POSE_REF, struct.pack('<Hf', 0, 1.0))
    kf0 += write_chunk(M_ANIMATION_POSE_REF, struct.pack('<Hf', 1, 0.5))
    track_data += write_chunk(M_ANIMATION_POSE_KEYFRAME, kf0)
    kf1 = struct.pack('<f', 1.0)
    kf1 += write_chunk(M_ANIMATION_POSE_REF, struct.pack('<Hf', 0, 0.0))
    kf1 += write_chunk(M_ANIMATION_POSE_REF, struct.pack('<Hf', 1, 1.0))
    track_data += write_chunk(M_ANIMATION_POSE_KEYFRAME, kf1)

    anim_data += write_chunk(M_ANIMATION_TRACK, track_data)
    anims_data += write_chunk(M_ANIMATION, anim_data)

    mesh_data = struct.pack('<B', 0)
    mesh_data += submesh
    mesh_data += write_bounds()
    mesh_data += write_chunk(M_POSES, poses_data)
    mesh_data += write_chunk(M_ANIMATIONS, anims_data)

    header = struct.pack('<H', M_HEADER) + write_string("[MeshSerializer_v1.8]")
    return header + write_chunk(M_MESH, mesh_data)


def generate_morph_keyframe_seed():
    vertices = [-1.0, 0.0, 0.0,  1.0, 0.0, 0.0,  0.0, 1.0, 0.0,  0.0, 0.0, 1.0]
    normals =  [0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 1.0, 0.0]

    geom = write_geometry(vertices, normals)
    submesh = write_submesh("MorphMat", [0, 1, 2, 0, 2, 3], geom)

    anims_data = b''
    anim_data = write_string("MorphAnim")
    anim_data += struct.pack('<f', 1.0)

    track_data = struct.pack('<HH', 1, 1)  # type=morph, target=1 (submesh 0)

    # Morph keyframe at t=0.0, hasNormals=false
    kf0 = struct.pack('<f', 0.0)
    kf0 += struct.pack('<B', 0)  # hasNormals = false
    for i in range(4):
        kf0 += struct.pack('<fff', vertices[i*3]+0.1, vertices[i*3+1]+0.1, vertices[i*3+2]+0.1)
    track_data += write_chunk(M_ANIMATION_MORPH_KEYFRAME, kf0)

    # Morph keyframe at t=0.5, hasNormals=true
    kf1 = struct.pack('<f', 0.5)
    kf1 += struct.pack('<B', 1)  # hasNormals = true
    for i in range(4):
        kf1 += struct.pack('<fff', vertices[i*3]+0.2, vertices[i*3+1]+0.2, vertices[i*3+2]+0.2)
        kf1 += struct.pack('<fff', 0.0, 0.0, 1.0)
    track_data += write_chunk(M_ANIMATION_MORPH_KEYFRAME, kf1)

    anim_data += write_chunk(M_ANIMATION_TRACK, track_data)
    anims_data += write_chunk(M_ANIMATION, anim_data)

    mesh_data = struct.pack('<B', 0)
    mesh_data += submesh
    mesh_data += write_bounds()
    mesh_data += write_chunk(M_ANIMATIONS, anims_data)

    header = struct.pack('<H', M_HEADER) + write_string("[MeshSerializer_v1.8]")
    return header + write_chunk(M_MESH, mesh_data)


def generate_edge_list_seed():
    vertices = [-1.0, 0.0, 0.0,  1.0, 0.0, 0.0,  0.0, 1.0, 0.0]
    normals =  [0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 0.0, 1.0]

    geom = write_geometry(vertices, normals)
    submesh = write_submesh("EdgeMat", [0, 1, 2], geom)

    edge_lists_data = b''

    # Edge list LOD 0: manual=false
    lod_data = struct.pack('<H', 0)   # lodIndex
    lod_data += struct.pack('<B', 0)  # manual = false
    lod_data += struct.pack('<B', 1)  # isClosed
    num_triangles = 1
    num_edge_groups = 1
    lod_data += struct.pack('<I', num_triangles)
    lod_data += struct.pack('<I', num_edge_groups)

    # Triangle: indexSet, vertexSet, vertIndex[3], sharedVertIndex[3], normal[4]
    lod_data += struct.pack('<II', 0, 0)
    lod_data += struct.pack('<III', 0, 1, 2)
    lod_data += struct.pack('<III', 0, 1, 2)
    lod_data += struct.pack('<ffff', 0.0, 0.0, 1.0, 0.0)

    # Edge group: vertexSet, triStart, triCount, numEdges
    eg_data = struct.pack('<III', 0, 0, 1)
    num_edges = 3
    eg_data += struct.pack('<I', num_edges)
    # Each edge: triIndex[2], vertIndex[2], sharedVertIndex[2], degenerate
    for e in range(num_edges):
        eg_data += struct.pack('<IIIIII', 0, 0, e, (e+1)%3, e, (e+1)%3)
        eg_data += struct.pack('<B', 0)

    lod_data += write_chunk(M_EDGE_GROUP, eg_data)
    edge_lists_data += write_chunk(M_EDGE_LIST_LOD, lod_data)

    mesh_data = struct.pack('<B', 0)
    mesh_data += submesh
    mesh_data += write_bounds()
    mesh_data += write_chunk(M_EDGE_LISTS, edge_lists_data)

    header = struct.pack('<H', M_HEADER) + write_string("[MeshSerializer_v1.8]")
    return header + write_chunk(M_MESH, mesh_data)


def generate_lod_generated_seed():
    vertices = [-1.0, 0.0, 0.0,  1.0, 0.0, 0.0,  0.0, 1.0, 0.0,  0.0, 0.0, 1.0]
    normals =  [0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 1.0, 0.0]

    geom = write_geometry(vertices, normals)
    submesh = write_submesh("LodMat", [0, 1, 2, 0, 2, 3], geom)

    # LOD info
    lod_data = write_string("Distance")
    lod_data += struct.pack('<H', 2)   # numLods
    lod_data += struct.pack('<B', 0)   # manual = false

    # LOD usage for level 1
    lod_usage_data = struct.pack('<f', 10.0)
    gen_data = struct.pack('<I', 3)    # indexCount = 3
    gen_data += struct.pack('<B', 0)   # is32bit = false
    gen_data += struct.pack('<HHH', 0, 1, 2)
    lod_usage_data += write_chunk(M_MESH_LOD_GENERATED, gen_data)
    lod_data += write_chunk(M_MESH_LOD_USAGE, lod_usage_data)

    mesh_data = struct.pack('<B', 0)
    mesh_data += submesh
    mesh_data += write_bounds()
    mesh_data += write_chunk(M_MESH_LOD, lod_data)

    header = struct.pack('<H', M_HEADER) + write_string("[MeshSerializer_v1.8]")
    return header + write_chunk(M_MESH, mesh_data)


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'test', 'models', 'Ogre', 'fuzz_seeds')
    os.makedirs(out_dir, exist_ok=True)

    seeds = [
        ('seed_pose_anim.mesh', generate_pose_anim_seed()),
        ('seed_morph_keyframe.mesh', generate_morph_keyframe_seed()),
        ('seed_edge_list.mesh', generate_edge_list_seed()),
        ('seed_lod_generated.mesh', generate_lod_generated_seed()),
    ]

    for name, data in seeds:
        path = os.path.join(out_dir, name)
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  Created {name}: {len(data)} bytes")


if __name__ == '__main__':
    main()
