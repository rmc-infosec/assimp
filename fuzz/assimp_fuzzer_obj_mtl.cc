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

// OBJ + MTL fuzzer: splits fuzz input into an OBJ file and its companion MTL
// file, writes both to /tmp, and uses ReadFile() so the OBJ importer can
// resolve the mtllib directive and load the MTL material library.
// This exercises ObjFileMtlImporter which is unreachable via ReadFileFromMemory.

#include "fuzzer_common.h"
#include <assimp/scene.h>
#include <fstream>
#include <cstring>
#include <cstdio>
#include <unistd.h>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    // Need at least 4 bytes: 2 for split offset + some content
    if (dataSize < 4 || dataSize > 8u * 1024u * 1024u) {
        return 0;
    }

    // First 2 bytes encode the split point (little-endian uint16_t)
    uint16_t mtlOffset;
    memcpy(&mtlOffset, data, 2);

    // Clamp split offset to valid range [2, dataSize)
    if (mtlOffset < 2) mtlOffset = 2;
    if (mtlOffset >= dataSize) mtlOffset = static_cast<uint16_t>(dataSize / 2);

    // OBJ content: bytes [2, mtlOffset)
    // MTL content: bytes [mtlOffset, dataSize)
    const char *objData = reinterpret_cast<const char *>(data + 2);
    size_t objSize = mtlOffset - 2;
    const char *mtlData = reinterpret_cast<const char *>(data + mtlOffset);
    size_t mtlSize = dataSize - mtlOffset;

    // Use PID in filenames for safety when multiple fuzzer processes run
    char objPath[128], mtlPath[128];
    snprintf(objPath, sizeof(objPath), "/tmp/assimp_fuzz_%d.obj", getpid());
    snprintf(mtlPath, sizeof(mtlPath), "/tmp/assimp_fuzz_%d.mtl", getpid());

    // Extract just the MTL filename from the full path for the mtllib directive
    const char *mtlFilename = strrchr(mtlPath, '/');
    mtlFilename = mtlFilename ? mtlFilename + 1 : mtlPath;

    // Write OBJ file with mtllib directive prepended
    {
        std::ofstream obj(objPath, std::ios::binary | std::ios::trunc);
        if (!obj) return 0;
        obj << "mtllib " << mtlFilename << "\n";
        obj.write(objData, objSize);
    }

    // Write MTL file
    {
        std::ofstream mtl(mtlPath, std::ios::binary | std::ios::trunc);
        if (!mtl) {
            remove(objPath);
            return 0;
        }
        mtl.write(mtlData, mtlSize);
    }

    Importer importer;
    // Force OBJ format only
    if (!AssimpFuzz::ForceFormat(importer, "obj")) {
        remove(objPath);
        remove(mtlPath);
        return 0;
    }

    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);
    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);

    importer.ReadFile(objPath, flags);

    // Cleanup temp files
    remove(objPath);
    remove(mtlPath);

    return 0;
}
