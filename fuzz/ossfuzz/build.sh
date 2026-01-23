#!/bin/bash -eu

# Build directory
mkdir -p build
cd build

# Configure
cmake .. \
  -G Ninja \
  -DCMAKE_C_COMPILER="${CC}" \
  -DCMAKE_CXX_COMPILER="${CXX}" \
  -DCMAKE_C_FLAGS="${CFLAGS}" \
  -DCMAKE_CXX_FLAGS="${CXXFLAGS}" \
  -DASSIMP_BUILD_ZLIB=ON \
  -DASSIMP_BUILD_TESTS=OFF \
  -DASSIMP_BUILD_ASSIMP_TOOLS=OFF \
  -DBUILD_SHARED_LIBS=OFF \
  -DASSIMP_BUILD_ALL_IMPORTERS_BY_DEFAULT=ON \
  -DASSIMP_BUILD_ALL_EXPORTERS_BY_DEFAULT=ON

# Build the library
ninja

# Helper function to build fuzzers
build_fuzzer() {
    local fuzzer_name=$1
    local source_file=$2

    echo "Building $fuzzer_name..."
    $CXX $CXXFLAGS -I../include -I../build/include -c "$source_file" -o "${fuzzer_name}.o"

    $CXX $CXXFLAGS $LIB_FUZZING_ENGINE "${fuzzer_name}.o" -o "$OUT/${fuzzer_name}" \
        ./lib/libassimp.a \
        ./contrib/zlib/libzlibstatic.a \
        -lpthread -ldl
}

# Helper function to build corpus from test/models subdirectory
build_corpus() {
    local fuzzer_name=$1
    local model_dir=$2
    local dict_name=${3:-assimp_fuzzer}  # Optional format-specific dict

    mkdir -p "${fuzzer_name}_corpus"

    # Copy from test/models
    if [ -d "../test/models/$model_dir" ]; then
        cp -r "../test/models/$model_dir"/* "${fuzzer_name}_corpus/" 2>/dev/null || true
    fi

    # Also copy from test/models-nonbsd (additional test files)
    if [ -d "../test/models-nonbsd/$model_dir" ]; then
        cp -r "../test/models-nonbsd/$model_dir"/* "${fuzzer_name}_corpus/" 2>/dev/null || true
    fi

    # Create corpus zip if we have files
    if [ -d "${fuzzer_name}_corpus" ] && [ "$(ls -A ${fuzzer_name}_corpus 2>/dev/null)" ]; then
        (cd "${fuzzer_name}_corpus" && zip -q -r "$OUT/${fuzzer_name}_seed_corpus.zip" .)
    fi
    rm -rf "${fuzzer_name}_corpus"

    # Use format-specific dict if available, otherwise generic
    if [ -f "../fuzz/${dict_name}.dict" ]; then
        cp "../fuzz/${dict_name}.dict" "$OUT/${fuzzer_name}.dict"
    else
        cp ../fuzz/assimp_fuzzer.dict "$OUT/${fuzzer_name}.dict" || true
    fi
}

# =============================================================================
# Generic Fuzzer (all formats)
# =============================================================================
build_fuzzer "assimp_fuzzer" "../fuzz/assimp_fuzzer.cc"
(cd ../test/models && zip -q -r $OUT/assimp_fuzzer_seed_corpus.zip .)
cp ../fuzz/assimp_fuzzer.dict $OUT/assimp_fuzzer.dict || true

# =============================================================================
# Tier 1: High Impact Formats (>3,000 lines of parser code)
# =============================================================================

# IFC - Industry Foundation Classes (17,391 lines)
build_fuzzer "assimp_fuzzer_ifc" "../fuzz/assimp_fuzzer_ifc.cc"
build_corpus "assimp_fuzzer_ifc" "IFC" "ifc"

# X3D - Extensible 3D (6,546 lines)
build_fuzzer "assimp_fuzzer_x3d" "../fuzz/assimp_fuzzer_x3d.cc"
build_corpus "assimp_fuzzer_x3d" "X3D"

# MDL - Quake/Half-Life models (4,367 lines)
build_fuzzer "assimp_fuzzer_mdl" "../fuzz/assimp_fuzzer_mdl.cc"
build_corpus "assimp_fuzzer_mdl" "MDL" "mdl"

# LWO - LightWave Object (3,803 lines)
build_fuzzer "assimp_fuzzer_lwo" "../fuzz/assimp_fuzzer_lwo.cc"
build_corpus "assimp_fuzzer_lwo" "LWO"

# Blender (3,782 lines)
build_fuzzer "assimp_fuzzer_blend" "../fuzz/assimp_fuzzer_blend.cc"
build_corpus "assimp_fuzzer_blend" "BLEND" "blend"

# Ogre - Ogre3D mesh XML format (3,443 lines)
build_fuzzer "assimp_fuzzer_ogre" "../fuzz/assimp_fuzzer_ogre.cc"
build_corpus "assimp_fuzzer_ogre" "Ogre"

# Ogre - Ogre3D binary mesh format
build_fuzzer "assimp_fuzzer_ogre_binary" "../fuzz/assimp_fuzzer_ogre_binary.cc"
build_corpus "assimp_fuzzer_ogre_binary" "Ogre"

# ASE - 3ds Max ASCII Scene Export (3,202 lines)
build_fuzzer "assimp_fuzzer_ase" "../fuzz/assimp_fuzzer_ase.cc"
build_corpus "assimp_fuzzer_ase" "ASE"

# 3DS - 3ds Max binary (2,729 lines)
build_fuzzer "assimp_fuzzer_3ds" "../fuzz/assimp_fuzzer_3ds.cc"
build_corpus "assimp_fuzzer_3ds" "3DS" "3ds"

# FBX (13,021 lines) - already existed
build_fuzzer "assimp_fuzzer_fbx" "../fuzz/assimp_fuzzer_fbx.cc"
build_corpus "assimp_fuzzer_fbx" "FBX" "fbx"

# Collada (6,150 lines) - already existed
build_fuzzer "assimp_fuzzer_collada" "../fuzz/assimp_fuzzer_collada.cc"
build_corpus "assimp_fuzzer_collada" "Collada" "collada"

# glTF2 (3,491 lines) - already existed
build_fuzzer "assimp_fuzzer_gltf" "../fuzz/assimp_fuzzer_gltf.cc"
mkdir -p gltf_corpus
[ -d "../test/models/glTF" ] && cp -r ../test/models/glTF/* gltf_corpus/ || true
[ -d "../test/models/glTF2" ] && cp -r ../test/models/glTF2/* gltf_corpus/ || true
if [ -d "gltf_corpus" ] && [ "$(ls -A gltf_corpus 2>/dev/null)" ]; then
    (cd gltf_corpus && zip -q -r $OUT/assimp_fuzzer_gltf_seed_corpus.zip .)
fi
rm -rf gltf_corpus
cp ../fuzz/glb.dict $OUT/assimp_fuzzer_gltf.dict || cp ../fuzz/assimp_fuzzer.dict $OUT/assimp_fuzzer_gltf.dict || true

# GLB - binary glTF - already existed
build_fuzzer "assimp_fuzzer_glb" "../fuzz/assimp_fuzzer_glb.cc"
mkdir -p glb_corpus
[ -d "../test/models/glTF" ] && find ../test/models/glTF -name "*.glb" -exec cp {} glb_corpus/ \; 2>/dev/null || true
[ -d "../test/models/glTF2" ] && find ../test/models/glTF2 -name "*.glb" -exec cp {} glb_corpus/ \; 2>/dev/null || true
if [ -d "glb_corpus" ] && [ "$(ls -A glb_corpus 2>/dev/null)" ]; then
    (cd glb_corpus && zip -q -r $OUT/assimp_fuzzer_glb_seed_corpus.zip .)
fi
rm -rf glb_corpus
cp ../fuzz/glb.dict $OUT/assimp_fuzzer_glb.dict || cp ../fuzz/assimp_fuzzer.dict $OUT/assimp_fuzzer_glb.dict || true

# OBJ (2,770 lines) - already existed
build_fuzzer "assimp_fuzzer_obj" "../fuzz/assimp_fuzzer_obj.cc"
build_corpus "assimp_fuzzer_obj" "OBJ" "obj"

# STL (807 lines) - already existed
build_fuzzer "assimp_fuzzer_stl" "../fuzz/assimp_fuzzer_stl.cc"
build_corpus "assimp_fuzzer_stl" "STL"

# =============================================================================
# Tier 2: Medium Impact Formats (1,000-3,000 lines)
# =============================================================================

# X - DirectX (2,587 lines)
build_fuzzer "assimp_fuzzer_x" "../fuzz/assimp_fuzzer_x.cc"
build_corpus "assimp_fuzzer_x" "X"

# PLY - Stanford Polygon (2,293 lines)
build_fuzzer "assimp_fuzzer_ply" "../fuzz/assimp_fuzzer_ply.cc"
build_corpus "assimp_fuzzer_ply" "PLY"

# IRR - Irrlicht (2,261 lines)
build_fuzzer "assimp_fuzzer_irr" "../fuzz/assimp_fuzzer_irr.cc"
build_corpus "assimp_fuzzer_irr" "IRR"

# AMF - Additive Manufacturing (2,002 lines)
build_fuzzer "assimp_fuzzer_amf" "../fuzz/assimp_fuzzer_amf.cc"
build_corpus "assimp_fuzzer_amf" "AMF"

# Assbin - Assimp binary (1,642 lines) - no sample files in repo
build_fuzzer "assimp_fuzzer_assbin" "../fuzz/assimp_fuzzer_assbin.cc"
build_corpus "assimp_fuzzer_assbin" "Assbin"  # Will start without seed corpus

# 3MF - 3D Manufacturing Format (1,507 lines)
build_fuzzer "assimp_fuzzer_3mf" "../fuzz/assimp_fuzzer_3mf.cc"
build_corpus "assimp_fuzzer_3mf" "3MF"

# M3D - Model 3D (1,381 lines)
build_fuzzer "assimp_fuzzer_m3d" "../fuzz/assimp_fuzzer_m3d.cc"
build_corpus "assimp_fuzzer_m3d" "M3D"

# OpenGEX (1,378 lines)
build_fuzzer "assimp_fuzzer_ogex" "../fuzz/assimp_fuzzer_ogex.cc"
build_corpus "assimp_fuzzer_ogex" "OpenGEX"

# USD - Universal Scene Description (1,278 lines)
build_fuzzer "assimp_fuzzer_usd" "../fuzz/assimp_fuzzer_usd.cc"
build_corpus "assimp_fuzzer_usd" "USD"

# MD5 - Doom 3/Quake 4 (1,276 lines)
build_fuzzer "assimp_fuzzer_md5" "../fuzz/assimp_fuzzer_md5.cc"
build_corpus "assimp_fuzzer_md5" "MD5"

# COB - TrueSpace (1,191 lines)
build_fuzzer "assimp_fuzzer_cob" "../fuzz/assimp_fuzzer_cob.cc"
build_corpus "assimp_fuzzer_cob" "COB"

# NFF - Neutral File Format (1,158 lines)
build_fuzzer "assimp_fuzzer_nff" "../fuzz/assimp_fuzzer_nff.cc"
build_corpus "assimp_fuzzer_nff" "NFF"

# DXF - AutoCAD (1,147 lines)
build_fuzzer "assimp_fuzzer_dxf" "../fuzz/assimp_fuzzer_dxf.cc"
build_corpus "assimp_fuzzer_dxf" "DXF"

# SMD - Valve Studiomdl (1,085 lines)
build_fuzzer "assimp_fuzzer_smd" "../fuzz/assimp_fuzzer_smd.cc"
build_corpus "assimp_fuzzer_smd" "SMD"

# MD3 - Quake 3 (1,071 lines) - no sample files in repo
build_fuzzer "assimp_fuzzer_md3" "../fuzz/assimp_fuzzer_md3.cc"
build_corpus "assimp_fuzzer_md3" "MD3"  # Will start without seed corpus

# MMD - MikuMikuDance (956 lines) - no sample files in repo
build_fuzzer "assimp_fuzzer_mmd" "../fuzz/assimp_fuzzer_mmd.cc"
build_corpus "assimp_fuzzer_mmd" "MMD"  # Will start without seed corpus

# Q3BSP - Quake 3 BSP (955 lines) - no sample files in repo
build_fuzzer "assimp_fuzzer_q3bsp" "../fuzz/assimp_fuzzer_q3bsp.cc"
build_corpus "assimp_fuzzer_q3bsp" "Q3BSP"  # Will start without seed corpus

# =============================================================================
# Tier 3: Lower Impact Formats (<1,000 lines)
# =============================================================================

# LWS - LightWave Scene (944 lines)
build_fuzzer "assimp_fuzzer_lws" "../fuzz/assimp_fuzzer_lws.cc"
build_corpus "assimp_fuzzer_lws" "LWS"

# AC - AC3D (896 lines)
build_fuzzer "assimp_fuzzer_ac" "../fuzz/assimp_fuzzer_ac.cc"
build_corpus "assimp_fuzzer_ac" "AC"

# SIB - Silo (875 lines)
build_fuzzer "assimp_fuzzer_sib" "../fuzz/assimp_fuzzer_sib.cc"
build_corpus "assimp_fuzzer_sib" "SIB"

# XGL (805 lines)
build_fuzzer "assimp_fuzzer_xgl" "../fuzz/assimp_fuzzer_xgl.cc"
build_corpus "assimp_fuzzer_xgl" "XGL"

# B3D - BlitzBasic 3D (743 lines)
build_fuzzer "assimp_fuzzer_b3d" "../fuzz/assimp_fuzzer_b3d.cc"
build_corpus "assimp_fuzzer_b3d" "B3D"

# MS3D - MilkShape 3D (649 lines)
build_fuzzer "assimp_fuzzer_ms3d" "../fuzz/assimp_fuzzer_ms3d.cc"
build_corpus "assimp_fuzzer_ms3d" "MS3D"

# Q3D - Quick3D (591 lines)
build_fuzzer "assimp_fuzzer_q3d" "../fuzz/assimp_fuzzer_q3d.cc"
build_corpus "assimp_fuzzer_q3d" "Q3D"

# BVH - Biovision Hierarchy (524 lines)
build_fuzzer "assimp_fuzzer_bvh" "../fuzz/assimp_fuzzer_bvh.cc"
build_corpus "assimp_fuzzer_bvh" "BVH"

# Unreal (517 lines) - uses .3d extension, samples in 3D directory
build_fuzzer "assimp_fuzzer_unreal" "../fuzz/assimp_fuzzer_unreal.cc"
build_corpus "assimp_fuzzer_unreal" "3D"

# HMP - 3D GameStudio (506 lines)
build_fuzzer "assimp_fuzzer_hmp" "../fuzz/assimp_fuzzer_hmp.cc"
build_corpus "assimp_fuzzer_hmp" "HMP"

# MDC - Return to Castle Wolfenstein (469 lines)
build_fuzzer "assimp_fuzzer_mdc" "../fuzz/assimp_fuzzer_mdc.cc"
build_corpus "assimp_fuzzer_mdc" "MDC"

# MD2 - Quake 2 (447 lines)
build_fuzzer "assimp_fuzzer_md2" "../fuzz/assimp_fuzzer_md2.cc"
build_corpus "assimp_fuzzer_md2" "MD2"

# OFF - Object File Format (329 lines)
build_fuzzer "assimp_fuzzer_off" "../fuzz/assimp_fuzzer_off.cc"
build_corpus "assimp_fuzzer_off" "OFF"

# IQM - Inter-Quake Model (314 lines)
build_fuzzer "assimp_fuzzer_iqm" "../fuzz/assimp_fuzzer_iqm.cc"
build_corpus "assimp_fuzzer_iqm" "IQM"

# NDO - Izware Nendo (313 lines) - no sample files in repo
build_fuzzer "assimp_fuzzer_ndo" "../fuzz/assimp_fuzzer_ndo.cc"
build_corpus "assimp_fuzzer_ndo" "NDO"  # Will start without seed corpus

# CSM - CharacterStudio Motion (304 lines)
build_fuzzer "assimp_fuzzer_csm" "../fuzz/assimp_fuzzer_csm.cc"
build_corpus "assimp_fuzzer_csm" "CSM"

# RAW - Raw Triangles (293 lines)
build_fuzzer "assimp_fuzzer_raw" "../fuzz/assimp_fuzzer_raw.cc"
build_corpus "assimp_fuzzer_raw" "RAW"

# Terragen (245 lines) - samples in TER directory
build_fuzzer "assimp_fuzzer_ter" "../fuzz/assimp_fuzzer_ter.cc"
build_corpus "assimp_fuzzer_ter" "TER"

# =============================================================================
# Export Fuzzers (roundtrip: import -> export -> import)
# =============================================================================

# OBJ Exporter
build_fuzzer "assimp_fuzzer_export_obj" "../fuzz/assimp_fuzzer_export_obj.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_obj_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/obj.dict "$OUT/assimp_fuzzer_export_obj.dict" 2>/dev/null || cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_obj.dict" || true

# Collada Exporter
build_fuzzer "assimp_fuzzer_export_collada" "../fuzz/assimp_fuzzer_export_collada.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_collada_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/collada.dict "$OUT/assimp_fuzzer_export_collada.dict" 2>/dev/null || cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_collada.dict" || true

# STL Exporter
build_fuzzer "assimp_fuzzer_export_stl" "../fuzz/assimp_fuzzer_export_stl.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_stl_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_stl.dict" || true

# PLY Exporter
build_fuzzer "assimp_fuzzer_export_ply" "../fuzz/assimp_fuzzer_export_ply.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_ply_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_ply.dict" || true

# 3DS Exporter
build_fuzzer "assimp_fuzzer_export_3ds" "../fuzz/assimp_fuzzer_export_3ds.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_3ds_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/3ds.dict "$OUT/assimp_fuzzer_export_3ds.dict" 2>/dev/null || cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_3ds.dict" || true

# glTF2 Exporter
build_fuzzer "assimp_fuzzer_export_gltf2" "../fuzz/assimp_fuzzer_export_gltf2.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_gltf2_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/glb.dict "$OUT/assimp_fuzzer_export_gltf2.dict" 2>/dev/null || cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_gltf2.dict" || true

# GLB2 Exporter
build_fuzzer "assimp_fuzzer_export_glb2" "../fuzz/assimp_fuzzer_export_glb2.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_glb2_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/glb.dict "$OUT/assimp_fuzzer_export_glb2.dict" 2>/dev/null || cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_glb2.dict" || true

# FBX Exporter
build_fuzzer "assimp_fuzzer_export_fbx" "../fuzz/assimp_fuzzer_export_fbx.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_fbx_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/fbx.dict "$OUT/assimp_fuzzer_export_fbx.dict" 2>/dev/null || cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_fbx.dict" || true

# X Exporter
build_fuzzer "assimp_fuzzer_export_x" "../fuzz/assimp_fuzzer_export_x.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_x_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_x.dict" || true

# 3MF Exporter
build_fuzzer "assimp_fuzzer_export_3mf" "../fuzz/assimp_fuzzer_export_3mf.cc"
cp "$OUT/assimp_fuzzer_seed_corpus.zip" "$OUT/assimp_fuzzer_export_3mf_seed_corpus.zip" 2>/dev/null || true
cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_export_3mf.dict" || true

echo ""
echo "=========================================="
echo "Built $(ls $OUT/assimp_fuzzer_* 2>/dev/null | grep -v seed_corpus | grep -v '.dict' | wc -l) fuzzers"
echo "=========================================="
