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

// Export fuzzer: Import any format, export to FBX, re-import
// Tests the FBX exporter code paths

#include "fuzzer_common.h"
#include <assimp/scene.h>
#include <assimp/Exporter.hpp>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (!AssimpFuzz::IsValidSize(dataSize)) {
        return 0;
    }

    Importer importer;
    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);
    AssimpFuzz::ForceEnableAllImportFeatures(importer);
    unsigned int importFlags = AssimpFuzz::GetImportFlagsForExport(data, dataSize);

    // Try to import the fuzzed data as any format
    const aiScene *scene = AssimpFuzz::ImportWithHints(importer, data, dataSize, importFlags);
    if (!scene || !scene->mRootNode) {
        return 0;
    }

    // Export to FBX format with export-appropriate flags
    const uint32_t exportHash = AssimpFuzz::HashBytes(data, dataSize);
    auto runRoundTrip = [&](unsigned int flags, uint32_t hashBits) {
        Exporter exporter;
        ExportProperties props;
        props.SetPropertyBool(AI_CONFIG_EXPORT_FBX_TRANSPARENCY_FACTOR_REFER_TO_OPACITY, (hashBits & 0x01u) != 0u);
        props.SetPropertyBool(AI_CONFIG_EXPORT_POINT_CLOUDS, (hashBits & 0x02u) != 0u);
        const aiExportDataBlob* blob = exporter.ExportToBlob(scene, "fbx", flags, &props);
        if (!blob || !blob->data || blob->size == 0) {
            return;
        }

        Importer importer2;
        AssimpFuzz::ApplyImporterConfigs(importer2, data, dataSize);
        importer2.ReadFileFromMemory(blob->data, blob->size, importFlags, "exported.fbx");
    };

    unsigned int exportFlags = AssimpFuzz::GetExportFlags(data, dataSize);
    runRoundTrip(exportFlags, exportHash);

    unsigned int altExportFlags = exportFlags ^ (aiProcess_Triangulate
            | aiProcess_GenNormals
            | aiProcess_GenUVCoords
            | aiProcess_SortByPType
            | aiProcess_GlobalScale);
    if ((altExportFlags & aiProcess_GenSmoothNormals) && (altExportFlags & aiProcess_GenNormals)) {
        altExportFlags &= ~aiProcess_GenNormals;
    }
    runRoundTrip(altExportFlags, ~exportHash);

    return 0;
}
