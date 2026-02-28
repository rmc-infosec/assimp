#!/usr/bin/env python3
"""Generate binary COB (TrueSpace) seed files for fuzzing.

COB Binary format:
- 32-byte header:
    bytes 0-8:   "Caligari " (9 bytes)
    bytes 9-14:  version string e.g. "V00.01" (6 bytes)
    byte 15:     format type - 'A' for ASCII, 'B'/'L' for binary (little-endian)
    bytes 16-31: padding ("LH" + zeros in practice)

- Binary chunk header (16 bytes):
    4 bytes: chunk type (e.g. "PolH", "Mat1", "Grou", "END ")
    2 bytes: major version (uint16 LE)
    2 bytes: minor version (uint16 LE)
    4 bytes: chunk id (uint32 LE)
    4 bytes: parent id (uint32 LE)
    4 bytes: data size in bytes (uint32 LE)

- ReadBasicNodeInfo_Binary layout:
    2 bytes: dupe count (uint16 LE)
    2 bytes: name length (uint16 LE)
    N bytes: name string
    48 bytes: local axes (skipped - 4 float32 * 3 axes * 4 = 48)
                Actually: 3 axes * 3 floats + center 3 floats = 48 bytes? Let's use 48 zeros.
    48 bytes: transform (3 rows * 4 columns * 4 bytes = 48 bytes as float32 LE)

- PolH binary data after node info:
    4 bytes: num vertices (uint32)
    num_verts * 12 bytes: vertex positions (3 * float32)
    4 bytes: num texture coords (uint32)
    num_tc * 8 bytes: texture coords (2 * float32)
    4 bytes: num faces (uint32)
    per face:
        1 byte: flags (0x08 = hole)
        2 bytes: num indices (uint16)
        2 bytes: material index (uint16) [only if not a hole]
        num_indices * 8 bytes: per index (uint32 pos_idx + uint32 uv_idx)
    if version > 4:
        4 bytes: draw_flags (uint32)
    if 5 < version < 8:
        4 bytes: extra data (uint32, unused)

- Mat1 binary data after chunk header:
    2 bytes: matnum (uint16)
    1 byte: shader type ('f'=flat, 'p'=phong, 'm'=metal)
    1 byte: autofacet ('f'=faceted, 'a'=autofaceted, 's'=smooth)
    1 byte: autofacet_angle (uint8)
    12 bytes: rgb (3 * float32)
    4 bytes: alpha (float32)
    4 bytes: ka (float32)
    4 bytes: ks (float32)
    4 bytes: exp (float32)
    4 bytes: ior (float32)
    2 bytes: texture id marker (e.g. "e:", "t:", "b:")
    ... texture data if present
    If no textures, the reader backtracks 2 bytes (reader.IncPtr(-2))

- Unit binary data after chunk header:
    2 bytes: unit type (uint16)

- Grou/Lght/Came: just basic node info
"""

import struct
import os

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'test', 'models', 'COB', 'fuzz_seeds')


def write_header(buf, version="V00.01", binary_marker='B'):
    """Write 32-byte COB header for binary format."""
    # "Caligari " (9 bytes) + version (6 bytes) + format marker (1 byte)
    header = b'Caligari '  # 9 bytes
    header += version.encode('ascii')  # 6 bytes, e.g. "V00.01"
    header += binary_marker.encode('ascii')  # 1 byte
    # Pad rest to 32 bytes (16 bytes remaining)
    header += b'LH' + b'\x00' * 14
    assert len(header) == 32
    buf.extend(header)


def write_chunk_header(buf, chunk_type, major_ver, minor_ver, chunk_id, parent_id, data_size):
    """Write a 16-byte binary chunk header."""
    assert len(chunk_type) == 4
    buf.extend(chunk_type.encode('ascii'))
    buf.extend(struct.pack('<HH', major_ver, minor_ver))
    buf.extend(struct.pack('<III', chunk_id, parent_id, data_size))


def write_basic_node_info(buf, name, dupe_count=0):
    """Write BasicNodeInfo_Binary: dupes, name, local axes (48 zeros), identity transform."""
    name_bytes = name.encode('ascii')
    buf.extend(struct.pack('<H', dupe_count))
    buf.extend(struct.pack('<H', len(name_bytes)))
    buf.extend(name_bytes)
    # Local axes: 48 bytes (skipped by reader)
    buf.extend(b'\x00' * 48)
    # Transform: 3x4 identity matrix (row-major, 3 rows of 4 floats)
    identity_3x4 = [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
    ]
    for val in identity_3x4:
        buf.extend(struct.pack('<f', val))


def basic_node_info_size(name):
    """Calculate the byte size of a BasicNodeInfo block."""
    return 2 + 2 + len(name.encode('ascii')) + 48 + 48  # dupes + name_len + name + axes + transform


def write_end_chunk(buf):
    """Write END chunk."""
    write_chunk_header(buf, 'END ', 0, 0, 0, 0, 0)


def generate_basic_binary_cob():
    """Generate a basic binary COB with a single mesh (PolH) + material (Mat1) + group (Grou)."""
    buf = bytearray()
    write_header(buf)

    # --- Grou chunk (group node, id=1, parent=0) ---
    grou_data = bytearray()
    write_basic_node_info(grou_data, "root")
    write_chunk_header(buf, 'Grou', 0, 1, 1, 0, len(grou_data))
    buf.extend(grou_data)

    # --- Unit chunk (id=2, parent=1) ---
    unit_data = struct.pack('<H', 2)  # Units = 2 (meters)
    write_chunk_header(buf, 'Unit', 0, 1, 2, 1, len(unit_data))
    buf.extend(unit_data)

    # --- PolH chunk (mesh, id=3, parent=1) ---
    # Version 0.6 (version = 0*10 + 6 = 6, which is > 4 so draw_flags is read)
    polh_data = bytearray()
    write_basic_node_info(polh_data, "Cube")

    # 8 vertices for a cube
    vertices = [
        (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0),
        (1.0, 1.0, -1.0), (-1.0, 1.0, -1.0),
        (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0),
        (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0),
    ]
    polh_data.extend(struct.pack('<I', len(vertices)))
    for v in vertices:
        polh_data.extend(struct.pack('<fff', *v))

    # 4 texture coords
    tex_coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    polh_data.extend(struct.pack('<I', len(tex_coords)))
    for tc in tex_coords:
        polh_data.extend(struct.pack('<ff', *tc))

    # 6 faces (quads) for a cube
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (2, 6, 7, 3),
        (0, 3, 7, 4), (1, 5, 6, 2),
    ]
    polh_data.extend(struct.pack('<I', len(faces)))
    for fi, face in enumerate(faces):
        polh_data.extend(struct.pack('<B', 0))  # flags: not a hole
        polh_data.extend(struct.pack('<H', len(face)))  # num indices
        polh_data.extend(struct.pack('<H', 0))  # material index
        for vi, pos_idx in enumerate(face):
            uv_idx = vi % len(tex_coords)
            polh_data.extend(struct.pack('<II', pos_idx, uv_idx))

    # draw_flags (version > 4)
    polh_data.extend(struct.pack('<I', 1))  # SOLID

    write_chunk_header(buf, 'PolH', 0, 6, 3, 1, len(polh_data))
    buf.extend(polh_data)

    # --- Mat1 chunk (material, id=4, parent=3) ---
    mat1_data = bytearray()
    mat1_data.extend(struct.pack('<H', 0))  # matnum = 0
    mat1_data.extend(b'p')  # shader = phong
    mat1_data.extend(b's')  # autofacet = smooth
    mat1_data.extend(struct.pack('<B', 45))  # autofacet_angle
    mat1_data.extend(struct.pack('<fff', 0.8, 0.2, 0.1))  # rgb
    mat1_data.extend(struct.pack('<f', 1.0))  # alpha
    mat1_data.extend(struct.pack('<f', 0.3))  # ka
    mat1_data.extend(struct.pack('<f', 0.7))  # ks
    mat1_data.extend(struct.pack('<f', 32.0))  # exp
    mat1_data.extend(struct.pack('<f', 1.5))  # ior
    # No textures - write dummy bytes that don't match any texture id
    # The reader reads 2 bytes for id, checks for 'e:', 't:', 'b:'
    # If none match, it does IncPtr(-2) to backtrack
    mat1_data.extend(b'xx')  # no textures
    write_chunk_header(buf, 'Mat1', 0, 8, 4, 3, len(mat1_data))
    buf.extend(mat1_data)

    # --- END chunk ---
    write_end_chunk(buf)

    return bytes(buf)


def generate_full_scene_binary_cob():
    """Generate a full binary COB scene with mesh, materials, textures, lights, camera, holes."""
    buf = bytearray()
    write_header(buf)

    # --- Grou chunk (root group, id=1, parent=0) ---
    grou_data = bytearray()
    write_basic_node_info(grou_data, "Scene")
    write_chunk_header(buf, 'Grou', 0, 1, 1, 0, len(grou_data))
    buf.extend(grou_data)

    # --- Unit chunk (id=2, parent=1) ---
    unit_data = struct.pack('<H', 0)  # Units = 0 (millimeters)
    write_chunk_header(buf, 'Unit', 0, 1, 2, 1, len(unit_data))
    buf.extend(unit_data)

    # --- PolH chunk (mesh with holes, id=3, parent=1) ---
    polh_data = bytearray()
    write_basic_node_info(polh_data, "MeshWithHoles")

    # 6 vertices: a quad + extra vertex for hole
    vertices = [
        (-2.0, -2.0, 0.0), (2.0, -2.0, 0.0),
        (2.0, 2.0, 0.0), (-2.0, 2.0, 0.0),
        (-0.5, -0.5, 0.0), (0.5, 0.5, 0.0),
    ]
    polh_data.extend(struct.pack('<I', len(vertices)))
    for v in vertices:
        polh_data.extend(struct.pack('<fff', *v))

    # 6 texture coords
    tex_coords = [
        (0.0, 0.0), (1.0, 0.0), (1.0, 1.0),
        (0.0, 1.0), (0.25, 0.25), (0.75, 0.75),
    ]
    polh_data.extend(struct.pack('<I', len(tex_coords)))
    for tc in tex_coords:
        polh_data.extend(struct.pack('<ff', *tc))

    # 2 faces: one normal quad + one hole
    polh_data.extend(struct.pack('<I', 2))

    # Face 1: normal quad (4 vertices, material 0)
    polh_data.extend(struct.pack('<B', 0))  # flags: not hole
    polh_data.extend(struct.pack('<H', 4))  # 4 indices
    polh_data.extend(struct.pack('<H', 0))  # material 0
    for i in range(4):
        polh_data.extend(struct.pack('<II', i, i))

    # Face 2: hole (inner triangle, gets reversed and appended to previous face)
    polh_data.extend(struct.pack('<B', 0x08))  # flags: is a hole
    polh_data.extend(struct.pack('<H', 3))  # 3 indices
    # No material for holes
    hole_verts = [(4, 4), (5, 5), (0, 0)]
    for pos_idx, uv_idx in hole_verts:
        polh_data.extend(struct.pack('<II', pos_idx, uv_idx))

    # draw_flags (version > 4)
    polh_data.extend(struct.pack('<I', 0x01 | 0x02))  # SOLID | TRANS

    # Extra uint32 for 5 < version < 8
    polh_data.extend(struct.pack('<I', 0))

    # Use version 0.7 (= 7) to trigger draw_flags and extra data
    write_chunk_header(buf, 'PolH', 0, 7, 3, 1, len(polh_data))
    buf.extend(polh_data)

    # --- Mat1 chunk with textures (id=5, parent=3) ---
    mat1_data = bytearray()
    mat1_data.extend(struct.pack('<H', 0))  # matnum = 0
    mat1_data.extend(b'm')  # shader = metal
    mat1_data.extend(b'a')  # autofacet = autofaceted
    mat1_data.extend(struct.pack('<B', 60))  # autofacet_angle
    mat1_data.extend(struct.pack('<fff', 0.9, 0.7, 0.3))  # rgb
    mat1_data.extend(struct.pack('<f', 0.85))  # alpha
    mat1_data.extend(struct.pack('<f', 0.4))  # ka
    mat1_data.extend(struct.pack('<f', 0.8))  # ks
    mat1_data.extend(struct.pack('<f', 64.0))  # exp
    mat1_data.extend(struct.pack('<f', 1.33))  # ior

    # Environment texture
    mat1_data.extend(b'e:')
    mat1_data.extend(struct.pack('<B', 0))  # unknown byte
    env_path = "environment.bmp"
    mat1_data.extend(struct.pack('<H', len(env_path)))
    mat1_data.extend(env_path.encode('ascii'))

    # Color/diffuse texture
    mat1_data.extend(b't:')
    mat1_data.extend(struct.pack('<B', 0))  # unknown byte
    tex_path = "diffuse.tga"
    mat1_data.extend(struct.pack('<H', len(tex_path)))
    mat1_data.extend(tex_path.encode('ascii'))
    # UV transform: translation(x,y), scaling(x,y)
    mat1_data.extend(struct.pack('<ffff', 0.0, 0.0, 1.0, 1.0))

    # Bump texture
    mat1_data.extend(b'b:')
    mat1_data.extend(struct.pack('<B', 0))  # unknown byte
    bump_path = "bump.tga"
    mat1_data.extend(struct.pack('<H', len(bump_path)))
    mat1_data.extend(bump_path.encode('ascii'))
    # UV transform: translation(x,y), scaling(x,y)
    mat1_data.extend(struct.pack('<ffff', 0.1, 0.2, 2.0, 2.0))
    # Bump amplitude
    mat1_data.extend(struct.pack('<f', 1.0))

    # After bump, reader does IncPtr(-2), so we need 2 dummy bytes
    mat1_data.extend(b'\x00\x00')

    write_chunk_header(buf, 'Mat1', 0, 8, 5, 3, len(mat1_data))
    buf.extend(mat1_data)

    # --- Lght chunk (light, id=6, parent=1) ---
    lght_data = bytearray()
    write_basic_node_info(lght_data, "SpotLight")
    write_chunk_header(buf, 'Lght', 0, 2, 6, 1, len(lght_data))
    buf.extend(lght_data)

    # --- Came chunk (camera, id=7, parent=1) ---
    came_data = bytearray()
    write_basic_node_info(came_data, "MainCamera")
    # Version 0.2 has extra data: if GetI2() == 512, skip 42 bytes
    came_data.extend(struct.pack('<H', 512))
    came_data.extend(b'\x00' * 42)
    write_chunk_header(buf, 'Came', 0, 2, 7, 1, len(came_data))
    buf.extend(came_data)

    # --- Second Grou (nested group, id=8, parent=1) ---
    grou2_data = bytearray()
    write_basic_node_info(grou2_data, "SubGroup")
    write_chunk_header(buf, 'Grou', 0, 2, 8, 1, len(grou2_data))
    buf.extend(grou2_data)

    # --- Second PolH (triangle mesh, id=9, parent=8) with version 0.4 (no draw_flags) ---
    polh2_data = bytearray()
    write_basic_node_info(polh2_data, "Triangle")

    vertices2 = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 1.0, 0.0)]
    polh2_data.extend(struct.pack('<I', len(vertices2)))
    for v in vertices2:
        polh2_data.extend(struct.pack('<fff', *v))

    tex_coords2 = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
    polh2_data.extend(struct.pack('<I', len(tex_coords2)))
    for tc in tex_coords2:
        polh2_data.extend(struct.pack('<ff', *tc))

    # 1 face: triangle
    polh2_data.extend(struct.pack('<I', 1))
    polh2_data.extend(struct.pack('<B', 0))  # not hole
    polh2_data.extend(struct.pack('<H', 3))  # 3 indices
    polh2_data.extend(struct.pack('<H', 0))  # material 0
    for i in range(3):
        polh2_data.extend(struct.pack('<II', i, i))
    # Version 0.4 => no draw_flags

    write_chunk_header(buf, 'PolH', 0, 4, 9, 8, len(polh2_data))
    buf.extend(polh2_data)

    # --- Mat1 for second mesh (id=10, parent=9) - flat shader, no textures ---
    mat2_data = bytearray()
    mat2_data.extend(struct.pack('<H', 0))  # matnum = 0
    mat2_data.extend(b'f')  # shader = flat
    mat2_data.extend(b'f')  # autofacet = faceted
    mat2_data.extend(struct.pack('<B', 0))  # autofacet_angle
    mat2_data.extend(struct.pack('<fff', 0.2, 0.6, 0.9))  # rgb
    mat2_data.extend(struct.pack('<f', 1.0))  # alpha
    mat2_data.extend(struct.pack('<f', 0.5))  # ka
    mat2_data.extend(struct.pack('<f', 0.5))  # ks
    mat2_data.extend(struct.pack('<f', 16.0))  # exp
    mat2_data.extend(struct.pack('<f', 1.0))  # ior
    mat2_data.extend(b'xx')  # no textures
    write_chunk_header(buf, 'Mat1', 0, 1, 10, 9, len(mat2_data))
    buf.extend(mat2_data)

    # --- BitM chunk (id=11, parent=0) ---
    bitm_data = bytearray()
    # ThumbNailHdrSize must match sizeof(Bitmap::BitmapHeader) which is 1 (empty struct in C++ = 1 byte)
    # Actually, looking at ReadBitM_Binary: it reads a uint32 len, skips len bytes,
    # reads another uint32, then skips that many bytes.
    thumb_data = b'\x00' * 8  # small thumbnail placeholder
    bitm_data.extend(struct.pack('<I', len(thumb_data)))  # len
    bitm_data.extend(thumb_data)
    bitm_data.extend(struct.pack('<I', 4))  # second len
    bitm_data.extend(b'\x00' * 4)
    write_chunk_header(buf, 'BitM', 0, 1, 11, 0, len(bitm_data))
    buf.extend(bitm_data)

    # --- OLay chunk (layer, id=12, parent=0) - tests the OLay skip path ---
    olay_data = b'\x00' * 4
    write_chunk_header(buf, 'OLay', 0, 1, 12, 0, len(olay_data))
    buf.extend(olay_data)

    # --- END chunk ---
    write_end_chunk(buf)

    return bytes(buf)


def generate_multi_material_binary_cob():
    """Generate a binary COB with multiple materials and shader types."""
    buf = bytearray()
    write_header(buf)

    # --- Grou chunk ---
    grou_data = bytearray()
    write_basic_node_info(grou_data, "root")
    write_chunk_header(buf, 'Grou', 0, 1, 1, 0, len(grou_data))
    buf.extend(grou_data)

    # --- PolH chunk (mesh with faces using different materials) ---
    polh_data = bytearray()
    write_basic_node_info(polh_data, "MultiMatMesh")

    vertices = [
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0), (0.5, 0.5, 1.0),
    ]
    polh_data.extend(struct.pack('<I', len(vertices)))
    for v in vertices:
        polh_data.extend(struct.pack('<fff', *v))

    tex_coords = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.5, 0.5)]
    polh_data.extend(struct.pack('<I', len(tex_coords)))
    for tc in tex_coords:
        polh_data.extend(struct.pack('<ff', *tc))

    # 4 faces with different materials
    faces = [
        (0, [(0, 0), (1, 1), (2, 2)]),      # mat 0
        (1, [(0, 0), (2, 2), (3, 3)]),      # mat 1
        (2, [(0, 0), (1, 1), (4, 4)]),      # mat 2
        (0, [(2, 2), (3, 3), (4, 4)]),      # mat 0 again
    ]
    polh_data.extend(struct.pack('<I', len(faces)))
    for mat_idx, indices in faces:
        polh_data.extend(struct.pack('<B', 0))  # not hole
        polh_data.extend(struct.pack('<H', len(indices)))
        polh_data.extend(struct.pack('<H', mat_idx))
        for pos_idx, uv_idx in indices:
            polh_data.extend(struct.pack('<II', pos_idx, uv_idx))

    # draw_flags for version > 4
    polh_data.extend(struct.pack('<I', 0x04))  # WIRED

    write_chunk_header(buf, 'PolH', 0, 5, 2, 1, len(polh_data))
    buf.extend(polh_data)

    # --- Mat1 #0: flat shader ---
    mat0_data = bytearray()
    mat0_data.extend(struct.pack('<H', 0))
    mat0_data.extend(b'f')  # flat
    mat0_data.extend(b'f')  # faceted
    mat0_data.extend(struct.pack('<B', 0))
    mat0_data.extend(struct.pack('<fff', 1.0, 0.0, 0.0))  # red
    mat0_data.extend(struct.pack('<f', 1.0))  # alpha
    mat0_data.extend(struct.pack('<f', 0.2))  # ka
    mat0_data.extend(struct.pack('<f', 0.3))  # ks
    mat0_data.extend(struct.pack('<f', 8.0))  # exp
    mat0_data.extend(struct.pack('<f', 1.0))  # ior
    mat0_data.extend(b'xx')
    write_chunk_header(buf, 'Mat1', 0, 1, 3, 2, len(mat0_data))
    buf.extend(mat0_data)

    # --- Mat1 #1: phong shader ---
    mat1_data = bytearray()
    mat1_data.extend(struct.pack('<H', 1))
    mat1_data.extend(b'p')  # phong
    mat1_data.extend(b's')  # smooth
    mat1_data.extend(struct.pack('<B', 30))
    mat1_data.extend(struct.pack('<fff', 0.0, 1.0, 0.0))  # green
    mat1_data.extend(struct.pack('<f', 0.8))
    mat1_data.extend(struct.pack('<f', 0.3))
    mat1_data.extend(struct.pack('<f', 0.6))
    mat1_data.extend(struct.pack('<f', 48.0))
    mat1_data.extend(struct.pack('<f', 1.2))
    mat1_data.extend(b'xx')
    write_chunk_header(buf, 'Mat1', 0, 1, 4, 2, len(mat1_data))
    buf.extend(mat1_data)

    # --- Mat1 #2: metal shader with color texture ---
    mat2_data = bytearray()
    mat2_data.extend(struct.pack('<H', 2))
    mat2_data.extend(b'm')  # metal
    mat2_data.extend(b'a')  # autofaceted
    mat2_data.extend(struct.pack('<B', 90))
    mat2_data.extend(struct.pack('<fff', 0.0, 0.0, 1.0))  # blue
    mat2_data.extend(struct.pack('<f', 0.9))
    mat2_data.extend(struct.pack('<f', 0.1))
    mat2_data.extend(struct.pack('<f', 0.9))
    mat2_data.extend(struct.pack('<f', 128.0))
    mat2_data.extend(struct.pack('<f', 2.0))
    # Color texture only (no env, no bump)
    mat2_data.extend(b't:')
    mat2_data.extend(struct.pack('<B', 0))
    tex_path = "metal.tga"
    mat2_data.extend(struct.pack('<H', len(tex_path)))
    mat2_data.extend(tex_path.encode('ascii'))
    mat2_data.extend(struct.pack('<ffff', 0.0, 0.0, 1.0, 1.0))
    # End marker that doesn't match b: or any texture id
    mat2_data.extend(b'xx')
    write_chunk_header(buf, 'Mat1', 0, 8, 5, 2, len(mat2_data))
    buf.extend(mat2_data)

    # --- Unit chunk ---
    unit_data = struct.pack('<H', 4)  # inches
    write_chunk_header(buf, 'Unit', 0, 1, 6, 1, len(unit_data))
    buf.extend(unit_data)

    # --- END chunk ---
    write_end_chunk(buf)

    return bytes(buf)


def generate_lights_cameras_binary_cob():
    """Generate binary COB with lights and cameras to cover Lght_Binary and Came_Binary."""
    buf = bytearray()
    write_header(buf)

    # --- Root group ---
    grou_data = bytearray()
    write_basic_node_info(grou_data, "root")
    write_chunk_header(buf, 'Grou', 0, 1, 1, 0, len(grou_data))
    buf.extend(grou_data)

    # --- Mesh so the scene isn't empty ---
    polh_data = bytearray()
    write_basic_node_info(polh_data, "Plane")
    vertices = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)]
    polh_data.extend(struct.pack('<I', len(vertices)))
    for v in vertices:
        polh_data.extend(struct.pack('<fff', *v))
    tex_coords = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
    polh_data.extend(struct.pack('<I', len(tex_coords)))
    for tc in tex_coords:
        polh_data.extend(struct.pack('<ff', *tc))
    polh_data.extend(struct.pack('<I', 1))  # 1 face
    polh_data.extend(struct.pack('<B', 0))  # not hole
    polh_data.extend(struct.pack('<H', 3))  # 3 indices
    polh_data.extend(struct.pack('<H', 0))  # material 0
    for i in range(3):
        polh_data.extend(struct.pack('<II', i, i))
    write_chunk_header(buf, 'PolH', 0, 4, 2, 1, len(polh_data))
    buf.extend(polh_data)

    # Mat1 for the mesh
    mat_data = bytearray()
    mat_data.extend(struct.pack('<H', 0))
    mat_data.extend(b'f')
    mat_data.extend(b'f')
    mat_data.extend(struct.pack('<B', 0))
    mat_data.extend(struct.pack('<fff', 0.5, 0.5, 0.5))
    mat_data.extend(struct.pack('<f', 1.0))
    mat_data.extend(struct.pack('<f', 0.3))
    mat_data.extend(struct.pack('<f', 0.5))
    mat_data.extend(struct.pack('<f', 16.0))
    mat_data.extend(struct.pack('<f', 1.0))
    mat_data.extend(b'xx')
    write_chunk_header(buf, 'Mat1', 0, 1, 3, 2, len(mat_data))
    buf.extend(mat_data)

    # --- Light 1 (version 0.1) ---
    lght1_data = bytearray()
    write_basic_node_info(lght1_data, "Light1")
    write_chunk_header(buf, 'Lght', 0, 1, 4, 1, len(lght1_data))
    buf.extend(lght1_data)

    # --- Light 2 (version 0.2) ---
    lght2_data = bytearray()
    write_basic_node_info(lght2_data, "Light2")
    write_chunk_header(buf, 'Lght', 0, 2, 5, 1, len(lght2_data))
    buf.extend(lght2_data)

    # --- Camera 1 (version 0.1, no extra data) ---
    came1_data = bytearray()
    write_basic_node_info(came1_data, "Camera1")
    write_chunk_header(buf, 'Came', 0, 1, 6, 1, len(came1_data))
    buf.extend(came1_data)

    # --- Camera 2 (version 0.2 with 512 check) ---
    came2_data = bytearray()
    write_basic_node_info(came2_data, "Camera2")
    came2_data.extend(struct.pack('<H', 512))
    came2_data.extend(b'\x00' * 42)
    write_chunk_header(buf, 'Came', 0, 2, 7, 1, len(came2_data))
    buf.extend(came2_data)

    # --- Camera 3 (version 0.2 without 512, different path) ---
    came3_data = bytearray()
    write_basic_node_info(came3_data, "Camera3")
    came3_data.extend(struct.pack('<H', 256))  # != 512, so no extra skip
    write_chunk_header(buf, 'Came', 0, 2, 8, 1, len(came3_data))
    buf.extend(came3_data)

    # --- END ---
    write_end_chunk(buf)

    return bytes(buf)


def main():
    os.makedirs(SEED_DIR, exist_ok=True)

    seeds = {
        'seed_binary_basic.cob': generate_basic_binary_cob,
        'seed_binary_full_scene.cob': generate_full_scene_binary_cob,
        'seed_binary_multi_material.cob': generate_multi_material_binary_cob,
        'seed_binary_lights_cameras.cob': generate_lights_cameras_binary_cob,
    }

    for name, generator in seeds.items():
        path = os.path.join(SEED_DIR, name)
        data = generator()
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  Created {name} ({len(data)} bytes)")

    print(f"\nTotal binary COB seeds created in {SEED_DIR}")


if __name__ == '__main__':
    main()
