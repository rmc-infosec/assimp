#!/usr/bin/env python3
"""Generate minimal .glb seed files with specific features for export fuzzer coverage.

Each seed targets a specific uncovered code path in FBXExporter, glTF2Exporter,
ColladaExporter, PbrtExporter, etc.
"""

import struct
import json
import base64
import os
import sys

def make_glb(gltf_json, bin_data=b""):
    """Pack a glTF JSON dict and optional binary data into a .glb file."""
    json_str = json.dumps(gltf_json, separators=(',', ':'))
    # Pad JSON to 4-byte boundary with spaces
    while len(json_str) % 4 != 0:
        json_str += ' '
    json_bytes = json_str.encode('utf-8')

    # Pad binary to 4-byte boundary with zeros
    bin_padded = bin_data
    while len(bin_padded) % 4 != 0:
        bin_padded += b'\x00'

    # GLB header: magic, version, total length
    total_length = 12  # header
    total_length += 8 + len(json_bytes)  # JSON chunk header + data
    if bin_padded:
        total_length += 8 + len(bin_padded)  # BIN chunk header + data

    out = struct.pack('<III', 0x46546C67, 2, total_length)
    # JSON chunk
    out += struct.pack('<II', len(json_bytes), 0x4E4F534A)
    out += json_bytes
    # BIN chunk
    if bin_padded:
        out += struct.pack('<II', len(bin_padded), 0x004E4942)
        out += bin_padded

    return out


def triangle_mesh_bin():
    """Return binary data for a simple triangle: positions + indices."""
    # 3 vertices: positions (vec3 float)
    positions = struct.pack('<9f',
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.5, 1.0, 0.0)
    # 1 triangle: indices (3x unsigned short)
    indices = struct.pack('<3H', 0, 1, 2)
    return positions, indices


def quad_mesh_bin():
    """Return binary data for a quad (2 triangles): positions + indices."""
    positions = struct.pack('<12f',
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 1.0, 0.0,
        0.0, 1.0, 0.0)
    normals = struct.pack('<12f',
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0)
    indices = struct.pack('<6H', 0, 1, 2, 0, 2, 3)
    return positions, normals, indices


def seed_camera(outdir):
    """Scene with a perspective camera."""
    positions, indices = triangle_mesh_bin()
    bin_data = positions + indices
    # Pad indices to 4 bytes
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    pos_len = len(positions)
    idx_len = len(indices)

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0, 1]}],
        "nodes": [
            {"mesh": 0, "name": "MeshNode"},
            {"camera": 0, "name": "CameraNode",
             "translation": [0.0, 0.0, 5.0]}
        ],
        "cameras": [{
            "type": "perspective",
            "perspective": {
                "aspectRatio": 1.5,
                "yfov": 0.7854,
                "znear": 0.1,
                "zfar": 100.0
            }
        }],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR",
             "min": [0], "max": [2]}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": pos_len, "byteLength": idx_len, "target": 34963}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_camera.glb"), 'wb') as f:
        f.write(data)


def seed_camera_ortho(outdir):
    """Scene with an orthographic camera."""
    positions, indices = triangle_mesh_bin()
    bin_data = positions + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    pos_len = len(positions)
    idx_len = len(indices)

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0, 1]}],
        "nodes": [
            {"mesh": 0, "name": "MeshNode"},
            {"camera": 0, "name": "OrthoCamera", "translation": [0.0, 0.0, 5.0]}
        ],
        "cameras": [{
            "type": "orthographic",
            "orthographic": {
                "xmag": 2.0,
                "ymag": 2.0,
                "znear": 0.1,
                "zfar": 100.0
            }
        }],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": pos_len, "byteLength": idx_len, "target": 34963}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_camera_ortho.glb"), 'wb') as f:
        f.write(data)


def seed_lights(outdir):
    """Scene with point, directional, and spot lights using KHR_lights_punctual."""
    positions, indices = triangle_mesh_bin()
    bin_data = positions + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    pos_len = len(positions)
    idx_len = len(indices)

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "extensionsUsed": ["KHR_lights_punctual"],
        "extensions": {
            "KHR_lights_punctual": {
                "lights": [
                    {"type": "point", "color": [1.0, 0.5, 0.0], "intensity": 100.0, "name": "PointLight",
                     "range": 50.0},
                    {"type": "directional", "color": [1.0, 1.0, 1.0], "intensity": 2.0, "name": "DirLight"},
                    {"type": "spot", "color": [0.0, 1.0, 0.5], "intensity": 200.0, "name": "SpotLight",
                     "range": 30.0,
                     "spot": {"innerConeAngle": 0.2, "outerConeAngle": 0.6}}
                ]
            }
        },
        "scene": 0,
        "scenes": [{"nodes": [0, 1, 2, 3]}],
        "nodes": [
            {"mesh": 0, "name": "MeshNode"},
            {"extensions": {"KHR_lights_punctual": {"light": 0}}, "name": "PointLightNode",
             "translation": [2.0, 2.0, 2.0]},
            {"extensions": {"KHR_lights_punctual": {"light": 1}}, "name": "DirLightNode",
             "rotation": [0.0, 0.707, 0.0, 0.707]},
            {"extensions": {"KHR_lights_punctual": {"light": 2}}, "name": "SpotLightNode",
             "translation": [0.0, 3.0, 0.0], "rotation": [0.707, 0.0, 0.0, 0.707]}
        ],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": pos_len, "byteLength": idx_len, "target": 34963}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_lights.glb"), 'wb') as f:
        f.write(data)


def seed_skinned(outdir):
    """Scene with a skinned mesh (2 bones, 4 vertices)."""
    # 4 vertices forming a vertical strip
    positions = struct.pack('<12f',
        -0.5, 0.0, 0.0,
         0.5, 0.0, 0.0,
        -0.5, 1.0, 0.0,
         0.5, 1.0, 0.0)
    # Joint indices: each vertex affected by joint 0 and/or joint 1
    joints = struct.pack('<16B',
        0, 1, 0, 0,  # vertex 0: joints 0,1
        0, 1, 0, 0,  # vertex 1: joints 0,1
        0, 1, 0, 0,  # vertex 2: joints 0,1
        0, 1, 0, 0)  # vertex 3: joints 0,1
    # Weights: bottom vertices mostly joint 0, top mostly joint 1
    weights = struct.pack('<16f',
        0.9, 0.1, 0.0, 0.0,
        0.9, 0.1, 0.0, 0.0,
        0.1, 0.9, 0.0, 0.0,
        0.1, 0.9, 0.0, 0.0)
    # Indices for 2 triangles
    indices = struct.pack('<6H', 0, 1, 2, 1, 3, 2)
    # Inverse bind matrices (2x mat4, identity)
    ibm = struct.pack('<32f',
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1,
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,-1,0,1)

    bin_data = positions + joints + weights + indices + ibm
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    off_pos = 0
    off_joints = len(positions)
    off_weights = off_joints + len(joints)
    off_indices = off_weights + len(weights)
    off_ibm = off_indices + len(indices)
    # Pad indices offset to 4 bytes
    idx_pad = (4 - (off_indices % 4)) % 4

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [
            {"name": "Armature", "children": [1, 3], "skin": 0},
            {"name": "Bone0", "children": [2], "translation": [0.0, 0.0, 0.0]},
            {"name": "Bone1", "translation": [0.0, 1.0, 0.0]},
            {"name": "SkinnedMesh", "mesh": 0}
        ],
        "skins": [{
            "joints": [1, 2],
            "skeleton": 1,
            "inverseBindMatrices": 4,
            "name": "ArmatureSkin"
        }],
        "meshes": [{"primitives": [{
            "attributes": {
                "POSITION": 0,
                "JOINTS_0": 1,
                "WEIGHTS_0": 2
            },
            "indices": 3
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3",
             "min": [-0.5, 0.0, 0.0], "max": [0.5, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5121, "count": 4, "type": "VEC4"},
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5123, "count": 6, "type": "SCALAR"},
            {"bufferView": 4, "componentType": 5126, "count": 2, "type": "MAT4"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": off_pos, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": off_joints, "byteLength": len(joints), "target": 34962},
            {"buffer": 0, "byteOffset": off_weights, "byteLength": len(weights), "target": 34962},
            {"buffer": 0, "byteOffset": off_indices, "byteLength": len(indices), "target": 34963},
            {"buffer": 0, "byteOffset": off_ibm, "byteLength": len(ibm)}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_skinned.glb"), 'wb') as f:
        f.write(data)


def seed_animation(outdir):
    """Scene with rotation animation on a node."""
    positions, indices = triangle_mesh_bin()
    # Animation data: 3 time keyframes + 3 rotation quaternions
    times = struct.pack('<3f', 0.0, 0.5, 1.0)
    rotations = struct.pack('<12f',
        0.0, 0.0, 0.0, 1.0,       # t=0: identity
        0.0, 0.707, 0.0, 0.707,    # t=0.5: 90 deg Y
        0.0, 0.0, 0.0, 1.0)        # t=1: identity

    bin_data = positions + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'
    anim_offset = len(bin_data)
    bin_data += times + rotations
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    pos_len = len(positions)
    idx_len = len(indices)

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "AnimatedNode"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "animations": [{
            "name": "Spin",
            "channels": [{
                "sampler": 0,
                "target": {"node": 0, "path": "rotation"}
            }],
            "samplers": [{
                "input": 2,
                "output": 3,
                "interpolation": "LINEAR"
            }]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "SCALAR",
             "min": [0.0], "max": [1.0]},
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC4"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": pos_len, "byteLength": idx_len, "target": 34963},
            {"buffer": 0, "byteOffset": anim_offset, "byteLength": len(times)},
            {"buffer": 0, "byteOffset": anim_offset + len(times), "byteLength": len(rotations)}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_animation.glb"), 'wb') as f:
        f.write(data)


def seed_morph_targets(outdir):
    """Scene with morph targets (blend shapes)."""
    # Base mesh: triangle
    positions = struct.pack('<9f',
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.5, 1.0, 0.0)
    normals = struct.pack('<9f',
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 1.0)
    # Morph target 0: displace vertex 2 upward
    morph0_pos = struct.pack('<9f',
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.5, 0.0)
    morph0_norm = struct.pack('<9f',
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0)
    # Morph target 1: widen base
    morph1_pos = struct.pack('<9f',
        -0.5, 0.0, 0.0,
         0.5, 0.0, 0.0,
         0.0, 0.0, 0.0)
    morph1_norm = struct.pack('<9f',
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0)
    indices = struct.pack('<3H', 0, 1, 2)

    bin_data = positions + normals + morph0_pos + morph0_norm + morph1_pos + morph1_norm + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    off = 0
    bv = []
    for name, data_chunk in [("pos", positions), ("norm", normals),
                              ("m0p", morph0_pos), ("m0n", morph0_norm),
                              ("m1p", morph1_pos), ("m1n", morph1_norm),
                              ("idx", indices)]:
        bv.append({"buffer": 0, "byteOffset": off, "byteLength": len(data_chunk),
                   "target": 34963 if name == "idx" else 34962})
        off += len(data_chunk)

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "MorphMesh"}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 6,
                "targets": [
                    {"POSITION": 2, "NORMAL": 3},
                    {"POSITION": 4, "NORMAL": 5}
                ]
            }],
            "weights": [0.5, 0.3],
            "extras": {"targetNames": ["Tall", "Wide"]}
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [-0.0, 0.0, 0.0], "max": [0.0, 0.5, 0.0]},
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 4, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [-0.5, 0.0, 0.0], "max": [0.5, 0.0, 0.0]},
            {"bufferView": 5, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 6, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": bv,
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_morph.glb"), 'wb') as f:
        f.write(data)


def seed_vertex_colors(outdir):
    """Scene with vertex colors."""
    positions = struct.pack('<9f',
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.5, 1.0, 0.0)
    colors = struct.pack('<12f',
        1.0, 0.0, 0.0, 1.0,  # red
        0.0, 1.0, 0.0, 1.0,  # green
        0.0, 0.0, 1.0, 1.0)  # blue
    indices = struct.pack('<3H', 0, 1, 2)

    bin_data = positions + colors + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "ColorMesh"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "COLOR_0": 1}, "indices": 2}]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC4"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(colors), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions) + len(colors), "byteLength": len(indices), "target": 34963}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_vertex_colors.glb"), 'wb') as f:
        f.write(data)


def seed_multi_material(outdir):
    """Scene with multiple materials and UV channels."""
    # 6 vertices (2 triangles, separate materials)
    positions = struct.pack('<18f',
        0.0, 0.0, 0.0,  1.0, 0.0, 0.0,  0.5, 1.0, 0.0,
        2.0, 0.0, 0.0,  3.0, 0.0, 0.0,  2.5, 1.0, 0.0)
    texcoords0 = struct.pack('<12f',
        0.0, 0.0,  1.0, 0.0,  0.5, 1.0,
        0.0, 0.0,  1.0, 0.0,  0.5, 1.0)
    texcoords1 = struct.pack('<12f',
        0.0, 1.0,  1.0, 1.0,  0.5, 0.0,
        0.0, 1.0,  1.0, 1.0,  0.5, 0.0)
    indices0 = struct.pack('<3H', 0, 1, 2)
    indices1 = struct.pack('<3H', 3, 4, 5)

    bin_data = positions + texcoords0 + texcoords1 + indices0
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'
    off_idx1 = len(bin_data)
    bin_data += indices1
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "MultiMatMesh"}],
        "materials": [
            {"name": "RedMat", "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 0.0, 0.0, 1.0],
                "metallicFactor": 0.5, "roughnessFactor": 0.5}},
            {"name": "BlueMat", "pbrMetallicRoughness": {
                "baseColorFactor": [0.0, 0.0, 1.0, 1.0],
                "metallicFactor": 0.0, "roughnessFactor": 1.0},
             "emissiveFactor": [0.2, 0.2, 0.2]}
        ],
        "meshes": [{"primitives": [
            {"attributes": {"POSITION": 0, "TEXCOORD_0": 1, "TEXCOORD_1": 2},
             "indices": 3, "material": 0},
            {"attributes": {"POSITION": 0, "TEXCOORD_0": 1, "TEXCOORD_1": 2},
             "indices": 4, "material": 1}
        ]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 6, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [3.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 6, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5126, "count": 6, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"},
            {"bufferView": 4, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(texcoords0), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions) + len(texcoords0), "byteLength": len(texcoords1), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions) + len(texcoords0) + len(texcoords1),
             "byteLength": len(indices0), "target": 34963},
            {"buffer": 0, "byteOffset": off_idx1, "byteLength": len(indices1), "target": 34963}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_multi_material.glb"), 'wb') as f:
        f.write(data)


def seed_embedded_texture(outdir):
    """Scene with an embedded tiny PNG texture."""
    positions = struct.pack('<9f',
        0.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        0.5, 1.0, 0.0)
    texcoords = struct.pack('<6f',
        0.0, 0.0,  1.0, 0.0,  0.5, 1.0)
    indices = struct.pack('<3H', 0, 1, 2)

    # Minimal 1x1 red PNG
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')

    bin_data = positions + texcoords + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'
    img_offset = len(bin_data)
    bin_data += png_data
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "TexturedMesh"}],
        "materials": [{
            "name": "TexturedMat",
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0},
                "metallicFactor": 0.0,
                "roughnessFactor": 1.0
            }
        }],
        "textures": [{"source": 0, "sampler": 0}],
        "images": [{"bufferView": 3, "mimeType": "image/png", "name": "embedded_tex"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(texcoords), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions) + len(texcoords), "byteLength": 6, "target": 34963},
            {"buffer": 0, "byteOffset": img_offset, "byteLength": len(png_data)}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_embedded_texture.glb"), 'wb') as f:
        f.write(data)


def seed_skinned_animated(outdir):
    """Scene with skinned mesh AND bone animation (high value for export coverage)."""
    # 4 vertices
    positions = struct.pack('<12f',
        -0.5, 0.0, 0.0,  0.5, 0.0, 0.0,
        -0.5, 1.0, 0.0,  0.5, 1.0, 0.0)
    normals = struct.pack('<12f',
        0.0, 0.0, 1.0,  0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,  0.0, 0.0, 1.0)
    joints = struct.pack('<16B',
        0, 1, 0, 0,  0, 1, 0, 0,
        0, 1, 0, 0,  0, 1, 0, 0)
    weights = struct.pack('<16f',
        1.0, 0.0, 0.0, 0.0,  1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,  0.0, 1.0, 0.0, 0.0)
    indices = struct.pack('<6H', 0, 1, 2, 1, 3, 2)
    ibm = struct.pack('<32f',
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1,
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,-1,0,1)
    # Animation: rotate bone1 over time
    times = struct.pack('<4f', 0.0, 0.33, 0.66, 1.0)
    rotations = struct.pack('<16f',
        0.0, 0.0, 0.0, 1.0,
        0.0, 0.0, 0.383, 0.924,
        0.0, 0.0, 0.707, 0.707,
        0.0, 0.0, 0.383, 0.924)
    # Translation animation for bone0
    translations = struct.pack('<12f',
        0.0, 0.0, 0.0,
        0.0, 0.1, 0.0,
        0.0, 0.0, 0.0,
        0.0, -0.1, 0.0)

    bin_data = (positions + normals + joints + weights + indices + ibm +
                times + rotations + translations)
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    off = 0
    sizes = [len(positions), len(normals), len(joints), len(weights),
             len(indices), len(ibm), len(times), len(rotations), len(translations)]
    offsets = []
    for s in sizes:
        offsets.append(off)
        off += s

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [
            {"name": "Root", "children": [1, 3]},
            {"name": "Bone0", "children": [2], "translation": [0.0, 0.0, 0.0]},
            {"name": "Bone1", "translation": [0.0, 1.0, 0.0]},
            {"name": "SkinnedMesh", "mesh": 0, "skin": 0}
        ],
        "skins": [{
            "joints": [1, 2],
            "skeleton": 1,
            "inverseBindMatrices": 5
        }],
        "animations": [{
            "name": "BoneAnim",
            "channels": [
                {"sampler": 0, "target": {"node": 2, "path": "rotation"}},
                {"sampler": 1, "target": {"node": 1, "path": "translation"}}
            ],
            "samplers": [
                {"input": 6, "output": 7, "interpolation": "LINEAR"},
                {"input": 6, "output": 8, "interpolation": "LINEAR"}
            ]
        }],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "JOINTS_0": 2, "WEIGHTS_0": 3},
            "indices": 4
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3",
             "min": [-0.5, 0.0, 0.0], "max": [0.5, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5121, "count": 4, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5126, "count": 4, "type": "VEC4"},
            {"bufferView": 4, "componentType": 5123, "count": 6, "type": "SCALAR"},
            {"bufferView": 5, "componentType": 5126, "count": 2, "type": "MAT4"},
            {"bufferView": 6, "componentType": 5126, "count": 4, "type": "SCALAR",
             "min": [0.0], "max": [1.0]},
            {"bufferView": 7, "componentType": 5126, "count": 4, "type": "VEC4"},
            {"bufferView": 8, "componentType": 5126, "count": 4, "type": "VEC3"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": offsets[0], "byteLength": sizes[0], "target": 34962},
            {"buffer": 0, "byteOffset": offsets[1], "byteLength": sizes[1], "target": 34962},
            {"buffer": 0, "byteOffset": offsets[2], "byteLength": sizes[2], "target": 34962},
            {"buffer": 0, "byteOffset": offsets[3], "byteLength": sizes[3], "target": 34962},
            {"buffer": 0, "byteOffset": offsets[4], "byteLength": sizes[4], "target": 34963},
            {"buffer": 0, "byteOffset": offsets[5], "byteLength": sizes[5]},
            {"buffer": 0, "byteOffset": offsets[6], "byteLength": sizes[6]},
            {"buffer": 0, "byteOffset": offsets[7], "byteLength": sizes[7]},
            {"buffer": 0, "byteOffset": offsets[8], "byteLength": sizes[8]}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_skinned_animated.glb"), 'wb') as f:
        f.write(data)


def seed_metadata(outdir):
    """Scene with node extras/metadata of various types."""
    positions, indices = triangle_mesh_bin()
    bin_data = positions + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{
            "mesh": 0,
            "name": "MetadataNode",
            "extras": {
                "boolVal": True,
                "intVal": 42,
                "floatVal": 3.14,
                "stringVal": "hello world",
                "arrayVal": [1, 2, 3],
                "nestedObj": {"key": "value"}
            }
        }],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(indices), "target": 34963}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_metadata.glb"), 'wb') as f:
        f.write(data)


def seed_material_extensions(outdir):
    """Scene with glTF2 material extensions (clearcoat, sheen, transmission, etc.)."""
    positions = struct.pack('<9f',
        0.0, 0.0, 0.0,  1.0, 0.0, 0.0,  0.5, 1.0, 0.0)
    normals = struct.pack('<9f',
        0.0, 0.0, 1.0,  0.0, 0.0, 1.0,  0.0, 0.0, 1.0)
    texcoords = struct.pack('<6f',
        0.0, 0.0,  1.0, 0.0,  0.5, 1.0)
    indices = struct.pack('<3H', 0, 1, 2)

    bin_data = positions + normals + texcoords + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "extensionsUsed": [
            "KHR_materials_clearcoat",
            "KHR_materials_sheen",
            "KHR_materials_transmission",
            "KHR_materials_volume",
            "KHR_materials_specular",
            "KHR_materials_ior",
            "KHR_materials_emissive_strength",
            "KHR_materials_unlit"
        ],
        "scene": 0,
        "scenes": [{"nodes": [0, 1, 2, 3]}],
        "nodes": [
            {"mesh": 0, "name": "ClearcoatMesh"},
            {"mesh": 1, "name": "SheenMesh", "translation": [2.0, 0.0, 0.0]},
            {"mesh": 2, "name": "TransmissionMesh", "translation": [4.0, 0.0, 0.0]},
            {"mesh": 3, "name": "SpecularMesh", "translation": [6.0, 0.0, 0.0]}
        ],
        "materials": [
            {
                "name": "ClearcoatMat",
                "pbrMetallicRoughness": {"baseColorFactor": [0.8, 0.1, 0.1, 1.0]},
                "extensions": {
                    "KHR_materials_clearcoat": {
                        "clearcoatFactor": 0.9,
                        "clearcoatRoughnessFactor": 0.1
                    }
                }
            },
            {
                "name": "SheenMat",
                "pbrMetallicRoughness": {"baseColorFactor": [0.2, 0.2, 0.8, 1.0]},
                "extensions": {
                    "KHR_materials_sheen": {
                        "sheenColorFactor": [1.0, 0.5, 0.0],
                        "sheenRoughnessFactor": 0.3
                    }
                }
            },
            {
                "name": "TransmissionMat",
                "pbrMetallicRoughness": {"baseColorFactor": [0.9, 0.9, 0.9, 1.0]},
                "extensions": {
                    "KHR_materials_transmission": {
                        "transmissionFactor": 0.8
                    },
                    "KHR_materials_volume": {
                        "thicknessFactor": 0.5,
                        "attenuationDistance": 1.0,
                        "attenuationColor": [0.8, 0.9, 1.0]
                    },
                    "KHR_materials_ior": {
                        "ior": 1.5
                    }
                }
            },
            {
                "name": "SpecularMat",
                "pbrMetallicRoughness": {"baseColorFactor": [0.5, 0.5, 0.5, 1.0]},
                "extensions": {
                    "KHR_materials_specular": {
                        "specularFactor": 0.8,
                        "specularColorFactor": [1.0, 0.8, 0.6]
                    },
                    "KHR_materials_emissive_strength": {
                        "emissiveStrength": 5.0
                    }
                },
                "emissiveFactor": [0.5, 0.3, 0.1]
            }
        ],
        "meshes": [
            {"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]},
            {"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 1}]},
            {"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 2}]},
            {"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 3}]}
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(normals), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions) + len(normals), "byteLength": len(texcoords), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions) + len(normals) + len(texcoords),
             "byteLength": len(indices), "target": 34963}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_material_extensions.glb"), 'wb') as f:
        f.write(data)


def seed_full_scene(outdir):
    """Kitchen sink: camera + lights + skinned mesh + animation + morph + vertex colors + metadata."""
    # 4 vertices for a skinned quad with vertex colors and morph targets
    positions = struct.pack('<12f',
        -0.5, 0.0, 0.0,  0.5, 0.0, 0.0,
        -0.5, 2.0, 0.0,  0.5, 2.0, 0.0)
    normals = struct.pack('<12f',
        0.0, 0.0, 1.0,  0.0, 0.0, 1.0,
        0.0, 0.0, 1.0,  0.0, 0.0, 1.0)
    colors = struct.pack('<16f',
        1.0, 0.0, 0.0, 1.0,  0.0, 1.0, 0.0, 1.0,
        0.0, 0.0, 1.0, 1.0,  1.0, 1.0, 0.0, 1.0)
    texcoords = struct.pack('<8f',
        0.0, 0.0,  1.0, 0.0,  0.0, 1.0,  1.0, 1.0)
    joints = struct.pack('<16B',
        0, 1, 0, 0,  0, 1, 0, 0,
        0, 1, 0, 0,  0, 1, 0, 0)
    weights = struct.pack('<16f',
        1.0, 0.0, 0.0, 0.0,  1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,  0.0, 1.0, 0.0, 0.0)
    indices = struct.pack('<6H', 0, 1, 2, 1, 3, 2)
    ibm = struct.pack('<32f',
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1,
        1,0,0,0, 0,1,0,0, 0,0,1,0, 0,-2,0,1)
    # Morph target: displace top vertices
    morph_pos = struct.pack('<12f',
        0.0, 0.0, 0.0,  0.0, 0.0, 0.0,
        0.0, 0.5, 0.0,  0.0, 0.5, 0.0)
    # Animation times + rotation for bone1
    anim_times = struct.pack('<3f', 0.0, 0.5, 1.0)
    anim_rots = struct.pack('<12f',
        0.0, 0.0, 0.0, 1.0,
        0.0, 0.0, 0.383, 0.924,
        0.0, 0.0, 0.0, 1.0)
    # Scale animation for morph weights
    anim_weights = struct.pack('<3f', 0.0, 1.0, 0.0)

    chunks = [positions, normals, colors, texcoords, joints, weights, indices,
              ibm, morph_pos, anim_times, anim_rots, anim_weights]

    bin_data = b""
    offsets = []
    for chunk in chunks:
        # Align to 4 bytes
        while len(bin_data) % 4 != 0:
            bin_data += b'\x00'
        offsets.append(len(bin_data))
        bin_data += chunk
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "extensionsUsed": ["KHR_lights_punctual"],
        "extensions": {
            "KHR_lights_punctual": {
                "lights": [
                    {"type": "point", "color": [1.0, 0.9, 0.8], "intensity": 50.0, "name": "PointLight"},
                    {"type": "spot", "color": [1.0, 1.0, 1.0], "intensity": 100.0, "name": "SpotLight",
                     "spot": {"innerConeAngle": 0.1, "outerConeAngle": 0.5}}
                ]
            }
        },
        "scene": 0,
        "scenes": [{"nodes": [0, 4, 5, 6]}],
        "nodes": [
            {"name": "Armature", "children": [1, 3]},
            {"name": "Root_Bone", "children": [2], "translation": [0.0, 0.0, 0.0]},
            {"name": "Tip_Bone", "translation": [0.0, 2.0, 0.0]},
            {"name": "SkinnedMesh", "mesh": 0, "skin": 0,
             "extras": {"customInt": 42, "customStr": "test", "customBool": True, "customFloat": 1.5}},
            {"name": "Camera", "camera": 0, "translation": [0.0, 1.0, 5.0]},
            {"name": "PointLightNode",
             "extensions": {"KHR_lights_punctual": {"light": 0}},
             "translation": [3.0, 3.0, 3.0]},
            {"name": "SpotLightNode",
             "extensions": {"KHR_lights_punctual": {"light": 1}},
             "translation": [0.0, 5.0, 0.0],
             "rotation": [0.707, 0.0, 0.0, 0.707]}
        ],
        "cameras": [{
            "type": "perspective",
            "perspective": {"aspectRatio": 1.78, "yfov": 0.9, "znear": 0.01, "zfar": 1000.0}
        }],
        "skins": [{
            "joints": [1, 2],
            "skeleton": 1,
            "inverseBindMatrices": 7
        }],
        "animations": [
            {
                "name": "BoneAnimation",
                "channels": [
                    {"sampler": 0, "target": {"node": 2, "path": "rotation"}}
                ],
                "samplers": [
                    {"input": 9, "output": 10, "interpolation": "LINEAR"}
                ]
            },
            {
                "name": "MorphAnimation",
                "channels": [
                    {"sampler": 0, "target": {"node": 3, "path": "weights"}}
                ],
                "samplers": [
                    {"input": 9, "output": 11, "interpolation": "LINEAR"}
                ]
            }
        ],
        "materials": [{
            "name": "FullMat",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.8, 0.2, 0.2, 1.0],
                "metallicFactor": 0.3,
                "roughnessFactor": 0.7
            },
            "doubleSided": True
        }],
        "meshes": [{
            "primitives": [{
                "attributes": {
                    "POSITION": 0, "NORMAL": 1, "COLOR_0": 2,
                    "TEXCOORD_0": 3, "JOINTS_0": 4, "WEIGHTS_0": 5
                },
                "indices": 6,
                "material": 0,
                "targets": [{"POSITION": 8}]
            }],
            "weights": [0.0],
            "extras": {"targetNames": ["TallMorph"]}
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3",
             "min": [-0.5, 0.0, 0.0], "max": [0.5, 2.0, 0.0]},  # POSITION
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},  # NORMAL
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC4"},  # COLOR_0
            {"bufferView": 3, "componentType": 5126, "count": 4, "type": "VEC2"},  # TEXCOORD_0
            {"bufferView": 4, "componentType": 5121, "count": 4, "type": "VEC4"},  # JOINTS_0
            {"bufferView": 5, "componentType": 5126, "count": 4, "type": "VEC4"},  # WEIGHTS_0
            {"bufferView": 6, "componentType": 5123, "count": 6, "type": "SCALAR"},  # indices
            {"bufferView": 7, "componentType": 5126, "count": 2, "type": "MAT4"},  # IBM
            {"bufferView": 8, "componentType": 5126, "count": 4, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [0.0, 0.5, 0.0]},  # morph pos
            {"bufferView": 9, "componentType": 5126, "count": 3, "type": "SCALAR",
             "min": [0.0], "max": [1.0]},  # anim times
            {"bufferView": 10, "componentType": 5126, "count": 3, "type": "VEC4"},  # anim rots
            {"bufferView": 11, "componentType": 5126, "count": 3, "type": "SCALAR"}  # morph weights
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": offsets[0], "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": offsets[1], "byteLength": len(normals), "target": 34962},
            {"buffer": 0, "byteOffset": offsets[2], "byteLength": len(colors), "target": 34962},
            {"buffer": 0, "byteOffset": offsets[3], "byteLength": len(texcoords), "target": 34962},
            {"buffer": 0, "byteOffset": offsets[4], "byteLength": len(joints), "target": 34962},
            {"buffer": 0, "byteOffset": offsets[5], "byteLength": len(weights), "target": 34962},
            {"buffer": 0, "byteOffset": offsets[6], "byteLength": len(indices), "target": 34963},
            {"buffer": 0, "byteOffset": offsets[7], "byteLength": len(ibm)},
            {"buffer": 0, "byteOffset": offsets[8], "byteLength": len(morph_pos), "target": 34962},
            {"buffer": 0, "byteOffset": offsets[9], "byteLength": len(anim_times)},
            {"buffer": 0, "byteOffset": offsets[10], "byteLength": len(anim_rots)},
            {"buffer": 0, "byteOffset": offsets[11], "byteLength": len(anim_weights)}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_full_scene.glb"), 'wb') as f:
        f.write(data)


def seed_scale_animation(outdir):
    """Scene with scale animation (exercises a different export path than rotation)."""
    positions, indices = triangle_mesh_bin()
    times = struct.pack('<3f', 0.0, 0.5, 1.0)
    scales = struct.pack('<9f',
        1.0, 1.0, 1.0,
        2.0, 2.0, 2.0,
        1.0, 1.0, 1.0)

    bin_data = positions + indices
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'
    anim_offset = len(bin_data)
    bin_data += times + scales
    while len(bin_data) % 4 != 0:
        bin_data += b'\x00'

    gltf = {
        "asset": {"version": "2.0", "generator": "seed_gen"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "ScaleAnimNode"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "animations": [{
            "name": "ScaleAnim",
            "channels": [
                {"sampler": 0, "target": {"node": 0, "path": "scale"}},
                {"sampler": 1, "target": {"node": 0, "path": "translation"}}
            ],
            "samplers": [
                {"input": 2, "output": 3, "interpolation": "LINEAR"},
                {"input": 2, "output": 3, "interpolation": "STEP"}
            ]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0.0, 0.0, 0.0], "max": [1.0, 1.0, 0.0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "SCALAR",
             "min": [0.0], "max": [1.0]},
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC3"}
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": len(positions), "byteLength": len(indices), "target": 34963},
            {"buffer": 0, "byteOffset": anim_offset, "byteLength": len(times)},
            {"buffer": 0, "byteOffset": anim_offset + len(times), "byteLength": len(scales)}
        ],
        "buffers": [{"byteLength": len(bin_data)}]
    }

    data = make_glb(gltf, bin_data)
    with open(os.path.join(outdir, "seed_scale_animation.glb"), 'wb') as f:
        f.write(data)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "export_seeds"
    os.makedirs(outdir, exist_ok=True)

    generators = [
        seed_camera,
        seed_camera_ortho,
        seed_lights,
        seed_skinned,
        seed_animation,
        seed_morph_targets,
        seed_vertex_colors,
        seed_multi_material,
        seed_embedded_texture,
        seed_skinned_animated,
        seed_metadata,
        seed_material_extensions,
        seed_full_scene,
        seed_scale_animation,
    ]

    for gen in generators:
        gen(outdir)
        print(f"Generated: {gen.__name__}")

    print(f"\n{len(generators)} seeds written to {outdir}/")
    for f in sorted(os.listdir(outdir)):
        size = os.path.getsize(os.path.join(outdir, f))
        print(f"  {f}: {size} bytes")


if __name__ == "__main__":
    main()
