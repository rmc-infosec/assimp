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
#include "fuzzer_common.h"
#include <assimp/scene.h>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (!AssimpFuzz::IsValidSize(dataSize)) {
        return 0;
    }

    const uint32_t hash = AssimpFuzz::HashBytes(data, dataSize);
    Importer importer;
    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);

    // Exercise Importer API for coverage
    aiString extList;
    importer.GetExtensionList(extList);
    size_t impCount = importer.GetImporterCount();
    if (impCount > 0) {
        importer.GetImporterInfo(0);
    }
    importer.IsExtensionSupported(".fbx");

    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);
    importer.ValidateFlags(flags);
    // Generic fuzzer runs in coverage mode over a fixed seed corpus. To avoid
    // timeout-prone auto-detect paths, only parse inputs with a concrete hint.
    const char *hint = AssimpFuzz::DetectFormatHint(data, dataSize);
    if (hint[0] == '\0') {
        return 0;
    }

    const aiScene *scene = importer.ReadFileFromMemory(data, dataSize, flags, hint);
    if (scene) {
        // Exercise GetMemoryRequirements (covers 101 lines in Importer.cpp)
        aiMemoryInfo info;
        importer.GetMemoryRequirements(info);
    } else {
        importer.GetErrorString();
    }
    importer.FreeScene();

    // Run a second import pass with complementary flags to cover branches that
    // are mutually exclusive in a single configuration.
    Importer importerAlt;
    AssimpFuzz::ApplyImporterConfigs(importerAlt, data, dataSize);
    unsigned int altFlags = flags ^ (aiProcess_Triangulate
            | aiProcess_GenNormals
            | aiProcess_FindInvalidData
            | aiProcess_GenUVCoords
            | aiProcess_OptimizeMeshes
            | aiProcess_GlobalScale);
    if (hash & 0x01u) {
        altFlags |= aiProcess_MakeLeftHanded;
    }
    if ((hash & 0x02u) == 0u) {
        altFlags ^= aiProcess_FlipUVs;
    }
    if ((hash & 0x04u) == 0u) {
        altFlags ^= aiProcess_FlipWindingOrder;
    }
    if ((altFlags & aiProcess_GenSmoothNormals) && (altFlags & aiProcess_GenNormals)) {
        altFlags &= ~aiProcess_GenNormals;
    }
    if ((altFlags & aiProcess_OptimizeGraph) && (altFlags & aiProcess_PreTransformVertices)) {
        altFlags &= ~aiProcess_OptimizeGraph;
    }

    importerAlt.ValidateFlags(altFlags);
    const aiScene *sceneAlt = importerAlt.ReadFileFromMemory(data, dataSize, altFlags, hint);
    if (sceneAlt) {
        aiMemoryInfo infoAlt;
        importerAlt.GetMemoryRequirements(infoAlt);
    } else {
        importerAlt.GetErrorString();
    }
    importerAlt.FreeScene();

    return 0;
}
