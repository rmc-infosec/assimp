// Mimics the exact fuzzer behavior: ReadFileFromMemory + ForceFormat + ApplyImporterConfigs
#include <assimp/Importer.hpp>
#include <assimp/BaseImporter.h>
#include <assimp/importerdesc.h>
#include <assimp/postprocess.h>
#include <assimp/config.h>
#include <assimp/matrix4x4.h>
#include <assimp/scene.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <fstream>

// Copied from fuzzer_common.h
namespace AssimpFuzz {

inline uint32_t HashBytes(const uint8_t* data, size_t dataSize) {
    uint32_t hash = 2166136261u;
    for (size_t i = 0; i < dataSize; ++i) {
        hash ^= data[i];
        hash *= 16777619u;
    }
    return hash;
}

inline bool ForceFormat(Assimp::Importer& importer, const char* targetExtension) {
    size_t count = importer.GetImporterCount();
    std::vector<Assimp::BaseImporter*> toRemove;
    bool found = false;

    for (size_t i = 0; i < count; ++i) {
        const aiImporterDesc* desc = importer.GetImporterInfo(i);
        Assimp::BaseImporter* imp = importer.GetImporter(i);
        if (!desc || !imp) continue;

        bool isTarget = false;
        const char* extList = desc->mFileExtensions;
        if (!extList) {
            toRemove.push_back(imp);
            continue;
        }
        const size_t targetLen = strlen(targetExtension);

        const char* p = extList;
        while ((p = strstr(p, targetExtension)) != nullptr) {
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
        delete imp;
    }

    return found;
}

inline unsigned int GetProcessingFlags(const uint8_t* data, size_t dataSize) {
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

    switch (selector % 4) {
        case 0: flags |= aiProcessPreset_TargetRealtime_Fast; break;
        case 1: flags |= aiProcessPreset_TargetRealtime_Quality; break;
        case 2: flags |= aiProcessPreset_TargetRealtime_MaxQuality; break;
        case 3: break;
    }

    if (extras & 0x01) flags |= aiProcess_CalcTangentSpace;
    if (extras & 0x02) flags |= aiProcess_GenNormals;
    if (extras & 0x04) flags |= aiProcess_GenSmoothNormals;
    if (extras & 0x08) flags |= aiProcess_FixInfacingNormals;
    if (extras & 0x10) flags |= aiProcess_FindDegenerates;
    if (extras & 0x20) flags |= aiProcess_FindInvalidData;
    if (extras & 0x40) flags |= aiProcess_OptimizeMeshes;
    if (extras & 0x80) flags |= aiProcess_OptimizeGraph;

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

    if ((flags & aiProcess_GenSmoothNormals) && (flags & aiProcess_GenNormals)) {
        flags &= ~aiProcess_GenNormals;
    }
    if ((flags & aiProcess_OptimizeGraph) && (flags & aiProcess_PreTransformVertices)) {
        flags &= ~aiProcess_OptimizeGraph;
    }

    return flags;
}

inline void ApplyImporterConfigs(Assimp::Importer& importer, const uint8_t* data, size_t dataSize) {
    if (dataSize < 8) return;

    const uint8_t b0 = data[0], b1 = data[1], b2 = data[2], b3 = data[3];
    const uint8_t b4 = data[4], b5 = data[5], b6 = data[6], b7 = data[7];

    importer.SetPropertyInteger(AI_CONFIG_IMPORT_NO_SKELETON_MESHES, (b0 & 0x01) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_REMOVE_EMPTY_BONES, (b0 & 0x02) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_PTV_KEEP_HIERARCHY, (b0 & 0x04) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_PTV_NORMALIZE, (b0 & 0x08) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_FD_REMOVE, (b0 & 0x10) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_FD_CHECKAREA, (b0 & 0x20) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_FAVOUR_SPEED, (b0 & 0x40) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_LBW_MAX_WEIGHTS, 1 + (b1 % 8));
    importer.SetPropertyInteger(AI_CONFIG_PP_SBBC_MAX_BONES, 4 + (b1 % 28));
    importer.SetPropertyInteger(AI_CONFIG_PP_SLM_TRIANGLE_LIMIT, 256 + (b2 * 64));
    importer.SetPropertyInteger(AI_CONFIG_PP_SLM_VERTEX_LIMIT, 256 + (b3 * 64));
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_GLOBAL_KEYFRAME, b4 % 60);
    importer.SetPropertyInteger(AI_CONFIG_IMPORT_MD2_KEYFRAME, (b5 % 30) - 1);
    importer.SetPropertyInteger(AI_CONFIG_PP_RVC_FLAGS, b6);
    importer.SetPropertyInteger(AI_CONFIG_PP_CT_TEXTURE_CHANNEL_INDEX, b7 & 0x03);
    importer.SetPropertyFloat(AI_CONFIG_PP_CT_MAX_SMOOTHING_ANGLE, 20.0f + static_cast<float>(b7 % 60));
    importer.SetPropertyFloat(AI_CONFIG_PP_GSN_MAX_SMOOTHING_ANGLE, 20.0f + static_cast<float>(b7 % 60));

    if (dataSize < 12) return;

    const uint8_t b8 = data[8], b9 = data[9], b10 = data[10], b11 = data[11];

    importer.SetPropertyInteger(AI_CONFIG_PP_PTV_ADD_ROOT_TRANSFORMATION, (b8 & 0x01) ? 1 : 0);
    importer.SetPropertyFloat(AI_CONFIG_PP_DB_THRESHOLD, 0.1f + static_cast<float>(b8 % 20) * 0.1f);
    importer.SetPropertyInteger(AI_CONFIG_PP_DB_ALL_OR_NONE, (b8 & 0x04) ? 1 : 0);
    importer.SetPropertyInteger(AI_CONFIG_PP_ICL_PTCACHE_SIZE, 4 + (b9 % 32));

    int tuv_eval = b11 & 0x07;
    if (tuv_eval == 0) tuv_eval = AI_UVTRAFO_ALL;
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
}

} // namespace AssimpFuzz

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <file> [mode]\n", argv[0]);
        fprintf(stderr, "  mode 0: exact fuzzer reproduction (with PTV/JIV masked)\n");
        fprintf(stderr, "  mode 1: exact fuzzer reproduction (no masking)\n");
        fprintf(stderr, "  mode 2: no configs, fuzzer flags only\n");
        fprintf(stderr, "  mode 3: no flags at all, just ReadFileFromMemory\n");
        return 1;
    }

    const char* file = argv[1];
    int mode = (argc >= 3) ? atoi(argv[2]) : 0;

    // Read file into memory
    std::ifstream ifs(file, std::ios::binary);
    if (!ifs) {
        fprintf(stderr, "Cannot open %s\n", file);
        return 1;
    }
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(ifs)),
                               std::istreambuf_iterator<char>());
    ifs.close();

    fprintf(stderr, "File: %s (%zu bytes)\n", file, data.size());

    Assimp::Importer importer;

    // Always force format to DAE only
    if (!AssimpFuzz::ForceFormat(importer, "dae")) {
        fprintf(stderr, "No Collada importer found\n");
        return 1;
    }

    unsigned int flags = 0;
    switch (mode) {
        case 0: // Exact fuzzer reproduction with masking
            AssimpFuzz::ApplyImporterConfigs(importer, data.data(), data.size());
            flags = AssimpFuzz::GetProcessingFlags(data.data(), data.size());
            flags &= ~aiProcess_PreTransformVertices;
            flags &= ~aiProcess_JoinIdenticalVertices;
            break;
        case 1: // Exact fuzzer reproduction without masking
            AssimpFuzz::ApplyImporterConfigs(importer, data.data(), data.size());
            flags = AssimpFuzz::GetProcessingFlags(data.data(), data.size());
            break;
        case 2: // No configs
            flags = AssimpFuzz::GetProcessingFlags(data.data(), data.size());
            flags &= ~aiProcess_PreTransformVertices;
            flags &= ~aiProcess_JoinIdenticalVertices;
            break;
        case 3: // No flags
            flags = 0;
            break;
        case 4: // Configs + fuzzer flags, only PTV masked
            AssimpFuzz::ApplyImporterConfigs(importer, data.data(), data.size());
            flags = AssimpFuzz::GetProcessingFlags(data.data(), data.size());
            flags &= ~aiProcess_PreTransformVertices;
            break;
        case 5: // Configs + fuzzer flags, only JIV masked
            AssimpFuzz::ApplyImporterConfigs(importer, data.data(), data.size());
            flags = AssimpFuzz::GetProcessingFlags(data.data(), data.size());
            flags &= ~aiProcess_JoinIdenticalVertices;
            break;
        case 6: // Configs + PTV only
            AssimpFuzz::ApplyImporterConfigs(importer, data.data(), data.size());
            flags = aiProcess_ValidateDataStructure | aiProcess_PreTransformVertices;
            break;
        case 7: // Configs + JIV only
            AssimpFuzz::ApplyImporterConfigs(importer, data.data(), data.size());
            flags = aiProcess_ValidateDataStructure | aiProcess_JoinIdenticalVertices;
            break;
        case 8: // No configs + PTV + JIV
            flags = AssimpFuzz::GetProcessingFlags(data.data(), data.size());
            break;
    }

    fprintf(stderr, "Flags: 0x%08x (mode %d)\n", flags, mode);

    const aiScene* scene = importer.ReadFileFromMemory(data.data(), data.size(), flags, "dae");

    if (!scene) {
        fprintf(stderr, "Import failed: %s\n", importer.GetErrorString());
    } else {
        fprintf(stderr, "Import OK: %u meshes, %u materials\n",
                scene->mNumMeshes, scene->mNumMaterials);

        // Dump texture coord state
        for (unsigned int i = 0; i < scene->mNumMeshes; ++i) {
            const aiMesh* m = scene->mMeshes[i];
            if (!m) continue;
            fprintf(stderr, "  mesh[%u]: %u verts, %u faces, name='%s'\n",
                    i, m->mNumVertices, m->mNumFaces, m->mName.C_Str());
            for (unsigned int k = 0; k < AI_MAX_NUMBER_OF_TEXTURECOORDS; ++k) {
                if (m->mTextureCoords[k])
                    fprintf(stderr, "    mTextureCoords[%u] = %p (%u components)\n",
                            k, (void*)m->mTextureCoords[k], m->mNumUVComponents[k]);
            }
            for (unsigned int k = 0; k < AI_MAX_NUMBER_OF_COLOR_SETS; ++k) {
                if (m->mColors[k])
                    fprintf(stderr, "    mColors[%u] = %p\n", k, (void*)m->mColors[k]);
            }
            fprintf(stderr, "    mNormals=%p mTangents=%p mBitangents=%p\n",
                    (void*)m->mNormals, (void*)m->mTangents, (void*)m->mBitangents);
        }

        // Check for buffer aliasing across meshes
        if (scene->mNumMeshes > 1) {
            fprintf(stderr, "Checking for buffer aliasing across %u meshes...\n", scene->mNumMeshes);
            for (unsigned int i = 0; i < scene->mNumMeshes; ++i) {
                for (unsigned int j = i + 1; j < scene->mNumMeshes; ++j) {
                    const aiMesh* a = scene->mMeshes[i];
                    const aiMesh* b = scene->mMeshes[j];
                    if (!a || !b) continue;
                    if (a == b)
                        fprintf(stderr, "  ALIAS: mesh[%u] == mesh[%u] (same object!)\n", i, j);
                    if (a->mVertices && a->mVertices == b->mVertices)
                        fprintf(stderr, "  ALIAS: mesh[%u].mVertices == mesh[%u].mVertices\n", i, j);
                    if (a->mNormals && a->mNormals == b->mNormals)
                        fprintf(stderr, "  ALIAS: mesh[%u].mNormals == mesh[%u].mNormals\n", i, j);
                    if (a->mTangents && a->mTangents == b->mTangents)
                        fprintf(stderr, "  ALIAS: mesh[%u].mTangents == mesh[%u].mTangents\n", i, j);
                    if (a->mBitangents && a->mBitangents == b->mBitangents)
                        fprintf(stderr, "  ALIAS: mesh[%u].mBitangents == mesh[%u].mBitangents\n", i, j);
                    if (a->mFaces && a->mFaces == b->mFaces)
                        fprintf(stderr, "  ALIAS: mesh[%u].mFaces == mesh[%u].mFaces\n", i, j);
                    for (unsigned int k = 0; k < AI_MAX_NUMBER_OF_TEXTURECOORDS; ++k) {
                        if (a->mTextureCoords[k] && a->mTextureCoords[k] == b->mTextureCoords[k])
                            fprintf(stderr, "  ALIAS: mesh[%u].mTextureCoords[%u] == mesh[%u]\n", i, k, j);
                    }
                    for (unsigned int k = 0; k < AI_MAX_NUMBER_OF_COLOR_SETS; ++k) {
                        if (a->mColors[k] && a->mColors[k] == b->mColors[k])
                            fprintf(stderr, "  ALIAS: mesh[%u].mColors[%u] == mesh[%u]\n", i, k, j);
                    }
                }
            }
            fprintf(stderr, "Aliasing check complete.\n");
        }
    }

    fprintf(stderr, "Destroying scene...\n");
    return 0;
}
