/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for SplitLargeMeshes and SplitByBoneCount post-processing steps.
Uses small splitting limits so even modest seed files trigger mesh splitting.
Also exercises GetOrphanedScene and GetMemoryRequirements for Importer.cpp coverage.
---------------------------------------------------------------------------
*/
#include "fuzzer_common.h"
#include <assimp/scene.h>
#include <assimp/mesh.h>
#include <cstring>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (!AssimpFuzz::IsValidSize(dataSize)) {
        return 0;
    }

    // Use very small limits: seeds have 8-12 faces and 12-16 vertices,
    // so SLM_TRIANGLE_LIMIT=3 and SLM_VERTEX_LIMIT=6 will force splitting.
    // SBBC max=3 splits the 6-8 bone meshes into 2-4 submeshes.
    Importer importer;
    importer.SetPropertyInteger(AI_CONFIG_PP_SLM_TRIANGLE_LIMIT, 3);
    importer.SetPropertyInteger(AI_CONFIG_PP_SLM_VERTEX_LIMIT, 6);
    importer.SetPropertyInteger(AI_CONFIG_PP_SBBC_MAX_BONES, 3);
    importer.SetPropertyInteger(AI_CONFIG_PP_LBW_MAX_WEIGHTS, 2);

    unsigned int flags = aiProcess_Triangulate
        | aiProcess_SplitLargeMeshes
        | aiProcess_SplitByBoneCount
        | aiProcess_LimitBoneWeights
        | aiProcess_ValidateDataStructure
        | aiProcess_SortByPType;

    const aiScene *scene = importer.ReadFileFromMemory(data, dataSize, flags, "gltf");
    if (scene) {
        // Exercise GetMemoryRequirements (101 uncovered lines in Importer.cpp)
        aiMemoryInfo info;
        importer.GetMemoryRequirements(info);

        // Exercise GetOrphanedScene (14 uncovered lines in Importer.cpp)
        aiScene *orphaned = importer.GetOrphanedScene();
        delete orphaned;
    }

    return 0;
}
