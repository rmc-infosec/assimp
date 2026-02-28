#!/usr/bin/env python3
"""Generate glTF2 seed files with morph targets and metadata for fuzz testing.

These seeds target uncovered regions in the glTF2 exporter:
- Lines 250-399: ExportDataSparse / NZDiff (morph target sparse export)
- Lines 442-484: ExportNodeExtras (metadata export)
- Lines 1352-1412: Morph target export with positions and normals
"""

import json
import struct
import base64
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', 'test', 'models', 'glTF2', 'fuzz_seeds')


def make_buffer_uri(data):
    """Create a data URI for binary buffer data."""
    return "data:application/octet-stream;base64," + base64.b64encode(data).decode()


def float_bytes(*values):
    """Pack float values to bytes."""
    return struct.pack(f'<{len(values)}f', *values)


def ushort_bytes(*values):
    """Pack unsigned short values to bytes."""
    return struct.pack(f'<{len(values)}H', *values)


def pad_to_4(data):
    """Pad data to 4-byte alignment."""
    remainder = len(data) % 4
    if remainder:
        data += b'\x00' * (4 - remainder)
    return data


def generate_morph_with_metadata():
    """Generate a glTF2 file with morph targets (positions + normals) and node metadata.

    This exercises:
    - ExportNodeExtras (lines 442-484): node extras with bool, int, float, string, nested
    - Morph target position export (lines 1365-1384)
    - Morph target normal export (lines 1388-1407) when GLTF2_TARGET_NORMAL_EXP is set
    - ExportDataSparse (lines 318-398) when GLTF2_SPARSE_ACCESSOR_EXP is set
    - NZDiff (lines 249-298) for sparse morph data
    """
    # Triangle: 3 vertices
    # Positions
    positions = float_bytes(
        -1.0, -1.0, 0.0,
         1.0, -1.0, 0.0,
         0.0,  1.0, 0.0,
    )
    # Normals (all pointing +Z)
    normals = float_bytes(
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
    )

    # Morph target 1: sparse displacement (only vertex 0 and 2 move)
    # This is the key: some vertices have zero displacement, triggering NZDiff sparse logic
    morph1_pos = float_bytes(
        0.1, 0.0, 0.0,   # vertex 0 moves
        0.0, 0.0, 0.0,   # vertex 1 stays (zero diff -> sparse)
        0.0, 0.1, 0.0,   # vertex 2 moves
    )
    morph1_norm = float_bytes(
        0.1, 0.0, 0.0,   # normal delta for vertex 0
        0.0, 0.0, 0.0,   # no change for vertex 1
       -0.1, 0.0, 0.0,   # normal delta for vertex 2
    )

    # Morph target 2: different displacement pattern
    morph2_pos = float_bytes(
        0.0, 0.0, 0.0,    # vertex 0 stays (zero diff)
       -0.2, 0.0, 0.0,    # vertex 1 moves
        0.0, -0.1, 0.0,   # vertex 2 moves
    )
    morph2_norm = float_bytes(
        0.0, 0.0, 0.0,    # no change for vertex 0
        0.0, 0.1, 0.0,    # normal delta for vertex 1
        0.0, -0.1, 0.0,   # normal delta for vertex 2
    )

    # Indices for one triangle
    indices = ushort_bytes(0, 1, 2)

    # Build buffer with proper alignment
    buf = positions + normals + morph1_pos + morph1_norm + morph2_pos + morph2_norm
    idx_offset = len(buf)
    idx_data = pad_to_4(indices)
    buf += idx_data

    gltf = {
        "asset": {"version": "2.0", "generator": "fuzz_seed_morph_metadata"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{
            "mesh": 0,
            "name": "MorphMetadataNode",
            "extras": {
                "custom_bool": True,
                "custom_int": 42,
                "custom_float": 3.14159,
                "custom_string": "hello world",
                "nested_metadata": {
                    "sub_int": 100,
                    "sub_string": "nested value",
                    "sub_bool": False,
                    "deeply_nested": {
                        "deep_float": 2.718,
                        "deep_string": "deep"
                    }
                }
            }
        }],
        "meshes": [{
            "name": "MorphMesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 6,
                "targets": [
                    {"POSITION": 2, "NORMAL": 3},
                    {"POSITION": 4, "NORMAL": 5}
                ]
            }],
            "weights": [0.5, 0.3],
            "extras": {"targetNames": ["SmileMorph", "FrownMorph"]}
        }],
        "accessors": [
            # 0: positions
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1.0, 1.0, 0.0], "min": [-1.0, -1.0, 0.0]},
            # 1: normals
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            # 2: morph1 position deltas
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC3"},
            # 3: morph1 normal deltas
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC3"},
            # 4: morph2 position deltas
            {"bufferView": 4, "componentType": 5126, "count": 3, "type": "VEC3"},
            # 5: morph2 normal deltas
            {"bufferView": 5, "componentType": 5126, "count": 3, "type": "VEC3"},
            # 6: indices
            {"bufferView": 6, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0,   "byteLength": 36, "target": 34962},   # positions
            {"buffer": 0, "byteOffset": 36,  "byteLength": 36, "target": 34962},   # normals
            {"buffer": 0, "byteOffset": 72,  "byteLength": 36},                     # morph1 pos
            {"buffer": 0, "byteOffset": 108, "byteLength": 36},                     # morph1 norm
            {"buffer": 0, "byteOffset": 144, "byteLength": 36},                     # morph2 pos
            {"buffer": 0, "byteOffset": 180, "byteLength": 36},                     # morph2 norm
            {"buffer": 0, "byteOffset": idx_offset, "byteLength": 6, "target": 34963},  # indices
        ],
        "buffers": [{"uri": make_buffer_uri(buf), "byteLength": len(buf)}]
    }

    return gltf


def generate_morph_many_vertices():
    """Generate a glTF2 file with morph targets on a larger mesh.

    More vertices means more interesting sparse patterns and better coverage
    of NZDiff loops. Uses a 4x4 grid (16 vertices, 18 triangles).
    Only a few vertices have non-zero morph displacement, making sparse
    encoding more efficient and exercising the sparse code path well.
    """
    # 4x4 grid of vertices
    verts = []
    norms = []
    for row in range(4):
        for col in range(4):
            x = col / 3.0 * 2.0 - 1.0
            y = row / 3.0 * 2.0 - 1.0
            verts.extend([x, y, 0.0])
            norms.extend([0.0, 0.0, 1.0])

    positions = struct.pack(f'<{len(verts)}f', *verts)
    normals = struct.pack(f'<{len(norms)}f', *norms)

    # Morph target: only 3 of 16 vertices move (sparse!)
    morph_pos = [0.0] * (16 * 3)
    morph_pos[0 * 3 + 0] = 0.1   # vertex 0 X
    morph_pos[5 * 3 + 1] = 0.2   # vertex 5 Y
    morph_pos[15 * 3 + 0] = -0.1  # vertex 15 X
    morph_pos_data = struct.pack(f'<{len(morph_pos)}f', *morph_pos)

    morph_norm = [0.0] * (16 * 3)
    morph_norm[0 * 3 + 0] = 0.05
    morph_norm[5 * 3 + 1] = 0.05
    morph_norm[15 * 3 + 2] = -0.05
    morph_norm_data = struct.pack(f'<{len(morph_norm)}f', *morph_norm)

    # Generate triangle indices for 3x3 grid of quads (each quad = 2 triangles)
    idx_list = []
    for row in range(3):
        for col in range(3):
            v0 = row * 4 + col
            v1 = v0 + 1
            v2 = v0 + 4
            v3 = v2 + 1
            idx_list.extend([v0, v1, v2, v1, v3, v2])
    indices = struct.pack(f'<{len(idx_list)}H', *idx_list)

    buf = positions + normals + morph_pos_data + morph_norm_data
    idx_offset = len(buf)
    idx_padded = pad_to_4(indices)
    buf += idx_padded

    gltf = {
        "asset": {"version": "2.0", "generator": "fuzz_seed_sparse_morph"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{
            "mesh": 0,
            "name": "SparseGrid",
            "extras": {
                "vertex_count": 16,
                "grid_size": "4x4",
                "is_sparse_test": True
            }
        }],
        "meshes": [{
            "name": "GridMesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 4,
                "targets": [
                    {"POSITION": 2, "NORMAL": 3}
                ]
            }],
            "weights": [0.7],
            "extras": {"targetNames": ["SparseDisplacement"]}
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 16, "type": "VEC3",
             "max": [1.0, 1.0, 0.0], "min": [-1.0, -1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 16, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 16, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5126, "count": 16, "type": "VEC3"},
            {"bufferView": 4, "componentType": 5123, "count": len(idx_list), "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 16 * 12, "target": 34962},
            {"buffer": 0, "byteOffset": 16 * 12, "byteLength": 16 * 12, "target": 34962},
            {"buffer": 0, "byteOffset": 16 * 12 * 2, "byteLength": 16 * 12},
            {"buffer": 0, "byteOffset": 16 * 12 * 3, "byteLength": 16 * 12},
            {"buffer": 0, "byteOffset": idx_offset, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_buffer_uri(buf), "byteLength": len(buf)}]
    }

    return gltf


def generate_metadata_types():
    """Generate a glTF2 file focused on metadata/extras variety.

    This exercises ExportNodeExtras with all metadata types:
    - AI_BOOL, AI_INT32, AI_UINT64, AI_FLOAT, AI_DOUBLE, AI_AISTRING, AI_AIMETADATA
    Multiple nodes each have different extras to maximize coverage.
    """
    # Minimal triangle
    positions = float_bytes(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.5, 1.0, 0.0)
    normals = float_bytes(0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0)
    indices = ushort_bytes(0, 1, 2)

    buf = positions + normals + pad_to_4(indices)

    gltf = {
        "asset": {"version": "2.0", "generator": "fuzz_seed_metadata"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [
            {
                "name": "RootWithExtras",
                "children": [1, 2],
                "extras": {
                    "bool_true": True,
                    "bool_false": False,
                    "int_zero": 0,
                    "int_positive": 12345,
                    "int_negative": -999,
                    "float_pi": 3.14159265,
                    "float_negative": -2.5,
                    "float_tiny": 0.00001,
                    "string_empty": "",
                    "string_ascii": "Hello Assimp World",
                    "string_special": "path/to/file.ext",
                    "nested_level1": {
                        "level1_int": 1,
                        "level1_string": "one",
                        "nested_level2": {
                            "level2_bool": True,
                            "level2_float": 99.99
                        }
                    }
                }
            },
            {
                "name": "ChildWithMesh",
                "mesh": 0,
                "extras": {
                    "material_id": 42,
                    "visible": True,
                    "label": "mesh_child"
                }
            },
            {
                "name": "EmptyChild",
                "extras": {
                    "purpose": "placeholder",
                    "weight": 0.0
                }
            }
        ],
        "meshes": [{
            "name": "SimpleTri",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 2
            }]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1.0, 1.0, 0.0], "min": [0.0, 0.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 72, "byteLength": 8, "target": 34963},
        ],
        "buffers": [{"uri": make_buffer_uri(buf), "byteLength": len(buf)}]
    }

    return gltf


def generate_animation_morph_weights():
    """Generate a glTF2 file with morph target animation.

    This tests the morph target weight animation path and ensures
    morph targets survive through the import pipeline even with animation data.
    """
    # Quad: 4 vertices, 2 triangles
    positions = float_bytes(
        -1.0, -1.0, 0.0,
         1.0, -1.0, 0.0,
         1.0,  1.0, 0.0,
        -1.0,  1.0, 0.0,
    )
    normals = float_bytes(
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
    )

    # Morph: move top vertices up
    morph_pos = float_bytes(
        0.0, 0.0, 0.0,   # no change
        0.0, 0.0, 0.0,   # no change
        0.0, 0.2, 0.0,   # move up
        0.0, 0.2, 0.0,   # move up
    )
    morph_norm = float_bytes(
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.1, 0.0,
        0.0, 0.1, 0.0,
    )

    indices = ushort_bytes(0, 1, 2, 0, 2, 3)

    # Animation data: 3 keyframes for weight
    anim_times = float_bytes(0.0, 0.5, 1.0)
    anim_weights = float_bytes(0.0, 1.0, 0.0)

    buf = positions + normals + morph_pos + morph_norm
    idx_offset = len(buf)
    buf += pad_to_4(indices)
    anim_time_offset = len(buf)
    buf += anim_times
    anim_weight_offset = len(buf)
    buf += anim_weights

    gltf = {
        "asset": {"version": "2.0", "generator": "fuzz_seed_anim_morph"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{
            "mesh": 0,
            "name": "AnimMorphNode",
            "extras": {
                "animation_type": "morph_weights",
                "duration": 1.0
            }
        }],
        "meshes": [{
            "name": "AnimMorphMesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 4,
                "targets": [
                    {"POSITION": 2, "NORMAL": 3}
                ]
            }],
            "weights": [0.0],
            "extras": {"targetNames": ["BulgeTop"]}
        }],
        "animations": [{
            "name": "MorphWeightAnim",
            "channels": [{
                "sampler": 0,
                "target": {"node": 0, "path": "weights"}
            }],
            "samplers": [{
                "input": 5,
                "output": 6,
                "interpolation": "LINEAR"
            }]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3",
             "max": [1.0, 1.0, 0.0], "min": [-1.0, -1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 4, "componentType": 5123, "count": 6, "type": "SCALAR"},
            {"bufferView": 5, "componentType": 5126, "count": 3, "type": "SCALAR",
             "max": [1.0], "min": [0.0]},
            {"bufferView": 6, "componentType": 5126, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 48, "target": 34962},
            {"buffer": 0, "byteOffset": 48, "byteLength": 48, "target": 34962},
            {"buffer": 0, "byteOffset": 96, "byteLength": 48},
            {"buffer": 0, "byteOffset": 144, "byteLength": 48},
            {"buffer": 0, "byteOffset": idx_offset, "byteLength": 12, "target": 34963},
            {"buffer": 0, "byteOffset": anim_time_offset, "byteLength": 12},
            {"buffer": 0, "byteOffset": anim_weight_offset, "byteLength": 12},
        ],
        "buffers": [{"uri": make_buffer_uri(buf), "byteLength": len(buf)}]
    }

    return gltf


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seeds = [
        ("29_morph_with_metadata.gltf", generate_morph_with_metadata,
         "Morph targets (2 targets, pos+norm) with node extras/metadata"),
        ("30_morph_sparse_grid.gltf", generate_morph_many_vertices,
         "16-vertex grid with sparse morph displacement (3 of 16 non-zero)"),
        ("31_metadata_variety.gltf", generate_metadata_types,
         "Multiple nodes with varied metadata types (bool, int, float, string, nested)"),
        ("32_anim_morph_weights.gltf", generate_animation_morph_weights,
         "Morph targets with weight animation and extras"),
    ]

    for filename, generator, description in seeds:
        gltf = generator()
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, 'w') as f:
            json.dump(gltf, f, separators=(',', ':'))
        size = os.path.getsize(path)
        print(f"  {filename} ({size} bytes): {description}")

    print(f"\nAll {len(seeds)} seed files written to {os.path.abspath(OUTPUT_DIR)}")


if __name__ == '__main__':
    main()
