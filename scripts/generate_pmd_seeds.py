#!/usr/bin/env python3
"""Generate minimal valid PMD binary seed files for fuzzing.

PMD format (MikuMikuDance model v1):
- Magic: "Pmd" (3 bytes)
- Version: float (1.0)
- Header: name(20) + comment(256)
- Vertices: count(u32) + vertex_data[]
- Indices: count(u32) + u16[]
- Materials: count(u32) + material_data[]
- Bones: count(u16) + bone_data[]
- IKs: count(u16) + ik_data[]
- Faces: count(u16) + face_data[]
- Face frames: count(u8) + u16[]
- Bone display names: count(u8) + name_data[]
- Bone display: count(u32) + disp_data[]
- English flag: bool
- (if english) english extensions
- Toon textures: 10 * 100 bytes
- Rigid bodies: count(u32) + rigid_body_data[]
- Constraints: count(u32) + constraint_data[]
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test', 'models', 'MMD', 'pmd_seeds')


def pad(s, length):
    """Pad string to fixed length with null bytes."""
    encoded = s.encode('ascii')[:length]
    return encoded + b'\x00' * (length - len(encoded))


def write_header(name, comment):
    """Write PMD file header: magic + version + name(20) + comment(256)."""
    data = b'Pmd'
    data += struct.pack('<f', 1.0)  # version must be 1.0
    data += pad(name, 20)
    data += pad(comment, 256)
    return data


def write_vertex(pos, normal, uv, bone0, bone1, bone_weight, edge_invisible):
    """Write a PmdVertex (38 bytes)."""
    data = struct.pack('<3f', *pos)
    data += struct.pack('<3f', *normal)
    data += struct.pack('<2f', *uv)
    data += struct.pack('<HH', bone0, bone1)
    data += struct.pack('<BB', bone_weight, 1 if edge_invisible else 0)
    return data


def write_material(diffuse, power, specular, ambient, toon_index,
                   edge_flag, index_count, texture_filename):
    """Write a PmdMaterial (70 bytes)."""
    data = struct.pack('<4f', *diffuse)
    data += struct.pack('<f', power)
    data += struct.pack('<3f', *specular)
    data += struct.pack('<3f', *ambient)
    data += struct.pack('<BB', toon_index, edge_flag)
    data += struct.pack('<I', index_count)
    data += pad(texture_filename, 20)
    return data


def write_bone(name, parent_index, tail_index, bone_type,
               ik_parent_index, head_pos):
    """Write a PmdBone (39 bytes)."""
    data = pad(name, 20)
    data += struct.pack('<HH', parent_index, tail_index)
    data += struct.pack('<B', bone_type)
    data += struct.pack('<H', ik_parent_index)
    data += struct.pack('<3f', *head_pos)
    return data


def write_ik(ik_bone_index, target_bone_index, chain_length,
             iterations, angle_limit, child_bones):
    """Write a PmdIk (variable length)."""
    data = struct.pack('<HH', ik_bone_index, target_bone_index)
    data += struct.pack('<B', chain_length)
    data += struct.pack('<H', iterations)
    data += struct.pack('<f', angle_limit)
    for bone_idx in child_bones:
        data += struct.pack('<H', bone_idx)
    return data


def write_face(name, face_type, vertices):
    """Write a PmdFace (variable length).
    face_type: 0=Base, 1=Eyebrow, 2=Eye, 3=Mouth, 4=Other
    vertices: list of (vertex_index, (x, y, z))
    """
    data = pad(name, 20)
    data += struct.pack('<i', len(vertices))  # vertex_count as int
    data += struct.pack('<B', face_type)
    for vidx, pos in vertices:
        data += struct.pack('<i', vidx)  # vertex_index as int
        data += struct.pack('<3f', *pos)
    return data


def write_rigid_body(name, related_bone, group_index, mask,
                     shape_type, size, position, orientation,
                     weight, linear_damping, angular_damping,
                     restitution, friction, rigid_type):
    """Write a PmdRigidBody (83 bytes)."""
    data = pad(name, 20)
    data += struct.pack('<H', related_bone)
    data += struct.pack('<B', group_index)
    data += struct.pack('<H', mask)
    data += struct.pack('<B', shape_type)
    data += struct.pack('<3f', *size)
    data += struct.pack('<3f', *position)
    data += struct.pack('<3f', *orientation)
    data += struct.pack('<f', weight)
    data += struct.pack('<f', linear_damping)
    data += struct.pack('<f', angular_damping)
    data += struct.pack('<f', restitution)
    data += struct.pack('<f', friction)
    data += struct.pack('<B', rigid_type)
    return data


def write_constraint(name, body_a, body_b, position, orientation,
                     lin_lower, lin_upper, ang_lower, ang_upper,
                     lin_stiffness, ang_stiffness):
    """Write a PmdConstraint (124 bytes)."""
    data = pad(name, 20)
    data += struct.pack('<II', body_a, body_b)
    data += struct.pack('<3f', *position)
    data += struct.pack('<3f', *orientation)
    data += struct.pack('<3f', *lin_lower)
    data += struct.pack('<3f', *lin_upper)
    data += struct.pack('<3f', *ang_lower)
    data += struct.pack('<3f', *ang_upper)
    data += struct.pack('<3f', *lin_stiffness)
    data += struct.pack('<3f', *ang_stiffness)
    return data


def write_basic_geometry(num_bones):
    """Write 4 vertices forming a quad, 3 face indices (1 triangle),
    and 1 material referencing those 3 indices."""
    data = b''
    bone1 = min(1, num_bones - 1)

    # 4 vertices
    data += struct.pack('<I', 4)
    data += write_vertex((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0),
                         0, bone1, 100, False)
    data += write_vertex((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0),
                         0, bone1, 80, False)
    data += write_vertex((1.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0),
                         0, bone1, 60, False)
    data += write_vertex((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0),
                         0, bone1, 50, True)

    # 3 face indices (1 triangle)
    data += struct.pack('<I', 3)
    data += struct.pack('<HHH', 0, 1, 2)

    # 1 material covering 3 indices
    data += struct.pack('<I', 1)
    data += write_material(
        diffuse=(0.8, 0.8, 0.8, 1.0),
        power=5.0,
        specular=(1.0, 1.0, 1.0),
        ambient=(0.3, 0.3, 0.3),
        toon_index=0,
        edge_flag=1,
        index_count=3,
        texture_filename="texture.bmp")

    return data


def write_toon_textures():
    """Write 10 toon texture filenames, 100 bytes each."""
    data = b''
    for i in range(10):
        data += pad(f'toon{i + 1:02d}.bmp', 100)
    return data


def make_pmd_basic():
    """Create a basic valid PMD file with minimal data."""
    data = b'Pmd'  # magic
    data += struct.pack('<f', 1.0)  # version

    # Header
    data += pad('test_model', 20)  # name
    data += pad('A test PMD model', 256)  # comment

    # Vertices: 3 vertices
    data += struct.pack('<I', 3)
    for i in range(3):
        x = float(i) * 10.0
        data += struct.pack('<3f', x, 0.0, 0.0)  # position
        data += struct.pack('<3f', 0.0, 1.0, 0.0)  # normal
        data += struct.pack('<2f', float(i) / 2.0, 0.0)  # uv
        data += struct.pack('<2H', 0, 0)  # bone_index
        data += struct.pack('<B', 100)  # bone_weight
        data += struct.pack('<B', 0)  # edge_invisible

    # Indices: 3 (one triangle)
    data += struct.pack('<I', 3)
    data += struct.pack('<3H', 0, 1, 2)

    # Materials: 1
    data += struct.pack('<I', 1)
    data += struct.pack('<4f', 0.8, 0.2, 0.2, 1.0)  # diffuse
    data += struct.pack('<f', 5.0)  # power
    data += struct.pack('<3f', 1.0, 1.0, 1.0)  # specular
    data += struct.pack('<3f', 0.2, 0.2, 0.2)  # ambient
    data += struct.pack('<B', 0)  # toon_index
    data += struct.pack('<B', 1)  # edge_flag
    data += struct.pack('<I', 3)  # index_count
    data += pad('texture.bmp', 20)  # texture_filename

    # Bones: 2
    data += struct.pack('<H', 2)
    for i in range(2):
        data += pad(f'bone{i}', 20)  # name
        data += struct.pack('<H', 0xFFFF if i == 0 else 0)  # parent
        data += struct.pack('<H', 1 if i == 0 else 0xFFFF)  # tail
        data += struct.pack('<B', i)  # bone_type
        data += struct.pack('<H', 0)  # ik_parent
        data += struct.pack('<3f', 0.0, float(i) * 5.0, 0.0)  # position

    # IKs: 0
    data += struct.pack('<H', 0)

    # Faces: 0
    data += struct.pack('<H', 0)

    # Face frames: 0
    data += struct.pack('<B', 0)

    # Bone display names: 0
    data += struct.pack('<B', 0)

    # Bone display: 0
    data += struct.pack('<I', 0)

    # English: 0
    data += struct.pack('<B', 0)

    return data


def make_pmd_full():
    """Create a comprehensive PMD file with all sections populated."""
    data = b'Pmd'
    data += struct.pack('<f', 1.0)

    # Header
    data += pad('full_model', 20)
    data += pad('A comprehensive PMD model for fuzzing', 256)

    # Vertices: 6 (2 triangles)
    num_verts = 6
    data += struct.pack('<I', num_verts)
    for i in range(num_verts):
        x = float(i % 3) * 10.0
        y = float(i // 3) * 10.0
        data += struct.pack('<3f', x, y, 0.0)
        data += struct.pack('<3f', 0.0, 0.0, 1.0)
        data += struct.pack('<2f', float(i) / 5.0, 0.5)
        data += struct.pack('<2H', min(i, 2), min(i + 1, 2))
        data += struct.pack('<B', 50 + i * 10)
        data += struct.pack('<B', i % 2)

    # Indices: 6
    data += struct.pack('<I', 6)
    data += struct.pack('<6H', 0, 1, 2, 3, 4, 5)

    # Materials: 2
    data += struct.pack('<I', 2)
    # Material 0 - with texture
    data += struct.pack('<4f', 1.0, 0.0, 0.0, 1.0)
    data += struct.pack('<f', 10.0)
    data += struct.pack('<3f', 1.0, 1.0, 1.0)
    data += struct.pack('<3f', 0.3, 0.0, 0.0)
    data += struct.pack('<B', 0)
    data += struct.pack('<B', 1)
    data += struct.pack('<I', 3)
    data += pad('tex.bmp*sphere.sph', 20)  # texture with sphere map

    # Material 1 - without sphere
    data += struct.pack('<4f', 0.0, 1.0, 0.0, 1.0)
    data += struct.pack('<f', 20.0)
    data += struct.pack('<3f', 0.5, 0.5, 0.5)
    data += struct.pack('<3f', 0.1, 0.3, 0.1)
    data += struct.pack('<B', 1)
    data += struct.pack('<B', 0)
    data += struct.pack('<I', 3)
    data += pad('material2.png', 20)

    # Bones: 3
    num_bones = 3
    data += struct.pack('<H', num_bones)
    # Root bone
    data += pad('center', 20)
    data += struct.pack('<H', 0xFFFF)  # no parent
    data += struct.pack('<H', 1)  # tail
    data += struct.pack('<B', 1)  # RotationAndMove
    data += struct.pack('<H', 0)
    data += struct.pack('<3f', 0.0, 0.0, 0.0)
    # Bone 1
    data += pad('upper_body', 20)
    data += struct.pack('<H', 0)
    data += struct.pack('<H', 2)
    data += struct.pack('<B', 0)  # Rotation
    data += struct.pack('<H', 0)
    data += struct.pack('<3f', 0.0, 5.0, 0.0)
    # Bone 2
    data += pad('head', 20)
    data += struct.pack('<H', 1)
    data += struct.pack('<H', 0xFFFF)
    data += struct.pack('<B', 0)
    data += struct.pack('<H', 0)
    data += struct.pack('<3f', 0.0, 10.0, 0.0)

    # IKs: 1
    data += struct.pack('<H', 1)
    data += struct.pack('<H', 2)  # ik_bone_index
    data += struct.pack('<H', 1)  # target_bone_index
    data += struct.pack('<B', 2)  # chain_length
    data += struct.pack('<H', 20)  # iterations
    data += struct.pack('<f', 0.5)  # angle_limit
    data += struct.pack('<2H', 0, 1)  # chain bone indices

    # Faces: 2
    num_faces = 2
    data += struct.pack('<H', num_faces)
    # Base face
    data += pad('base', 20)
    data += struct.pack('<i', 3)  # vertex_count
    data += struct.pack('<B', 0)  # type: Base
    for i in range(3):
        data += struct.pack('<i', i)  # vertex_index
        data += struct.pack('<3f', float(i), 0.0, 0.0)
    # Smile face
    data += pad('smile', 20)
    data += struct.pack('<i', 2)
    data += struct.pack('<B', 3)  # type: Mouth
    for i in range(2):
        data += struct.pack('<i', i)
        data += struct.pack('<3f', 0.1, 0.2, 0.0)

    # Face frames: 1
    data += struct.pack('<B', 1)
    data += struct.pack('<H', 1)

    # Bone display names: 2
    num_bone_disp = 2
    data += struct.pack('<B', num_bone_disp)
    data += pad('body', 50)
    data += pad('head', 50)

    # Bone display: 2
    data += struct.pack('<I', 2)
    data += struct.pack('<H', 1)  # bone_index
    data += struct.pack('<B', 1)  # bone_disp_index
    data += struct.pack('<H', 2)
    data += struct.pack('<B', 2)

    # English: 1
    data += struct.pack('<B', 1)
    # English header extension
    data += pad('full_model_en', 20)
    data += pad('English comment', 256)
    # English bone names
    for i in range(num_bones):
        data += pad(f'bone{i}_en', 20)
    # English face names (skip Base type)
    data += pad('smile_en', 20)
    # English bone display names
    for i in range(num_bone_disp):
        data += pad(f'disp{i}_en', 50)

    # Toon textures: 10
    for i in range(10):
        data += pad(f'toon{i:02d}.bmp', 100)

    # Rigid bodies: 1
    data += struct.pack('<I', 1)
    data += pad('rigid0', 20)  # name
    data += struct.pack('<H', 0)  # related_bone_index
    data += struct.pack('<B', 0)  # group_index
    data += struct.pack('<H', 0xFFFF)  # mask
    data += struct.pack('<B', 0)  # shape: Sphere
    data += struct.pack('<3f', 1.0, 1.0, 1.0)  # size
    data += struct.pack('<3f', 0.0, 5.0, 0.0)  # position
    data += struct.pack('<3f', 0.0, 0.0, 0.0)  # orientation
    data += struct.pack('<f', 1.0)  # weight
    data += struct.pack('<f', 0.5)  # linear_damping
    data += struct.pack('<f', 0.5)  # angular_damping
    data += struct.pack('<f', 0.0)  # restitution
    data += struct.pack('<f', 0.5)  # friction
    data += struct.pack('<B', 0)  # rigid_type: BoneConnected

    # Constraints: 1
    data += struct.pack('<I', 1)
    data += pad('constraint0', 20)  # name
    data += struct.pack('<I', 0)  # rigid_body_index_a
    data += struct.pack('<I', 0)  # rigid_body_index_b
    data += struct.pack('<3f', 0.0, 0.0, 0.0)  # position
    data += struct.pack('<3f', 0.0, 0.0, 0.0)  # orientation
    data += struct.pack('<3f', -1.0, -1.0, -1.0)  # linear_lower_limit
    data += struct.pack('<3f', 1.0, 1.0, 1.0)  # linear_upper_limit
    data += struct.pack('<3f', -0.5, -0.5, -0.5)  # angular_lower_limit
    data += struct.pack('<3f', 0.5, 0.5, 0.5)  # angular_upper_limit
    data += struct.pack('<3f', 1.0, 1.0, 1.0)  # linear_stiffness
    data += struct.pack('<3f', 1.0, 1.0, 1.0)  # angular_stiffness

    return data


def make_pmd_physics():
    """Create PMD with physics: 3 rigid bodies (sphere/box/capsule),
    2 constraints, IK chain with chain_length=3, 1 base face."""
    data = write_header("physics_model", "PMD model with physics")

    # 4 vertices, 3 indices, 1 material
    data += write_basic_geometry(num_bones=3)

    # 3 bones in a hierarchy: root -> spine -> head
    data += struct.pack('<H', 3)
    data += write_bone("root", 0xFFFF, 1, 0, 0, (0.0, 0.0, 0.0))
    data += write_bone("spine", 0, 2, 0, 0, (0.0, 3.0, 0.0))
    # head: IkEffector type (2)
    data += write_bone("head", 1, 0xFFFF, 2, 0, (0.0, 6.0, 0.0))

    # 1 IK entry with chain_length=3
    data += struct.pack('<H', 1)
    data += write_ik(
        ik_bone_index=2,
        target_bone_index=0,
        chain_length=3,
        iterations=20,
        angle_limit=0.5,
        child_bones=[0, 1, 2])

    # 1 face (base type) with 2 face vertices
    data += struct.pack('<H', 1)
    data += write_face("base", 0, [
        (0, (0.0, 0.0, 0.0)),
        (1, (0.1, 0.0, 0.0)),
    ])

    # face display: 1 entry
    data += struct.pack('<B', 1)
    data += struct.pack('<H', 0)

    # bone display names: 1
    data += struct.pack('<B', 1)
    data += pad("body", 50)

    # bone display: 1 entry
    data += struct.pack('<I', 1)
    data += struct.pack('<HB', 0, 1)

    # english flag = 0
    data += struct.pack('<B', 0)

    # toon textures
    data += write_toon_textures()

    # 3 rigid bodies: sphere, box, capsule
    data += struct.pack('<I', 3)
    data += write_rigid_body(
        name="rb_sphere",
        related_bone=0,
        group_index=0,
        mask=0xFFFF,
        shape_type=0,  # Sphere
        size=(0.5, 0.0, 0.0),
        position=(0.0, 0.0, 0.0),
        orientation=(0.0, 0.0, 0.0),
        weight=1.0,
        linear_damping=0.5,
        angular_damping=0.5,
        restitution=0.0,
        friction=0.5,
        rigid_type=0)  # BoneConnected
    data += write_rigid_body(
        name="rb_box",
        related_bone=1,
        group_index=1,
        mask=0xFFFE,
        shape_type=1,  # Box
        size=(0.5, 1.0, 0.5),
        position=(0.0, 3.0, 0.0),
        orientation=(0.0, 0.0, 0.0),
        weight=2.0,
        linear_damping=0.3,
        angular_damping=0.3,
        restitution=0.1,
        friction=0.8,
        rigid_type=1)  # Physics
    data += write_rigid_body(
        name="rb_capsule",
        related_bone=2,
        group_index=2,
        mask=0xFFFC,
        shape_type=2,  # Capsule
        size=(0.3, 0.8, 0.0),
        position=(0.0, 6.0, 0.0),
        orientation=(0.1, 0.0, 0.0),
        weight=0.5,
        linear_damping=0.4,
        angular_damping=0.4,
        restitution=0.05,
        friction=0.6,
        rigid_type=2)  # ConnectedPhysics

    # 2 constraints
    data += struct.pack('<I', 2)
    data += write_constraint(
        name="joint_root_spine",
        body_a=0, body_b=1,
        position=(0.0, 1.5, 0.0),
        orientation=(0.0, 0.0, 0.0),
        lin_lower=(-0.1, -0.1, -0.1),
        lin_upper=(0.1, 0.1, 0.1),
        ang_lower=(-0.5, -0.5, -0.5),
        ang_upper=(0.5, 0.5, 0.5),
        lin_stiffness=(1.0, 1.0, 1.0),
        ang_stiffness=(1.0, 1.0, 1.0))
    data += write_constraint(
        name="joint_spine_head",
        body_a=1, body_b=2,
        position=(0.0, 4.5, 0.0),
        orientation=(0.0, 0.0, 0.0),
        lin_lower=(-0.05, -0.05, -0.05),
        lin_upper=(0.05, 0.05, 0.05),
        ang_lower=(-0.3, -0.3, -0.3),
        ang_upper=(0.3, 0.3, 0.3),
        lin_stiffness=(2.0, 2.0, 2.0),
        ang_stiffness=(2.0, 2.0, 2.0))

    return data


def make_pmd_english():
    """Create PMD with english extension, toon textures, no physics.
    2 bones, 2 faces (base + eyebrow), english_flag=1."""
    num_bones = 2
    num_bone_disp_names = 1

    data = write_header("english_model", "PMD with english extension")

    # 4 vertices, 3 indices, 1 material
    data += write_basic_geometry(num_bones=num_bones)

    # 2 bones
    data += struct.pack('<H', num_bones)
    data += write_bone("center", 0xFFFF, 1, 0, 0, (0.0, 0.0, 0.0))
    data += write_bone("arm", 0, 0xFFFF, 1, 0, (1.0, 0.0, 0.0))

    # 0 IK entries
    data += struct.pack('<H', 0)

    # 2 faces: base + eyebrow
    data += struct.pack('<H', 2)
    data += write_face("base", 0, [  # Base type (skipped by english reader)
        (0, (0.0, 0.0, 0.0)),
        (1, (1.0, 0.0, 0.0)),
    ])
    data += write_face("eyebrow_up", 1, [  # Eyebrow type
        (0, (0.0, 0.1, 0.0)),
    ])

    # face display: 1 entry (the eyebrow face)
    data += struct.pack('<B', 1)
    data += struct.pack('<H', 1)

    # bone display names: 1
    data += struct.pack('<B', num_bone_disp_names)
    data += pad("arms", 50)

    # bone display: 1 entry
    data += struct.pack('<I', 1)
    data += struct.pack('<HB', 1, 1)

    # english flag = 1
    data += struct.pack('<B', 1)

    # english header: name(20) + comment(256)
    data += pad("english_model_en", 20)
    data += pad("English comment for model", 256)

    # english bone names: bone_count x 20 bytes
    data += pad("center_en", 20)
    data += pad("arm_en", 20)

    # english face names: skip Base faces, read for non-Base faces
    # face[0]=Base (skipped), face[1]=Eyebrow (read)
    data += pad("eyebrow_up_en", 20)

    # english bone display names: bone_disp_name_count x 50 bytes
    data += pad("arms_en", 50)

    # toon textures
    data += write_toon_textures()

    # 0 rigid bodies, 0 constraints
    data += struct.pack('<I', 0)
    data += struct.pack('<I', 0)

    return data


def make_pmd_ik_faces():
    """Create PMD with 2 IK entries (chain_length 1 and 4),
    all 5 face types: Base, Eyebrow, Eye, Mouth, Other.
    4 bones, 0 rigid bodies, 0 constraints."""
    data = write_header("ik_faces_model", "PMD with IK and face types")

    # 4 vertices, 3 indices, 1 material
    data += write_basic_geometry(num_bones=4)

    # 4 bones
    data += struct.pack('<H', 4)
    data += write_bone("root", 0xFFFF, 1, 0, 0, (0.0, 0.0, 0.0))
    # spine: IkEffectable type (4)
    data += write_bone("spine", 0, 2, 4, 0, (0.0, 3.0, 0.0))
    # left_leg: IkEffector type (2)
    data += write_bone("left_leg", 1, 3, 2, 0, (0.0, 6.0, 0.0))
    # right_leg: IkTarget type (6)
    data += write_bone("right_leg", 1, 0xFFFF, 6, 2, (-1.0, 6.0, 0.0))

    # 2 IK entries
    data += struct.pack('<H', 2)
    # IK 1: chain_length=1
    data += write_ik(
        ik_bone_index=2,
        target_bone_index=0,
        chain_length=1,
        iterations=10,
        angle_limit=0.3,
        child_bones=[1])
    # IK 2: chain_length=4
    data += write_ik(
        ik_bone_index=3,
        target_bone_index=0,
        chain_length=4,
        iterations=40,
        angle_limit=1.0,
        child_bones=[0, 1, 2, 3])

    # 5 faces: all types (Base=0, Eyebrow=1, Eye=2, Mouth=3, Other=4)
    data += struct.pack('<H', 5)
    data += write_face("base", 0, [
        (0, (0.0, 0.0, 0.0)),
        (1, (1.0, 0.0, 0.0)),
        (2, (1.0, 1.0, 0.0)),
    ])
    data += write_face("brow_raise", 1, [
        (0, (0.0, 0.2, 0.0)),
    ])
    data += write_face("eye_close", 2, [
        (1, (0.0, -0.1, 0.0)),
    ])
    data += write_face("mouth_open", 3, [
        (2, (0.0, -0.3, 0.0)),
        (3, (0.0, -0.2, 0.0)),
    ])
    data += write_face("other_expr", 4, [
        (0, (0.05, 0.05, 0.0)),
    ])

    # face display: 4 entries (non-base faces)
    data += struct.pack('<B', 4)
    data += struct.pack('<HHHH', 1, 2, 3, 4)

    # bone display names: 2
    data += struct.pack('<B', 2)
    data += pad("body", 50)
    data += pad("legs", 50)

    # bone display: 2 entries
    data += struct.pack('<I', 2)
    data += struct.pack('<HB', 0, 1)  # root -> body
    data += struct.pack('<HB', 2, 2)  # left_leg -> legs

    # english flag = 0
    data += struct.pack('<B', 0)

    # toon textures
    data += write_toon_textures()

    # 0 rigid bodies, 0 constraints
    data += struct.pack('<I', 0)
    data += struct.pack('<I', 0)

    return data


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seeds = [
        ('seed_basic.pmd', make_pmd_basic),
        ('seed_full.pmd', make_pmd_full),
        ('seed_physics.pmd', make_pmd_physics),
        ('seed_english.pmd', make_pmd_english),
        ('seed_ik_faces.pmd', make_pmd_ik_faces),
    ]

    for filename, generator in seeds:
        data = generator()
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, 'wb') as f:
            f.write(data)
        print(f"Written {path} ({len(data)} bytes)")


if __name__ == '__main__':
    main()
