#!/usr/bin/env python3
"""
Generate minimal valid Quake 1 MDL files for fuzzing.

The Quake 1 MDL format ("IDPO", version 6) is used by the original Quake engine.
Assimp's MDLImporter reads these via InternReadFile_Quake1().

Header structure (84 bytes, packed):
  uint32  ident           "IDPO" (0x4F504449 LE)
  int32   version         6
  float   scale[3]        per-axis scale factors
  float   translate[3]    per-axis translation
  float   boundingradius
  float   eyePosition[3]
  int32   num_skins
  int32   skinwidth
  int32   skinheight
  int32   num_verts
  int32   num_tris
  int32   num_frames
  int32   synctype        0=sync, 1=rand
  int32   flags
  float   size

After header:
  1. Skins (num_skins entries):
     - int32 skinType (0=single, 1=group)
     - If single: skinwidth*skinheight bytes (8-bit palette indices)
     - If group: int32 numSkins, float[numSkins] intervals,
                 then numSkins * skinwidth*skinheight bytes

  2. Texture coordinates (num_verts entries, 12 bytes each):
     - int32 onseam
     - int32 s
     - int32 t

  3. Triangles (num_tris entries, 16 bytes each):
     - int32 facesfront
     - int32 vertexIndices[3]

  4. Frames (num_frames entries):
     - int32 frameType (0=simple, non-zero=group)
     - If simple:
         Vertex bboxmin (4 bytes: x, y, z, normalIndex)
         Vertex bboxmax (4 bytes)
         char name[16]
         Vertex[num_verts] (4 bytes each)
     - If group:
         int32 numFrames
         Vertex bboxmin (4 bytes)
         Vertex bboxmax (4 bytes)
         float[numFrames] intervals
         Then numFrames simple frames (bboxmin, bboxmax, name, vertices)
"""

import struct
import os

# Quake 1 MDL magic and version
MAGIC_IDPO = b'IDPO'  # 0x4F504449 little-endian stored as bytes
VERSION_Q1 = 6

HEADER_FMT = '<4si 3f 3f f 3f 8i f'
# ident(4) + version(4) + scale(12) + translate(12) + boundingradius(4) +
# eyePos(12) + num_skins(4) + skinwidth(4) + skinheight(4) + num_verts(4) +
# num_tris(4) + num_frames(4) + synctype(4) + flags(4) + size(4)
# = 84 bytes

assert struct.calcsize(HEADER_FMT) == 84


def make_header(num_skins, skinwidth, skinheight, num_verts, num_tris,
                num_frames, synctype=0, flags=0):
    """Build an 84-byte Quake 1 MDL header."""
    return struct.pack(
        HEADER_FMT,
        MAGIC_IDPO,         # ident
        VERSION_Q1,         # version
        1.0, 1.0, 1.0,     # scale
        0.0, 0.0, 0.0,     # translate
        10.0,               # boundingradius
        0.0, 0.0, 0.0,     # eyePosition
        num_skins,
        skinwidth,
        skinheight,
        num_verts,
        num_tris,
        num_frames,
        synctype,
        flags,
        0.0,                # size
    )


def make_single_skin(skinwidth, skinheight):
    """Build a single skin: int32 type=0 + palette data."""
    data = struct.pack('<i', 0)  # skinType = 0 (single)
    data += b'\x00' * (skinwidth * skinheight)  # palette indices
    return data


def make_group_skin(skinwidth, skinheight, num_subskins):
    """Build a group skin: int32 type=1, int32 numSkins, float[] intervals, data.

    Note: assimp's Quake 1 parser only reads ONE skin's worth of pixel data
    from a group skin (skinwidth * skinheight bytes), regardless of numSkins.
    The skip is: 8 (group+nb) + numSkins*4 (intervals) + skinwidth*skinheight.
    We generate data matching this parser behavior."""
    data = struct.pack('<i', 1)  # skinType = 1 (group)
    data += struct.pack('<i', num_subskins)
    # intervals (one float per sub-skin)
    for i in range(num_subskins):
        data += struct.pack('<f', 0.1 * (i + 1))
    # pixel data: only one skin's worth (matches parser skip)
    data += b'\x00' * (skinwidth * skinheight)
    return data


def make_texcoord(onseam, s, t):
    """Build one texture coordinate entry (12 bytes)."""
    return struct.pack('<iii', onseam, s, t)


def make_triangle(facesfront, v0, v1, v2):
    """Build one triangle entry (16 bytes)."""
    return struct.pack('<iiii', facesfront, v0, v1, v2)


def make_vertex(x, y, z, normal_index=0):
    """Build one trivertx_t (4 bytes): x, y, z, normalIndex as uint8."""
    return struct.pack('BBBB', x & 0xFF, y & 0xFF, z & 0xFF, normal_index & 0xFF)


def make_simple_frame(num_verts, name=b'frame0', vertices=None):
    """Build a simple frame (no type prefix).
    Returns: bboxmin(4) + bboxmax(4) + name(16) + vertices(4*num_verts)"""
    data = b''
    # bboxmin
    data += make_vertex(0, 0, 0, 0)
    # bboxmax
    data += make_vertex(128, 128, 128, 0)
    # name (16 bytes, null-padded)
    padded_name = name[:16].ljust(16, b'\x00')
    data += padded_name
    # vertices
    if vertices is None:
        for i in range(num_verts):
            data += make_vertex(i * 10, i * 5, i * 3, i % 162)
    else:
        for v in vertices:
            data += make_vertex(*v)
    return data


def make_frame_single(num_verts, name=b'frame0', vertices=None):
    """Build a complete single frame entry: type(4) + simple_frame."""
    data = struct.pack('<i', 0)  # frameType = 0 (simple)
    data += make_simple_frame(num_verts, name, vertices)
    return data


def make_frame_group(num_verts, sub_frames):
    """Build a complete group frame entry.
    sub_frames: list of (name, vertices_or_None)"""
    num_subframes = len(sub_frames)
    data = struct.pack('<i', 1)  # frameType != 0 (group)
    data += struct.pack('<i', num_subframes)
    # group bboxmin
    data += make_vertex(0, 0, 0, 0)
    # group bboxmax
    data += make_vertex(255, 255, 255, 0)
    # intervals (float per sub-frame)
    for i in range(num_subframes):
        data += struct.pack('<f', 0.1 * (i + 1))
    # sub-frames (each is a simple frame, no type prefix)
    for name, verts in sub_frames:
        data += make_simple_frame(num_verts, name, verts)
    return data


def generate_seed_basic(out_dir):
    """seed_quake1_basic.mdl: 1 skin, 3 verts, 1 triangle, 1 frame,
    skinWidth=4, skinHeight=4."""
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_verts = 3
    num_tris = 1
    num_frames = 1

    data = bytearray()
    data += make_header(num_skins, skinwidth, skinheight, num_verts,
                        num_tris, num_frames)
    # 1 single skin
    data += make_single_skin(skinwidth, skinheight)
    # texture coords
    data += make_texcoord(0, 0, 0)
    data += make_texcoord(0, 3, 0)
    data += make_texcoord(0, 0, 3)
    # 1 triangle
    data += make_triangle(1, 0, 1, 2)
    # 1 frame
    data += make_frame_single(num_verts)

    filepath = os.path.join(out_dir, 'seed_quake1_basic.mdl')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")


def generate_seed_multiskin(out_dir):
    """seed_quake1_multiskin.mdl: 2 skins (both single type), 4 verts,
    2 triangles, 1 frame."""
    num_skins = 2
    skinwidth = 4
    skinheight = 4
    num_verts = 4
    num_tris = 2
    num_frames = 1

    data = bytearray()
    data += make_header(num_skins, skinwidth, skinheight, num_verts,
                        num_tris, num_frames)
    # 2 single skins
    data += make_single_skin(skinwidth, skinheight)
    data += make_single_skin(skinwidth, skinheight)
    # texture coords
    data += make_texcoord(0, 0, 0)
    data += make_texcoord(0, 3, 0)
    data += make_texcoord(0, 0, 3)
    data += make_texcoord(0x20, 2, 2)  # onseam = 0x20
    # 2 triangles
    data += make_triangle(1, 0, 1, 2)
    data += make_triangle(0, 0, 2, 3)  # backface
    # 1 frame
    data += make_frame_single(num_verts)

    filepath = os.path.join(out_dir, 'seed_quake1_multiskin.mdl')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")


def generate_seed_multiframe(out_dir):
    """seed_quake1_multiframe.mdl: 1 skin, 3 verts, 1 triangle,
    3 frames (animation)."""
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_verts = 3
    num_tris = 1
    num_frames = 3

    data = bytearray()
    data += make_header(num_skins, skinwidth, skinheight, num_verts,
                        num_tris, num_frames)
    # 1 single skin
    data += make_single_skin(skinwidth, skinheight)
    # texture coords
    data += make_texcoord(0, 0, 0)
    data += make_texcoord(0, 3, 0)
    data += make_texcoord(0, 0, 3)
    # 1 triangle
    data += make_triangle(1, 0, 1, 2)
    # 3 frames
    data += make_frame_single(num_verts, b'frame0',
                              [(0, 0, 0, 0), (10, 0, 0, 1), (0, 10, 0, 2)])
    data += make_frame_single(num_verts, b'frame1',
                              [(5, 5, 0, 0), (15, 5, 0, 1), (5, 15, 0, 2)])
    data += make_frame_single(num_verts, b'frame2',
                              [(10, 10, 0, 0), (20, 10, 0, 1), (10, 20, 0, 2)])

    filepath = os.path.join(out_dir, 'seed_quake1_multiframe.mdl')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")


def generate_seed_group_skin(out_dir):
    """seed_quake1_group_skin.mdl: 1 group skin with 2 sub-skins,
    3 verts, 1 triangle, 1 frame."""
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_verts = 3
    num_tris = 1
    num_frames = 1

    data = bytearray()
    data += make_header(num_skins, skinwidth, skinheight, num_verts,
                        num_tris, num_frames)
    # 1 group skin with 2 sub-skins
    data += make_group_skin(skinwidth, skinheight, 2)
    # texture coords
    data += make_texcoord(0, 0, 0)
    data += make_texcoord(0, 3, 0)
    data += make_texcoord(0, 0, 3)
    # 1 triangle
    data += make_triangle(1, 0, 1, 2)
    # 1 frame
    data += make_frame_single(num_verts)

    filepath = os.path.join(out_dir, 'seed_quake1_group_skin.mdl')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")


def generate_seed_group_frame(out_dir):
    """seed_quake1_group_frame.mdl: 1 skin, 3 verts, 1 triangle,
    1 frame group with 2 sub-frames."""
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_verts = 3
    num_tris = 1
    num_frames = 1  # 1 frame entry (which is a group)

    data = bytearray()
    data += make_header(num_skins, skinwidth, skinheight, num_verts,
                        num_tris, num_frames)
    # 1 single skin
    data += make_single_skin(skinwidth, skinheight)
    # texture coords
    data += make_texcoord(0, 0, 0)
    data += make_texcoord(0, 3, 0)
    data += make_texcoord(0, 0, 3)
    # 1 triangle
    data += make_triangle(1, 0, 1, 2)
    # 1 frame group with 2 sub-frames
    sub_frames = [
        (b'group_f0', [(0, 0, 0, 0), (10, 0, 0, 1), (0, 10, 0, 2)]),
        (b'group_f1', [(5, 5, 5, 0), (15, 5, 5, 1), (5, 15, 5, 2)]),
    ]
    data += make_frame_group(num_verts, sub_frames)

    filepath = os.path.join(out_dir, 'seed_quake1_group_frame.mdl')
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(base, 'test', 'models', 'MDL', 'Quake1', 'fuzz_seeds')
    os.makedirs(out_dir, exist_ok=True)

    print("=== Generating Quake 1 MDL seeds ===")
    generate_seed_basic(out_dir)
    generate_seed_multiskin(out_dir)
    generate_seed_multiframe(out_dir)
    generate_seed_group_skin(out_dir)
    generate_seed_group_frame(out_dir)
    print("\n=== Done! ===")


if __name__ == '__main__':
    main()
