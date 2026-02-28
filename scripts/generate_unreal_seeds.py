#!/usr/bin/env python3
"""Generate minimal valid Unreal .3d mesh seed files for fuzzing."""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test', 'models', '3D', 'fuzz_seeds')


def make_unreal_3d(num_polygons, vertices, triangles):
    """
    Create an Unreal .3d file.

    Format:
    - Header: numPolygons (uint16), numVertices (uint16)
    - Vertices: each is x(int16), y(int16), z(int16), pad(int16)
    - Triangles: each has vertex indices (uint16 x3), type(uint8), color(uint8),
                 texcoords (uint8 x6), texnum(uint8), flags(uint8)

    vertices: list of (x, y, z) tuples
    triangles: list of (idx0, idx1, idx2, type, color, texcoords, texnum, flags)
        where texcoords is a tuple of 6 uint8 values
    """
    num_vertices = len(vertices)
    data = struct.pack('<HH', num_polygons, num_vertices)

    # Vertices
    for (x, y, z) in vertices:
        data += struct.pack('<hhhh', x, y, z, 0)  # pad = 0

    # Triangles/Polygons
    for tri in triangles:
        idx0, idx1, idx2, typ, color, texcoords, texnum, flags = tri
        data += struct.pack('<HHH', idx0, idx1, idx2)
        data += struct.pack('<BB', typ, color)
        for tc in texcoords:
            data += struct.pack('<B', tc)
        data += struct.pack('<BB', texnum, flags)

    return data


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Seed 1: Basic - 1 triangle, 3 vertices
    vertices = [
        (0, 0, 0),
        (100, 0, 0),
        (50, 100, 0),
    ]
    triangles = [
        # idx0, idx1, idx2, type, color, texcoords(6), texnum, flags
        (0, 1, 2, 0, 1, (0, 0, 255, 0, 128, 255), 0, 0),
    ]
    data = make_unreal_3d(1, vertices, triangles)
    path = os.path.join(OUTPUT_DIR, 'seed_basic.3d')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Written {path} ({len(data)} bytes)")

    # Seed 2: Multi - 4 triangles, 6 vertices
    vertices = [
        (0, 0, 0),
        (100, 0, 0),
        (100, 100, 0),
        (0, 100, 0),
        (50, 50, 100),
        (50, 50, -100),
    ]
    triangles = [
        (0, 1, 2, 0, 1, (0, 0, 255, 0, 128, 255), 0, 0),
        (0, 2, 3, 0, 2, (0, 0, 128, 128, 255, 255), 0, 0),
        (0, 1, 4, 1, 3, (0, 0, 255, 0, 128, 128), 1, 0),
        (2, 3, 5, 1, 4, (128, 128, 0, 255, 255, 0), 1, 0),
    ]
    data = make_unreal_3d(4, vertices, triangles)
    path = os.path.join(OUTPUT_DIR, 'seed_multi.3d')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Written {path} ({len(data)} bytes)")


if __name__ == '__main__':
    main()
