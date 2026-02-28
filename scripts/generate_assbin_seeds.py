#!/usr/bin/env python3
"""
Generate minimal valid Assbin (Assimp Binary) seed files for fuzzing.

The Assbin format is Assimp's native binary interchange format.
See code/Common/assbin_chunks.h for the chunk magic constants.

File layout:
  - 512-byte header
  - Chunk data (scene chunk containing nested node/mesh/material chunks)

Each chunk: uint32 magic + uint32 data_length + data bytes.
All integers are little-endian.
"""

import struct
import os
import io

# ---------------------------------------------------------------------------
# Constants from assbin_chunks.h
# ---------------------------------------------------------------------------
ASSBIN_VERSION_MAJOR = 1
ASSBIN_VERSION_MINOR = 0

ASSBIN_HEADER_LENGTH = 512

ASSBIN_CHUNK_AICAMERA = 0x1234
ASSBIN_CHUNK_AILIGHT = 0x1235
ASSBIN_CHUNK_AITEXTURE = 0x1236
ASSBIN_CHUNK_AIMESH = 0x1237
ASSBIN_CHUNK_AINODEANIM = 0x1238
ASSBIN_CHUNK_AISCENE = 0x1239
ASSBIN_CHUNK_AIBONE = 0x123A
ASSBIN_CHUNK_AIANIMATION = 0x123B
ASSBIN_CHUNK_AINODE = 0x123C
ASSBIN_CHUNK_AIMATERIAL = 0x123D
ASSBIN_CHUNK_AIMATERIALPROPERTY = 0x123E

ASSBIN_MESH_HAS_POSITIONS = 0x1
ASSBIN_MESH_HAS_NORMALS = 0x2
ASSBIN_MESH_HAS_TANGENTS_AND_BITANGENTS = 0x4
ASSBIN_MESH_HAS_TEXCOORD_BASE = 0x100
ASSBIN_MESH_HAS_COLOR_BASE = 0x10000

HINTMAXTEXTURELEN = 9  # 8 chars + null terminator


def assbin_mesh_has_texcoord(n):
    return ASSBIN_MESH_HAS_TEXCOORD_BASE << n


def assbin_mesh_has_color(n):
    return ASSBIN_MESH_HAS_COLOR_BASE << n


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_header(f, shortened=0, compressed=0):
    """Write the 512-byte Assbin header."""
    # Magic string: "ASSIMP.binary-dump." padded to 44 bytes with zeros
    magic = b"ASSIMP.binary-dump.\x00"
    magic = magic.ljust(44, b"\x00")
    f.write(magic)

    # Version major, minor (uint32 each)
    f.write(struct.pack("<I", ASSBIN_VERSION_MAJOR))
    f.write(struct.pack("<I", ASSBIN_VERSION_MINOR))

    # SVN revision
    f.write(struct.pack("<I", 0))

    # Compile flags
    f.write(struct.pack("<I", 0))

    # Shortened flag (uint16), compressed flag (uint16)
    f.write(struct.pack("<H", shortened))
    f.write(struct.pack("<H", compressed))

    # Source filename: 256 bytes, zero-padded
    f.write(b"seed.assbin\x00".ljust(256, b"\x00"))

    # Command line: 128 bytes, zero-padded
    f.write(b"\x00" * 128)

    # Reserved/padding: 64 bytes (the writer fills with 0xcd)
    f.write(b"\xcd" * 64)

    assert f.tell() == ASSBIN_HEADER_LENGTH


def write_aistring(buf, s):
    """Write an aiString: uint32 length + raw bytes (no null terminator in data)."""
    encoded = s.encode("utf-8") if isinstance(s, str) else s
    buf.write(struct.pack("<I", len(encoded)))
    buf.write(encoded)


def write_matrix4x4_identity(buf):
    """Write a 4x4 identity matrix (16 floats)."""
    identity = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]
    for v in identity:
        buf.write(struct.pack("<f", v))


def write_vector3d(buf, x, y, z):
    """Write an aiVector3D (3 floats)."""
    buf.write(struct.pack("<fff", x, y, z))


def write_chunk(container, magic, data_bytes):
    """Write a chunk: uint32 magic + uint32 size + data."""
    container.write(struct.pack("<I", magic))
    container.write(struct.pack("<I", len(data_bytes)))
    container.write(data_bytes)


# ---------------------------------------------------------------------------
# Node builder
# ---------------------------------------------------------------------------

def build_node_chunk(name, num_children=0, mesh_indices=None, children_data=None):
    """
    Build a node chunk's inner data.
    The chunk wrapper (magic + size) is added by write_chunk.

    Layout (from ReadBinaryNode):
      - aiString name
      - aiMatrix4x4 transformation
      - uint32 numChildren
      - uint32 numMeshes
      - uint32 nb_metadata (0)
      - [mesh indices: uint32 each]
      - [children: nested node chunks]
    """
    buf = io.BytesIO()
    write_aistring(buf, name)
    write_matrix4x4_identity(buf)
    buf.write(struct.pack("<I", num_children))
    num_meshes = len(mesh_indices) if mesh_indices else 0
    buf.write(struct.pack("<I", num_meshes))
    buf.write(struct.pack("<I", 0))  # nb_metadata = 0

    # Mesh indices
    if mesh_indices:
        for idx in mesh_indices:
            buf.write(struct.pack("<I", idx))

    # Children (already-built chunk data including their chunk headers)
    if children_data:
        buf.write(children_data)

    return buf.getvalue()


def build_node_chunk_bytes(name, num_children=0, mesh_indices=None, children_data=None):
    """Build a complete node chunk (magic + size + data)."""
    data = build_node_chunk(name, num_children, mesh_indices, children_data)
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AINODE, data)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Mesh builder
# ---------------------------------------------------------------------------

def build_mesh_chunk(vertices, faces, material_index=0, normals=None,
                     texcoords_channels=None, primitive_types=4):
    """
    Build a mesh chunk.

    vertices: list of (x,y,z) tuples
    faces: list of lists of vertex indices
    normals: optional list of (x,y,z) tuples
    texcoords_channels: optional list of (num_components, [(u,v,w),...]) per channel
    primitive_types: bitmask (4 = triangles)

    Layout (from ReadBinaryMesh):
      - uint32 mPrimitiveTypes
      - uint32 mNumVertices
      - uint32 mNumFaces
      - uint32 mNumBones
      - uint32 mMaterialIndex
      - uint32 component_flags
      - [vertex data if has_positions]
      - [normal data if has_normals]
      - [for each texcoord channel: uint32 numUVComponents + vertex data]
      - [face data: uint16 numIndices + indices (uint16 if <65536 verts, else uint32)]
    """
    buf = io.BytesIO()
    num_vertices = len(vertices)
    num_faces = len(faces)
    num_bones = 0

    buf.write(struct.pack("<I", primitive_types))
    buf.write(struct.pack("<I", num_vertices))
    buf.write(struct.pack("<I", num_faces))
    buf.write(struct.pack("<I", num_bones))
    buf.write(struct.pack("<I", material_index))

    # Build component flags
    flags = 0
    flags |= ASSBIN_MESH_HAS_POSITIONS
    if normals:
        flags |= ASSBIN_MESH_HAS_NORMALS
    if texcoords_channels:
        for i in range(len(texcoords_channels)):
            flags |= assbin_mesh_has_texcoord(i)

    buf.write(struct.pack("<I", flags))

    # Vertex positions
    for v in vertices:
        write_vector3d(buf, v[0], v[1], v[2])

    # Normals
    if normals:
        for n in normals:
            write_vector3d(buf, n[0], n[1], n[2])

    # Texture coordinates
    if texcoords_channels:
        for num_components, coords in texcoords_channels:
            buf.write(struct.pack("<I", num_components))
            for c in coords:
                # Always write 3 floats (aiVector3D) regardless of num_components
                write_vector3d(buf, c[0], c[1], c[2] if len(c) > 2 else 0.0)

    # Faces
    use_short_indices = num_vertices < 65536
    for face in faces:
        buf.write(struct.pack("<H", len(face)))
        for idx in face:
            if use_short_indices:
                buf.write(struct.pack("<H", idx))
            else:
                buf.write(struct.pack("<I", idx))

    # No bones

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AIMESH, data)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Bone builder
# ---------------------------------------------------------------------------

def build_bone_chunk(name, weights, offset_matrix=None):
    """
    Build a bone chunk.

    weights: list of (vertex_id, weight) tuples
    offset_matrix: 16 floats or None for identity
    """
    buf = io.BytesIO()
    write_aistring(buf, name)
    buf.write(struct.pack("<I", len(weights)))
    if offset_matrix:
        for v in offset_matrix:
            buf.write(struct.pack("<f", v))
    else:
        write_matrix4x4_identity(buf)

    # Weights: each is uint32 vertex_id + float weight
    for vid, w in weights:
        buf.write(struct.pack("<I", vid))
        buf.write(struct.pack("<f", w))

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AIBONE, data)
    return out.getvalue()


def build_mesh_with_bones_chunk(vertices, faces, bones, material_index=0,
                                primitive_types=4):
    """
    Build a mesh chunk that includes bones.

    bones: list of (name, [(vertex_id, weight), ...]) tuples
    """
    buf = io.BytesIO()
    num_vertices = len(vertices)
    num_faces = len(faces)
    num_bones = len(bones)

    buf.write(struct.pack("<I", primitive_types))
    buf.write(struct.pack("<I", num_vertices))
    buf.write(struct.pack("<I", num_faces))
    buf.write(struct.pack("<I", num_bones))
    buf.write(struct.pack("<I", material_index))

    flags = ASSBIN_MESH_HAS_POSITIONS
    buf.write(struct.pack("<I", flags))

    # Vertex positions
    for v in vertices:
        write_vector3d(buf, v[0], v[1], v[2])

    # Faces
    use_short_indices = num_vertices < 65536
    for face in faces:
        buf.write(struct.pack("<H", len(face)))
        for idx in face:
            if use_short_indices:
                buf.write(struct.pack("<H", idx))
            else:
                buf.write(struct.pack("<I", idx))

    # Bones (as nested chunks)
    for bone_name, weights in bones:
        buf.write(build_bone_chunk(bone_name, weights))

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AIMESH, data)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Material builder
# ---------------------------------------------------------------------------

def build_material_property_chunk(key, data_bytes, data_type=1, semantic=0, index=0):
    """
    Build a material property chunk.

    data_type: aiPropertyTypeInfo enum
      1 = aiPTI_Float
      3 = aiPTI_String
      4 = aiPTI_Integer
      5 = aiPTI_Buffer
    """
    buf = io.BytesIO()
    write_aistring(buf, key)
    buf.write(struct.pack("<I", semantic))
    buf.write(struct.pack("<I", index))
    buf.write(struct.pack("<I", len(data_bytes)))
    buf.write(struct.pack("<I", data_type))
    buf.write(data_bytes)

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AIMATERIALPROPERTY, data)
    return out.getvalue()


def build_material_chunk(properties):
    """
    Build a material chunk.

    properties: list of (key, data_bytes, data_type, semantic, index) tuples
    """
    buf = io.BytesIO()
    buf.write(struct.pack("<I", len(properties)))
    for key, data_bytes, data_type, semantic, index in properties:
        buf.write(build_material_property_chunk(key, data_bytes, data_type, semantic, index))

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AIMATERIAL, data)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Animation builder
# ---------------------------------------------------------------------------

def build_node_anim_chunk(node_name, position_keys=None, rotation_keys=None,
                          scaling_keys=None):
    """
    Build a node animation channel chunk.

    position_keys: list of (time, x, y, z)
    rotation_keys: list of (time, w, x, y, z)
    scaling_keys: list of (time, x, y, z)
    """
    buf = io.BytesIO()
    write_aistring(buf, node_name)

    num_pos = len(position_keys) if position_keys else 0
    num_rot = len(rotation_keys) if rotation_keys else 0
    num_scl = len(scaling_keys) if scaling_keys else 0

    buf.write(struct.pack("<I", num_pos))
    buf.write(struct.pack("<I", num_rot))
    buf.write(struct.pack("<I", num_scl))
    buf.write(struct.pack("<I", 0))  # mPreState = aiAnimBehaviour_DEFAULT
    buf.write(struct.pack("<I", 0))  # mPostState = aiAnimBehaviour_DEFAULT

    # Position keys: double time + 3 floats (aiVector3D)
    if position_keys:
        for t, x, y, z in position_keys:
            buf.write(struct.pack("<d", t))
            write_vector3d(buf, x, y, z)

    # Rotation keys: double time + 4 floats (aiQuaternion: w, x, y, z)
    if rotation_keys:
        for t, w, x, y, z in rotation_keys:
            buf.write(struct.pack("<d", t))
            buf.write(struct.pack("<ffff", w, x, y, z))

    # Scaling keys: double time + 3 floats (aiVector3D)
    if scaling_keys:
        for t, x, y, z in scaling_keys:
            buf.write(struct.pack("<d", t))
            write_vector3d(buf, x, y, z)

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AINODEANIM, data)
    return out.getvalue()


def build_animation_chunk(name, duration, ticks_per_second, channels_data):
    """
    Build an animation chunk.

    channels_data: list of already-serialized node anim chunk bytes
    """
    buf = io.BytesIO()
    write_aistring(buf, name)
    buf.write(struct.pack("<d", duration))
    buf.write(struct.pack("<d", ticks_per_second))
    buf.write(struct.pack("<I", len(channels_data)))

    for ch in channels_data:
        buf.write(ch)

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AIANIMATION, data)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Scene builder
# ---------------------------------------------------------------------------

def build_scene_chunk(flags, node_chunk_bytes, mesh_chunks=None,
                      material_chunks=None, animation_chunks=None,
                      texture_chunks=None, light_chunks=None,
                      camera_chunks=None):
    """
    Build the scene chunk.

    Layout (from ReadBinaryScene):
      - uint32 mFlags
      - uint32 mNumMeshes
      - uint32 mNumMaterials
      - uint32 mNumAnimations
      - uint32 mNumTextures
      - uint32 mNumLights
      - uint32 mNumCameras
      - [node chunk (root)]
      - [mesh chunks]
      - [material chunks]
      - [animation chunks]
      - [texture chunks]
      - [light chunks]
      - [camera chunks]
    """
    meshes = mesh_chunks or []
    materials = material_chunks or []
    animations = animation_chunks or []
    textures = texture_chunks or []
    lights = light_chunks or []
    cameras = camera_chunks or []

    buf = io.BytesIO()
    buf.write(struct.pack("<I", flags))
    buf.write(struct.pack("<I", len(meshes)))
    buf.write(struct.pack("<I", len(materials)))
    buf.write(struct.pack("<I", len(animations)))
    buf.write(struct.pack("<I", len(textures)))
    buf.write(struct.pack("<I", len(lights)))
    buf.write(struct.pack("<I", len(cameras)))

    # Root node
    buf.write(node_chunk_bytes)

    # Meshes
    for m in meshes:
        buf.write(m)

    # Materials
    for m in materials:
        buf.write(m)

    # Animations
    for a in animations:
        buf.write(a)

    # Textures
    for t in textures:
        buf.write(t)

    # Lights
    for l in lights:
        buf.write(l)

    # Cameras
    for c in cameras:
        buf.write(c)

    data = buf.getvalue()
    out = io.BytesIO()
    write_chunk(out, ASSBIN_CHUNK_AISCENE, data)
    return out.getvalue()


def write_assbin_file(filepath, scene_chunk_bytes, shortened=0, compressed=0):
    """Write a complete .assbin file: header + scene chunk."""
    with open(filepath, "wb") as f:
        write_header(f, shortened, compressed)
        f.write(scene_chunk_bytes)
    print(f"  Written: {filepath} ({os.path.getsize(filepath)} bytes)")


# ---------------------------------------------------------------------------
# Default material (used when a mesh references material index 0)
# ---------------------------------------------------------------------------

def make_default_material():
    """Create a minimal material with a name property."""
    # Material name as aiPTI_String (type 3)
    # aiString in material property data: uint32 length + chars (the writer
    # stores the raw property data, which for strings includes the 4-byte
    # length prefix).
    name = b"DefaultMaterial"
    name_data = struct.pack("<I", len(name)) + name
    props = [
        ("?mat.name", name_data, 3, 0, 0),  # aiPTI_String = 3
    ]
    return build_material_chunk(props)


# ===========================================================================
# Seed generators
# ===========================================================================

def generate_seed_empty(output_dir):
    """seed_empty.assbin - Empty scene with root node only, 0 meshes, 0 materials."""
    root_node = build_node_chunk_bytes("RootNode")
    scene = build_scene_chunk(0, root_node)
    write_assbin_file(os.path.join(output_dir, "seed_empty.assbin"), scene)


def generate_seed_one_mesh(output_dir):
    """seed_one_mesh.assbin - Scene with 1 triangle mesh, 1 material."""
    # A single triangle
    vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    ]
    faces = [
        [0, 1, 2],
    ]

    mesh_data = build_mesh_chunk(vertices, faces, material_index=0,
                                 primitive_types=4)  # aiPrimitiveType_TRIANGLE = 4

    material_data = make_default_material()

    # Root node references mesh 0
    root_node = build_node_chunk_bytes("RootNode", mesh_indices=[0])

    scene = build_scene_chunk(
        0, root_node,
        mesh_chunks=[mesh_data],
        material_chunks=[material_data],
    )
    write_assbin_file(os.path.join(output_dir, "seed_one_mesh.assbin"), scene)


def generate_seed_textured(output_dir):
    """seed_textured.assbin - Scene with 1 mesh that has UV coordinates."""
    vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    ]
    normals = [
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, 1.0),
    ]
    faces = [
        [0, 1, 2],
    ]
    # One UV channel with 2 components
    texcoords = [
        (2, [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ]),
    ]

    mesh_data = build_mesh_chunk(
        vertices, faces, material_index=0,
        normals=normals,
        texcoords_channels=texcoords,
        primitive_types=4,
    )

    # Material with a diffuse texture path property
    name = b"TexturedMaterial"
    name_data = struct.pack("<I", len(name)) + name
    # Texture file path as aiPTI_String
    tex_path = b"texture.png"
    tex_data = struct.pack("<I", len(tex_path)) + tex_path
    props = [
        ("?mat.name", name_data, 3, 0, 0),
        ("$tex.file", tex_data, 3, 1, 0),  # semantic=1 (aiTextureType_DIFFUSE), index=0
    ]
    material_data = build_material_chunk(props)

    root_node = build_node_chunk_bytes("RootNode", mesh_indices=[0])

    scene = build_scene_chunk(
        0, root_node,
        mesh_chunks=[mesh_data],
        material_chunks=[material_data],
    )
    write_assbin_file(os.path.join(output_dir, "seed_textured.assbin"), scene)


def generate_seed_animated(output_dir):
    """seed_animated.assbin - Scene with 1 mesh, 1 bone, 1 animation."""
    # Two triangles forming a simple quad (4 vertices, 2 faces)
    vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
    ]
    faces = [
        [0, 1, 2],
        [0, 2, 3],
    ]

    # One bone affecting all vertices
    bones = [
        ("Bone1", [(0, 1.0), (1, 1.0), (2, 1.0), (3, 1.0)]),
    ]

    mesh_data = build_mesh_with_bones_chunk(
        vertices, faces, bones,
        material_index=0, primitive_types=4,
    )

    material_data = make_default_material()

    # Build node hierarchy: RootNode -> BoneNode (with mesh reference on root)
    bone_node = build_node_chunk_bytes("Bone1")
    root_node = build_node_chunk_bytes(
        "RootNode",
        num_children=1,
        mesh_indices=[0],
        children_data=bone_node,
    )

    # Animation: one channel for "Bone1" with position, rotation, and scaling keys
    position_keys = [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 1.0, 0.0),
    ]
    rotation_keys = [
        (0.0, 1.0, 0.0, 0.0, 0.0),  # identity quaternion
        (1.0, 0.707, 0.0, 0.707, 0.0),  # 90 degree rotation around Y
    ]
    scaling_keys = [
        (0.0, 1.0, 1.0, 1.0),
        (1.0, 1.0, 1.0, 1.0),
    ]

    node_anim = build_node_anim_chunk(
        "Bone1",
        position_keys=position_keys,
        rotation_keys=rotation_keys,
        scaling_keys=scaling_keys,
    )

    anim = build_animation_chunk("Animation0", 1.0, 24.0, [node_anim])

    scene = build_scene_chunk(
        0, root_node,
        mesh_chunks=[mesh_data],
        material_chunks=[material_data],
        animation_chunks=[anim],
    )
    write_assbin_file(os.path.join(output_dir, "seed_animated.assbin"), scene)


# ===========================================================================
# Main
# ===========================================================================

def main():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "test", "models", "Assbin")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print()

    print("Generating seed_empty.assbin ...")
    generate_seed_empty(output_dir)

    print("Generating seed_one_mesh.assbin ...")
    generate_seed_one_mesh(output_dir)

    print("Generating seed_textured.assbin ...")
    generate_seed_textured(output_dir)

    print("Generating seed_animated.assbin ...")
    generate_seed_animated(output_dir)

    print()
    print("Verification:")
    for name in ["seed_empty.assbin", "seed_one_mesh.assbin",
                 "seed_textured.assbin", "seed_animated.assbin"]:
        path = os.path.join(output_dir, name)
        with open(path, "rb") as f:
            header = f.read(44)
        magic = b"ASSIMP.binary-dump."
        if header[:len(magic)] == magic:
            print(f"  OK  {name} - starts with correct magic bytes")
        else:
            print(f"  FAIL {name} - magic bytes mismatch: {header[:20]!r}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
