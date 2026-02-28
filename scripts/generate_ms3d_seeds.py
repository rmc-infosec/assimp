#!/usr/bin/env python3
"""Generate valid MS3D (MilkShape 3D) binary seed files for fuzzing.

This script generates seeds that target coverage gaps, specifically:
- Comments section (group, material, joint, model comments)
- Subversion vertex weight data (bone_id/weight pairs for multi-bone skinning)
- Multiple animation keyframes with parent-child joints
- Multiple groups with different materials
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "test", "models", "MS3D", "fuzz_seeds")


def write_header(version=4):
    """MS3D header: 10-byte magic + int32 version."""
    return b"MS3D000000" + struct.pack("<i", version)


def write_vertex(x, y, z, bone_id=-1, flags=0, ref_count=0):
    """15 bytes: flags(u8) + vertex(3xf32) + boneId(i8) + referenceCount(u8)."""
    # bone_id is a signed byte (-1 means no bone)
    return struct.pack("<B3fbB", flags, x, y, z, bone_id, ref_count)


def write_triangle(v0, v1, v2, normals=None, s_coords=None, t_coords=None,
                   smoothing_group=1, group_index=0, flags=0):
    """70 bytes per triangle."""
    if normals is None:
        normals = [0.0, 0.0, 1.0] * 3
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
    """Variable size group."""
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


def write_comments(items_with_comments):
    """Write a comment section.

    items_with_comments: list of (index, comment_string) tuples.
    Format: u16 count, then for each: u32 index, u32 length, bytes.
    """
    data = struct.pack("<H", len(items_with_comments))
    for index, comment in items_with_comments:
        comment_bytes = comment.encode("ascii")
        data += struct.pack("<II", index, len(comment_bytes))
        data += comment_bytes
    return data


def write_model_comment(comment):
    """Write the model-level comment.

    Format: u32 numComments (1), u32 length, bytes.
    """
    comment_bytes = comment.encode("ascii")
    data = struct.pack("<I", 1)  # numComments must be non-zero
    data += struct.pack("<I", len(comment_bytes))
    data += comment_bytes
    return data


def write_subversion_vertex_weights(num_verts, weights_per_vert, subversion=1):
    """Write subversion vertex weight data.

    subversion 1: per vertex, 3x (u8 bone_id, u8 weight_byte)
    subversion 2: same + 4 extra bytes per vertex
    subversion 3: same + 8 extra bytes per vertex

    weights_per_vert: list of num_verts entries, each a list of
        (bone_id, weight_0_255) tuples of length 3.
    """
    data = struct.pack("<I", subversion)
    for i in range(num_verts):
        w = weights_per_vert[i] if i < len(weights_per_vert) else [(255, 0)] * 3
        for bone_id, weight in w:
            data += struct.pack("<BB", bone_id & 0xFF, weight & 0xFF)
        # Extra bytes for subversion > 1
        extra = (subversion - 1) * 4
        data += b"\x00" * extra
    return data


def generate_seed_comments():
    """Seed with comments on groups, materials, joints, and model-level comment.

    Targets the ReadComments<T> template and model comment parsing code paths.
    """
    data = write_header()

    # 4 vertices (quad)
    data += struct.pack("<H", 4)
    data += write_vertex(-1.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(1.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(1.0, 2.0, 0.0, bone_id=1)
    data += write_vertex(-1.0, 2.0, 0.0, bone_id=1)

    # 2 triangles
    data += struct.pack("<H", 2)
    data += write_triangle(0, 1, 2, group_index=0)
    data += write_triangle(0, 2, 3, group_index=0)

    # 1 group
    data += struct.pack("<H", 1)
    data += write_group("torso", [0, 1], material_index=0)

    # 1 material
    data += struct.pack("<H", 1)
    data += write_material("skin",
                           diffuse=(0.9, 0.7, 0.5, 1.0),
                           shininess=32.0,
                           texture="skin.bmp",
                           alphamap="skin_a.bmp")

    # Animation: 2 joints
    data += write_animation_header(fps=30.0, current_time=0.0, total_frames=60)
    data += struct.pack("<H", 2)

    data += write_joint("root", "",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 0.0, 0.0),
                        rotation_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (1.0, 0.1, 0.0, 0.0),
                            (2.0, 0.0, 0.0, 0.0),
                        ],
                        position_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (1.0, 0.0, 0.5, 0.0),
                            (2.0, 0.0, 0.0, 0.0),
                        ])

    data += write_joint("upper", "root",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 2.0, 0.0),
                        rotation_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (0.5, 0.3, 0.0, 0.0),
                            (1.0, 0.0, 0.0, 0.0),
                        ],
                        position_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                        ])

    # --- Comment subversion section (subversion == 1) ---
    data += struct.pack("<I", 1)  # subversion for comments

    # Group comments (ReadComments<TempGroup>)
    data += write_comments([(0, "Torso group: main body mesh")])

    # Material comments (ReadComments<TempMaterial>)
    data += write_comments([(0, "Skin material with texture")])

    # Joint comments (ReadComments<TempJoint>)
    data += write_comments([
        (0, "Root joint at origin"),
        (1, "Upper body joint"),
    ])

    # Model comment
    data += write_model_comment("Test MS3D model with comments")

    return data


def generate_seed_subversion_weights():
    """Seed with subversion vertex weights (multi-bone skinning).

    Targets the per-vertex bone weight reading code path with subversion 2
    (which adds 4 extra bytes per vertex beyond subversion 1).
    """
    data = write_header()

    # 6 vertices (two triangles forming a strip)
    data += struct.pack("<H", 6)
    data += write_vertex(-1.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(0.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(-0.5, 1.0, 0.0, bone_id=0)
    data += write_vertex(0.0, 0.0, 0.0, bone_id=1)
    data += write_vertex(1.0, 0.0, 0.0, bone_id=1)
    data += write_vertex(0.5, 1.0, 0.0, bone_id=1)

    # 2 triangles
    data += struct.pack("<H", 2)
    data += write_triangle(0, 1, 2, group_index=0)
    data += write_triangle(3, 4, 5, group_index=0)

    # 1 group
    data += struct.pack("<H", 1)
    data += write_group("mesh", [0, 1], material_index=0)

    # 1 material
    data += struct.pack("<H", 1)
    data += write_material("default",
                           diffuse=(0.7, 0.7, 0.7, 1.0),
                           shininess=16.0)

    # 3 joints
    data += write_animation_header(fps=24.0, current_time=0.0, total_frames=48)
    data += struct.pack("<H", 3)

    data += write_joint("hip", "",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 0.0, 0.0),
                        rotation_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (2.0, 0.0, 0.0, 0.0),
                        ],
                        position_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (2.0, 0.0, 0.0, 0.0),
                        ])

    data += write_joint("leg_l", "hip",
                        rotation=(0.0, 0.0, 0.0),
                        position=(-0.5, -1.0, 0.0),
                        rotation_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (1.0, 0.3, 0.0, 0.0),
                            (2.0, 0.0, 0.0, 0.0),
                        ],
                        position_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                        ])

    data += write_joint("leg_r", "hip",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.5, -1.0, 0.0),
                        rotation_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (1.0, -0.3, 0.0, 0.0),
                            (2.0, 0.0, 0.0, 0.0),
                        ],
                        position_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                        ])

    # Comment subversion section
    data += struct.pack("<I", 1)  # subversion for comments

    # Group comments
    data += write_comments([(0, "Main mesh group")])
    # Material comments
    data += write_comments([(0, "Default grey material")])
    # Joint comments
    data += write_comments([(0, "Hip root"), (1, "Left leg")])
    # Model comment (0 means no model comment)
    data += struct.pack("<I", 0)

    # Subversion vertex weight data (subversion 2 => 4 extra bytes per vert)
    # Per vertex: 3x (bone_id u8, weight u8), then 4 extra bytes
    # The weight byte is 0-255 mapped to 0.0-1.0
    # bone_id[1..3], weights[0..2] from those bytes; weights[3] = 1 - sum
    weights = [
        [(1, 128), (2, 64), (255, 0)],   # v0: hip(primary), leg_l(50%), leg_r(25%)
        [(1, 200), (2, 55), (255, 0)],    # v1: blended
        [(0, 128), (255, 0), (255, 0)],   # v2: hip(50%), primary bone rest
        [(2, 128), (1, 64), (255, 0)],    # v3: leg_r/leg_l blend
        [(2, 200), (255, 0), (255, 0)],   # v4: mostly leg_r
        [(1, 100), (2, 100), (255, 0)],   # v5: even blend
    ]
    data += write_subversion_vertex_weights(6, weights, subversion=2)

    return data


def generate_seed_comments_subv1():
    """Seed with subversion 1 vertex weights (no extra bytes per vertex).

    Targets the subversion==1 specific code path.
    """
    data = write_header()

    # 3 vertices, simplest possible mesh
    data += struct.pack("<H", 3)
    data += write_vertex(0.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(1.0, 0.0, 0.0, bone_id=0)
    data += write_vertex(0.5, 1.0, 0.0, bone_id=1)

    # 1 triangle
    data += struct.pack("<H", 1)
    data += write_triangle(0, 1, 2)

    # 1 group
    data += struct.pack("<H", 1)
    data += write_group("tri", [0], material_index=0)

    # 1 material
    data += struct.pack("<H", 1)
    data += write_material("mat0",
                           diffuse=(0.5, 0.8, 0.5, 1.0),
                           transparency=0.9)

    # 2 joints
    data += write_animation_header(fps=24.0, current_time=0.0, total_frames=24)
    data += struct.pack("<H", 2)

    data += write_joint("base", "",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 0.0, 0.0),
                        rotation_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (1.0, 0.0, 0.5, 0.0),
                        ],
                        position_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                        ])

    data += write_joint("tip", "base",
                        rotation=(0.0, 0.0, 0.0),
                        position=(0.0, 1.0, 0.0),
                        rotation_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                            (0.5, 0.2, 0.0, 0.0),
                            (1.0, 0.0, 0.0, 0.0),
                        ],
                        position_keyframes=[
                            (0.0, 0.0, 0.0, 0.0),
                        ])

    # Comments subversion
    data += struct.pack("<I", 1)

    # Group comments (none)
    data += write_comments([])
    # Material comments (none)
    data += write_comments([])
    # Joint comments
    data += write_comments([(0, "Base joint"), (1, "Tip joint")])
    # Model comment
    data += write_model_comment("Subversion 1 test")

    # Subversion 1 vertex weights: no extra bytes per vertex
    weights = [
        [(1, 128), (255, 0), (255, 0)],  # v0: base + tip blend
        [(255, 0), (255, 0), (255, 0)],   # v1: primary bone only
        [(0, 200), (255, 0), (255, 0)],   # v2: mostly base
    ]
    data += write_subversion_vertex_weights(3, weights, subversion=1)

    return data


def generate_seed_nomat_default():
    """Seed with a group having no material (mat == -1 / 0xFF).

    Targets the need_default material creation code path.
    """
    data = write_header()

    # 6 verts, 2 tris, 2 groups - one with material, one without
    data += struct.pack("<H", 6)
    data += write_vertex(0.0, 0.0, 0.0)
    data += write_vertex(1.0, 0.0, 0.0)
    data += write_vertex(0.5, 1.0, 0.0)
    data += write_vertex(2.0, 0.0, 0.0)
    data += write_vertex(3.0, 0.0, 0.0)
    data += write_vertex(2.5, 1.0, 0.0)

    data += struct.pack("<H", 2)
    data += write_triangle(0, 1, 2, group_index=0)
    data += write_triangle(3, 4, 5, group_index=1)

    # 2 groups: group 0 has material, group 1 has no material (-1)
    data += struct.pack("<H", 2)
    data += write_group("with_mat", [0], material_index=0)
    data += write_group("no_mat", [1], material_index=-1)

    # 1 material (only used by group 0; group 1 triggers default material)
    data += struct.pack("<H", 1)
    data += write_material("red",
                           diffuse=(1.0, 0.0, 0.0, 1.0),
                           shininess=0.0,
                           transparency=1.0)

    # No joints
    data += write_animation_header(fps=24.0, current_time=0.0, total_frames=1)
    data += struct.pack("<H", 0)

    return data


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seeds = {
        "seed_comments.ms3d": generate_seed_comments,
        "seed_subversion_weights.ms3d": generate_seed_subversion_weights,
        "seed_comments_subv1.ms3d": generate_seed_comments_subv1,
        "seed_nomat_default.ms3d": generate_seed_nomat_default,
    }

    for filename, generator in seeds.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        data = generator()
        with open(filepath, "wb") as f:
            f.write(data)
        print(f"Written {filepath} ({len(data)} bytes)")

    # Verification
    print("\nVerification:")
    for filename in seeds:
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "rb") as f:
            magic = f.read(10)
            version = struct.unpack("<i", f.read(4))[0]
            size = os.path.getsize(filepath)
            print(f"  {filename}: magic={magic!r}, version={version}, size={size} bytes")


if __name__ == "__main__":
    main()
