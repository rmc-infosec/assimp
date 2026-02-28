#!/bin/bash -eu

# Build directory
if [ -f build/CMakeCache.txt ]; then
    cache_src_dir=$(grep -E '^CMAKE_HOME_DIRECTORY:' build/CMakeCache.txt | cut -d= -f2- || true)
    if [ -n "$cache_src_dir" ] && [ "$cache_src_dir" != "$(pwd)" ]; then
        echo "CMake cache source mismatch ($cache_src_dir != $(pwd)); clearing build dir"
        rm -rf build
    fi
fi
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
  -DASSIMP_BUILD_ALL_EXPORTERS_BY_DEFAULT=ON \
  -DASSIMP_BUILD_VRML_IMPORTER=OFF

# Build the library
ninja

# Helper function to build fuzzers
build_fuzzer() {
    local fuzzer_name=$1
    local source_file=$2

    if should_skip_fuzzer "$fuzzer_name"; then
        echo "Skipping $fuzzer_name (disabled)"
        return 0
    fi

    echo "Building $fuzzer_name..."
    $CXX $CXXFLAGS -I../include -I../build/include -I.. -c "$source_file" -o "${fuzzer_name}.o"

    $CXX $CXXFLAGS $LIB_FUZZING_ENGINE "${fuzzer_name}.o" -o "$OUT/${fuzzer_name}" \
        ./lib/libassimp.a \
        ./contrib/zlib/libzlibstatic.a \
        -lpthread -ldl
}

# Copy corpus tree while skipping reference image directories.
copy_corpus_tree() {
    local src_dir=$1
    local dest_dir=$2

    if [ -d "$src_dir" ]; then
        if command -v rsync >/dev/null 2>&1; then
            rsync -a \
                --exclude 'ref/' \
                --exclude 'ref/**' \
                --exclude 'ReferenceImages/' \
                --exclude 'ReferenceImages/**' \
                --exclude 'screenshots/' \
                --exclude 'screenshots/**' \
                "$src_dir"/ "$dest_dir"/
        else
            (cd "$src_dir" && tar -cf - \
                --exclude './ref' \
                --exclude './ref/**' \
                --exclude './ReferenceImages' \
                --exclude './ReferenceImages/**' \
                --exclude './screenshots' \
                --exclude './screenshots/**' \
                .) | (cd "$dest_dir" && tar -xf -)
        fi
    fi
}

# Helper function to build corpus from test/models subdirectory
build_corpus() {
    local fuzzer_name=$1
    local model_dir=$2
    local dict_name=${3:-assimp_fuzzer}  # Optional format-specific dict

    if should_skip_fuzzer "$fuzzer_name"; then
        return 0
    fi

    mkdir -p "${fuzzer_name}_corpus"

    # Copy from test/models
    copy_corpus_tree "../test/models/$model_dir" "${fuzzer_name}_corpus"

    # Also copy from test/models-nonbsd (additional test files)
    copy_corpus_tree "../test/models-nonbsd/$model_dir" "${fuzzer_name}_corpus"

    # Flatten subdirectories so all files are at top level in corpus.
    # Fuzzers only read top-level files from corpus dirs.
    if [ -d "${fuzzer_name}_corpus" ]; then
        # Use a standalone script to avoid issues with set -e in main script
        python3 -c "
import os, shutil, sys
corpus = sys.argv[1]
for root, dirs, files in os.walk(corpus):
    if root == corpus:
        continue
    for f in files:
        src = os.path.join(root, f)
        dst = os.path.join(corpus, f)
        if os.path.exists(dst):
            parent = os.path.basename(root)
            dst = os.path.join(corpus, parent + '_' + f)
        try:
            shutil.move(src, dst)
        except:
            pass
# Remove empty dirs
for root, dirs, files in os.walk(corpus, topdown=False):
    if root != corpus:
        try:
            os.rmdir(root)
        except:
            pass
" "${fuzzer_name}_corpus"
    fi

    # Create corpus zip if we have files
    if [ -d "${fuzzer_name}_corpus" ] && [ ! "$(ls -A ${fuzzer_name}_corpus 2>/dev/null)" ]; then
        # Keep a placeholder so coverage runs don't fail on missing corpora.
        printf '\0' > "${fuzzer_name}_corpus/.empty"
    fi
    # Remove any old zip first (zip -r updates rather than replaces)
    rm -f "$OUT/${fuzzer_name}_seed_corpus.zip"
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

# Copy per-fuzzer libFuzzer options into $OUT (e.g., rss_limit_mb overrides).
copy_fuzzer_options() {
    if compgen -G "../fuzz/ossfuzz/*.options" > /dev/null; then
        cp ../fuzz/ossfuzz/*.options "$OUT"/
    fi
}

# For coverage builds, copy sources into $OUT so llvm-cov can resolve paths.
if [ "${SANITIZER:-}" = "coverage" ]; then
    mkdir -p "$OUT/src/assimp"
    rsync -a --delete \
        --exclude .git \
        --exclude .venv \
        --exclude .lake \
        --exclude build \
        --exclude build_* \
        --exclude oss-fuzz-test \
        /src/assimp/ "$OUT/src/assimp/"
fi

# Fuzzers disabled due to known blockers (see ROADMAP.md).
DISABLED_FUZZERS=(
)

# Remove any stale binaries for disabled fuzzers from previous builds.
for disabled in "${DISABLED_FUZZERS[@]}"; do
    rm -f "$OUT/$disabled"
done

should_skip_fuzzer() {
    local name=$1
    for disabled in "${DISABLED_FUZZERS[@]}"; do
        if [ "$name" = "$disabled" ]; then
            return 0
        fi
    done
    return 1
}

# =============================================================================
# C API Fuzzer (covers Assimp.cpp C bindings)
# =============================================================================
build_fuzzer "assimp_fuzzer_capi" "../fuzz/assimp_fuzzer_capi.cc"
build_corpus "assimp_fuzzer_capi" "OBJ"

# =============================================================================
# Generic Fuzzer (all formats)
# =============================================================================
if ! should_skip_fuzzer "assimp_fuzzer"; then
    build_fuzzer "assimp_fuzzer" "../fuzz/assimp_fuzzer.cc"
    mkdir -p assimp_fuzzer_corpus
    copy_corpus_tree "../test/models" "assimp_fuzzer_corpus"
    copy_corpus_tree "../test/models-nonbsd" "assimp_fuzzer_corpus"
    # Flatten subdirectories (fuzzers only read top-level files)
    python3 -c "
import os, shutil, sys
corpus = sys.argv[1]
for root, dirs, files in os.walk(corpus):
    if root == corpus:
        continue
    for f in files:
        src = os.path.join(root, f)
        dst = os.path.join(corpus, f)
        if os.path.exists(dst):
            parent = os.path.basename(root)
            dst = os.path.join(corpus, parent + '_' + f)
        try:
            shutil.move(src, dst)
        except:
            pass
for root, dirs, files in os.walk(corpus, topdown=False):
    if root != corpus:
        try:
            os.rmdir(root)
        except:
            pass
" assimp_fuzzer_corpus
    # Prune known timeout-prone inputs from the generic corpus.
    # These formats are still covered by dedicated fuzzers.
    find assimp_fuzzer_corpus -maxdepth 1 -type f \( -iname '*.lws' -o -iname '*.nff' \) -delete
    # Keep generic corpus focused on model-like extensions to reduce
    # auto-detection timeouts on docs/textures.
    python3 -c '
import os, sys
keep = {
    ".gltf", ".glb", ".fbx", ".dae", ".x3d", ".irr", ".irrmesh",
    ".3ds", ".stl", ".obj", ".ply", ".off", ".xml", ".json",
}
root = sys.argv[1]
for name in os.listdir(root):
    path = os.path.join(root, name)
    if not os.path.isfile(path):
        continue
    ext = os.path.splitext(name)[1].lower()
    if ext not in keep:
        try:
            os.remove(path)
        except:
            pass
' assimp_fuzzer_corpus
    rm -f "$OUT/assimp_fuzzer_seed_corpus.zip"
    (cd assimp_fuzzer_corpus && zip -q -r $OUT/assimp_fuzzer_seed_corpus.zip .)
    rm -rf assimp_fuzzer_corpus
    cp ../fuzz/assimp_fuzzer.dict $OUT/assimp_fuzzer.dict || true
else
    echo "Skipping assimp_fuzzer corpus/dict (disabled)"
fi

# =============================================================================
# Tier 1: High Impact Formats (>3,000 lines of parser code)
# =============================================================================

# IFC - Industry Foundation Classes (17,391 lines)
build_fuzzer "assimp_fuzzer_ifc" "../fuzz/assimp_fuzzer_ifc.cc"
build_corpus "assimp_fuzzer_ifc" "IFC" "ifc"

# X3D - Extensible 3D (6,546 lines)
build_fuzzer "assimp_fuzzer_x3d" "../fuzz/assimp_fuzzer_x3d.cc"
build_corpus "assimp_fuzzer_x3d" "X3D" "x3d"

# X3DB - binary X3D
build_fuzzer "assimp_fuzzer_x3db" "../fuzz/assimp_fuzzer_x3db.cc"
build_corpus "assimp_fuzzer_x3db" "X3DB" "x3d"

# X3DV - classic VRML encoding
build_fuzzer "assimp_fuzzer_x3dv" "../fuzz/assimp_fuzzer_x3dv.cc"
build_corpus "assimp_fuzzer_x3dv" "X3DV" "x3d"

# VRML - .wrl
build_fuzzer "assimp_fuzzer_wrl" "../fuzz/assimp_fuzzer_wrl.cc"
build_corpus "assimp_fuzzer_wrl" "WRL" "wrl"

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

# Ogre - file-based fuzzer for OgreMaterial/skeleton loading via ReadFile
# ReadFileFromMemory can't provide companion .material/.skeleton.xml files
build_fuzzer "assimp_fuzzer_ogre_file" "../fuzz/assimp_fuzzer_ogre_file.cc"
build_corpus "assimp_fuzzer_ogre_file" "Ogre"

# ASE - 3ds Max ASCII Scene Export (3,202 lines)
build_fuzzer "assimp_fuzzer_ase" "../fuzz/assimp_fuzzer_ase.cc"
build_corpus "assimp_fuzzer_ase" "ASE" "ase"

# 3DS - 3ds Max binary (2,729 lines)
build_fuzzer "assimp_fuzzer_3ds" "../fuzz/assimp_fuzzer_3ds.cc"
build_corpus "assimp_fuzzer_3ds" "3DS" "3ds"

# FBX (13,021 lines) - already existed
build_fuzzer "assimp_fuzzer_fbx" "../fuzz/assimp_fuzzer_fbx.cc"
build_corpus "assimp_fuzzer_fbx" "FBX" "fbx"

# Collada (6,150 lines) - already existed
build_fuzzer "assimp_fuzzer_collada" "../fuzz/assimp_fuzzer_collada.cc"
build_corpus "assimp_fuzzer_collada" "Collada" "collada"

# glTF text format (both v1 and v2 importers handle .gltf extension)
if ! should_skip_fuzzer "assimp_fuzzer_gltf"; then
    build_fuzzer "assimp_fuzzer_gltf" "../fuzz/assimp_fuzzer_gltf.cc"
    mkdir -p gltf_corpus
    copy_corpus_tree "../test/models/glTF" "gltf_corpus"
    copy_corpus_tree "../test/models/glTF2" "gltf_corpus"
    copy_corpus_tree "../test/models-nonbsd/glTF" "gltf_corpus"
    copy_corpus_tree "../test/models-nonbsd/glTF2" "gltf_corpus"
    # Flatten subdirectories
    python3 -c "
import os, shutil, sys
corpus = sys.argv[1]
for root, dirs, files in os.walk(corpus):
    if root == corpus:
        continue
    for f in files:
        src = os.path.join(root, f)
        dst = os.path.join(corpus, f)
        if os.path.exists(dst):
            parent = os.path.basename(root)
            dst = os.path.join(corpus, parent + '_' + f)
        try:
            shutil.move(src, dst)
        except:
            pass
for root, dirs, files in os.walk(corpus, topdown=False):
    if root != corpus:
        try:
            os.rmdir(root)
        except:
            pass
" "gltf_corpus"
    rm -f "$OUT/assimp_fuzzer_gltf_seed_corpus.zip"
    if [ -d "gltf_corpus" ] && [ "$(ls -A gltf_corpus 2>/dev/null)" ]; then
        (cd gltf_corpus && zip -q -r $OUT/assimp_fuzzer_gltf_seed_corpus.zip .)
    fi
    rm -rf gltf_corpus
    cp ../fuzz/glb.dict $OUT/assimp_fuzzer_gltf.dict || cp ../fuzz/assimp_fuzzer.dict $OUT/assimp_fuzzer_gltf.dict || true
else
    echo "Skipping assimp_fuzzer_gltf corpus/dict (disabled)"
fi

# glTF v1 only - dedicated fuzzer for glTF v1 to ensure coverage
# (The shared gltf fuzzer is dominated by v2 files)
build_fuzzer "assimp_fuzzer_gltf1" "../fuzz/assimp_fuzzer_gltf1.cc"
build_corpus "assimp_fuzzer_gltf1" "glTF" "glb"

# GLB - binary glTF - already existed
if ! should_skip_fuzzer "assimp_fuzzer_glb"; then
    build_fuzzer "assimp_fuzzer_glb" "../fuzz/assimp_fuzzer_glb.cc"
    mkdir -p glb_corpus
    [ -d "../test/models/glTF" ] && find ../test/models/glTF -name "*.glb" -exec cp {} glb_corpus/ \; 2>/dev/null || true
    [ -d "../test/models/glTF2" ] && find ../test/models/glTF2 -name "*.glb" -exec cp {} glb_corpus/ \; 2>/dev/null || true
    if [ -d "glb_corpus" ] && [ "$(ls -A glb_corpus 2>/dev/null)" ]; then
        (cd glb_corpus && zip -q -r $OUT/assimp_fuzzer_glb_seed_corpus.zip .)
    fi
    rm -rf glb_corpus
    cp ../fuzz/glb.dict $OUT/assimp_fuzzer_glb.dict || cp ../fuzz/assimp_fuzzer.dict $OUT/assimp_fuzzer_glb.dict || true
else
    echo "Skipping assimp_fuzzer_glb corpus/dict (disabled)"
fi

# OBJ (2,770 lines) - already existed
build_fuzzer "assimp_fuzzer_obj" "../fuzz/assimp_fuzzer_obj.cc"
build_corpus "assimp_fuzzer_obj" "OBJ" "obj"

# OBJ + MTL - exercises ObjFileMtlImporter via ReadFile with temp files
build_fuzzer "assimp_fuzzer_obj_mtl" "../fuzz/assimp_fuzzer_obj_mtl.cc"
build_corpus "assimp_fuzzer_obj_mtl" "OBJ" "obj"

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
build_corpus "assimp_fuzzer_ply" "PLY" "ply"

# IRR - Irrlicht (2,261 lines)
build_fuzzer "assimp_fuzzer_irr" "../fuzz/assimp_fuzzer_irr.cc"
build_corpus "assimp_fuzzer_irr" "IRR" "irr"

# IRRMesh - Irrlicht mesh
build_fuzzer "assimp_fuzzer_irrmesh" "../fuzz/assimp_fuzzer_irrmesh.cc"
build_corpus "assimp_fuzzer_irrmesh" "IRRMesh" "irr"

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
build_corpus "assimp_fuzzer_ogex" "OpenGEX" "ogex"

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
build_corpus "assimp_fuzzer_smd" "SMD" "smd"

# MD3 - Quake 3 (1,071 lines) - no sample files in repo
build_fuzzer "assimp_fuzzer_md3" "../fuzz/assimp_fuzzer_md3.cc"
build_corpus "assimp_fuzzer_md3" "MD3"  # Will start without seed corpus

# MD3 file-based - exercises shader/skin loading and multipart paths
build_fuzzer "assimp_fuzzer_md3_file" "../fuzz/assimp_fuzzer_md3_file.cc"
build_corpus "assimp_fuzzer_md3_file" "MD3"

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

# ZGL - compressed XGL (shared XGL code, ~200 lines of decompression)
build_fuzzer "assimp_fuzzer_zgl" "../fuzz/assimp_fuzzer_zgl.cc"
build_corpus "assimp_fuzzer_zgl" "XGL"

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

# Unreal file-based (270 lines) - exercises multi-file loading (_d.3d + _a.3d + .uc)
# ReadFileFromMemory can't provide companion files, so this writes temp files
build_fuzzer "assimp_fuzzer_unreal_file" "../fuzz/assimp_fuzzer_unreal_file.cc"
build_corpus "assimp_fuzzer_unreal_file" "3D"

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

# PMD parser (374 lines) - header-only parser included in MMD, not reached via normal import
build_fuzzer "assimp_fuzzer_pmd" "../fuzz/assimp_fuzzer_pmd.cc"
build_corpus "assimp_fuzzer_pmd" "MMD"

# VMD parser (230 lines) - motion data parser included in MMD, not reached via normal import
build_fuzzer "assimp_fuzzer_vmd" "../fuzz/assimp_fuzzer_vmd.cc"
build_corpus "assimp_fuzzer_vmd" "MMD"

# PMD file-based parser (381 lines) - exercises PmdModel::LoadFromFile with ifstream*
# The istream-based PMD fuzzer (assimp_fuzzer_pmd) can't reach ifstream* methods
build_fuzzer "assimp_fuzzer_pmd_file" "../fuzz/assimp_fuzzer_pmd_file.cc"
build_corpus "assimp_fuzzer_pmd_file" "MMD"

# SceneCombiner exercise fuzzer - directly tests MergeScenes, MergeMeshes,
# MergeMaterials, and Copy functions for metadata/textures/morph targets
build_fuzzer "assimp_fuzzer_scenecombiner" "../fuzz/assimp_fuzzer_scenecombiner.cc"
# Use OBJ corpus as seed (any small scene files work)
build_corpus "assimp_fuzzer_scenecombiner" "OBJ"

# =============================================================================
# Specialized Fuzzers (exercise code paths not reachable through import)
# =============================================================================

# Mesh splitter - exercises SplitLargeMeshes and SplitByBoneCount with tight limits
build_fuzzer "assimp_fuzzer_mesh_splitter" "../fuzz/assimp_fuzzer_mesh_splitter.cc"
build_corpus "assimp_fuzzer_mesh_splitter" "glTF2"

# Validate - exercises ValidateDataStructure with multiple formats
# Uses multi-format corpus to exercise animation/camera/light/bone/texture validation
build_fuzzer "assimp_fuzzer_validate" "../fuzz/assimp_fuzzer_validate.cc"
if ! should_skip_fuzzer "assimp_fuzzer_validate"; then
    mkdir -p assimp_fuzzer_validate_corpus
    # OBJ: basic mesh validation
    for f in ../test/models/OBJ/fuzz_seeds/*.obj; do [ -f "$f" ] && cp "$f" assimp_fuzzer_validate_corpus/; done
    # FBX: animations, cameras, lights, bones, textures
    for f in ../test/models/FBX/fuzz_seeds/*.fbx; do [ -f "$f" ] && cp "$f" assimp_fuzzer_validate_corpus/; done
    # Collada: animations, cameras, lights, bones
    for f in ../test/models/Collada/fuzz_seeds/*.dae; do [ -f "$f" ] && cp "$f" assimp_fuzzer_validate_corpus/; done
    # glTF2: animations, bones, morph targets
    for f in ../test/models/glTF2/fuzz_seeds/*.gltf; do [ -f "$f" ] && cp "$f" assimp_fuzzer_validate_corpus/; done
    # B3D: bones, animations
    copy_corpus_tree "../test/models/B3D" assimp_fuzzer_validate_corpus
    # 3DS: cameras, lights
    for f in ../test/models/3D/fuzz_seeds/*.3ds; do [ -f "$f" ] && cp "$f" assimp_fuzzer_validate_corpus/; done
    # BVH: animation-only format
    copy_corpus_tree "../test/models/BVH" assimp_fuzzer_validate_corpus
    # IRR: cameras, lights, animators
    for f in ../test/models/IRR/fuzz_seeds/*.irr; do [ -f "$f" ] && cp "$f" assimp_fuzzer_validate_corpus/; done
    # Flatten and zip
    python3 -c "
import os, shutil, sys
corpus = sys.argv[1]
for root, dirs, files in os.walk(corpus):
    if root == corpus: continue
    for f in files:
        src = os.path.join(root, f)
        dst = os.path.join(corpus, f)
        if os.path.exists(dst):
            dst = os.path.join(corpus, os.path.basename(root) + '_' + f)
        try: shutil.move(src, dst)
        except: pass
for root, dirs, files in os.walk(corpus, topdown=False):
    if root != corpus:
        try: os.rmdir(root)
        except: pass
" assimp_fuzzer_validate_corpus
    rm -f "$OUT/assimp_fuzzer_validate_seed_corpus.zip"
    (cd assimp_fuzzer_validate_corpus && zip -q -r "$OUT/assimp_fuzzer_validate_seed_corpus.zip" .)
    rm -rf assimp_fuzzer_validate_corpus
    # Use generic dict
    cp ../fuzz/assimp_fuzzer.dict "$OUT/assimp_fuzzer_validate.dict" 2>/dev/null || true
fi

# =============================================================================
# Export Fuzzers (roundtrip: import -> export -> import)
# =============================================================================

# Export fuzzers use a small, curated corpus of representative files to avoid
# timeout during coverage runs (the generic corpus has 681 files which is too
# large for roundtrip import->export->reimport on every run).
build_export_corpus() {
    local fuzzer_name=$1
    local dict_name=${2:-assimp_fuzzer}

    if should_skip_fuzzer "$fuzzer_name"; then
        return 0
    fi

    mkdir -p "${fuzzer_name}_corpus"

    # Small set of representative files. Includes files with materials,
    # cameras, skinning, morph targets, animations, lights, and PBR
    # materials to exercise exporter branches.
    # IMPORTANT: keep total corpus small (<30 files, no file >50KB)
    # to avoid coverage timeouts in roundtrip fuzzers.
    for f in \
        ../test/models/OBJ/box.obj \
        ../test/models/OBJ/spider.obj \
        ../test/models/Collada/box.dae \
        ../test/models/Collada/cameras.dae \
        ../test/models/STL/sphereWithHole.stl \
        ../test/models/PLY/cube_binary.ply \
        ../test/models/PLY/cube.ply \
        ../test/models/FBX/box.fbx \
        ../test/models/FBX/phong_cube.fbx \
        ../test/models/3DS/fels.3ds \
        ../test/models/X/test.x \
        ../test/models/OFF/Cube.off \
        ../test/models/glTF2/simple_skin/simple_skin.gltf \
        ../test/models/glTF2/cameras/Cameras.gltf \
        ../test/models/glTF2/fuzz_seeds/01_pbr_metallic_roughness.gltf \
        ../test/models/glTF2/fuzz_seeds/05_morph_targets.gltf \
        ../test/models/glTF2/fuzz_seeds/06_skinning.gltf \
        ../test/models/glTF2/fuzz_seeds/07_animations.gltf \
        ../test/models/glTF2/fuzz_seeds/12_multiple_uv_sets.gltf \
        ../test/models/glTF2/fuzz_seeds/13_vertex_colors.gltf \
        ../test/models/glTF2/fuzz_seeds/23_lights_punctual.gltf \
        ../test/models/glTF2/fuzz_seeds/25_combined_extensions.gltf \
        ../test/models/glTF2/fuzz_seeds/29_morph_with_metadata.gltf \
        ../test/models/glTF2/fuzz_seeds/30_morph_sparse_grid.gltf \
        ../test/models/glTF2/fuzz_seeds/31_metadata_variety.gltf \
        ../test/models/glTF2/fuzz_seeds/32_anim_morph_weights.gltf \
        ../test/models/glTF2/fuzz_seeds/33_many_bones_morph.gltf \
        ../test/models/glTF2/fuzz_seeds/34_many_bones_colors_tangents.gltf \
        ../test/models/Collada/fuzz_seeds/seed_skin.dae \
        ../test/models/Collada/fuzz_seeds/seed_morph.dae \
        ../test/models/Collada/fuzz_seeds/seed_multi_anim.dae \
        ../test/models/Collada/fuzz_seeds/seed_lights_cameras.dae \
        ../test/models/Collada/fuzz_seeds/seed_maya_sampler_props.dae \
        ../test/models/Collada/fuzz_seeds/seed_blinn_constant_shading.dae \
        ../test/models/glTF2/fuzz_seeds/36_step_cubicspline_anim.gltf \
        ../test/models/glTF2/fuzz_seeds/37_morph_weight_anim.gltf \
        ../test/models/glTF2/fuzz_seeds/38_cameras_lights_simple.gltf \
        ../test/models/FBX/fuzz_seeds/seed_blend_shapes.fbx \
        ../test/models/FBX/fuzz_seeds/seed_lights_cameras.fbx \
        ../test/models/FBX/fuzz_seeds/seed_skeletal.fbx \
        ../test/models/FBX/fuzz_seeds/seed_animation_layers.fbx \
        ../test/models/FBX/maxPbrMaterial_metalRough.fbx \
        ../test/models/glTF2/fuzz_seeds/39_sparse_morph_targets.gltf \
        ../test/models/glTF2/fuzz_seeds/40_unlimited_bones.gltf \
        ../test/models/glTF2/fuzz_seeds/41_perspective_ortho_cameras.gltf \
        ../test/models/Collada/fuzz_seeds/seed_morph_controller.dae \
        ../test/models/Collada/fuzz_seeds/seed_spline_interpolation.dae \
        ../test/models/Collada/fuzz_seeds/seed_skin_weights.dae \
        ../test/models/Collada/fuzz_seeds/seed_x_up_large_unit.dae \
        ../test/models/glTF2/fuzz_seeds/44_edge_cases.gltf \
        ../test/models/glTF2/fuzz_seeds/45_extras_extensions.gltf \
        ../test/models/glTF2/fuzz_seeds/46_morph_animation.gltf \
        ../test/models/glTF2/fuzz_seeds/42_texture_transforms.gltf \
        ../test/models/glTF2/fuzz_seeds/43_sampler_modes.gltf \
        ../test/models/Collada/fuzz_seeds/seed_morph_relative.dae \
        ../test/models/Collada/fuzz_seeds/seed_blend_modes.dae \
        ../test/models/Collada/fuzz_seeds/seed_anim_interpolation.dae \
        ../test/models/glTF2/fuzz_seeds/47_all_light_types.gltf \
        ../test/models/Collada/fuzz_seeds/seed_spot_light_atten.dae \
        ../test/models/Collada/fuzz_seeds/seed_anim_all_channels.dae \
        ../test/models/Collada/fuzz_seeds/seed_morph_multi_targets_relative.dae \
        ../test/models/Collada/fuzz_seeds/seed_skin_full.dae \
        ../test/models/Collada/fuzz_seeds/seed_transparency_modes.dae \
        ../test/models/Collada/fuzz_seeds/seed_tristrips_lines.dae \
        ../test/models/ASE/fuzz_seeds/seed_skeleton_only.ase \
        ../test/models/FBX/fuzz_seeds/seed_pivots_transforms.fbx \
        ../test/models/FBX/fuzz_seeds/seed_morph_animated.fbx \
        ../test/models/FBX/fuzz_seeds/seed_multi_material_morph.fbx \
        ../test/models/glTF2/fuzz_seeds/48_primitive_types.gltf \
        ../test/models/glTF2/fuzz_seeds/49_clearcoat_material.gltf \
        ../test/models/glTF2/fuzz_seeds/50_cubicspline_anim.gltf \
        ../test/models/glTF2/fuzz_seeds/51_emissive_strength_ior.gltf \
        ../test/models/glTF2/fuzz_seeds/52_sparse_accessor_draco.gltf \
        ../test/models/Collada/fuzz_seeds/seed_spline_anim.dae \
        ../test/models/glTF2/fuzz_seeds/55_step_cubicspline_morph.gltf \
        ../test/models/glTF2/fuzz_seeds/57_camera_edge_cases.gltf \
        ../test/models/glTF2/fuzz_seeds/58_multi_extension_single_material.gltf \
        ../test/models/Collada/fuzz_seeds/seed_cameras_lights_full.dae \
        ../test/models/Collada/fuzz_seeds/seed_texcoord_offsets.dae \
        ../test/models/FBX/fuzz_seeds/seed_all_light_types.fbx \
        ../test/models/FBX/fuzz_seeds/seed_camera_fov.fbx \
    ; do
        [ -f "$f" ] && cp "$f" "${fuzzer_name}_corpus/" 2>/dev/null || true
    done

    # Remove any old zip first (zip -r updates rather than replaces)
    rm -f "$OUT/${fuzzer_name}_seed_corpus.zip"
    if [ -d "${fuzzer_name}_corpus" ] && [ "$(ls -A ${fuzzer_name}_corpus 2>/dev/null)" ]; then
        (cd "${fuzzer_name}_corpus" && zip -q -r "$OUT/${fuzzer_name}_seed_corpus.zip" .)
    fi
    rm -rf "${fuzzer_name}_corpus"

    if [ -f "../fuzz/${dict_name}.dict" ]; then
        cp "../fuzz/${dict_name}.dict" "$OUT/${fuzzer_name}.dict"
    else
        cp ../fuzz/assimp_fuzzer.dict "$OUT/${fuzzer_name}.dict" || true
    fi
}

# Helper: add extra seeds to an already-built corpus zip
add_extra_seeds_to_corpus() {
    local fuzzer_name=$1
    shift
    local zip_path="$OUT/${fuzzer_name}_seed_corpus.zip"
    if [ ! -f "$zip_path" ]; then
        return 0
    fi
    mkdir -p "${fuzzer_name}_extra"
    for f in "$@"; do
        [ -f "$f" ] && cp "$f" "${fuzzer_name}_extra/" 2>/dev/null || true
    done
    if [ "$(ls -A ${fuzzer_name}_extra 2>/dev/null)" ]; then
        (cd "${fuzzer_name}_extra" && zip -q -r "$zip_path" .)
    fi
    rm -rf "${fuzzer_name}_extra"
}

# OBJ Exporter
build_fuzzer "assimp_fuzzer_export_obj" "../fuzz/assimp_fuzzer_export_obj.cc"
build_export_corpus "assimp_fuzzer_export_obj" "obj"

# Collada Exporter
build_fuzzer "assimp_fuzzer_export_collada" "../fuzz/assimp_fuzzer_export_collada.cc"
build_export_corpus "assimp_fuzzer_export_collada" "collada"
add_extra_seeds_to_corpus "assimp_fuzzer_export_collada" \
    ../test/models/glTF2/fuzz_seeds/35_all_material_extensions.gltf \
    ../test/models/Collada/fuzz_seeds/seed_effects.dae \
    ../test/models/Collada/fuzz_seeds/seed_profile_effects.dae \
    ../test/models/glTF2/fuzz_seeds/53_anisotropy_clearcoat_sheen.gltf \
    ../test/models/glTF2/fuzz_seeds/54_transmission_volume_specular.gltf \
    ../test/models/Collada/fuzz_seeds/seed_controller_weights.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_camera.dae \
    ../test/models/glTF2/fuzz_seeds/61_morph_target_names.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/FBX/fuzz_seeds/seed_pivots_geometric.fbx \
    ../test/models/FBX/fuzz_seeds/seed_morph_animation.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_lines_emissive.dae \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_matrix_element_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/69_multi_color_sets_cubicspline.gltf \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# STL Exporter
build_fuzzer "assimp_fuzzer_export_stl" "../fuzz/assimp_fuzzer_export_stl.cc"
build_export_corpus "assimp_fuzzer_export_stl"

# PLY Exporter
build_fuzzer "assimp_fuzzer_export_ply" "../fuzz/assimp_fuzzer_export_ply.cc"
build_export_corpus "assimp_fuzzer_export_ply"

# 3DS Exporter
build_fuzzer "assimp_fuzzer_export_3ds" "../fuzz/assimp_fuzzer_export_3ds.cc"
build_export_corpus "assimp_fuzzer_export_3ds" "3ds"

# glTF v1 Exporter (roundtrip: import -> export -> re-import)
build_fuzzer "assimp_fuzzer_export_gltf" "../fuzz/assimp_fuzzer_export_gltf.cc"
build_export_corpus "assimp_fuzzer_export_gltf" "glb"

# glTF2 Exporter - uses extended corpus with material extension seeds
build_fuzzer "assimp_fuzzer_export_gltf2" "../fuzz/assimp_fuzzer_export_gltf2.cc"
build_export_corpus "assimp_fuzzer_export_gltf2" "glb"
# Add material extension seeds (safe for glTF2, may crash PBRT exporter)
add_extra_seeds_to_corpus "assimp_fuzzer_export_gltf2" \
    ../test/models/glTF2/fuzz_seeds/35_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/02_pbr_specular_glossiness.gltf \
    ../test/models/glTF2/fuzz_seeds/04_clearcoat_material.gltf \
    ../test/models/glTF2/fuzz_seeds/18_specular_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/19_sheen_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/20_transmission_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/21_volume_ior_emissive.gltf \
    ../test/models/glTF2/fuzz_seeds/22_anisotropy_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/53_anisotropy_clearcoat_sheen.gltf \
    ../test/models/glTF2/fuzz_seeds/54_transmission_volume_specular.gltf \
    ../test/models/glTF2/fuzz_seeds/55_step_cubicspline_morph.gltf \
    ../test/models/glTF2/fuzz_seeds/56_bufferView_images.gltf \
    ../test/models/glTF2/fuzz_seeds/58_multi_extension_single_material.gltf \
    ../test/models/glTF2/fuzz_seeds/61_morph_target_names.gltf \
    ../test/models/glTF2/fuzz_seeds/62_sparse_accessors.gltf \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/65_texture_transform.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/glTF2/fuzz_seeds/69_multi_color_sets_cubicspline.gltf \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/73_sparse_accessor.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# GLB2 Exporter - also uses extended corpus
build_fuzzer "assimp_fuzzer_export_glb2" "../fuzz/assimp_fuzzer_export_glb2.cc"
build_export_corpus "assimp_fuzzer_export_glb2" "glb"
add_extra_seeds_to_corpus "assimp_fuzzer_export_glb2" \
    ../test/models/glTF2/fuzz_seeds/35_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/02_pbr_specular_glossiness.gltf \
    ../test/models/glTF2/fuzz_seeds/04_clearcoat_material.gltf \
    ../test/models/glTF2/fuzz_seeds/18_specular_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/19_sheen_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/20_transmission_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/21_volume_ior_emissive.gltf \
    ../test/models/glTF2/fuzz_seeds/22_anisotropy_extension.gltf \
    ../test/models/glTF2/fuzz_seeds/53_anisotropy_clearcoat_sheen.gltf \
    ../test/models/glTF2/fuzz_seeds/54_transmission_volume_specular.gltf \
    ../test/models/glTF2/fuzz_seeds/55_step_cubicspline_morph.gltf \
    ../test/models/glTF2/fuzz_seeds/56_bufferView_images.gltf \
    ../test/models/glTF2/fuzz_seeds/58_multi_extension_single_material.gltf \
    ../test/models/glTF2/fuzz_seeds/61_morph_target_names.gltf \
    ../test/models/glTF2/fuzz_seeds/62_sparse_accessors.gltf \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/65_texture_transform.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/glTF2/fuzz_seeds/69_multi_color_sets_cubicspline.gltf \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/73_sparse_accessor.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# FBX Exporter
build_fuzzer "assimp_fuzzer_export_fbx" "../fuzz/assimp_fuzzer_export_fbx.cc"
build_export_corpus "assimp_fuzzer_export_fbx" "fbx"
add_extra_seeds_to_corpus "assimp_fuzzer_export_fbx" \
    ../test/models/glTF2/fuzz_seeds/35_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/53_anisotropy_clearcoat_sheen.gltf \
    ../test/models/glTF2/fuzz_seeds/54_transmission_volume_specular.gltf \
    ../test/models/glTF2/fuzz_seeds/61_morph_target_names.gltf \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/FBX/fuzz_seeds/seed_pivots_geometric.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/FBX/fuzz_seeds/seed_morph_animation.fbx \
    ../test/models/FBX/fuzz_seeds/seed_multi_material.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/69_multi_color_sets_cubicspline.gltf \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# X Exporter
build_fuzzer "assimp_fuzzer_export_x" "../fuzz/assimp_fuzzer_export_x.cc"
build_export_corpus "assimp_fuzzer_export_x"

# 3MF Exporter
build_fuzzer "assimp_fuzzer_export_3mf" "../fuzz/assimp_fuzzer_export_3mf.cc"
build_export_corpus "assimp_fuzzer_export_3mf"

# Assimp JSON Exporter (export-only format)
build_fuzzer "assimp_fuzzer_export_assjson" "../fuzz/assimp_fuzzer_export_assjson.cc"
build_export_corpus "assimp_fuzzer_export_assjson"
add_extra_seeds_to_corpus "assimp_fuzzer_export_assjson" \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/FBX/fuzz_seeds/seed_pivots_geometric.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_lines_emissive.dae \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# Assimp XML Exporter (export-only format)
build_fuzzer "assimp_fuzzer_export_assxml" "../fuzz/assimp_fuzzer_export_assxml.cc"
build_export_corpus "assimp_fuzzer_export_assxml"
add_extra_seeds_to_corpus "assimp_fuzzer_export_assxml" \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/FBX/fuzz_seeds/seed_pivots_geometric.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_lines_emissive.dae \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# Assbin Exporter (roundtrip: import -> export -> re-import)
build_fuzzer "assimp_fuzzer_export_assbin" "../fuzz/assimp_fuzzer_export_assbin.cc"
build_export_corpus "assimp_fuzzer_export_assbin"
add_extra_seeds_to_corpus "assimp_fuzzer_export_assbin" \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/FBX/fuzz_seeds/seed_pivots_geometric.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_lines_emissive.dae \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# FBX ASCII Exporter (roundtrip)
build_fuzzer "assimp_fuzzer_export_fbxa" "../fuzz/assimp_fuzzer_export_fbxa.cc"
build_export_corpus "assimp_fuzzer_export_fbxa" "fbx"
add_extra_seeds_to_corpus "assimp_fuzzer_export_fbxa" \
    ../test/models/glTF2/fuzz_seeds/35_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/53_anisotropy_clearcoat_sheen.gltf \
    ../test/models/glTF2/fuzz_seeds/54_transmission_volume_specular.gltf \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/FBX/fuzz_seeds/seed_pivots_geometric.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/FBX/fuzz_seeds/seed_morph_animation.fbx \
    ../test/models/FBX/fuzz_seeds/seed_multi_material.fbx \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/69_multi_color_sets_cubicspline.gltf \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/71_morph_normals_sparse.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# Binary STL Exporter (roundtrip)
build_fuzzer "assimp_fuzzer_export_stlb" "../fuzz/assimp_fuzzer_export_stlb.cc"
build_export_corpus "assimp_fuzzer_export_stlb"

# Binary PLY Exporter (roundtrip)
build_fuzzer "assimp_fuzzer_export_plyb" "../fuzz/assimp_fuzzer_export_plyb.cc"
build_export_corpus "assimp_fuzzer_export_plyb"

# X3D Exporter (roundtrip)
build_fuzzer "assimp_fuzzer_export_x3d" "../fuzz/assimp_fuzzer_export_x3d.cc"
build_export_corpus "assimp_fuzzer_export_x3d" "x3d"
add_extra_seeds_to_corpus "assimp_fuzzer_export_x3d" \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/66_morph_normals_tangents.gltf \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_lines_emissive.dae \
    ../test/models/Collada/fuzz_seeds/seed_morph_weight_anim.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# Step Exporter (export-only)
build_fuzzer "assimp_fuzzer_export_stp" "../fuzz/assimp_fuzzer_export_stp.cc"
build_export_corpus "assimp_fuzzer_export_stp"

# Model 3D Exporter (roundtrip)
build_fuzzer "assimp_fuzzer_export_m3d" "../fuzz/assimp_fuzzer_export_m3d.cc"
build_export_corpus "assimp_fuzzer_export_m3d"

# pbrt-v4 Exporter (export-only)
build_fuzzer "assimp_fuzzer_export_pbrt" "../fuzz/assimp_fuzzer_export_pbrt.cc"
build_export_corpus "assimp_fuzzer_export_pbrt"
# Add light/camera/PBR seeds for PBRT exporter coverage
add_extra_seeds_to_corpus "assimp_fuzzer_export_pbrt" \
    ../test/models/glTF2/fuzz_seeds/23_lights_punctual.gltf \
    ../test/models/glTF2/fuzz_seeds/47_all_light_types.gltf \
    ../test/models/glTF2/fuzz_seeds/01_pbr_metallic_roughness.gltf \
    ../test/models/Collada/fuzz_seeds/seed_lights_cameras.dae \
    ../test/models/FBX/fuzz_seeds/seed_lights_cameras.fbx \
    ../test/models/glTF2/fuzz_seeds/57_camera_edge_cases.gltf \
    ../test/models/Collada/fuzz_seeds/seed_cameras_lights_full.dae \
    ../test/models/FBX/fuzz_seeds/seed_all_light_types.fbx \
    ../test/models/FBX/fuzz_seeds/seed_camera_fov.fbx \
    ../test/models/glTF2/fuzz_seeds/67_lights_range.gltf \
    ../test/models/Collada/fuzz_seeds/seed_full_export.dae \
    ../test/models/glTF2/fuzz_seeds/64_material_extensions.gltf \
    ../test/models/FBX/fuzz_seeds/seed_kitchen_sink.fbx \
    ../test/models/Collada/fuzz_seeds/seed_lines_emissive.dae \
    ../test/models/Collada/fuzz_seeds/seed_ortho_cam_penumbra.dae \
    ../test/models/glTF2/fuzz_seeds/70_all_material_extensions.gltf \
    ../test/models/glTF2/fuzz_seeds/72_primitive_modes.gltf \
    ../test/models/glTF2/fuzz_seeds/74_lights_all_types.gltf

# Copy any per-fuzzer .options overrides.
copy_fuzzer_options

echo ""
echo "=========================================="
echo "Built $(ls $OUT/assimp_fuzzer_* 2>/dev/null | grep -v seed_corpus | grep -v '.dict' | wc -l) fuzzers"
echo "=========================================="
