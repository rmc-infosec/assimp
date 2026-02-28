#!/usr/bin/env python3
"""Generate binary 3DS seed files for fuzzing.

3DS uses a chunk-based binary format:
  - Each chunk: uint16 chunk_id + uint32 chunk_size (including header)
  - Chunk header is 6 bytes
  - Strings are null-terminated
  - Numbers are little-endian
"""

import struct
import os

# Chunk IDs from 3DSHelper.h
CHUNK_MAIN       = 0x4D4D
CHUNK_VERSION    = 0x0002
CHUNK_OBJMESH    = 0x3D3D
CHUNK_MASTER_SCALE = 0x0100
CHUNK_AMBCOLOR   = 0x2100
CHUNK_BIT_MAP    = 0x1100
CHUNK_BIT_MAP_EXISTS = 0x1101

# Object chunks
CHUNK_OBJBLOCK   = 0x4000
CHUNK_TRIMESH    = 0x4100
CHUNK_VERTLIST   = 0x4110
CHUNK_FACELIST   = 0x4120
CHUNK_FACEMAT    = 0x4130
CHUNK_MAPLIST    = 0x4140
CHUNK_SMOOLIST   = 0x4150
CHUNK_TRMATRIX   = 0x4160

# Light chunks
CHUNK_LIGHT      = 0x4600
CHUNK_DL_SPOTLIGHT = 0x4610
CHUNK_DL_ATTENUATE = 0x4625
CHUNK_DL_MULTIPLIER = 0x465B

# Camera chunks
CHUNK_CAMERA     = 0x4700
CHUNK_CAM_RANGES = 0x4720

# Color chunks
CHUNK_RGBF       = 0x0010
CHUNK_RGBB       = 0x0011
CHUNK_LINRGBF    = 0x0013
CHUNK_LINRGBB    = 0x0012
CHUNK_PERCENTW   = 0x0030
CHUNK_PERCENTF   = 0x0031

# Material chunks
CHUNK_MAT_MATERIAL  = 0xAFFF
CHUNK_MAT_MATNAME   = 0xA000
CHUNK_MAT_AMBIENT   = 0xA010
CHUNK_MAT_DIFFUSE   = 0xA020
CHUNK_MAT_SPECULAR  = 0xA030
CHUNK_MAT_SHININESS = 0xA040
CHUNK_MAT_SHININESS_PERCENT = 0xA041
CHUNK_MAT_SHADING   = 0xA100
CHUNK_MAT_TRANSPARENCY = 0xA050
CHUNK_MAT_TWO_SIDE  = 0xA081
CHUNK_MAT_SELF_ILLUM = 0xA080
CHUNK_MAT_SELF_ILPCT = 0xA084
CHUNK_MAT_TEXTURE   = 0xA200
CHUNK_MAT_BUMPMAP   = 0xA230
CHUNK_MAT_OPACMAP   = 0xA210
CHUNK_MAT_SPECMAP   = 0xA204
CHUNK_MAT_REFLMAP   = 0xA220
CHUNK_MAT_SELFIMAP  = 0xA33D
CHUNK_MAT_MAT_SHINMAP = 0xA33C
CHUNK_MAPFILE       = 0xA300
CHUNK_MAT_MAP_USCALE  = 0xA354
CHUNK_MAT_MAP_VSCALE  = 0xA356
CHUNK_MAT_MAP_UOFFSET = 0xA358
CHUNK_MAT_MAP_VOFFSET = 0xA35A
CHUNK_MAT_MAP_ANG     = 0xA35C
CHUNK_MAT_MAP_TILING  = 0xA351

# Keyframe chunks
CHUNK_KEYFRAMER     = 0xB000
CHUNK_TRACKINFO     = 0xB002
CHUNK_TRACKOBJNAME  = 0xB010
CHUNK_TRACKDUMMYOBJNAME = 0xB011
CHUNK_TRACKPIVOT    = 0xB013
CHUNK_TRACKPOS      = 0xB020
CHUNK_TRACKROTATE   = 0xB021
CHUNK_TRACKSCALE    = 0xB022
CHUNK_TRACKCAMERA   = 0xB003
CHUNK_TRACKROLL     = 0xB024
CHUNK_TRACKCAMTGT   = 0xB004
CHUNK_TRACKLIGHT    = 0xB005
CHUNK_TRACKLIGTGT   = 0xB006
CHUNK_TRACKFOV      = 0xB023


def make_chunk(chunk_id, data=b''):
    """Build a chunk: uint16 id + uint32 size + data."""
    size = 6 + len(data)
    return struct.pack('<HI', chunk_id, size) + data


def make_string(s):
    """Null-terminated string."""
    return s.encode('ascii') + b'\x00'


def make_color_rgbf(r, g, b):
    """Float RGB color chunk."""
    return make_chunk(CHUNK_RGBF, struct.pack('<fff', r, g, b))


def make_color_rgbb(r, g, b):
    """Byte RGB color chunk."""
    return make_chunk(CHUNK_RGBB, struct.pack('<BBB', r, g, b))


def make_color_linrgbf(r, g, b):
    """Linear float RGB color chunk."""
    return make_chunk(CHUNK_LINRGBF, struct.pack('<fff', r, g, b))


def make_color_linrgbb(r, g, b):
    """Linear byte RGB color chunk."""
    return make_chunk(CHUNK_LINRGBB, struct.pack('<BBB', r, g, b))


def make_percent_w(val):
    """Integer percentage chunk (0-100 maps to uint16)."""
    return make_chunk(CHUNK_PERCENTW, struct.pack('<H', val))


def make_percent_f(val):
    """Float percentage chunk."""
    return make_chunk(CHUNK_PERCENTF, struct.pack('<f', val))


def make_material(name, diff=(200, 200, 200), spec=(255, 255, 255),
                  amb=(50, 50, 50), shininess=50, transparency=0,
                  shading=2, two_sided=False, texture=None, bumpmap=None):
    """Build a complete material chunk."""
    data = b''
    data += make_chunk(CHUNK_MAT_MATNAME, make_string(name))

    data += make_chunk(CHUNK_MAT_AMBIENT, make_color_rgbb(*amb))
    data += make_chunk(CHUNK_MAT_DIFFUSE, make_color_rgbf(
        diff[0]/255.0, diff[1]/255.0, diff[2]/255.0))
    data += make_chunk(CHUNK_MAT_SPECULAR, make_color_linrgbb(*spec))

    data += make_chunk(CHUNK_MAT_SHININESS, make_percent_w(shininess))
    data += make_chunk(CHUNK_MAT_SHININESS_PERCENT, make_percent_f(0.8))
    data += make_chunk(CHUNK_MAT_SHADING, struct.pack('<H', shading))

    if transparency > 0:
        data += make_chunk(CHUNK_MAT_TRANSPARENCY, make_percent_w(transparency))

    if two_sided:
        data += make_chunk(CHUNK_MAT_TWO_SIDE)

    # Self illumination
    data += make_chunk(CHUNK_MAT_SELF_ILLUM, make_color_rgbb(10, 10, 10))
    data += make_chunk(CHUNK_MAT_SELF_ILPCT, make_percent_w(5))

    if texture:
        tex_data = make_chunk(CHUNK_MAPFILE, make_string(texture))
        tex_data += make_chunk(CHUNK_MAT_MAP_USCALE, struct.pack('<f', 1.0))
        tex_data += make_chunk(CHUNK_MAT_MAP_VSCALE, struct.pack('<f', 1.0))
        tex_data += make_chunk(CHUNK_MAT_MAP_UOFFSET, struct.pack('<f', 0.0))
        tex_data += make_chunk(CHUNK_MAT_MAP_VOFFSET, struct.pack('<f', 0.0))
        tex_data += make_chunk(CHUNK_MAT_MAP_ANG, struct.pack('<f', 0.0))
        tex_data += make_chunk(CHUNK_MAT_MAP_TILING, struct.pack('<H', 0x0002))
        data += make_chunk(CHUNK_MAT_TEXTURE, tex_data)

    if bumpmap:
        bump_data = make_chunk(CHUNK_MAPFILE, make_string(bumpmap))
        bump_data += make_chunk(CHUNK_MAT_MAP_USCALE, struct.pack('<f', 2.0))
        bump_data += make_chunk(CHUNK_MAT_MAP_VSCALE, struct.pack('<f', 2.0))
        data += make_chunk(CHUNK_MAT_BUMPMAP, bump_data)

    return make_chunk(CHUNK_MAT_MATERIAL, data)


def make_trimesh(vertices, faces, uvs=None, smoothing=None, face_mat=None,
                 mat_name=None, transform=None):
    """Build a triangle mesh chunk."""
    data = b''

    # Vertex list
    vert_data = struct.pack('<H', len(vertices))
    for v in vertices:
        vert_data += struct.pack('<fff', *v)
    data += make_chunk(CHUNK_VERTLIST, vert_data)

    # UV map list
    if uvs:
        uv_data = struct.pack('<H', len(uvs))
        for uv in uvs:
            uv_data += struct.pack('<ff', *uv)
        data += make_chunk(CHUNK_MAPLIST, uv_data)

    # Face list
    face_data = struct.pack('<H', len(faces))
    for f in faces:
        # 3 vertex indices + edge visibility flag
        face_data += struct.pack('<HHHH', f[0], f[1], f[2], 0x0007)

    # Face material sub-chunk
    face_sub = b''
    if mat_name and face_mat:
        fmat_data = make_string(mat_name)
        fmat_data += struct.pack('<H', len(face_mat))
        for fi in face_mat:
            fmat_data += struct.pack('<H', fi)
        face_sub += make_chunk(CHUNK_FACEMAT, fmat_data)

    # Smoothing groups sub-chunk
    if smoothing:
        smooth_data = b''
        for sg in smoothing:
            smooth_data += struct.pack('<I', sg)
        face_sub += make_chunk(CHUNK_SMOOLIST, smooth_data)

    data += make_chunk(CHUNK_FACELIST, face_data + face_sub)

    # Transformation matrix
    if transform:
        mat_data = struct.pack('<12f', *transform)
        data += make_chunk(CHUNK_TRMATRIX, mat_data)
    else:
        # Identity matrix
        mat_data = struct.pack('<12f',
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            0.0, 0.0, 0.0)
        data += make_chunk(CHUNK_TRMATRIX, mat_data)

    return make_chunk(CHUNK_TRIMESH, data)


def make_light(name, pos, color=(1.0, 1.0, 1.0), spotlight=None,
               multiplier=1.0, attenuation=0.0):
    """Build a named object block containing a light."""
    light_data = struct.pack('<fff', *pos)
    light_data += make_color_rgbf(*color)

    if spotlight:
        target, hotspot, falloff = spotlight
        spot_data = struct.pack('<fff', *target)
        spot_data += struct.pack('<f', hotspot)
        spot_data += struct.pack('<f', falloff)
        light_data += make_chunk(CHUNK_DL_SPOTLIGHT, spot_data)

    if multiplier != 1.0:
        light_data += make_chunk(CHUNK_DL_MULTIPLIER,
                                 struct.pack('<f', multiplier))

    if attenuation > 0:
        light_data += make_chunk(CHUNK_DL_ATTENUATE,
                                 struct.pack('<f', attenuation))

    obj_data = make_string(name) + make_chunk(CHUNK_LIGHT, light_data)
    return make_chunk(CHUNK_OBJBLOCK, obj_data)


def make_camera(name, pos, target, roll=0.0, fov=45.0,
                near_clip=0.1, far_clip=1000.0):
    """Build a named object block containing a camera."""
    cam_data = struct.pack('<fff', *pos)
    cam_data += struct.pack('<fff', *target)
    cam_data += struct.pack('<f', roll)
    cam_data += struct.pack('<f', fov)

    # Camera ranges sub-chunk
    cam_data += make_chunk(CHUNK_CAM_RANGES,
                           struct.pack('<ff', near_clip, far_clip))

    obj_data = make_string(name) + make_chunk(CHUNK_CAMERA, cam_data)
    return make_chunk(CHUNK_OBJBLOCK, obj_data)


def make_named_mesh(name, trimesh_data):
    """Wrap a trimesh in a named OBJBLOCK."""
    obj_data = make_string(name) + trimesh_data
    return make_chunk(CHUNK_OBJBLOCK, obj_data)


def make_track_pos(keys):
    """Position keyframe track. keys: list of (frame, x, y, z)."""
    data = struct.pack('<HII', 0, 0, len(keys))  # flags(2) + unknown(4) + unknown(4) = 10 bytes total
    for frame, x, y, z in keys:
        data += struct.pack('<I', frame)      # frame index
        data += struct.pack('<H', 0)          # TCB flags (none)
        data += struct.pack('<fff', x, y, z)
    return make_chunk(CHUNK_TRACKPOS, data)


def make_track_rotate(keys):
    """Rotation keyframe track. keys: list of (frame, angle, ax, ay, az)."""
    data = struct.pack('<HII', 0, 0, len(keys))
    for frame, angle, ax, ay, az in keys:
        data += struct.pack('<I', frame)
        data += struct.pack('<H', 0)          # TCB flags
        data += struct.pack('<ffff', angle, ax, ay, az)
    return make_chunk(CHUNK_TRACKROTATE, data)


def make_track_scale(keys):
    """Scaling keyframe track. keys: list of (frame, sx, sy, sz)."""
    # Note: scale track reads numFrames as uint16 + 2 bytes skip
    data = struct.pack('<HHIH', 0, 0, 0, len(keys))  # flags(2) + pad(2) + unknown(4) + numFrames(2)
    data += struct.pack('<H', 0)  # 2 extra bytes that get skipped
    for frame, sx, sy, sz in keys:
        data += struct.pack('<I', frame)
        data += struct.pack('<H', 0)          # TCB flags
        data += struct.pack('<fff', sx, sy, sz)
    return make_chunk(CHUNK_TRACKSCALE, data)


def make_track_roll(keys):
    """Camera roll keyframe track. keys: list of (frame, roll_angle)."""
    data = struct.pack('<HII', 0, 0, len(keys))
    for frame, roll in keys:
        data += struct.pack('<I', frame)
        data += struct.pack('<H', 0)          # TCB flags
        data += struct.pack('<f', roll)
    return make_chunk(CHUNK_TRACKROLL, data)


def make_track_objname(name, hierarchy_pos, flags1=0, flags2=0):
    """Track object name chunk."""
    data = make_string(name)
    data += struct.pack('<HH', flags1, flags2)  # two unknown uint16 values
    data += struct.pack('<H', hierarchy_pos)
    return make_chunk(CHUNK_TRACKOBJNAME, data)


def make_track_pivot(x, y, z):
    """Track pivot chunk."""
    return make_chunk(CHUNK_TRACKPIVOT, struct.pack('<fff', x, y, z))


def make_track_fov():
    """FOV track chunk (triggers the skip/error path)."""
    return make_chunk(CHUNK_TRACKFOV, b'')


def make_trackinfo(name, hierarchy_pos, pos_keys=None, rot_keys=None,
                   scale_keys=None, pivot=None):
    """Build a TRACKINFO chunk for a mesh object."""
    data = make_track_objname(name, hierarchy_pos)

    if pivot:
        data += make_track_pivot(*pivot)

    if pos_keys:
        data += make_track_pos(pos_keys)

    if rot_keys:
        data += make_track_rotate(rot_keys)

    if scale_keys:
        data += make_track_scale(scale_keys)

    return make_chunk(CHUNK_TRACKINFO, data)


def make_trackcamera(name, hierarchy_pos, pos_keys=None, roll_keys=None):
    """Build a TRACKCAMERA chunk."""
    data = make_track_objname(name, hierarchy_pos)

    if pos_keys:
        data += make_track_pos(pos_keys)

    if roll_keys:
        data += make_track_roll(roll_keys)

    # Include FOV track to exercise that code path
    data += make_track_fov()

    return make_chunk(CHUNK_TRACKCAMERA, data)


def make_trackcamtgt(name, hierarchy_pos, pos_keys=None):
    """Build a TRACKCAMTGT chunk."""
    data = make_track_objname(name, hierarchy_pos)
    if pos_keys:
        data += make_track_pos(pos_keys)
    return make_chunk(CHUNK_TRACKCAMTGT, data)


def make_tracklight(name, hierarchy_pos, pos_keys=None):
    """Build a TRACKLIGHT chunk."""
    data = make_track_objname(name, hierarchy_pos)
    if pos_keys:
        data += make_track_pos(pos_keys)
    return make_chunk(CHUNK_TRACKLIGHT, data)


def make_trackligtgt(name, hierarchy_pos, pos_keys=None):
    """Build a TRACKLIGTGT chunk for light target."""
    data = make_track_objname(name, hierarchy_pos)
    if pos_keys:
        data += make_track_pos(pos_keys)
    return make_chunk(CHUNK_TRACKLIGTGT, data)


def generate_full_scene():
    """Generate a complete 3DS scene with mesh, camera, light, and animation."""
    editor_data = b''

    # Version
    editor_data += make_chunk(CHUNK_VERSION, struct.pack('<H', 3))

    # Object mesh section
    objmesh_data = b''

    # Master scale
    objmesh_data += make_chunk(CHUNK_MASTER_SCALE, struct.pack('<f', 1.0))

    # Ambient color
    objmesh_data += make_chunk(CHUNK_AMBCOLOR, make_color_rgbf(0.1, 0.1, 0.1))

    # Background image
    objmesh_data += make_chunk(CHUNK_BIT_MAP, make_string("background.jpg"))
    objmesh_data += make_chunk(CHUNK_BIT_MAP_EXISTS, b'')

    # Material 1: textured with bump map
    objmesh_data += make_material(
        "WoodMat", diff=(180, 120, 60), spec=(200, 200, 200),
        amb=(40, 30, 15), shininess=30, shading=3,
        texture="wood.jpg", bumpmap="wood_bump.jpg")

    # Material 2: semi-transparent, two-sided
    objmesh_data += make_material(
        "GlassMat", diff=(200, 220, 255), spec=(255, 255, 255),
        amb=(20, 22, 25), shininess=90, transparency=50,
        two_sided=True, shading=4)

    # Material 3: basic flat shading
    objmesh_data += make_material(
        "FlatMat", diff=(100, 200, 100), spec=(50, 50, 50),
        amb=(20, 40, 20), shininess=10, shading=1)

    # Mesh 1: Cube (8 verts, 12 faces)
    cube_verts = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1,  1), (1, -1,  1), (1, 1,  1), (-1, 1,  1)
    ]
    cube_faces = [
        (0, 1, 2), (0, 2, 3),  # front
        (4, 6, 5), (4, 7, 6),  # back
        (0, 4, 5), (0, 5, 1),  # bottom
        (2, 6, 7), (2, 7, 3),  # top
        (0, 3, 7), (0, 7, 4),  # left
        (1, 5, 6), (1, 6, 2),  # right
    ]
    cube_uvs = [
        (0, 0), (1, 0), (1, 1), (0, 1),
        (0, 0), (1, 0), (1, 1), (0, 1)
    ]
    cube_smooth = [1, 1, 2, 2, 4, 4, 8, 8, 16, 16, 32, 32]

    cube_mesh = make_trimesh(
        cube_verts, cube_faces, uvs=cube_uvs,
        smoothing=cube_smooth, face_mat=list(range(12)),
        mat_name="WoodMat")
    objmesh_data += make_named_mesh("Cube", cube_mesh)

    # Mesh 2: Triangle with transform
    tri_verts = [(0, 0, 0), (2, 0, 0), (1, 2, 0)]
    tri_faces = [(0, 1, 2)]
    tri_uvs = [(0, 0), (1, 0), (0.5, 1)]
    tri_mesh = make_trimesh(
        tri_verts, tri_faces, uvs=tri_uvs,
        smoothing=[1], face_mat=[0], mat_name="GlassMat",
        transform=[1, 0, 0, 0, 1, 0, 0, 0, 1, 5, 0, 0])
    objmesh_data += make_named_mesh("Triangle", tri_mesh)

    # Spotlight
    objmesh_data += make_light(
        "SpotLight1",
        pos=(0, 0, 10),
        color=(1.0, 0.9, 0.8),
        spotlight=((0, 0, 0), 30.0, 15.0),
        multiplier=2.0,
        attenuation=0.5)

    # Point light (no spotlight sub-chunk)
    objmesh_data += make_light(
        "PointLight1",
        pos=(5, 5, 5),
        color=(0.8, 0.8, 1.0),
        multiplier=1.5)

    # Camera
    objmesh_data += make_camera(
        "Camera1",
        pos=(10, 10, 10),
        target=(0, 0, 0),
        roll=15.0, fov=60.0,
        near_clip=0.1, far_clip=500.0)

    editor_data += make_chunk(CHUNK_OBJMESH, objmesh_data)

    # Keyframer section
    keyframer_data = b''

    # Cube animation: position + rotation + scale
    keyframer_data += make_trackinfo(
        "Cube", hierarchy_pos=0,
        pivot=(0, 0, 0),
        pos_keys=[
            (0, 0.0, 0.0, 0.0),
            (15, 2.0, 0.0, 0.0),
            (30, 0.0, 0.0, 0.0),
        ],
        rot_keys=[
            (0, 0.0, 0.0, 1.0, 0.0),
            (30, 3.14159, 0.0, 1.0, 0.0),
        ],
        scale_keys=[
            (0, 1.0, 1.0, 1.0),
            (15, 1.5, 1.5, 1.5),
            (30, 1.0, 1.0, 1.0),
        ])

    # Triangle animation: just position
    keyframer_data += make_trackinfo(
        "Triangle", hierarchy_pos=0,
        pos_keys=[
            (0, 5.0, 0.0, 0.0),
            (30, 5.0, 3.0, 0.0),
        ])

    # Camera animation: position + roll
    keyframer_data += make_trackcamera(
        "Camera1", hierarchy_pos=0,
        pos_keys=[
            (0, 10.0, 10.0, 10.0),
            (30, 15.0, 10.0, 5.0),
        ],
        roll_keys=[
            (0, 0.0),
            (15, 10.0),
            (30, 0.0),
        ])

    # Camera target animation
    keyframer_data += make_trackcamtgt(
        "Camera1.Target", hierarchy_pos=1,
        pos_keys=[
            (0, 0.0, 0.0, 0.0),
            (30, 2.0, 1.0, 0.0),
        ])

    # Light animation
    keyframer_data += make_tracklight(
        "SpotLight1", hierarchy_pos=0,
        pos_keys=[
            (0, 0.0, 0.0, 10.0),
            (30, 0.0, 0.0, 15.0),
        ])

    # Light target animation
    keyframer_data += make_trackligtgt(
        "SpotLight1.Target", hierarchy_pos=1,
        pos_keys=[
            (0, 0.0, 0.0, 0.0),
            (30, 1.0, 1.0, 0.0),
        ])

    editor_data += make_chunk(CHUNK_KEYFRAMER, keyframer_data)

    # Wrap everything in CHUNK_MAIN
    return make_chunk(CHUNK_MAIN, editor_data)


def generate_dummy_hierarchy():
    """Generate a 3DS file with $$$DUMMY nodes to exercise hierarchy code."""
    editor_data = b''
    editor_data += make_chunk(CHUNK_VERSION, struct.pack('<H', 3))

    objmesh_data = b''
    objmesh_data += make_chunk(CHUNK_MASTER_SCALE, struct.pack('<f', 1.0))

    # Simple material
    objmesh_data += make_material("SimpleMat", diff=(200, 100, 50))

    # Simple mesh
    verts = [(0, 0, 0), (1, 0, 0), (0.5, 1, 0)]
    faces = [(0, 1, 2)]
    mesh = make_trimesh(verts, faces, smoothing=[1],
                        face_mat=[0], mat_name="SimpleMat")
    objmesh_data += make_named_mesh("Mesh1", mesh)

    editor_data += make_chunk(CHUNK_OBJMESH, objmesh_data)

    # Keyframer with dummy node hierarchy
    keyframer_data = b''

    # Root: $$$DUMMY with real name via TRACKDUMMYOBJNAME
    dummy_data = make_track_objname("$$$DUMMY", hierarchy_pos=0)
    dummy_data += make_chunk(CHUNK_TRACKDUMMYOBJNAME,
                             make_string("RealRootName"))
    dummy_data += make_track_pivot(0, 0, 0)
    dummy_data += make_track_pos([(0, 0.0, 0.0, 0.0)])
    keyframer_data += make_chunk(CHUNK_TRACKINFO, dummy_data)

    # Child mesh node
    keyframer_data += make_trackinfo(
        "Mesh1", hierarchy_pos=1,
        pos_keys=[(0, 0.0, 0.0, 0.0), (10, 1.0, 0.0, 0.0)])

    editor_data += make_chunk(CHUNK_KEYFRAMER, keyframer_data)

    return make_chunk(CHUNK_MAIN, editor_data)


def generate_multi_material():
    """Generate a 3DS file with many material types to hit material parsing."""
    editor_data = b''
    editor_data += make_chunk(CHUNK_VERSION, struct.pack('<H', 3))

    objmesh_data = b''
    objmesh_data += make_chunk(CHUNK_MASTER_SCALE, struct.pack('<f', 2.5))

    # Ambient with percent-based color
    objmesh_data += make_chunk(CHUNK_AMBCOLOR, make_color_linrgbf(0.2, 0.2, 0.3))

    # Material with all texture types
    mat_data = b''
    mat_data += make_chunk(CHUNK_MAT_MATNAME, make_string("FullMat"))
    mat_data += make_chunk(CHUNK_MAT_AMBIENT, make_color_linrgbb(30, 30, 30))
    mat_data += make_chunk(CHUNK_MAT_DIFFUSE, make_color_rgbb(200, 180, 160))
    mat_data += make_chunk(CHUNK_MAT_SPECULAR, make_color_rgbf(0.9, 0.9, 0.9))
    mat_data += make_chunk(CHUNK_MAT_SHININESS, make_percent_f(50.0))
    mat_data += make_chunk(CHUNK_MAT_SHININESS_PERCENT, make_percent_w(80))
    mat_data += make_chunk(CHUNK_MAT_TRANSPARENCY, make_percent_w(10))
    mat_data += make_chunk(CHUNK_MAT_SHADING, struct.pack('<H', 3))
    mat_data += make_chunk(CHUNK_MAT_TWO_SIDE)
    mat_data += make_chunk(CHUNK_MAT_SELF_ILPCT, make_percent_w(15))

    # Diffuse texture with tiling
    tex = make_chunk(CHUNK_MAPFILE, make_string("diffuse.png"))
    tex += make_chunk(CHUNK_MAT_MAP_TILING, struct.pack('<H', 0x0010))
    tex += make_chunk(CHUNK_MAT_MAP_USCALE, struct.pack('<f', 2.0))
    tex += make_chunk(CHUNK_MAT_MAP_VSCALE, struct.pack('<f', 2.0))
    tex += make_chunk(CHUNK_MAT_MAP_ANG, struct.pack('<f', 45.0))
    mat_data += make_chunk(CHUNK_MAT_TEXTURE, tex)

    # Opacity map
    opac = make_chunk(CHUNK_MAPFILE, make_string("opacity.png"))
    mat_data += make_chunk(CHUNK_MAT_OPACMAP, opac)

    # Specular map
    spm = make_chunk(CHUNK_MAPFILE, make_string("specular.png"))
    mat_data += make_chunk(CHUNK_MAT_SPECMAP, spm)

    # Bump map
    bmp = make_chunk(CHUNK_MAPFILE, make_string("bump.png"))
    mat_data += make_chunk(CHUNK_MAT_BUMPMAP, bmp)

    # Shininess map
    shm = make_chunk(CHUNK_MAPFILE, make_string("shininess.png"))
    mat_data += make_chunk(CHUNK_MAT_MAT_SHINMAP, shm)

    # Self-illumination map
    sim = make_chunk(CHUNK_MAPFILE, make_string("selfillum.png"))
    mat_data += make_chunk(CHUNK_MAT_SELFIMAP, sim)

    # Reflection map
    rfm = make_chunk(CHUNK_MAPFILE, make_string("reflect.png"))
    mat_data += make_chunk(CHUNK_MAT_REFLMAP, rfm)

    objmesh_data += make_chunk(CHUNK_MAT_MATERIAL, mat_data)

    # Wire material
    objmesh_data += make_material(
        "WireMat", diff=(255, 255, 255), shading=0)

    # Simple mesh
    verts = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)]
    faces = [(0, 1, 2), (0, 2, 3)]
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    mesh = make_trimesh(verts, faces, uvs=uvs,
                        smoothing=[1, 1],
                        face_mat=[0, 1], mat_name="FullMat")
    objmesh_data += make_named_mesh("Quad", mesh)

    editor_data += make_chunk(CHUNK_OBJMESH, objmesh_data)

    return make_chunk(CHUNK_MAIN, editor_data)


def main():
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "test", "models", "3DS", "fuzz_seeds")
    os.makedirs(out_dir, exist_ok=True)

    seeds = {
        "seed_full_scene.3ds": generate_full_scene,
        "seed_dummy_hierarchy.3ds": generate_dummy_hierarchy,
        "seed_multi_material.3ds": generate_multi_material,
    }

    for name, generator in seeds.items():
        path = os.path.join(out_dir, name)
        data = generator()
        with open(path, 'wb') as f:
            f.write(data)
        print(f"Generated {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
