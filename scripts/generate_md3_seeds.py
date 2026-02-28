#!/usr/bin/env python3
"""Generate minimal valid MD3 binary seed files for fuzzing."""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test', 'models', 'MD3', 'fuzz_seeds')


def pad_string(s, length):
    """Pad a string to a fixed length with null bytes."""
    encoded = s.encode('ascii')[:length]
    return encoded + b'\x00' * (length - len(encoded))


def make_frame(name="frame", mins=(-1.0, -1.0, -1.0), maxs=(1.0, 1.0, 1.0),
               origin=(0.0, 0.0, 0.0), radius=1.732):
    """Create a 56-byte MD3 frame."""
    data = struct.pack('<3f', *mins)
    data += struct.pack('<3f', *maxs)
    data += struct.pack('<3f', *origin)
    data += struct.pack('<f', radius)
    data += pad_string(name, 16)
    assert len(data) == 56
    return data


def make_tag(name="tag", origin=(0.0, 0.0, 0.0),
             axis=(1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)):
    """Create a 112-byte MD3 tag."""
    data = pad_string(name, 64)
    data += struct.pack('<3f', *origin)
    data += struct.pack('<9f', *axis)
    assert len(data) == 112
    return data


def make_surface(name="surface", num_frames=1, num_shaders=1, num_verts=3,
                 num_triangles=1, shader_name="default"):
    """Create an MD3 surface with all sub-structures."""
    HEADER_SIZE = 108

    # Build sub-structures first to compute offsets
    # Triangles: 3x int32 per triangle
    triangles_data = b''
    for t in range(num_triangles):
        base = t * 3
        idx0 = base % num_verts
        idx1 = (base + 1) % num_verts
        idx2 = (base + 2) % num_verts
        triangles_data += struct.pack('<3i', idx0, idx1, idx2)

    # Shaders: 64-byte name + int32 index
    shaders_data = b''
    for s in range(num_shaders):
        sname = shader_name if s == 0 else f"shader{s}"
        shaders_data += pad_string(sname, 64)
        shaders_data += struct.pack('<i', s)

    # ST (texcoords): 2x float32 per vert
    st_data = b''
    for v in range(num_verts):
        u = float(v) / max(num_verts - 1, 1)
        st_data += struct.pack('<2f', u, 1.0 - u)

    # XYZNormal: 2x int16 (x,y) + int16 (z) + int16 (encoded normal) per vert per frame
    xyznormal_data = b''
    for f in range(num_frames):
        for v in range(num_verts):
            x = int(v * 10)
            y = int(f * 5)
            z = 0
            normal = 0  # encoded normal
            xyznormal_data += struct.pack('<4h', x, y, z, normal)

    # Compute offsets (all relative to surface start)
    ofs_triangles = HEADER_SIZE
    ofs_shaders = ofs_triangles + len(triangles_data)
    ofs_st = ofs_shaders + len(shaders_data)
    ofs_xyznormal = ofs_st + len(st_data)
    ofs_end = ofs_xyznormal + len(xyznormal_data)

    # Surface header (108 bytes)
    header = b'IDP3'
    header += pad_string(name, 64)
    header += struct.pack('<i', 0)  # flags
    header += struct.pack('<i', num_frames)
    header += struct.pack('<i', num_shaders)
    header += struct.pack('<i', num_verts)
    header += struct.pack('<i', num_triangles)
    header += struct.pack('<i', ofs_triangles)
    header += struct.pack('<i', ofs_shaders)
    header += struct.pack('<i', ofs_st)
    header += struct.pack('<i', ofs_xyznormal)
    header += struct.pack('<i', ofs_end)
    assert len(header) == HEADER_SIZE

    return header + triangles_data + shaders_data + st_data + xyznormal_data


def make_md3(name="model", num_frames=1, num_tags=0, surfaces=None, tags=None):
    """Create a complete MD3 file."""
    HEADER_SIZE = 108

    if surfaces is None:
        surfaces = [make_surface(num_frames=num_frames)]
    if tags is None:
        tags = [make_tag(f"tag{i}") for i in range(num_tags)]

    num_surfaces = len(surfaces)

    # Frames
    frames_data = b''
    for f in range(num_frames):
        frames_data += make_frame(f"frame{f}")

    # Tags (num_tags * num_frames tags total)
    tags_data = b''
    for f in range(num_frames):
        for tag in tags:
            tags_data += tag

    # Surfaces
    surfaces_data = b''
    for surf in surfaces:
        surfaces_data += surf

    # Compute offsets
    ofs_frames = HEADER_SIZE
    ofs_tags = ofs_frames + len(frames_data)
    ofs_surfaces = ofs_tags + len(tags_data)
    ofs_end = ofs_surfaces + len(surfaces_data)

    # MD3 header (108 bytes)
    header = b'IDP3'
    header += struct.pack('<i', 15)  # version
    header += pad_string(name, 64)
    header += struct.pack('<i', 0)  # flags
    header += struct.pack('<i', num_frames)
    header += struct.pack('<i', num_tags)
    header += struct.pack('<i', num_surfaces)
    header += struct.pack('<i', 0)  # numSkins
    header += struct.pack('<i', ofs_frames)
    header += struct.pack('<i', ofs_tags)
    header += struct.pack('<i', ofs_surfaces)
    header += struct.pack('<i', ofs_end)
    assert len(header) == HEADER_SIZE

    return header + frames_data + tags_data + surfaces_data


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Seed 1: Basic - 1 frame, 0 tags, 1 surface, 1 triangle, 3 verts
    data = make_md3(
        name="basic",
        num_frames=1,
        num_tags=0,
        surfaces=[make_surface(
            name="surface0",
            num_frames=1,
            num_shaders=1,
            num_verts=3,
            num_triangles=1,
            shader_name="default"
        )]
    )
    path = os.path.join(OUTPUT_DIR, 'seed_basic.md3')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Written {path} ({len(data)} bytes)")

    # Seed 2: Multi-surface - 1 frame, 1 tag, 2 surfaces
    data = make_md3(
        name="multi_surface",
        num_frames=1,
        num_tags=1,
        surfaces=[
            make_surface(
                name="body",
                num_frames=1,
                num_shaders=1,
                num_verts=4,
                num_triangles=2,
                shader_name="body_shader"
            ),
            make_surface(
                name="head",
                num_frames=1,
                num_shaders=1,
                num_verts=3,
                num_triangles=1,
                shader_name="head_shader"
            ),
        ],
        tags=[make_tag("tag_head", origin=(0.0, 0.0, 5.0))]
    )
    path = os.path.join(OUTPUT_DIR, 'seed_multi_surface.md3')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Written {path} ({len(data)} bytes)")

    # Seed 3: Multi-frame (animation) - 3 frames, 0 tags, 1 surface
    data = make_md3(
        name="animated",
        num_frames=3,
        num_tags=0,
        surfaces=[make_surface(
            name="mesh",
            num_frames=3,
            num_shaders=1,
            num_verts=6,
            num_triangles=4,
            shader_name="anim_shader"
        )]
    )
    path = os.path.join(OUTPUT_DIR, 'seed_multi_frame.md3')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"Written {path} ({len(data)} bytes)")


if __name__ == '__main__':
    main()
