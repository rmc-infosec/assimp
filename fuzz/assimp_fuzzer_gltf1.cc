/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer dedicated to glTF v1 format only.
The shared gltf fuzzer processes both v1 and v2 files, but v2 files
far outnumber v1 files in the corpus, starving v1 of coverage time.
This fuzzer forces only the v1 importer and uses a v1-only corpus.
---------------------------------------------------------------------------
*/
#include "fuzzer_common.h"
#include <assimp/scene.h>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (!AssimpFuzz::IsValidSize(dataSize, "gltf")) {
        return 0;
    }

    Importer importer;
    // Force only glTF v1 importer by removing all but gltf handlers.
    // Both v1 and v2 importers match "gltf", but the v1 importer's
    // CanRead(checkSig=true) will reject v2 files (and vice versa).
    if (!AssimpFuzz::ForceFormat(importer, "gltf")) {
        return 0;
    }

    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);
    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);
    importer.ReadFileFromMemory(data, dataSize, flags, "gltf");

    return 0;
}
