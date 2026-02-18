/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for MMD PMD parser via file I/O.
PmdModel::LoadFromFile/LoadFromStream take std::ifstream*, so we need
to write fuzz data to a temporary file to exercise those code paths.
---------------------------------------------------------------------------
*/
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <unistd.h>
#include <memory>

// PMD parser header
#include "code/AssetLib/MMD/MMDPmdParser.h"

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (dataSize < 16 || dataSize > 4 * 1024 * 1024) {
        return 0;
    }

    // Write fuzz data to a temp file
    char tmpPath[64];
    snprintf(tmpPath, sizeof(tmpPath), "/tmp/assimp_fuzz_pmd_%d.pmd",
             static_cast<int>(getpid()));

    FILE *fp = fopen(tmpPath, "wb");
    if (!fp) {
        return 0;
    }
    fwrite(data, 1, dataSize, fp);
    fclose(fp);

    // Exercise PmdModel::LoadFromFile which calls LoadFromStream(ifstream*)
    // This covers PmdHeader::Read(ifstream*), PmdVertex::Read(ifstream*),
    // PmdMaterial::Read(ifstream*), and the full LoadFromStream logic.
    auto model = pmd::PmdModel::LoadFromFile(tmpPath);

    unlink(tmpPath);
    return 0;
}
