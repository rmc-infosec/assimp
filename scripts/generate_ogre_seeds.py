#!/usr/bin/env python3
"""Generate Ogre .mesh.xml and .skeleton.xml seeds for fuzzing coverage."""
import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test', 'models', 'Ogre', 'fuzz_seeds')

def write_seed(name, content):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, name)
    if isinstance(content, bytes):
        with open(path, 'wb') as f:
            f.write(content)
    else:
        with open(path, 'w') as f:
            f.write(content)
    print(f"  {name}: {len(content)} bytes")

def seed_mesh_xml_tangents():
    """Mesh with tangent vectors and multiple UV channels."""
    return """<?xml version="1.0" encoding="utf-8"?>
<mesh>
  <submeshes>
    <submesh material="TangentMat" usesharedvertices="false" operationtype="triangle_list">
      <faces count="1">
        <face v1="0" v2="1" v3="2"/>
      </faces>
      <geometry vertexcount="3">
        <vertexbuffer positions="true" normals="true" tangents="true" texture_coords="2">
          <vertex>
            <position x="0" y="0" z="0"/>
            <normal x="0" y="1" z="0"/>
            <tangent x="1" y="0" z="0"/>
            <texcoord u="0" v="0"/>
            <texcoord u="0.5" v="0.5"/>
          </vertex>
          <vertex>
            <position x="1" y="0" z="0"/>
            <normal x="0" y="1" z="0"/>
            <tangent x="1" y="0" z="0"/>
            <texcoord u="1" v="0"/>
            <texcoord u="1.0" v="0.5"/>
          </vertex>
          <vertex>
            <position x="0" y="0" z="1"/>
            <normal x="0" y="1" z="0"/>
            <tangent x="1" y="0" z="0"/>
            <texcoord u="0" v="1"/>
            <texcoord u="0.5" v="1.0"/>
          </vertex>
        </vertexbuffer>
      </geometry>
    </submesh>
  </submeshes>
</mesh>"""

def seed_mesh_xml_skeleton_and_boneassign():
    """Mesh with skeleton link and submesh-level bone assignments."""
    return """<?xml version="1.0" encoding="utf-8"?>
<mesh>
  <skeletonlink name="skeleton_test.skeleton.xml"/>
  <submeshes>
    <submesh material="SkinMat" usesharedvertices="false" operationtype="triangle_list">
      <faces count="2">
        <face v1="0" v2="1" v3="2"/>
        <face v1="2" v2="3" v3="0"/>
      </faces>
      <geometry vertexcount="4">
        <vertexbuffer positions="true" normals="true">
          <vertex><position x="0" y="0" z="0"/><normal x="0" y="1" z="0"/></vertex>
          <vertex><position x="1" y="0" z="0"/><normal x="0" y="1" z="0"/></vertex>
          <vertex><position x="1" y="1" z="0"/><normal x="0" y="1" z="0"/></vertex>
          <vertex><position x="0" y="1" z="0"/><normal x="0" y="1" z="0"/></vertex>
        </vertexbuffer>
      </geometry>
      <boneassignments>
        <vertexboneassignment vertexindex="0" boneindex="0" weight="1.0"/>
        <vertexboneassignment vertexindex="1" boneindex="0" weight="0.5"/>
        <vertexboneassignment vertexindex="1" boneindex="1" weight="0.5"/>
        <vertexboneassignment vertexindex="2" boneindex="1" weight="1.0"/>
        <vertexboneassignment vertexindex="3" boneindex="0" weight="0.7"/>
        <vertexboneassignment vertexindex="3" boneindex="1" weight="0.3"/>
      </boneassignments>
    </submesh>
  </submeshes>
</mesh>"""

def seed_skeleton_xml_with_scale():
    """Skeleton with bone scale (both factor and per-axis forms) and animations."""
    return """<?xml version="1.0" encoding="utf-8"?>
<skeleton>
  <bones>
    <bone id="0" name="Root">
      <position x="0" y="0" z="0"/>
      <rotation angle="0">
        <axis x="1" y="0" z="0"/>
      </rotation>
      <scale factor="1.0"/>
    </bone>
    <bone id="1" name="Child1">
      <position x="0" y="1" z="0"/>
      <rotation angle="0.5">
        <axis x="0" y="0" z="1"/>
      </rotation>
      <scale x="1" y="2" z="1"/>
    </bone>
    <bone id="2" name="Child2">
      <position x="0" y="2" z="0"/>
      <rotation angle="0">
        <axis x="1" y="0" z="0"/>
      </rotation>
      <scale factor="0.5"/>
    </bone>
  </bones>
  <bonehierarchy>
    <boneparent bone="Child1" parent="Root"/>
    <boneparent bone="Child2" parent="Child1"/>
  </bonehierarchy>
  <animations>
    <animation name="Walk" length="1.0">
      <tracks>
        <track bone="Root">
          <keyframes>
            <keyframe time="0">
              <translate x="0" y="0" z="0"/>
              <rotate angle="0"><axis x="0" y="0" z="1"/></rotate>
              <scale x="1" y="1" z="1"/>
            </keyframe>
            <keyframe time="0.5">
              <translate x="0" y="0.5" z="0"/>
              <rotate angle="0.3"><axis x="0" y="1" z="0"/></rotate>
              <scale x="1.1" y="1.1" z="1.1"/>
            </keyframe>
            <keyframe time="1.0">
              <translate x="0" y="0" z="0"/>
              <rotate angle="0"><axis x="0" y="0" z="1"/></rotate>
              <scale x="1" y="1" z="1"/>
            </keyframe>
          </keyframes>
        </track>
        <track bone="Child1">
          <keyframes>
            <keyframe time="0">
              <translate x="0" y="0" z="0"/>
              <rotate angle="0"><axis x="1" y="0" z="0"/></rotate>
            </keyframe>
            <keyframe time="0.5">
              <translate x="0" y="0" z="0"/>
              <rotate angle="1.2"><axis x="1" y="0" z="0"/></rotate>
            </keyframe>
            <keyframe time="1.0">
              <translate x="0" y="0" z="0"/>
              <rotate angle="0"><axis x="1" y="0" z="0"/></rotate>
            </keyframe>
          </keyframes>
        </track>
      </tracks>
    </animation>
  </animations>
</skeleton>"""

def seed_mesh_xml_shared_geometry():
    """Mesh using shared geometry with multiple submeshes."""
    return """<?xml version="1.0" encoding="utf-8"?>
<mesh>
  <sharedgeometry vertexcount="6">
    <vertexbuffer positions="true" normals="true" colours_diffuse="true" texture_coords="1">
      <vertex>
        <position x="0" y="0" z="0"/><normal x="0" y="1" z="0"/>
        <colour_diffuse value="1.0 0.0 0.0 1.0"/><texcoord u="0" v="0"/>
      </vertex>
      <vertex>
        <position x="1" y="0" z="0"/><normal x="0" y="1" z="0"/>
        <colour_diffuse value="0.0 1.0 0.0 1.0"/><texcoord u="1" v="0"/>
      </vertex>
      <vertex>
        <position x="0.5" y="0" z="1"/><normal x="0" y="1" z="0"/>
        <colour_diffuse value="0.0 0.0 1.0 1.0"/><texcoord u="0.5" v="1"/>
      </vertex>
      <vertex>
        <position x="2" y="0" z="0"/><normal x="0" y="1" z="0"/>
        <colour_diffuse value="1.0 1.0 0.0 1.0"/><texcoord u="0" v="0"/>
      </vertex>
      <vertex>
        <position x="3" y="0" z="0"/><normal x="0" y="1" z="0"/>
        <colour_diffuse value="0.0 1.0 1.0 1.0"/><texcoord u="1" v="0"/>
      </vertex>
      <vertex>
        <position x="2.5" y="0" z="1"/><normal x="0" y="1" z="0"/>
        <colour_diffuse value="1.0 0.0 1.0 1.0"/><texcoord u="0.5" v="1"/>
      </vertex>
    </vertexbuffer>
  </sharedgeometry>
  <submeshes>
    <submesh material="Mat1" usesharedvertices="true" operationtype="triangle_list">
      <faces count="1"><face v1="0" v2="1" v3="2"/></faces>
    </submesh>
    <submesh material="Mat2" usesharedvertices="true" operationtype="triangle_list">
      <faces count="1"><face v1="3" v2="4" v3="5"/></faces>
    </submesh>
  </submeshes>
  <submeshnames>
    <submeshname name="TriangleA" index="0"/>
    <submeshname name="TriangleB" index="1"/>
  </submeshnames>
</mesh>"""

# ========== BINARY OGRE .mesh SEEDS ==========

# Ogre binary chunk IDs
M_HEADER = 0x1000
M_MESH = 0x3000
M_SUBMESH = 0x4000
M_SUBMESH_OPERATION = 0x4010
M_SUBMESH_BONE_ASSIGNMENT = 0x4100
M_SUBMESH_TEXTURE_ALIAS = 0x4200
M_GEOMETRY = 0x5000
M_GEOMETRY_VERTEX_DECLARATION = 0x5100
M_GEOMETRY_VERTEX_ELEMENT = 0x5110
M_GEOMETRY_VERTEX_BUFFER = 0x5200
M_GEOMETRY_VERTEX_BUFFER_DATA = 0x5210
M_MESH_SKELETON_LINK = 0x6000
M_MESH_BONE_ASSIGNMENT = 0x7000
M_MESH_LOD = 0x8000
M_MESH_LOD_USAGE = 0x8100
M_MESH_LOD_MANUAL = 0x8110
M_MESH_LOD_GENERATED = 0x8120
M_MESH_BOUNDS = 0x9000
M_SUBMESH_NAME_TABLE = 0xA000
M_SUBMESH_NAME_TABLE_ELEMENT = 0xA100
M_EDGE_LISTS = 0xB000
M_EDGE_LIST_LOD = 0xB100
M_EDGE_GROUP = 0xB110
M_POSES = 0xC000
M_POSE = 0xC100
M_POSE_VERTEX = 0xC111
M_ANIMATIONS = 0xD000
M_ANIMATION = 0xD100
M_ANIMATION_BASEINFO = 0xD105
M_ANIMATION_TRACK = 0xD110
M_ANIMATION_MORPH_KEYFRAME = 0xD111
M_ANIMATION_POSE_KEYFRAME = 0xD112
M_ANIMATION_POSE_REF = 0xD113

# Vertex element semantic
VES_POSITION = 1
VES_NORMAL = 4
VES_TEXTURE_COORDINATES = 7

# Vertex element type
VET_FLOAT3 = 2  # 3 floats
VET_FLOAT2 = 1  # 2 floats

def write_chunk(chunk_id, data):
    """Write an Ogre binary chunk: uint16 ID + uint32 length (incl header)."""
    header = struct.pack('<HI', chunk_id, len(data) + 6)
    return header + data

def write_string(s):
    """Write null-terminated string."""
    return s.encode('utf-8') + b'\x00'

def seed_binary_mesh_with_lod():
    """Binary .mesh with LOD levels."""
    # Geometry: 3 vertices (position only)
    vdecl = write_chunk(M_GEOMETRY_VERTEX_ELEMENT,
        struct.pack('<HHHHH', 0, VET_FLOAT3, VES_POSITION, 0, 0))

    vbuf_data = write_chunk(M_GEOMETRY_VERTEX_BUFFER_DATA,
        struct.pack('<9f',
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0))

    vbuf = write_chunk(M_GEOMETRY_VERTEX_BUFFER,
        struct.pack('<HH', 0, 12) + vbuf_data)

    geom = write_chunk(M_GEOMETRY,
        struct.pack('<I', 3) +
        write_chunk(M_GEOMETRY_VERTEX_DECLARATION, vdecl) +
        vbuf)

    # Submesh with 1 triangle, 32-bit indices, not shared
    submesh_data = (
        write_string("Material1") +
        struct.pack('<?', False) +  # useSharedVertices
        struct.pack('<I', 1) +  # indexCount = 3 vertices
        struct.pack('<?', True) +  # indexes32Bit
        struct.pack('<3I', 0, 1, 2) +  # indices
        geom
    )
    submesh = write_chunk(M_SUBMESH, submesh_data)

    # LOD: 2 levels
    lod_data = (
        write_string("manual_lod") +  # strategy name
        struct.pack('<H', 2) +  # numLevels
        # LOD usage 1 (manual)
        write_chunk(M_MESH_LOD_USAGE,
            struct.pack('<f', 10.0) +  # LOD value
            write_chunk(M_MESH_LOD_MANUAL, write_string("lod1.mesh")))
    )
    lod = write_chunk(M_MESH_LOD, lod_data)

    # Submesh name table
    name_table = write_chunk(M_SUBMESH_NAME_TABLE,
        write_chunk(M_SUBMESH_NAME_TABLE_ELEMENT,
            struct.pack('<H', 0) + write_string("MainMesh")))

    # Mesh bounds
    bounds = write_chunk(M_MESH_BOUNDS,
        struct.pack('<7f', 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.5))

    mesh = write_chunk(M_MESH,
        struct.pack('<?', False) +  # skelAnimated
        submesh + lod + name_table + bounds)

    header = write_chunk(M_HEADER, write_string("[MeshSerializer_v1.100]"))
    return header + mesh

def seed_binary_mesh_with_poses():
    """Binary .mesh with poses and pose animation."""
    # Simple geometry
    vdecl = write_chunk(M_GEOMETRY_VERTEX_ELEMENT,
        struct.pack('<HHHHH', 0, VET_FLOAT3, VES_POSITION, 0, 0))

    vbuf_data = write_chunk(M_GEOMETRY_VERTEX_BUFFER_DATA,
        struct.pack('<9f', 0,0,0, 1,0,0, 0,1,0))
    vbuf = write_chunk(M_GEOMETRY_VERTEX_BUFFER,
        struct.pack('<HH', 0, 12) + vbuf_data)
    geom = write_chunk(M_GEOMETRY,
        struct.pack('<I', 3) +
        write_chunk(M_GEOMETRY_VERTEX_DECLARATION, vdecl) + vbuf)

    submesh = write_chunk(M_SUBMESH,
        write_string("PoseMat") +
        struct.pack('<?', False) +
        struct.pack('<I', 1) +
        struct.pack('<?', False) +  # 16-bit indices
        struct.pack('<3H', 0, 1, 2) +
        geom)

    # Poses: 2 poses with vertex offsets
    pose1_verts = (
        write_chunk(M_POSE_VERTEX, struct.pack('<I3f', 0, 0.1, 0.2, 0.0)) +
        write_chunk(M_POSE_VERTEX, struct.pack('<I3f', 1, -0.1, 0.3, 0.0)) +
        write_chunk(M_POSE_VERTEX, struct.pack('<I3f', 2, 0.0, 0.0, 0.5))
    )
    pose1 = write_chunk(M_POSE,
        write_string("Smile") +
        struct.pack('<H?', 0, False) +  # target=0, includesNormals=false
        pose1_verts)

    pose2_verts = (
        write_chunk(M_POSE_VERTEX, struct.pack('<I3f', 0, -0.2, 0.0, 0.1)) +
        write_chunk(M_POSE_VERTEX, struct.pack('<I3f', 2, 0.3, -0.1, 0.0))
    )
    pose2 = write_chunk(M_POSE,
        write_string("Frown") +
        struct.pack('<H?', 0, False) +
        pose2_verts)

    poses = write_chunk(M_POSES, pose1 + pose2)

    # Animation with pose keyframes
    pose_ref1 = write_chunk(M_ANIMATION_POSE_REF,
        struct.pack('<Hf', 0, 1.0))  # pose index 0, influence 1.0
    pose_ref2 = write_chunk(M_ANIMATION_POSE_REF,
        struct.pack('<Hf', 1, 0.5))  # pose index 1, influence 0.5

    keyframe0 = write_chunk(M_ANIMATION_POSE_KEYFRAME,
        struct.pack('<f', 0.0) + pose_ref1)
    keyframe1 = write_chunk(M_ANIMATION_POSE_KEYFRAME,
        struct.pack('<f', 1.0) + pose_ref2)

    track = write_chunk(M_ANIMATION_TRACK,
        struct.pack('<H', 0) +  # target submesh
        keyframe0 + keyframe1)

    anim = write_chunk(M_ANIMATION,
        write_string("FacialAnim") +
        struct.pack('<f', 1.0) +  # length
        track)

    animations = write_chunk(M_ANIMATIONS, anim)

    mesh = write_chunk(M_MESH,
        struct.pack('<?', False) + submesh + poses + animations)

    header = write_chunk(M_HEADER, write_string("[MeshSerializer_v1.100]"))
    return header + mesh

def seed_binary_mesh_with_morph():
    """Binary .mesh with morph animation keyframes."""
    vdecl = write_chunk(M_GEOMETRY_VERTEX_ELEMENT,
        struct.pack('<HHHHH', 0, VET_FLOAT3, VES_POSITION, 0, 0))

    vbuf_data = write_chunk(M_GEOMETRY_VERTEX_BUFFER_DATA,
        struct.pack('<9f', 0,0,0, 1,0,0, 0,1,0))
    vbuf = write_chunk(M_GEOMETRY_VERTEX_BUFFER,
        struct.pack('<HH', 0, 12) + vbuf_data)
    geom = write_chunk(M_GEOMETRY,
        struct.pack('<I', 3) +
        write_chunk(M_GEOMETRY_VERTEX_DECLARATION, vdecl) + vbuf)

    submesh = write_chunk(M_SUBMESH,
        write_string("MorphMat") +
        struct.pack('<?', False) +
        struct.pack('<I', 1) +
        struct.pack('<?', False) +
        struct.pack('<3H', 0, 1, 2) +
        geom)

    # Morph keyframes: 3 vertices * 3 floats = 9 floats per keyframe
    morph_kf0 = write_chunk(M_ANIMATION_MORPH_KEYFRAME,
        struct.pack('<f?', 0.0, False) +  # time, includesNormals
        struct.pack('<9f', 0,0,0, 1,0,0, 0,1,0))
    morph_kf1 = write_chunk(M_ANIMATION_MORPH_KEYFRAME,
        struct.pack('<f?', 1.0, False) +
        struct.pack('<9f', 0,0.5,0, 1,0.5,0, 0,1.5,0))

    track = write_chunk(M_ANIMATION_TRACK,
        struct.pack('<H', 0) + morph_kf0 + morph_kf1)

    anim = write_chunk(M_ANIMATION,
        write_string("MorphWiggle") +
        struct.pack('<f', 1.0) +
        track)

    animations = write_chunk(M_ANIMATIONS, anim)

    mesh = write_chunk(M_MESH,
        struct.pack('<?', False) + submesh + animations)

    header = write_chunk(M_HEADER, write_string("[MeshSerializer_v1.100]"))
    return header + mesh

def seed_binary_mesh_with_edges():
    """Binary .mesh with edge lists."""
    vdecl = write_chunk(M_GEOMETRY_VERTEX_ELEMENT,
        struct.pack('<HHHHH', 0, VET_FLOAT3, VES_POSITION, 0, 0))

    vbuf_data = write_chunk(M_GEOMETRY_VERTEX_BUFFER_DATA,
        struct.pack('<12f', 0,0,0, 1,0,0, 0,1,0, 0,0,1))
    vbuf = write_chunk(M_GEOMETRY_VERTEX_BUFFER,
        struct.pack('<HH', 0, 12) + vbuf_data)
    geom = write_chunk(M_GEOMETRY,
        struct.pack('<I', 4) +
        write_chunk(M_GEOMETRY_VERTEX_DECLARATION, vdecl) + vbuf)

    submesh = write_chunk(M_SUBMESH,
        write_string("EdgeMat") +
        struct.pack('<?', False) +
        struct.pack('<I', 2) +  # 2 triangles = 6 indices
        struct.pack('<?', False) +
        struct.pack('<6H', 0,1,2, 0,2,3) +
        geom)

    # Submesh operation (triangle_strip = 4)
    sub_op = write_chunk(M_SUBMESH_OPERATION, struct.pack('<H', 4))

    # Edge list LOD with one edge group
    edge_group = write_chunk(M_EDGE_GROUP,
        struct.pack('<III', 0, 4, 3) +  # vertexSet, triStart, triCount
        struct.pack('<III', 3, 0, 0))   # edgeCount, vertexStart, vertexData (placeholder)

    edge_lod = write_chunk(M_EDGE_LIST_LOD,
        struct.pack('<H?', 0, False) +  # LOD index, isManual
        struct.pack('<I', 2) +  # numTriangles
        struct.pack('<I', 3) +  # numEdgeGroups
        edge_group)

    edge_lists = write_chunk(M_EDGE_LISTS, edge_lod)

    mesh = write_chunk(M_MESH,
        struct.pack('<?', False) + submesh + edge_lists)

    header = write_chunk(M_HEADER, write_string("[MeshSerializer_v1.100]"))
    return header + mesh

def seed_binary_mesh_with_skeleton():
    """Binary .mesh with skeleton link and bone assignments."""
    vdecl = write_chunk(M_GEOMETRY_VERTEX_ELEMENT,
        struct.pack('<HHHHH', 0, VET_FLOAT3, VES_POSITION, 0, 0))

    vbuf_data = write_chunk(M_GEOMETRY_VERTEX_BUFFER_DATA,
        struct.pack('<12f', 0,0,0, 1,0,0, 0,1,0, 1,1,0))
    vbuf = write_chunk(M_GEOMETRY_VERTEX_BUFFER,
        struct.pack('<HH', 0, 12) + vbuf_data)
    geom = write_chunk(M_GEOMETRY,
        struct.pack('<I', 4) +
        write_chunk(M_GEOMETRY_VERTEX_DECLARATION, vdecl) + vbuf)

    submesh = write_chunk(M_SUBMESH,
        write_string("SkelMat") +
        struct.pack('<?', False) +
        struct.pack('<I', 2) +
        struct.pack('<?', False) +
        struct.pack('<6H', 0,1,2, 2,3,0) +
        geom +
        # Submesh bone assignments
        write_chunk(M_SUBMESH_BONE_ASSIGNMENT,
            struct.pack('<IHf', 0, 0, 1.0)) +
        write_chunk(M_SUBMESH_BONE_ASSIGNMENT,
            struct.pack('<IHf', 1, 0, 0.5)) +
        write_chunk(M_SUBMESH_BONE_ASSIGNMENT,
            struct.pack('<IHf', 1, 1, 0.5)) +
        write_chunk(M_SUBMESH_BONE_ASSIGNMENT,
            struct.pack('<IHf', 2, 1, 1.0)) +
        # Texture alias
        write_chunk(M_SUBMESH_TEXTURE_ALIAS,
            write_string("diffuse_tex") + write_string("actual_texture.png"))
    )

    skel_link = write_chunk(M_MESH_SKELETON_LINK,
        write_string("skeleton_test.skeleton"))

    # Mesh-level bone assignments too
    mesh_bone1 = write_chunk(M_MESH_BONE_ASSIGNMENT,
        struct.pack('<IHf', 3, 1, 0.7))
    mesh_bone2 = write_chunk(M_MESH_BONE_ASSIGNMENT,
        struct.pack('<IHf', 3, 0, 0.3))

    mesh = write_chunk(M_MESH,
        struct.pack('<?', True) +  # skelAnimated
        submesh + skel_link + mesh_bone1 + mesh_bone2)

    header = write_chunk(M_HEADER, write_string("[MeshSerializer_v1.100]"))
    return header + mesh

def seed_binary_mesh_with_lod_generated():
    """Binary .mesh with generated (not manual) LOD."""
    vdecl = write_chunk(M_GEOMETRY_VERTEX_ELEMENT,
        struct.pack('<HHHHH', 0, VET_FLOAT3, VES_POSITION, 0, 0))

    vbuf_data = write_chunk(M_GEOMETRY_VERTEX_BUFFER_DATA,
        struct.pack('<9f', 0,0,0, 1,0,0, 0,1,0))
    vbuf = write_chunk(M_GEOMETRY_VERTEX_BUFFER,
        struct.pack('<HH', 0, 12) + vbuf_data)
    geom = write_chunk(M_GEOMETRY,
        struct.pack('<I', 3) +
        write_chunk(M_GEOMETRY_VERTEX_DECLARATION, vdecl) + vbuf)

    submesh = write_chunk(M_SUBMESH,
        write_string("LodGenMat") +
        struct.pack('<?', False) +
        struct.pack('<I', 1) +
        struct.pack('<?', False) +
        struct.pack('<3H', 0, 1, 2) +
        geom)

    # Generated LOD with index data
    lod_gen = write_chunk(M_MESH_LOD_GENERATED,
        struct.pack('<I', 3) +   # indexCount
        struct.pack('<?', False) +  # 16-bit indices
        struct.pack('<3H', 0, 1, 2))  # reduced indices

    lod = write_chunk(M_MESH_LOD,
        write_string("distance") +
        struct.pack('<H', 2) +  # numLevels
        write_chunk(M_MESH_LOD_USAGE,
            struct.pack('<f', 5.0) + lod_gen))

    mesh = write_chunk(M_MESH,
        struct.pack('<?', False) + submesh + lod)

    header = write_chunk(M_HEADER, write_string("[MeshSerializer_v1.100]"))
    return header + mesh

if __name__ == '__main__':
    print("Generating Ogre XML seeds:")
    write_seed('seed_tangents_multiuv.mesh.xml', seed_mesh_xml_tangents())
    write_seed('seed_skeleton_link.mesh.xml', seed_mesh_xml_skeleton_and_boneassign())
    write_seed('skeleton_test.skeleton.xml', seed_skeleton_xml_with_scale())
    write_seed('seed_shared_geometry.mesh.xml', seed_mesh_xml_shared_geometry())

    print("\nGenerating Ogre binary seeds:")
    write_seed('seed_lod.mesh', seed_binary_mesh_with_lod())
    write_seed('seed_poses.mesh', seed_binary_mesh_with_poses())
    write_seed('seed_morph.mesh', seed_binary_mesh_with_morph())
    write_seed('seed_edges.mesh', seed_binary_mesh_with_edges())
    write_seed('seed_skeleton_link.mesh', seed_binary_mesh_with_skeleton())
    write_seed('seed_lod_generated.mesh', seed_binary_mesh_with_lod_generated())

    print(f"\nDone! Seeds in {OUTPUT_DIR}")
