#!/usr/bin/env python3
"""Generate binary Q3D (Quick3D) seed files for fuzzing.

Quick3D format (.q3o / .q3s):
  - Header: "quick3Do" or "quick3Ds" (8 bytes) + version (2 bytes) +
    numMeshes (4) + numMats (4) + numTextures (4) = 22 bytes header
  - Chunk types: 'm' (meshes), 'c' (materials), 't' (textures), 's' (scene)
  - The loader reads chunks in order until EOF or 's' (scene) chunk
  - Mesh chunk: for each mesh: numVerts(4), verts(12*n), numFaces(4),
    face_indices_count(2*n), indices(4*n per face), mat_indices(4*n),
    numNormals(4), normals(12*n), numUVs(4), [UVs + UV indices], 36 skip bytes
  - Material chunk: name(null-term string), ambient(12), diffuse(12),
    specular(12), transparency(4), texIdx(4)
  - Texture chunk: name(null-term), width(4), height(4), texels(3*w*h)
  - Scene chunk: skip(12), 4x4 matrix(64), skip(16), camera pos(12),
    skip(12), fgColor(12), skip(29), light color(12), t1(4), t2(4),
    bg name(null-term), skip(t1*t2*3 + 20)
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test", "models", "Q3D", "fuzz_seeds")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def write_float(f):
    return struct.pack('<f', f)


def write_u32(v):
    return struct.pack('<I', v)


def write_u16(v):
    return struct.pack('<H', v)


def write_u8(v):
    return struct.pack('<B', v)


def make_header(sig, version, num_meshes, num_mats, num_textures):
    """Build the 22-byte Q3D header."""
    # sig is 8 bytes like "quick3Do"
    # version is 2 chars, e.g. "30"
    return (sig.encode('ascii')[:8] +
            version.encode('ascii')[:2] +
            write_u32(num_meshes) +
            write_u32(num_mats) +
            write_u32(num_textures))


def make_vertex(x, y, z):
    return write_float(x) + write_float(y) + write_float(z)


def make_mesh_chunk(vertices, faces, normals, uvs=None, face_uvindices=None,
                    has_textures=False, version_major='3', version_minor='0'):
    """Build mesh data for one mesh inside an 'm' chunk.

    faces: list of (num_indices, [vertex_indices], material_index)
    normals: list of (x,y,z)
    uvs: optional list of (u,v)
    face_uvindices: optional list of lists of uv indices per face
    """
    data = b''

    # Vertices
    data += write_u32(len(vertices))
    for v in vertices:
        data += make_vertex(*v)

    # Faces
    num_faces = len(faces)
    data += write_u32(num_faces)

    # Number of indices per face
    for f in faces:
        data += write_u16(f[0])

    # Indices per face
    for f in faces:
        for idx in f[1]:
            data += write_u32(idx)

    # Material indices per face
    for f in faces:
        data += write_u32(f[2])

    # Normals
    data += write_u32(len(normals))
    for n in normals:
        data += make_vertex(*n)

    # UV coords
    if has_textures and uvs:
        data += write_u32(len(uvs))
        for uv in uvs:
            data += write_float(uv[0]) + write_float(uv[1])
        # UV indices per face
        for i, f in enumerate(faces):
            for idx in (face_uvindices[i] if face_uvindices else f[1]):
                data += write_u32(idx)
    else:
        data += write_u32(0)

    # 36 bytes of skipped data
    data += b'\x00' * 36

    # If version > '30', skip face_count extra bytes
    if version_minor > '0' and version_major == '3':
        data += b'\x00' * num_faces

    return data


def make_material_chunk(name, ambient, diffuse, specular, transparency, tex_idx):
    """Build one material inside a 'c' chunk."""
    data = b''
    # Name (null-terminated)
    data += name.encode('ascii') + b'\x00'
    # Ambient
    data += write_float(ambient[0]) + write_float(ambient[1]) + write_float(ambient[2])
    # Diffuse
    data += write_float(diffuse[0]) + write_float(diffuse[1]) + write_float(diffuse[2])
    # Specular
    data += write_float(specular[0]) + write_float(specular[1]) + write_float(specular[2])
    # Transparency
    data += write_float(transparency)
    # Texture index
    data += write_u32(tex_idx)
    return data


def make_texture_chunk(name, width, height, pixels):
    """Build one texture in a 't' chunk.

    pixels: list of (r,g,b) tuples, length = width*height
    """
    data = b''
    data += name.encode('ascii') + b'\x00'
    data += write_u32(width)
    data += write_u32(height)
    for p in pixels:
        data += write_u8(p[0]) + write_u8(p[1]) + write_u8(p[2])
    return data


def make_scene_chunk(camera_pos=(0, 0, 5), fg_color=(0.8, 0.8, 0.8),
                     light_color=(1.0, 1.0, 1.0)):
    """Build the 's' (scene) chunk data."""
    data = b''
    # Skip 12 bytes (position)
    data += b'\x00' * 12
    # 4x4 identity matrix
    for i in range(4):
        for j in range(4):
            data += write_float(1.0 if i == j else 0.0)
    # Skip 16 bytes
    data += b'\x00' * 16
    # Camera position
    data += write_float(camera_pos[0]) + write_float(camera_pos[1]) + write_float(camera_pos[2])
    # Skip eye rotation (12 bytes)
    data += b'\x00' * 12
    # Foreground color
    data += write_float(fg_color[0]) + write_float(fg_color[1]) + write_float(fg_color[2])
    # Skip 29 bytes
    data += b'\x00' * 29
    # Light color
    data += write_float(light_color[0]) + write_float(light_color[1]) + write_float(light_color[2])
    # t1, t2 (background texture dimensions, set to 0)
    data += write_u32(0)
    data += write_u32(0)
    # Background name (null-terminated empty)
    data += b'\x00'
    # Skip t1*t2*3 + 20 = 0 + 20 = 20 bytes
    data += b'\x00' * 20
    return data


def seed_minimal_triangle():
    """Minimal Q3D with a single triangle, no textures, no scene chunk."""
    header = make_header("quick3Do", "30", 1, 1, 0)

    # Material chunk
    mat_data = make_material_chunk("mat0", (0.2, 0.2, 0.2), (0.8, 0.0, 0.0),
                                   (1.0, 1.0, 1.0), 0.0, 0xFFFFFFFF)
    # Mesh chunk
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    normals = [(0, 0, 1), (0, 0, 1), (0, 0, 1)]
    faces = [(3, [0, 1, 2], 0)]  # (num_indices, indices, material)
    mesh_data = make_mesh_chunk(vertices, faces, normals)

    return header + b'c' + mat_data + b'm' + mesh_data


def seed_scene_with_camera_light():
    """Q3D file with mesh + scene chunk (camera + light)."""
    header = make_header("quick3Do", "30", 1, 1, 0)

    mat_data = make_material_chunk("SceneMat", (0.1, 0.1, 0.1), (0.5, 0.5, 0.8),
                                   (1.0, 1.0, 1.0), 0.5, 0xFFFFFFFF)
    vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    normals = [(0, 0, 1)] * 4
    faces = [(4, [0, 1, 2, 3], 0)]  # quad
    mesh_data = make_mesh_chunk(vertices, faces, normals)
    scene_data = make_scene_chunk(camera_pos=(0, 0, 10))

    return header + b'c' + mat_data + b'm' + mesh_data + b's' + scene_data


def seed_multi_mesh_multi_mat():
    """Q3D with 2 meshes and 2 materials."""
    header = make_header("quick3Do", "30", 2, 2, 0)

    mat0 = make_material_chunk("red", (0.1, 0.0, 0.0), (1.0, 0.0, 0.0),
                               (1.0, 1.0, 1.0), 0.0, 0xFFFFFFFF)
    mat1 = make_material_chunk("blue", (0.0, 0.0, 0.1), (0.0, 0.0, 1.0),
                               (1.0, 1.0, 1.0), 0.0, 0xFFFFFFFF)

    # Mesh 0: triangle
    verts0 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    norms0 = [(0, 0, 1)] * 3
    faces0 = [(3, [0, 1, 2], 0)]
    mesh0 = make_mesh_chunk(verts0, faces0, norms0)

    # Mesh 1: another triangle
    verts1 = [(2, 0, 0), (3, 0, 0), (2, 1, 0)]
    norms1 = [(0, 0, 1)] * 3
    faces1 = [(3, [0, 1, 2], 1)]
    mesh1 = make_mesh_chunk(verts1, faces1, norms1)

    return header + b'c' + mat0 + mat1 + b'm' + mesh0 + mesh1


def seed_with_texture():
    """Q3D with embedded texture and UV mapping."""
    header = make_header("quick3Do", "30", 1, 1, 1)

    mat_data = make_material_chunk("texMat", (0.2, 0.2, 0.2), (0.8, 0.8, 0.8),
                                   (1.0, 1.0, 1.0), 0.0, 0)

    # Small 2x2 texture
    pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    tex_data = make_texture_chunk("diffuse", 2, 2, pixels)

    vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    normals = [(0, 0, 1)] * 4
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    faces = [(4, [0, 1, 2, 3], 0)]
    uv_indices = [[0, 1, 2, 3]]
    mesh_data = make_mesh_chunk(vertices, faces, normals, uvs, uv_indices,
                                has_textures=True)

    return header + b'c' + mat_data + b't' + tex_data + b'm' + mesh_data


def seed_q3s_format():
    """Q3S (Quick3D Scene) format variant."""
    header = make_header("quick3Ds", "30", 1, 1, 0)

    mat_data = make_material_chunk("q3sMat", (0.2, 0.2, 0.2), (0.5, 0.8, 0.5),
                                   (1.0, 1.0, 1.0), 0.0, 0xFFFFFFFF)
    vertices = [(0, 0, 0), (1, 0, 0), (0.5, 1, 0)]
    normals = [(0, 0, 1)] * 3
    faces = [(3, [0, 1, 2], 0)]
    mesh_data = make_mesh_chunk(vertices, faces, normals)
    scene_data = make_scene_chunk()

    return header + b'c' + mat_data + b'm' + mesh_data + b's' + scene_data


def seed_version_31():
    """Q3D version 3.1 - has extra per-face byte in mesh chunk."""
    header = make_header("quick3Do", "31", 1, 1, 0)

    mat_data = make_material_chunk("v31mat", (0.2, 0.2, 0.2), (0.6, 0.3, 0.1),
                                   (1.0, 1.0, 1.0), 0.0, 0xFFFFFFFF)
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    normals = [(0, 0, 1)] * 3
    faces = [(3, [0, 1, 2], 0)]
    mesh_data = make_mesh_chunk(vertices, faces, normals,
                                version_major='3', version_minor='1')

    return header + b'c' + mat_data + b'm' + mesh_data


def seed_no_normals():
    """Q3D mesh where normals count is less than vertex count, triggering face normal calculation."""
    header = make_header("quick3Do", "30", 1, 1, 0)

    mat_data = make_material_chunk("noNrm", (0.2, 0.2, 0.2), (0.7, 0.7, 0.0),
                                   (1.0, 1.0, 1.0), 0.0, 0xFFFFFFFF)
    vertices = [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (0, 0, 1)]
    # Only 1 normal for 4 vertices -> triggers face normal path
    normals = [(0, 0, 1)]
    faces = [(3, [0, 1, 2], 0), (3, [0, 2, 3], 0)]
    mesh_data = make_mesh_chunk(vertices, faces, normals)

    return header + b'c' + mat_data + b'm' + mesh_data


def seed_default_material():
    """Q3D with no material chunk, triggering default material generation."""
    header = make_header("quick3Do", "30", 1, 0, 0)

    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    normals = [(0, 0, 1)] * 3
    faces = [(3, [0, 1, 2], 0)]
    mesh_data = make_mesh_chunk(vertices, faces, normals)

    return header + b'm' + mesh_data


def seed_full_scene_textured():
    """Complete Q3D with texture, materials, mesh, and scene chunk."""
    header = make_header("quick3Do", "30", 1, 1, 1)

    mat_data = make_material_chunk("fullMat", (0.1, 0.1, 0.1), (0.9, 0.9, 0.9),
                                   (1.0, 1.0, 1.0), 0.0, 0)

    pixels = [(128, 128, 128), (200, 200, 200), (64, 64, 64), (255, 255, 255)]
    tex_data = make_texture_chunk("main_tex", 2, 2, pixels)

    vertices = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
    normals = [(0, 0, 1)] * 4
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    faces = [(3, [0, 1, 2], 0), (3, [0, 2, 3], 0)]
    uv_indices = [[0, 1, 2], [0, 2, 3]]
    mesh_data = make_mesh_chunk(vertices, faces, normals, uvs, uv_indices,
                                has_textures=True)

    scene_data = make_scene_chunk(camera_pos=(2, 3, 5),
                                  fg_color=(0.3, 0.3, 0.3),
                                  light_color=(0.9, 0.9, 0.8))

    return header + b'c' + mat_data + b't' + tex_data + b'm' + mesh_data + b's' + scene_data


def seed_uv_shared_indices():
    """Q3D with UVs where prevUVIdx stays the same (shared UV index path)."""
    header = make_header("quick3Do", "30", 1, 1, 1)

    mat_data = make_material_chunk("shUV", (0.2, 0.2, 0.2), (0.5, 0.5, 0.5),
                                   (1.0, 1.0, 1.0), 0.0, 0)

    pixels = [(255, 0, 0)] * 4
    tex_data = make_texture_chunk("t", 2, 2, pixels)

    # Enough UVs to cover verts.size()
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    normals = [(0, 0, 1)] * 3
    uvs = [(0.5, 0.5), (0.5, 0.5), (0.5, 0.5)]
    faces = [(3, [0, 1, 2], 0)]
    # All UV indices the same -> prevUVIdx stays constant, triggering the shared path
    uv_indices = [[0, 0, 0]]
    mesh_data = make_mesh_chunk(vertices, faces, normals, uvs, uv_indices,
                                has_textures=True)

    return header + b'c' + mat_data + b't' + tex_data + b'm' + mesh_data


def main():
    seeds = {
        "seed_minimal_triangle.q3o": seed_minimal_triangle(),
        "seed_scene_camera_light.q3o": seed_scene_with_camera_light(),
        "seed_multi_mesh_mat.q3o": seed_multi_mesh_multi_mat(),
        "seed_with_texture.q3o": seed_with_texture(),
        "seed_q3s_scene.q3s": seed_q3s_format(),
        "seed_version_31.q3o": seed_version_31(),
        "seed_no_normals.q3o": seed_no_normals(),
        "seed_default_material.q3o": seed_default_material(),
        "seed_full_scene_textured.q3o": seed_full_scene_textured(),
        "seed_uv_shared_indices.q3o": seed_uv_shared_indices(),
    }

    for name, data in seeds.items():
        path = os.path.join(OUTPUT_DIR, name)
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  {name}: {len(data)} bytes")

    print(f"\nGenerated {len(seeds)} Q3D seed files in {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
