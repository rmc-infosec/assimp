/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------

Copyright (c) 2006-2025, assimp team

All rights reserved.

Redistribution and use of this software in source and binary forms,
with or without modification, are permitted provided that the following
conditions are met:

* Redistributions of source code must retain the above
  copyright notice, this list of conditions and the
  following disclaimer.

* Redistributions in binary form must reproduce the above
  copyright notice, this list of conditions and the
  following disclaimer in the documentation and/or other
  materials provided with the distribution.

* Neither the name of the assimp team, nor the names of its
  contributors may be used to endorse or promote products
  derived from this software without specific prior
  written permission of the assimp team.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
---------------------------------------------------------------------------
*/
#pragma once

#include <assimp/Importer.hpp>
#include <assimp/BaseImporter.h>
#include <assimp/importerdesc.h>
#include <assimp/postprocess.h>
#include <assimp/config.h>
#include <assimp/matrix4x4.h>
#include <assimp/AssertHandler.h>
#include <cstring>
#include <cstdint>
#include <cstddef>
#include <vector>

namespace AssimpFuzz {

// Replace the default assert handler (which calls abort()) with a no-op.
// Coverage builds do NOT define FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION,
// so ai_assert failures would otherwise crash the fuzzer and lose coverage.
static void fuzzAssertHandler(const char*, const char*, int) {
    // No-op: let the fuzzer continue past assert violations
}

struct AssertHandlerInstaller {
    AssertHandlerInstaller() {
        Assimp::setAiAssertHandler(fuzzAssertHandler);
    }
};
static AssertHandlerInstaller s_assertInstaller;

inline uint32_t HashBytes(const uint8_t* data, size_t dataSize) {
    uint32_t hash = 2166136261u;
    for (size_t i = 0; i < dataSize; ++i) {
        hash ^= data[i];
        hash *= 16777619u;
    }
    return hash;
}

inline size_t GetMaxInputSize(const char* ext) {
    if (!ext) {
        return 16u * 1024u * 1024u;
    }

    struct SizeCap {
        const char* ext;
        size_t max;
    };

    static const SizeCap caps[] = {
        {"gltf", 24u * 1024u * 1024u},
        {"gltf2", 24u * 1024u * 1024u},
        {"glb", 24u * 1024u * 1024u},
        {"fbx", 8u * 1024u * 1024u},
        {"ifc", 8u * 1024u * 1024u},
        {"assbin", 8u * 1024u * 1024u},
        {"pk3", 16u * 1024u * 1024u},
        {"sib", 4u * 1024u * 1024u},
        {"ndo", 4u * 1024u * 1024u},
        {"ogre", 16u * 1024u * 1024u},
        {"mesh", 16u * 1024u * 1024u},
        {"mesh.xml", 16u * 1024u * 1024u},
        {"amf", 16u * 1024u * 1024u},
        {"ase", 16u * 1024u * 1024u},
        {"bvh", 8u * 1024u * 1024u},
        {"irr", 8u * 1024u * 1024u},
        {"irrmesh", 8u * 1024u * 1024u},
        {"md5", 8u * 1024u * 1024u},
        {"mdl", 8u * 1024u * 1024u},
        {"x", 8u * 1024u * 1024u},
        {"wrl", 8u * 1024u * 1024u},
        {"dae", 8u * 1024u * 1024u},
        {"blend", 8u * 1024u * 1024u},
        {"csm", 8u * 1024u * 1024u},
        {"b3d", 8u * 1024u * 1024u},
        {"lwo", 8u * 1024u * 1024u},
        {"stl", 8u * 1024u * 1024u},
        {"obj", 8u * 1024u * 1024u},
        {"x3d", 8u * 1024u * 1024u},
        {"x3db", 8u * 1024u * 1024u},
        {"x3dv", 8u * 1024u * 1024u},
        {"usda", 8u * 1024u * 1024u},
        {"usd", 8u * 1024u * 1024u},
        {"usdc", 8u * 1024u * 1024u},
        {"3ds", 8u * 1024u * 1024u},
        {"3mf", 8u * 1024u * 1024u},
    };

    for (const auto& cap : caps) {
        if (std::strcmp(cap.ext, ext) == 0) {
            return cap.max;
        }
    }

    return 1024u * 1024u;
}

inline bool IsValidSize(size_t dataSize, const char* ext = nullptr, size_t minSize = 4) {
    return dataSize >= minSize && dataSize <= GetMaxInputSize(ext);
}

// Unregisters all loaders except the ones matching the given extension.
// Returns true if at least one loader was kept.
inline bool ForceFormat(Assimp::Importer& importer, const char* targetExtension) {
    size_t count = importer.GetImporterCount();
    std::vector<Assimp::BaseImporter*> toRemove;
    bool found = false;

    for (size_t i = 0; i < count; ++i) {
        const aiImporterDesc* desc = importer.GetImporterInfo(i);
        Assimp::BaseImporter* imp = importer.GetImporter(i);
        
        if (!desc || !imp) continue;

        // Check if the importer supports the target extension
        // mFileExtensions is a space-separated list (e.g., "obj mod")
        // We wrap target in spaces or check bounds to be precise, 
        // but for fuzzing, a simple strstr is usually sufficient 
        // if the target string is unique enough (e.g. "gltf", "obj").
        // A more robust check:
        
        bool isTarget = false;
        const char* extList = desc->mFileExtensions;
        if (!extList) {
            toRemove.push_back(imp);
            continue;
        }
        const size_t targetLen = strlen(targetExtension);

        const char* p = extList;
        while ((p = strstr(p, targetExtension)) != nullptr) {
            // Check boundaries: extensions are space-separated (e.g., "obj mod").
            // At start of string, treat as having implicit space boundary.
            const char prev = (p == extList) ? ' ' : *(p - 1);
            const char next = *(p + targetLen);
            
            if (prev == ' ' && (next == ' ' || next == '\0')) {
                isTarget = true;
                break;
            }
            p++;
        }

        if (isTarget) {
            found = true;
        } else {
            toRemove.push_back(imp);
        }
    }

    for (auto* imp : toRemove) {
        importer.UnregisterLoader(imp);
        delete imp;  // Free the unregistered importer to prevent memory leaks
    }

    return found;
}

// Generate varied post-processing flags based on input data to maximize coverage.
// Uses bytes from the input to deterministically select which flags to enable.
inline unsigned int GetProcessingFlags(const uint8_t* data, size_t dataSize) {
    // Base flags that are always useful
    unsigned int flags = aiProcess_ValidateDataStructure;

    if (dataSize < 2) {
        return flags | aiProcessPreset_TargetRealtime_Fast;
    }

    const size_t first_len = dataSize < 64 ? dataSize : 64;
    uint32_t hash = HashBytes(data, first_len);
    if (dataSize > 64) {
        hash ^= HashBytes(data + (dataSize - 64), 64);
    }

    const uint8_t selector = static_cast<uint8_t>(hash);
    const uint8_t extras = static_cast<uint8_t>(hash >> 8);

    // Select base preset based on first byte
    switch (selector % 4) {
        case 0:
            flags |= aiProcessPreset_TargetRealtime_Fast;
            break;
        case 1:
            flags |= aiProcessPreset_TargetRealtime_Quality;
            break;
        case 2:
            flags |= aiProcessPreset_TargetRealtime_MaxQuality;
            break;
        case 3:
            // Minimal processing - just validation
            break;
    }

    // Add extra flags based on second byte bits
    if (extras & 0x01) flags |= aiProcess_CalcTangentSpace;
    if (extras & 0x02) flags |= aiProcess_GenNormals;
    if (extras & 0x04) flags |= aiProcess_GenSmoothNormals;
    if (extras & 0x08) flags |= aiProcess_FixInfacingNormals;
    if (extras & 0x10) flags |= aiProcess_FindDegenerates;
    if (extras & 0x20) flags |= aiProcess_FindInvalidData;
    if (extras & 0x40) flags |= aiProcess_OptimizeMeshes;
    if (extras & 0x80) flags |= aiProcess_OptimizeGraph;

    // Use third byte for more flags if available
    if (dataSize >= 3) {
        uint8_t more = static_cast<uint8_t>(hash >> 16);
        if (more & 0x01) flags |= aiProcess_SplitLargeMeshes;
        if (more & 0x02) flags |= aiProcess_ImproveCacheLocality;
        if (more & 0x04) flags |= aiProcess_RemoveRedundantMaterials;
        if (more & 0x08) flags |= aiProcess_SortByPType;
        if (more & 0x10) flags |= aiProcess_FindInstances;
        if (more & 0x20) flags |= aiProcess_GenUVCoords;
        if (more & 0x40) flags |= aiProcess_TransformUVCoords;
        if (more & 0x80) flags |= aiProcess_Triangulate;
    }

    if (dataSize >= 4) {
        uint8_t more = static_cast<uint8_t>(hash >> 24);
        if (more & 0x01) flags |= aiProcess_PreTransformVertices;
        if (more & 0x02) flags |= aiProcess_JoinIdenticalVertices;
        if (more & 0x04) flags |= aiProcess_LimitBoneWeights;
        if (more & 0x08) flags |= aiProcess_SplitByBoneCount;
        if (more & 0x10) flags |= aiProcess_Debone;
        if (more & 0x20) flags |= aiProcess_GenBoundingBoxes;
        if (more & 0x40) flags |= aiProcess_FlipUVs;
        if (more & 0x80) flags |= aiProcess_FlipWindingOrder;
    }

    // MakeLeftHanded is orthogonal to other flags
    if (dataSize >= 6 && (data[5] & 0x01)) {
        flags |= aiProcess_MakeLeftHanded;
    }

    // DropNormals - only when NOT generating normals
    if (dataSize >= 6 && (data[5] & 0x02) &&
        !(flags & aiProcess_GenNormals) &&
        !(flags & aiProcess_GenSmoothNormals) &&
        !(flags & aiProcess_ForceGenNormals)) {
        flags |= aiProcess_DropNormals;
    }

    // Additional coverage-oriented flags using XOR of hash bytes
    if (dataSize >= 5) {
        uint8_t extra = data[4] ^ static_cast<uint8_t>(hash);
        if (extra & 0x01) flags |= aiProcess_RemoveComponent;
        if (extra & 0x02) flags |= aiProcess_PopulateArmatureData;
        if (extra & 0x04) flags |= aiProcess_GlobalScale;
        if (extra & 0x08) flags |= aiProcess_EmbedTextures;
        if (extra & 0x10) flags |= aiProcess_ForceGenNormals;
    }

    // Avoid invalid combinations that trigger assertions in Importer.
    if ((flags & aiProcess_GenSmoothNormals) && (flags & aiProcess_GenNormals)) {
        flags &= ~aiProcess_GenNormals;
    }
    if ((flags & aiProcess_OptimizeGraph) && (flags & aiProcess_PreTransformVertices)) {
        flags &= ~aiProcess_OptimizeGraph;
    }

    return flags;
}

// Apply importer configuration options based on input data to explore config branches.
inline void ApplyImporterConfigs(Assimp::Importer& importer, const uint8_t* data, size_t dataSize) {
    if (dataSize < 8) {
        return;
    }

    const uint8_t b0 = data[0];
    const uint8_t b1 = data[1];
    const uint8_t b2 = data[2];
    const uint8_t b3 = data[3];
    const uint8_t b4 = data[4];
    const uint8_t b5 = data[5];
    const uint8_t b6 = data[6];
    const uint8_t b7 = data[7];

    importer.SetPropertyInteger(AI_CONFIG_IMPORT_NO_SKELETON_MESHES, (b0 & 0x01) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_REMOVE_EMPTY_BONES, (b0 & 0x02) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_PTV_KEEP_HIERARCHY, (b0 & 0x04) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_PTV_NORMALIZE, (b0 & 0x08) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_FD_REMOVE, (b0 & 0x10) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_FD_CHECKAREA, (b0 & 0x20) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_FAVOUR_SPEED, (b0 & 0x40) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_LBW_MAX_WEIGHTS, 1 + (b1 % 8));
    importer.SetPropertyInteger(AI_CONFIG_PP_SBBC_MAX_BONES, 4 + (b1 % 28));
    importer.SetPropertyInteger(AI_CONFIG_PP_SLM_TRIANGLE_LIMIT, 4 + (b2 * 16));
    importer.SetPropertyInteger(AI_CONFIG_PP_SLM_VERTEX_LIMIT, 8 + (b3 * 16));
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_GLOBAL_KEYFRAME, b4 % 60);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_MD2_KEYFRAME, (b5 % 30) - 1);
    importer.SetPropertyInteger(AI_CONFIG_PP_RVC_FLAGS, b6);
    importer.SetPropertyInteger(AI_CONFIG_PP_CT_TEXTURE_CHANNEL_INDEX, b7 & 0x03);
    importer.SetPropertyFloat(AI_CONFIG_PP_CT_MAX_SMOOTHING_ANGLE, 20.0f + static_cast<float>(b7 % 60));
    importer.SetPropertyFloat(AI_CONFIG_PP_GSN_MAX_SMOOTHING_ANGLE, 20.0f + static_cast<float>(b7 % 60));

    if (dataSize < 12) {
        return;
    }

    const uint8_t b8 = data[8];
    const uint8_t b9 = data[9];
    const uint8_t b10 = data[10];
    const uint8_t b11 = data[11];

    importer.SetPropertyInteger(AI_CONFIG_PP_PTV_ADD_ROOT_TRANSFORMATION, (b8 & 0x01) ? 1 : 0);
    importer.SetPropertyFloat(AI_CONFIG_PP_DB_THRESHOLD, 0.1f + static_cast<float>(b8 % 20) * 0.1f);
    importer.SetPropertyInteger(AI_CONFIG_PP_DB_ALL_OR_NONE, (b8 & 0x04) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_ICL_PTCACHE_SIZE, 4 + (b9 % 32));

    int tuv_eval = b11 & 0x07;
    if (tuv_eval == 0) {
        tuv_eval = AI_UVTRAFO_ALL;
    }
    importer.SetPropertyInteger(AI_CONFIG_PP_TUV_EVALUATE, tuv_eval);

    aiMatrix4x4 root;
    root.a4 = (static_cast<float>(b9) - 128.0f) / 32.0f;
    root.b4 = (static_cast<float>(b10) - 128.0f) / 32.0f;
    root.c4 = (static_cast<float>(b11) - 128.0f) / 32.0f;
    if (b8 & 0x02) {
        const float scale = 0.25f + static_cast<float>(b8 % 6) * 0.25f;
        root.a1 = scale;
        root.b2 = scale;
        root.c3 = scale;
    }
    importer.SetPropertyMatrix(AI_CONFIG_PP_PTV_ROOT_TRANSFORMATION, root);

    // Global scale factor for aiProcess_GlobalScale
    importer.SetPropertyFloat(AI_CONFIG_GLOBAL_SCALE_FACTOR_KEY,
        0.5f + static_cast<float>(b10 % 20) * 0.1f);

    // Format-specific configs to unlock additional importer code paths
    if (dataSize < 16) {
        return;
    }

    const uint8_t b12 = data[12];
    const uint8_t b13 = data[13];
    const uint8_t b14 = data[14];
    const uint8_t b15 = data[15];

    // Collada configs
    importer.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_IGNORE_UP_DIRECTION, (b12 & 0x01) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_IGNORE_UNIT_SIZE, (b12 & 0x02) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_USE_COLLADA_NAMES, (b12 & 0x04) != 0);

    // FBX configs
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_PRESERVE_PIVOTS, (b12 & 0x08) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_OPTIMIZE_EMPTY_ANIMATION_CURVES, (b12 & 0x10) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ALL_MATERIALS, (b12 & 0x20) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ALL_GEOMETRY_LAYERS, (b12 & 0x40) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_EMBEDDED_TEXTURES_LEGACY_NAMING, (b12 & 0x80) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_STRICT_MODE, (b13 & 0x01) != 0);

    // IFC configs
    importer.SetPropertyBool(AI_CONFIG_IMPORT_IFC_SKIP_SPACE_REPRESENTATIONS, (b13 & 0x02) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_IFC_CUSTOM_TRIANGULATION, (b13 & 0x04) != 0);
    importer.SetPropertyFloat(AI_CONFIG_IMPORT_IFC_SMOOTHING_ANGLE, 10.0f + static_cast<float>(b14 % 16) * 10.0f);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_IFC_CYLINDRICAL_TESSELLATION, 4 + (b14 % 28));

    // SMD configs
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_SMD_KEYFRAME, b15 % 30);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_SMD_LOAD_ANIMATION_LIST, (b15 & 0x04) != 0);

    // Ogre configs
    importer.SetPropertyBool(AI_CONFIG_IMPORT_OGRE_TEXTURETYPE_FROM_FILENAME, (b13 & 0x08) != 0);

    // FBX read toggles (default is true; setting false disables reading of entire categories)
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_MATERIALS, (b13 & 0x10) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_TEXTURES, (b13 & 0x20) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_CAMERAS, (b13 & 0x40) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_LIGHTS, (b13 & 0x80) != 0);
    importer.SetPropertyBool(AI_CONFIG_FBX_CONVERT_TO_M, (b15 & 0x01) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_IGNORE_UP_DIRECTION, (b15 & 0x02) != 0);

    if (dataSize < 20) {
        return;
    }

    const uint8_t b16 = data[16];
    const uint8_t b17 = data[17];
    const uint8_t b18 = data[18];
    const uint8_t b19 = data[19];

    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ANIMATIONS, (b16 & 0x01) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_WEIGHTS, (b16 & 0x02) != 0);
    importer.SetPropertyBool(AI_CONFIG_FBX_USE_SKELETON_BONE_CONTAINER, (b18 & 0x80) != 0);

    // AC3D configs
    importer.SetPropertyBool(AI_CONFIG_IMPORT_AC_SEPARATE_BFCULL, (b16 & 0x04) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_AC_EVAL_SUBDIVISION, (b16 & 0x08) != 0);

    // IRR config
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_IRR_ANIM_FPS, 15 + (b16 % 46));

    // MDL Half-Life configs
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_ANIMATIONS, (b17 & 0x01) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_ANIMATION_EVENTS, (b17 & 0x02) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_BLEND_CONTROLLERS, (b17 & 0x04) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_SEQUENCE_TRANSITIONS, (b17 & 0x08) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_ATTACHMENTS, (b17 & 0x10) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_BONE_CONTROLLERS, (b17 & 0x20) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_HITBOXES, (b17 & 0x40) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_MISC_GLOBAL_INFO, (b17 & 0x80) != 0);

    // ASE config
    importer.SetPropertyBool(AI_CONFIG_IMPORT_ASE_RECONSTRUCT_NORMALS, (b18 & 0x01) != 0);

    // MD3 multipart config (for MD3 file-based fuzzer)
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MD3_HANDLE_MULTIPART, (b18 & 0x20) != 0);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MD3_LOAD_SHADERS, (b18 & 0x40) != 0);

    // Terragen config
    importer.SetPropertyBool(AI_CONFIG_IMPORT_TER_MAKE_UVS, (b18 & 0x02) != 0);

    // MD5 config
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MD5_NO_ANIM_AUTOLOAD, (b18 & 0x04) != 0);

    // LWO config
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_LWO_ONE_LAYER_ONLY, (b18 & 0x08) ? (b19 % 5) : -1);

    // Unreal config
    importer.SetPropertyBool(AI_CONFIG_IMPORT_UNREAL_HANDLE_FLAGS, (b18 & 0x10) != 0);

    // Additional keyframe configs
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_MDL_KEYFRAME, b19 % 30);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_MDC_KEYFRAME, b19 % 30);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_MD3_KEYFRAME, b19 % 30);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_UNREAL_KEYFRAME, b19 % 30);

    // Global configs
    importer.SetPropertyBool(AI_CONFIG_GLOB_MEASURE_TIME, (b19 & 0x80) != 0);
}

// Force-enable all format-specific import features for maximum coverage.
// Call this AFTER ApplyImporterConfigs() in export fuzzers to ensure
// the imported scene contains all features (cameras, lights, animations, etc.)
// so that exporters have rich data to exercise their code paths.
inline void ForceEnableAllImportFeatures(Assimp::Importer& importer) {
    // FBX: enable all reading features
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_PRESERVE_PIVOTS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_CAMERAS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_LIGHTS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ANIMATIONS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_WEIGHTS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_MATERIALS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_TEXTURES, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ALL_GEOMETRY_LAYERS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ALL_MATERIALS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_FBX_OPTIMIZE_EMPTY_ANIMATION_CURVES, true);

    // Collada: don't ignore anything
    importer.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_IGNORE_UP_DIRECTION, false);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_IGNORE_UNIT_SIZE, false);

    // MDL Half-Life: enable all reading features
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_ANIMATIONS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_ANIMATION_EVENTS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_BLEND_CONTROLLERS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_SEQUENCE_TRANSITIONS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_ATTACHMENTS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_BONE_CONTROLLERS, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_HITBOXES, true);
    importer.SetPropertyBool(AI_CONFIG_IMPORT_MDL_HL1_READ_MISC_GLOBAL_INFO, true);
}

// Import flags for export fuzzers: preserve all scene data (bones, animations,
// cameras, lights) so exporters can exercise their full code paths.
// Never enables PTV, OptimizeGraph, Debone, or SplitByBoneCount.
inline unsigned int GetImportFlagsForExport(const uint8_t* data, size_t dataSize) {
    unsigned int flags = aiProcess_Triangulate | aiProcess_ValidateDataStructure;

    if (dataSize < 8) {
        return flags;
    }

    uint8_t selector = data[7];

    // Safe flags that preserve scene structure
    if (selector & 0x01) flags |= aiProcess_JoinIdenticalVertices;
    if (selector & 0x02) flags |= aiProcess_GenNormals;
    if (selector & 0x04) flags |= aiProcess_GenSmoothNormals;
    if (selector & 0x08) flags |= aiProcess_CalcTangentSpace;
    if (selector & 0x10) flags |= aiProcess_FixInfacingNormals;
    if (selector & 0x20) flags |= aiProcess_GenUVCoords;
    if (selector & 0x40) flags |= aiProcess_PopulateArmatureData;
    if (selector & 0x80) flags |= aiProcess_LimitBoneWeights;

    // Avoid mutually exclusive flags
    if ((flags & aiProcess_GenSmoothNormals) && (flags & aiProcess_GenNormals)) {
        flags &= ~aiProcess_GenNormals;
    }

    return flags;
}

// Generate export-appropriate preprocessing flags.
// Export flags are a subset of import flags that make sense for export operations.
// Uses up to 2 bytes from input for ~65k flag combinations.
inline unsigned int GetExportFlags(const uint8_t* data, size_t dataSize) {
    unsigned int flags = aiProcess_ValidateDataStructure;

    if (dataSize < 1) {
        return flags | aiProcess_Triangulate;
    }

    uint8_t selector = data[0];

    // Export-appropriate flags: no PTV, no Debone, no OptimizeGraph
    // (these strip bones/animations/hierarchy needed by exporters)
    if (selector & 0x01) flags |= aiProcess_Triangulate;
    if (selector & 0x02) flags |= aiProcess_JoinIdenticalVertices;
    if (selector & 0x04) flags |= aiProcess_GenNormals;
    if (selector & 0x08) flags |= aiProcess_GenSmoothNormals;
    if (selector & 0x10) flags |= aiProcess_CalcTangentSpace;
    if (selector & 0x20) flags |= aiProcess_FlipUVs;
    if (selector & 0x40) flags |= aiProcess_FlipWindingOrder;
    if (selector & 0x80) flags |= aiProcess_SortByPType;

    // Additional export flags from second byte
    if (dataSize >= 2) {
        uint8_t extras = data[1];
        if (extras & 0x01) flags |= aiProcess_OptimizeMeshes;
        if (extras & 0x02) flags |= aiProcess_RemoveRedundantMaterials;
        if (extras & 0x04) flags |= aiProcess_FixInfacingNormals;
        if (extras & 0x08) flags |= aiProcess_GenUVCoords;
        if (extras & 0x10) flags |= aiProcess_TransformUVCoords;
        if (extras & 0x20) flags |= aiProcess_EmbedTextures;
        if (extras & 0x40) flags |= aiProcess_GlobalScale;
        if (extras & 0x80) flags |= aiProcess_GenBoundingBoxes;
    }

    // More export flags from third byte
    if (dataSize >= 3) {
        uint8_t more = data[2];
        if (more & 0x01) flags |= aiProcess_PopulateArmatureData;
        if (more & 0x02) flags |= aiProcess_LimitBoneWeights;
        if (more & 0x04) flags |= aiProcess_FindDegenerates;
        if (more & 0x08) flags |= aiProcess_FindInvalidData;
    }

    // Avoid invalid combinations
    if ((flags & aiProcess_GenSmoothNormals) && (flags & aiProcess_GenNormals)) {
        flags &= ~aiProcess_GenNormals;
    }

    return flags;
}

// Detect the likely file format from content and return an appropriate hint
// for ReadFileFromMemory. This helps auto-detection work reliably for all
// supported formats, especially text-based ones like .gltf and .dae.
inline const char* DetectFormatHint(const uint8_t* data, size_t dataSize) {
    if (dataSize < 4) return "";

    // GLB binary glTF (magic: "glTF")
    if (data[0] == 'g' && data[1] == 'l' && data[2] == 'T' && data[3] == 'F') {
        return "scene.glb";
    }

    // Check for text-based formats by scanning first bytes
    // Skip BOM if present
    size_t start = 0;
    if (dataSize >= 3 && data[0] == 0xEF && data[1] == 0xBB && data[2] == 0xBF) {
        start = 3;
    }

    // Skip whitespace
    while (start < dataSize && (data[start] == ' ' || data[start] == '\t' ||
           data[start] == '\r' || data[start] == '\n')) {
        start++;
    }

    if (start >= dataSize) return "";

    // JSON (glTF text format) - starts with '{'
    if (data[start] == '{') {
        // Check if it looks like glTF by searching for "asset" key
        const size_t scanLen = (dataSize - start) < 512 ? (dataSize - start) : 512;
        for (size_t i = start; i + 5 < start + scanLen; i++) {
            if (data[i] == 'a' && data[i+1] == 's' && data[i+2] == 's' &&
                data[i+3] == 'e' && data[i+4] == 't') {
                return "scene.gltf";
            }
        }
        return "scene.json";
    }

    // XML-based formats
    if (data[start] == '<') {
        const size_t scanLen = (dataSize - start) < 1024 ? (dataSize - start) : 1024;
        for (size_t i = start; i + 8 < start + scanLen; i++) {
            // COLLADA
            if ((data[i] == 'C' || data[i] == 'c') &&
                (data[i+1] == 'O' || data[i+1] == 'o') &&
                (data[i+2] == 'L' || data[i+2] == 'l') &&
                (data[i+3] == 'L' || data[i+3] == 'l') &&
                (data[i+4] == 'A' || data[i+4] == 'a') &&
                (data[i+5] == 'D' || data[i+5] == 'd') &&
                (data[i+6] == 'A' || data[i+6] == 'a')) {
                return "scene.dae";
            }
            // X3D
            if ((data[i] == 'X' || data[i] == 'x') && data[i+1] == '3' &&
                (data[i+2] == 'D' || data[i+2] == 'd')) {
                return "scene.x3d";
            }
            // IRR scene
            if (data[i] == 'i' && data[i+1] == 'r' && data[i+2] == 'r' &&
                data[i+3] == '_' && data[i+4] == 's' && data[i+5] == 'c') {
                return "scene.irr";
            }
            // IRR mesh
            if (data[i] == 'i' && data[i+1] == 'r' && data[i+2] == 'r' &&
                data[i+3] == 'm' && data[i+4] == 'e' && data[i+5] == 's') {
                return "scene.irrmesh";
            }
        }
        return "scene.xml";
    }

    // FBX binary (magic: "Kaydara FBX Binary")
    if (dataSize >= 18 && data[0] == 'K' && data[1] == 'a' && data[2] == 'y' &&
        data[3] == 'd' && data[4] == 'a' && data[5] == 'r' && data[6] == 'a') {
        return "scene.fbx";
    }

    // FBX ASCII (starts with "; FBX" comment)
    if (dataSize >= 5 && data[0] == ';' && data[1] == ' ' && data[2] == 'F' &&
        data[3] == 'B' && data[4] == 'X') {
        return "scene.fbx";
    }

    // 3DS (magic: 0x4D4D at offset 0)
    if (dataSize >= 2 && data[0] == 0x4D && data[1] == 0x4D) {
        return "scene.3ds";
    }

    // STL binary (starts with 80-byte header, then triangle count)
    // STL ASCII (starts with "solid")
    if (dataSize >= 5 && data[0] == 's' && data[1] == 'o' && data[2] == 'l' &&
        data[3] == 'i' && data[4] == 'd') {
        return "scene.stl";
    }

    // OBJ (starts with comments or vertex data)
    if (data[start] == '#' || (data[start] == 'v' && dataSize > start + 1 &&
        (data[start+1] == ' ' || data[start+1] == 't' || data[start+1] == 'n'))) {
        return "scene.obj";
    }

    // PLY
    if (dataSize >= 3 && data[0] == 'p' && data[1] == 'l' && data[2] == 'y') {
        return "scene.ply";
    }

    // OFF
    if (dataSize >= 3 && data[0] == 'O' && data[1] == 'F' && data[2] == 'F') {
        return "scene.off";
    }

    return "";
}

// Import with format detection: tries auto-detect first, then uses format hints.
// Returns the imported scene, or nullptr if import fails.
inline const aiScene* ImportWithHints(Assimp::Importer& importer,
                                      const uint8_t* data, size_t dataSize,
                                      unsigned int importFlags) {
    // First try with format hint for reliable detection
    const char* hint = DetectFormatHint(data, dataSize);
    if (hint[0] != '\0') {
        const aiScene* scene = importer.ReadFileFromMemory(data, dataSize, importFlags, hint);
        if (scene) return scene;
    }

    // Fall back to auto-detection (tries all importers)
    return importer.ReadFileFromMemory(data, dataSize, importFlags);
}

}
