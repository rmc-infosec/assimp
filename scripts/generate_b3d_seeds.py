#!/usr/bin/env python3
"""Generate B3D (BlitzBasic 3D) binary seed files for fuzzing.

B3D binary format structure:
- Each chunk: 4-byte tag + 4-byte size (of remaining content) + content
- BB3D is the root chunk, contains version (int32) then sub-chunks
- TEXS: texture definitions (string name, int flags, int blend, vec2 pos, vec2 scale, float rot)
- BRUS: brush/material definitions (int n_texs, then per brush: string name, vec3 color,
        float alpha, float shiny, int blend, int fx, then n_texs * int texid)
- NODE: node hierarchy (string name, vec3 pos, vec3 scale, quat rot, then sub-chunks)
- MESH: mesh data (int matid, then VRTS/TRIS sub-chunks)
- VRTS: vertex data (int flags, int tcsets, int tcsize, then vertex data)
        flags: 1=has normals, 2=has colors(rgba as quat)
- TRIS: triangle data (int matid, then triples of int indices)
- BONE: bone weights (pairs of int vertex_id, float weight)
- KEYS: animation keyframes (int flags, then per frame: int frame, optional vec3/vec3/quat)
        flags: 1=position, 2=scale, 4=rotation
- ANIM: animation info (int flags, int frames, float fps)
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test", "models", "B3D", "fuzz_seeds")


def write_int(val):
    return struct.pack('<i', val)


def write_float(val):
    return struct.pack('<f', val)


def write_vec2(x, y):
    return struct.pack('<ff', x, y)


def write_vec3(x, y, z):
    return struct.pack('<fff', x, y, z)


def write_quat(w, x, y, z):
    return struct.pack('<ffff', w, x, y, z)


def write_string(s):
    return s.encode('ascii') + b'\x00'


def make_chunk(tag, content):
    """Create a B3D chunk: 4-byte tag + 4-byte size + content."""
    assert len(tag) == 4
    return tag.encode('ascii') + struct.pack('<I', len(content)) + content


def make_texs(textures):
    """Create TEXS chunk with texture definitions."""
    data = b''
    for name, flags, blend, pos, scale, rot in textures:
        data += write_string(name)
        data += write_int(flags)
        data += write_int(blend)
        data += write_vec2(*pos)
        data += write_vec2(*scale)
        data += write_float(rot)
    return make_chunk('TEXS', data)


def make_brus(n_texs, brushes):
    """Create BRUS chunk with brush/material definitions."""
    data = write_int(n_texs)
    for name, color, alpha, shiny, blend, fx, tex_ids in brushes:
        data += write_string(name)
        data += write_vec3(*color)
        data += write_float(alpha)
        data += write_float(shiny)
        data += write_int(blend)
        data += write_int(fx)
        for tid in tex_ids:
            data += write_int(tid)
    return make_chunk('BRUS', data)


def make_vrts(flags, tcsets, tcsize, vertices):
    """Create VRTS chunk.
    flags: 1=normals, 2=colors
    Each vertex: (pos, [normal], [color_rgba], [tc0, tc1, ...])
    """
    data = write_int(flags)
    data += write_int(tcsets)
    data += write_int(tcsize)
    for v in vertices:
        idx = 0
        # position (always present)
        data += write_vec3(*v[idx]); idx += 1
        # normals
        if flags & 1:
            data += write_vec3(*v[idx]); idx += 1
        # colors (as quat: w,x,y,z -> r,g,b,a)
        if flags & 2:
            data += write_quat(*v[idx]); idx += 1
        # texture coords
        for tc_set in range(tcsets):
            tc = v[idx]; idx += 1
            for k in range(tcsize):
                data += write_float(tc[k] if k < len(tc) else 0.0)
    return make_chunk('VRTS', data)


def make_tris(matid, triangles):
    """Create TRIS chunk with triangle indices."""
    data = write_int(matid)
    for i0, i1, i2 in triangles:
        data += write_int(i0)
        data += write_int(i1)
        data += write_int(i2)
    return make_chunk('TRIS', data)


def make_mesh(matid, vrts_chunk, tris_chunks):
    """Create MESH chunk containing VRTS and TRIS sub-chunks."""
    data = write_int(matid)
    data += vrts_chunk
    for tris in tris_chunks:
        data += tris
    return make_chunk('MESH', data)


def make_bone(bone_weights):
    """Create BONE chunk with (vertex_id, weight) pairs."""
    data = b''
    for vid, weight in bone_weights:
        data += write_int(vid)
        data += write_float(weight)
    return make_chunk('BONE', data)


def make_keys(flags, keyframes):
    """Create KEYS chunk.
    flags: 1=position, 2=scale, 4=rotation
    keyframes: list of (frame, [pos], [scale], [rot])
    """
    data = write_int(flags)
    for kf in keyframes:
        idx = 0
        data += write_int(kf[idx]); idx += 1  # frame
        if flags & 1:
            data += write_vec3(*kf[idx]); idx += 1
        if flags & 2:
            data += write_vec3(*kf[idx]); idx += 1
        if flags & 4:
            data += write_quat(*kf[idx]); idx += 1
    return make_chunk('KEYS', data)


def make_anim(flags, frames, fps):
    """Create ANIM chunk."""
    data = write_int(flags)
    data += write_int(frames)
    data += write_float(fps)
    return make_chunk('ANIM', data)


def make_node(name, pos, scale, rot, sub_chunks):
    """Create NODE chunk with name, transform, and sub-chunks."""
    data = write_string(name)
    data += write_vec3(*pos)
    data += write_vec3(*scale)
    data += write_quat(*rot)  # w, x, y, z
    for chunk in sub_chunks:
        data += chunk
    return make_chunk('NODE', data)


def make_bb3d(version, chunks):
    """Create top-level BB3D chunk."""
    data = write_int(version)
    for chunk in chunks:
        data += chunk
    return make_chunk('BB3D', data)


def seed_basic_mesh():
    """Seed 1: Minimal mesh - just a triangle with normals and texcoords."""
    vrts = make_vrts(
        flags=1,  # normals
        tcsets=1, tcsize=2,
        vertices=[
            # (pos, normal, tc)
            ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0)),
            ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0)),
            ((0.5, 1.0, 0.0), (0.0, 0.0, 1.0), (0.5, 1.0)),
        ]
    )
    tris = make_tris(0, [(0, 1, 2)])
    mesh = make_mesh(0, vrts, [tris])
    node = make_node("Triangle", (0, 0, 0), (1, 1, 1), (-1, 0, 0, 0), [mesh])
    brus = make_brus(0, [("default", (1.0, 1.0, 1.0), 1.0, 0.0, 0, 0, [])])
    return make_bb3d(1, [brus, node])


def seed_textured_mesh():
    """Seed 2: Mesh with textures and brushes referencing them."""
    texs = make_texs([
        ("diffuse.png", 0, 0, (0.0, 0.0), (1.0, 1.0), 0.0),
        ("normal.png", 0, 0, (0.0, 0.0), (1.0, 1.0), 0.0),
    ])
    brus = make_brus(2, [
        ("mat0", (0.8, 0.2, 0.1), 1.0, 0.5, 1, 0x10, [0, 1]),
        ("mat1", (0.1, 0.8, 0.2), 0.8, 0.3, 0, 0, [-1, 0]),
    ])
    vrts = make_vrts(
        flags=1, tcsets=1, tcsize=2,
        vertices=[
            ((0, 0, 0), (0, 1, 0), (0.0, 0.0)),
            ((1, 0, 0), (0, 1, 0), (1.0, 0.0)),
            ((1, 0, 1), (0, 1, 0), (1.0, 1.0)),
            ((0, 0, 1), (0, 1, 0), (0.0, 1.0)),
        ]
    )
    tris0 = make_tris(0, [(0, 1, 2)])
    tris1 = make_tris(1, [(0, 2, 3)])
    mesh = make_mesh(0, vrts, [tris0, tris1])
    node = make_node("Quad", (0, 0, 0), (1, 1, 1), (-1, 0, 0, 0), [mesh])
    return make_bb3d(1, [texs, brus, node])


def seed_colored_vertices():
    """Seed 3: Mesh with vertex colors (vflags=2) and no normals."""
    vrts = make_vrts(
        flags=2,  # colors only
        tcsets=0, tcsize=0,
        vertices=[
            # (pos, color_rgba_as_quat)
            ((0, 0, 0), (1.0, 0.0, 0.0, 1.0)),
            ((1, 0, 0), (0.0, 1.0, 0.0, 1.0)),
            ((0.5, 1, 0), (0.0, 0.0, 1.0, 1.0)),
        ]
    )
    tris = make_tris(0, [(0, 1, 2)])
    mesh = make_mesh(0, vrts, [tris])
    brus = make_brus(0, [("col_mat", (1, 1, 1), 1.0, 0.0, 0, 0, [])])
    node = make_node("ColorTri", (0, 0, 0), (1, 1, 1), (-1, 0, 0, 0), [mesh])
    return make_bb3d(1, [brus, node])


def seed_normals_and_colors():
    """Seed 4: Mesh with both normals and vertex colors (vflags=3)."""
    vrts = make_vrts(
        flags=3,  # normals + colors
        tcsets=1, tcsize=2,
        vertices=[
            # (pos, normal, color, tc)
            ((0, 0, 0), (0, 0, 1), (1.0, 0.5, 0.5, 1.0), (0.0, 0.0)),
            ((1, 0, 0), (0, 0, 1), (0.5, 1.0, 0.5, 1.0), (1.0, 0.0)),
            ((0.5, 1, 0), (0, 0, 1), (0.5, 0.5, 1.0, 1.0), (0.5, 1.0)),
        ]
    )
    tris = make_tris(0, [(0, 1, 2)])
    mesh = make_mesh(0, vrts, [tris])
    brus = make_brus(0, [("full_mat", (1, 1, 1), 1.0, 0.8, 0, 0, [])])
    node = make_node("FullVert", (0, 0, 0), (1, 1, 1), (-1, 0, 0, 0), [mesh])
    return make_bb3d(1, [brus, node])


def seed_animated_skeleton():
    """Seed 5: Skeletal animation with BONE, KEYS, ANIM chunks."""
    brus = make_brus(0, [("skin", (0.9, 0.7, 0.5), 1.0, 0.1, 0, 0, [])])

    # 4 vertices for a simple quad
    vrts = make_vrts(
        flags=1, tcsets=1, tcsize=2,
        vertices=[
            ((0, 0, 0), (0, 0, 1), (0, 0)),
            ((1, 0, 0), (0, 0, 1), (1, 0)),
            ((1, 2, 0), (0, 0, 1), (1, 1)),
            ((0, 2, 0), (0, 0, 1), (0, 1)),
        ]
    )
    tris = make_tris(0, [(0, 1, 2), (0, 2, 3)])
    mesh = make_mesh(0, vrts, [tris])

    # Bone weights: vertex 0,1 -> bone 0; vertex 2,3 -> bone 1
    bone0 = make_bone([(0, 1.0), (1, 1.0)])
    bone1 = make_bone([(2, 0.8), (3, 0.8), (1, 0.2), (0, 0.0)])

    anim = make_anim(0, 30, 24.0)

    # KEYS with position only (flags=1)
    keys_pos = make_keys(1, [
        (0, (0, 0, 0)),
        (15, (0, 1, 0)),
        (30, (0, 0, 0)),
    ])

    # KEYS with rotation only (flags=4)
    keys_rot = make_keys(4, [
        (0, (-1.0, 0, 0, 0)),
        (15, (-0.707, 0.707, 0, 0)),
        (30, (-1.0, 0, 0, 0)),
    ])

    # KEYS with scale only (flags=2)
    keys_scale = make_keys(2, [
        (0, (1, 1, 1)),
        (15, (1.5, 1.5, 1.5)),
        (30, (1, 1, 1)),
    ])

    # KEYS with all three (flags=7)
    keys_all = make_keys(7, [
        (0, (0, 0, 0), (1, 1, 1), (-1.0, 0, 0, 0)),
        (30, (0, 1, 0), (1.2, 1.2, 1.2), (-0.707, 0.707, 0, 0)),
    ])

    # Child bone node
    child_node = make_node("Bone1", (0, 1, 0), (1, 1, 1), (-1, 0, 0, 0),
                           [bone1, keys_rot])

    # Root bone node
    root_bone = make_node("Bone0", (0, 0, 0), (1, 1, 1), (-1, 0, 0, 0),
                          [mesh, bone0, anim, keys_pos, child_node])

    return make_bb3d(1, [brus, root_bone])


def seed_multi_tc_sets():
    """Seed 6: Multiple texture coordinate sets (tcsets=2, tcsize=3)."""
    vrts = make_vrts(
        flags=0,  # no normals, no colors
        tcsets=2, tcsize=3,
        vertices=[
            # (pos, tc0, tc1)
            ((0, 0, 0), (0.0, 0.0, 0.0), (0.5, 0.5, 0.0)),
            ((1, 0, 0), (1.0, 0.0, 0.0), (0.5, 0.5, 0.0)),
            ((0.5, 1, 0), (0.5, 1.0, 0.0), (0.5, 0.5, 1.0)),
        ]
    )
    tris = make_tris(0, [(0, 1, 2)])
    mesh = make_mesh(0, vrts, [tris])
    brus = make_brus(0, [("multi_tc", (1, 1, 1), 1.0, 0.0, 0, 0, [])])
    node = make_node("MultiTC", (2.0, 0, 0), (1, 1, 1), (-1, 0, 0, 0), [mesh])
    return make_bb3d(1, [brus, node])


def seed_nested_nodes():
    """Seed 7: Nested node hierarchy with transforms."""
    brus = make_brus(0, [("nested_mat", (0.5, 0.5, 0.5), 1.0, 0.0, 0, 0, [])])

    def simple_triangle_mesh():
        vrts = make_vrts(flags=0, tcsets=0, tcsize=0, vertices=[
            ((0, 0, 0),), ((1, 0, 0),), ((0.5, 1, 0),),
        ])
        tris = make_tris(0, [(0, 1, 2)])
        return make_mesh(0, vrts, [tris])

    leaf1 = make_node("Leaf1", (1, 0, 0), (0.5, 0.5, 0.5), (-1, 0, 0, 0),
                       [simple_triangle_mesh()])
    leaf2 = make_node("Leaf2", (-1, 0, 0), (0.5, 0.5, 0.5), (-0.707, 0, 0.707, 0),
                       [simple_triangle_mesh()])
    mid = make_node("Mid", (0, 2, 0), (1, 1, 1), (-1, 0, 0, 0),
                     [leaf1, leaf2])
    root = make_node("Root", (0, 0, 0), (1, 1, 1), (-1, 0, 0, 0),
                      [simple_triangle_mesh(), mid])
    return make_bb3d(1, [brus, root])


def seed_full_featured():
    """Seed 8: Full-featured B3D with all chunk types combined."""
    texs = make_texs([
        ("skin.png", 1, 2, (0.1, 0.2), (2.0, 2.0), 45.0),
    ])
    brus = make_brus(1, [
        ("shiny_skin", (0.9, 0.8, 0.7), 1.0, 0.9, 1, 0x10, [0]),
    ])

    vrts = make_vrts(
        flags=3,  # normals + colors
        tcsets=1, tcsize=2,
        vertices=[
            ((0, 0, 0), (0, 0, 1), (1, 0, 0, 1), (0, 0)),
            ((1, 0, 0), (0, 0, 1), (0, 1, 0, 1), (1, 0)),
            ((1, 1, 0), (0, 0, 1), (0, 0, 1, 1), (1, 1)),
            ((0, 1, 0), (0, 0, 1), (1, 1, 0, 1), (0, 1)),
            ((0.5, 2, 0), (0, 0, 1), (1, 0, 1, 1), (0.5, 1)),
        ]
    )
    tris = make_tris(0, [(0, 1, 2), (0, 2, 3), (3, 2, 4)])
    mesh = make_mesh(0, vrts, [tris])

    bone0 = make_bone([(0, 1.0), (1, 0.8), (3, 0.5)])
    bone1 = make_bone([(2, 1.0), (4, 1.0), (1, 0.2), (3, 0.5)])

    anim = make_anim(1, 60, 30.0)

    keys_all = make_keys(7, [
        (0, (0, 0, 0), (1, 1, 1), (-1.0, 0, 0, 0)),
        (20, (0, 0.5, 0), (1.1, 1.1, 1.1), (-0.866, 0.5, 0, 0)),
        (40, (0, 1, 0), (1.2, 1.0, 1.0), (-0.707, 0.707, 0, 0)),
        (60, (0, 0, 0), (1, 1, 1), (-1.0, 0, 0, 0)),
    ])

    child = make_node("UpperBone", (0, 1, 0), (1, 1, 1), (-1, 0, 0, 0),
                       [bone1, keys_all])
    root = make_node("RootBone", (0, 0, 0), (1, 1, 1), (-1, 0, 0, 0),
                      [mesh, bone0, anim, keys_all, child])
    return make_bb3d(1, [texs, brus, root])


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seeds = {
        "seed_basic_mesh.b3d": seed_basic_mesh,
        "seed_textured.b3d": seed_textured_mesh,
        "seed_colored_verts.b3d": seed_colored_vertices,
        "seed_normals_colors.b3d": seed_normals_and_colors,
        "seed_animated.b3d": seed_animated_skeleton,
        "seed_multi_tc.b3d": seed_multi_tc_sets,
        "seed_nested_nodes.b3d": seed_nested_nodes,
        "seed_full_featured.b3d": seed_full_featured,
    }

    for name, gen_func in seeds.items():
        path = os.path.join(OUTPUT_DIR, name)
        data = gen_func()
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  {name}: {len(data)} bytes")

    print(f"\nGenerated {len(seeds)} B3D seed files in {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
