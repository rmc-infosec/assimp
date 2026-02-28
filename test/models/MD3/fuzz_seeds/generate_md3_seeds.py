#!/usr/bin/env python3
"""Generate valid MD3 (Quake 3 model) binary seed files for fuzzing."""

import struct
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# MD3 constants
IDP3_MAGIC = b"IDP3"
MD3_VERSION = 15

HEADER_SIZE = 108        # 4+4+64+4+4+4+4+4+4+4+4+4
FRAME_SIZE = 56          # 3*4+3*4+3*4+4+16
TAG_SIZE = 112           # 64+3*4+9*4
SURFACE_HEADER_SIZE = 108  # 4+64+4+4+4+4+4+4+4+4+4+4
SHADER_SIZE = 68         # 64+4
TRIANGLE_SIZE = 12       # 3*4
TEXCOORD_SIZE = 8        # 2*4
VERTEX_SIZE = 8          # 3*2+2*1


def pad_string(s, length):
    """Pad string to fixed length with null bytes."""
    b = s.encode("ascii") if isinstance(s, str) else s
    return b[:length].ljust(length, b"\x00")


def make_header(name, num_frames, num_tags, num_surfaces, num_skins,
                ofs_frames, ofs_tags, ofs_surfaces, ofs_eof):
    """Build an MD3 file header (108 bytes)."""
    return struct.pack(
        "<4si64siiiiiiiii",
        IDP3_MAGIC,              # magic (4)
        MD3_VERSION,             # version (4)
        pad_string(name, 64),    # name (64)
        0,                       # flags (4)
        num_frames,              # (4)
        num_tags,                # (4)
        num_surfaces,            # (4)
        num_skins,               # (4) unused
        ofs_frames,              # (4)
        ofs_tags,                # (4)
        ofs_surfaces,            # (4)
        ofs_eof,                 # (4)
    )


def make_frame(name="frame0", min_v=(-1, -1, -1), max_v=(1, 1, 1),
               origin=(0, 0, 0), radius=1.732):
    """Build a Frame struct (56 bytes)."""
    return struct.pack(
        "<3f3f3ff16s",
        *[float(x) for x in min_v],
        *[float(x) for x in max_v],
        *[float(x) for x in origin],
        float(radius),
        pad_string(name, 16),
    )


def make_tag(name="tag", origin=(0, 0, 0),
             axis=(1, 0, 0, 0, 1, 0, 0, 0, 1)):
    """Build a Tag struct (112 bytes)."""
    return struct.pack(
        "<64s3f9f",
        pad_string(name, 64),
        *[float(x) for x in origin],
        *[float(x) for x in axis],
    )


def make_surface_header(name, num_frames, num_shaders, num_verts, num_tris,
                        ofs_triangles, ofs_shaders, ofs_st, ofs_xyznormal, ofs_end):
    """Build a Surface header (108 bytes)."""
    return struct.pack(
        "<4s64siiiiiiiiii",
        IDP3_MAGIC,
        pad_string(name, 64),
        0,                  # flags
        num_frames,
        num_shaders,
        num_verts,
        num_tris,
        ofs_triangles,
        ofs_shaders,
        ofs_st,
        ofs_xyznormal,
        ofs_end,
    )


def make_shader(name="textures/default", index=0):
    """Build a Shader struct (68 bytes)."""
    return struct.pack("<64si", pad_string(name, 64), index)


def make_triangle(v0, v1, v2):
    """Build a Triangle struct (12 bytes)."""
    return struct.pack("<iii", v0, v1, v2)


def make_texcoord(s, t):
    """Build a TexCoord struct (8 bytes)."""
    return struct.pack("<ff", float(s), float(t))


def encode_normal(nx, ny, nz):
    """Encode a normal vector into 2 bytes (lat, lng) per MD3 spec."""
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length < 1e-6:
        return 0, 0
    nx, ny, nz = nx / length, ny / length, nz / length
    lat = math.acos(max(-1.0, min(1.0, nz)))
    lng = math.atan2(ny, nx)
    # Map to 0-255 range
    lat_byte = int(lat * 255.0 / (2.0 * math.pi)) & 0xFF
    lng_byte = int(lng * 255.0 / (2.0 * math.pi)) & 0xFF
    return lat_byte, lng_byte


def make_vertex(x, y, z, nx=0.0, ny=0.0, nz=1.0):
    """Build a Vertex/XYZNormal struct (8 bytes).
    x,y,z are in world units (will be scaled by 64).
    nx,ny,nz is the normal direction for encoding."""
    sx = max(-32768, min(32767, int(x * 64.0)))
    sy = max(-32768, min(32767, int(y * 64.0)))
    sz = max(-32768, min(32767, int(z * 64.0)))
    lat, lng = encode_normal(nx, ny, nz)
    return struct.pack("<3hBB", sx, sy, sz, lat, lng)


def build_surface(name, num_frames, shaders, triangles, texcoords, verts_per_frame):
    """
    Build a complete surface blob (header + data).

    shaders: list of (name, index)
    triangles: list of (v0, v1, v2)
    texcoords: list of (s, t) -- one per vertex (shared across frames)
    verts_per_frame: list of frames, each frame is list of (x, y, z) world coords
    """
    num_shaders = len(shaders)
    num_tris = len(triangles)
    num_verts = len(texcoords)

    ofs_triangles = SURFACE_HEADER_SIZE
    ofs_shaders = ofs_triangles + num_tris * TRIANGLE_SIZE
    ofs_st = ofs_shaders + num_shaders * SHADER_SIZE
    ofs_xyznormal = ofs_st + num_verts * TEXCOORD_SIZE
    ofs_end = ofs_xyznormal + num_frames * num_verts * VERTEX_SIZE

    data = bytearray()
    data += make_surface_header(name, num_frames, num_shaders, num_verts, num_tris,
                                ofs_triangles, ofs_shaders, ofs_st, ofs_xyznormal, ofs_end)

    for tri in triangles:
        data += make_triangle(*tri)

    for sh_name, sh_idx in shaders:
        data += make_shader(sh_name, sh_idx)

    for s, t in texcoords:
        data += make_texcoord(s, t)

    for frame_verts in verts_per_frame:
        for vx, vy, vz in frame_verts:
            data += make_vertex(vx, vy, vz)

    assert len(data) == ofs_end, f"Surface size mismatch: {len(data)} != {ofs_end}"
    return data


def build_md3(name, num_frames, tags_per_frame, surface_blobs, frames_data):
    """
    Build a complete MD3 file.

    name: model name string
    num_frames: number of animation frames
    tags_per_frame: list of lists -- tags_per_frame[frame_idx] = [(name, origin, axis), ...]
    surface_blobs: list of bytes (pre-built surface data)
    frames_data: list of frame bytes
    """
    num_tags = len(tags_per_frame[0]) if tags_per_frame else 0

    all_frames = b''.join(frames_data)
    # Tags are stored as num_frames * num_tags, frame-major order
    all_tags = bytearray()
    for frame_tags in tags_per_frame:
        for tag_name, tag_origin, tag_axis in frame_tags:
            all_tags += make_tag(tag_name, tag_origin, tag_axis)
    all_surfaces = b''.join(surface_blobs)

    ofs_frames = HEADER_SIZE
    ofs_tags = ofs_frames + len(all_frames)
    ofs_surfaces = ofs_tags + len(all_tags)
    ofs_eof = ofs_surfaces + len(all_surfaces)

    header = make_header(name, num_frames, num_tags, len(surface_blobs), 0,
                         ofs_frames, ofs_tags, ofs_surfaces, ofs_eof)

    return header + all_frames + bytes(all_tags) + all_surfaces


def write_seed(filename, data):
    """Write binary data to a seed file."""
    path = os.path.join(SCRIPT_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    print(f"  {filename}: {len(data)} bytes")


# ============================================================
# Seed 1: seed_basic.md3
#   1 frame, 0 tags, 1 surface (3 verts, 1 triangle)
# ============================================================
def generate_seed_basic():
    frames = [make_frame("frame0")]

    surf = build_surface(
        name="basic_surface",
        num_frames=1,
        shaders=[("textures/basic", 0)],
        triangles=[(0, 1, 2)],
        texcoords=[(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)],
        verts_per_frame=[
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 1.0, 0.0)],
        ],
    )

    data = build_md3("basic_model", 1, [], [surf], frames)
    write_seed("seed_basic.md3", data)


# ============================================================
# Seed 2: seed_multisurface.md3
#   1 frame, 0 tags, 3 surfaces with different vertex counts
# ============================================================
def generate_seed_multisurface():
    frames = [make_frame("frame0", (-2, -2, -2), (2, 2, 2), (0, 0, 0), 3.464)]

    # Surface 0: triangle (3 verts, 1 tri)
    surf0 = build_surface(
        name="triangle_surf",
        num_frames=1,
        shaders=[("textures/red", 0)],
        triangles=[(0, 1, 2)],
        texcoords=[(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)],
        verts_per_frame=[
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 1.0, 0.0)],
        ],
    )

    # Surface 1: quad (4 verts, 2 tris)
    surf1 = build_surface(
        name="quad_surf",
        num_frames=1,
        shaders=[("textures/green", 1)],
        triangles=[(0, 1, 2), (0, 2, 3)],
        texcoords=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        verts_per_frame=[
            [(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 1.0, 0.0), (-1.0, 1.0, 0.0)],
        ],
    )

    # Surface 2: pentagon (5 verts, 3 tris)
    surf2 = build_surface(
        name="penta_surf",
        num_frames=1,
        shaders=[("textures/blue", 2), ("textures/blue_alt", 3)],
        triangles=[(0, 1, 2), (0, 2, 3), (0, 3, 4)],
        texcoords=[
            (0.5, 0.0), (1.0, 0.4), (0.8, 1.0), (0.2, 1.0), (0.0, 0.4),
        ],
        verts_per_frame=[
            [
                (0.0, 1.0, 0.0),
                (0.95, 0.31, 0.0),
                (0.59, -0.81, 0.0),
                (-0.59, -0.81, 0.0),
                (-0.95, 0.31, 0.0),
            ],
        ],
    )

    data = build_md3("multisurface_model", 1, [], [surf0, surf1, surf2], frames)
    write_seed("seed_multisurface.md3", data)


# ============================================================
# Seed 3: seed_animated.md3
#   3 frames, 0 tags, 1 surface (4 verts, 2 tris) - vertex animation
# ============================================================
def generate_seed_animated():
    frames = [
        make_frame("stand0", (-1, -1, -1), (1, 1, 1), (0, 0, 0), 1.732),
        make_frame("stand1", (-1, -1, -0.5), (1, 1, 1.5), (0, 0, 0.25), 1.8),
        make_frame("stand2", (-1, -1, -1.5), (1, 1, 0.5), (0, 0, -0.25), 1.8),
    ]

    surf = build_surface(
        name="animated_surf",
        num_frames=3,
        shaders=[("textures/skin", 0)],
        triangles=[(0, 1, 2), (0, 2, 3)],
        texcoords=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        verts_per_frame=[
            # Frame 0: flat quad
            [(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 1.0, 0.0), (-1.0, 1.0, 0.0)],
            # Frame 1: bent up
            [(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 1.0, 0.5), (-1.0, 1.0, 0.5)],
            # Frame 2: bent down
            [(-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 1.0, -0.5), (-1.0, 1.0, -0.5)],
        ],
    )

    data = build_md3("animated_model", 3, [], [surf], frames)
    write_seed("seed_animated.md3", data)


# ============================================================
# Seed 4: seed_tags.md3
#   1 frame, 2 tags, 1 surface
# ============================================================
def generate_seed_tags():
    frames = [make_frame("frame0")]

    # Identity rotation axis
    identity_axis = (1, 0, 0, 0, 1, 0, 0, 0, 1)
    # 45-degree rotation around Z
    c45 = math.cos(math.pi / 4.0)
    s45 = math.sin(math.pi / 4.0)
    rot45z_axis = (c45, s45, 0, -s45, c45, 0, 0, 0, 1)

    tags_frame0 = [
        ("tag_head",   (0.0, 0.0, 2.0), identity_axis),
        ("tag_weapon", (1.0, 0.0, 1.0), rot45z_axis),
    ]

    surf = build_surface(
        name="body",
        num_frames=1,
        shaders=[("models/players/body", 0)],
        triangles=[(0, 1, 2)],
        texcoords=[(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)],
        verts_per_frame=[
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 0.0, 1.0)],
        ],
    )

    data = build_md3("tagged_model", 1, [tags_frame0], [surf], frames)
    write_seed("seed_tags.md3", data)


# ============================================================
# Seed 5: seed_complex.md3
#   2 frames, 2 tags, 2 surfaces, multiple triangles
# ============================================================
def generate_seed_complex():
    frames = [
        make_frame("idle0", (-3, -3, -3), (3, 3, 3), (0, 0, 0), 5.196),
        make_frame("idle1", (-3, -3, -2.5), (3, 3, 3.5), (0, 0, 0.25), 5.5),
    ]

    identity_axis = (1, 0, 0, 0, 1, 0, 0, 0, 1)

    tags_frame0 = [
        ("tag_head",   (0.0, 0.0, 2.0),  identity_axis),
        ("tag_weapon", (1.5, 0.0, 1.0),  identity_axis),
    ]
    tags_frame1 = [
        ("tag_head",   (0.0, 0.0, 2.2),  identity_axis),
        ("tag_weapon", (1.5, 0.2, 1.0),  identity_axis),
    ]

    # Surface 0: cube (8 verts, 12 triangles)
    cube_tris = [
        (0, 1, 5), (0, 5, 4),  # front
        (1, 2, 6), (1, 6, 5),  # right
        (2, 3, 7), (2, 7, 6),  # back
        (3, 0, 4), (3, 4, 7),  # left
        (4, 5, 6), (4, 6, 7),  # top
        (3, 2, 1), (3, 1, 0),  # bottom
    ]
    cube_tc = [
        (0.00, 0.0), (0.25, 0.0), (0.50, 0.0), (0.75, 0.0),
        (0.00, 1.0), (0.25, 1.0), (0.50, 1.0), (0.75, 1.0),
    ]
    cube_v0 = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1,  1), (1, -1,  1), (1, 1,  1), (-1, 1,  1),
    ]
    cube_v1 = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1.2), (1, -1, 1.2), (1, 1, 1.2), (-1, 1, 1.2),
    ]

    surf0 = build_surface(
        name="cube_surface",
        num_frames=2,
        shaders=[("textures/cube_skin", 0)],
        triangles=cube_tris,
        texcoords=cube_tc,
        verts_per_frame=[
            [(float(x), float(y), float(z)) for x, y, z in cube_v0],
            [(float(x), float(y), float(z)) for x, y, z in cube_v1],
        ],
    )

    # Surface 1: pyramid (5 verts, 6 triangles)
    pyr_tris = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),  # sides
        (1, 3, 2), (1, 4, 3),                          # base
    ]
    pyr_tc = [
        (0.5, 0.0),
        (0.0, 1.0), (1.0, 1.0),
        (1.0, 0.0), (0.0, 0.0),
    ]
    pyr_v0 = [
        (0.0, 0.0, 2.0),
        (-1.0, -1.0, 0.0), (1.0, -1.0, 0.0),
        (1.0, 1.0, 0.0), (-1.0, 1.0, 0.0),
    ]
    pyr_v1 = [
        (0.0, 0.0, 2.5),
        (-1.0, -1.0, 0.0), (1.0, -1.0, 0.0),
        (1.0, 1.0, 0.0), (-1.0, 1.0, 0.0),
    ]

    surf1 = build_surface(
        name="pyramid_surface",
        num_frames=2,
        shaders=[("textures/pyramid_skin", 0)],
        triangles=pyr_tris,
        texcoords=pyr_tc,
        verts_per_frame=[pyr_v0, pyr_v1],
    )

    data = build_md3("complex_model", 2, [tags_frame0, tags_frame1], [surf0, surf1], frames)
    write_seed("seed_complex.md3", data)


# ============================================================
# Legacy: seed_minimal.md3 (kept for backward compatibility)
#   Same as seed_basic but uses raw vertex scale values
# ============================================================
def generate_seed_minimal():
    """Minimal valid MD3: 1 surface, 1 frame, 3 vertices, 1 triangle."""
    frames = [make_frame("frame0", (0, 0, 0), (1, 1, 0), (0.5, 0.5, 0), 1.0)]

    surf = build_surface(
        name="surface0",
        num_frames=1,
        shaders=[("textures/default", 0)],
        triangles=[(0, 1, 2)],
        texcoords=[(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)],
        verts_per_frame=[
            [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        ],
    )

    data = build_md3("seed_minimal", 1, [], [surf], frames)
    write_seed("seed_minimal.md3", data)


# ============================================================
if __name__ == "__main__":
    print("Generating MD3 fuzz seeds...")
    generate_seed_basic()
    generate_seed_multisurface()
    generate_seed_animated()
    generate_seed_tags()
    generate_seed_complex()
    generate_seed_minimal()
    print("Done.")
