#!/usr/bin/env python3
"""Generate MDL7 binary seed files for fuzzing.

Creates seeds that exercise:
- Bone structures with various naming sizes (16, 36, 48 bytes)
- Multiple skin types (0x10=material, 0x01=referrer, 0x30=material+HLSL)
- Double UV coordinate sets (triangle_stc_size >= 26)
- Multiple frames with bone transforms
- Vertex normal encoding variants (16-byte vs 26-byte mainvertex)
"""

import struct
import os
import math

# MDL7 magic
MAGIC_MDL7 = b'MDL7'

# Bone struct sizes
BONE_SIZE_NO_NAME = 16     # AI_MDL7_BONE_STRUCT_SIZE__NAME_IS_NOT_THERE
BONE_SIZE_NAME_20 = 36     # AI_MDL7_BONE_STRUCT_SIZE__NAME_IS_20_CHARS
BONE_SIZE_NAME_32 = 48     # AI_MDL7_BONE_STRUCT_SIZE__NAME_IS_32_CHARS

# SkinSet_MDL7: 3 uint16 st_index + 1 int32 material = 10 bytes
SKINSET_SIZE = 10
# Triangle with 1 UV set + material index: 6 + 10 = 16
TRI_SIZE_ONE_UV_MAT = 6 + SKINSET_SIZE  # 16
# Triangle with 2 UV sets: 6 + 2*10 = 26
TRI_SIZE_TWO_UV = 6 + 2 * SKINSET_SIZE  # 26

# Vertex sizes
MAINVERTEX_16 = 16  # AI_MDL7_FRAMEVERTEX120503_STCSIZE (quake2 normal index)
MAINVERTEX_26 = 26  # AI_MDL7_FRAMEVERTEX030305_STCSIZE (full float normals)

# Skin type flags
SKINTYPE_MATERIAL = 0x10
SKINTYPE_HLSL = 0x20
SKINTYPE_REFERRER = 0x01
SKINTYPE_ARGB8888 = 0x05   # ARGB8888 texture format

# BoneTransform_MDL7: 4*4 floats (64) + uint16 bone_index + 2 padding = 68
BONETRANS_SIZE = 68

# Header size = 48, Group header = 44, Frame header = 24, Skin header = 28
HEADER_SIZE = 48
GROUP_HEADER_SIZE = 44
FRAME_HEADER_SIZE = 24
SKIN_HEADER_SIZE = 28


def write_header(bones_num, groups_num, data_size, bone_stc_size,
                 skin_stc_size=28, colorvalue_stc_size=16, material_stc_size=68,
                 skinpoint_stc_size=8, triangle_stc_size=16,
                 mainvertex_stc_size=26, framevertex_stc_size=26,
                 bonetrans_stc_size=68, frame_stc_size=24):
    return struct.pack('<4si II i ii HHHHHHHHHH',
        MAGIC_MDL7, 110, bones_num, groups_num, data_size, 0, 0,
        bone_stc_size, skin_stc_size, colorvalue_stc_size, material_stc_size,
        skinpoint_stc_size, triangle_stc_size, mainvertex_stc_size,
        framevertex_stc_size, bonetrans_stc_size, frame_stc_size)


def write_bone(parent_index, x, y, z, name=b'', bone_stc_size=36):
    data = struct.pack('<Hxx fff', parent_index, x, y, z)
    if bone_stc_size > BONE_SIZE_NO_NAME:
        name_size = bone_stc_size - 16
        padded_name = name[:name_size].ljust(name_size, b'\x00')
        data += padded_name
    return data


def write_group(typ, deformers, max_weights, groupdata_size, name,
                numskins, num_stpts, numtris, numverts, numframes):
    padded_name = name[:16].ljust(16, b'\x00')
    return struct.pack('<bbbx i 16s iiiii',
        typ, deformers, max_weights,
        groupdata_size, padded_name,
        numskins, num_stpts, numtris, numverts, numframes)


def write_skin_material_only(material_data):
    """Material-only skin (typ=0x10, w=0, h=0). No texture pixel data."""
    header = struct.pack('<Bxxx ii 16s', SKINTYPE_MATERIAL, 0, 0, b'\x00' * 16)
    return header + material_data


def write_skin_material_hlsl(material_data, hlsl_text):
    """Material+HLSL skin (typ=0x30, w=0, h=0)."""
    typ = SKINTYPE_MATERIAL | SKINTYPE_HLSL  # 0x30
    header = struct.pack('<Bxxx ii 16s', typ, 0, 0, b'\x00' * 16)
    hlsl_bytes = hlsl_text.encode('ascii')
    hlsl_data = struct.pack('<i', len(hlsl_bytes)) + hlsl_bytes
    return header + material_data + hlsl_data


def write_skin_argb8888(width, height, tex_name, pixels):
    """ARGB8888 texture skin (typ=0x05). pixels must be width*height*4 bytes."""
    padded_name = tex_name[:16].ljust(16, b'\x00')
    header = struct.pack('<Bxxx ii 16s', SKINTYPE_ARGB8888, width, height, padded_name)
    return header + pixels


def write_skin_argb8888_material(width, height, tex_name, pixels, material_data):
    """ARGB8888 texture + material (typ=0x15)."""
    padded_name = tex_name[:16].ljust(16, b'\x00')
    typ = SKINTYPE_ARGB8888 | SKINTYPE_MATERIAL  # 0x15
    header = struct.pack('<Bxxx ii 16s', typ, width, height, padded_name)
    return header + pixels + material_data


def write_skin_referrer(referrer_index=0):
    """Referrer skin (typ=0x01). width=referrer_index, height=0."""
    return struct.pack('<Bxxx ii 16s', SKINTYPE_REFERRER, referrer_index, 0, b'\x00' * 16)


def write_material_mdl7(diffuse=(0.8, 0.2, 0.2, 1.0), power=32.0):
    """Material_MDL7: 4 ColorValue_MDL7 (4 floats each=16 bytes) + float Power = 68 bytes."""
    d = struct.pack('<ffff', *diffuse)
    a = struct.pack('<ffff', 0.1, 0.1, 0.1, 0.8)
    s = struct.pack('<ffff', 1.0, 1.0, 1.0, 1.0)
    e = struct.pack('<ffff', 0.0, 0.0, 0.0, 1.0)
    return d + a + s + e + struct.pack('<f', power)


def write_texcoord(u, v):
    return struct.pack('<ff', u, v)


def write_triangle_one_uv(v0, v1, v2, st0, st1, st2, mat_idx=0):
    data = struct.pack('<HHH', v0, v1, v2)
    data += struct.pack('<HHHi', st0, st1, st2, mat_idx)
    return data


def write_triangle_two_uv(v0, v1, v2, st0, st1, st2, mat0,
                           st0b, st1b, st2b, mat1):
    data = struct.pack('<HHH', v0, v1, v2)
    data += struct.pack('<HHHi', st0, st1, st2, mat0)
    data += struct.pack('<HHHi', st0b, st1b, st2b, mat1)
    return data


def write_vertex_26(x, y, z, bone_index, nx, ny, nz):
    """26-byte vertex: xyz(12) + bone_index(2) + normal_xyz(12) = 26."""
    return struct.pack('<fffH fff', x, y, z, bone_index, nx, ny, nz)


def write_vertex_16(x, y, z, bone_index, normal_index):
    """16-byte vertex: xyz(12) + bone_index(2) + normal_index(1) + pad(1) = 16."""
    return struct.pack('<fffH Bx', x, y, z, bone_index, normal_index)


def write_frame(name, vertices_count, transmatrix_count):
    padded_name = name[:16].ljust(16, b'\x00')
    return struct.pack('<16s II', padded_name, vertices_count, transmatrix_count)


def write_bone_transform(bone_index, matrix=None):
    if matrix is None:
        matrix = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    return struct.pack('<16f Hxx', *matrix, bone_index)


def generate_basic_mdl7():
    """Basic MDL7: 1 root bone (named, 20-char), 1 group, material-only skin, 1 frame."""
    bone_stc = BONE_SIZE_NAME_20
    tri_stc = TRI_SIZE_ONE_UV_MAT
    vert_stc = MAINVERTEX_26

    # Note: Only root bones (parent=0xFFFF) to avoid bug in AddBonesToNodeGraph_3DGS_MDL7
    # where recursive child bone processing reads past the array end.
    bones = write_bone(0xFFFF, 0, 0, 0, b'Root', bone_stc)

    mat = write_material_mdl7()
    skin_data = write_skin_material_only(mat)

    uvs = write_texcoord(0, 0) + write_texcoord(1, 0) + write_texcoord(0.5, 1)
    tris = write_triangle_one_uv(0, 1, 2, 0, 1, 2, 0)

    verts = write_vertex_26(-1, 0, 0, 0, 0, 0, 1)
    verts += write_vertex_26(1, 0, 0, 0, 0, 0, 1)
    verts += write_vertex_26(0, 1, 0, 0, 0, 0, 1)

    frame = write_frame(b'frame0', 0, 0)

    group_payload = skin_data + uvs + tris + verts + frame
    group_hdr = write_group(1, 0, 0, len(group_payload) + GROUP_HEADER_SIZE,
                            b'Group0', 1, 3, 1, 3, 1)

    body = bones + group_hdr + group_payload
    header = write_header(1, 1, len(body), bone_stc,
                          triangle_stc_size=tri_stc, mainvertex_stc_size=vert_stc)
    return header + body


def generate_bones_animated_mdl7():
    """MDL7: 3 bones (32-char names) with hierarchy, 2 animation frames with bone transforms."""
    bone_stc = BONE_SIZE_NAME_32
    tri_stc = TRI_SIZE_ONE_UV_MAT
    vert_stc = MAINVERTEX_26

    bones = write_bone(0xFFFF, 0, 0, 0, b'RootBone', bone_stc)
    bones += write_bone(0, 2.0, 0, 0, b'ArmBone', bone_stc)
    bones += write_bone(1, 1.5, 0, 0, b'HandBone', bone_stc)

    mat = write_material_mdl7()
    skin_data = write_skin_material_only(mat)

    uvs = (write_texcoord(0, 0) + write_texcoord(1, 0) +
           write_texcoord(0.5, 1) + write_texcoord(0.5, 0.5))

    tris = write_triangle_one_uv(0, 1, 2, 0, 1, 2, 0)
    tris += write_triangle_one_uv(1, 2, 3, 1, 2, 3, 0)

    verts = write_vertex_26(-1, 0, 0, 0, 0, 0, 1)
    verts += write_vertex_26(1, 0, 0, 1, 0, 0, 1)
    verts += write_vertex_26(0, 1, 0, 1, 0, 0, 1)
    verts += write_vertex_26(2, 1, 0, 2, 0, 0, 1)

    # Frame 0: rest pose, 3 bone transforms
    frame0 = write_frame(b'rest', 0, 3)
    bt0 = (write_bone_transform(0) +
           write_bone_transform(1, [1,0,0,0, 0,1,0,0, 0,0,1,0, 2,0,0,1]) +
           write_bone_transform(2, [1,0,0,0, 0,1,0,0, 0,0,1,0, 3.5,0,0,1]))

    # Frame 1: animated, 3 bone transforms
    c, s = math.cos(0.5), math.sin(0.5)
    frame1 = write_frame(b'anim1', 0, 3)
    bt1 = (write_bone_transform(0) +
           write_bone_transform(1, [c,-s,0,0, s,c,0,0, 0,0,1,0, 2,0,0,1]) +
           write_bone_transform(2, [c,s,0,0, -s,c,0,0, 0,0,1,0, 3,0.5,0,1]))

    group_payload = skin_data + uvs + tris + verts + frame0 + bt0 + frame1 + bt1
    group_hdr = write_group(1, 0, 0, len(group_payload) + GROUP_HEADER_SIZE,
                            b'AnimGroup', 1, 4, 2, 4, 2)

    body = bones + group_hdr + group_payload
    header = write_header(3, 1, len(body), bone_stc,
                          triangle_stc_size=tri_stc, mainvertex_stc_size=vert_stc,
                          bonetrans_stc_size=BONETRANS_SIZE)
    return header + body


def generate_dual_uv_mdl7():
    """MDL7: no-name bones, dual UV, ARGB8888 texture + referrer skin."""
    bone_stc = BONE_SIZE_NO_NAME
    tri_stc = TRI_SIZE_TWO_UV
    vert_stc = MAINVERTEX_16

    bones = write_bone(0xFFFF, 0, 0, 0, bone_stc_size=bone_stc)

    # Skin 0: 2x2 ARGB8888 texture (4 bytes per pixel = 16 bytes)
    pixels = bytes([255, 0, 0, 255,  0, 255, 0, 255,
                    0, 0, 255, 255,  255, 255, 0, 255])
    skin0 = write_skin_argb8888(2, 2, b'tex_diffuse', pixels)

    # Skin 1: referrer to skin 0
    skin1 = write_skin_referrer(0)

    uvs = (write_texcoord(0, 0) + write_texcoord(1, 0) +
           write_texcoord(0.5, 1) + write_texcoord(0.5, 0.5) +
           write_texcoord(0.25, 0.25) + write_texcoord(0.75, 0.75))

    tris = write_triangle_two_uv(0, 1, 2, 0, 1, 2, 0, 3, 4, 5, 1)
    tris += write_triangle_two_uv(1, 2, 3, 1, 2, 3, 0, 4, 5, 3, 1)

    verts = write_vertex_16(-1, 0, 0, 0, 0)
    verts += write_vertex_16(1, 0, 0, 0, 22)
    verts += write_vertex_16(0, 1, 0, 0, 46)
    verts += write_vertex_16(0, 0, 1, 0, 89)

    frame = write_frame(b'frame0', 0, 0)

    group_payload = skin0 + skin1 + uvs + tris + verts + frame
    group_hdr = write_group(1, 0, 0, len(group_payload) + GROUP_HEADER_SIZE,
                            b'DualUV', 2, 6, 2, 4, 1)

    body = bones + group_hdr + group_payload
    header = write_header(1, 1, len(body), bone_stc,
                          triangle_stc_size=tri_stc, mainvertex_stc_size=vert_stc)
    return header + body


def generate_material_hlsl_mdl7():
    """MDL7: material + HLSL shader skin."""
    bone_stc = BONE_SIZE_NAME_20
    tri_stc = TRI_SIZE_ONE_UV_MAT
    vert_stc = MAINVERTEX_26

    bones = write_bone(0xFFFF, 0, 0, 0, b'Root', bone_stc)

    mat = write_material_mdl7()
    hlsl = "float4 ps() : COLOR { return 1; }"
    skin_data = write_skin_material_hlsl(mat, hlsl)

    uvs = write_texcoord(0, 0) + write_texcoord(1, 0) + write_texcoord(0.5, 1)
    tris = write_triangle_one_uv(0, 1, 2, 0, 1, 2, 0)

    verts = write_vertex_26(0, 0, 0, 0, 0, 0, 1)
    verts += write_vertex_26(1, 0, 0, 0, 0, 0, 1)
    verts += write_vertex_26(0.5, 1, 0, 0, 0, 0, 1)

    frame = write_frame(b'frame0', 0, 0)

    group_payload = skin_data + uvs + tris + verts + frame
    group_hdr = write_group(1, 0, 0, len(group_payload) + GROUP_HEADER_SIZE,
                            b'HLSLGroup', 1, 3, 1, 3, 1)

    body = bones + group_hdr + group_payload
    header = write_header(1, 1, len(body), bone_stc,
                          triangle_stc_size=tri_stc, mainvertex_stc_size=vert_stc)
    return header + body


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'test', 'models', 'MDL', 'fuzz_seeds')
    os.makedirs(out_dir, exist_ok=True)

    seeds = [
        ('seed_mdl7_basic.mdl', generate_basic_mdl7()),
        ('seed_mdl7_bones_animated.mdl', generate_bones_animated_mdl7()),
        ('seed_mdl7_dual_uv.mdl', generate_dual_uv_mdl7()),
        ('seed_mdl7_material_hlsl.mdl', generate_material_hlsl_mdl7()),
    ]

    for name, data in seeds:
        path = os.path.join(out_dir, name)
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  Created {name}: {len(data)} bytes")


if __name__ == '__main__':
    main()
