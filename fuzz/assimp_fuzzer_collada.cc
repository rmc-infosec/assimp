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
    if (!AssimpFuzz::IsValidSize(dataSize, "dae")) {
        return 0;
    }

    const uint32_t hash = AssimpFuzz::HashBytes(data, dataSize);
    Importer importer;
    // Force Collada format (dae)
    if (!AssimpFuzz::ForceFormat(importer, "dae")) {
        return 0;
    }

    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);

    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);
    importer.ReadFileFromMemory(data, dataSize, flags, "dae");

    // Alternate pass to exercise Collada parser branches behind opposite knobs.
    Importer importerAlt;
    if (!AssimpFuzz::ForceFormat(importerAlt, "dae")) {
        return 0;
    }
    AssimpFuzz::ApplyImporterConfigs(importerAlt, data, dataSize);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_IGNORE_UP_DIRECTION, (hash & 0x01u) == 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_IGNORE_UNIT_SIZE, (hash & 0x02u) == 0u);
    importerAlt.SetPropertyBool(AI_CONFIG_IMPORT_COLLADA_USE_COLLADA_NAMES, (hash & 0x04u) == 0u);

    unsigned int altFlags = flags ^ (aiProcess_Triangulate
            | aiProcess_GenNormals
            | aiProcess_GenUVCoords
            | aiProcess_FindDegenerates
            | aiProcess_GlobalScale);
    if ((altFlags & aiProcess_GenSmoothNormals) && (altFlags & aiProcess_GenNormals)) {
        altFlags &= ~aiProcess_GenNormals;
    }
    if ((altFlags & aiProcess_OptimizeGraph) && (altFlags & aiProcess_PreTransformVertices)) {
        altFlags &= ~aiProcess_OptimizeGraph;
    }
    importerAlt.ReadFileFromMemory(data, dataSize, altFlags, "dae");

    return 0;
}
