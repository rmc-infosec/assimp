/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for ValidateDataStructure post-processing step.
Tries multiple format hints per input to exercise validation of animations,
cameras, lights, bones, textures, and morph targets across different importers.
---------------------------------------------------------------------------
*/
#include "fuzzer_common.h"
#include <assimp/scene.h>
#include <assimp/mesh.h>
#include <assimp/postprocess.h>
#include <cstdint>
#include <cstddef>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (dataSize < 8) {
        return 0;
    }

    // Try each input with multiple format hints. The corpus contains OBJ, FBX,
    // Collada, glTF2, B3D, 3DS, BVH, and IRR files. Each format produces
    // different scene features (animations, cameras, lights, bones, textures).
    // By trying multiple hints, we ensure the correct importer handles its
    // native format AND exercises the validator on the resulting scene.
    static const char* formats[] = {
        "obj", "fbx", "dae", "gltf", "b3d", "3ds", "bvh", "irr"
    };

    for (int fi = 0; fi < 8; fi++) {
        Importer importer;
        unsigned int flags = aiProcess_ValidateDataStructure
            | aiProcess_Triangulate;

        const aiScene *scene = importer.ReadFileFromMemory(
            data, dataSize, flags, formats[fi]);
        if (scene) {
            // If import succeeded, also apply more post-processing + re-validate
            importer.ApplyPostProcessing(
                aiProcess_FindDegenerates
                | aiProcess_FindInvalidData
                | aiProcess_SortByPType
                | aiProcess_ValidateDataStructure);
            break;  // One successful parse is enough per input
        }
    }

    return 0;
}
