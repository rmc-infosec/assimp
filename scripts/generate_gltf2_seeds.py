#!/usr/bin/env python3
"""
Generate targeted glTF 2.0 seed files for fuzzing the assimp glTF2 importer.

Each seed exercises specific glTF 2.0 features to maximize code coverage.
All files are self-contained using base64 data URIs for buffers.

Output: test/models/glTF2/fuzz_seeds/
"""

import base64
import json
import os
import struct
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "test", "models", "glTF2", "fuzz_seeds")


def make_data_uri(data: bytes) -> str:
    """Encode raw bytes as a base64 data URI for glTF buffer."""
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:application/octet-stream;base64,{encoded}"


def pack_floats(*values) -> bytes:
    """Pack float values into little-endian binary."""
    return struct.pack(f"<{len(values)}f", *values)


def pack_ushorts(*values) -> bytes:
    """Pack unsigned short values into little-endian binary."""
    return struct.pack(f"<{len(values)}H", *values)


def pack_ubytes(*values) -> bytes:
    """Pack unsigned byte values into binary."""
    return struct.pack(f"<{len(values)}B", *values)


def pack_u32(*values) -> bytes:
    """Pack unsigned 32-bit integer values into little-endian binary."""
    return struct.pack(f"<{len(values)}I", *values)


def pad_to_4(data: bytes) -> bytes:
    """Pad data to a multiple of 4 bytes."""
    remainder = len(data) % 4
    if remainder:
        data += b"\x00" * (4 - remainder)
    return data


def base_asset():
    """Return a minimal glTF 2.0 asset object."""
    return {"version": "2.0", "generator": "assimp-fuzz-seeds"}


# ============================================================================
# Seed 1: PBR Metallic-Roughness with all properties
# ============================================================================
def seed_pbr_metallic_roughness():
    """PBR material with baseColorFactor, metallicFactor, roughnessFactor,
    baseColorTexture, metallicRoughnessTexture, normalTexture, occlusionTexture,
    emissiveTexture, emissiveFactor, alphaMode, alphaCutoff, doubleSided."""

    # Triangle: 3 verts (pos) + 3 verts (normal) + 3 verts (uv) + 3 indices
    positions = pack_floats(
        0, 0, 0, 1, 0, 0, 0.5, 1, 0
    )
    normals = pack_floats(
        0, 0, 1, 0, 0, 1, 0, 0, 1
    )
    uvs = pack_floats(
        0, 0, 1, 0, 0.5, 1
    )
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    # 1x1 white pixel PNG-like image (just 4 RGBA bytes for simplicity --
    # the importer will attempt to load it; it doesn't need to be a real PNG
    # for coverage purposes, but let's use a valid minimal RGBA block)
    # Actually, for glTF we can use a data URI image. Use raw RGBA bytes.
    # The importer handles embedded images via base64.
    pixel = pack_ubytes(255, 255, 255, 255)  # 1 white pixel RGBA

    buf = positions + normals + uvs + indices
    pos_off = 0
    nrm_off = len(positions)
    uv_off = nrm_off + len(normals)
    idx_off = uv_off + len(uvs)

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "PBRNode"}],
        "meshes": [{
            "name": "PBRMesh",
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "NORMAL": 1,
                    "TEXCOORD_0": 2
                },
                "indices": 3,
                "material": 0
            }]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": pos_off, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": nrm_off, "byteLength": len(normals), "target": 34962},
            {"buffer": 0, "byteOffset": uv_off, "byteLength": len(uvs), "target": 34962},
            {"buffer": 0, "byteOffset": idx_off, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "name": "PBRMaterial",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.8, 0.2, 0.1, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 0.3,
                "baseColorTexture": {"index": 0, "texCoord": 0},
                "metallicRoughnessTexture": {"index": 0, "texCoord": 0}
            },
            "normalTexture": {"index": 0, "scale": 1.5},
            "occlusionTexture": {"index": 0, "strength": 0.8},
            "emissiveTexture": {"index": 0},
            "emissiveFactor": [0.1, 0.2, 0.3],
            "alphaMode": "MASK",
            "alphaCutoff": 0.4,
            "doubleSided": True
        }],
        "textures": [{"source": 0, "sampler": 0}],
        "images": [{"uri": make_data_uri(pixel), "mimeType": "image/png"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]
    }


# ============================================================================
# Seed 2: KHR_materials_pbrSpecularGlossiness
# ============================================================================
def seed_pbr_specular_glossiness():
    """Exercises the KHR_materials_pbrSpecularGlossiness extension path."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + normals + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_materials_pbrSpecularGlossiness"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
            "indices": 3, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 72, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 96, "byteLength": 8, "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "name": "SpecGlossMat",
            "extensions": {
                "KHR_materials_pbrSpecularGlossiness": {
                    "diffuseFactor": [0.9, 0.1, 0.1, 1.0],
                    "specularFactor": [0.5, 0.5, 0.5],
                    "glossinessFactor": 0.8,
                    "diffuseTexture": {"index": 0, "texCoord": 0},
                    "specularGlossinessTexture": {"index": 0, "texCoord": 0}
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(128, 128, 128, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 3: KHR_materials_unlit
# ============================================================================
def seed_unlit_material():
    """Exercises the KHR_materials_unlit extension."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_materials_unlit"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0},
            "indices": 1, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "name": "UnlitMat",
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 0.0, 0.5, 1.0]
            },
            "extensions": {
                "KHR_materials_unlit": {}
            }
        }]
    }


# ============================================================================
# Seed 4: KHR_materials_clearcoat
# ============================================================================
def seed_clearcoat_material():
    """Exercises KHR_materials_clearcoat extension with all properties."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_materials_clearcoat"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 60, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "name": "ClearcoatMat",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.5, 0.5, 0.8, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.4
            },
            "extensions": {
                "KHR_materials_clearcoat": {
                    "clearcoatFactor": 1.0,
                    "clearcoatTexture": {"index": 0, "texCoord": 0},
                    "clearcoatRoughnessFactor": 0.1,
                    "clearcoatRoughnessTexture": {"index": 0, "texCoord": 0},
                    "clearcoatNormalTexture": {"index": 0, "scale": 1.0}
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(200, 200, 200, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 5: Morph targets with weights
# ============================================================================
def seed_morph_targets():
    """Mesh with morph targets (POSITION and NORMAL deltas) and weights."""

    # Base mesh: a triangle
    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
    # Morph target 0 displacements
    morph0_pos = pack_floats(0, 0.1, 0, 0, 0.1, 0, 0, 0.2, 0)
    morph0_nrm = pack_floats(0, 0, 0, 0, 0, 0, 0, 0, 0)
    # Morph target 1 displacements
    morph1_pos = pack_floats(0.1, 0, 0, -0.1, 0, 0, 0, -0.1, 0)
    morph1_nrm = pack_floats(0, 0, 0, 0, 0, 0, 0, 0, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + normals + morph0_pos + morph0_nrm + morph1_pos + morph1_nrm + indices
    off = 0
    bvs = []
    sizes = [36, 36, 36, 36, 36, 36, len(indices)]
    targets_34962 = [34962] * 6 + [34963]
    for i, sz in enumerate(sizes):
        bvs.append({"buffer": 0, "byteOffset": off, "byteLength": sz, "target": targets_34962[i]})
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
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
            "weights": [0.5, 0.3]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 4, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 5, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 6, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 6: Skinning (joints, inverseBindMatrices, skeleton)
# ============================================================================
def seed_skinning():
    """Skin with 2 joints, inverseBindMatrices, and JOINTS_0/WEIGHTS_0 attributes."""

    # 4 vertices forming a vertical strip
    positions = pack_floats(
        -0.5, 0, 0, 0.5, 0, 0,
        -0.5, 1, 0, 0.5, 1, 0
    )
    # Joint indices (each vertex: 4 joints) - use ubyte
    joints = pack_ubytes(
        0, 0, 0, 0,   # vertex 0 -> joint 0
        0, 0, 0, 0,   # vertex 1 -> joint 0
        1, 0, 0, 0,   # vertex 2 -> joint 1
        1, 0, 0, 0,   # vertex 3 -> joint 1
    )
    # Weights (each vertex: 4 weights)
    weights = pack_floats(
        1, 0, 0, 0,
        1, 0, 0, 0,
        1, 0, 0, 0,
        1, 0, 0, 0,
    )
    # Indices (2 triangles for a quad)
    indices = pack_ushorts(0, 1, 2, 2, 1, 3)
    # Inverse bind matrices: 2 x mat4 (identity)
    ibm = pack_floats(
        1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1,  # joint 0
        1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, -1, 0, 1,  # joint 1
    )

    buf = positions + joints + weights + indices + ibm
    pos_len = len(positions)     # 48
    jnt_len = len(joints)        # 16
    wgt_len = len(weights)       # 64
    idx_len = len(indices)       # 12
    ibm_len = len(ibm)           # 128

    off = 0
    bvs = []
    for sz, tgt in [(pos_len, 34962), (jnt_len, 34962), (wgt_len, 34962),
                     (idx_len, 34963), (ibm_len, None)]:
        bv = {"buffer": 0, "byteOffset": off, "byteLength": sz}
        if tgt:
            bv["target"] = tgt
        bvs.append(bv)
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [2]}],
        "nodes": [
            {"name": "Joint0", "children": [1], "translation": [0, 0, 0]},
            {"name": "Joint1", "translation": [0, 1, 0]},
            {"name": "SkinRoot", "mesh": 0, "skin": 0, "children": [0]}
        ],
        "meshes": [{"primitives": [{
            "attributes": {
                "POSITION": 0,
                "JOINTS_0": 1,
                "WEIGHTS_0": 2
            },
            "indices": 3
        }]}],
        "skins": [{
            "inverseBindMatrices": 4,
            "joints": [0, 1],
            "skeleton": 0,
            "name": "TestSkin"
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3",
             "max": [0.5, 1, 0], "min": [-0.5, 0, 0]},
            {"bufferView": 1, "componentType": 5121, "count": 4, "type": "VEC4"},
            {"bufferView": 2, "componentType": 5126, "count": 4, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5123, "count": 6, "type": "SCALAR"},
            {"bufferView": 4, "componentType": 5126, "count": 2, "type": "MAT4"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 7: Multiple animations (translation, rotation, scale, LINEAR + STEP)
# ============================================================================
def seed_animations():
    """Two animations with translation/rotation/scale channels, LINEAR and STEP interpolation."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    # Animation data: 3 keyframes at t=0, 0.5, 1.0
    times = pack_floats(0.0, 0.5, 1.0)
    # Translation values: 3 VEC3
    translations = pack_floats(0, 0, 0, 1, 0, 0, 0, 1, 0)
    # Rotation values: 3 quaternions (VEC4)
    rotations = pack_floats(
        0, 0, 0, 1,
        0, 0, 0.707, 0.707,
        0, 0, 1, 0,
    )
    # Scale values: 3 VEC3
    scales = pack_floats(1, 1, 1, 2, 2, 2, 1, 1, 1)

    buf = positions + indices + times + translations + rotations + scales
    off = 0
    sizes = [len(positions), len(indices), len(times), len(translations),
             len(rotations), len(scales)]
    bvs = []
    for i, sz in enumerate(sizes):
        bv = {"buffer": 0, "byteOffset": off, "byteLength": sz}
        if i == 0:
            bv["target"] = 34962
        elif i == 1:
            bv["target"] = 34963
        bvs.append(bv)
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "AnimNode"}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0}, "indices": 1
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
            # Animation accessors
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "SCALAR",
             "max": [1.0], "min": [0.0]},
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 4, "componentType": 5126, "count": 3, "type": "VEC4"},
            {"bufferView": 5, "componentType": 5126, "count": 3, "type": "VEC3"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "animations": [
            {
                "name": "TranslateAnim",
                "samplers": [
                    {"input": 2, "output": 3, "interpolation": "LINEAR"},
                    {"input": 2, "output": 4, "interpolation": "STEP"}
                ],
                "channels": [
                    {"sampler": 0, "target": {"node": 0, "path": "translation"}},
                    {"sampler": 1, "target": {"node": 0, "path": "rotation"}}
                ]
            },
            {
                "name": "ScaleAnim",
                "samplers": [
                    {"input": 2, "output": 5, "interpolation": "LINEAR"}
                ],
                "channels": [
                    {"sampler": 0, "target": {"node": 0, "path": "scale"}}
                ]
            }
        ]
    }


# ============================================================================
# Seed 8: Cameras (perspective and orthographic)
# ============================================================================
def seed_cameras():
    """Scene with both perspective and orthographic cameras on different nodes."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + indices

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0, 1, 2]}],
        "nodes": [
            {"mesh": 0, "name": "MeshNode"},
            {"camera": 0, "name": "PerspCam", "translation": [0, 0, 5]},
            {"camera": 1, "name": "OrthoCam", "translation": [0, 0, 10]}
        ],
        "cameras": [
            {
                "type": "perspective",
                "perspective": {
                    "aspectRatio": 1.5,
                    "yfov": 0.66,
                    "zfar": 100.0,
                    "znear": 0.1
                }
            },
            {
                "type": "orthographic",
                "orthographic": {
                    "xmag": 2.0,
                    "ymag": 2.0,
                    "zfar": 50.0,
                    "znear": 0.01
                }
            }
        ],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0}, "indices": 1
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 9: Multiple scenes with default scene selection
# ============================================================================
def seed_multiple_scenes():
    """Two scenes with the default scene set to the second one."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + indices

    return {
        "asset": base_asset(),
        "scene": 1,
        "scenes": [
            {"name": "Scene0", "nodes": [0]},
            {"name": "Scene1", "nodes": [1]}
        ],
        "nodes": [
            {"mesh": 0, "name": "NodeA"},
            {"mesh": 0, "name": "NodeB", "translation": [2, 0, 0]}
        ],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0}, "indices": 1
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 10: Sparse accessors
# ============================================================================
def seed_sparse_accessors():
    """Accessor with sparse data overriding specific elements."""

    # Base positions for 4 vertices (quad as 2 triangles)
    positions = pack_floats(
        0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0
    )
    indices = pack_ushorts(0, 1, 2, 0, 2, 3)

    # Sparse override: replace vertex 1 and 3 positions
    sparse_indices = pack_ushorts(1, 3)
    sparse_values = pack_floats(1.5, 0, 0, -0.5, 1, 0)

    buf = positions + pad_to_4(indices) + pad_to_4(sparse_indices) + sparse_values

    pos_off = 0
    idx_off = len(positions)
    idx_padded = pad_to_4(indices)
    sp_idx_off = idx_off + len(idx_padded)
    sp_idx_padded = pad_to_4(sparse_indices)
    sp_val_off = sp_idx_off + len(sp_idx_padded)

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0}, "indices": 1
        }]}],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126, "count": 4, "type": "VEC3",
                "max": [1.5, 1, 0], "min": [-0.5, 0, 0],
                "sparse": {
                    "count": 2,
                    "indices": {
                        "bufferView": 2,
                        "byteOffset": 0,
                        "componentType": 5123
                    },
                    "values": {
                        "bufferView": 3,
                        "byteOffset": 0
                    }
                }
            },
            {"bufferView": 1, "componentType": 5123, "count": 6, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": pos_off, "byteLength": len(positions), "target": 34962},
            {"buffer": 0, "byteOffset": idx_off, "byteLength": len(idx_padded), "target": 34963},
            {"buffer": 0, "byteOffset": sp_idx_off, "byteLength": len(sp_idx_padded)},
            {"buffer": 0, "byteOffset": sp_val_off, "byteLength": len(sparse_values)},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 11: Interleaved buffer views (byteStride, shared bufferView)
# ============================================================================
def seed_interleaved_buffers():
    """Multiple accessors sharing one bufferView with byteStride for interleaved data."""

    # Interleaved vertex data: position(VEC3) + normal(VEC3) = 24 bytes per vertex
    # 3 vertices
    vert0 = pack_floats(0, 0, 0) + pack_floats(0, 0, 1)
    vert1 = pack_floats(1, 0, 0) + pack_floats(0, 0, 1)
    vert2 = pack_floats(0.5, 1, 0) + pack_floats(0, 0, 1)
    interleaved = vert0 + vert1 + vert2

    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = interleaved + indices

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1}, "indices": 2
        }]}],
        "accessors": [
            {"bufferView": 0, "byteOffset": 0, "componentType": 5126,
             "count": 3, "type": "VEC3", "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 0, "byteOffset": 12, "componentType": 5126,
             "count": 3, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(interleaved),
             "byteStride": 24, "target": 34962},
            {"buffer": 0, "byteOffset": len(interleaved), "byteLength": len(indices),
             "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 12: Multiple UV sets (TEXCOORD_0 and TEXCOORD_1)
# ============================================================================
def seed_multiple_uv_sets():
    """Mesh with two UV sets: TEXCOORD_0 and TEXCOORD_1."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
    uv0 = pack_floats(0, 0, 1, 0, 0.5, 1)
    uv1 = pack_floats(0, 1, 1, 1, 0.5, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + normals + uv0 + uv1 + indices
    sizes = [len(positions), len(normals), len(uv0), len(uv1), len(indices)]
    off = 0
    bvs = []
    for i, sz in enumerate(sizes):
        bv = {"buffer": 0, "byteOffset": off, "byteLength": sz}
        if i < 4:
            bv["target"] = 34962
        else:
            bv["target"] = 34963
        bvs.append(bv)
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {
                "POSITION": 0,
                "NORMAL": 1,
                "TEXCOORD_0": 2,
                "TEXCOORD_1": 3
            },
            "indices": 4,
            "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 4, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": 0, "texCoord": 0},
                "metallicRoughnessTexture": {"index": 0, "texCoord": 1}
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(255, 0, 0, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 13: Vertex colors (COLOR_0)
# ============================================================================
def seed_vertex_colors():
    """Mesh with COLOR_0 attribute (VEC4 float RGBA)."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    colors = pack_floats(
        1, 0, 0, 1,    # red
        0, 1, 0, 1,    # green
        0, 0, 1, 1,    # blue
    )
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + colors + indices

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "COLOR_0": 1},
            "indices": 2
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC4"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 48, "target": 34962},
            {"buffer": 0, "byteOffset": 84, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 14: Tangent vectors (TANGENT attribute)
# ============================================================================
def seed_tangent_vectors():
    """Mesh with POSITION, NORMAL, TANGENT (VEC4) attributes."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
    # TANGENT is VEC4: xyz=tangent direction, w=handedness (+1 or -1)
    tangents = pack_floats(
        1, 0, 0, 1,
        1, 0, 0, 1,
        1, 0, 0, -1,
    )
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + normals + tangents + uvs + indices
    sizes = [36, 36, 48, 24, len(indices)]
    off = 0
    bvs = []
    for i, sz in enumerate(sizes):
        bv = {"buffer": 0, "byteOffset": off, "byteLength": sz}
        bv["target"] = 34963 if i == len(sizes) - 1 else 34962
        bvs.append(bv)
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {
                "POSITION": 0, "NORMAL": 1, "TANGENT": 2, "TEXCOORD_0": 3
            },
            "indices": 4
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 4, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 15: Multi-primitive meshes (different materials per primitive)
# ============================================================================
def seed_multi_primitive():
    """Mesh with 2 primitives, each using a different material."""

    # Primitive 0: triangle
    pos0 = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    idx0 = pack_ushorts(0, 1, 2)
    idx0 = pad_to_4(idx0)
    # Primitive 1: another triangle, offset
    pos1 = pack_floats(2, 0, 0, 3, 0, 0, 2.5, 1, 0)
    idx1 = pack_ushorts(0, 1, 2)
    idx1 = pad_to_4(idx1)

    buf = pos0 + idx0 + pos1 + idx1
    off = 0
    bvs = []
    for sz, tgt in [(len(pos0), 34962), (len(idx0), 34963),
                     (len(pos1), 34962), (len(idx1), 34963)]:
        bvs.append({"buffer": 0, "byteOffset": off, "byteLength": sz, "target": tgt})
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "name": "MultiPrimMesh",
            "primitives": [
                {
                    "attributes": {"POSITION": 0},
                    "indices": 1,
                    "material": 0,
                    "mode": 4  # TRIANGLES
                },
                {
                    "attributes": {"POSITION": 2},
                    "indices": 3,
                    "material": 1,
                    "mode": 4
                }
            ]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [3, 1, 0], "min": [2, 0, 0]},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [
            {"pbrMetallicRoughness": {"baseColorFactor": [1, 0, 0, 1]}},
            {"pbrMetallicRoughness": {"baseColorFactor": [0, 0, 1, 1]}}
        ]
    }


# ============================================================================
# Seed 16: Node hierarchy with matrix transforms (not TRS)
# ============================================================================
def seed_node_matrix_hierarchy():
    """Deep node hierarchy using 4x4 matrix transforms instead of TRS."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + indices

    # A 3-level hierarchy: root -> child -> grandchild
    # Each node has a matrix transform
    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [
            {
                "name": "Root",
                "children": [1],
                "matrix": [
                    2, 0, 0, 0,
                    0, 2, 0, 0,
                    0, 0, 2, 0,
                    0, 0, 0, 1
                ]
            },
            {
                "name": "Child",
                "children": [2],
                "matrix": [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    5, 0, 0, 1
                ]
            },
            {
                "name": "Grandchild",
                "mesh": 0,
                "matrix": [
                    0.707, 0.707, 0, 0,
                    -0.707, 0.707, 0, 0,
                    0, 0, 1, 0,
                    0, 3, 0, 1
                ]
            }
        ],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0}, "indices": 1
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 17: KHR_texture_transform extension
# ============================================================================
def seed_texture_transform():
    """Exercises KHR_texture_transform with offset, rotation, and scale."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_texture_transform"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 60, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorTexture": {
                    "index": 0,
                    "texCoord": 0,
                    "extensions": {
                        "KHR_texture_transform": {
                            "offset": [0.1, 0.2],
                            "rotation": 0.785,
                            "scale": [2.0, 2.0]
                        }
                    }
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(0, 255, 0, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 18: KHR_materials_specular extension
# ============================================================================
def seed_specular_extension():
    """Exercises KHR_materials_specular with specularFactor, specularColorFactor, textures."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_materials_specular"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 60, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.8, 0.8, 0.8, 1.0]
            },
            "extensions": {
                "KHR_materials_specular": {
                    "specularFactor": 0.8,
                    "specularTexture": {"index": 0, "texCoord": 0},
                    "specularColorFactor": [1.0, 0.9, 0.8],
                    "specularColorTexture": {"index": 0, "texCoord": 0}
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(200, 200, 200, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 19: KHR_materials_sheen extension
# ============================================================================
def seed_sheen_extension():
    """Exercises KHR_materials_sheen with all properties."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_materials_sheen"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 60, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.6, 0.3, 0.1, 1.0]
            },
            "extensions": {
                "KHR_materials_sheen": {
                    "sheenColorFactor": [0.9, 0.8, 0.7],
                    "sheenColorTexture": {"index": 0, "texCoord": 0},
                    "sheenRoughnessFactor": 0.5,
                    "sheenRoughnessTexture": {"index": 0, "texCoord": 0}
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(180, 150, 120, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 20: KHR_materials_transmission extension
# ============================================================================
def seed_transmission_extension():
    """Exercises KHR_materials_transmission."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_materials_transmission"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 60, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.0
            },
            "extensions": {
                "KHR_materials_transmission": {
                    "transmissionFactor": 0.9,
                    "transmissionTexture": {"index": 0, "texCoord": 0}
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(255, 255, 255, 128)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 21: KHR_materials_volume + KHR_materials_ior + KHR_materials_emissive_strength
# ============================================================================
def seed_volume_ior_emissive():
    """Exercises KHR_materials_volume, KHR_materials_ior, and KHR_materials_emissive_strength."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": [
            "KHR_materials_volume",
            "KHR_materials_ior",
            "KHR_materials_emissive_strength"
        ],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 60, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.8, 0.9, 1.0, 1.0]
            },
            "emissiveFactor": [1.0, 0.5, 0.0],
            "extensions": {
                "KHR_materials_volume": {
                    "thicknessFactor": 0.5,
                    "thicknessTexture": {"index": 0, "texCoord": 0},
                    "attenuationDistance": 1.0,
                    "attenuationColor": [0.8, 0.9, 1.0]
                },
                "KHR_materials_ior": {
                    "ior": 1.5
                },
                "KHR_materials_emissive_strength": {
                    "emissiveStrength": 5.0
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(128, 128, 255, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 22: KHR_materials_anisotropy extension
# ============================================================================
def seed_anisotropy_extension():
    """Exercises KHR_materials_anisotropy with all properties."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_materials_anisotropy"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "TEXCOORD_0": 1},
            "indices": 2, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 60, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.7, 0.7, 0.7, 1.0],
                "metallicFactor": 1.0,
                "roughnessFactor": 0.3
            },
            "extensions": {
                "KHR_materials_anisotropy": {
                    "anisotropyStrength": 0.8,
                    "anisotropyRotation": 1.57,
                    "anisotropyTexture": {"index": 0, "texCoord": 0}
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(128, 0, 128, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Seed 23: KHR_lights_punctual extension
# ============================================================================
def seed_lights_punctual():
    """Exercises KHR_lights_punctual with directional, point, and spot lights."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": ["KHR_lights_punctual"],
        "extensions": {
            "KHR_lights_punctual": {
                "lights": [
                    {
                        "type": "directional",
                        "name": "DirLight",
                        "color": [1.0, 0.9, 0.8],
                        "intensity": 2.0
                    },
                    {
                        "type": "point",
                        "name": "PointLight",
                        "color": [0.8, 0.8, 1.0],
                        "intensity": 5.0,
                        "range": 10.0
                    },
                    {
                        "type": "spot",
                        "name": "SpotLight",
                        "color": [1.0, 1.0, 1.0],
                        "intensity": 8.0,
                        "range": 20.0,
                        "spot": {
                            "innerConeAngle": 0.2,
                            "outerConeAngle": 0.5
                        }
                    }
                ]
            }
        },
        "scene": 0,
        "scenes": [{"nodes": [0, 1, 2, 3]}],
        "nodes": [
            {"mesh": 0, "name": "MeshNode"},
            {"name": "DirLightNode", "extensions": {"KHR_lights_punctual": {"light": 0}},
             "rotation": [0.383, 0, 0, 0.924]},
            {"name": "PointLightNode", "extensions": {"KHR_lights_punctual": {"light": 1}},
             "translation": [0, 3, 0]},
            {"name": "SpotLightNode", "extensions": {"KHR_lights_punctual": {"light": 2}},
             "translation": [0, 5, 5]}
        ],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0}, "indices": 1
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}]
    }


# ============================================================================
# Seed 24: Animation with CUBICSPLINE interpolation and weights path
# ============================================================================
def seed_animation_cubicspline_weights():
    """Exercises CUBICSPLINE interpolation and the 'weights' animation path."""

    # Triangle with a morph target
    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    morph_pos = pack_floats(0, 0.5, 0, 0, 0.5, 0, 0, 0.5, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    # CUBICSPLINE requires 3x values per keyframe: in-tangent, value, out-tangent
    # 2 keyframes, 1 weight per morph target: 2 * 3 * 1 = 6 floats
    times = pack_floats(0.0, 1.0)
    # For weights path with CUBICSPLINE: each keyframe has (inTangent, value, outTangent)
    weight_values = pack_floats(
        0, 0, 0,      # keyframe 0: inTangent=0, value=0, outTangent=0
        0, 1.0, 0,    # keyframe 1: inTangent=0, value=1, outTangent=0
    )

    buf = positions + morph_pos + indices + times + weight_values
    off = 0
    sizes = [len(positions), len(morph_pos), len(indices), len(times), len(weight_values)]
    bvs = []
    for i, sz in enumerate(sizes):
        bv = {"buffer": 0, "byteOffset": off, "byteLength": sz}
        if i == 0 or i == 1:
            bv["target"] = 34962
        elif i == 2:
            bv["target"] = 34963
        bvs.append(bv)
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "MorphAnimNode"}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 2,
                "targets": [{"POSITION": 1}]
            }],
            "weights": [0.0]
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
            {"bufferView": 3, "componentType": 5126, "count": 2, "type": "SCALAR",
             "max": [1.0], "min": [0.0]},
            {"bufferView": 4, "componentType": 5126, "count": 6, "type": "SCALAR"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "animations": [{
            "name": "WeightsCubicSpline",
            "samplers": [
                {"input": 3, "output": 4, "interpolation": "CUBICSPLINE"}
            ],
            "channels": [
                {"sampler": 0, "target": {"node": 0, "path": "weights"}}
            ]
        }]
    }


# ============================================================================
# Seed 25: Kitchen sink -- multiple extensions combined
# ============================================================================
def seed_combined_extensions():
    """Combines clearcoat, transmission, volume, ior, emissive_strength, and
    texture_transform in a single material to maximize combined extension code paths."""

    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
    uvs = pack_floats(0, 0, 1, 0, 0.5, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)
    buf = positions + normals + uvs + indices

    return {
        "asset": base_asset(),
        "extensionsUsed": [
            "KHR_materials_clearcoat",
            "KHR_materials_transmission",
            "KHR_materials_volume",
            "KHR_materials_ior",
            "KHR_materials_emissive_strength",
            "KHR_texture_transform",
            "KHR_materials_anisotropy"
        ],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2},
            "indices": 3, "material": 0
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC2"},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 36, "byteLength": 36, "target": 34962},
            {"buffer": 0, "byteOffset": 72, "byteLength": 24, "target": 34962},
            {"buffer": 0, "byteOffset": 96, "byteLength": len(indices), "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [{
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.9, 0.9, 0.95, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.1,
                "baseColorTexture": {
                    "index": 0,
                    "texCoord": 0,
                    "extensions": {
                        "KHR_texture_transform": {
                            "offset": [0.0, 0.0],
                            "rotation": 0.3,
                            "scale": [1.5, 1.5]
                        }
                    }
                }
            },
            "emissiveFactor": [0.5, 0.5, 0.5],
            "doubleSided": True,
            "extensions": {
                "KHR_materials_clearcoat": {
                    "clearcoatFactor": 0.5,
                    "clearcoatRoughnessFactor": 0.2
                },
                "KHR_materials_transmission": {
                    "transmissionFactor": 0.7
                },
                "KHR_materials_volume": {
                    "thicknessFactor": 0.3,
                    "attenuationDistance": 2.0,
                    "attenuationColor": [0.95, 0.95, 1.0]
                },
                "KHR_materials_ior": {
                    "ior": 1.45
                },
                "KHR_materials_emissive_strength": {
                    "emissiveStrength": 3.0
                },
                "KHR_materials_anisotropy": {
                    "anisotropyStrength": 0.5,
                    "anisotropyRotation": 0.0
                }
            }
        }],
        "textures": [{"source": 0}],
        "images": [{"uri": make_data_uri(pack_ubytes(230, 230, 240, 255)), "mimeType": "image/png"}]
    }


# ============================================================================
# Registry of all seeds
# ============================================================================
SEEDS = {
    "01_pbr_metallic_roughness.gltf": seed_pbr_metallic_roughness,
    "02_pbr_specular_glossiness.gltf": seed_pbr_specular_glossiness,
    "03_unlit_material.gltf": seed_unlit_material,
    "04_clearcoat_material.gltf": seed_clearcoat_material,
    "05_morph_targets.gltf": seed_morph_targets,
    "06_skinning.gltf": seed_skinning,
    "07_animations.gltf": seed_animations,
    "08_cameras.gltf": seed_cameras,
    "09_multiple_scenes.gltf": seed_multiple_scenes,
    "10_sparse_accessors.gltf": seed_sparse_accessors,
    "11_interleaved_buffers.gltf": seed_interleaved_buffers,
    "12_multiple_uv_sets.gltf": seed_multiple_uv_sets,
    "13_vertex_colors.gltf": seed_vertex_colors,
    "14_tangent_vectors.gltf": seed_tangent_vectors,
    "15_multi_primitive.gltf": seed_multi_primitive,
    "16_node_matrix_hierarchy.gltf": seed_node_matrix_hierarchy,
    "17_texture_transform.gltf": seed_texture_transform,
    "18_specular_extension.gltf": seed_specular_extension,
    "19_sheen_extension.gltf": seed_sheen_extension,
    "20_transmission_extension.gltf": seed_transmission_extension,
    "21_volume_ior_emissive.gltf": seed_volume_ior_emissive,
    "22_anisotropy_extension.gltf": seed_anisotropy_extension,
    "23_lights_punctual.gltf": seed_lights_punctual,
    "24_animation_cubicspline_weights.gltf": seed_animation_cubicspline_weights,
    "25_combined_extensions.gltf": seed_combined_extensions,
}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_bytes = 0
    for filename, gen_func in sorted(SEEDS.items()):
        filepath = os.path.join(OUTPUT_DIR, filename)
        data = gen_func()
        content = json.dumps(data, indent=None, separators=(",", ":"))
        with open(filepath, "w") as f:
            f.write(content)
        size = len(content)
        total_bytes += size
        print(f"  {filename:48s}  {size:5d} bytes")

    print(f"\nGenerated {len(SEEDS)} seed files in {OUTPUT_DIR}")
    print(f"Total size: {total_bytes:,} bytes, avg {total_bytes // len(SEEDS):,} bytes/file")


if __name__ == "__main__":
    main()
