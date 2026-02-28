#!/usr/bin/env python3
"""Generate binary LWO/LWO2/LWOB/LWO3 seed files for fuzzing the assimp LWO importer.

Produces seed files exercising various LWO format features:
  - seed_lwo2_basic.lwo       LWO2 with LAYR, PNTS, POLS, SURF, TAGS, PTAG, VMAP
  - seed_lwo2_advanced.lwo    LWO2 with multiple layers, VMAD, weight/morph VMAPs,
                               texture blocks, CLIPs, ENVLs
  - seed_lwob.lwo             LWOB (pre-v6) format
  - seed_lwo3_nodal.lwo       LWO3 with nodal surface blocks
  - seed_lwo2_clips.lwo       LWO2 with ISEQ, NEGA clips
  - seed_lwo2_subdivision.lwo LWO2 with SUBD/PTCH polygon types

All binary data uses big-endian byte order per the IFF/LWO specification.
"""

import os
import struct

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test", "models", "LWO", "fuzz_seeds")


# ---------------------------------------------------------------------------
# Helper: FourCC as big-endian uint32
# ---------------------------------------------------------------------------
def fourcc(s):
    """Convert a 4-character ASCII string to a big-endian uint32."""
    assert len(s) == 4
    return struct.pack(">4s", s.encode("ascii"))


# IFF top-level tags
FORM = fourcc("FORM")
LWOB = fourcc("LWOB")
LWO2 = fourcc("LWO2")
LWO3 = fourcc("LWO3")

# Top-level chunk tags
LAYR = fourcc("LAYR")
TAGS = fourcc("TAGS")
SRFS = fourcc("SRFS")
PNTS = fourcc("PNTS")
POLS = fourcc("POLS")
PTAG = fourcc("PTAG")
VMAP = fourcc("VMAP")
VMAD = fourcc("VMAD")
SURF = fourcc("SURF")
CLIP = fourcc("CLIP")
ENVL = fourcc("ENVL")

# Polygon types
FACE = fourcc("FACE")
SUBD = fourcc("SUBD")
PTCH = fourcc("PTCH")

# PTAG types (reuse chunk tags)
SURF_TAG = fourcc("SURF")
SMGP = fourcc("SMGP")

# VMAP types
TXUV = fourcc("TXUV")
WGHT = fourcc("WGHT")
MNVW = fourcc("MNVW")
MORF = fourcc("MORF")
RGB_ = fourcc("RGB ")
RGBA = fourcc("RGBA")

# Surface subchunks
COLR = fourcc("COLR")
DIFF = fourcc("DIFF")
SPEC = fourcc("SPEC")
GLOS = fourcc("GLOS")
TRNL = fourcc("TRNL")
TRAN = fourcc("TRAN")
BUMP = fourcc("BUMP")
SMAN = fourcc("SMAN")
SIDE = fourcc("SIDE")
BLOK = fourcc("BLOK")
VCOL = fourcc("VCOL")
CLRH = fourcc("CLRH")
RIND = fourcc("RIND")
LINE = fourcc("LINE")
ADTR = fourcc("ADTR")

# Texture block subchunks
IMAP = fourcc("IMAP")
PROC = fourcc("PROC")
GRAD = fourcc("GRAD")
SHDR = fourcc("SHDR")
CHAN = fourcc("CHAN")
ENAB = fourcc("ENAB")
OPAC = fourcc("OPAC")
PROJ = fourcc("PROJ")
WRAP = fourcc("WRAP")
AXIS = fourcc("AXIS")
IMAG = fourcc("IMAG")
VMAP_SUB = fourcc("VMAP")  # subchunk inside IMAP
TMAP = fourcc("TMAP")
WRPW = fourcc("WRPW")
WRPH = fourcc("WRPH")
FUNC = fourcc("FUNC")

# Clip subchunks
STIL = fourcc("STIL")
ISEQ = fourcc("ISEQ")
NEGA = fourcc("NEGA")
XREF = fourcc("XREF")

# Envelope subchunks
TYPE = fourcc("TYPE")
PRE_ = fourcc("PRE ")
POST = fourcc("POST")
KEY_ = fourcc("KEY ")
SPAN = fourcc("SPAN")

# Envelope interpolation types
STEP = fourcc("STEP")
LINE_E = fourcc("LINE")
TCB_ = fourcc("TCB ")
HERM = fourcc("HERM")
BEZI = fourcc("BEZI")
BEZ2 = fourcc("BEZ2")

# LWOB-specific subchunks
FLAG = fourcc("FLAG")
CTEX = fourcc("CTEX")
DTEX = fourcc("DTEX")
STEX = fourcc("STEX")
BTEX = fourcc("BTEX")
TTEX = fourcc("TTEX")
TIMG = fourcc("TIMG")
TFLG = fourcc("TFLG")
TVAL = fourcc("TVAL")
LUMI = fourcc("LUMI")

# LWO3 nodal
NODS = fourcc("NODS")
NNDS = fourcc("NNDS")
NTAG = fourcc("NTAG")
NDTA = fourcc("NDTA")
ENTR = fourcc("ENTR")
NAME = fourcc("NAME")
VALU = fourcc("VALU")
FLAG_N = fourcc("FLAG")
TAG_ = fourcc("TAG ")
VERS = fourcc("VERS")


# ---------------------------------------------------------------------------
# Primitive packing helpers
# ---------------------------------------------------------------------------
def f4(val):
    """Pack a 32-bit big-endian float."""
    return struct.pack(">f", val)


def f8(val):
    """Pack a 64-bit big-endian double."""
    return struct.pack(">d", val)


def u4(val):
    """Pack a 32-bit big-endian unsigned int."""
    return struct.pack(">I", val)


def u2(val):
    """Pack a 16-bit big-endian unsigned short."""
    return struct.pack(">H", val)


def u1(val):
    """Pack an 8-bit unsigned byte."""
    return struct.pack(">B", val)


def s2(val):
    """Pack a 16-bit big-endian signed short."""
    return struct.pack(">h", val)


def lwo_string(s):
    """Encode a null-terminated, even-padded LWO string."""
    b = s.encode("ascii") + b"\x00"
    if len(b) % 2 != 0:
        b += b"\x00"
    return b


def vx(index):
    """Encode a variable-length vertex index for LWO2/LWO3.

    If index < 0xFF00 use 2 bytes, otherwise use 4 bytes with 0xFF prefix byte.
    """
    if index < 0xFF00:
        return struct.pack(">H", index)
    else:
        return struct.pack(">BH", 0xFF, index)


# ---------------------------------------------------------------------------
# Chunk / subchunk builders
# ---------------------------------------------------------------------------
def chunk(tag, data):
    """Build a top-level IFF chunk: 4-byte tag + 4-byte big-endian length + data.

    Pads to even length per IFF spec.
    """
    if len(data) % 2 != 0:
        data += b"\x00"
    return tag + u4(len(data)) + data


def subchunk(tag, data):
    """Build an IFF subchunk: 4-byte tag + 2-byte big-endian length + data.

    Pads to even length per IFF spec.
    """
    if len(data) % 2 != 0:
        data += b"\x00"
    return tag + u2(len(data)) + data


def form_chunk(tag, data):
    """Build a FORM wrapper: 'FORM' + 4-byte length + 4-byte form type + data."""
    inner = tag + data
    return FORM + u4(len(inner)) + inner


def iff_file(form_type, chunks_data):
    """Build a complete IFF file: FORM header + form type + concatenated chunk data."""
    inner = form_type + chunks_data
    return FORM + u4(len(inner)) + inner


# ---------------------------------------------------------------------------
# Vertex / polygon helpers
# ---------------------------------------------------------------------------
def make_pnts(vertices):
    """Build a PNTS chunk from a list of (x, y, z) tuples."""
    data = b""
    for x, y, z in vertices:
        data += f4(x) + f4(y) + f4(z)
    return chunk(PNTS, data)


def make_lwo2_pols(poly_type, faces):
    """Build a LWO2 POLS chunk.

    poly_type: 4-byte tag (FACE, SUBD, PTCH, etc.)
    faces: list of lists of vertex indices
    """
    data = poly_type
    for face in faces:
        n = len(face)
        data += u2(n)
        for idx in face:
            data += vx(idx)
    return chunk(POLS, data)


def make_lwob_pols(faces_with_surf):
    """Build an LWOB POLS chunk.

    faces_with_surf: list of (vertex_indices_list, surface_index_1based)
    In LWOB, each polygon stores: numverts, idx0, idx1, ..., surface_index (signed int16).
    """
    data = b""
    for indices, surf_idx in faces_with_surf:
        data += u2(len(indices))
        for idx in indices:
            data += u2(idx)
        data += s2(surf_idx)
    return chunk(POLS, data)


def make_tags(names):
    """Build a TAGS chunk from a list of surface name strings."""
    data = b""
    for name in names:
        data += lwo_string(name)
    return chunk(TAGS, data)


def make_srfs(names):
    """Build an LWOB SRFS chunk from a list of surface name strings."""
    data = b""
    for name in names:
        data += lwo_string(name)
    return chunk(SRFS, data)


def make_ptag(tag_type, assignments):
    """Build a PTAG chunk.

    tag_type: 4-byte tag (SURF, SMGP, etc.)
    assignments: list of (polygon_index, tag_index) tuples
    """
    data = tag_type
    for poly_idx, tag_idx in assignments:
        data += vx(poly_idx) + u2(tag_idx)
    return chunk(PTAG, data)


def make_layr(index, flags=0, pivot=(0.0, 0.0, 0.0), name="", parent=None):
    """Build a LAYR chunk."""
    data = u2(index) + u2(flags)
    data += f4(pivot[0]) + f4(pivot[1]) + f4(pivot[2])
    data += lwo_string(name)
    if parent is not None:
        data += u2(parent)
    return chunk(LAYR, data)


def make_vmap(vmap_type, dimension, name, entries):
    """Build a VMAP chunk.

    entries: list of (vertex_index, values_tuple) where values_tuple has `dimension` floats
    """
    data = vmap_type + u2(dimension) + lwo_string(name)
    for idx, values in entries:
        data += vx(idx)
        for v in values:
            data += f4(v)
    return chunk(VMAP, data)


def make_vmad(vmap_type, dimension, name, entries):
    """Build a VMAD (discontinuous vertex map) chunk.

    entries: list of (vertex_index, polygon_index, values_tuple)
    """
    data = vmap_type + u2(dimension) + lwo_string(name)
    for vtx_idx, poly_idx, values in entries:
        data += vx(vtx_idx) + vx(poly_idx)
        for v in values:
            data += f4(v)
    return chunk(VMAD, data)


# ---------------------------------------------------------------------------
# SEED 1: seed_lwo2_basic.lwo
# ---------------------------------------------------------------------------
def generate_seed_lwo2_basic():
    """LWO2 with LAYR, PNTS, POLS(FACE), TAGS, PTAG, SURF (COLR, DIFF, SPEC, GLOS, TRNL), VMAP(TXUV)."""
    vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
    ]
    faces = [
        [0, 1, 2],
        [0, 2, 3],
    ]
    uv_entries = [
        (0, (0.0, 0.0)),
        (1, (1.0, 0.0)),
        (2, (1.0, 1.0)),
        (3, (0.0, 1.0)),
    ]

    # Surface: "Default"
    surf_data = lwo_string("Default") + lwo_string("")  # name + source (empty)
    # COLR: 3 floats + 2-byte envelope index (0)
    surf_data += subchunk(COLR, f4(0.8) + f4(0.2) + f4(0.1) + u2(0))
    # DIFF: float + envelope
    surf_data += subchunk(DIFF, f4(0.9) + u2(0))
    # SPEC: float + envelope
    surf_data += subchunk(SPEC, f4(0.5) + u2(0))
    # GLOS: float + envelope
    surf_data += subchunk(GLOS, f4(0.4) + u2(0))
    # TRNL: float + envelope (translucency)
    surf_data += subchunk(TRNL, f4(0.0) + u2(0))
    # SMAN: smoothing angle
    surf_data += subchunk(SMAN, f4(1.5))

    chunks = b""
    chunks += make_tags(["Default"])
    chunks += make_layr(0, name="Layer0")
    chunks += make_pnts(vertices)
    chunks += make_lwo2_pols(FACE, faces)
    chunks += make_ptag(SURF_TAG, [(0, 0), (1, 0)])
    chunks += make_vmap(TXUV, 2, "UVMap", uv_entries)
    chunks += chunk(SURF, surf_data)

    return iff_file(LWO2, chunks)


# ---------------------------------------------------------------------------
# SEED 2: seed_lwo2_advanced.lwo
# ---------------------------------------------------------------------------
def generate_seed_lwo2_advanced():
    """LWO2 with multiple layers, VMAD, weight/morph VMAPs, texture blocks,
    CLIPs, and ENVLs with various interpolation types."""

    vertices_l0 = [
        (-1.0, -1.0, 0.0),
        (1.0, -1.0, 0.0),
        (1.0, 1.0, 0.0),
        (-1.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    ]
    faces_l0 = [
        [0, 1, 4],
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4],
        [0, 1, 2, 3],
    ]

    vertices_l1 = [
        (2.0, 0.0, 0.0),
        (3.0, 0.0, 0.0),
        (3.0, 1.0, 0.0),
    ]
    faces_l1 = [
        [0, 1, 2],
    ]

    # -- CLIP 1: STIL
    clip1_data = u4(1)  # clip index
    clip1_sub = subchunk(STIL, lwo_string("textures/diffuse.tga"))
    clip1 = chunk(CLIP, clip1_data + clip1_sub)

    # -- CLIP 2: STIL with NEGA
    clip2_data = u4(2)
    clip2_sub = subchunk(STIL, lwo_string("textures/specular.tga"))
    clip2_sub += subchunk(NEGA, u2(1))
    clip2 = chunk(CLIP, clip2_data + clip2_sub)

    # -- ENVL 1: position X envelope with multiple keys and SPAN types
    envl1_data = vx(1)  # envelope index
    envl1_data += subchunk(TYPE, u1(0) + u1(0x01))  # user format + type
    envl1_data += subchunk(PRE_, u2(1))   # constant
    envl1_data += subchunk(POST, u2(2))   # repeat
    envl1_data += subchunk(KEY_, f4(0.0) + f4(0.0))
    envl1_data += subchunk(KEY_, f4(1.0) + f4(5.0))
    envl1_data += subchunk(SPAN, STEP)
    envl1_data += subchunk(KEY_, f4(2.0) + f4(3.0))
    envl1_data += subchunk(SPAN, LINE_E)
    envl1_data += subchunk(KEY_, f4(3.0) + f4(7.0))
    envl1_data += subchunk(SPAN, TCB_)
    envl1_data += subchunk(KEY_, f4(4.0) + f4(1.0))
    envl1_data += subchunk(SPAN, HERM)
    envl1_data += subchunk(KEY_, f4(5.0) + f4(9.0))
    envl1_data += subchunk(SPAN, BEZI)
    envl1_data += subchunk(KEY_, f4(6.0) + f4(2.0))
    envl1_data += subchunk(SPAN, BEZ2)
    envl1 = chunk(ENVL, envl1_data)

    # -- Surface "MatA" with BLOK containing IMAP texture
    surf_a = lwo_string("MatA") + lwo_string("")
    surf_a += subchunk(COLR, f4(0.9) + f4(0.1) + f4(0.1) + u2(0))
    surf_a += subchunk(DIFF, f4(1.0) + u2(0))
    surf_a += subchunk(SPEC, f4(0.3) + u2(0))
    surf_a += subchunk(GLOS, f4(0.5) + u2(0))
    surf_a += subchunk(SMAN, f4(1.0))
    surf_a += subchunk(SIDE, u2(3))  # double-sided
    surf_a += subchunk(RIND, f4(1.5))
    surf_a += subchunk(BUMP, f4(1.0) + u2(0))
    surf_a += subchunk(CLRH, f4(0.2) + u2(0))
    surf_a += subchunk(TRAN, f4(0.0) + u2(0))
    surf_a += subchunk(ADTR, f4(0.0) + u2(0))
    surf_a += subchunk(LINE, u2(0))

    # Build an IMAP texture block
    # The texture header: ordinal + subchunks (CHAN, ENAB, OPAC)
    tex_header = lwo_string("\x00")  # ordinal
    tex_header += subchunk(CHAN, COLR)  # channel = color
    tex_header += subchunk(ENAB, u2(1))
    tex_header += subchunk(OPAC, u2(0) + f4(1.0))  # blend type + strength

    # IMAP body: PROJ, WRAP, IMAG, VMAP, WRPW, WRPH
    imap_body = subchunk(PROJ, u2(5))  # UV mapping
    imap_body += subchunk(WRAP, u2(1) + u2(1))  # repeat, repeat
    imap_body += subchunk(IMAG, u2(1))  # clip index 1
    imap_body += subchunk(VMAP_SUB, lwo_string("UVMap"))
    imap_body += subchunk(WRPW, f4(1.0) + u2(0))
    imap_body += subchunk(WRPH, f4(1.0) + u2(0))
    imap_body += subchunk(AXIS, u2(2))  # Z axis

    # Complete IMAP subchunk inside BLOK
    imap_sub = subchunk(IMAP, tex_header) + imap_body

    # BLOK subchunk
    surf_a += subchunk(BLOK, imap_sub)

    # Build a second texture block for specular using IMAP
    tex_header2 = lwo_string("\x01")
    tex_header2 += subchunk(CHAN, SPEC)
    tex_header2 += subchunk(ENAB, u2(1))
    tex_header2 += subchunk(OPAC, u2(0) + f4(0.5))

    imap_body2 = subchunk(PROJ, u2(5))
    imap_body2 += subchunk(WRAP, u2(1) + u2(1))
    imap_body2 += subchunk(IMAG, u2(2))
    imap_body2 += subchunk(VMAP_SUB, lwo_string("UVMap"))

    imap_sub2 = subchunk(IMAP, tex_header2) + imap_body2
    surf_a += subchunk(BLOK, imap_sub2)

    # Build a shader block
    shdr_header = lwo_string("\x02")
    shdr_header += subchunk(ENAB, u2(1))
    shdr_header += subchunk(FUNC, lwo_string("LW_FastFresnel"))
    surf_a += subchunk(BLOK, subchunk(SHDR, shdr_header))

    # -- Surface "MatB" (simpler)
    surf_b = lwo_string("MatB") + lwo_string("")
    surf_b += subchunk(COLR, f4(0.1) + f4(0.1) + f4(0.9) + u2(0))
    surf_b += subchunk(DIFF, f4(0.7) + u2(0))
    surf_b += subchunk(SPEC, f4(0.8) + u2(0))
    surf_b += subchunk(GLOS, f4(0.3) + u2(0))

    # VCOL subchunk
    surf_b += subchunk(VCOL,
                       f4(1.0) + vx(0) + fourcc("RGBA") + lwo_string("VColors"))

    # Assemble all chunks
    chunks = b""
    chunks += make_tags(["MatA", "MatB"])

    # Layer 0
    chunks += make_layr(0, name="BaseLayer")
    chunks += make_pnts(vertices_l0)
    chunks += make_lwo2_pols(FACE, faces_l0)
    chunks += make_ptag(SURF_TAG, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 1)])
    chunks += make_ptag(SMGP, [(0, 1), (1, 1), (2, 1), (3, 1), (4, 0)])

    # UVs
    uv_l0 = [
        (0, (0.0, 0.0)),
        (1, (1.0, 0.0)),
        (2, (1.0, 1.0)),
        (3, (0.0, 1.0)),
        (4, (0.5, 0.5)),
    ]
    chunks += make_vmap(TXUV, 2, "UVMap", uv_l0)

    # Weight map
    wght_entries = [(0, (1.0,)), (1, (0.5,)), (2, (0.8,)), (3, (0.3,)), (4, (1.0,))]
    chunks += make_vmap(WGHT, 1, "BoneWeight", wght_entries)

    # Secondary weight (MNVW)
    mnvw_entries = [(0, (0.5,)), (1, (0.2,))]
    chunks += make_vmap(MNVW, 1, "SubdWeight", mnvw_entries)

    # VMAD (discontinuous UV)
    vmad_entries = [
        (0, 0, (0.1, 0.1)),
        (1, 0, (0.9, 0.1)),
        (4, 0, (0.5, 0.5)),
    ]
    chunks += make_vmad(TXUV, 2, "UVMap", vmad_entries)

    # Layer 1
    chunks += make_layr(1, name="SecondLayer", parent=0)
    chunks += make_pnts(vertices_l1)
    chunks += make_lwo2_pols(FACE, faces_l1)
    chunks += make_ptag(SURF_TAG, [(0, 1)])

    # Clips
    chunks += clip1
    chunks += clip2

    # Envelope
    chunks += envl1

    # Surfaces
    chunks += chunk(SURF, surf_a)
    chunks += chunk(SURF, surf_b)

    return iff_file(LWO2, chunks)


# ---------------------------------------------------------------------------
# SEED 3: seed_lwob.lwo
# ---------------------------------------------------------------------------
def generate_seed_lwob():
    """LWOB (pre-v6) format with SRFS, PNTS, POLS, SURF (old-style subchunks)."""
    vertices = [
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (2.0, 2.0, 0.0),
        (0.0, 2.0, 0.0),
        (1.0, 1.0, 1.0),
    ]

    # LWOB polygon format: numverts idx0 idx1 ... surfaceIndex(signed int16, 1-based)
    faces = [
        ([0, 1, 2], 1),
        ([0, 2, 3], 1),
        ([0, 1, 4], 2),
        ([1, 2, 4], 2),
        ([2, 3, 4], 2),
        ([3, 0, 4], 2),
    ]

    # Surface "Wood" (old format)
    surf1 = lwo_string("Wood")
    # COLR: 4 bytes (R, G, B, pad)
    surf1 += subchunk(COLR, u1(180) + u1(120) + u1(60) + u1(0))
    # DIFF: 2-byte fraction (0-255 scaled)
    surf1 += subchunk(DIFF, u2(230))
    # SPEC: 2-byte
    surf1 += subchunk(SPEC, u2(50))
    # GLOS: 2-byte
    surf1 += subchunk(GLOS, u2(64))
    # TRAN: 2-byte
    surf1 += subchunk(TRAN, u2(0))
    # LUMI: 2-byte
    surf1 += subchunk(LUMI, u2(0))
    # FLAG: smoothing + double-sided
    surf1 += subchunk(FLAG, u2(0x04 | 0x100))
    # SMAN
    surf1 += subchunk(SMAN, f4(1.5))
    # CTEX - color texture type
    surf1 += subchunk(CTEX, lwo_string("Planar Image Map"))
    # TIMG - texture file path
    surf1 += subchunk(TIMG, lwo_string("textures/wood_diffuse.tga"))
    # TFLG - texture axis
    surf1 += subchunk(TFLG, u2(4))  # Z axis
    # TVAL - texture strength
    surf1 += subchunk(TVAL, u1(200))

    # Surface "Metal" (old format)
    surf2 = lwo_string("Metal")
    surf2 += subchunk(COLR, u1(200) + u1(200) + u1(210) + u1(0))
    surf2 += subchunk(DIFF, u2(200))
    surf2 += subchunk(SPEC, u2(200))
    surf2 += subchunk(GLOS, u2(128))
    surf2 += subchunk(TRAN, u2(0))
    surf2 += subchunk(FLAG, u2(0x04 | 0x08))  # smoothing + color highlights
    surf2 += subchunk(SMAN, f4(1.2))
    # DTEX - diffuse texture
    surf2 += subchunk(DTEX, lwo_string("Cylindrical Image Map"))
    surf2 += subchunk(TIMG, lwo_string("textures/metal_bump.tga"))
    surf2 += subchunk(TFLG, u2(2))  # Y axis

    chunks = b""
    chunks += make_srfs(["Wood", "Metal"])
    chunks += make_pnts(vertices)
    chunks += make_lwob_pols(faces)
    chunks += chunk(SURF, surf1)
    chunks += chunk(SURF, surf2)

    return iff_file(LWOB, chunks)


# ---------------------------------------------------------------------------
# SEED 4: seed_lwo3_nodal.lwo
# ---------------------------------------------------------------------------
def generate_seed_lwo3_nodal():
    """LWO3 format with LAYR, PNTS, POLS, TAGS, PTAG, and SURF with nodal blocks
    containing NNDS -> NODS -> NTAG -> NDTA with various value types."""

    vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.5, 1.0, 0.0),
        (0.5, 0.5, 1.0),
    ]
    faces = [
        [0, 1, 2],
        [0, 1, 3],
        [1, 2, 3],
        [2, 0, 3],
    ]

    # Build nodal data (NDTA) with ENTR entries containing various value types
    # ENTR with "int" value
    entr1_inner = b""
    entr1_inner += chunk(NAME, lwo_string("SomeInt") + b"\x00" * (2 if len(lwo_string("SomeInt")) % 2 == 0 else 0))
    entr1_inner += chunk(FLAG_N, u4(0))
    # VALU: 8 bytes padding + type string + value
    valu1_data = b"\x00" * 8 + lwo_string("int") + b"\x00" * (4 if len(lwo_string("int")) % 2 == 0 else 0) + u4(42)
    entr1_inner += chunk(VALU, valu1_data)
    entr1 = chunk(ENTR, entr1_inner)

    # ENTR with "double" value
    entr2_inner = b""
    entr2_inner += chunk(NAME, lwo_string("SomeDouble") + b"\x00" * 2)
    entr2_inner += chunk(FLAG_N, u4(0))
    valu2_data = b"\x00" * 8 + lwo_string("double") + b"\x00" * 2 + f8(3.14159)
    entr2_inner += chunk(VALU, valu2_data)
    entr2 = chunk(ENTR, entr2_inner)

    # ENTR with "vparam" value for Diffuse
    entr3_inner = b""
    entr3_inner += chunk(NAME, lwo_string("Diffuse") + b"\x00" * 0)
    entr3_inner += chunk(FLAG_N, u4(0))
    valu3_data = b"\x00" * 8 + lwo_string("vparam")
    valu3_data += b"\x00" * 24  # 24 bytes padding before the value
    valu3_data += f8(0.85)
    entr3_inner += chunk(VALU, valu3_data)
    entr3 = chunk(ENTR, entr3_inner)

    # ENTR with "vparam3" value for Color
    entr4_inner = b""
    entr4_inner += chunk(NAME, lwo_string("Color") + b"\x00" * 0)
    entr4_inner += chunk(FLAG_N, u4(0))
    valu4_data = b"\x00" * 8 + lwo_string("vparam3")
    # pad vparam3 string: "vparam3\0" = 8 bytes (already even)
    valu4_data += b"\x00" * 24
    valu4_data += f8(0.9) + f8(0.2) + f8(0.1)
    entr4_inner += chunk(VALU, valu4_data)
    entr4 = chunk(ENTR, entr4_inner)

    # NDTA contains ENTR entries
    ndta_data = entr3 + entr4
    ndta = chunk(NDTA, ndta_data)

    # NTAG contains NDTA
    ntag = chunk(NTAG, ndta)

    # NODS contains NTAG
    nods = chunk(NODS, ntag)

    # NNDS wraps NODS
    nnds = chunk(NNDS, nods)

    # LWO3 Surface: the surface chunk in LWO3 starts with FORM SURF header
    # LoadLWO3Surface does: mFileBuffer += 8; end = mFileBuffer + size - 12;
    # then reads name, derived, and subchunks
    # The SURF chunk in the main loop is loaded as a normal chunk (tag+length)
    # but LoadLWO3Surface skips 8 bytes at start and adjusts end by -12
    # So we need: 8 bytes padding + surface name + derived name + subchunks
    # where total subchunk region size = chunk_data_length - 12
    surf_inner = b"\x00" * 8  # 8 bytes skipped by LoadLWO3Surface
    surf_inner += lwo_string("NodalMat")
    surf_inner += lwo_string("")  # no derived surface
    surf_inner += chunk(SMAN, f4(1.5))
    surf_inner += chunk(SIDE, u2(3) + u2(0))  # padded to 4 bytes for LWO3
    # NODS subchunk (which dispatches to LoadNodalBlocks)
    surf_inner += chunk(NODS, nnds)

    # Pad surface inner to account for the -12 adjustment
    # We need 12 extra bytes at the end so LoadLWO3Surface's end calculation
    # doesn't cut off our data. Actually, the code does:
    #   mFileBuffer += 8; end = mFileBuffer + size - 12
    # So effective data window = size - 8 - 12 = size - 20 from the chunk start
    # We add 12 bytes of padding at the end
    surf_inner += b"\x00" * 12

    chunks = b""
    chunks += make_tags(["NodalMat"])
    chunks += make_layr(0, name="NodalLayer")
    chunks += make_pnts(vertices)
    chunks += make_lwo2_pols(FACE, faces)
    chunks += make_ptag(SURF_TAG, [(0, 0), (1, 0), (2, 0), (3, 0)])
    chunks += chunk(SURF, surf_inner)

    return iff_file(LWO3, chunks)


# ---------------------------------------------------------------------------
# SEED 5: seed_lwo2_clips.lwo
# ---------------------------------------------------------------------------
def generate_seed_lwo2_clips():
    """LWO2 with CLIP (ISEQ, STIL with NEGA), multiple clips referenced from surfaces."""

    vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
    ]
    faces = [
        [0, 1, 2],
        [0, 2, 3],
    ]

    # CLIP 1: STIL (still image)
    clip1_data = u4(1) + subchunk(STIL, lwo_string("images/photo.tga"))
    clip1 = chunk(CLIP, clip1_data)

    # CLIP 2: ISEQ (image sequence)
    # ISEQ format: digits(U1), flags(U1), offset(I2), pad(4 bytes), start(I2), pad(4 bytes),
    #              prefix string, suffix string
    iseq_inner = u1(3)        # digits
    iseq_inner += u1(0)       # flags
    iseq_inner += u2(0)       # offset
    iseq_inner += u4(0)       # padding
    iseq_inner += u2(1)       # start frame
    iseq_inner += u4(0)       # padding
    iseq_inner += lwo_string("frames/anim_")
    iseq_inner += lwo_string(".tga")
    clip2_data = u4(2) + subchunk(ISEQ, iseq_inner)
    clip2 = chunk(CLIP, clip2_data)

    # CLIP 3: STIL with NEGA flag
    clip3_data = u4(3)
    clip3_data += subchunk(STIL, lwo_string("images/mask.tga"))
    clip3_data += subchunk(NEGA, u2(1))
    clip3 = chunk(CLIP, clip3_data)

    # CLIP 4: XREF to clip 1
    clip4_data = u4(4)
    clip4_data += subchunk(XREF, u4(1))
    clip4 = chunk(CLIP, clip4_data)

    # Surface with BLOK referencing clips 1 (color) and 3 (opacity)
    surf_data = lwo_string("ClipSurf") + lwo_string("")
    surf_data += subchunk(COLR, f4(1.0) + f4(1.0) + f4(1.0) + u2(0))
    surf_data += subchunk(DIFF, f4(1.0) + u2(0))
    surf_data += subchunk(SPEC, f4(0.2) + u2(0))
    surf_data += subchunk(GLOS, f4(0.3) + u2(0))
    surf_data += subchunk(SMAN, f4(1.0))

    # Texture block referencing clip 1 on color channel
    tex_h1 = lwo_string("\x00")
    tex_h1 += subchunk(CHAN, COLR)
    tex_h1 += subchunk(ENAB, u2(1))
    tex_h1 += subchunk(OPAC, u2(0) + f4(1.0))
    imap1 = subchunk(PROJ, u2(5))
    imap1 += subchunk(WRAP, u2(1) + u2(1))
    imap1 += subchunk(IMAG, u2(1))  # clip index 1
    imap1 += subchunk(VMAP_SUB, lwo_string("UV"))
    surf_data += subchunk(BLOK, subchunk(IMAP, tex_h1) + imap1)

    # Texture block referencing clip 2 (sequence) on diffuse channel
    tex_h2 = lwo_string("\x01")
    tex_h2 += subchunk(CHAN, DIFF)
    tex_h2 += subchunk(ENAB, u2(1))
    tex_h2 += subchunk(OPAC, u2(0) + f4(0.8))
    imap2 = subchunk(PROJ, u2(0))  # planar
    imap2 += subchunk(WRAP, u2(1) + u2(1))
    imap2 += subchunk(IMAG, u2(2))  # clip index 2
    imap2 += subchunk(AXIS, u2(1))  # Y axis
    surf_data += subchunk(BLOK, subchunk(IMAP, tex_h2) + imap2)

    # Texture block referencing clip 3 (negated) on opacity channel
    tex_h3 = lwo_string("\x02")
    tex_h3 += subchunk(CHAN, TRAN)
    tex_h3 += subchunk(ENAB, u2(1))
    tex_h3 += subchunk(OPAC, u2(0) + f4(1.0))
    imap3 = subchunk(PROJ, u2(5))
    imap3 += subchunk(WRAP, u2(1) + u2(1))
    imap3 += subchunk(IMAG, u2(3))  # clip index 3
    imap3 += subchunk(VMAP_SUB, lwo_string("UV"))
    surf_data += subchunk(BLOK, subchunk(IMAP, tex_h3) + imap3)

    uv_entries = [
        (0, (0.0, 0.0)),
        (1, (1.0, 0.0)),
        (2, (1.0, 1.0)),
        (3, (0.0, 1.0)),
    ]

    chunks = b""
    chunks += make_tags(["ClipSurf"])
    chunks += make_layr(0, name="ClipLayer")
    chunks += make_pnts(vertices)
    chunks += make_lwo2_pols(FACE, faces)
    chunks += make_ptag(SURF_TAG, [(0, 0), (1, 0)])
    chunks += make_vmap(TXUV, 2, "UV", uv_entries)
    chunks += clip1
    chunks += clip2
    chunks += clip3
    chunks += clip4
    chunks += chunk(SURF, surf_data)

    return iff_file(LWO2, chunks)


# ---------------------------------------------------------------------------
# SEED 6: seed_lwo2_subdivision.lwo
# ---------------------------------------------------------------------------
def generate_seed_lwo2_subdivision():
    """LWO2 with SUBD and PTCH polygon types and APS.Level VMAP."""

    # A cube with 8 vertices
    vertices = [
        (-1.0, -1.0, -1.0),
        (1.0, -1.0, -1.0),
        (1.0, 1.0, -1.0),
        (-1.0, 1.0, -1.0),
        (-1.0, -1.0, 1.0),
        (1.0, -1.0, 1.0),
        (1.0, 1.0, 1.0),
        (-1.0, 1.0, 1.0),
    ]

    # Faces for subdivision surfaces (quads)
    subd_faces = [
        [0, 1, 2, 3],  # front
        [4, 7, 6, 5],  # back
        [0, 4, 5, 1],  # bottom
        [2, 6, 7, 3],  # top
    ]

    # Faces for patches (quads)
    ptch_faces = [
        [0, 3, 7, 4],  # left
        [1, 5, 6, 2],  # right
    ]

    # UV entries
    uv_entries = []
    for i in range(8):
        uv_entries.append((i, (float(i % 2), float(i // 4))))

    # Weight entries
    wght_entries = [(i, (1.0,)) for i in range(8)]

    chunks = b""
    chunks += make_tags(["SubdSurf", "PatchSurf"])
    chunks += make_layr(0, name="SubdLayer")
    chunks += make_pnts(vertices)

    # SUBD polygons
    chunks += make_lwo2_pols(SUBD, subd_faces)
    # PTAG for SUBD faces (indices 0-3)
    chunks += make_ptag(SURF_TAG, [(0, 0), (1, 0), (2, 0), (3, 0)])

    # PTCH polygons
    chunks += make_lwo2_pols(PTCH, ptch_faces)
    # PTAG for PTCH faces (indices 0-1 offset by previous face count -> 4,5)
    chunks += make_ptag(SURF_TAG, [(0, 1), (1, 1)])

    chunks += make_vmap(TXUV, 2, "UVMap", uv_entries)
    chunks += make_vmap(WGHT, 1, "BoneWeight", wght_entries)

    # APS.Level weight map for subdivision level (handled as unknown but with name check)
    aps_entries = [(i, (2.0,)) for i in range(8)]
    chunks += make_vmap(WGHT, 1, "APS.Level", aps_entries)

    # Surface "SubdSurf"
    surf1 = lwo_string("SubdSurf") + lwo_string("")
    surf1 += subchunk(COLR, f4(0.2) + f4(0.7) + f4(0.2) + u2(0))
    surf1 += subchunk(DIFF, f4(0.9) + u2(0))
    surf1 += subchunk(SPEC, f4(0.4) + u2(0))
    surf1 += subchunk(GLOS, f4(0.5) + u2(0))
    surf1 += subchunk(SMAN, f4(1.5))
    chunks += chunk(SURF, surf1)

    # Surface "PatchSurf"
    surf2 = lwo_string("PatchSurf") + lwo_string("")
    surf2 += subchunk(COLR, f4(0.7) + f4(0.2) + f4(0.7) + u2(0))
    surf2 += subchunk(DIFF, f4(0.8) + u2(0))
    surf2 += subchunk(SPEC, f4(0.6) + u2(0))
    surf2 += subchunk(GLOS, f4(0.3) + u2(0))
    surf2 += subchunk(SMAN, f4(1.0))
    chunks += chunk(SURF, surf2)

    return iff_file(LWO2, chunks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seeds = [
        ("seed_lwo2_basic.lwo", generate_seed_lwo2_basic),
        ("seed_lwo2_advanced.lwo", generate_seed_lwo2_advanced),
        ("seed_lwob.lwo", generate_seed_lwob),
        ("seed_lwo3_nodal.lwo", generate_seed_lwo3_nodal),
        ("seed_lwo2_clips.lwo", generate_seed_lwo2_clips),
        ("seed_lwo2_subdivision.lwo", generate_seed_lwo2_subdivision),
    ]

    for filename, generator in seeds:
        path = os.path.join(OUTPUT_DIR, filename)
        data = generator()
        with open(path, "wb") as fh:
            fh.write(data)
        print(f"  Written {path} ({len(data)} bytes)")

    print(f"\nGenerated {len(seeds)} LWO seed files in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
