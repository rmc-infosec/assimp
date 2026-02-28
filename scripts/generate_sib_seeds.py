#!/usr/bin/env python3
"""Generate binary SIB (Silo) seed files for fuzzing.

SIB format (reverse-engineered, undocumented):
  - Chunk-based structure (IFF-like)
  - Each chunk: Tag (4 bytes big-endian) + Size (4 bytes little-endian)
  - StreamReaderLE with SetReadLimit for nested chunks
  - Top-level chunks in ReadScene: HEAD, SHAP, GRPS, TEXP, INST, MATR, LGHT
  - SHAP sub-chunks: VRTS, FACS, FTVS, SNAM, FAMA, AXIS, EDGS, ECRS,
    MIRP, IMRP, DINF, PINF, VMIR, FMIR, TXSM, FAHS
  - MATR: diffuse(16) + ambient(16) + specular(16) + emissive(16) +
    shininess(4) + nameLen(4) + name(UTF16) + texLen(4) + tex(UTF16)
  - LGHT sub-chunks: LNFO, SNAM
  - INST sub-chunks: DINF, PINF, AXIS, INSI, SMTX, SNAM
  - HEAD: version uint32 (1 or 2)
  - VRTS: float32 xyz triples (chunk.Size / 12 vertices)
  - FACS: repeated [numPoints(4), pointIndices(4*n)]
  - FTVS: repeated [faceIdx(4), numPoints(4), uvPairs(8*n)]
  - FAMA: RLE material assignments [face(4), mtl(4)]
  - AXIS: 12 floats for 4x4 matrix (translation + 3 axes)
  - EDGS: pairs of vertex indices [posA(4), posB(4)]
  - ECRS: edge indices to mark as creased
  - Strings are UTF-16LE (2 bytes per char)
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test", "models", "SIB", "fuzz_seeds")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def u32(v):
    return struct.pack('<I', v)


def u32be(v):
    return struct.pack('>I', v)


def f32(v):
    return struct.pack('<f', v)


def u16(v):
    return struct.pack('<H', v)


def tag(a, b, c, d):
    """Create a 4-byte tag in big-endian order (matching TAG macro)."""
    return struct.pack('>I', (ord(a) << 24) | (ord(b) << 16) | (ord(c) << 8) | ord(d))


def make_chunk(tag_bytes, data):
    """Create a SIB chunk: tag(4 BE) + size(4 LE) + data."""
    # Tag is read as GetU4 (LE) then Swap4 -> effectively big-endian
    # But StreamReaderLE reads 4 bytes as LE, then ByteSwap::Swap4 makes it BE
    # So we store tag as big-endian bytes
    return tag_bytes + u32(len(data)) + data


def make_utf16_string(s):
    """Encode string as UTF-16LE."""
    return s.encode('utf-16-le')


def make_color(r, g, b):
    """Color is 4 floats (r,g,b, unused)."""
    return f32(r) + f32(g) + f32(b) + f32(1.0)


def make_head(version=1):
    """HEAD chunk with version."""
    return make_chunk(tag('H', 'E', 'A', 'D'), u32(version))


def make_vertices(verts):
    """VRTS chunk: list of (x,y,z) tuples."""
    data = b''
    for v in verts:
        data += f32(v[0]) + f32(v[1]) + f32(v[2])
    return make_chunk(tag('V', 'R', 'T', 'S'), data)


def make_faces(faces):
    """FACS chunk: list of lists of vertex indices.

    Each face: numPoints(4), indices(4*n)
    """
    data = b''
    for face in faces:
        data += u32(len(face))
        for idx in face:
            data += u32(idx)
    return make_chunk(tag('F', 'A', 'C', 'S'), data)


def make_uvs(face_uvs):
    """FTVS chunk: UV data per face.

    face_uvs: list of (face_idx, [(u, v), ...])
    """
    data = b''
    for face_idx, uvs in face_uvs:
        data += u32(face_idx)
        data += u32(len(uvs))
        for uv in uvs:
            data += f32(uv[0]) + f32(uv[1])
    return make_chunk(tag('F', 'T', 'V', 'S'), data)


def make_name(name):
    """SNAM chunk: UTF-16LE name string."""
    data = make_utf16_string(name)
    return make_chunk(tag('S', 'N', 'A', 'M'), data)


def make_material_assignments(assignments):
    """FAMA chunk: RLE material assignments.

    assignments: list of (face_index, material_index)
    The loader adds 1 to each material internally.
    """
    data = b''
    for face, mtl in assignments:
        data += u32(face) + u32(mtl)
    return make_chunk(tag('F', 'A', 'M', 'A'), data)


def make_axis(tx=0, ty=0, tz=0):
    """AXIS chunk: translation + 3 axis vectors (identity)."""
    data = b''
    # Translation
    data += f32(tx) + f32(ty) + f32(tz)
    # X axis
    data += f32(1.0) + f32(0.0) + f32(0.0)
    # Y axis
    data += f32(0.0) + f32(1.0) + f32(0.0)
    # Z axis
    data += f32(0.0) + f32(0.0) + f32(1.0)
    return make_chunk(tag('A', 'X', 'I', 'S'), data)


def make_edges(edges):
    """EDGS chunk: list of (posA, posB) pairs."""
    data = b''
    for e in edges:
        data += u32(e[0]) + u32(e[1])
    return make_chunk(tag('E', 'D', 'G', 'S'), data)


def make_creases(crease_indices):
    """ECRS chunk: list of edge indices to mark as creased."""
    data = b''
    for idx in crease_indices:
        data += u32(idx)
    return make_chunk(tag('E', 'C', 'R', 'S'), data)


def make_shape(name, verts, faces, face_uvs=None, mat_assignments=None,
               edges=None, creases=None, tx=0, ty=0, tz=0):
    """Build a SHAP chunk containing mesh data."""
    data = b''
    data += make_vertices(verts)
    data += make_faces(faces)
    if face_uvs:
        data += make_uvs(face_uvs)
    data += make_name(name)
    if mat_assignments:
        data += make_material_assignments(mat_assignments)
    data += make_axis(tx, ty, tz)
    if edges:
        data += make_edges(edges)
    if creases is not None and edges:
        data += make_creases(creases)
    return make_chunk(tag('S', 'H', 'A', 'P'), data)


def make_material(name, diffuse=(0.8, 0.8, 0.8), ambient=(0.2, 0.2, 0.2),
                  specular=(1.0, 1.0, 1.0), emissive=(0.0, 0.0, 0.0),
                  shininess=32, texture=""):
    """Build a MATR chunk."""
    data = b''
    data += make_color(*diffuse)
    data += make_color(*ambient)
    data += make_color(*specular)
    data += make_color(*emissive)
    data += u32(int(shininess))

    # Name: length in bytes + UTF-16LE string
    name_utf16 = make_utf16_string(name)
    data += u32(len(name_utf16))
    data += name_utf16

    # Texture: length in bytes + UTF-16LE string
    tex_utf16 = make_utf16_string(texture)
    data += u32(len(tex_utf16))
    data += tex_utf16

    return make_chunk(tag('M', 'A', 'T', 'R'), data)


def make_light_info(light_type=0, pos=(0, 5, 0), direction=(0, -1, 0),
                    diffuse=(1, 1, 1), ambient=(0.2, 0.2, 0.2),
                    specular=(1, 1, 1), spot_exp=0.0, spot_cutoff=180.0,
                    atten_const=1.0, atten_linear=0.0, atten_quad=0.0):
    """Build LNFO sub-chunk data."""
    data = b''
    data += u32(light_type)
    data += f32(pos[0]) + f32(pos[1]) + f32(pos[2])
    data += f32(direction[0]) + f32(direction[1]) + f32(direction[2])
    data += make_color(*diffuse)
    data += make_color(*ambient)
    data += make_color(*specular)
    data += f32(spot_exp)
    data += f32(spot_cutoff)
    data += f32(atten_const)
    data += f32(atten_linear)
    data += f32(atten_quad)
    return make_chunk(tag('L', 'N', 'F', 'O'), data)


def make_light(name, light_type=0, **kwargs):
    """Build a LGHT chunk."""
    data = b''
    data += make_light_info(light_type=light_type, **kwargs)
    data += make_name(name)
    return make_chunk(tag('L', 'G', 'H', 'T'), data)


def make_instance(name, shape_index=0, tx=0, ty=0, tz=0, scale_matrix=None):
    """Build an INST chunk."""
    data = b''
    data += make_axis(tx, ty, tz)
    # INSI: shape index
    data += make_chunk(tag('I', 'N', 'S', 'I'), u32(shape_index))
    data += make_name(name)
    if scale_matrix:
        # SMTX: 4x4 matrix as 16 floats
        sm_data = b''
        for v in scale_matrix:
            sm_data += f32(v)
        data += make_chunk(tag('S', 'M', 'T', 'X'), sm_data)
    return make_chunk(tag('I', 'N', 'S', 'T'), data)


def seed_minimal_triangle():
    """Minimal SIB with one material and one triangle."""
    data = b''
    data += make_head(version=1)
    data += make_material("default_mat")
    data += make_shape("Triangle",
                       verts=[(0, 0, 0), (1, 0, 0), (0, 1, 0)],
                       faces=[[0, 1, 2]])
    return data


def seed_quad_with_uvs():
    """SIB with a quad, UV mapping, and material assignment."""
    data = b''
    data += make_head(version=1)
    data += make_material("quad_mat", diffuse=(0.8, 0.2, 0.2))
    data += make_shape("Quad",
                       verts=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
                       faces=[[0, 1, 2, 3]],
                       face_uvs=[(0, [(0, 0), (1, 0), (1, 1), (0, 1)])],
                       mat_assignments=[(0, 0)])
    return data


def seed_multi_face():
    """SIB with multiple faces and normals calculation paths."""
    data = b''
    data += make_head(version=1)
    data += make_material("mat0", diffuse=(1, 0, 0))
    data += make_material("mat1", diffuse=(0, 1, 0))
    data += make_shape("MultiFace",
                       verts=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0.5, 0.5, 1)],
                       faces=[[0, 1, 2, 3],   # quad on bottom
                              [0, 1, 4],       # triangle side
                              [1, 2, 4],       # triangle side
                              [2, 3, 4],       # triangle side
                              [3, 0, 4]],      # triangle side (pyramid)
                       mat_assignments=[(0, 0), (1, 1), (3, 0)])
    return data


def seed_with_edges_creases():
    """SIB with edge data and creased edges for normal calculation."""
    data = b''
    data += make_head(version=1)
    data += make_material("crease_mat")
    data += make_shape("Creased",
                       verts=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                              (0, 0, 1), (1, 0, 1)],
                       faces=[[0, 1, 2, 3],    # face A
                              [0, 1, 5, 4]],   # face B shares edge 0-1
                       edges=[(0, 1), (1, 2), (2, 3), (3, 0), (0, 4), (1, 5), (4, 5)],
                       creases=[0])   # crease edge 0 (the shared edge)
    return data


def seed_with_lights():
    """SIB with different light types."""
    data = b''
    data += make_head(version=1)
    data += make_material("lit_mat")
    data += make_shape("LitMesh",
                       verts=[(0, 0, 0), (1, 0, 0), (0, 1, 0)],
                       faces=[[0, 1, 2]])
    # Point light
    data += make_light("PointLight", light_type=0,
                       pos=(0, 5, 0), diffuse=(1, 1, 1))
    # Spot light
    data += make_light("SpotLight", light_type=1,
                       pos=(3, 3, 3), direction=(0, -1, 0),
                       spot_exp=10.0, spot_cutoff=45.0)
    # Directional light
    data += make_light("DirLight", light_type=2,
                       direction=(0, -1, -1), diffuse=(0.8, 0.8, 0.5))
    return data


def seed_with_instance():
    """SIB with an instance referencing a shape."""
    data = b''
    data += make_head(version=1)
    data += make_material("inst_mat")
    data += make_shape("OrigShape",
                       verts=[(0, 0, 0), (1, 0, 0), (0, 1, 0)],
                       faces=[[0, 1, 2]])
    # Instance referencing shape 0
    data += make_instance("Instance1", shape_index=0, tx=3, ty=0, tz=0)
    return data


def seed_with_instance_scale():
    """SIB with instance that has a scale matrix (SMTX)."""
    data = b''
    data += make_head(version=1)
    data += make_material("scale_mat")
    data += make_shape("BaseShape",
                       verts=[(0, 0, 0), (1, 0, 0), (0, 1, 0)],
                       faces=[[0, 1, 2]])
    # Instance with scale 2x
    scale = [2, 0, 0, 0,
             0, 2, 0, 0,
             0, 0, 2, 0,
             0, 0, 0, 1]
    data += make_instance("Scaled", shape_index=0, tx=5, ty=0, tz=0,
                          scale_matrix=scale)
    return data


def seed_version_2():
    """SIB with version 2 header."""
    data = b''
    data += make_head(version=2)
    data += make_material("v2_mat")
    data += make_shape("V2Mesh",
                       verts=[(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)],
                       faces=[[0, 1, 2], [1, 3, 2]])
    return data


def seed_textured_material():
    """SIB with material that has a texture path."""
    data = b''
    data += make_head(version=1)
    data += make_material("texmat", diffuse=(0.9, 0.9, 0.9),
                          texture="texture.png")
    data += make_shape("TexMesh",
                       verts=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
                       faces=[[0, 1, 2, 3]],
                       face_uvs=[(0, [(0, 0), (1, 0), (1, 1), (0, 1)])])
    return data


def seed_multi_material_mesh():
    """SIB with multiple materials assigned to different faces."""
    data = b''
    data += make_head(version=1)
    data += make_material("red", diffuse=(1, 0, 0))
    data += make_material("green", diffuse=(0, 1, 0))
    data += make_material("blue", diffuse=(0, 0, 1))
    data += make_shape("MultiMat",
                       verts=[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
                              (2, 0, 0), (2, 1, 0)],
                       faces=[[0, 1, 2], [0, 2, 3], [1, 4, 5, 2]],
                       mat_assignments=[(0, 0), (1, 1), (2, 2)])
    return data


def seed_complex_scene():
    """SIB with shapes, instances, lights, and multiple materials."""
    data = b''
    data += make_head(version=1)
    data += make_material("floor_mat", diffuse=(0.5, 0.5, 0.5))
    data += make_material("wall_mat", diffuse=(0.8, 0.6, 0.4), texture="wall.jpg")

    # Floor shape
    data += make_shape("Floor",
                       verts=[(-5, 0, -5), (5, 0, -5), (5, 0, 5), (-5, 0, 5)],
                       faces=[[0, 1, 2, 3]],
                       face_uvs=[(0, [(0, 0), (1, 0), (1, 1), (0, 1)])],
                       mat_assignments=[(0, 0)])

    # Wall shape
    data += make_shape("Wall",
                       verts=[(0, 0, 0), (2, 0, 0), (2, 3, 0), (0, 3, 0)],
                       faces=[[0, 1, 2, 3]],
                       mat_assignments=[(0, 1)],
                       edges=[(0, 1), (1, 2), (2, 3), (3, 0)],
                       creases=[2])

    # Instance of wall
    data += make_instance("WallCopy", shape_index=1, tx=4, ty=0, tz=0)

    # Lights
    data += make_light("SunLight", light_type=2,
                       direction=(0.5, -1, -0.3), diffuse=(1, 0.95, 0.8))
    data += make_light("FillLight", light_type=0,
                       pos=(-3, 4, 2), diffuse=(0.3, 0.3, 0.5))

    return data


def main():
    seeds = {
        "seed_minimal_triangle.sib": seed_minimal_triangle(),
        "seed_quad_uvs.sib": seed_quad_with_uvs(),
        "seed_multi_face.sib": seed_multi_face(),
        "seed_edges_creases.sib": seed_with_edges_creases(),
        "seed_lights.sib": seed_with_lights(),
        "seed_instance.sib": seed_with_instance(),
        "seed_instance_scale.sib": seed_with_instance_scale(),
        "seed_version_2.sib": seed_version_2(),
        "seed_textured_mat.sib": seed_textured_material(),
        "seed_multi_material.sib": seed_multi_material_mesh(),
        "seed_complex_scene.sib": seed_complex_scene(),
    }

    for name, data in seeds.items():
        path = os.path.join(OUTPUT_DIR, name)
        with open(path, 'wb') as f:
            f.write(data)
        print(f"  {name}: {len(data)} bytes")

    print(f"\nGenerated {len(seeds)} SIB seed files in {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
