/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for Unreal .3d format via file I/O.
The Unreal loader requires 3 companion files (_d.3d, _a.3d, .uc).
ReadFileFromMemory can't provide these, so we write temp files.

Fuzz input layout:
  - Bytes [0,1]: uint16 split_offset for _d/_a boundary
  - Bytes [2, split_offset): _d.3d data (triangles + header)
  - Bytes [split_offset, end): _a.3d data (vertex animation)
  A fixed .uc file is always generated to test script parsing.
---------------------------------------------------------------------------
*/
#include "fuzzer_common.h"
#include <assimp/scene.h>
#include <cstdio>
#include <cstring>
#include <unistd.h>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (dataSize < 20 || dataSize > 1024 * 1024) {
        return 0;
    }

    // Split input into _d.3d and _a.3d parts
    uint16_t split = 0;
    memcpy(&split, data, 2);
    size_t split_offset = 2 + (split % (dataSize - 2));
    if (split_offset >= dataSize) split_offset = dataSize / 2 + 2;

    const uint8_t *d_data = data + 2;
    size_t d_size = split_offset - 2;
    const uint8_t *a_data = data + split_offset;
    size_t a_size = dataSize - split_offset;

    if (d_size < 4 || a_size < 4) return 0;

    // Write files
    int pid = static_cast<int>(getpid());
    char d_path[128], a_path[128], uc_path[128];
    snprintf(d_path, sizeof(d_path), "/tmp/assimp_fuzz_unreal_%d_d.3d", pid);
    snprintf(a_path, sizeof(a_path), "/tmp/assimp_fuzz_unreal_%d_a.3d", pid);
    snprintf(uc_path, sizeof(uc_path), "/tmp/assimp_fuzz_unreal_%d.uc", pid);

    FILE *fp = fopen(d_path, "wb");
    if (!fp) return 0;
    fwrite(d_data, 1, d_size, fp);
    fclose(fp);

    fp = fopen(a_path, "wb");
    if (!fp) { unlink(d_path); return 0; }
    fwrite(a_data, 1, a_size, fp);
    fclose(fp);

    // Write a .uc file with texture commands to exercise the UC parser
    static const char uc_content[] =
        "#exec TEXTURE IMPORT NAME=Jtex1 FILE=tex1.pcx\n"
        "#exec TEXTURE IMPORT NAME=Jtex2 FILE=tex2.pcx\n"
        "#exec MESHMAP SETTEXTURE MESHMAP=box NUM=0 TEXTURE=Jtex1\n"
        "#exec MESHMAP SETTEXTURE MESHMAP=box NUM=1 TEXTURE=Jtex2\n"
        "#exec MESHMAP SCALE MESHMAP=box X=0.1 Y=0.1 Z=0.2\n";
    fp = fopen(uc_path, "w");
    if (!fp) { unlink(d_path); unlink(a_path); return 0; }
    fwrite(uc_content, 1, sizeof(uc_content) - 1, fp);
    fclose(fp);

    Importer importer;
    if (!AssimpFuzz::ForceFormat(importer, "3d")) {
        unlink(d_path); unlink(a_path); unlink(uc_path);
        return 0;
    }

    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);
    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);

    importer.ReadFile(d_path, flags);

    unlink(d_path);
    unlink(a_path);
    unlink(uc_path);
    return 0;
}
