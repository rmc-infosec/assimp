#!/usr/bin/env python3
"""Generate valid MS3D (MilkShape 3D) binary seed files for fuzzing."""

import struct
import os
import math

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuzz_seeds")


def write_header(version=4):
    """MS3D header: 10-byte magic + int32 version."""
    return b"MS3D000000" + struct.pack("<i", version)


def write_vertex(x, y, z, bone_id=-1, flags=0, ref_count=0):
    """15 bytes: flags(u8) + vertex(3xf32) + boneId(i8) + referenceCount(u8)."""
    return struct.pack("<B3fbB", flags, x, y, z, bone_id, ref_count)


def write_triangle(v0, v1, v2, normals=None, s_coords=None, t_coords=None,
                   smoothing_group=1, group_index=0, flags=0):
    """70 bytes per triangle."""
    if normals is None:
        # Default: all normals pointing up (+Y)
        normals = [0.0, 1.0, 0.0] * 3
    if s_coords is None:
        s_coords = [0.0, 1.0, 0.5]
    if t_coords is None:
        t_coords = [0.0, 0.0, 1.0]

    data = struct.pack("<H", flags)
    data += struct.pack("<3H", v0, v1, v2)
    data += struct.pack("<9f", *normals)
    data += struct.pack("<3f", *s_coords)
    data += struct.pack("<3f", *t_coords)
    data += struct.pack("<BB", smoothing_group, group_index)
    return data


def write_group(name, triangle_indices, material_index=-1, flags=0):
    """Variable size: flags(u8) + name(32) + numTriangles(u16) + indices(Nx u16) + materialIndex(i8)."""
    name_bytes = name.encode("ascii")[:31].ljust(32, b"\x00")
    data = struct.pack("<B", flags)
    data += name_bytes
    data += struct.pack("<H", len(triangle_indices))
    for idx in triangle_indices:
        data += struct.pack("<H", idx)
    data += struct.pack("<b", material_index)
    return data


def write_material(name, ambient=(0.2, 0.2, 0.2, 1.0), diffuse=(0.8, 0.8, 0.8, 1.0),
                   specular=(1.0, 1.0, 1.0, 1.0), emissive=(0.0, 0.0, 0.0, 1.0),
                   shininess=64.0, transparency=1.0, mode=0,
                   texture="", alphamap=""):
    """361 bytes per material."""
    name_bytes = name.encode("ascii")[:31].ljust(32, b"\x00")
    texture_bytes = texture.encode("ascii")[:127].ljust(128, b"\x00")
    alphamap_bytes = alphamap.encode("ascii")[:127].ljust(128, b"\x00")

    data = name_bytes
    data += struct.pack("<4f", *ambient)
    data += struct.pack("<4f", *diffuse)
    data += struct.pack("<4f", *specular)
    data += struct.pack("<4f", *emissive)
    data += struct.pack("<f", shininess)
    data += struct.pack("<f", transparency)
    data += struct.pack("<B", mode)
    data += texture_bytes
    data += alphamap_bytes
    return data


def write_keyframe(time, x, y, z):
    """16 bytes: time(f32) + values(3xf32)."""
    return struct.pack("<4f", time, x, y, z)


def write_joint(name, parent_name, rotation, position,
                rotation_keyframes=None, position_keyframes=None, flags=0):
    """Variable size joint."""
    if rotation_keyframes is None:
        rotation_keyframes = []
    if position_keyframes is None:
        position_keyframes = []

    name_bytes = name.encode("ascii")[:31].ljust(32, b"\x00")
    parent_bytes = parent_name.encode("ascii")[:31].ljust(32, b"\x00")

    data = struct.pack("<B", flags)
    data += name_bytes
    data += parent_bytes
    data += struct.pack("<3f", *rotation)
    data += struct.pack("<3f", *position)
    data += struct.pack("<H", len(rotation_keyframes))
    data += struct.pack("<H", len(position_keyframes))

    for kf in rotation_keyframes:
        data += write_keyframe(*kf)
    for kf in position_keyframes:
        data += write_keyframe(*kf)

    return data


def write_animation_header(fps=24.0, current_time=0.0, total_frames=1):
    """Animation header: fps(f32) + currentTime(f32) + totalFrames(i32)."""
    return struct.pack("<ffI", fps, current_time, total_frames)


def generate_seed_basic():
    """Seed 1: Minimal - 3 verts, 1 triangle, 1 group, 1 material, no joints."""
    data = write_header()

    # Vertices: simple triangle on XY plane
    data += struct.pack("<H", 3)
    data += write_vertex(0.0, 0.0, 0.0, bone_id=-1)
    data += write_vertex(1.0, 0.0, 0.0, bone_id=-1)
    data += write_vertex(0.5, 1.0, 0.0, bone_id=-1)

    # Triangles
    data += struct.pack("<H", 1)
    data += write_triangle(0, 1, 2,
                           normals=[0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0],
                           s_coords=[0.0, 1.0, 0.5],
                           t_coords=[0.0, 0.0, 1.0],
                           group_index=0)

    # Groups
    data += struct.pack("<H", 1)
    data += write_group("default", [0], material_index=0)

    # Materials
    data += struct.pack("<H", 1)
    data += write_material("material0",
                           diffuse=(0.8, 0.2, 0.2, 1.0),
                           texture="texture.png")

    # Animation: no joints
    data += write_animation_header(fps=24.0, current_time=0.0, total_frames=1)
    data += struct.pack("<H", 0)  # numJoints = 0

    return data


def generate_seed_animated():
    """Seed 2: 4 verts, 2 triangles, 1 group, 1 material, 2 joints with keyframes."""
    data = write_header()

    # Vertices: a quad (two triangles), assigned to bones
    data += struct.pack("<H", 4)
    data += write_vertex(-1.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(1.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(1.0, 2.0, 0.0, bone_id=1)
    data += write_vertex(-1.0, 2.0, 0.0, bone_id=1)

    # Triangles
    data += struct.pack("<H", 2)
    data += write_triangle(0, 1, 2,
                           normals=[0.0, 0.0, 1.0] * 3,
                           s_coords=[0.0, 1.0, 1.0],
                           t_coords=[0.0, 0.0, 1.0],
                           group_index=0)
    data += write_triangle(0, 2, 3,
                           normals=[0.0, 0.0, 1.0] * 3,
                           s_coords=[0.0, 1.0, 0.0],
                           t_coords=[0.0, 1.0, 1.0],
                           group_index=0)

    # Groups
    data += struct.pack("<H", 1)
    data += write_group("body", [0, 1], material_index=0)

    # Materials
    data += struct.pack("<H", 1)
    data += write_material("skin",
                           diffuse=(0.9, 0.7, 0.5, 1.0),
                           shininess=32.0)

    # Animation with 2 joints and keyframes
    data += write_animation_header(fps=24.0, current_time=0.0, total_frames=48)
    data += struct.pack("<H", 2)

    # Joint 0: root (no parent)
    rot_kf_0 = [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 0.3, 0.0),
        (2.0, 0.0, 0.0, 0.0),
    ]
    pos_kf_0 = [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 1.0, 0.0),
        (2.0, 0.0, 0.0, 0.0),
    ]
    data += write_joint("root", "",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 0.0, 0.0),
                        rotation_keyframes=rot_kf_0,
                        position_keyframes=pos_kf_0)

    # Joint 1: child of root
    rot_kf_1 = [
        (0.0, 0.0, 0.0, 0.0),
        (0.5, 0.5, 0.0, 0.0),
        (1.0, 0.0, 0.0, 0.0),
        (1.5, -0.5, 0.0, 0.0),
        (2.0, 0.0, 0.0, 0.0),
    ]
    pos_kf_1 = [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 0.5, 0.0),
        (2.0, 0.0, 0.0, 0.0),
    ]
    data += write_joint("upper", "root",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 2.0, 0.0),
                        rotation_keyframes=rot_kf_1,
                        position_keyframes=pos_kf_1)

    return data


def generate_seed_multimaterial():
    """Seed 3: Multiple groups with different materials."""
    data = write_header()

    # 6 vertices: two separate triangles
    data += struct.pack("<H", 6)
    # Triangle 1 verts (group 0)
    data += write_vertex(0.0, 0.0, 0.0)
    data += write_vertex(1.0, 0.0, 0.0)
    data += write_vertex(0.5, 1.0, 0.0)
    # Triangle 2 verts (group 1)
    data += write_vertex(2.0, 0.0, 0.0)
    data += write_vertex(3.0, 0.0, 0.0)
    data += write_vertex(2.5, 1.0, 0.0)

    # 2 triangles
    data += struct.pack("<H", 2)
    data += write_triangle(0, 1, 2,
                           normals=[0.0, 0.0, 1.0] * 3,
                           s_coords=[0.0, 1.0, 0.5],
                           t_coords=[0.0, 0.0, 1.0],
                           group_index=0)
    data += write_triangle(3, 4, 5,
                           normals=[0.0, 0.0, 1.0] * 3,
                           s_coords=[0.0, 1.0, 0.5],
                           t_coords=[0.0, 0.0, 1.0],
                           group_index=1)

    # 2 groups, each referencing different material
    data += struct.pack("<H", 2)
    data += write_group("red_group", [0], material_index=0)
    data += write_group("blue_group", [1], material_index=1)

    # 2 materials
    data += struct.pack("<H", 2)
    data += write_material("red_mat",
                           ambient=(0.1, 0.0, 0.0, 1.0),
                           diffuse=(1.0, 0.0, 0.0, 1.0),
                           specular=(1.0, 0.5, 0.5, 1.0),
                           shininess=128.0,
                           texture="red.png")
    data += write_material("blue_mat",
                           ambient=(0.0, 0.0, 0.1, 1.0),
                           diffuse=(0.0, 0.0, 1.0, 1.0),
                           specular=(0.5, 0.5, 1.0, 1.0),
                           shininess=64.0,
                           texture="blue.png",
                           alphamap="blue_alpha.png")

    # No animation
    data += write_animation_header(fps=24.0, current_time=0.0, total_frames=1)
    data += struct.pack("<H", 0)

    return data


def generate_seed_skeleton():
    """Seed 4: Complex skeleton with parent-child joints, bone assignments."""
    data = write_header()

    # 12 vertices forming a simple humanoid shape (torso + limbs as triangles)
    # Each vertex assigned to a bone
    data += struct.pack("<H", 12)

    # Torso verts (bone 0 = spine)
    data += write_vertex(-0.5, 0.0, 0.0, bone_id=0)   # v0
    data += write_vertex(0.5, 0.0, 0.0, bone_id=0)    # v1
    data += write_vertex(0.0, 2.0, 0.0, bone_id=0)    # v2

    # Left arm verts (bone 1 = left_arm)
    data += write_vertex(-0.5, 2.0, 0.0, bone_id=1)   # v3
    data += write_vertex(-2.0, 2.0, 0.0, bone_id=1)   # v4
    data += write_vertex(-1.0, 2.5, 0.0, bone_id=1)   # v5

    # Right arm verts (bone 2 = right_arm)
    data += write_vertex(0.5, 2.0, 0.0, bone_id=2)    # v6
    data += write_vertex(2.0, 2.0, 0.0, bone_id=2)    # v7
    data += write_vertex(1.0, 2.5, 0.0, bone_id=2)    # v8

    # Head verts (bone 3 = head)
    data += write_vertex(-0.3, 2.5, 0.0, bone_id=3)   # v9
    data += write_vertex(0.3, 2.5, 0.0, bone_id=3)    # v10
    data += write_vertex(0.0, 3.5, 0.0, bone_id=3)    # v11

    # 4 triangles
    data += struct.pack("<H", 4)
    data += write_triangle(0, 1, 2,
                           normals=[0.0, 0.0, 1.0] * 3,
                           group_index=0)  # torso
    data += write_triangle(3, 4, 5,
                           normals=[0.0, 0.0, 1.0] * 3,
                           group_index=0)  # left arm
    data += write_triangle(6, 7, 8,
                           normals=[0.0, 0.0, 1.0] * 3,
                           group_index=0)  # right arm
    data += write_triangle(9, 10, 11,
                           normals=[0.0, 0.0, 1.0] * 3,
                           group_index=0)  # head

    # 1 group with all triangles
    data += struct.pack("<H", 1)
    data += write_group("body", [0, 1, 2, 3], material_index=0)

    # 1 material
    data += struct.pack("<H", 1)
    data += write_material("body_mat",
                           diffuse=(0.7, 0.6, 0.5, 1.0),
                           shininess=16.0)

    # Animation with 4 joints forming a hierarchy:
    # spine -> left_arm
    # spine -> right_arm
    # spine -> head
    data += write_animation_header(fps=30.0, current_time=0.0, total_frames=60)
    data += struct.pack("<H", 4)

    # Joint 0: spine (root)
    spine_rot_kf = [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 0.1, 0.0),
        (2.0, 0.0, 0.0, 0.0),
    ]
    spine_pos_kf = [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.0, 0.5, 0.0),
        (2.0, 0.0, 0.0, 0.0),
    ]
    data += write_joint("spine", "",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 1.0, 0.0),
                        rotation_keyframes=spine_rot_kf,
                        position_keyframes=spine_pos_kf)

    # Joint 1: left_arm (child of spine)
    larm_rot_kf = [
        (0.0, 0.0, 0.0, 0.0),
        (0.5, 0.0, 0.0, -0.5),
        (1.0, 0.0, 0.0, 0.0),
        (1.5, 0.0, 0.0, 0.5),
        (2.0, 0.0, 0.0, 0.0),
    ]
    larm_pos_kf = [
        (0.0, 0.0, 0.0, 0.0),
    ]
    data += write_joint("left_arm", "spine",
                        rotation=(0.0, 0.0, 0.0),
                        position=(-0.5, 2.0, 0.0),
                        rotation_keyframes=larm_rot_kf,
                        position_keyframes=larm_pos_kf)

    # Joint 2: right_arm (child of spine)
    rarm_rot_kf = [
        (0.0, 0.0, 0.0, 0.0),
        (0.5, 0.0, 0.0, 0.5),
        (1.0, 0.0, 0.0, 0.0),
        (1.5, 0.0, 0.0, -0.5),
        (2.0, 0.0, 0.0, 0.0),
    ]
    rarm_pos_kf = [
        (0.0, 0.0, 0.0, 0.0),
    ]
    data += write_joint("right_arm", "spine",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.5, 2.0, 0.0),
                        rotation_keyframes=rarm_rot_kf,
                        position_keyframes=rarm_pos_kf)

    # Joint 3: head (child of spine)
    head_rot_kf = [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.2, 0.0, 0.0),
        (2.0, 0.0, 0.0, 0.0),
    ]
    head_pos_kf = [
        (0.0, 0.0, 0.0, 0.0),
    ]
    data += write_joint("head", "spine",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 2.5, 0.0),
                        rotation_keyframes=head_rot_kf,
                        position_keyframes=head_pos_kf)

    return data


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seeds = {
        "seed_basic.ms3d": generate_seed_basic,
        "seed_animated.ms3d": generate_seed_animated,
        "seed_multimaterial.ms3d": generate_seed_multimaterial,
        "seed_skeleton.ms3d": generate_seed_skeleton,
    }

    for filename, generator in seeds.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        data = generator()
        with open(filepath, "wb") as f:
            f.write(data)
        print(f"Written {filepath} ({len(data)} bytes)")

    # Verification: check that each file starts with correct magic and version
    print("\nVerification:")
    for filename in seeds:
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "rb") as f:
            magic = f.read(10)
            version = struct.unpack("<i", f.read(4))[0]
            print(f"  {filename}: magic={magic!r}, version={version}")


if __name__ == "__main__":
    main()
