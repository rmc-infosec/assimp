#!/usr/bin/env python3
"""Generate binary seed files for the Unreal file fuzzer (assimp_fuzzer_unreal_file).

The fuzzer splits input:
  bytes [0,1] = uint16 split_offset
  bytes [2, 2+split_offset) = _d.3d data
  bytes [2+split_offset, end) = _a.3d data

_d.3d format:
  uint16 numTris
  uint16 numVerts
  44 bytes padding/header
  per triangle (12 bytes each):
    uint16 vertex_idx[3]
    uint8 type
    uint8 color (padding)
    uint8 tex[3][2]  (6 bytes, UV coords)
    uint8 texnum
    uint8 flags (padding)

_a.3d format:
  uint16 numFrames
  uint16 recordSize (= numVerts * 4)
  per frame, per vertex (4 bytes each):
    int32 compressed_vertex (Unreal packed XYZ)
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test', 'models', '3D', 'fuzz_seeds')


def compress_vertex(x, y, z):
    """Compress vertex into Unreal 32-bit format.
    Format: 11 bits X, 11 bits Y, 10 bits Z (signed)."""
    # Clamp to range
    x = max(-1023, min(1023, int(x)))
    y = max(-1023, min(1023, int(y)))
    z = max(-511, min(511, int(z)))
    # Pack as signed values
    return (x & 0x7FF) | ((y & 0x7FF) << 11) | ((z & 0x3FF) << 22)


def make_seed(num_tris, num_verts, triangles, vertices, num_frames=1):
    """Create binary seed combining _d.3d and _a.3d data."""
    # Build _d.3d
    d_data = struct.pack('<HH', num_tris, num_verts)
    d_data += b'\x00' * 44  # padding

    for tri in triangles:
        v0, v1, v2, typ, texcoords, texnum = tri
        d_data += struct.pack('<HHH', v0, v1, v2)
        d_data += struct.pack('<BB', typ, 0)  # type + color
        for tc in texcoords:
            d_data += struct.pack('<B', tc)
        d_data += struct.pack('<BB', texnum, 0)  # texnum + flags

    # Build _a.3d
    a_data = struct.pack('<HH', num_frames, num_verts * 4)
    for frame in range(num_frames):
        for vx, vy, vz in vertices:
            # Add slight animation offset per frame
            cv = compress_vertex(vx + frame * 2, vy, vz)
            a_data += struct.pack('<I', cv)

    # Combine with split header
    split_offset = len(d_data)
    header = struct.pack('<H', split_offset)
    return header + d_data + a_data


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Seed 1: Basic - 1 triangle
    triangles = [
        # (v0, v1, v2, type, texcoords[6], texnum)
        (0, 1, 2, 0, [0, 0, 128, 0, 64, 128], 0),  # MF_NORMAL_OS
    ]
    vertices = [(0, 0, 0), (100, 0, 0), (50, 100, 0)]
    data = make_seed(1, 3, triangles, vertices)
    path = os.path.join(OUTPUT_DIR, 'seed_file_basic.bin')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Written {path} ({len(data)} bytes)")

    # Seed 2: Multi-type - exercises different material types
    # Type values:
    # 0 = MF_NORMAL_OS (one-sided)
    # 1 = MF_NORMAL_TS (two-sided)
    # 2 = MF_NORMAL_TRANS_TS (transparent two-sided)
    # 3 = MF_NORMAL_MOD_TS (modulated two-sided -> treated as two-sided)
    # 4 = MF_NORMAL_MASKED_TS (masked two-sided -> treated as two-sided)
    # 8 = MF_WEAPON_PLACEHOLDER
    triangles = [
        (0, 1, 2, 0, [0, 0, 255, 0, 128, 255], 0),    # Normal one-sided
        (0, 2, 3, 1, [0, 0, 128, 128, 255, 255], 0),   # Two-sided
        (0, 3, 4, 2, [0, 0, 64, 64, 128, 128], 1),     # Transparent
        (1, 2, 3, 3, [128, 0, 0, 128, 128, 255], 1),   # Modulated -> two-sided
        (2, 3, 4, 4, [0, 128, 128, 0, 255, 0], 2),     # Masked -> two-sided
        (3, 4, 5, 8, [0, 0, 0, 0, 0, 0], 0),           # Weapon placeholder
    ]
    vertices = [
        (0, 0, 0), (100, 0, 0), (100, 100, 0),
        (0, 100, 0), (50, 50, 100), (50, 50, -100),
    ]
    data = make_seed(6, 6, triangles, vertices, num_frames=2)
    path = os.path.join(OUTPUT_DIR, 'seed_file_multi_type.bin')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Written {path} ({len(data)} bytes)")


if __name__ == '__main__':
    main()
