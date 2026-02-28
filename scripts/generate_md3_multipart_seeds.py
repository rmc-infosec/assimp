#!/usr/bin/env python3
"""
Generate MD3 multipart player model seed files for fuzzing.

Creates lower.md3, upper.md3, and head.md3 in the correct Q3 player model
structure. The multipart code in MD3Loader::ReadMultipartFile() is triggered
when:
  1. AI_CONFIG_IMPORT_MD3_HANDLE_MULTIPART is set to 1 (default)
  2. The loaded filename (lowercased, before last '_' or '.') equals
     "lower", "upper", or "head"
  3. All three files (lower.md3, upper.md3, head.md3) exist in the same dir

The attachment hierarchy is:
  lower.md3 (must contain tag_torso) -> upper.md3 (must contain tag_head) -> head.md3

Also generates suffixed variants (lower_d.md3, upper_d.md3, head_d.md3) to
exercise the suffix-parsing path in ReadMultipartFile.
"""

import struct
import math
import os

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "test", "models", "MD3", "fuzz_seeds", "multipart"
)

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
VERTEX_SIZE = 8          # 3*2+2*1 (3 int16 + 1 uint16 packed as 2 bytes)


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


def write_file(filepath, data):
    """Write binary data to a file."""
    with open(filepath, "wb") as f:
        f.write(data)
    print(f"  {os.path.basename(filepath)}: {len(data)} bytes")


# ============================================================
# lower.md3 - Lower body with tag_torso
#   The tag_torso defines where the upper body attaches.
#   2 frames for animation, 1 surface (legs mesh), 1 tag (tag_torso)
# ============================================================
def generate_lower(output_dir, suffix=""):
    """Generate lower body MD3 with tag_torso."""
    num_frames = 2

    frames = [
        make_frame("idle0", (-2, -2, 0), (2, 2, 3), (0, 0, 1.5), 3.0),
        make_frame("idle1", (-2, -2, 0), (2, 2, 3.2), (0, 0, 1.6), 3.1),
    ]

    identity_axis = (1, 0, 0, 0, 1, 0, 0, 0, 1)

    # tag_torso: attachment point at waist height, per frame
    tags_frame0 = [
        ("tag_torso", (0.0, 0.0, 3.0), identity_axis),
    ]
    tags_frame1 = [
        ("tag_torso", (0.0, 0.0, 3.1), identity_axis),
    ]

    # Legs mesh: a simple box-like shape (8 verts, 12 tris)
    leg_tris = [
        (0, 1, 2), (0, 2, 3),  # front
        (4, 5, 6), (4, 6, 7),  # back
        (0, 4, 7), (0, 7, 3),  # left
        (1, 5, 6), (1, 6, 2),  # right
        (3, 2, 6), (3, 6, 7),  # top
        (0, 1, 5), (0, 5, 4),  # bottom
    ]
    leg_tc = [
        (0.0, 0.0), (0.25, 0.0), (0.25, 0.5), (0.0, 0.5),
        (0.5, 0.0), (0.75, 0.0), (0.75, 0.5), (0.5, 0.5),
    ]
    # Frame 0 verts: box from (-1,-1,0) to (1,1,3)
    leg_v0 = [
        (-1, -1, 0), (1, -1, 0), (1, -1, 3), (-1, -1, 3),
        (-1,  1, 0), (1,  1, 0), (1,  1, 3), (-1,  1, 3),
    ]
    # Frame 1 verts: slight animation - legs spread
    leg_v1 = [
        (-1.1, -1.1, 0), (1.1, -1.1, 0), (1.0, -1.0, 3.1), (-1.0, -1.0, 3.1),
        (-1.1,  1.1, 0), (1.1,  1.1, 0), (1.0,  1.0, 3.1), (-1.0,  1.0, 3.1),
    ]

    surf = build_surface(
        name="l_legs",
        num_frames=num_frames,
        shaders=[("models/players/sarge/lower", 0)],
        triangles=leg_tris,
        texcoords=leg_tc,
        verts_per_frame=[
            [(float(x), float(y), float(z)) for x, y, z in leg_v0],
            [(float(x), float(y), float(z)) for x, y, z in leg_v1],
        ],
    )

    data = build_md3("models/players/sarge/lower", num_frames,
                     [tags_frame0, tags_frame1], [surf], frames)
    fname = f"lower{suffix}.md3"
    write_file(os.path.join(output_dir, fname), data)
    return data


# ============================================================
# upper.md3 - Upper body with tag_head and tag_torso
#   tag_head defines where the head attaches.
#   tag_torso is also present (so RemoveSingleNodeFromList exercises it).
#   2 frames for animation, 1 surface (torso mesh), 2 tags
# ============================================================
def generate_upper(output_dir, suffix=""):
    """Generate upper body MD3 with tag_head (and tag_torso for removal)."""
    num_frames = 2

    frames = [
        make_frame("idle0", (-2, -2, 3), (2, 2, 6), (0, 0, 4.5), 3.0),
        make_frame("idle1", (-2, -2, 3), (2, 2, 6.2), (0, 0, 4.6), 3.1),
    ]

    identity_axis = (1, 0, 0, 0, 1, 0, 0, 0, 1)

    # tag_head: attachment point at top of torso
    # tag_torso: present for RemoveSingleNodeFromList to exercise
    tags_frame0 = [
        ("tag_head",  (0.0, 0.0, 6.0), identity_axis),
        ("tag_torso", (0.0, 0.0, 3.0), identity_axis),
    ]
    tags_frame1 = [
        ("tag_head",  (0.0, 0.0, 6.1), identity_axis),
        ("tag_torso", (0.0, 0.0, 3.0), identity_axis),
    ]

    # Torso mesh: box from (-1.5,-1,3) to (1.5,1,6)
    torso_tris = [
        (0, 1, 2), (0, 2, 3),  # front
        (4, 5, 6), (4, 6, 7),  # back
        (0, 4, 7), (0, 7, 3),  # left
        (1, 5, 6), (1, 6, 2),  # right
        (3, 2, 6), (3, 6, 7),  # top
        (0, 1, 5), (0, 5, 4),  # bottom
    ]
    torso_tc = [
        (0.0, 0.0), (0.33, 0.0), (0.33, 0.5), (0.0, 0.5),
        (0.5, 0.0), (0.83, 0.0), (0.83, 0.5), (0.5, 0.5),
    ]
    torso_v0 = [
        (-1.5, -1, 3), (1.5, -1, 3), (1.5, -1, 6), (-1.5, -1, 6),
        (-1.5,  1, 3), (1.5,  1, 3), (1.5,  1, 6), (-1.5,  1, 6),
    ]
    torso_v1 = [
        (-1.5, -1, 3), (1.5, -1, 3), (1.5, -1, 6.1), (-1.5, -1, 6.1),
        (-1.5,  1, 3), (1.5,  1, 3), (1.5,  1, 6.1), (-1.5,  1, 6.1),
    ]

    surf = build_surface(
        name="u_torso",
        num_frames=num_frames,
        shaders=[("models/players/sarge/upper", 0)],
        triangles=torso_tris,
        texcoords=torso_tc,
        verts_per_frame=[
            [(float(x), float(y), float(z)) for x, y, z in torso_v0],
            [(float(x), float(y), float(z)) for x, y, z in torso_v1],
        ],
    )

    data = build_md3("models/players/sarge/upper", num_frames,
                     [tags_frame0, tags_frame1], [surf], frames)
    fname = f"upper{suffix}.md3"
    write_file(os.path.join(output_dir, fname), data)
    return data


# ============================================================
# head.md3 - Head model with tag_head (for RemoveSingleNodeFromList)
#   1 frame (heads typically don't animate), 1 surface, 1 tag
# ============================================================
def generate_head(output_dir, suffix=""):
    """Generate head MD3 with tag_head (for removal exercise)."""
    num_frames = 2  # Match frame count with other parts

    frames = [
        make_frame("idle0", (-1, -1, 6), (1, 1, 8), (0, 0, 7), 1.5),
        make_frame("idle1", (-1, -1, 6), (1, 1, 8), (0, 0, 7), 1.5),
    ]

    identity_axis = (1, 0, 0, 0, 1, 0, 0, 0, 1)

    # tag_head present so RemoveSingleNodeFromList can exercise removing it
    tags_frame0 = [
        ("tag_head", (0.0, 0.0, 6.0), identity_axis),
    ]
    tags_frame1 = [
        ("tag_head", (0.0, 0.0, 6.0), identity_axis),
    ]

    # Head mesh: a simple sphere-approximation (6 verts, 8 tris - octahedron)
    head_tris = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),  # top half
        (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4),  # bottom half
    ]
    head_tc = [
        (0.5, 0.0),  # top
        (0.0, 0.5), (0.5, 0.5), (1.0, 0.5), (0.5, 1.0),  # equator
        (0.5, 1.0),  # bottom
    ]
    head_v0 = [
        (0.0,  0.0, 8.0),   # top
        (1.0,  0.0, 7.0),   # front
        (0.0,  1.0, 7.0),   # right
        (-1.0, 0.0, 7.0),   # back
        (0.0, -1.0, 7.0),   # left
        (0.0,  0.0, 6.0),   # bottom
    ]
    # Frame 1: identical (heads don't animate much)
    head_v1 = head_v0[:]

    surf = build_surface(
        name="h_head",
        num_frames=num_frames,
        shaders=[("models/players/sarge/head", 0)],
        triangles=head_tris,
        texcoords=head_tc,
        verts_per_frame=[head_v0, head_v1],
    )

    data = build_md3("models/players/sarge/head", num_frames,
                     [tags_frame0, tags_frame1], [surf], frames)
    fname = f"head{suffix}.md3"
    write_file(os.path.join(output_dir, fname), data)
    return data


# ============================================================
# Generate skin files for multipart model
# ============================================================
def generate_skin(output_dir, part_name, surface_name, suffix=""):
    """Generate a .skin file for a model part."""
    skin_name = f"{part_name}{suffix}_default.skin"
    content = f"{surface_name},{part_name}_texture\n"
    filepath = os.path.join(output_dir, skin_name)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"  {skin_name}: {len(content)} bytes")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating MD3 multipart seeds in {OUTPUT_DIR}")
    print()

    # Set 1: Plain names (lower.md3, upper.md3, head.md3)
    print("Set 1: Plain multipart (lower/upper/head.md3)")
    generate_lower(OUTPUT_DIR)
    generate_upper(OUTPUT_DIR)
    generate_head(OUTPUT_DIR)
    generate_skin(OUTPUT_DIR, "lower", "l_legs")
    generate_skin(OUTPUT_DIR, "upper", "u_torso")
    generate_skin(OUTPUT_DIR, "head", "h_head")
    print()

    # Set 2: Suffixed names (lower_d.md3, upper_d.md3, head_d.md3)
    # This exercises the suffix-parsing path where mod_filename is extracted
    # before the last '_' in the filename.
    print("Set 2: Suffixed multipart (lower_d/upper_d/head_d.md3)")
    generate_lower(OUTPUT_DIR, suffix="_d")
    generate_upper(OUTPUT_DIR, suffix="_d")
    generate_head(OUTPUT_DIR, suffix="_d")
    generate_skin(OUTPUT_DIR, "lower", "l_legs", suffix="_d")
    generate_skin(OUTPUT_DIR, "upper", "u_torso", suffix="_d")
    generate_skin(OUTPUT_DIR, "head", "h_head", suffix="_d")
    print()

    print("Done. Generated multipart MD3 seed files.")
    print()
    print("To use in fuzzing:")
    print("  - The md3_file fuzzer should write fuzz data as 'lower.md3'")
    print("    and provide upper.md3 + head.md3 as companions")
    print("  - Set AI_CONFIG_IMPORT_MD3_HANDLE_MULTIPART = 1")
    print(f"  - Seed corpus: {OUTPUT_DIR}")
