#!/usr/bin/env python3
"""
Generate minimal valid GameStudio MDL3/MDL5 files for fuzzing.

GameStudio MDL3 (magic "MDL3", iGSFileVersion=3) and MDL5 (magic "MDL5",
iGSFileVersion=5) share the same 84-byte header as Quake 1 MDL but differ
in texture, UV, triangle, and vertex formats.

Header structure (84 bytes, same as Quake 1):
  uint32  ident           "MDL3" or "MDL5"
  int32   version         6
  float   scale[3]
  float   translate[3]
  float   boundingradius
  float   eyePosition[3]
  int32   num_skins
  int32   skinwidth
  int32   skinheight
  int32   num_verts
  int32   num_tris
  int32   num_frames
  int32   synctype        ** In MDLn: number of UV coordinates **
  int32   flags
  float   size

Key differences from Quake 1:

  SKINS (MDL3/4):
    Each skin entry:
      int32  skinType   (0=palette 8-bit, 2=RGB565, 3=ARGB4444, etc.)
      uint8  data[skinwidth * skinheight * bpp]  (bpp depends on type)

  SKINS (MDL5):
    Each skin entry:
      int32  skinType
      uint32 width       (embedded width)
      uint32 height      (embedded height)
      uint8  data[width * height * bpp]

  TEXTURE COORDINATES (TexCoord_MDL3, 4 bytes each):
    int16  u
    int16  v
    Count is header.synctype (repurposed as UV count)

  TRIANGLES (Triangle_MDL3, 12 bytes each):
    uint16  index_xyz[3]   vertex indices
    uint16  index_uv[3]    UV indices

  FRAMES:
    For MDL3 (iGSFileVersion <= 3): uses Vertex (uint8 v[3] + uint8 normalIndex = 4 bytes)
    For MDL4/5 (iGSFileVersion > 3): uses Vertex_MDL4 (uint16 v[3] + uint8 normalIndex + uint8 unused = 8 bytes)

    Frame structure:
      int32  frameType (0=simple)
      If simple (MDL3):
        Vertex   bboxmin (4 bytes)
        Vertex   bboxmax (4 bytes)
        char     name[16]
        Vertex   vertices[num_verts]
      If simple (MDL4/5):
        Vertex_MDL4  bboxmin (8 bytes)
        Vertex_MDL4  bboxmax (8 bytes)
        char         name[16]
        Vertex_MDL4  vertices[num_verts]
"""

import struct
import os

VERSION = 6

HEADER_FMT = '<4si 3f 3f f 3f 8i f'
assert struct.calcsize(HEADER_FMT) == 84


def make_header(magic, num_skins, skinwidth, skinheight, num_verts, num_tris,
                num_frames, num_uvcoords, flags=0):
    """Build an 84-byte GameStudio MDL header.
    num_uvcoords goes into the synctype field."""
    return struct.pack(
        HEADER_FMT,
        magic,              # ident ("MDL3" or "MDL5")
        VERSION,            # version
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
        num_uvcoords,       # synctype = num UV coords for MDLn
        flags,
        0.0,                # size
    )


def make_skin_mdl3(skinwidth, skinheight, skin_type=0):
    """Build a skin for MDL3/4 format.
    skin_type 0 = palettized 8-bit (1 byte per pixel).
    skin_type 2 = RGB565 (2 bytes per pixel).
    Returns (skin_data, skip_bytes) where skip_bytes is the pixel data size."""
    data = struct.pack('<i', skin_type)  # skinType
    if skin_type == 0:
        # 8-bit palette indexed: 1 byte per pixel
        pixel_data = b'\x00' * (skinwidth * skinheight)
    elif skin_type == 2:
        # RGB565: 2 bytes per pixel
        pixel_data = b'\x00' * (skinwidth * skinheight * 2)
    elif skin_type == 3:
        # ARGB4444: 2 bytes per pixel
        pixel_data = b'\x00' * (skinwidth * skinheight * 2)
    else:
        # Default to palette
        pixel_data = b'\x00' * (skinwidth * skinheight)
    data += pixel_data
    return data


def make_skin_mdl5(skinwidth, skinheight, skin_type=0):
    """Build a skin for MDL5 format.
    MDL5 skin layout: int32 skinType, then the pixel data is read by
    CreateTexture_3DGS_MDL5 which first reads uint32 width + uint32 height,
    then the pixel data.

    The skip calculation in MDL5: iSkip from ParseTextureColorData + 8 (for w+h).
    Total cursor advance = iSkip + sizeof(uint32_t) [for the skin type field].
    """
    data = struct.pack('<i', skin_type)  # skinType
    # MDL5 prepends width and height before pixel data
    data += struct.pack('<II', skinwidth, skinheight)
    if skin_type == 0:
        # 8-bit palette indexed
        pixel_data = b'\x00' * (skinwidth * skinheight)
    elif skin_type == 2:
        # RGB565: 2 bytes per pixel
        pixel_data = b'\x00' * (skinwidth * skinheight * 2)
    else:
        pixel_data = b'\x00' * (skinwidth * skinheight)
    data += pixel_data
    return data


def make_texcoord_mdl3(u, v):
    """Build one TexCoord_MDL3 entry (4 bytes): int16 u, int16 v."""
    return struct.pack('<hh', u, v)


def make_triangle_mdl3(xyz_indices, uv_indices):
    """Build one Triangle_MDL3 entry (12 bytes):
    uint16 index_xyz[3], uint16 index_uv[3]."""
    return struct.pack('<HHHHHH',
                       xyz_indices[0], xyz_indices[1], xyz_indices[2],
                       uv_indices[0], uv_indices[1], uv_indices[2])


def make_vertex_q1(x, y, z, normal_index=0):
    """Build one Vertex (4 bytes): uint8 v[3] + uint8 normalIndex.
    Used by MDL3 (iGSFileVersion <= 3)."""
    return struct.pack('BBBB', x & 0xFF, y & 0xFF, z & 0xFF, normal_index & 0xFF)


def make_vertex_mdl4(x, y, z, normal_index=0):
    """Build one Vertex_MDL4 (8 bytes): uint16 v[3] + uint8 normalIndex + uint8 unused.
    Used by MDL4/5 (iGSFileVersion > 3)."""
    return struct.pack('<HHH BB', x & 0xFFFF, y & 0xFFFF, z & 0xFFFF,
                       normal_index & 0xFF, 0)


def make_simple_frame_mdl3(num_verts, name=b'frame0', vertices=None):
    """Build a simple frame for MDL3 format (byte-packed vertices).
    int32 type=0, Vertex bboxmin, Vertex bboxmax, char name[16], Vertex[num_verts]."""
    data = struct.pack('<i', 0)  # frameType = 0 (simple)
    # bboxmin (Vertex, 4 bytes)
    data += make_vertex_q1(0, 0, 0, 0)
    # bboxmax (Vertex, 4 bytes)
    data += make_vertex_q1(128, 128, 128, 0)
    # name (16 bytes, null-padded)
    data += name[:16].ljust(16, b'\x00')
    # vertices
    if vertices is None:
        for i in range(num_verts):
            data += make_vertex_q1(i * 10, i * 5, i * 3, i % 162)
    else:
        for v in vertices:
            data += make_vertex_q1(*v)
    return data


def make_simple_frame_mdl5(num_verts, name=b'frame0', vertices=None):
    """Build a simple frame for MDL4/5 format (short-packed vertices).
    int32 type=0, Vertex_MDL4 bboxmin, Vertex_MDL4 bboxmax, char name[16],
    Vertex_MDL4[num_verts]."""
    data = struct.pack('<i', 0)  # frameType = 0 (simple)
    # bboxmin (Vertex_MDL4, 8 bytes)
    data += make_vertex_mdl4(0, 0, 0, 0)
    # bboxmax (Vertex_MDL4, 8 bytes)
    data += make_vertex_mdl4(1000, 1000, 1000, 0)
    # name (16 bytes, null-padded)
    data += name[:16].ljust(16, b'\x00')
    # vertices
    if vertices is None:
        for i in range(num_verts):
            data += make_vertex_mdl4(i * 100, i * 50, i * 30, i % 162)
    else:
        for v in vertices:
            data += make_vertex_mdl4(*v)
    return data


def generate_mdl3_basic(out_dir):
    """seed_mdl3_basic.mdl: Magic "MDL3", 1 skin (palette), 3 verts, 1 triangle, 1 frame.
    skinWidth=4, skinHeight=4, 3 UV coords."""
    magic = b'MDL3'
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_verts = 3
    num_tris = 1
    num_frames = 1
    num_uvcoords = 3

    data = bytearray()
    data += make_header(magic, num_skins, skinwidth, skinheight, num_verts,
                        num_tris, num_frames, num_uvcoords)

    # 1 skin (palette type 0)
    data += make_skin_mdl3(skinwidth, skinheight, skin_type=0)

    # UV coordinates (3 entries)
    data += make_texcoord_mdl3(0, 0)
    data += make_texcoord_mdl3(3, 0)
    data += make_texcoord_mdl3(0, 3)

    # 1 triangle
    data += make_triangle_mdl3((0, 1, 2), (0, 1, 2))

    # 1 frame (MDL3 uses byte-packed vertices)
    data += make_simple_frame_mdl3(num_verts)

    filepath = os.path.join(out_dir, 'seed_mdl3_basic.mdl')
    os.makedirs(out_dir, exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")


def generate_mdl5_basic(out_dir):
    """seed_mdl5_basic.mdl: Magic "MDL5", 1 skin (palette), 4 verts, 2 triangles, 1 frame.
    skinWidth=4, skinHeight=4, 4 UV coords."""
    magic = b'MDL5'
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_verts = 4
    num_tris = 2
    num_frames = 1
    num_uvcoords = 4

    data = bytearray()
    data += make_header(magic, num_skins, skinwidth, skinheight, num_verts,
                        num_tris, num_frames, num_uvcoords)

    # 1 skin (palette type 0, MDL5 format with embedded width/height)
    data += make_skin_mdl5(skinwidth, skinheight, skin_type=0)

    # UV coordinates (4 entries)
    data += make_texcoord_mdl3(0, 0)
    data += make_texcoord_mdl3(3, 0)
    data += make_texcoord_mdl3(3, 3)
    data += make_texcoord_mdl3(0, 3)

    # 2 triangles
    data += make_triangle_mdl3((0, 1, 2), (0, 1, 2))
    data += make_triangle_mdl3((0, 2, 3), (0, 2, 3))

    # 1 frame (MDL5 uses short-packed vertices)
    data += make_simple_frame_mdl5(num_verts)

    filepath = os.path.join(out_dir, 'seed_mdl5_basic.mdl')
    os.makedirs(out_dir, exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(data)
    print(f"  Created {filepath} ({len(data)} bytes)")


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("=== Generating GameStudio MDL3 seeds ===")
    mdl3_dir = os.path.join(base, 'test', 'models', 'MDL', 'MDL3', 'fuzz_seeds')
    generate_mdl3_basic(mdl3_dir)

    print("\n=== Generating GameStudio MDL5 seeds ===")
    mdl5_dir = os.path.join(base, 'test', 'models', 'MDL', 'MDL5', 'fuzz_seeds')
    generate_mdl5_basic(mdl5_dir)

    print("\n=== Done! ===")


if __name__ == '__main__':
    main()
