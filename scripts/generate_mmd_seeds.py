#!/usr/bin/env python3
"""Generate minimal valid MMD PMX seed files for fuzzing.

Each seed exercises different PMX format features to maximize coverage
of the MMD/PMX importer code paths.
"""

import os
import struct
import sys


def pmx_text(text, encoding):
    """Encode a text string for PMX format.

    Args:
        text: The string to encode.
        encoding: 0 for UTF-16LE, 1 for UTF-8.

    Returns:
        bytes: 4-byte length prefix + encoded string data.
    """
    if encoding == 0:
        encoded = text.encode("utf-16-le")
    else:
        encoded = text.encode("utf-8")
    return struct.pack("<I", len(encoded)) + encoded


def pmx_empty_text(encoding):
    """Return an empty text field (4-byte zero length)."""
    return struct.pack("<I", 0)


def pmx_header(version=2.0, encoding=0, uv=0, vertex_idx_size=1,
               texture_idx_size=1, material_idx_size=1, bone_idx_size=1,
               morph_idx_size=1, rigidbody_idx_size=1):
    """Build a PMX header.

    Args:
        version: PMX version as float (2.0 or 2.1).
        encoding: 0=UTF-16LE, 1=UTF-8.
        uv: Number of additional UV channels (0-4).
        vertex_idx_size: Bytes per vertex index (1, 2, or 4).
        texture_idx_size: Bytes per texture index (1, 2, or 4).
        material_idx_size: Bytes per material index (1, 2, or 4).
        bone_idx_size: Bytes per bone index (1, 2, or 4).
        morph_idx_size: Bytes per morph index (1, 2, or 4).
        rigidbody_idx_size: Bytes per rigidbody index (1, 2, or 4).

    Returns:
        bytes: The PMX header bytes.
    """
    data = b""
    # Magic "PMX "
    data += b"\x50\x4D\x58\x20"
    # Version float
    data += struct.pack("<f", version)
    # Settings header size count (always 8)
    data += struct.pack("<B", 8)
    # 8 setting bytes
    data += struct.pack("<8B", encoding, uv, vertex_idx_size,
                        texture_idx_size, material_idx_size, bone_idx_size,
                        morph_idx_size, rigidbody_idx_size)
    return data


def pmx_index(value, size):
    """Encode an index value with the given byte size.

    Args:
        value: The index value (-1 encodes as all-1s sentinel).
        size: 1, 2, or 4 bytes.

    Returns:
        bytes: The encoded index.
    """
    if size == 1:
        if value == -1:
            return struct.pack("<B", 255)
        return struct.pack("<B", value)
    elif size == 2:
        if value == -1:
            return struct.pack("<H", 65535)
        return struct.pack("<H", value)
    elif size == 4:
        return struct.pack("<i", value)
    else:
        raise ValueError(f"Invalid index size: {size}")


def pmx_vertex_bdef1(position, normal, uv, bone_index, edge_scale,
                     bone_idx_size, uv_count=0):
    """Build a PMX vertex with BDEF1 skinning.

    Args:
        position: (x, y, z) tuple of floats.
        normal: (nx, ny, nz) tuple of floats.
        uv: (u, v) tuple of floats.
        bone_index: Index of the bone.
        edge_scale: Edge scale float.
        bone_idx_size: Bytes per bone index.
        uv_count: Number of additional UV channels.

    Returns:
        bytes: The vertex data.
    """
    data = b""
    data += struct.pack("<3f", *position)
    data += struct.pack("<3f", *normal)
    data += struct.pack("<2f", *uv)
    # Additional UV data (4 floats per channel)
    for _ in range(uv_count):
        data += struct.pack("<4f", 0.0, 0.0, 0.0, 0.0)
    # Skinning type: BDEF1 = 0
    data += struct.pack("<B", 0)
    # Bone index
    data += pmx_index(bone_index, bone_idx_size)
    # Edge scale
    data += struct.pack("<f", edge_scale)
    return data


def pmx_material(encoding, texture_idx_size, name="", english_name="",
                 diffuse=(0.8, 0.8, 0.8, 1.0), specular=(0.5, 0.5, 0.5),
                 specularity=5.0, ambient=(0.4, 0.4, 0.4), flag=0,
                 edge_color=(0.0, 0.0, 0.0, 1.0), edge_size=1.0,
                 diffuse_texture_index=-1, sphere_texture_index=-1,
                 sphere_op_mode=0, common_toon_flag=1, toon_texture_index=0,
                 memo="", index_count=3):
    """Build a PMX material.

    Args:
        encoding: Text encoding (0=UTF-16LE, 1=UTF-8).
        texture_idx_size: Bytes per texture index.
        name: Material name string.
        english_name: Material english name string.
        diffuse: (r, g, b, a) diffuse color.
        specular: (r, g, b) specular color.
        specularity: Specular strength float.
        ambient: (r, g, b) ambient color.
        flag: Draw flags byte.
        edge_color: (r, g, b, a) edge color.
        edge_size: Edge size float.
        diffuse_texture_index: Texture index.
        sphere_texture_index: Sphere texture index.
        sphere_op_mode: Sphere mode byte.
        common_toon_flag: 1=shared toon (1 byte index), 0=individual (texture index).
        toon_texture_index: Toon texture index.
        memo: Memo text string.
        index_count: Number of face indices this material covers.

    Returns:
        bytes: The material data.
    """
    data = b""
    data += pmx_text(name, encoding)
    data += pmx_text(english_name, encoding)
    data += struct.pack("<4f", *diffuse)
    data += struct.pack("<3f", *specular)
    data += struct.pack("<f", specularity)
    data += struct.pack("<3f", *ambient)
    data += struct.pack("<B", flag)
    data += struct.pack("<4f", *edge_color)
    data += struct.pack("<f", edge_size)
    data += pmx_index(diffuse_texture_index, texture_idx_size)
    data += pmx_index(sphere_texture_index, texture_idx_size)
    data += struct.pack("<B", sphere_op_mode)
    data += struct.pack("<B", common_toon_flag)
    if common_toon_flag:
        # Shared toon: 1 byte index
        data += struct.pack("<B", toon_texture_index)
    else:
        # Individual toon: texture index
        data += pmx_index(toon_texture_index, texture_idx_size)
    data += pmx_text(memo, encoding)
    data += struct.pack("<i", index_count)
    return data


def pmx_bone(encoding, bone_idx_size, name="bone", english_name="bone",
             position=(0.0, 0.0, 0.0), parent_index=-1, level=0,
             bone_flag=0x0000, offset=(0.0, 0.0, 0.0)):
    """Build a PMX bone with minimal flags (offset mode, no IK, no grants).

    Args:
        encoding: Text encoding.
        bone_idx_size: Bytes per bone index.
        name: Bone name.
        english_name: Bone english name.
        position: (x, y, z) bone position.
        parent_index: Parent bone index (-1 for root).
        level: Bone layer/level.
        bone_flag: 16-bit bone flags.
        offset: (x, y, z) tail offset (used when flag bit 0x0001 is not set).

    Returns:
        bytes: The bone data.
    """
    data = b""
    data += pmx_text(name, encoding)
    data += pmx_text(english_name, encoding)
    data += struct.pack("<3f", *position)
    data += pmx_index(parent_index, bone_idx_size)
    data += struct.pack("<i", level)
    data += struct.pack("<H", bone_flag)
    # If bit 0x0001 is set, read target index; otherwise read offset
    if bone_flag & 0x0001:
        data += pmx_index(0, bone_idx_size)
    else:
        data += struct.pack("<3f", *offset)
    # If grant flags (0x0100 or 0x0200) set
    if bone_flag & (0x0100 | 0x0200):
        data += pmx_index(0, bone_idx_size)
        data += struct.pack("<f", 1.0)
    # If fixed axis (0x0400)
    if bone_flag & 0x0400:
        data += struct.pack("<3f", 0.0, 1.0, 0.0)
    # If local axis (0x0800)
    if bone_flag & 0x0800:
        data += struct.pack("<3f", 1.0, 0.0, 0.0)
        data += struct.pack("<3f", 0.0, 1.0, 0.0)
    # If external parent (0x2000)
    if bone_flag & 0x2000:
        data += struct.pack("<i", 0)
    # If IK (0x0020)
    if bone_flag & 0x0020:
        data += pmx_index(0, bone_idx_size)  # ik_target_bone_index
        data += struct.pack("<i", 10)  # ik_loop
        data += struct.pack("<f", 1.0)  # ik_loop_angle_limit
        data += struct.pack("<i", 0)  # ik_link_count
    return data


def pmx_morph_vertex(encoding, morph_idx_size, vertex_idx_size,
                     name="morph", english_name="morph",
                     vertex_offsets=None):
    """Build a PMX vertex morph.

    Args:
        encoding: Text encoding.
        morph_idx_size: Bytes per morph index.
        vertex_idx_size: Bytes per vertex index.
        name: Morph name.
        english_name: Morph english name.
        vertex_offsets: List of (vertex_index, (dx, dy, dz)) tuples.

    Returns:
        bytes: The morph data.
    """
    if vertex_offsets is None:
        vertex_offsets = []
    data = b""
    data += pmx_text(name, encoding)
    data += pmx_text(english_name, encoding)
    # category: Other = 4
    data += struct.pack("<B", 4)
    # morph_type: Vertex = 1
    data += struct.pack("<B", 1)
    # offset_count
    data += struct.pack("<i", len(vertex_offsets))
    for vidx, (dx, dy, dz) in vertex_offsets:
        data += pmx_index(vidx, vertex_idx_size)
        data += struct.pack("<3f", dx, dy, dz)
    return data


def pmx_frame(encoding, bone_idx_size, morph_idx_size,
              name="frame", english_name="frame", frame_flag=0,
              elements=None):
    """Build a PMX display frame.

    Args:
        encoding: Text encoding.
        bone_idx_size: Bytes per bone index.
        morph_idx_size: Bytes per morph index.
        name: Frame name.
        english_name: Frame english name.
        frame_flag: 0=normal, 1=special.
        elements: List of (target, index) tuples.
            target=0 means bone index, target=1 means morph index.

    Returns:
        bytes: The frame data.
    """
    if elements is None:
        elements = []
    data = b""
    data += pmx_text(name, encoding)
    data += pmx_text(english_name, encoding)
    data += struct.pack("<B", frame_flag)
    data += struct.pack("<i", len(elements))
    for target, idx in elements:
        data += struct.pack("<B", target)
        if target == 0:
            data += pmx_index(idx, bone_idx_size)
        else:
            data += pmx_index(idx, morph_idx_size)
    return data


def pmx_rigidbody(encoding, bone_idx_size, name="body", english_name="body",
                  target_bone=0, group=0, mask=0xFFFF, shape=0,
                  size=(1.0, 1.0, 1.0), position=(0.0, 0.0, 0.0),
                  orientation=(0.0, 0.0, 0.0), mass=1.0,
                  move_attenuation=0.5, rotation_attenuation=0.5,
                  repulsion=0.0, friction=0.5, physics_calc_type=0):
    """Build a PMX rigid body.

    Args:
        encoding: Text encoding.
        bone_idx_size: Bytes per bone index.
        name: Rigid body name.
        english_name: Rigid body english name.
        target_bone: Associated bone index.
        group: Collision group byte.
        mask: Collision mask uint16.
        shape: 0=sphere, 1=box, 2=capsule.
        size: (x, y, z) shape dimensions.
        position: (x, y, z) position.
        orientation: (rx, ry, rz) rotation in radians.
        mass: Mass float.
        move_attenuation: Linear damping.
        rotation_attenuation: Angular damping.
        repulsion: Restitution.
        friction: Friction coefficient.
        physics_calc_type: 0=follow bone, 1=physics, 2=physics+bone.

    Returns:
        bytes: The rigid body data.
    """
    data = b""
    data += pmx_text(name, encoding)
    data += pmx_text(english_name, encoding)
    data += pmx_index(target_bone, bone_idx_size)
    data += struct.pack("<B", group)
    data += struct.pack("<H", mask)
    data += struct.pack("<B", shape)
    data += struct.pack("<3f", *size)
    data += struct.pack("<3f", *position)
    data += struct.pack("<3f", *orientation)
    data += struct.pack("<f", mass)
    data += struct.pack("<f", move_attenuation)
    data += struct.pack("<f", rotation_attenuation)
    data += struct.pack("<f", repulsion)
    data += struct.pack("<f", friction)
    data += struct.pack("<B", physics_calc_type)
    return data


def pmx_joint(encoding, rigidbody_idx_size, name="joint",
              english_name="joint", joint_type=0, rigid_body1=0,
              rigid_body2=0, position=(0.0, 0.0, 0.0),
              orientation=(0.0, 0.0, 0.0)):
    """Build a PMX joint.

    Args:
        encoding: Text encoding.
        rigidbody_idx_size: Bytes per rigidbody index.
        name: Joint name.
        english_name: Joint english name.
        joint_type: 0=6DOF spring, 1=6DOF, 2=P2P, 3=cone, 5=slider, 6=hinge.
        rigid_body1: First rigid body index.
        rigid_body2: Second rigid body index.
        position: (x, y, z) position.
        orientation: (rx, ry, rz) orientation.

    Returns:
        bytes: The joint data.
    """
    data = b""
    data += pmx_text(name, encoding)
    data += pmx_text(english_name, encoding)
    data += struct.pack("<B", joint_type)
    # Joint param
    data += pmx_index(rigid_body1, rigidbody_idx_size)
    data += pmx_index(rigid_body2, rigidbody_idx_size)
    data += struct.pack("<3f", *position)
    data += struct.pack("<3f", *orientation)
    # move_limitation_min, move_limitation_max
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    # rotation_limitation_min, rotation_limitation_max
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    # spring_move_coefficient, spring_rotation_coefficient
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    return data


# ---------------------------------------------------------------------------
# Seed generators
# ---------------------------------------------------------------------------

def seed_minimal():
    """Empty model (all counts = 0), UTF-16LE encoding."""
    encoding = 0
    data = pmx_header(version=2.0, encoding=encoding)
    # 4 empty text fields
    for _ in range(4):
        data += pmx_empty_text(encoding)
    # All 9 counts = 0
    for _ in range(9):
        data += struct.pack("<i", 0)
    return data


def seed_utf8():
    """UTF-8 encoding with model name, all counts = 0."""
    encoding = 1
    data = pmx_header(version=2.0, encoding=encoding)
    # model_name
    data += pmx_text("TestModel", encoding)
    # model_english_name
    data += pmx_text("TestModel_EN", encoding)
    # model_comment
    data += pmx_text("A test PMX model", encoding)
    # model_english_comment
    data += pmx_text("A test PMX model (English)", encoding)
    # All 9 counts = 0
    for _ in range(9):
        data += struct.pack("<i", 0)
    return data


def seed_utf16():
    """UTF-16LE encoding with model name, all counts = 0."""
    encoding = 0
    data = pmx_header(version=2.0, encoding=encoding)
    # model_name
    data += pmx_text("TestModel", encoding)
    # model_english_name
    data += pmx_text("TestModel_EN", encoding)
    # model_comment
    data += pmx_text("UTF-16 test", encoding)
    # model_english_comment
    data += pmx_text("UTF-16 test (English)", encoding)
    # All 9 counts = 0
    for _ in range(9):
        data += struct.pack("<i", 0)
    return data


def seed_one_vertex():
    """1 vertex (BDEF1), 3 indices forming a degenerate triangle, 1 material, 1 bone."""
    encoding = 1
    bone_idx_size = 1
    vertex_idx_size = 1
    texture_idx_size = 1
    material_idx_size = 1
    morph_idx_size = 1
    rigidbody_idx_size = 1

    data = pmx_header(
        version=2.0, encoding=encoding, uv=0,
        vertex_idx_size=vertex_idx_size,
        texture_idx_size=texture_idx_size,
        material_idx_size=material_idx_size,
        bone_idx_size=bone_idx_size,
        morph_idx_size=morph_idx_size,
        rigidbody_idx_size=rigidbody_idx_size,
    )
    # Text fields
    data += pmx_text("OneVertex", encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)

    # vertex_count = 1
    data += struct.pack("<i", 1)
    data += pmx_vertex_bdef1(
        position=(0.0, 0.0, 0.0),
        normal=(0.0, 0.0, 1.0),
        uv=(0.0, 0.0),
        bone_index=0,
        edge_scale=1.0,
        bone_idx_size=bone_idx_size,
    )

    # index_count = 3 (one triangle, all pointing to vertex 0)
    data += struct.pack("<i", 3)
    for _ in range(3):
        data += pmx_index(0, vertex_idx_size)

    # texture_count = 0
    data += struct.pack("<i", 0)

    # material_count = 1
    data += struct.pack("<i", 1)
    data += pmx_material(
        encoding=encoding,
        texture_idx_size=texture_idx_size,
        name="mat0",
        english_name="mat0",
        index_count=3,
    )

    # bone_count = 1
    data += struct.pack("<i", 1)
    data += pmx_bone(
        encoding=encoding,
        bone_idx_size=bone_idx_size,
        name="root",
        english_name="root",
        position=(0.0, 0.0, 0.0),
        parent_index=-1,
        level=0,
        bone_flag=0x0000,
        offset=(0.0, 1.0, 0.0),
    )

    # morph_count = 0
    data += struct.pack("<i", 0)
    # frame_count = 0
    data += struct.pack("<i", 0)
    # rigid_body_count = 0
    data += struct.pack("<i", 0)
    # joint_count = 0
    data += struct.pack("<i", 0)

    return data


def seed_triangle():
    """Simple triangle: 3 vertices, 3 indices, 1 material, 1 bone."""
    encoding = 1
    bone_idx_size = 2
    vertex_idx_size = 2
    texture_idx_size = 1
    material_idx_size = 1
    morph_idx_size = 1
    rigidbody_idx_size = 1

    data = pmx_header(
        version=2.0, encoding=encoding, uv=0,
        vertex_idx_size=vertex_idx_size,
        texture_idx_size=texture_idx_size,
        material_idx_size=material_idx_size,
        bone_idx_size=bone_idx_size,
        morph_idx_size=morph_idx_size,
        rigidbody_idx_size=rigidbody_idx_size,
    )
    # Text fields
    data += pmx_text("Triangle", encoding)
    data += pmx_text("Triangle", encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)

    # 3 vertices
    data += struct.pack("<i", 3)
    vertices = [
        ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.5, 0.0)),
        ((-1.0, -1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0)),
        ((1.0, -1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0)),
    ]
    for pos, nrm, uv in vertices:
        data += pmx_vertex_bdef1(
            position=pos, normal=nrm, uv=uv,
            bone_index=0, edge_scale=1.0,
            bone_idx_size=bone_idx_size,
        )

    # 3 indices
    data += struct.pack("<i", 3)
    for i in range(3):
        data += pmx_index(i, vertex_idx_size)

    # texture_count = 0
    data += struct.pack("<i", 0)

    # material_count = 1
    data += struct.pack("<i", 1)
    data += pmx_material(
        encoding=encoding,
        texture_idx_size=texture_idx_size,
        name="trimat",
        english_name="trimat",
        index_count=3,
    )

    # bone_count = 1
    data += struct.pack("<i", 1)
    data += pmx_bone(
        encoding=encoding,
        bone_idx_size=bone_idx_size,
        name="root",
        english_name="root",
        position=(0.0, 0.0, 0.0),
        parent_index=-1,
    )

    # morph_count = 0
    data += struct.pack("<i", 0)
    # frame_count = 0
    data += struct.pack("<i", 0)
    # rigid_body_count = 0
    data += struct.pack("<i", 0)
    # joint_count = 0
    data += struct.pack("<i", 0)

    return data


def seed_morph():
    """Model with 1 vertex morph: 3 vertices, 3 indices, 1 material, 1 bone, 1 morph."""
    encoding = 1
    bone_idx_size = 1
    vertex_idx_size = 1
    texture_idx_size = 1
    material_idx_size = 1
    morph_idx_size = 1
    rigidbody_idx_size = 1

    data = pmx_header(
        version=2.0, encoding=encoding, uv=0,
        vertex_idx_size=vertex_idx_size,
        texture_idx_size=texture_idx_size,
        material_idx_size=material_idx_size,
        bone_idx_size=bone_idx_size,
        morph_idx_size=morph_idx_size,
        rigidbody_idx_size=rigidbody_idx_size,
    )
    # Text fields
    data += pmx_text("MorphModel", encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)

    # 3 vertices
    data += struct.pack("<i", 3)
    vertices = [
        ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.5, 0.0)),
        ((-1.0, -1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0)),
        ((1.0, -1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0)),
    ]
    for pos, nrm, uv in vertices:
        data += pmx_vertex_bdef1(
            position=pos, normal=nrm, uv=uv,
            bone_index=0, edge_scale=1.0,
            bone_idx_size=bone_idx_size,
        )

    # 3 indices
    data += struct.pack("<i", 3)
    for i in range(3):
        data += pmx_index(i, vertex_idx_size)

    # texture_count = 0
    data += struct.pack("<i", 0)

    # material_count = 1
    data += struct.pack("<i", 1)
    data += pmx_material(
        encoding=encoding,
        texture_idx_size=texture_idx_size,
        name="mat0",
        english_name="mat0",
        index_count=3,
    )

    # bone_count = 1
    data += struct.pack("<i", 1)
    data += pmx_bone(
        encoding=encoding,
        bone_idx_size=bone_idx_size,
        name="root",
        english_name="root",
        parent_index=-1,
    )

    # morph_count = 1
    data += struct.pack("<i", 1)
    data += pmx_morph_vertex(
        encoding=encoding,
        morph_idx_size=morph_idx_size,
        vertex_idx_size=vertex_idx_size,
        name="smile",
        english_name="smile",
        vertex_offsets=[
            (0, (0.0, 0.5, 0.0)),
            (1, (0.1, 0.0, 0.0)),
            (2, (-0.1, 0.0, 0.0)),
        ],
    )

    # frame_count = 0
    data += struct.pack("<i", 0)
    # rigid_body_count = 0
    data += struct.pack("<i", 0)
    # joint_count = 0
    data += struct.pack("<i", 0)

    return data


def seed_rigidbody():
    """Model with 1 rigid body and 1 joint."""
    encoding = 1
    bone_idx_size = 1
    vertex_idx_size = 1
    texture_idx_size = 1
    material_idx_size = 1
    morph_idx_size = 1
    rigidbody_idx_size = 1

    data = pmx_header(
        version=2.0, encoding=encoding, uv=0,
        vertex_idx_size=vertex_idx_size,
        texture_idx_size=texture_idx_size,
        material_idx_size=material_idx_size,
        bone_idx_size=bone_idx_size,
        morph_idx_size=morph_idx_size,
        rigidbody_idx_size=rigidbody_idx_size,
    )
    # Text fields
    data += pmx_text("RigidBodyModel", encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)

    # 3 vertices
    data += struct.pack("<i", 3)
    vertices = [
        ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.5, 0.0)),
        ((-1.0, -1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0)),
        ((1.0, -1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0)),
    ]
    for pos, nrm, uv in vertices:
        data += pmx_vertex_bdef1(
            position=pos, normal=nrm, uv=uv,
            bone_index=0, edge_scale=1.0,
            bone_idx_size=bone_idx_size,
        )

    # 3 indices
    data += struct.pack("<i", 3)
    for i in range(3):
        data += pmx_index(i, vertex_idx_size)

    # texture_count = 0
    data += struct.pack("<i", 0)

    # material_count = 1
    data += struct.pack("<i", 1)
    data += pmx_material(
        encoding=encoding,
        texture_idx_size=texture_idx_size,
        name="mat0",
        english_name="mat0",
        index_count=3,
    )

    # bone_count = 1
    data += struct.pack("<i", 1)
    data += pmx_bone(
        encoding=encoding,
        bone_idx_size=bone_idx_size,
        name="root",
        english_name="root",
        parent_index=-1,
    )

    # morph_count = 0
    data += struct.pack("<i", 0)
    # frame_count = 0
    data += struct.pack("<i", 0)

    # rigid_body_count = 1
    data += struct.pack("<i", 1)
    data += pmx_rigidbody(
        encoding=encoding,
        bone_idx_size=bone_idx_size,
        name="body0",
        english_name="body0",
        target_bone=0,
        shape=0,  # sphere
        size=(0.5, 0.0, 0.0),
    )

    # joint_count = 1
    data += struct.pack("<i", 1)
    data += pmx_joint(
        encoding=encoding,
        rigidbody_idx_size=rigidbody_idx_size,
        name="joint0",
        english_name="joint0",
        joint_type=0,
        rigid_body1=0,
        rigid_body2=0,
    )

    return data


def seed_v21():
    """Version 2.1 model with all counts = 0."""
    encoding = 1
    data = pmx_header(version=2.1, encoding=encoding)
    # Text fields
    data += pmx_text("V21Model", encoding)
    data += pmx_text("V21Model_EN", encoding)
    data += pmx_empty_text(encoding)
    data += pmx_empty_text(encoding)
    # All 9 counts = 0
    for _ in range(9):
        data += struct.pack("<i", 0)
    return data


SEEDS = {
    "seed_minimal": seed_minimal,
    "seed_utf8": seed_utf8,
    "seed_utf16": seed_utf16,
    "seed_one_vertex": seed_one_vertex,
    "seed_triangle": seed_triangle,
    "seed_morph": seed_morph,
    "seed_rigidbody": seed_rigidbody,
    "seed_v21": seed_v21,
}


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "mmd_seeds"
    os.makedirs(outdir, exist_ok=True)

    for name, gen in SEEDS.items():
        data = gen()
        path = os.path.join(outdir, f"{name}.pmx")
        with open(path, "wb") as f:
            f.write(data)
        # Verify magic bytes
        assert data[:4] == b"\x50\x4D\x58\x20", f"Bad magic in {name}"
        print(f"  {path} ({len(data)} bytes)")

    print(f"\nGenerated {len(SEEDS)} PMX seed files in {outdir}/")


if __name__ == "__main__":
    main()
