#!/usr/bin/env python3
"""Generate binary seed files for the OBJ+MTL fuzzer.

Each seed is a binary blob:
  [uint16_t split_offset][OBJ content bytes][MTL content bytes]

The split_offset (little-endian) tells the fuzzer where the MTL content
starts within the blob.  The OBJ content occupies bytes [2, split_offset)
and the MTL content occupies bytes [split_offset, end).

Note: The fuzzer automatically prepends 'mtllib <name>.mtl\\n' to the OBJ
content, so the OBJ seeds here should NOT include a mtllib directive.
"""

import os
import struct

SEED_DIR = os.path.join(os.path.dirname(__file__),
                        "..", "test", "models", "OBJ", "fuzz_seeds")

# ---------------------------------------------------------------------------
# Seed 1: Basic OBJ + MTL  (cube with simple Phong material)
# ---------------------------------------------------------------------------

OBJ_BASIC = """\
# Basic cube
usemtl BasicMat
o Cube
v -1.0 -1.0  1.0
v  1.0 -1.0  1.0
v  1.0  1.0  1.0
v -1.0  1.0  1.0
v -1.0 -1.0 -1.0
v  1.0 -1.0 -1.0
v  1.0  1.0 -1.0
v -1.0  1.0 -1.0
vn  0.0  0.0  1.0
vn  0.0  0.0 -1.0
vn  1.0  0.0  0.0
vn -1.0  0.0  0.0
vn  0.0  1.0  0.0
vn  0.0 -1.0  0.0
vt 0.0 0.0
vt 1.0 0.0
vt 1.0 1.0
vt 0.0 1.0
f 1/1/1 2/2/1 3/3/1 4/4/1
f 5/1/2 8/2/2 7/3/2 6/4/2
f 2/1/3 6/2/3 7/3/3 3/4/3
f 1/1/4 4/2/4 8/3/4 5/4/4
f 4/1/5 3/2/5 7/3/5 8/4/5
f 1/1/6 5/2/6 6/3/6 2/4/6
"""

MTL_BASIC = """\
newmtl BasicMat
Kd 0.8 0.2 0.1
Ks 1.0 1.0 1.0
Ns 100.0
d 0.95
illum 2
"""

# ---------------------------------------------------------------------------
# Seed 2: Rich OBJ + MTL  (exercises every MTL parser branch)
# ---------------------------------------------------------------------------

OBJ_RICH = """\
# Rich OBJ with multiple groups, objects, materials, smoothing, and all vertex types
o RichObject
g Group1
s 1
usemtl RichMat1
v -1.0 -1.0  1.0
v  1.0 -1.0  1.0
v  1.0  1.0  1.0
v -1.0  1.0  1.0
v -1.0 -1.0 -1.0
v  1.0 -1.0 -1.0
v  1.0  1.0 -1.0
v -1.0  1.0 -1.0
vn  0.0  0.0  1.0
vn  0.0  0.0 -1.0
vn  1.0  0.0  0.0
vn -1.0  0.0  0.0
vn  0.0  1.0  0.0
vn  0.0 -1.0  0.0
vt 0.0 0.0
vt 1.0 0.0
vt 1.0 1.0
vt 0.0 1.0
vt 0.5 0.5
f 1/1/1 2/2/1 3/3/1 4/4/1
f 5/1/2 8/2/2 7/3/2 6/4/2
g Group2
s 2
usemtl RichMat2
f 2/1/3 6/2/3 7/3/3 3/4/3
f 1/1/4 4/2/4 8/3/4 5/4/4
g Group3
s off
usemtl RichMat3
f 4/1/5 3/2/5 7/3/5 8/4/5
f 1/1/6 5/2/6 6/3/6 2/4/6
# Lines and points to exercise SortByPType
l 1 2 3 4
p 1 2 3
"""

MTL_RICH = """\
# Rich material library exercising all ObjFileMtlImporter branches

# Material 1: Full traditional + PBR properties
newmtl RichMat1
Ka 0.2 0.2 0.2
Kd 0.8 0.2 0.1
Ks 1.0 1.0 1.0
Ke 0.1 0.05 0.0
Ns 100.0
Ni 1.5
d 0.9
Tr 0.1
Tf 0.5 0.5 0.5
illum 2
Pm 0.5
Pr 0.3
Ps 0.1 0.2 0.3
Pc 0.8
Pcr 0.5
Pct 0.3
aniso 0.5
anisor 0.3
map_Kd texture_diffuse.png
map_Ka texture_ambient.png
map_Ks texture_specular.png
map_Ns texture_shininess.png
map_d texture_alpha.png
map_Ke texture_emissive.png
bump bump_map.png
map_bump -bm 2.5 bump_map2.png
map_Kn normal_v1.png
norm normal_v2.png
disp displacement.png
map_disp displacement2.png
map_Pm metallic.png
map_Pr roughness.png
map_Ps sheen.png
refl -type sphere env_sphere.png

# Material 2: Texture options - exercises getTextureOption branches
newmtl RichMat2
Kd 0.1 0.8 0.2
Ks 0.5 0.5 0.5
Ns 50.0
d 1.0
illum 5
map_Kd -s 2.0 2.0 1.0 -o 0.5 0.0 0.0 -t 0.1 0.1 0.1 tiled_diffuse.png
map_Ks -blendu on -blendv on -boost 2.0 specular_opts.png
map_bump -bm 3.0 -clamp on -mm 0 1 bump_clamped.png
map_d -texres 512 -imfchan r opacity_opts.png
refl -type cube_top cube_top.png
refl -type cube_bottom cube_bottom.png
refl -type cube_front cube_front.png
refl -type cube_back cube_back.png
refl -type cube_left cube_left.png
refl -type cube_right cube_right.png

# Material 3: Disney/PBR keywords (lowercase branch coverage)
newmtl RichMat3
Kd 0.5 0.5 0.5
d 1.0
illum 2
roughness 0.4
metallic 0.8
subsurface 0.1
specularTint 0.2
sheen 0.15
sheenTint 0.3
clearcoat 0.5
clearcoatGloss 0.8
ao 0.95
map_emissive emissive_alt.png
"""


def write_seed(obj_text: str, mtl_text: str, filename: str) -> None:
    """Pack OBJ + MTL into a binary seed with a 2-byte split header."""
    obj_bytes = obj_text.encode("utf-8")
    mtl_bytes = mtl_text.encode("utf-8")

    # split_offset = 2 (header size) + len(obj_bytes)
    split_offset = 2 + len(obj_bytes)
    if split_offset > 0xFFFF:
        raise ValueError(f"OBJ content too large for uint16 offset: {split_offset}")

    header = struct.pack("<H", split_offset)
    blob = header + obj_bytes + mtl_bytes

    path = os.path.join(SEED_DIR, filename)
    with open(path, "wb") as f:
        f.write(blob)
    print(f"  Wrote {path} ({len(blob)} bytes, split@{split_offset})")


def main():
    os.makedirs(SEED_DIR, exist_ok=True)
    print("Generating OBJ+MTL fuzz seeds:")
    write_seed(OBJ_BASIC, MTL_BASIC, "seed_obj_mtl_basic.bin")
    write_seed(OBJ_RICH, MTL_RICH, "seed_obj_mtl_rich.bin")
    print("Done.")


if __name__ == "__main__":
    main()
