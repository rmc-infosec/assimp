#!/usr/bin/env python3
"""
Generate minimal glTF2 JSON seed files with various KHR material extensions
and other features (cameras, lights, skinning, morph targets, animation)
for fuzzer corpus seeds to improve code coverage.

All files are self-contained using base64 data URIs for buffers.

Usage: python3 generate_gltf2_material_seeds.py /path/to/output
"""

import base64
import json
import os
import struct
import sys


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


def pad_to_4(data: bytes) -> bytes:
    """Pad data to a multiple of 4 bytes."""
    remainder = len(data) % 4
    if remainder:
        data += b"\x00" * (4 - remainder)
    return data


def base_asset():
    """Return a minimal glTF 2.0 asset object."""
    return {"version": "2.0", "generator": "assimp-fuzz-material-seeds"}


def make_triangle_buffer():
    """Create a minimal triangle buffer with positions and normals.

    Returns (buf, pos_len, nrm_len, idx_padded_len) for a 3-vertex triangle.
    """
    positions = pack_floats(
        0, 0, 0,
        1, 0, 0,
        0.5, 1, 0,
    )
    normals = pack_floats(
        0, 0, 1,
        0, 0, 1,
        0, 0, 1,
    )
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + normals + indices
    return buf, len(positions), len(normals), len(indices)


def make_triangle_gltf_base():
    """Build a base glTF dict with a triangle mesh (positions + normals + indices).

    Returns (gltf_dict, buf_bytes).
    The caller can add materials, extensions, etc.
    """
    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + normals + indices
    pos_len = len(positions)  # 36
    nrm_len = len(normals)    # 36
    idx_len = len(indices)    # 8

    gltf = {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1},
            "indices": 2,
            "material": 0,
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": pos_len, "target": 34962},
            {"buffer": 0, "byteOffset": pos_len, "byteLength": nrm_len, "target": 34962},
            {"buffer": 0, "byteOffset": pos_len + nrm_len, "byteLength": idx_len, "target": 34963},
        ],
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "materials": [],
    }
    return gltf


# ============================================================================
# Seed 1: KHR_materials_pbrSpecularGlossiness
# ============================================================================
def seed_pbr_specgloss():
    """A minimal glTF2 with KHR_materials_pbrSpecularGlossiness extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_pbrSpecularGlossiness"]
    gltf["materials"] = [{
        "name": "PbrSpecGlossMat",
        "extensions": {
            "KHR_materials_pbrSpecularGlossiness": {
                "diffuseFactor": [0.9, 0.1, 0.1, 1.0],
                "specularFactor": [0.5, 0.5, 0.5],
                "glossinessFactor": 0.8,
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 2: KHR_materials_sheen
# ============================================================================
def seed_sheen():
    """A glTF2 with KHR_materials_sheen extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_sheen"]
    gltf["materials"] = [{
        "name": "SheenMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.6, 0.3, 0.1, 1.0]
        },
        "extensions": {
            "KHR_materials_sheen": {
                "sheenColorFactor": [0.5, 0.3, 0.1],
                "sheenRoughnessFactor": 0.4,
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 3: KHR_materials_clearcoat
# ============================================================================
def seed_clearcoat():
    """A glTF2 with KHR_materials_clearcoat extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_clearcoat"]
    gltf["materials"] = [{
        "name": "ClearcoatMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.5, 0.5, 0.8, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.4,
        },
        "extensions": {
            "KHR_materials_clearcoat": {
                "clearcoatFactor": 0.8,
                "clearcoatRoughnessFactor": 0.3,
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 4: KHR_materials_transmission
# ============================================================================
def seed_transmission():
    """A glTF2 with KHR_materials_transmission extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_transmission"]
    gltf["materials"] = [{
        "name": "TransmissionMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.0,
        },
        "extensions": {
            "KHR_materials_transmission": {
                "transmissionFactor": 0.5,
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 5: KHR_materials_volume
# ============================================================================
def seed_volume():
    """A glTF2 with KHR_materials_volume extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_volume"]
    gltf["materials"] = [{
        "name": "VolumeMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.8, 0.9, 1.0, 1.0],
        },
        "extensions": {
            "KHR_materials_volume": {
                "thicknessFactor": 2.0,
                "attenuationDistance": 5.0,
                "attenuationColor": [0.9, 0.8, 0.7],
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 6: KHR_materials_ior
# ============================================================================
def seed_ior():
    """A glTF2 with KHR_materials_ior extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_ior"]
    gltf["materials"] = [{
        "name": "IORMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.9, 0.9, 0.95, 1.0],
        },
        "extensions": {
            "KHR_materials_ior": {
                "ior": 1.7,
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 7: KHR_materials_emissive_strength
# ============================================================================
def seed_emissive_strength():
    """A glTF2 with KHR_materials_emissive_strength extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_emissive_strength"]
    gltf["materials"] = [{
        "name": "EmissiveStrengthMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.1, 0.1, 0.1, 1.0],
        },
        "emissiveFactor": [1.0, 0.5, 0.0],
        "extensions": {
            "KHR_materials_emissive_strength": {
                "emissiveStrength": 5.0,
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 8: KHR_materials_anisotropy
# ============================================================================
def seed_anisotropy():
    """A glTF2 with KHR_materials_anisotropy extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_anisotropy"]
    gltf["materials"] = [{
        "name": "AnisotropyMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.7, 0.7, 0.7, 1.0],
            "metallicFactor": 1.0,
            "roughnessFactor": 0.3,
        },
        "extensions": {
            "KHR_materials_anisotropy": {
                "anisotropyStrength": 0.7,
                "anisotropyRotation": 0.5,
            }
        }
    }]
    return gltf


# ============================================================================
# Seed 9: KHR_materials_unlit
# ============================================================================
def seed_unlit():
    """A glTF2 with KHR_materials_unlit extension."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = ["KHR_materials_unlit"]
    gltf["materials"] = [{
        "name": "UnlitMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [1.0, 0.0, 0.5, 1.0],
        },
        "extensions": {
            "KHR_materials_unlit": {}
        }
    }]
    return gltf


# ============================================================================
# Seed 10: All material extensions on one material
# ============================================================================
def seed_all_extensions():
    """A glTF2 with ALL material extensions combined on one material."""
    gltf = make_triangle_gltf_base()
    gltf["extensionsUsed"] = [
        "KHR_materials_specular",
        "KHR_materials_sheen",
        "KHR_materials_clearcoat",
        "KHR_materials_transmission",
        "KHR_materials_volume",
        "KHR_materials_ior",
        "KHR_materials_emissive_strength",
        "KHR_materials_anisotropy",
    ]
    gltf["materials"] = [{
        "name": "AllExtensionsMat",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.8, 0.8, 0.8, 1.0],
            "metallicFactor": 0.5,
            "roughnessFactor": 0.5,
        },
        "emissiveFactor": [0.5, 0.5, 0.5],
        "doubleSided": True,
        "extensions": {
            "KHR_materials_specular": {
                "specularFactor": 0.8,
                "specularColorFactor": [1.0, 0.9, 0.8],
            },
            "KHR_materials_sheen": {
                "sheenColorFactor": [0.5, 0.3, 0.1],
                "sheenRoughnessFactor": 0.4,
            },
            "KHR_materials_clearcoat": {
                "clearcoatFactor": 0.6,
                "clearcoatRoughnessFactor": 0.2,
            },
            "KHR_materials_transmission": {
                "transmissionFactor": 0.3,
            },
            "KHR_materials_volume": {
                "thicknessFactor": 1.5,
                "attenuationDistance": 3.0,
                "attenuationColor": [0.9, 0.85, 0.8],
            },
            "KHR_materials_ior": {
                "ior": 1.5,
            },
            "KHR_materials_emissive_strength": {
                "emissiveStrength": 2.0,
            },
            "KHR_materials_anisotropy": {
                "anisotropyStrength": 0.6,
                "anisotropyRotation": 0.3,
            },
        }
    }]
    return gltf


# ============================================================================
# Seed 11: Cameras (perspective + orthographic)
# ============================================================================
def seed_cameras():
    """A glTF2 with perspective and orthographic cameras."""
    gltf = make_triangle_gltf_base()
    # Remove material ref since we don't define materials for this seed
    del gltf["materials"]
    gltf["meshes"][0]["primitives"][0].pop("material", None)

    # Add camera nodes
    gltf["scenes"] = [{"nodes": [0, 1, 2]}]
    gltf["nodes"] = [
        {"mesh": 0, "name": "MeshNode"},
        {"camera": 0, "name": "PerspCam", "translation": [0, 0, 5]},
        {"camera": 1, "name": "OrthoCam", "translation": [0, 0, 10]},
    ]
    gltf["cameras"] = [
        {
            "type": "perspective",
            "perspective": {
                "aspectRatio": 1.5,
                "yfov": 0.66,
                "znear": 0.1,
                "zfar": 100.0,
            }
        },
        {
            "type": "orthographic",
            "orthographic": {
                "xmag": 2.0,
                "ymag": 2.0,
                "znear": 0.01,
                "zfar": 50.0,
            }
        }
    ]
    return gltf


# ============================================================================
# Seed 12: KHR_lights_punctual (directional, point, spot)
# ============================================================================
def seed_lights():
    """A glTF2 with KHR_lights_punctual: directional, point, and spot lights."""
    gltf = make_triangle_gltf_base()
    del gltf["materials"]
    gltf["meshes"][0]["primitives"][0].pop("material", None)

    gltf["extensionsUsed"] = ["KHR_lights_punctual"]
    gltf["extensions"] = {
        "KHR_lights_punctual": {
            "lights": [
                {
                    "type": "directional",
                    "name": "DirLight",
                    "color": [1.0, 0.9, 0.8],
                    "intensity": 2.0,
                },
                {
                    "type": "point",
                    "name": "PointLight",
                    "color": [0.8, 0.8, 1.0],
                    "intensity": 5.0,
                    "range": 10.0,
                },
                {
                    "type": "spot",
                    "name": "SpotLight",
                    "color": [1.0, 1.0, 1.0],
                    "intensity": 8.0,
                    "range": 20.0,
                    "spot": {
                        "innerConeAngle": 0.2,
                        "outerConeAngle": 0.5,
                    }
                },
            ]
        }
    }
    gltf["scenes"] = [{"nodes": [0, 1, 2, 3]}]
    gltf["nodes"] = [
        {"mesh": 0, "name": "MeshNode"},
        {
            "name": "DirLightNode",
            "extensions": {"KHR_lights_punctual": {"light": 0}},
            "rotation": [0.383, 0, 0, 0.924],
        },
        {
            "name": "PointLightNode",
            "extensions": {"KHR_lights_punctual": {"light": 1}},
            "translation": [0, 3, 0],
        },
        {
            "name": "SpotLightNode",
            "extensions": {"KHR_lights_punctual": {"light": 2}},
            "translation": [0, 5, 5],
        },
    ]
    return gltf


# ============================================================================
# Seed 13: Skinning (joints, inverse bind matrices, JOINTS_0/WEIGHTS_0)
# ============================================================================
def seed_skinning():
    """A glTF2 with skinning: 4 vertices, 2 joints, inverse bind matrices."""
    # 4 vertices forming a vertical strip
    positions = pack_floats(
        -0.5, 0, 0,
         0.5, 0, 0,
        -0.5, 1, 0,
         0.5, 1, 0,
    )
    normals = pack_floats(
        0, 0, 1,
        0, 0, 1,
        0, 0, 1,
        0, 0, 1,
    )
    # Joint indices (each vertex: 4 joints) - use ubyte (componentType 5121)
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
    # Inverse bind matrices: 2 x mat4 (identity and translated)
    ibm = pack_floats(
        1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1,    # joint 0: identity
        1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, -1, 0, 1,    # joint 1: translate -Y
    )

    buf = positions + normals + joints + weights + indices + ibm
    pos_len = len(positions)      # 48
    nrm_len = len(normals)        # 48
    jnt_len = len(joints)         # 16
    wgt_len = len(weights)        # 64
    idx_len = len(indices)        # 12
    ibm_len = len(ibm)            # 128

    off = 0
    bvs = []
    for sz, tgt in [(pos_len, 34962), (nrm_len, 34962), (jnt_len, 34962),
                     (wgt_len, 34962), (idx_len, 34963), (ibm_len, None)]:
        bv = {"buffer": 0, "byteOffset": off, "byteLength": sz}
        if tgt is not None:
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
            {"name": "SkinRoot", "mesh": 0, "skin": 0, "children": [0]},
        ],
        "meshes": [{"primitives": [{
            "attributes": {
                "POSITION": 0,
                "NORMAL": 1,
                "JOINTS_0": 2,
                "WEIGHTS_0": 3,
            },
            "indices": 4,
        }]}],
        "skins": [{
            "inverseBindMatrices": 5,
            "joints": [0, 1],
            "skeleton": 0,
            "name": "TestSkin",
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3",
             "max": [0.5, 1, 0], "min": [-0.5, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 4, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5121, "count": 4, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5126, "count": 4, "type": "VEC4"},
            {"bufferView": 4, "componentType": 5123, "count": 6, "type": "SCALAR"},
            {"bufferView": 5, "componentType": 5126, "count": 2, "type": "MAT4"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
    }


# ============================================================================
# Seed 14: Morph targets
# ============================================================================
def seed_morph():
    """A glTF2 with morph targets: one target with position offsets and weights."""
    # Base mesh: triangle
    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
    # Morph target: position deltas
    morph_pos = pack_floats(0, 0.1, 0, 0, 0.1, 0, 0, 0.2, 0)
    indices = pack_ushorts(0, 1, 2)
    indices = pad_to_4(indices)

    buf = positions + normals + morph_pos + indices
    pos_len = len(positions)     # 36
    nrm_len = len(normals)       # 36
    morph_len = len(morph_pos)   # 36
    idx_len = len(indices)       # 8

    off = 0
    bvs = []
    for sz, tgt in [(pos_len, 34962), (nrm_len, 34962),
                     (morph_len, None), (idx_len, 34963)]:
        bv = {"buffer": 0, "byteOffset": off, "byteLength": sz}
        if tgt is not None:
            bv["target"] = tgt
        bvs.append(bv)
        off += sz

    return {
        "asset": base_asset(),
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "MorphNode"}],
        "meshes": [{
            "name": "MorphMesh",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 3,
                "targets": [{"POSITION": 2}],
            }],
            "weights": [0.5],
        }],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 3, "componentType": 5123, "count": 3, "type": "SCALAR"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
    }


# ============================================================================
# Seed 15: Animation (translation, rotation, scale channels)
# ============================================================================
def seed_animation():
    """A glTF2 with animation: translation, rotation, and scale channels
    with keyframes at 0.0, 0.5, 1.0."""
    positions = pack_floats(0, 0, 0, 1, 0, 0, 0.5, 1, 0)
    normals = pack_floats(0, 0, 1, 0, 0, 1, 0, 0, 1)
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

    buf = positions + normals + indices + times + translations + rotations + scales
    off = 0
    sizes = [len(positions), len(normals), len(indices), len(times),
             len(translations), len(rotations), len(scales)]
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
        "nodes": [{"mesh": 0, "name": "AnimNode"}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1},
            "indices": 2,
        }]}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3",
             "max": [1, 1, 0], "min": [0, 0, 0]},
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"},
            # Animation accessors
            {"bufferView": 3, "componentType": 5126, "count": 3, "type": "SCALAR",
             "max": [1.0], "min": [0.0]},
            {"bufferView": 4, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 5, "componentType": 5126, "count": 3, "type": "VEC4"},
            {"bufferView": 6, "componentType": 5126, "count": 3, "type": "VEC3"},
        ],
        "bufferViews": bvs,
        "buffers": [{"uri": make_data_uri(buf), "byteLength": len(buf)}],
        "animations": [{
            "name": "MainAnim",
            "samplers": [
                {"input": 3, "output": 4, "interpolation": "LINEAR"},
                {"input": 3, "output": 5, "interpolation": "LINEAR"},
                {"input": 3, "output": 6, "interpolation": "LINEAR"},
            ],
            "channels": [
                {"sampler": 0, "target": {"node": 0, "path": "translation"}},
                {"sampler": 1, "target": {"node": 0, "path": "rotation"}},
                {"sampler": 2, "target": {"node": 0, "path": "scale"}},
            ],
        }],
    }


# ============================================================================
# Registry of all seeds
# ============================================================================
SEEDS = {
    "seed_gltf2_pbr_specgloss.gltf": seed_pbr_specgloss,
    "seed_gltf2_sheen.gltf": seed_sheen,
    "seed_gltf2_clearcoat.gltf": seed_clearcoat,
    "seed_gltf2_transmission.gltf": seed_transmission,
    "seed_gltf2_volume.gltf": seed_volume,
    "seed_gltf2_ior.gltf": seed_ior,
    "seed_gltf2_emissive_strength.gltf": seed_emissive_strength,
    "seed_gltf2_anisotropy.gltf": seed_anisotropy,
    "seed_gltf2_unlit.gltf": seed_unlit,
    "seed_gltf2_all_extensions.gltf": seed_all_extensions,
    "seed_gltf2_cameras.gltf": seed_cameras,
    "seed_gltf2_lights.gltf": seed_lights,
    "seed_gltf2_skinning.gltf": seed_skinning,
    "seed_gltf2_morph.gltf": seed_morph,
    "seed_gltf2_animation.gltf": seed_animation,
}


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} /path/to/output", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]
    os.makedirs(output_dir, exist_ok=True)

    total_bytes = 0
    for filename, gen_func in sorted(SEEDS.items()):
        filepath = os.path.join(output_dir, filename)
        data = gen_func()
        content = json.dumps(data, indent=None, separators=(",", ":"))
        with open(filepath, "w") as f:
            f.write(content)
        size = len(content)
        total_bytes += size
        print(f"  {filename:48s}  {size:5d} bytes")

    print(f"\nGenerated {len(SEEDS)} seed files in {output_dir}")
    print(f"Total size: {total_bytes:,} bytes, avg {total_bytes // len(SEEDS):,} bytes/file")


if __name__ == "__main__":
    main()
