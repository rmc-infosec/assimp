#!/usr/bin/env python3
"""Generate binary IQM (Inter-Quake Model) seed files for fuzzing.

IQM format:
  - Header: "INTERQUAKEMODEL\0" (16 bytes magic) + 27 uint32 fields
  - iqmheader is 124 bytes total
  - All multi-byte values are little-endian
  - Data sections: text, meshes, vertex arrays, triangles, joints, poses, anims, etc.
  - Version must be 2, filesize must match actual file size
  - Vertex arrays have: type(4), flags(4), format(4), size(4), offset(4)
  - Mesh: name(4), material(4), first_vertex(4), num_vertexes(4),
          first_triangle(4), num_triangles(4)
  - Triangle: vertex[3] (3 uint32s)
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test", "models", "IQM", "fuzz_seeds")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Constants
IQM_MAGIC = b"INTERQUAKEMODEL\x00"
IQM_VERSION = 2

# Vertex array types
IQM_POSITION = 0
IQM_TEXCOORD = 1
IQM_NORMAL = 2
IQM_TANGENT = 3
IQM_BLENDINDEXES = 4
IQM_BLENDWEIGHTS = 5
IQM_COLOR = 6
IQM_CUSTOM = 0x10

# Formats
IQM_BYTE = 0
IQM_UBYTE = 1
IQM_SHORT = 2
IQM_USHORT = 3
IQM_INT = 4
IQM_UINT = 5
IQM_HALF = 6
IQM_FLOAT = 7
IQM_DOUBLE = 8

HEADER_SIZE = 124
MESH_SIZE = 24       # 6 * 4
TRIANGLE_SIZE = 12   # 3 * 4
VERTEXARRAY_SIZE = 20  # 5 * 4
JOINT_SIZE = 48      # name(4) + parent(4) + translate(12) + rotate(16) + scale(12)
POSE_SIZE = 88       # parent(4) + mask(4) + channeloffset(40) + channelscale(40)
ANIM_SIZE = 20       # name(4) + first_frame(4) + num_frames(4) + framerate(4) + flags(4)


def u32(v):
    return struct.pack('<I', v)


def i32(v):
    return struct.pack('<i', v)


def f32(v):
    return struct.pack('<f', v)


def build_iqm(text_data=b'\x00', meshes=None, vertexarrays=None,
              vertex_data=None, triangles=None, joints=None,
              poses=None, anims=None, frame_data=None,
              num_vertexes=0, num_framechannels=0):
    """Build a complete IQM file from components."""

    # Start laying out data after the header
    offset = HEADER_SIZE

    # Text section
    ofs_text = offset
    num_text = len(text_data)
    offset += num_text

    # Meshes
    num_meshes = len(meshes) if meshes else 0
    ofs_meshes = offset if num_meshes else 0
    mesh_blob = b''
    if meshes:
        for m in meshes:
            mesh_blob += u32(m['name']) + u32(m['material'])
            mesh_blob += u32(m['first_vertex']) + u32(m['num_vertexes'])
            mesh_blob += u32(m['first_triangle']) + u32(m['num_triangles'])
        offset += len(mesh_blob)

    # Vertex arrays
    num_vas = len(vertexarrays) if vertexarrays else 0
    ofs_vertexarrays = offset if num_vas else 0
    va_blob = b''
    # We'll fill in actual offsets after we know where vertex data goes
    va_data_offset = offset + num_vas * VERTEXARRAY_SIZE
    if vertexarrays:
        for va in vertexarrays:
            va_blob += u32(va['type']) + u32(va.get('flags', 0))
            va_blob += u32(va['format']) + u32(va['size'])
            va_blob += u32(va_data_offset + va['data_offset'])
        offset += len(va_blob)

    # Vertex data
    vdata_blob = vertex_data if vertex_data else b''
    offset += len(vdata_blob)

    # Triangles
    num_triangles = len(triangles) if triangles else 0
    ofs_triangles = offset if num_triangles else 0
    tri_blob = b''
    if triangles:
        for t in triangles:
            tri_blob += u32(t[0]) + u32(t[1]) + u32(t[2])
        offset += len(tri_blob)

    # Joints
    num_joints = len(joints) if joints else 0
    ofs_joints = offset if num_joints else 0
    joint_blob = b''
    if joints:
        for j in joints:
            joint_blob += u32(j['name']) + i32(j['parent'])
            joint_blob += f32(j['tx']) + f32(j['ty']) + f32(j['tz'])
            joint_blob += f32(j['rx']) + f32(j['ry']) + f32(j['rz']) + f32(j['rw'])
            joint_blob += f32(j['sx']) + f32(j['sy']) + f32(j['sz'])
        offset += len(joint_blob)

    # Poses
    num_poses = len(poses) if poses else 0
    ofs_poses = offset if num_poses else 0
    pose_blob = b''
    if poses:
        for p in poses:
            pose_blob += i32(p['parent']) + u32(p['mask'])
            for v in p['channeloffset']:
                pose_blob += f32(v)
            for v in p['channelscale']:
                pose_blob += f32(v)
        offset += len(pose_blob)

    # Animations
    num_anims = len(anims) if anims else 0
    ofs_anims = offset if num_anims else 0
    anim_blob = b''
    if anims:
        for a in anims:
            anim_blob += u32(a['name']) + u32(a['first_frame'])
            anim_blob += u32(a['num_frames']) + f32(a['framerate'])
            anim_blob += u32(a.get('flags', 0))
        offset += len(anim_blob)

    # Frame data
    num_frames = 0
    ofs_frames = 0
    frame_blob = b''
    if frame_data:
        num_frames = len(frame_data)
        ofs_frames = offset
        for fd in frame_data:
            frame_blob += fd
        offset += len(frame_blob)

    filesize = offset

    # Build header
    header = IQM_MAGIC
    header += u32(IQM_VERSION)
    header += u32(filesize)
    header += u32(0)  # flags
    header += u32(num_text) + u32(ofs_text)
    header += u32(num_meshes) + u32(ofs_meshes)
    header += u32(num_vas) + u32(num_vertexes) + u32(ofs_vertexarrays)
    header += u32(num_triangles) + u32(ofs_triangles) + u32(0)  # ofs_adjacency
    header += u32(num_joints) + u32(ofs_joints)
    header += u32(num_poses) + u32(ofs_poses)
    header += u32(num_anims) + u32(ofs_anims)
    header += u32(num_frames) + u32(num_framechannels) + u32(ofs_frames) + u32(0)  # ofs_bounds
    header += u32(0) + u32(0)  # num_comment, ofs_comment
    header += u32(0) + u32(0)  # num_extensions, ofs_extensions

    result = header + text_data + mesh_blob + va_blob + vdata_blob + tri_blob
    result += joint_blob + pose_blob + anim_blob + frame_blob

    assert len(result) == filesize, f"Size mismatch: {len(result)} vs {filesize}"
    return result


def seed_minimal_triangle():
    """Minimal IQM with 1 mesh, 1 triangle, position-only vertex array."""
    # Text: material name at offset 0 = "\0" (empty)
    text = b'\x00mesh\x00'  # offset 0: '\0', offset 1: 'mesh\0'

    # 3 vertices, each 3 floats (position only)
    vdata = b''
    vdata += f32(0.0) + f32(0.0) + f32(0.0)
    vdata += f32(1.0) + f32(0.0) + f32(0.0)
    vdata += f32(0.0) + f32(1.0) + f32(0.0)

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
    ]

    meshes = [
        {'name': 1, 'material': 0, 'first_vertex': 0, 'num_vertexes': 3,
         'first_triangle': 0, 'num_triangles': 1},
    ]

    triangles = [(0, 1, 2)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=3)


def seed_with_normals_and_uvs():
    """IQM with position, normal, and texcoord vertex arrays."""
    text = b'\x00mat0\x00'

    # 3 vertices, each with: position(3f), normal(3f), texcoord(2f)
    pos_data = b''
    pos_data += f32(0.0) + f32(0.0) + f32(0.0)
    pos_data += f32(1.0) + f32(0.0) + f32(0.0)
    pos_data += f32(0.0) + f32(1.0) + f32(0.0)

    nrm_data = b''
    nrm_data += f32(0.0) + f32(0.0) + f32(1.0)
    nrm_data += f32(0.0) + f32(0.0) + f32(1.0)
    nrm_data += f32(0.0) + f32(0.0) + f32(1.0)

    uv_data = b''
    uv_data += f32(0.0) + f32(0.0)
    uv_data += f32(1.0) + f32(0.0)
    uv_data += f32(0.0) + f32(1.0)

    vdata = pos_data + nrm_data + uv_data
    pos_size = len(pos_data)
    nrm_size = len(nrm_data)

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
        {'type': IQM_NORMAL, 'format': IQM_FLOAT, 'size': 3, 'data_offset': pos_size},
        {'type': IQM_TEXCOORD, 'format': IQM_FLOAT, 'size': 2, 'data_offset': pos_size + nrm_size},
    ]

    meshes = [{'name': 1, 'material': 0, 'first_vertex': 0, 'num_vertexes': 3,
               'first_triangle': 0, 'num_triangles': 1}]
    triangles = [(0, 1, 2)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=3)


def seed_with_colors_ubyte():
    """IQM with vertex colors (UBYTE format)."""
    text = b'\x00colored\x00'

    pos_data = b''
    for v in [(0, 0, 0), (1, 0, 0), (0, 1, 0)]:
        pos_data += f32(v[0]) + f32(v[1]) + f32(v[2])

    # 3 vertices, RGBA as 4 ubytes each
    color_data = b''
    color_data += bytes([255, 0, 0, 255])    # red
    color_data += bytes([0, 255, 0, 255])    # green
    color_data += bytes([0, 0, 255, 255])    # blue

    vdata = pos_data + color_data

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
        {'type': IQM_COLOR, 'format': IQM_UBYTE, 'size': 4, 'data_offset': len(pos_data)},
    ]

    meshes = [{'name': 1, 'material': 0, 'first_vertex': 0, 'num_vertexes': 3,
               'first_triangle': 0, 'num_triangles': 1}]
    triangles = [(0, 1, 2)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=3)


def seed_with_colors_float():
    """IQM with vertex colors (FLOAT format)."""
    text = b'\x00fcolored\x00'

    pos_data = b''
    for v in [(0, 0, 0), (1, 0, 0), (0, 1, 0)]:
        pos_data += f32(v[0]) + f32(v[1]) + f32(v[2])

    # 3 vertices, RGBA as 4 floats each
    color_data = b''
    color_data += f32(1.0) + f32(0.0) + f32(0.0) + f32(1.0)
    color_data += f32(0.0) + f32(1.0) + f32(0.0) + f32(1.0)
    color_data += f32(0.0) + f32(0.0) + f32(1.0) + f32(1.0)

    vdata = pos_data + color_data

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
        {'type': IQM_COLOR, 'format': IQM_FLOAT, 'size': 4, 'data_offset': len(pos_data)},
    ]

    meshes = [{'name': 1, 'material': 0, 'first_vertex': 0, 'num_vertexes': 3,
               'first_triangle': 0, 'num_triangles': 1}]
    triangles = [(0, 1, 2)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=3)


def seed_with_colors_ubyte_rgb():
    """IQM with vertex colors (UBYTE, 3 channels - no alpha, triggers step==3 path)."""
    text = b'\x00rgb3\x00'

    pos_data = b''
    for v in [(0, 0, 0), (1, 0, 0), (0, 1, 0)]:
        pos_data += f32(v[0]) + f32(v[1]) + f32(v[2])

    # 3 vertices, RGB as 3 ubytes each (no alpha)
    color_data = b''
    color_data += bytes([255, 0, 0])
    color_data += bytes([0, 255, 0])
    color_data += bytes([0, 0, 255])

    vdata = pos_data + color_data

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
        {'type': IQM_COLOR, 'format': IQM_UBYTE, 'size': 3, 'data_offset': len(pos_data)},
    ]

    meshes = [{'name': 1, 'material': 0, 'first_vertex': 0, 'num_vertexes': 3,
               'first_triangle': 0, 'num_triangles': 1}]
    triangles = [(0, 1, 2)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=3)


def seed_multi_mesh():
    """IQM with 2 meshes sharing vertex data."""
    text = b'\x00mesh0\x00mesh1\x00mat0\x00mat1\x00'
    # offsets: 0=\0, 1=mesh0, 7=mesh1, 13=mat0, 18=mat1

    # 6 vertices (3 per mesh)
    pos_data = b''
    for v in [(0, 0, 0), (1, 0, 0), (0, 1, 0),    # mesh 0
              (2, 0, 0), (3, 0, 0), (2, 1, 0)]:    # mesh 1
        pos_data += f32(v[0]) + f32(v[1]) + f32(v[2])

    vdata = pos_data

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
    ]

    meshes = [
        {'name': 1, 'material': 13, 'first_vertex': 0, 'num_vertexes': 3,
         'first_triangle': 0, 'num_triangles': 1},
        {'name': 7, 'material': 18, 'first_vertex': 3, 'num_vertexes': 3,
         'first_triangle': 1, 'num_triangles': 1},
    ]

    triangles = [(0, 1, 2), (3, 4, 5)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=6)


def seed_full_attributes():
    """IQM with position, normals, texcoords, and UBYTE colors."""
    text = b'\x00fullmesh\x00fullmat\x00'

    pos_data = b''
    nrm_data = b''
    uv_data = b''
    color_data = b''
    for i, v in enumerate([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)]):
        pos_data += f32(v[0]) + f32(v[1]) + f32(v[2])
        nrm_data += f32(0.0) + f32(0.0) + f32(1.0)
        uv_data += f32(v[0]) + f32(v[1])
        color_data += bytes([255 if i == 0 else 0, 255 if i == 1 else 0,
                            255 if i == 2 else 0, 255])

    vdata = pos_data + nrm_data + uv_data + color_data

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
        {'type': IQM_NORMAL, 'format': IQM_FLOAT, 'size': 3, 'data_offset': len(pos_data)},
        {'type': IQM_TEXCOORD, 'format': IQM_FLOAT, 'size': 2,
         'data_offset': len(pos_data) + len(nrm_data)},
        {'type': IQM_COLOR, 'format': IQM_UBYTE, 'size': 4,
         'data_offset': len(pos_data) + len(nrm_data) + len(uv_data)},
    ]

    meshes = [{'name': 1, 'material': 10, 'first_vertex': 0, 'num_vertexes': 4,
               'first_triangle': 0, 'num_triangles': 2}]
    triangles = [(0, 1, 2), (0, 2, 3)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=4)


def seed_colors_float_rgb():
    """IQM with vertex colors (FLOAT, 3 channels - triggers step==3 alpha=1 path)."""
    text = b'\x00frgb3\x00'

    pos_data = b''
    for v in [(0, 0, 0), (1, 0, 0), (0, 1, 0)]:
        pos_data += f32(v[0]) + f32(v[1]) + f32(v[2])

    color_data = b''
    color_data += f32(1.0) + f32(0.0) + f32(0.0)
    color_data += f32(0.0) + f32(1.0) + f32(0.0)
    color_data += f32(0.0) + f32(0.0) + f32(1.0)

    vdata = pos_data + color_data

    vertexarrays = [
        {'type': IQM_POSITION, 'format': IQM_FLOAT, 'size': 3, 'data_offset': 0},
        {'type': IQM_COLOR, 'format': IQM_FLOAT, 'size': 3, 'data_offset': len(pos_data)},
    ]

    meshes = [{'name': 1, 'material': 0, 'first_vertex': 0, 'num_vertexes': 3,
               'first_triangle': 0, 'num_triangles': 1}]
    triangles = [(0, 1, 2)]

    return build_iqm(text_data=text, meshes=meshes, vertexarrays=vertexarrays,
                     vertex_data=vdata, triangles=triangles, num_vertexes=3)


def main():
    seeds = {
        "seed_minimal_triangle.iqm": seed_minimal_triangle(),
        "seed_normals_uvs.iqm": seed_with_normals_and_uvs(),
        "seed_colors_ubyte.iqm": seed_with_colors_ubyte(),
        "seed_colors_float.iqm": seed_with_colors_float(),
        "seed_colors_ubyte_rgb.iqm": seed_with_colors_ubyte_rgb(),
        "seed_multi_mesh.iqm": seed_multi_mesh(),
        "seed_full_attributes.iqm": seed_full_attributes(),
        "seed_colors_float_rgb.iqm": seed_colors_float_rgb(),
    }

    for name, data in seeds.items():
        path = os.path.join(OUTPUT_DIR, name)
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  {name}: {len(data)} bytes")

    print(f"\nGenerated {len(seeds)} IQM seed files in {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
