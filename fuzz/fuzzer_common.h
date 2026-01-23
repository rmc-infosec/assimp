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
#pragma once

#include <assimp/Importer.hpp>
#include <assimp/BaseImporter.h>
#include <assimp/importerdesc.h>
#include <assimp/postprocess.h>
#include <cstring>
#include <cstdint>
#include <vector>

namespace AssimpFuzz {

// Unregisters all loaders except the ones matching the given extension.
// Returns true if at least one loader was kept.
inline bool ForceFormat(Assimp::Importer& importer, const char* targetExtension) {
    size_t count = importer.GetImporterCount();
    std::vector<Assimp::BaseImporter*> toRemove;
    bool found = false;

    for (size_t i = 0; i < count; ++i) {
        const aiImporterDesc* desc = importer.GetImporterInfo(i);
        Assimp::BaseImporter* imp = importer.GetImporter(i);
        
        if (!desc || !imp) continue;

        // Check if the importer supports the target extension
        // mFileExtensions is a space-separated list (e.g., "obj mod")
        // We wrap target in spaces or check bounds to be precise, 
        // but for fuzzing, a simple strstr is usually sufficient 
        // if the target string is unique enough (e.g. "gltf", "obj").
        // A more robust check:
        
        bool isTarget = false;
        const char* extList = desc->mFileExtensions;
        if (!extList) {
            toRemove.push_back(imp);
            continue;
        }
        const size_t targetLen = strlen(targetExtension);

        const char* p = extList;
        while ((p = strstr(p, targetExtension)) != nullptr) {
            // Check boundaries: extensions are space-separated (e.g., "obj mod").
            // At start of string, treat as having implicit space boundary.
            const char prev = (p == extList) ? ' ' : *(p - 1);
            const char next = *(p + targetLen);
            
            if (prev == ' ' && (next == ' ' || next == '\0')) {
                isTarget = true;
                break;
            }
            p++;
        }

        if (isTarget) {
            found = true;
        } else {
            toRemove.push_back(imp);
        }
    }

    for (auto* imp : toRemove) {
        importer.UnregisterLoader(imp);
        delete imp;  // Free the unregistered importer to prevent memory leaks
    }

    return found;
}

// Generate varied post-processing flags based on input data to maximize coverage.
// Uses bytes from the input to deterministically select which flags to enable.
inline unsigned int GetProcessingFlags(const uint8_t* data, size_t dataSize) {
    // Base flags that are always useful
    unsigned int flags = aiProcess_ValidateDataStructure;

    if (dataSize < 2) {
        return flags | aiProcessPreset_TargetRealtime_Fast;
    }

    // Use first two bytes to select flag combinations
    uint8_t selector = data[0];
    uint8_t extras = data[1];

    // Select base preset based on first byte
    switch (selector % 4) {
        case 0:
            flags |= aiProcessPreset_TargetRealtime_Fast;
            break;
        case 1:
            flags |= aiProcessPreset_TargetRealtime_Quality;
            break;
        case 2:
            flags |= aiProcessPreset_TargetRealtime_MaxQuality;
            break;
        case 3:
            // Minimal processing - just validation
            break;
    }

    // Add extra flags based on second byte bits
    // Note: GenNormals and GenSmoothNormals are mutually exclusive in assimp.
    // We intentionally allow both to be set to test assimp's handling of
    // invalid flag combinations - this is valid fuzzing behavior.
    if (extras & 0x01) flags |= aiProcess_CalcTangentSpace;
    if (extras & 0x02) flags |= aiProcess_GenNormals;
    if (extras & 0x04) flags |= aiProcess_GenSmoothNormals;
    if (extras & 0x08) flags |= aiProcess_FixInfacingNormals;
    if (extras & 0x10) flags |= aiProcess_FindDegenerates;
    if (extras & 0x20) flags |= aiProcess_FindInvalidData;
    if (extras & 0x40) flags |= aiProcess_OptimizeMeshes;
    if (extras & 0x80) flags |= aiProcess_OptimizeGraph;

    // Use third byte for more flags if available
    if (dataSize >= 3) {
        uint8_t more = data[2];
        if (more & 0x01) flags |= aiProcess_SplitLargeMeshes;
        if (more & 0x02) flags |= aiProcess_ImproveCacheLocality;
        if (more & 0x04) flags |= aiProcess_RemoveRedundantMaterials;
        if (more & 0x08) flags |= aiProcess_SortByPType;
        if (more & 0x10) flags |= aiProcess_FindInstances;
        if (more & 0x20) flags |= aiProcess_GenUVCoords;
        if (more & 0x40) flags |= aiProcess_TransformUVCoords;
        if (more & 0x80) flags |= aiProcess_Triangulate;
    }

    return flags;
}

// Generate export-appropriate preprocessing flags.
// Export flags are a subset of import flags that make sense for export operations.
// Uses up to 2 bytes from input for ~65k flag combinations.
inline unsigned int GetExportFlags(const uint8_t* data, size_t dataSize) {
    unsigned int flags = aiProcess_ValidateDataStructure;

    if (dataSize < 1) {
        return flags | aiProcess_Triangulate;
    }

    uint8_t selector = data[0];

    // Export-appropriate flags based on first input byte
    // Note: GenNormals and GenSmoothNormals are mutually exclusive in assimp.
    // We intentionally allow both to be set to test assimp's handling of
    // invalid flag combinations - this is valid fuzzing behavior.
    if (selector & 0x01) flags |= aiProcess_Triangulate;
    if (selector & 0x02) flags |= aiProcess_JoinIdenticalVertices;
    if (selector & 0x04) flags |= aiProcess_GenNormals;
    if (selector & 0x08) flags |= aiProcess_GenSmoothNormals;
    if (selector & 0x10) flags |= aiProcess_CalcTangentSpace;
    if (selector & 0x20) flags |= aiProcess_FlipUVs;
    if (selector & 0x40) flags |= aiProcess_FlipWindingOrder;
    if (selector & 0x80) flags |= aiProcess_PreTransformVertices;

    // Additional export flags from second byte
    if (dataSize >= 2) {
        uint8_t extras = data[1];
        if (extras & 0x01) flags |= aiProcess_OptimizeMeshes;
        if (extras & 0x02) flags |= aiProcess_OptimizeGraph;
        if (extras & 0x04) flags |= aiProcess_SortByPType;
        if (extras & 0x08) flags |= aiProcess_RemoveRedundantMaterials;
        if (extras & 0x10) flags |= aiProcess_FixInfacingNormals;
        if (extras & 0x20) flags |= aiProcess_GenUVCoords;
        if (extras & 0x40) flags |= aiProcess_TransformUVCoords;
        if (extras & 0x80) flags |= aiProcess_SplitLargeMeshes;
    }

    return flags;
}

}
