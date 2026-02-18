#!/usr/bin/env python3
"""
Generate additional fuzz seed files for SMD, ASE, and MDL importers.

Targets code paths that are likely uncovered by existing seed files,
focusing on:
  SMD: Deep bone hierarchies, weight normalization edge cases,
       skeleton-only (SkeletonMeshBuilder), multi-material triangles,
       multi-frame animations with many bones, VTA vertex animation.
  ASE: Scale animation (CONTROL_SCALE_*), mesh weights (MESH_WEIGHTS),
       mapping channels, complete normals, vertex color faces, mesh
       animation keyword, helper objects, wire/flat shading, non-bitmap
       map classes, inherit flags, target animation for cameras/lights.
  MDL: Quake1 with group skins and group frames, 3DGS MDL3 (8-bit verts),
       3DGS MDL4 (16-bit verts), 3DGS MDL5, MDL7 with bones/groups/
       deformers/materials, Half-Life 1 with proper header/bones/
       bodyparts/textures/sequences.
"""

import os
import struct
import sys


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_text(path, content):
    with open(path, "w", newline="\n") as f:
        f.write(content)
    print(f"  wrote {path} ({os.path.getsize(path)} bytes)")


def write_bin(path, data):
    with open(path, "wb") as f:
        f.write(data)
    print(f"  wrote {path} ({os.path.getsize(path)} bytes)")


# ---------------------------------------------------------------------------
# SMD seed generation
# ---------------------------------------------------------------------------

def generate_smd_seeds(out_dir):
    ensure_dir(out_dir)
    print(f"Generating SMD seeds in {out_dir}")

    # 1. seed_smd_skeleton.smd
    #    A reference SMD with a deep skeleton hierarchy (7 bones),
    #    multiple triangles using different materials, and vertices
    #    with multi-bone weights. Exercises bone hierarchy construction,
    #    weight normalization, and multi-material mesh creation.
    write_text(os.path.join(out_dir, "seed_smd_skeleton.smd"), """\
version 1
nodes
0 "root" -1
1 "pelvis" 0
2 "spine1" 1
3 "spine2" 2
4 "neck" 3
5 "left_arm" 3
6 "right_arm" 3
end
skeleton
time 0
0 0.0 0.0 0.0 0.0 0.0 0.0
1 0.0 0.0 1.0 0.0 0.0 0.0
2 0.0 0.0 2.0 0.1 0.0 0.0
3 0.0 0.0 3.0 0.0 0.1 0.0
4 0.0 0.0 4.0 0.0 0.0 0.1
5 -1.0 0.0 3.5 0.0 0.0 -0.3
6 1.0 0.0 3.5 0.0 0.0 0.3
end
triangles
torso_skin
0 0.0 0.0 1.0 0.0 1.0 0.0 0.0 0.0 3 1 0.4 2 0.3 3 0.2
0 1.0 0.0 1.0 0.0 1.0 0.0 1.0 0.0 4 1 0.3 2 0.2 3 0.15 4 0.1
0 0.5 1.0 1.5 0.0 1.0 0.0 0.5 1.0 3 2 0.35 3 0.35 4 0.15
torso_skin
1 0.0 0.0 2.5 0.0 1.0 0.0 0.0 0.5 4 2 0.2 3 0.25 4 0.15 5 0.1
1 1.0 0.0 2.5 0.0 1.0 0.0 1.0 0.5 3 3 0.3 4 0.3 6 0.1
1 0.5 1.0 3.0 0.0 1.0 0.0 0.5 1.0 4 3 0.2 4 0.2 5 0.15 6 0.15
arm_skin
5 -1.0 0.0 3.5 -1.0 0.0 0.0 0.0 0.0 2 3 0.4 5 0.5
5 -2.0 0.0 3.5 -1.0 0.0 0.0 1.0 0.0 2 3 0.3 5 0.6
5 -1.5 0.5 3.5 -1.0 0.0 0.0 0.5 1.0 2 3 0.35 5 0.55
arm_skin
6 1.0 0.0 3.5 1.0 0.0 0.0 0.0 0.0 2 3 0.4 6 0.5
6 2.0 0.0 3.5 1.0 0.0 0.0 1.0 0.0 2 3 0.3 6 0.6
6 1.5 0.5 3.5 1.0 0.0 0.0 0.5 1.0 2 3 0.35 6 0.55
end
""")

    # 2. seed_smd_animation.smd
    #    Animation-only SMD (no triangles) with many time frames
    #    and multiple bones. This triggers the AI_SCENE_FLAGS_INCOMPLETE
    #    path and SkeletonMeshBuilder. Also exercises FixTimeValues
    #    with negative time offsets and large time ranges.
    lines = ["version 1", "nodes"]
    num_bones = 8
    for i in range(num_bones):
        parent = i - 1 if i > 0 else -1
        lines.append(f'{i} "bone_{i}" {parent}')
    lines.append("end")
    lines.append("skeleton")
    num_frames = 12
    for t in range(num_frames):
        lines.append(f"time {t}")
        for b in range(num_bones):
            px = b * 0.5
            py = 0.0
            pz = b * 1.0
            rx = 0.1 * t * (b + 1) * 0.1
            ry = 0.05 * t * (b + 1) * 0.1
            rz = 0.02 * t * (b + 1) * 0.1
            lines.append(f"{b} {px:.4f} {py:.4f} {pz:.4f} {rx:.4f} {ry:.4f} {rz:.4f}")
    lines.append("end")
    lines.append("")
    write_text(os.path.join(out_dir, "seed_smd_animation.smd"), "\n".join(lines))

    # 3. seed_smd_vertexanim.smd (VTA-style vertex animation in .smd)
    #    Uses vertexanimation section with multiple time frames.
    #    The configFrameID defaults to 0, so "time 0" data is used.
    #    Vertices in vertexanimation don't have UV coords.
    #    This exercises the ParseVASection code path with proper
    #    triangle grouping (groups of 3 vertices).
    write_text(os.path.join(out_dir, "seed_smd_vertexanim.smd"), """\
version 1
nodes
0 "root" -1
1 "jaw" 0
2 "brow" 0
end
skeleton
time 0
0 0.0 0.0 0.0 0.0 0.0 0.0
1 0.0 -0.5 0.5 0.0 0.0 0.0
2 0.0 0.5 1.0 0.0 0.0 0.0
end
vertexanimation
time 0
0 0.0 0.0 0.0 0.0 0.0 1.0
0 1.0 0.0 0.0 0.0 0.0 1.0
0 0.5 1.0 0.0 0.0 0.0 1.0
1 0.0 -0.5 0.5 0.0 -1.0 0.0
1 0.5 -0.5 0.5 0.0 -1.0 0.0
1 0.25 0.0 0.5 0.0 -1.0 0.0
2 -0.5 0.5 1.0 0.0 1.0 0.0
2 0.5 0.5 1.0 0.0 1.0 0.0
2 0.0 1.0 1.0 0.0 1.0 0.0
end
triangles
face_mat
0 0.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0
0 1.0 0.0 0.0 0.0 0.0 1.0 1.0 0.0
0 0.5 1.0 0.0 0.0 0.0 1.0 0.5 1.0
jaw_mat
1 0.0 -0.5 0.5 0.0 -1.0 0.0 0.0 0.0
1 0.5 -0.5 0.5 0.0 -1.0 0.0 1.0 0.0
1 0.25 0.0 0.5 0.0 -1.0 0.0 0.5 1.0
brow_mat
2 -0.5 0.5 1.0 0.0 1.0 0.0 0.0 0.0
2 0.5 0.5 1.0 0.0 1.0 0.0 1.0 0.0
2 0.0 1.0 1.0 0.0 1.0 0.0 0.5 1.0
end
""")

    # 4. seed_smd_weight_edge.smd
    #    Tests weight normalization edge cases:
    #    - Vertex with no bone links (weight goes to parent)
    #    - Vertex with partial weights (remainder to parent)
    #    - Vertex with weight sum > 0.975 (no parent assignment)
    #    - Vertex with invalid parent (UINT_MAX via -1 parent bone)
    write_text(os.path.join(out_dir, "seed_smd_weight_edge.smd"), """\
version 1
nodes
0 "root" -1
1 "bone_a" 0
2 "bone_b" 1
end
skeleton
time 0
0 0.0 0.0 0.0 0.0 0.0 0.0
1 1.0 0.0 0.0 0.0 0.0 0.0
2 2.0 0.0 0.0 0.0 0.0 0.0
end
triangles
mat
0 0.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0
0 1.0 0.0 0.0 0.0 0.0 1.0 1.0 0.0 0
0 0.5 1.0 0.0 0.0 0.0 1.0 0.5 1.0 0
mat
1 0.0 0.0 1.0 0.0 1.0 0.0 0.0 0.0 1 2 0.3
1 1.0 0.0 1.0 0.0 1.0 0.0 1.0 0.0 2 1 0.5 2 0.49
1 0.5 1.0 1.0 0.0 1.0 0.0 0.5 1.0 2 0 0.3 1 0.3 2 0.38
end
""")

    # 5. seed_smd_skeleton_only.smd
    #    Pure animation SMD with branching hierarchy and negative time
    #    values. Tests iSmallestFrame adjustment and FixTimeValues with
    #    negative frame numbers. No triangles => skeleton mesh builder.
    write_text(os.path.join(out_dir, "seed_smd_skeleton_only.smd"), """\
version 1
nodes
0 "root" -1
1 "child_a" 0
2 "child_b" 0
3 "grandchild_a1" 1
4 "grandchild_a2" 1
5 "grandchild_b1" 2
end
skeleton
time -5
0 0.0 0.0 0.0 0.0 0.0 0.0
1 1.0 0.0 0.0 0.0 0.0 0.0
2 -1.0 0.0 0.0 0.0 0.0 0.0
3 2.0 0.0 0.0 0.0 0.0 0.0
4 1.0 1.0 0.0 0.0 0.0 0.0
5 -2.0 0.0 0.0 0.0 0.0 0.0
time -2
0 0.0 0.0 0.0 0.0 0.0 0.0
1 1.0 0.5 0.0 0.1 0.0 0.0
2 -1.0 0.5 0.0 -0.1 0.0 0.0
3 2.0 0.3 0.0 0.2 0.0 0.0
4 1.0 1.3 0.0 0.15 0.0 0.0
5 -2.0 0.3 0.0 -0.2 0.0 0.0
time 0
0 0.0 0.0 0.0 0.0 0.0 0.0
1 1.0 1.0 0.0 0.2 0.0 0.0
2 -1.0 1.0 0.0 -0.2 0.0 0.0
3 2.0 0.5 0.0 0.3 0.0 0.0
4 1.0 1.5 0.0 0.25 0.0 0.0
5 -2.0 0.5 0.0 -0.3 0.0 0.0
time 5
0 0.0 0.0 0.0 0.0 0.0 0.0
1 1.0 0.0 0.0 0.0 0.0 0.0
2 -1.0 0.0 0.0 0.0 0.0 0.0
3 2.0 0.0 0.0 0.0 0.0 0.0
4 1.0 1.0 0.0 0.0 0.0 0.0
5 -2.0 0.0 0.0 0.0 0.0 0.0
end
""")


# ---------------------------------------------------------------------------
# ASE seed generation
# ---------------------------------------------------------------------------

def generate_ase_seeds(out_dir):
    ensure_dir(out_dir)
    print(f"Generating ASE seeds in {out_dir}")

    # 1. seed_ase_full.ase
    #    Comprehensive ASE file with *SCENE, *MATERIAL_LIST with
    #    submaterials and texture maps (diffuse, ambient, specular,
    #    bump, opacity, emissive, shininess), *GEOMOBJECT with full
    #    *MESH including vertices, faces, normals, texture coords,
    #    texture faces, vertex colors, color faces, and *MESH_ANIMATION.
    #    Also exercises *MESH_WEIGHTS with bone vertices.
    write_text(os.path.join(out_dir, "seed_ase_full.ase"), """\
*3DSMAX_ASCIIEXPORT 200
*COMMENT "Full ASE seed with all major features"
*SCENE {
\t*SCENE_FILENAME "test.max"
\t*SCENE_FIRSTFRAME 0
\t*SCENE_LASTFRAME 30
\t*SCENE_FRAMESPEED 30
\t*SCENE_TICKSPERFRAME 160
\t*SCENE_BACKGROUND_STATIC 0.2 0.3 0.4
\t*SCENE_AMBIENT_STATIC 0.1 0.1 0.1
}
*MATERIAL_LIST {
\t*MATERIAL_COUNT 1
\t*MATERIAL 0 {
\t\t*MATERIAL_NAME "FullMat"
\t\t*MATERIAL_CLASS "Standard"
\t\t*MATERIAL_AMBIENT 0.1 0.1 0.1
\t\t*MATERIAL_DIFFUSE 0.8 0.7 0.6
\t\t*MATERIAL_SPECULAR 1.0 1.0 1.0
\t\t*MATERIAL_SHINE 0.5
\t\t*MATERIAL_SHINESTRENGTH 0.8
\t\t*MATERIAL_TRANSPARENCY 0.1
\t\t*MATERIAL_SELFILLUM 0.2
\t\t*MATERIAL_TWOSIDED
\t\t*MATERIAL_SHADING Phong
\t\t*NUMSUBMTLS 2
\t\t*SUBMATERIAL 0 {
\t\t\t*MATERIAL_NAME "SubMat0"
\t\t\t*MATERIAL_AMBIENT 0.2 0.2 0.2
\t\t\t*MATERIAL_DIFFUSE 0.9 0.1 0.1
\t\t\t*MATERIAL_SPECULAR 1.0 1.0 1.0
\t\t\t*MATERIAL_SHINE 0.3
\t\t\t*MATERIAL_SHADING Blinn
\t\t\t*MAP_DIFFUSE {
\t\t\t\t*MAP_NAME "Diffuse0"
\t\t\t\t*MAP_CLASS "Bitmap"
\t\t\t\t*BITMAP "textures/diffuse0.bmp"
\t\t\t\t*MAP_AMOUNT 1.0
\t\t\t\t*UVW_U_OFFSET 0.0
\t\t\t\t*UVW_V_OFFSET 0.0
\t\t\t\t*UVW_U_TILING 1.0
\t\t\t\t*UVW_V_TILING 1.0
\t\t\t\t*UVW_ANGLE 0.0
\t\t\t}
\t\t\t*MAP_BUMP {
\t\t\t\t*MAP_NAME "Bump0"
\t\t\t\t*MAP_CLASS "Normal Bump"
\t\t\t\t*BITMAP "textures/normal0.tga"
\t\t\t\t*MAP_AMOUNT 0.5
\t\t\t}
\t\t}
\t\t*SUBMATERIAL 1 {
\t\t\t*MATERIAL_NAME "SubMat1"
\t\t\t*MATERIAL_AMBIENT 0.1 0.1 0.1
\t\t\t*MATERIAL_DIFFUSE 0.1 0.9 0.1
\t\t\t*MATERIAL_SPECULAR 0.5 0.5 0.5
\t\t\t*MATERIAL_SHINE 0.7
\t\t\t*MATERIAL_SHADING Flat
\t\t\t*MAP_AMBIENT {
\t\t\t\t*MAP_NAME "Ambient1"
\t\t\t\t*MAP_CLASS "Bitmap"
\t\t\t\t*BITMAP "textures/ambient1.bmp"
\t\t\t\t*MAP_AMOUNT 0.3
\t\t\t}
\t\t\t*MAP_SPECULAR {
\t\t\t\t*MAP_NAME "Spec1"
\t\t\t\t*MAP_CLASS "Bitmap"
\t\t\t\t*BITMAP "textures/spec1.bmp"
\t\t\t\t*MAP_AMOUNT 0.7
\t\t\t}
\t\t\t*MAP_OPACITY {
\t\t\t\t*MAP_NAME "Opacity1"
\t\t\t\t*MAP_CLASS "Bitmap"
\t\t\t\t*BITMAP "textures/opacity1.bmp"
\t\t\t\t*MAP_AMOUNT 1.0
\t\t\t}
\t\t\t*MAP_SELFILLUM {
\t\t\t\t*MAP_NAME "Emit1"
\t\t\t\t*MAP_CLASS "Bitmap"
\t\t\t\t*BITMAP "textures/emissive1.bmp"
\t\t\t\t*MAP_AMOUNT 0.5
\t\t\t}
\t\t\t*MAP_SHINESTRENGTH {
\t\t\t\t*MAP_NAME "Gloss1"
\t\t\t\t*MAP_CLASS "Bitmap"
\t\t\t\t*BITMAP "textures/gloss1.bmp"
\t\t\t\t*MAP_AMOUNT 0.6
\t\t\t}
\t\t}
\t}
}
*GEOMOBJECT {
\t*NODE_NAME "FullMesh"
\t*NODE_TM {
\t\t*NODE_NAME "FullMesh"
\t\t*INHERIT_POS 0 0 0
\t\t*INHERIT_ROT 0 0 0
\t\t*INHERIT_SCL 0 0 0
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 0.0 0.0 0.0
\t}
\t*MESH {
\t\t*MESH_NUMVERTEX 8
\t\t*MESH_NUMFACES 6
\t\t*MESH_VERTEX_LIST {
\t\t\t*MESH_VERTEX 0 0.0 0.0 0.0
\t\t\t*MESH_VERTEX 1 1.0 0.0 0.0
\t\t\t*MESH_VERTEX 2 1.0 1.0 0.0
\t\t\t*MESH_VERTEX 3 0.0 1.0 0.0
\t\t\t*MESH_VERTEX 4 0.0 0.0 1.0
\t\t\t*MESH_VERTEX 5 1.0 0.0 1.0
\t\t\t*MESH_VERTEX 6 1.0 1.0 1.0
\t\t\t*MESH_VERTEX 7 0.0 1.0 1.0
\t\t}
\t\t*MESH_FACE_LIST {
\t\t\t*MESH_FACE 0: A: 0 B: 1 C: 2 *MESH_SMOOTHING 1 *MESH_MTLID 0
\t\t\t*MESH_FACE 1: A: 0 B: 2 C: 3 *MESH_SMOOTHING 1 *MESH_MTLID 0
\t\t\t*MESH_FACE 2: A: 4 B: 5 C: 6 *MESH_SMOOTHING 2 *MESH_MTLID 1
\t\t\t*MESH_FACE 3: A: 4 B: 6 C: 7 *MESH_SMOOTHING 2 *MESH_MTLID 1
\t\t\t*MESH_FACE 4: A: 0 B: 4 C: 5 *MESH_SMOOTHING 3 *MESH_MTLID 0
\t\t\t*MESH_FACE 5: A: 0 B: 5 C: 1 *MESH_SMOOTHING 3 *MESH_MTLID 1
\t\t}
\t\t*MESH_NUMTVERTEX 8
\t\t*MESH_TVERTLIST {
\t\t\t*MESH_TVERT 0 0.0 0.0 0.0
\t\t\t*MESH_TVERT 1 1.0 0.0 0.0
\t\t\t*MESH_TVERT 2 1.0 1.0 0.0
\t\t\t*MESH_TVERT 3 0.0 1.0 0.0
\t\t\t*MESH_TVERT 4 0.0 0.0 0.0
\t\t\t*MESH_TVERT 5 1.0 0.0 0.0
\t\t\t*MESH_TVERT 6 1.0 1.0 0.0
\t\t\t*MESH_TVERT 7 0.0 1.0 0.0
\t\t}
\t\t*MESH_NUMTVFACES 6
\t\t*MESH_TFACELIST {
\t\t\t*MESH_TFACE 0 0 1 2
\t\t\t*MESH_TFACE 1 0 2 3
\t\t\t*MESH_TFACE 2 4 5 6
\t\t\t*MESH_TFACE 3 4 6 7
\t\t\t*MESH_TFACE 4 0 4 5
\t\t\t*MESH_TFACE 5 0 5 1
\t\t}
\t\t*MESH_NUMCVERTEX 8
\t\t*MESH_CVERTLIST {
\t\t\t*MESH_VERTCOL 0 1.0 0.0 0.0
\t\t\t*MESH_VERTCOL 1 0.0 1.0 0.0
\t\t\t*MESH_VERTCOL 2 0.0 0.0 1.0
\t\t\t*MESH_VERTCOL 3 1.0 1.0 0.0
\t\t\t*MESH_VERTCOL 4 1.0 0.0 1.0
\t\t\t*MESH_VERTCOL 5 0.0 1.0 1.0
\t\t\t*MESH_VERTCOL 6 1.0 1.0 1.0
\t\t\t*MESH_VERTCOL 7 0.5 0.5 0.5
\t\t}
\t\t*MESH_NUMCVFACES 6
\t\t*MESH_CFACELIST {
\t\t\t*MESH_CFACE 0 0 1 2
\t\t\t*MESH_CFACE 1 0 2 3
\t\t\t*MESH_CFACE 2 4 5 6
\t\t\t*MESH_CFACE 3 4 6 7
\t\t\t*MESH_CFACE 4 0 4 5
\t\t\t*MESH_CFACE 5 0 5 1
\t\t}
\t\t*MESH_NORMALS {
\t\t\t*MESH_FACENORMAL 0 0.0 0.0 -1.0
\t\t\t\t*MESH_VERTEXNORMAL 0 0.0 0.0 -1.0
\t\t\t\t*MESH_VERTEXNORMAL 1 0.0 0.0 -1.0
\t\t\t\t*MESH_VERTEXNORMAL 2 0.0 0.0 -1.0
\t\t\t*MESH_FACENORMAL 1 0.0 0.0 -1.0
\t\t\t\t*MESH_VERTEXNORMAL 0 0.0 0.0 -1.0
\t\t\t\t*MESH_VERTEXNORMAL 2 0.0 0.0 -1.0
\t\t\t\t*MESH_VERTEXNORMAL 3 0.0 0.0 -1.0
\t\t\t*MESH_FACENORMAL 2 0.0 0.0 1.0
\t\t\t\t*MESH_VERTEXNORMAL 4 0.0 0.0 1.0
\t\t\t\t*MESH_VERTEXNORMAL 5 0.0 0.0 1.0
\t\t\t\t*MESH_VERTEXNORMAL 6 0.0 0.0 1.0
\t\t\t*MESH_FACENORMAL 3 0.0 0.0 1.0
\t\t\t\t*MESH_VERTEXNORMAL 4 0.0 0.0 1.0
\t\t\t\t*MESH_VERTEXNORMAL 6 0.0 0.0 1.0
\t\t\t\t*MESH_VERTEXNORMAL 7 0.0 0.0 1.0
\t\t\t*MESH_FACENORMAL 4 0.0 -1.0 0.0
\t\t\t\t*MESH_VERTEXNORMAL 0 0.0 -1.0 0.0
\t\t\t\t*MESH_VERTEXNORMAL 4 0.0 -1.0 0.0
\t\t\t\t*MESH_VERTEXNORMAL 5 0.0 -1.0 0.0
\t\t\t*MESH_FACENORMAL 5 0.0 -1.0 0.0
\t\t\t\t*MESH_VERTEXNORMAL 0 0.0 -1.0 0.0
\t\t\t\t*MESH_VERTEXNORMAL 5 0.0 -1.0 0.0
\t\t\t\t*MESH_VERTEXNORMAL 1 0.0 -1.0 0.0
\t\t}
\t\t*MESH_MAPPINGCHANNEL 2 {
\t\t\t*MESH_NUMTVERTEX 4
\t\t\t*MESH_TVERTLIST {
\t\t\t\t*MESH_TVERT 0 0.0 0.0 0.5
\t\t\t\t*MESH_TVERT 1 1.0 0.0 0.5
\t\t\t\t*MESH_TVERT 2 1.0 1.0 0.5
\t\t\t\t*MESH_TVERT 3 0.0 1.0 0.5
\t\t\t}
\t\t\t*MESH_NUMTVFACES 6
\t\t\t*MESH_TFACELIST {
\t\t\t\t*MESH_TFACE 0 0 1 2
\t\t\t\t*MESH_TFACE 1 0 2 3
\t\t\t\t*MESH_TFACE 2 0 1 2
\t\t\t\t*MESH_TFACE 3 0 2 3
\t\t\t\t*MESH_TFACE 4 0 1 2
\t\t\t\t*MESH_TFACE 5 0 1 2
\t\t\t}
\t\t}
\t\t*MESH_WEIGHTS {
\t\t\t*MESH_NUMVERTEX 8
\t\t\t*MESH_NUMBONE 2
\t\t\t*MESH_BONE_LIST {
\t\t\t\t*MESH_BONE_NAME 0 "Bone0"
\t\t\t\t*MESH_BONE_NAME 1 "Bone1"
\t\t\t}
\t\t\t*MESH_BONE_VERTEX_LIST {
\t\t\t\t*MESH_BONE_VERTEX 0 0.0 0.0 0.0 0 1.0
\t\t\t\t*MESH_BONE_VERTEX 1 1.0 0.0 0.0 0 0.8 1 0.2
\t\t\t\t*MESH_BONE_VERTEX 2 1.0 1.0 0.0 0 0.5 1 0.5
\t\t\t\t*MESH_BONE_VERTEX 3 0.0 1.0 0.0 0 0.7 1 0.3
\t\t\t\t*MESH_BONE_VERTEX 4 0.0 0.0 1.0 1 0.9 0 0.1
\t\t\t\t*MESH_BONE_VERTEX 5 1.0 0.0 1.0 1 0.8 0 0.2
\t\t\t\t*MESH_BONE_VERTEX 6 1.0 1.0 1.0 1 0.6 0 0.4
\t\t\t\t*MESH_BONE_VERTEX 7 0.0 1.0 1.0 1 1.0
\t\t\t}
\t\t}
\t\t*MESH_ANIMATION {
\t\t}
\t}
\t*MATERIAL_REF 0
\t*TM_ANIMATION {
\t\t*NODE_NAME "FullMesh"
\t\t*CONTROL_POS_TRACK {
\t\t\t*CONTROL_POS_SAMPLE 0 0.0 0.0 0.0
\t\t\t*CONTROL_POS_SAMPLE 160 1.0 0.0 0.0
\t\t\t*CONTROL_POS_SAMPLE 320 2.0 1.0 0.0
\t\t}
\t\t*CONTROL_ROT_TRACK {
\t\t\t*CONTROL_ROT_SAMPLE 0 0.0 0.0 1.0 0.0
\t\t\t*CONTROL_ROT_SAMPLE 160 0.0 0.0 1.0 0.5
\t\t\t*CONTROL_ROT_SAMPLE 320 0.0 0.0 1.0 1.0
\t\t}
\t\t*CONTROL_SCALE_TRACK {
\t\t\t*CONTROL_SCALE_SAMPLE 0 1.0 1.0 1.0
\t\t\t*CONTROL_SCALE_SAMPLE 160 1.5 1.5 1.5
\t\t\t*CONTROL_SCALE_SAMPLE 320 1.0 1.0 1.0
\t\t}
\t}
}
""")

    # 2. seed_ase_lights_cameras.ase
    #    ASE file with *CAMERAOBJECT (target and free) and *LIGHTOBJECT
    #    (omni, target, free, directional) with light settings and
    #    camera settings. Also exercises target animation.
    write_text(os.path.join(out_dir, "seed_ase_lights_cameras.ase"), """\
*3DSMAX_ASCIIEXPORT 200
*SCENE {
\t*SCENE_FIRSTFRAME 0
\t*SCENE_LASTFRAME 100
\t*SCENE_FRAMESPEED 30
\t*SCENE_TICKSPERFRAME 160
}
*MATERIAL_LIST {
\t*MATERIAL_COUNT 0
}
*CAMERAOBJECT {
\t*NODE_NAME "Camera_Target"
\t*CAMERA_TYPE target
\t*NODE_TM {
\t\t*NODE_NAME "Camera_Target"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 10.0 -20.0 5.0
\t}
\t*NODE_TM {
\t\t*NODE_NAME "Camera_Target.Target"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 0.0 0.0 0.0
\t}
\t*CAMERA_SETTINGS {
\t\t*CAMERA_NEAR 1.0
\t\t*CAMERA_FAR 1000.0
\t\t*CAMERA_FOV 0.785
\t}
\t*TM_ANIMATION {
\t\t*NODE_NAME "Camera_Target"
\t\t*CONTROL_POS_TRACK {
\t\t\t*CONTROL_POS_SAMPLE 0 10.0 -20.0 5.0
\t\t\t*CONTROL_POS_SAMPLE 480 15.0 -15.0 5.0
\t\t}
\t}
\t*TM_ANIMATION {
\t\t*NODE_NAME "Camera_Target.Target"
\t\t*CONTROL_POS_TRACK {
\t\t\t*CONTROL_POS_SAMPLE 0 0.0 0.0 0.0
\t\t\t*CONTROL_POS_SAMPLE 480 2.0 3.0 0.0
\t\t}
\t}
}
*CAMERAOBJECT {
\t*NODE_NAME "Camera_Free"
\t*CAMERA_TYPE free
\t*NODE_TM {
\t\t*NODE_NAME "Camera_Free"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 5.0 5.0 5.0
\t}
\t*CAMERA_SETTINGS {
\t\t*CAMERA_NEAR 0.5
\t\t*CAMERA_FAR 500.0
\t\t*CAMERA_FOV 1.047
\t}
}
*LIGHTOBJECT {
\t*NODE_NAME "Light_Omni"
\t*LIGHT_TYPE omni
\t*NODE_TM {
\t\t*NODE_NAME "Light_Omni"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 0.0 0.0 10.0
\t}
\t*LIGHT_SETTINGS {
\t\t*LIGHT_COLOR 1.0 0.9 0.8
\t\t*LIGHT_INTENS 1.5
\t\t*LIGHT_HOTSPOT 45.0
\t\t*LIGHT_FALLOFF 60.0
\t}
}
*LIGHTOBJECT {
\t*NODE_NAME "Light_Target"
\t*LIGHT_TYPE target
\t*NODE_TM {
\t\t*NODE_NAME "Light_Target"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 -5.0 0.0 8.0
\t}
\t*LIGHT_SETTINGS {
\t\t*LIGHT_COLOR 0.5 0.5 1.0
\t\t*LIGHT_INTENS 2.0
\t}
\t*TM_ANIMATION {
\t\t*NODE_NAME "Light_Target.Target"
\t\t*CONTROL_POS_TRACK {
\t\t\t*CONTROL_POS_SAMPLE 0 0.0 0.0 0.0
\t\t\t*CONTROL_POS_SAMPLE 480 1.0 1.0 0.0
\t\t}
\t}
}
*LIGHTOBJECT {
\t*NODE_NAME "Light_Dir"
\t*LIGHT_TYPE directional
\t*NODE_TM {
\t\t*NODE_NAME "Light_Dir"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 0.0 0.0 20.0
\t}
\t*LIGHT_SETTINGS {
\t\t*LIGHT_COLOR 1.0 1.0 1.0
\t\t*LIGHT_INTENS 1.0
\t}
}
*LIGHTOBJECT {
\t*NODE_NAME "Light_Free"
\t*LIGHT_TYPE free
\t*NODE_TM {
\t\t*NODE_NAME "Light_Free"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 3.0 3.0 3.0
\t}
\t*LIGHT_SETTINGS {
\t\t*LIGHT_COLOR 0.8 1.0 0.8
\t\t*LIGHT_INTENS 0.8
\t\t*LIGHT_HOTSPOT 30.0
\t\t*LIGHT_FALLOFF 50.0
\t}
}
""")

    # 3. seed_ase_multimaterial.ase
    #    ASE with multiple geometry objects referencing different materials,
    #    including multi/sub-object materials. Uses Bezier and TCB animation
    #    types. Exercises CONTROL_BEZIER_POS_KEY, CONTROL_TCB_ROT_KEY,
    #    CONTROL_BEZIER_SCALE_KEY, and Wire shading type.
    write_text(os.path.join(out_dir, "seed_ase_multimaterial.ase"), """\
*3DSMAX_ASCIIEXPORT 200
*SCENE {
\t*SCENE_FIRSTFRAME 0
\t*SCENE_LASTFRAME 50
\t*SCENE_FRAMESPEED 24
\t*SCENE_TICKSPERFRAME 200
}
*MATERIAL_LIST {
\t*MATERIAL_COUNT 3
\t*MATERIAL 0 {
\t\t*MATERIAL_NAME "RedMat"
\t\t*MATERIAL_AMBIENT 0.2 0.0 0.0
\t\t*MATERIAL_DIFFUSE 0.9 0.1 0.1
\t\t*MATERIAL_SPECULAR 1.0 0.5 0.5
\t\t*MATERIAL_SHINE 0.6
\t\t*MATERIAL_SHADING Wire
\t\t*MAP_DIFFUSE {
\t\t\t*MAP_NAME "RedTex"
\t\t\t*MAP_CLASS "Bitmap"
\t\t\t*BITMAP "red.tga"
\t\t\t*MAP_AMOUNT 1.0
\t\t\t*UVW_U_OFFSET 0.1
\t\t\t*UVW_V_OFFSET -0.2
\t\t\t*UVW_U_TILING 2.0
\t\t\t*UVW_V_TILING 2.0
\t\t\t*UVW_ANGLE 0.5
\t\t}
\t}
\t*MATERIAL 1 {
\t\t*MATERIAL_NAME "GreenMat"
\t\t*MATERIAL_AMBIENT 0.0 0.2 0.0
\t\t*MATERIAL_DIFFUSE 0.1 0.9 0.1
\t\t*MATERIAL_SPECULAR 0.5 1.0 0.5
\t\t*MATERIAL_SHINE 0.4
\t\t*MATERIAL_SHADING Gouraud
\t}
\t*MATERIAL 2 {
\t\t*MATERIAL_NAME "BlueMat"
\t\t*MATERIAL_AMBIENT 0.0 0.0 0.2
\t\t*MATERIAL_DIFFUSE 0.1 0.1 0.9
\t\t*MATERIAL_SPECULAR 0.5 0.5 1.0
\t\t*MATERIAL_SHINE 0.8
\t\t*MATERIAL_SHADING Blinn
\t\t*NUMSUBMTLS 2
\t\t*SUBMATERIAL 0 {
\t\t\t*MATERIAL_NAME "BlueSub0"
\t\t\t*MATERIAL_DIFFUSE 0.2 0.2 1.0
\t\t\t*MATERIAL_SHADING Phong
\t\t}
\t\t*SUBMATERIAL 1 {
\t\t\t*MATERIAL_NAME "BlueSub1"
\t\t\t*MATERIAL_DIFFUSE 0.1 0.1 0.7
\t\t\t*MATERIAL_SHADING Flat
\t\t}
\t}
}
*GEOMOBJECT {
\t*NODE_NAME "RedTriangle"
\t*NODE_TM {
\t\t*NODE_NAME "RedTriangle"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 0.0 0.0 0.0
\t}
\t*MESH {
\t\t*MESH_NUMVERTEX 3
\t\t*MESH_NUMFACES 1
\t\t*MESH_VERTEX_LIST {
\t\t\t*MESH_VERTEX 0 0.0 0.0 0.0
\t\t\t*MESH_VERTEX 1 2.0 0.0 0.0
\t\t\t*MESH_VERTEX 2 1.0 2.0 0.0
\t\t}
\t\t*MESH_FACE_LIST {
\t\t\t*MESH_FACE 0: A: 0 B: 1 C: 2 *MESH_SMOOTHING 1 *MESH_MTLID 0
\t\t}
\t\t*MESH_NUMTVERTEX 3
\t\t*MESH_TVERTLIST {
\t\t\t*MESH_TVERT 0 0.0 0.0 0.0
\t\t\t*MESH_TVERT 1 1.0 0.0 0.0
\t\t\t*MESH_TVERT 2 0.5 1.0 0.0
\t\t}
\t\t*MESH_NUMTVFACES 1
\t\t*MESH_TFACELIST {
\t\t\t*MESH_TFACE 0 0 1 2
\t\t}
\t}
\t*MATERIAL_REF 0
\t*TM_ANIMATION {
\t\t*NODE_NAME "RedTriangle"
\t\t*CONTROL_POS_BEZIER {
\t\t\t*CONTROL_BEZIER_POS_KEY 0 0.0 0.0 0.0
\t\t\t*CONTROL_BEZIER_POS_KEY 200 1.0 0.0 0.0
\t\t\t*CONTROL_BEZIER_POS_KEY 400 2.0 1.0 0.0
\t\t}
\t\t*CONTROL_ROT_TCB {
\t\t\t*CONTROL_TCB_ROT_KEY 0 0.0 0.0 1.0 0.0
\t\t\t*CONTROL_TCB_ROT_KEY 200 0.0 0.0 1.0 0.785
\t\t\t*CONTROL_TCB_ROT_KEY 400 0.0 0.0 1.0 1.571
\t\t}
\t\t*CONTROL_SCALE_BEZIER {
\t\t\t*CONTROL_BEZIER_SCALE_KEY 0 1.0 1.0 1.0
\t\t\t*CONTROL_BEZIER_SCALE_KEY 200 1.5 1.5 1.5
\t\t\t*CONTROL_BEZIER_SCALE_KEY 400 1.0 1.0 1.0
\t\t}
\t}
}
*GEOMOBJECT {
\t*NODE_NAME "GreenQuad"
\t*NODE_PARENT "RedTriangle"
\t*NODE_TM {
\t\t*NODE_NAME "GreenQuad"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 3.0 0.0 0.0
\t}
\t*MESH {
\t\t*MESH_NUMVERTEX 4
\t\t*MESH_NUMFACES 2
\t\t*MESH_VERTEX_LIST {
\t\t\t*MESH_VERTEX 0 0.0 0.0 0.0
\t\t\t*MESH_VERTEX 1 1.0 0.0 0.0
\t\t\t*MESH_VERTEX 2 1.0 1.0 0.0
\t\t\t*MESH_VERTEX 3 0.0 1.0 0.0
\t\t}
\t\t*MESH_FACE_LIST {
\t\t\t*MESH_FACE 0: A: 0 B: 1 C: 2 *MESH_SMOOTHING 1 *MESH_MTLID 0
\t\t\t*MESH_FACE 1: A: 0 B: 2 C: 3 *MESH_SMOOTHING 1 *MESH_MTLID 0
\t\t}
\t}
\t*MATERIAL_REF 1
\t*TM_ANIMATION {
\t\t*NODE_NAME "GreenQuad"
\t\t*CONTROL_POS_TCB {
\t\t\t*CONTROL_TCB_POS_KEY 0 3.0 0.0 0.0
\t\t\t*CONTROL_TCB_POS_KEY 200 3.0 2.0 0.0
\t\t\t*CONTROL_TCB_POS_KEY 400 3.0 0.0 0.0
\t\t}
\t\t*CONTROL_SCALE_TCB {
\t\t\t*CONTROL_TCB_SCALE_KEY 0 1.0 1.0 1.0
\t\t\t*CONTROL_TCB_SCALE_KEY 200 2.0 2.0 2.0
\t\t\t*CONTROL_TCB_SCALE_KEY 400 1.0 1.0 1.0
\t\t}
\t}
}
*GEOMOBJECT {
\t*NODE_NAME "BlueBox"
\t*NODE_TM {
\t\t*NODE_NAME "BlueBox"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 -3.0 0.0 0.0
\t}
\t*MESH {
\t\t*MESH_NUMVERTEX 4
\t\t*MESH_NUMFACES 2
\t\t*MESH_VERTEX_LIST {
\t\t\t*MESH_VERTEX 0 0.0 0.0 0.0
\t\t\t*MESH_VERTEX 1 1.0 0.0 0.0
\t\t\t*MESH_VERTEX 2 1.0 1.0 0.0
\t\t\t*MESH_VERTEX 3 0.0 1.0 0.0
\t\t}
\t\t*MESH_FACE_LIST {
\t\t\t*MESH_FACE 0: A: 0 B: 1 C: 2 *MESH_SMOOTHING 1 *MESH_MTLID 0
\t\t\t*MESH_FACE 1: A: 0 B: 2 C: 3 *MESH_SMOOTHING 2 *MESH_MTLID 1
\t\t}
\t}
\t*MATERIAL_REF 2
\t*TM_ANIMATION {
\t\t*NODE_NAME "BlueBox"
\t\t*CONTROL_ROT_BEZIER {
\t\t\t*CONTROL_BEZIER_ROT_KEY 0 1.0 0.0 0.0 0.0
\t\t\t*CONTROL_BEZIER_ROT_KEY 200 1.0 0.0 0.0 1.571
\t\t\t*CONTROL_BEZIER_ROT_KEY 400 1.0 0.0 0.0 3.142
\t\t}
\t}
}
*HELPEROBJECT {
\t*NODE_NAME "Helper1"
\t*NODE_TM {
\t\t*NODE_NAME "Helper1"
\t\t*TM_ROW0 1.0 0.0 0.0
\t\t*TM_ROW1 0.0 1.0 0.0
\t\t*TM_ROW2 0.0 0.0 1.0
\t\t*TM_ROW3 0.0 0.0 5.0
\t}
}
""")


# ---------------------------------------------------------------------------
# MDL seed generation helpers
# ---------------------------------------------------------------------------

def pack_float(f):
    return struct.pack("<f", f)


def pack_int32(i):
    return struct.pack("<i", i)


def pack_uint32(i):
    return struct.pack("<I", i)


def pack_uint16(i):
    return struct.pack("<H", i)


def pack_uint8(i):
    return struct.pack("<B", i)


def pad_string(s, length):
    """Pad/truncate a string to exactly `length` bytes, null-terminated."""
    encoded = s.encode("ascii")[:length - 1]
    return encoded + b"\x00" * (length - len(encoded))


# ---------------------------------------------------------------------------
# MDL seed generation - Quake 1 format
# ---------------------------------------------------------------------------

def generate_mdl_quake1(out_dir):
    """Generate a Quake 1 MDL (IDPO magic) with a small mesh."""
    # Header structure (MDL::Header):
    #   uint32 ident (IDPO = 0x4F504449)
    #   int32  version (6)
    #   float  scale[3]
    #   float  translate[3]
    #   float  boundingradius
    #   float  vEyePos[3]  (ai_real = float on most systems)
    #   int32  num_skins
    #   int32  skinwidth
    #   int32  skinheight
    #   int32  num_verts
    #   int32  num_tris
    #   int32  num_frames
    #   int32  synctype
    #   int32  flags
    #   float  size

    num_verts = 4
    num_tris = 2
    num_frames = 1
    num_skins = 1
    skinwidth = 4
    skinheight = 4

    header = b""
    header += struct.pack("<4s", b"IDPO")  # ident
    header += pack_int32(6)                # version
    header += pack_float(1.0) + pack_float(1.0) + pack_float(1.0)  # scale
    header += pack_float(0.0) + pack_float(0.0) + pack_float(0.0)  # translate
    header += pack_float(10.0)             # boundingradius
    header += pack_float(0.0) + pack_float(0.0) + pack_float(0.0)  # vEyePos
    header += pack_int32(num_skins)
    header += pack_int32(skinwidth)
    header += pack_int32(skinheight)
    header += pack_int32(num_verts)
    header += pack_int32(num_tris)
    header += pack_int32(num_frames)
    header += pack_int32(0)                # synctype
    header += pack_int32(0)                # flags
    header += pack_float(0.0)              # size

    # Skin data: single skin (group=0), then pixel data
    skin_data = pack_int32(0)  # group = 0 (single skin)
    skin_data += b"\x00" * (skinwidth * skinheight)  # palettized pixel data

    # Texture coordinates (TexCoord: onseam, s, t) for each vertex
    texcoords = b""
    tc_values = [(0, 0, 0), (0, 3, 0), (0, 3, 3), (0, 0, 3)]
    for onseam, s, t in tc_values:
        texcoords += pack_int32(onseam) + pack_int32(s) + pack_int32(t)

    # Triangles (Triangle: facesfront, vertex[3])
    triangles = b""
    triangles += pack_int32(1) + pack_int32(0) + pack_int32(1) + pack_int32(2)  # front face
    triangles += pack_int32(0) + pack_int32(0) + pack_int32(2) + pack_int32(3)  # back face

    # Frame: type=0 (simple), then SimpleFrame
    # SimpleFrame: bboxmin(Vertex), bboxmax(Vertex), name[16], verts[]
    # Vertex: v[3](uint8), normalIndex(uint8)
    frame = pack_int32(0)  # type = 0 (simple frame)
    # bboxmin
    frame += pack_uint8(0) + pack_uint8(0) + pack_uint8(0) + pack_uint8(0)
    # bboxmax
    frame += pack_uint8(100) + pack_uint8(100) + pack_uint8(100) + pack_uint8(0)
    # name
    frame += pad_string("frame0", 16)
    # vertices
    vert_positions = [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)]
    for vx, vy, vz in vert_positions:
        frame += pack_uint8(vx) + pack_uint8(vy) + pack_uint8(vz) + pack_uint8(0)

    data = header + skin_data + texcoords + triangles + frame
    write_bin(os.path.join(out_dir, "seed_quake1.mdl"), data)


def generate_mdl_quake1_groupframe(out_dir):
    """Generate a Quake 1 MDL with a group frame (type != 0)."""
    num_verts = 3
    num_tris = 1
    num_frames = 1
    num_skins = 1
    skinwidth = 2
    skinheight = 2

    header = b""
    header += struct.pack("<4s", b"IDPO")
    header += pack_int32(6)
    header += pack_float(1.0) * 3  # scale
    header += pack_float(0.0) * 3  # translate
    header += pack_float(5.0)      # boundingradius
    header += pack_float(0.0) * 3  # vEyePos
    header += pack_int32(num_skins)
    header += pack_int32(skinwidth)
    header += pack_int32(skinheight)
    header += pack_int32(num_verts)
    header += pack_int32(num_tris)
    header += pack_int32(num_frames)
    header += pack_int32(0)  # synctype
    header += pack_int32(0)  # flags
    header += pack_float(0.0)

    # Single skin, group=0
    skin_data = pack_int32(0) + b"\x01\x02\x03\x04"

    # TexCoords
    texcoords = b""
    for i in range(num_verts):
        texcoords += pack_int32(0) + pack_int32(i) + pack_int32(i)

    # Triangle
    triangles = pack_int32(1) + pack_int32(0) + pack_int32(1) + pack_int32(2)

    # Group frame: type=1, numframes=2, min, max, times[2], then 2 SimpleFrames
    num_subframes = 2
    frame = pack_int32(1)  # type = 1 (group frame)
    frame += pack_int32(num_subframes)
    # min vertex
    frame += pack_uint8(0) + pack_uint8(0) + pack_uint8(0) + pack_uint8(0)
    # max vertex
    frame += pack_uint8(50) + pack_uint8(50) + pack_uint8(50) + pack_uint8(0)
    # times
    frame += pack_float(0.0) + pack_float(1.0)
    # SimpleFrame 1 (the one that gets parsed - first in group)
    frame += pack_uint8(0) * 4 + pack_uint8(50) * 3 + pack_uint8(0)  # bbox
    frame += pad_string("grp_f0", 16)
    frame += (pack_uint8(0) + pack_uint8(0) + pack_uint8(0) + pack_uint8(0)) * num_verts
    # SimpleFrame 2
    frame += pack_uint8(0) * 4 + pack_uint8(50) * 3 + pack_uint8(0)
    frame += pad_string("grp_f1", 16)
    frame += (pack_uint8(25) + pack_uint8(25) + pack_uint8(25) + pack_uint8(0)) * num_verts

    data = header + skin_data + texcoords + triangles + frame
    write_bin(os.path.join(out_dir, "seed_quake1_groupframe.mdl"), data)


# ---------------------------------------------------------------------------
# MDL seed generation - 3DGS MDL3 format
# ---------------------------------------------------------------------------

def generate_mdl_gs3(out_dir):
    """Generate a 3D GameStudio A2 MDL (MDL2 magic) with byte-packed vertices.

    MDL2 magic sets iGSFileVersion=2 and calls InternReadFile_Quake1().
    In that path, skins use Quake1 skin reading code where group=0 means
    single skin and calls CreateTexture_3DGS_MDL4 with iType=group.
    Type 2 = R5G6B5 format (2 bytes/pixel).

    Note: MDL2 uses InternReadFile_Quake1 which uses Quake1 TexCoord
    and Triangle structures (NOT MDL3 ones), despite being "GS3" version.
    """

    num_verts = 3
    num_tris = 1
    num_frames = 1
    num_skins = 1
    skinwidth = 4
    skinheight = 4

    header = b""
    header += struct.pack("<4s", b"MDL2")
    header += pack_int32(6)
    header += pack_float(1.0) * 3  # scale
    header += pack_float(0.0) * 3  # translate
    header += pack_float(5.0)
    header += pack_float(0.0) * 3  # vEyePos
    header += pack_int32(num_skins)
    header += pack_int32(skinwidth)
    header += pack_int32(skinheight)
    header += pack_int32(num_verts)
    header += pack_int32(num_tris)
    header += pack_int32(num_frames)
    header += pack_int32(0)   # synctype (0 for Quake1 path)
    header += pack_int32(0)   # flags
    header += pack_float(0.0)

    # Skin: type=2 (R5G6B5), pixel data is 2 bytes per pixel
    # CreateTexture_3DGS_MDL4 handles type 2 as R5G6B5
    skin_data = pack_int32(2)  # group/type = 2
    skin_data += b"\x00\x00" * (skinwidth * skinheight)  # R5G6B5 pixels

    # Quake1 TexCoord (12 bytes each: onseam, s, t)
    texcoords = b""
    for i in range(num_verts):
        texcoords += pack_int32(0) + pack_int32(i) + pack_int32(i)

    # Quake1 Triangle (16 bytes: facesfront, vertex[3])
    triangles = pack_int32(1) + pack_int32(0) + pack_int32(1) + pack_int32(2)

    # Frame: type=0, SimpleFrame with byte Vertices
    frame = pack_int32(0)
    frame += pack_uint8(0) * 4 + pack_uint8(50) * 3 + pack_uint8(0)
    frame += pad_string("frame0", 16)
    verts = [(10, 20, 30), (40, 10, 30), (25, 40, 30)]
    for vx, vy, vz in verts:
        frame += pack_uint8(vx) + pack_uint8(vy) + pack_uint8(vz) + pack_uint8(0)

    # Padding to ensure VALIDATE_FILE_SIZE passes
    padding = b"\x00" * 32

    data = header + skin_data + texcoords + triangles + frame + padding
    write_bin(os.path.join(out_dir, "seed_mdl_gs3.mdl"), data)


# ---------------------------------------------------------------------------
# MDL seed generation - 3DGS MDL4 format (16-bit vertices)
# ---------------------------------------------------------------------------

def generate_mdl_gs4(out_dir):
    """Generate a 3D GameStudio A4 MDL (MDL3 magic) with MDL4 features.
    For GS version 4+, frame type != 0 uses Vertex_MDL4 (16-bit vertices)."""

    num_verts = 4
    num_tris = 2
    num_frames = 1
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_uvcoords = 4

    header = b""
    header += struct.pack("<4s", b"MDL3")
    header += pack_int32(6)
    header += pack_float(0.01) * 3  # scale (small for 16-bit range)
    header += pack_float(0.0) * 3   # translate
    header += pack_float(10.0)
    header += pack_float(0.0) * 3
    header += pack_int32(num_skins)
    header += pack_int32(skinwidth)
    header += pack_int32(skinheight)
    header += pack_int32(num_verts)
    header += pack_int32(num_tris)
    header += pack_int32(num_frames)
    header += pack_int32(num_uvcoords)
    header += pack_int32(0)
    header += pack_float(0.0)

    # Skin: type=2 (R5G6B5), pixel data is 2 bytes per pixel
    skin_data = pack_int32(2)
    skin_data += b"\x00\x00" * (skinwidth * skinheight)

    # TexCoord_MDL3
    texcoords = b""
    for i in range(num_uvcoords):
        texcoords += struct.pack("<hh", i, i)

    # Triangle_MDL3
    triangles = b""
    triangles += struct.pack("<HHH", 0, 1, 2) + struct.pack("<HHH", 0, 1, 2)
    triangles += struct.pack("<HHH", 0, 2, 3) + struct.pack("<HHH", 0, 2, 3)

    # Frame type=1 triggers short-packed (Vertex_MDL4) path for GS version >= 4
    # BUT: for iGSFileVersion == 3, it uses byte packed even with type != 0
    # So we use type=0 for GS3 magic (iGSFileVersion=3) to exercise byte path
    frame = pack_int32(0)
    # SimpleFrame
    frame += pack_uint8(0) * 4 + pack_uint8(200) * 3 + pack_uint8(0)
    frame += pad_string("frame0", 16)
    verts = [(10, 20, 30), (100, 20, 30), (100, 100, 30), (10, 100, 30)]
    for vx, vy, vz in verts:
        frame += pack_uint8(vx) + pack_uint8(vy) + pack_uint8(vz) + pack_uint8(5)

    data = header + skin_data + texcoords + triangles + frame
    write_bin(os.path.join(out_dir, "seed_mdl_gs4.mdl"), data)


# ---------------------------------------------------------------------------
# MDL seed generation - 3DGS MDL5 format (16-bit vertices with MIPs)
# ---------------------------------------------------------------------------

def generate_mdl_gs5(out_dir):
    """Generate a 3DGS A5 MDL (MDL5 magic) which uses MDL5 skin loading
    and 16-bit packed vertices (frame type != 0 with version >= 4).

    For MDL5 (iGSFileVersion=5), skin loading calls CreateTexture_3DGS_MDL5
    which reads width and height from the skin data itself (NOT from the header).
    Skin data layout after the type uint32:
      uint32 width, uint32 height, then pixel data
    """

    num_verts = 3
    num_tris = 1
    num_frames = 1
    num_skins = 1
    skinwidth = 4
    skinheight = 4
    num_uvcoords = 3

    header = b""
    header += struct.pack("<4s", b"MDL5")
    header += pack_int32(6)
    header += pack_float(0.001) * 3  # very small scale for 16-bit
    header += pack_float(0.0) * 3
    header += pack_float(5.0)
    header += pack_float(0.0) * 3
    header += pack_int32(num_skins)
    header += pack_int32(skinwidth)   # used for UV scaling only in MDL5
    header += pack_int32(skinheight)
    header += pack_int32(num_verts)
    header += pack_int32(num_tris)
    header += pack_int32(num_frames)
    header += pack_int32(num_uvcoords)
    header += pack_int32(0)
    header += pack_float(0.0)

    # MDL5 skin: type(uint32) + width(uint32) + height(uint32) + pixel data
    # type 2 = R5G6B5 (2 bytes per pixel)
    skin_pixels = skinwidth * skinheight
    skin_data = pack_int32(2)  # type = 2 (R5G6B5)
    skin_data += pack_uint32(skinwidth)   # width read by CreateTexture_3DGS_MDL5
    skin_data += pack_uint32(skinheight)  # height read by CreateTexture_3DGS_MDL5
    skin_data += b"\x00\x00" * skin_pixels  # R5G6B5 pixels

    # TexCoord_MDL3
    texcoords = b""
    for i in range(num_uvcoords):
        texcoords += struct.pack("<hh", i, i)

    # Triangle_MDL3
    triangles = struct.pack("<HHH", 0, 1, 2) + struct.pack("<HHH", 0, 1, 2)

    # Frame type=1 to trigger Vertex_MDL4 (16-bit) path
    # SimpleFrame_MDLn_SP: bboxmin(Vertex_MDL4), bboxmax(Vertex_MDL4), name[16], verts[]
    # Vertex_MDL4: uint16 v[3], uint8 normalIndex, uint8 unused
    frame = pack_int32(1)  # type != 0 and version >= 4 -> short packed
    # bboxmin (Vertex_MDL4)
    frame += struct.pack("<HHH", 0, 0, 0) + pack_uint8(0) + pack_uint8(0)
    # bboxmax
    frame += struct.pack("<HHH", 1000, 1000, 1000) + pack_uint8(0) + pack_uint8(0)
    # name
    frame += pad_string("sframe0", 16)
    # Vertex_MDL4 data
    v_positions = [(100, 200, 300), (500, 100, 300), (300, 500, 300)]
    for vx, vy, vz in v_positions:
        frame += struct.pack("<HHH", vx, vy, vz) + pack_uint8(10) + pack_uint8(0)

    # Padding
    padding = b"\x00" * 32

    data = header + skin_data + texcoords + triangles + frame + padding
    write_bin(os.path.join(out_dir, "seed_mdl_gs5.mdl"), data)


# ---------------------------------------------------------------------------
# MDL seed generation - 3DGS MDL4 with ARGB4 texture (type=3)
# ---------------------------------------------------------------------------

def generate_mdl_gs4_argb4(out_dir):
    """Generate a MDL4 with ARGB4 texture (skin type 3)."""

    num_verts = 3
    num_tris = 1
    num_skins = 1
    skinwidth = 2
    skinheight = 2
    num_uvcoords = 3

    header = b""
    header += struct.pack("<4s", b"MDL4")  # GS5a magic
    header += pack_int32(6)
    header += pack_float(1.0) * 3
    header += pack_float(0.0) * 3
    header += pack_float(5.0)
    header += pack_float(0.0) * 3
    header += pack_int32(num_skins)
    header += pack_int32(skinwidth)
    header += pack_int32(skinheight)
    header += pack_int32(num_verts)
    header += pack_int32(num_tris)
    header += pack_int32(1)  # num_frames
    header += pack_int32(num_uvcoords)
    header += pack_int32(0)
    header += pack_float(0.0)

    # Skin type 3 = ARGB4444, 2 bytes per pixel
    skin_data = pack_int32(3)
    skin_data += b"\xFF\xFF" * (skinwidth * skinheight)

    texcoords = b""
    for i in range(num_uvcoords):
        texcoords += struct.pack("<hh", i, i)

    triangles = struct.pack("<HHH", 0, 1, 2) + struct.pack("<HHH", 0, 1, 2)

    # Frame type=1, 16-bit vertices
    frame = pack_int32(1)
    frame += struct.pack("<HHH", 0, 0, 0) + pack_uint8(0) + pack_uint8(0)
    frame += struct.pack("<HHH", 500, 500, 500) + pack_uint8(0) + pack_uint8(0)
    frame += pad_string("f0", 16)
    for vx, vy, vz in [(100, 0, 0), (0, 100, 0), (50, 50, 100)]:
        frame += struct.pack("<HHH", vx, vy, vz) + pack_uint8(0) + pack_uint8(0)

    data = header + skin_data + texcoords + triangles + frame
    write_bin(os.path.join(out_dir, "seed_mdl_gs4_argb4.mdl"), data)


# ---------------------------------------------------------------------------
# MDL seed generation - Half-Life 1 format
# ---------------------------------------------------------------------------

def generate_mdl_hl1(out_dir):
    """Generate a Half-Life 1 MDL (IDST magic, version 10) with bones,
    bodyparts, textures, and sequences. This is a complex binary format."""

    # HalfLifeMDLBaseHeader: char ident[4], int32 version
    # Header_HL1 extends it with many fields

    # We build a minimal but valid HL1 MDL:
    # - 2 bones (parent hierarchy)
    # - 1 bodypart with 1 model, 1 mesh
    # - 1 texture with 4x4 pixel data + 256-color palette
    # - 1 sequence with 1 frame
    # - 1 sequence group

    # Calculate offsets carefully
    header_size = 244  # sizeof(Header_HL1): 4+4+64+4 + 3*4*5 + 4 + 2*(4+4) + ...
    # Let's compute it exactly:
    # HalfLifeMDLBaseHeader: 4 (ident) + 4 (version) = 8
    # name[64] = 64
    # length: 4
    # eyeposition: 12
    # min: 12, max: 12
    # bbmin: 12, bbmax: 12
    # unused(flags): 4
    # numbones: 4, boneindex: 4
    # numbonecontrollers: 4, bonecontrollerindex: 4
    # numhitboxes: 4, hitboxindex: 4
    # numseq: 4, seqindex: 4
    # numseqgroups: 4, seqgroupindex: 4
    # numtextures: 4, textureindex: 4, texturedataindex: 4
    # numskinref: 4, numskinfamilies: 4, skinindex: 4
    # numbodyparts: 4, bodypartindex: 4
    # numattachments: 4, attachmentindex: 4
    # unused2..5: 4*4 = 16
    # numtransitions: 4, transitionindex: 4
    # Total: 8 + 64 + 4 + 12*4 + 4 + 4*2 + 4*2 + 4*2 + 4*2 + 4*2 + 4*3 + 4*3 + 4*2 + 4*2 + 16 + 4*2
    # = 8 + 64 + 4 + 48 + 4 + 8 + 8 + 8 + 8 + 8 + 12 + 12 + 8 + 8 + 16 + 8
    # = 244

    num_bones = 2
    num_bodyparts = 1
    num_textures = 1
    num_sequences = 1
    num_seqgroups = 1
    num_models = 1
    num_meshes = 1
    num_verts = 3
    num_norms = 3
    num_tris = 1
    tex_width = 4
    tex_height = 4

    # Bone_HL1: name[32] + parent(4) + unused(4) + bonecontroller[6]*4=24 + value[6]*4=24 + scale[6]*4=24
    # = 32 + 4 + 4 + 24 + 24 + 24 = 112
    bone_size = 112

    # SequenceGroup_HL1: label[32] + name[64] + unused(4) + unused2(4) = 104
    seqgroup_size = 104

    # SequenceDesc_HL1: label[32] + fps(4) + flags(4) + activity(4) + actweight(4)
    #   + numevents(4) + eventindex(4) + numframes(4) + unused(4) + unused2(4)
    #   + motiontype(4) + motionbone(4) + linearmovement(12)
    #   + unused3(4) + unused4(4) + bbmin(12) + bbmax(12)
    #   + numblends(4) + animindex(4) + blendtype[2]*4=8 + blendstart[2]*4=8
    #   + blendend[2]*4=8 + unused5(4) + seqgroup(4) + entrynode(4) + exitnode(4)
    #   + nodeflags(4) + unused6(4)
    # = 32+4+4+4+4+4+4+4+4+4+4+4+12+4+4+12+12+4+4+8+8+8+4+4+4+4+4+4 = 176
    seqdesc_size = 176

    # AnimValueOffset_HL1: offset[6] * uint16 = 12
    animoffset_size = 12

    # Bodypart_HL1: name[64] + nummodels(4) + base(4) + modelindex(4) = 76
    bodypart_size = 76

    # Model_HL1: name[64] + unused(4) + unused2(4) + nummesh(4) + meshindex(4)
    #   + numverts(4) + vertinfoindex(4) + vertindex(4) + numnorms(4)
    #   + norminfoindex(4) + normindex(4) + unused3(4) + unused4(4) = 112
    model_size = 112

    # Mesh_HL1: numtris(4) + triindex(4) + skinref(4) + numnorms(4) + unused(4) = 20
    mesh_size = 20

    # Texture_HL1: name[64] + flags(4) + width(4) + height(4) + index(4) = 80
    texture_size = 80

    # Layout:
    # [Header_HL1] at 0
    # [Bones] at header_size
    bone_offset = header_size
    # [Sequence groups] after bones
    seqgroup_offset = bone_offset + num_bones * bone_size
    # [Sequence descs] after seqgroups
    seqdesc_offset = seqgroup_offset + num_seqgroups * seqgroup_size
    # [Anim value offsets] after seqdescs (for 1 blend * num_bones)
    animoffset_offset = seqdesc_offset + num_sequences * seqdesc_size
    # [Anim data] after anim offsets (minimal: just zeros)
    animdata_offset = animoffset_offset + num_bones * animoffset_size
    animdata_size = 12  # small amount of anim data
    # [Bodyparts] after anim data
    bodypart_offset = animdata_offset + animdata_size
    # [Models] after bodyparts
    model_offset = bodypart_offset + num_bodyparts * bodypart_size
    # [Meshes] after models
    mesh_offset = model_offset + num_models * model_size
    # [Vertex bone indices (vertinfo)] after meshes
    vertinfo_offset = mesh_offset + num_meshes * mesh_size
    # [Vertices] after vertinfo
    vert_offset = vertinfo_offset + num_verts  # 1 byte per vertex
    # [Normal bone indices (norminfo)] after vertices
    norminfo_offset = vert_offset + num_norms * 12  # vec3_t = 12 bytes
    # [Normals] after norminfo
    norm_offset = norminfo_offset + num_norms  # 1 byte per normal
    # [Tri commands] after normals
    tricommand_offset = norm_offset + num_norms * 12
    # [Skin refs] after tri commands
    # Tri commands: short count, then Trivert structs
    # Simple: 3 (triangle strip of 3), 3 triverts, 0 (end)
    trivert_size = 8  # short vertindex, normindex, s, t
    tricommand_data = struct.pack("<h", 3)  # strip of 3
    for i in range(3):
        tricommand_data += struct.pack("<hhhh", i, i, i * tex_width, i * tex_height)
    tricommand_data += struct.pack("<h", 0)  # end
    tricommand_size = len(tricommand_data)

    skinref_offset = tricommand_offset + tricommand_size
    skinref_data = struct.pack("<H", 0)  # 1 skin ref pointing to texture 0
    skinref_size = len(skinref_data)

    # [Textures] after skin refs
    texture_offset = skinref_offset + skinref_size
    # [Texture data] after texture headers
    texturedata_offset = texture_offset + num_textures * texture_size
    # Texture pixel data: width*height bytes + 256*3 palette
    texdata_pixels = b"\x00" * (tex_width * tex_height)
    texdata_palette = b"\x00\x00\x00" * 256  # 768 bytes
    texdata_total = texdata_pixels + texdata_palette

    total_size = texturedata_offset + len(texdata_total)

    # Build the file
    buf = bytearray(total_size)

    # -- Header --
    pos = 0
    struct.pack_into("<4s", buf, pos, b"IDST"); pos += 4
    struct.pack_into("<i", buf, pos, 10); pos += 4  # version 10
    buf[pos:pos+64] = pad_string("test_model.mdl", 64); pos += 64
    struct.pack_into("<i", buf, pos, total_size); pos += 4  # length
    # eyeposition
    struct.pack_into("<fff", buf, pos, 0.0, 0.0, 2.0); pos += 12
    # min, max
    struct.pack_into("<fff", buf, pos, -1.0, -1.0, 0.0); pos += 12
    struct.pack_into("<fff", buf, pos, 1.0, 1.0, 2.0); pos += 12
    # bbmin, bbmax
    struct.pack_into("<fff", buf, pos, -1.0, -1.0, 0.0); pos += 12
    struct.pack_into("<fff", buf, pos, 1.0, 1.0, 2.0); pos += 12
    # unused (flags)
    struct.pack_into("<i", buf, pos, 0); pos += 4
    # bones
    struct.pack_into("<i", buf, pos, num_bones); pos += 4
    struct.pack_into("<i", buf, pos, bone_offset); pos += 4
    # bone controllers
    struct.pack_into("<i", buf, pos, 0); pos += 4
    struct.pack_into("<i", buf, pos, 0); pos += 4
    # hitboxes
    struct.pack_into("<i", buf, pos, 0); pos += 4
    struct.pack_into("<i", buf, pos, 0); pos += 4
    # sequences
    struct.pack_into("<i", buf, pos, num_sequences); pos += 4
    struct.pack_into("<i", buf, pos, seqdesc_offset); pos += 4
    # sequence groups
    struct.pack_into("<i", buf, pos, num_seqgroups); pos += 4
    struct.pack_into("<i", buf, pos, seqgroup_offset); pos += 4
    # textures
    struct.pack_into("<i", buf, pos, num_textures); pos += 4
    struct.pack_into("<i", buf, pos, texture_offset); pos += 4
    struct.pack_into("<i", buf, pos, texturedata_offset); pos += 4
    # skin refs
    struct.pack_into("<i", buf, pos, 1); pos += 4  # numskinref
    struct.pack_into("<i", buf, pos, 1); pos += 4  # numskinfamilies
    struct.pack_into("<i", buf, pos, skinref_offset); pos += 4
    # bodyparts
    struct.pack_into("<i", buf, pos, num_bodyparts); pos += 4
    struct.pack_into("<i", buf, pos, bodypart_offset); pos += 4
    # attachments
    struct.pack_into("<i", buf, pos, 0); pos += 4
    struct.pack_into("<i", buf, pos, 0); pos += 4
    # unused2..5
    struct.pack_into("<iiii", buf, pos, 0, 0, 0, 0); pos += 16
    # transitions
    struct.pack_into("<i", buf, pos, 0); pos += 4
    struct.pack_into("<i", buf, pos, 0); pos += 4
    assert pos == header_size, f"Header size mismatch: {pos} != {header_size}"

    # -- Bones --
    pos = bone_offset
    for i in range(num_bones):
        bone_name = f"bone_{i}"
        buf[pos:pos+32] = pad_string(bone_name, 32); pos += 32
        struct.pack_into("<i", buf, pos, -1 if i == 0 else 0); pos += 4  # parent
        struct.pack_into("<i", buf, pos, 0); pos += 4  # unused
        # bonecontroller[6]
        for _ in range(6):
            struct.pack_into("<i", buf, pos, -1); pos += 4
        # value[6]: pos xyz, rot xyz
        struct.pack_into("<ffffff", buf, pos, 0.0, 0.0, float(i), 0.0, 0.0, 0.0); pos += 24
        # scale[6]
        struct.pack_into("<ffffff", buf, pos, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0); pos += 24

    # -- Sequence Groups --
    pos = seqgroup_offset
    buf[pos:pos+32] = pad_string("default", 32); pos += 32
    buf[pos:pos+64] = pad_string("", 64); pos += 64
    struct.pack_into("<ii", buf, pos, 0, 0); pos += 8

    # -- Sequence Descs --
    pos = seqdesc_offset
    buf[pos:pos+32] = pad_string("idle", 32); pos += 32
    struct.pack_into("<f", buf, pos, 30.0); pos += 4  # fps
    struct.pack_into("<i", buf, pos, 0); pos += 4  # flags
    struct.pack_into("<i", buf, pos, 0); pos += 4  # activity
    struct.pack_into("<i", buf, pos, 0); pos += 4  # actweight
    struct.pack_into("<i", buf, pos, 0); pos += 4  # numevents
    struct.pack_into("<i", buf, pos, 0); pos += 4  # eventindex
    struct.pack_into("<i", buf, pos, 1); pos += 4  # numframes
    struct.pack_into("<ii", buf, pos, 0, 0); pos += 8  # unused, unused2
    struct.pack_into("<i", buf, pos, 0); pos += 4  # motiontype
    struct.pack_into("<i", buf, pos, 0); pos += 4  # motionbone
    struct.pack_into("<fff", buf, pos, 0.0, 0.0, 0.0); pos += 12  # linearmovement
    struct.pack_into("<ii", buf, pos, 0, 0); pos += 8  # unused3, unused4
    struct.pack_into("<fff", buf, pos, -1.0, -1.0, 0.0); pos += 12  # bbmin
    struct.pack_into("<fff", buf, pos, 1.0, 1.0, 2.0); pos += 12  # bbmax
    struct.pack_into("<i", buf, pos, 1); pos += 4  # numblends
    struct.pack_into("<i", buf, pos, animoffset_offset); pos += 4  # animindex
    struct.pack_into("<ii", buf, pos, 0, 0); pos += 8  # blendtype[2]
    struct.pack_into("<ff", buf, pos, 0.0, 0.0); pos += 8  # blendstart[2]
    struct.pack_into("<ff", buf, pos, 0.0, 0.0); pos += 8  # blendend[2]
    struct.pack_into("<i", buf, pos, 0); pos += 4  # unused5
    struct.pack_into("<i", buf, pos, 0); pos += 4  # seqgroup
    struct.pack_into("<ii", buf, pos, 0, 0); pos += 8  # entrynode, exitnode
    struct.pack_into("<i", buf, pos, 0); pos += 4  # nodeflags
    struct.pack_into("<i", buf, pos, 0); pos += 4  # unused6

    # -- Anim value offsets (AnimValueOffset_HL1 per bone) --
    pos = animoffset_offset
    for _ in range(num_bones):
        # offset[6] = all zeros (means use default bone values)
        for _ in range(6):
            struct.pack_into("<H", buf, pos, 0); pos += 2

    # -- Anim data --
    # Just zeros
    pos = animdata_offset
    buf[pos:pos+animdata_size] = b"\x00" * animdata_size

    # -- Bodyparts --
    pos = bodypart_offset
    buf[pos:pos+64] = pad_string("body", 64); pos += 64
    struct.pack_into("<i", buf, pos, num_models); pos += 4  # nummodels
    struct.pack_into("<i", buf, pos, 1); pos += 4  # base
    struct.pack_into("<i", buf, pos, model_offset); pos += 4  # modelindex

    # -- Models --
    pos = model_offset
    buf[pos:pos+64] = pad_string("model0", 64); pos += 64
    struct.pack_into("<i", buf, pos, 0); pos += 4  # unused
    struct.pack_into("<f", buf, pos, 0.0); pos += 4  # unused2
    struct.pack_into("<i", buf, pos, num_meshes); pos += 4  # nummesh
    struct.pack_into("<i", buf, pos, mesh_offset); pos += 4  # meshindex
    struct.pack_into("<i", buf, pos, num_verts); pos += 4  # numverts
    struct.pack_into("<i", buf, pos, vertinfo_offset); pos += 4  # vertinfoindex
    struct.pack_into("<i", buf, pos, vert_offset); pos += 4  # vertindex
    struct.pack_into("<i", buf, pos, num_norms); pos += 4  # numnorms
    struct.pack_into("<i", buf, pos, norminfo_offset); pos += 4  # norminfoindex
    struct.pack_into("<i", buf, pos, norm_offset); pos += 4  # normindex
    struct.pack_into("<ii", buf, pos, 0, 0); pos += 8  # unused3, unused4

    # -- Meshes --
    pos = mesh_offset
    struct.pack_into("<i", buf, pos, num_tris); pos += 4  # numtris
    struct.pack_into("<i", buf, pos, tricommand_offset); pos += 4  # triindex
    struct.pack_into("<i", buf, pos, 0); pos += 4  # skinref
    struct.pack_into("<i", buf, pos, num_norms); pos += 4  # numnorms
    struct.pack_into("<i", buf, pos, 0); pos += 4  # unused

    # -- Vertex bone indices --
    pos = vertinfo_offset
    for i in range(num_verts):
        buf[pos] = i % num_bones; pos += 1

    # -- Vertices (vec3_t each) --
    pos = vert_offset
    v_positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.5, 1.0, 0.0)]
    for vx, vy, vz in v_positions:
        struct.pack_into("<fff", buf, pos, vx, vy, vz); pos += 12

    # -- Normal bone indices --
    pos = norminfo_offset
    for i in range(num_norms):
        buf[pos] = i % num_bones; pos += 1

    # -- Normals (vec3_t each) --
    pos = norm_offset
    for _ in range(num_norms):
        struct.pack_into("<fff", buf, pos, 0.0, 0.0, 1.0); pos += 12

    # -- Tri commands --
    pos = tricommand_offset
    buf[pos:pos+tricommand_size] = tricommand_data

    # -- Skin refs --
    pos = skinref_offset
    buf[pos:pos+skinref_size] = skinref_data

    # -- Textures --
    pos = texture_offset
    buf[pos:pos+64] = pad_string("skin.bmp", 64); pos += 64
    struct.pack_into("<i", buf, pos, 0); pos += 4  # flags
    struct.pack_into("<i", buf, pos, tex_width); pos += 4  # width
    struct.pack_into("<i", buf, pos, tex_height); pos += 4  # height
    struct.pack_into("<i", buf, pos, texturedata_offset); pos += 4  # index

    # -- Texture data --
    pos = texturedata_offset
    buf[pos:pos+len(texdata_total)] = texdata_total

    write_bin(os.path.join(out_dir, "seed_hl1.mdl"), bytes(buf))


# ---------------------------------------------------------------------------
# MDL seed generation - Half-Life 2 format (IDST, version > 10)
# ---------------------------------------------------------------------------

def generate_mdl_hl2(out_dir):
    """Generate a minimal Half-Life 2 MDL (IDST magic, version 44).
    The HL2 importer in assimp is mostly a stub that creates empty scene,
    but we need to exercise the dispatch path."""

    # HL2 uses same IDST magic but version != 10
    # The HalfLifeMDLBaseHeader is 8 bytes: ident[4] + version(int32)
    # The InternReadFile_HL2 function is mostly a stub.
    # Minimum file size is sizeof(SequenceHeader_HL1) = 8+64+4 = 76 bytes

    buf = bytearray(80)
    struct.pack_into("<4s", buf, 0, b"IDST")
    struct.pack_into("<i", buf, 4, 44)  # version 44 (Source engine)
    buf[8:72] = pad_string("hl2_model.mdl", 64)
    struct.pack_into("<i", buf, 72, 80)  # length

    write_bin(os.path.join(out_dir, "seed_hl2.mdl"), bytes(buf))


# ---------------------------------------------------------------------------
# MDL seed generation - MDL7 format with bones and group
# ---------------------------------------------------------------------------

def generate_mdl7_bones_group(out_dir):
    """Generate a MDL7 with bones, a group, skins, and deformers.
    Exercises the MDL7 bone traversal and group parsing code paths."""

    # Header_MDL7:
    # char ident[4] = "MDL7"
    # int32 version
    # uint32 bones_num
    # uint32 groups_num
    # uint32 data_size
    # int32 entlump_size
    # int32 medlump_size
    # uint16 bone_stc_size
    # uint16 skin_stc_size
    # uint16 colorvalue_stc_size
    # uint16 material_stc_size
    # uint16 skinpoint_stc_size
    # uint16 triangle_stc_size
    # uint16 mainvertex_stc_size
    # uint16 framevertex_stc_size
    # uint16 bonetrans_stc_size
    # uint16 frame_stc_size
    # Total header: 4+4+4+4+4+4+4 + 10*2 = 48

    num_bones = 3
    num_groups = 1
    bone_stc_size = 36  # AI_MDL7_BONE_STRUCT_SIZE__NAME_IS_20_CHARS

    # Bone_MDL7: parent_index(uint16) + _unused[2] + x,y,z(float*3) + name[20]
    # = 2+2+12+20 = 36

    # Build bones data
    bones_data = b""
    bone_configs = [
        (0xFFFF, 0.0, 0.0, 0.0, "root"),
        (0, 1.0, 0.0, 0.0, "child1"),
        (0, -1.0, 0.0, 0.0, "child2"),
    ]
    for parent, x, y, z, name in bone_configs:
        bones_data += struct.pack("<H", parent)
        bones_data += b"\x00\x00"  # _unused
        bones_data += struct.pack("<fff", x, y, z)
        bones_data += pad_string(name, 20)

    # Group_MDL7: typ(1) + deformers(1) + max_weights(1) + _unused(1)
    #   + groupdata_size(4) + name[16] + numskins(4) + num_stpts(4)
    #   + numtris(4) + numverts(4) + numframes(4)
    # = 1+1+1+1+4+16+4+4+4+4+4 = 44

    num_tris = 1
    num_verts = 3
    num_stpts = 3
    num_skins = 1
    num_frames = 1

    # Calculate skin size
    # Skin_MDL7: typ(1) + _unused(3) + width(4) + height(4) + texture_name[16] = 28
    skin_stc_size = 28
    skin_width = 4
    skin_height = 4
    # Skin type 0x80 = RGB flag, actual pixel data follows
    # For type with RGB flag: width * height * 3 bytes

    # skinpoint_stc_size = 8 (TexCoord_MDL7: float u, float v)
    skinpoint_stc_size = 8

    # Triangle_MDL7: v_index[3](uint16*3=6) + skinsets[2](SkinSet_MDL7*2)
    # SkinSet_MDL7: st_index[3](uint16*3=6) + material(int32=4) = 10
    # Total triangle = 6 + 2*10 = 26
    triangle_stc_size = 26

    # Vertex_MDL7: x,y,z(float*3) + vertindex(uint16) + norm162index(uint8) [padded]
    # Actually sizeof = 16 (AI_MDL7_FRAMEVERTEX120503_STCSIZE)
    mainvertex_stc_size = 16

    # Frame_MDL7: frame_name[16] + vertices_count(4) + transmatrix_count(4) = 24
    frame_stc_size = 24

    # Material_MDL7: Diffuse(16) + Ambient(16) + Specular(16) + Emissive(16) + Power(4) = 68
    material_stc_size = 68
    colorvalue_stc_size = 16

    # BoneTransform_MDL7: m[4*4](float*16=64) + bone_index(uint16) + _unused[2] = 68
    bonetrans_stc_size = 68

    # Skin data: skin header + pixel data
    skin_header = pack_uint8(0)  # typ = 0 (no material, just skin name)
    skin_header += b"\x00\x00\x00"  # _unused
    skin_header += pack_int32(skin_width) + pack_int32(skin_height)
    skin_header += pad_string("skin0.tga", 16)
    # For type 0, no pixel data follows (just texture name reference)
    skin_total = skin_header

    # Skinpoints (UV coords)
    skinpoints = b""
    uv_values = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
    for u, v in uv_values:
        skinpoints += struct.pack("<ff", u, v)

    # Triangles
    tris = b""
    # v_index[3]
    tris += struct.pack("<HHH", 0, 1, 2)
    # skinset 0: st_index[3] + material
    tris += struct.pack("<HHH", 0, 1, 2) + pack_int32(0)
    # skinset 1: st_index[3] + material
    tris += struct.pack("<HHH", 0, 1, 2) + pack_int32(-1)

    # Vertices
    verts = b""
    vert_positions = [(0.0, 0.0, 0.0, 0), (1.0, 0.0, 0.0, 0), (0.5, 1.0, 0.0, 1)]
    for x, y, z, bi in vert_positions:
        verts += struct.pack("<fff", x, y, z)
        verts += struct.pack("<H", bi)
        verts += pack_uint8(0)  # norm162index
        verts += b"\x00"  # pad to 16

    # Frame
    frame_header = pad_string("frame0", 16)
    frame_header += pack_uint32(num_verts)
    frame_header += pack_uint32(0)  # transmatrix_count

    # Group data = skins + skinpoints + triangles + vertices + frames
    group_inner = skin_total + skinpoints + tris + verts + frame_header + verts
    group_data_size = 44 + len(group_inner)  # include group header itself

    # Group header
    group_header = pack_uint8(1)  # typ = 1 (triangle based)
    group_header += struct.pack("<bbb", 0, 0, 0)  # deformers, max_weights, _unused
    group_header += pack_int32(group_data_size)
    group_header += pad_string("group0", 16)
    group_header += pack_int32(num_skins)
    group_header += pack_int32(num_stpts)
    group_header += pack_int32(num_tris)
    group_header += pack_int32(num_verts)
    group_header += pack_int32(num_frames)

    # Full file data
    data_after_header = bones_data + group_header + group_inner
    data_size = len(data_after_header)

    # MDL7 header
    header = struct.pack("<4s", b"MDL7")
    header += pack_int32(1)  # version
    header += pack_uint32(num_bones)
    header += pack_uint32(num_groups)
    header += pack_uint32(data_size)
    header += pack_int32(0)  # entlump_size
    header += pack_int32(0)  # medlump_size
    header += pack_uint16(bone_stc_size)
    header += pack_uint16(skin_stc_size)
    header += pack_uint16(colorvalue_stc_size)
    header += pack_uint16(material_stc_size)
    header += pack_uint16(skinpoint_stc_size)
    header += pack_uint16(triangle_stc_size)
    header += pack_uint16(mainvertex_stc_size)
    header += pack_uint16(16)  # framevertex_stc_size
    header += pack_uint16(bonetrans_stc_size)
    header += pack_uint16(frame_stc_size)

    full_data = header + data_after_header
    write_bin(os.path.join(out_dir, "seed_mdl7_full.mdl"), full_data)


# ---------------------------------------------------------------------------
# MDL seed generation - Quake1 with group skin
# ---------------------------------------------------------------------------

def generate_mdl_quake1_groupskin(out_dir):
    """Generate a Quake 1 MDL with a group skin (skin group = 1).

    For Quake1 group skins, the parser reads:
      szCurrent += sizeof(uint32_t) * 2  (group + nb)
      CreateTextureARGB8_3DGS_MDL3(szCurrent + iNumImages * sizeof(float))
      szCurrent += skinheight * skinwidth + sizeof(float) * iNumImages

    So the skin block after the 2 uint32s is:
      times[nb] (float each) + pixel_data (skinw * skinh bytes)

    NOTE: The code only advances past ONE image worth of pixels,
    even though there are nb images. This is how the original code works.
    The file must be large enough so that VALIDATE_FILE_SIZE passes.
    """

    num_verts = 3
    num_tris = 1
    skinwidth = 4
    skinheight = 4
    num_images = 2

    header = b""
    header += struct.pack("<4s", b"IDPO")
    header += pack_int32(6)
    header += pack_float(1.0) * 3
    header += pack_float(0.0) * 3
    header += pack_float(5.0)
    header += pack_float(0.0) * 3
    header += pack_int32(1)  # num_skins
    header += pack_int32(skinwidth)
    header += pack_int32(skinheight)
    header += pack_int32(num_verts)
    header += pack_int32(num_tris)
    header += pack_int32(1)  # num_frames
    header += pack_int32(0)
    header += pack_int32(0)
    header += pack_float(0.0)

    # Group skin layout:
    #   int32 group=1, int32 nb=num_images
    #   float times[num_images]
    #   uint8 pixel_data[skinwidth * skinheight]  (for first image - CreateTexture reads this)
    # After the group skin block, the code advances szCurrent by:
    #   skinheight * skinwidth + sizeof(float) * num_images
    skin_data = pack_int32(1)  # group = 1 (group skin)
    skin_data += pack_int32(num_images)  # nb
    # times
    for i in range(num_images):
        skin_data += pack_float(float(i) * 0.5)
    # pixel data (palettized 8-bit, skinw * skinh for the one image the parser reads)
    skin_data += bytes([i % 256 for i in range(skinwidth * skinheight)])

    # TexCoord (12 bytes each: onseam, s, t)
    texcoords = b""
    for i in range(num_verts):
        texcoords += pack_int32(0) + pack_int32(i) + pack_int32(i)

    # Triangle (16 bytes each: facesfront, vertex[3])
    triangles = pack_int32(1) + pack_int32(0) + pack_int32(1) + pack_int32(2)

    # Frame: type=0, SimpleFrame
    frame = pack_int32(0)
    frame += pack_uint8(0) * 4 + pack_uint8(50) * 3 + pack_uint8(0)
    frame += pad_string("f0", 16)
    for vx, vy, vz in [(10, 0, 0), (0, 10, 0), (5, 5, 10)]:
        frame += pack_uint8(vx) + pack_uint8(vy) + pack_uint8(vz) + pack_uint8(0)

    # Add padding at the end to ensure VALIDATE_FILE_SIZE checks pass
    padding = b"\x00" * 64

    data = header + skin_data + texcoords + triangles + frame + padding
    write_bin(os.path.join(out_dir, "seed_quake1_groupskin.mdl"), data)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    smd_dir = os.path.join(base, "test", "models", "SMD", "fuzz_seeds")
    ase_dir = os.path.join(base, "test", "models", "ASE", "fuzz_seeds")
    mdl_dir = os.path.join(base, "test", "models", "MDL", "fuzz_seeds")

    print("=== Generating remaining fuzz seeds ===\n")

    generate_smd_seeds(smd_dir)
    print()
    generate_ase_seeds(ase_dir)
    print()

    print(f"Generating MDL seeds in {mdl_dir}")
    ensure_dir(mdl_dir)
    generate_mdl_quake1(mdl_dir)
    generate_mdl_quake1_groupframe(mdl_dir)
    generate_mdl_quake1_groupskin(mdl_dir)
    generate_mdl_gs3(mdl_dir)
    generate_mdl_gs4(mdl_dir)
    generate_mdl_gs5(mdl_dir)
    generate_mdl_gs4_argb4(mdl_dir)
    generate_mdl7_bones_group(mdl_dir)
    generate_mdl_hl1(mdl_dir)
    generate_mdl_hl2(mdl_dir)

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
