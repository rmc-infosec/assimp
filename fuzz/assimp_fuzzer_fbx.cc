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
    if (!AssimpFuzz::IsValidSize(dataSize, "fbx")) {
        return 0;
    }

    const uint32_t hash = AssimpFuzz::HashBytes(data, dataSize);
    Importer importer;
    // Force FBX format
    if (!AssimpFuzz::ForceFormat(importer, "fbx")) {
        return 0;
    }

    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);

    // Always enable ALL FBX reading features for maximum coverage.
    // The generic ApplyImporterConfigs randomly toggles these, but for the
    // dedicated FBX fuzzer we want to exercise every code path.
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

    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);
    importer.ReadFileFromMemory(data, dataSize, flags, "fbx");

    // Second FBX pass with complementary feature toggles to cover disabled paths.
    Importer importerAlt;
    if (!AssimpFuzz::ForceFormat(importerAlt, "fbx")) {
        return 0;
    }
    AssimpFuzz::ApplyImporterConfigs(importerAlt, data, dataSize);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_PRESERVE_PIVOTS, (hash & 0x0001u) == 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_CAMERAS, (hash & 0x0002u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_LIGHTS, (hash & 0x0004u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ANIMATIONS, (hash & 0x0008u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_WEIGHTS, (hash & 0x0010u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_MATERIALS, (hash & 0x0020u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_TEXTURES, (hash & 0x0040u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ALL_GEOMETRY_LAYERS, (hash & 0x0080u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_READ_ALL_MATERIALS, (hash & 0x0100u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_OPTIMIZE_EMPTY_ANIMATION_CURVES, (hash & 0x0200u) == 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_STRICT_MODE, (hash & 0x0400u) != 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_FBX_EMBEDDED_TEXTURES_LEGACY_NAMING, (hash & 0x0800u) != 0u);

    unsigned int altFlags = flags ^ (aiProcess_Triangulate
            | aiProcess_GenNormals
            | aiProcess_GenUVCoords
            | aiProcess_FindInvalidData
            | aiProcess_GlobalScale);
    if ((altFlags & aiProcess_GenSmoothNormals) && (altFlags & aiProcess_GenNormals)) {
        altFlags &= ~aiProcess_GenNormals;
    }
    if ((altFlags & aiProcess_OptimizeGraph) && (altFlags & aiProcess_PreTransformVertices)) {
        altFlags &= ~aiProcess_OptimizeGraph;
    }
    importerAlt.ReadFileFromMemory(data, dataSize, altFlags, "fbx");

    return 0;
}
