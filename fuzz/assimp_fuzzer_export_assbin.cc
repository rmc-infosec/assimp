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

// Export fuzzer: Import any format, export to Assbin, re-import
// Tests the Assbin exporter and importer code paths

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

    // Export to Assbin format
    Exporter exporter;
    unsigned int exportFlags = AssimpFuzz::GetExportFlags(data, dataSize);
    const aiExportDataBlob* blob = exporter.ExportToBlob(scene, "assbin", exportFlags);
    if (!blob || !blob->data || blob->size == 0) {
        return 0;
    }

    // Re-import the exported Assbin data
    Importer importer2;
    AssimpFuzz::ApplyImporterConfigs(importer2, data, dataSize);
    importer2.ReadFileFromMemory(blob->data, blob->size, importFlags, "exported.assbin");

    return 0;
}
