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

// C API fuzzer: Exercises the C binding layer (Assimp.cpp)
// Covers aiImportFileFromMemory*, aiGetMaterialProperty, scene traversal, etc.

#include "fuzzer_common.h"
#include <assimp/cimport.h>
#include <assimp/cexport.h>
#include <assimp/scene.h>
#include <assimp/postprocess.h>
#include <assimp/material.h>
#include <assimp/version.h>
#include <assimp/config.h>
#include <cstring>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (!AssimpFuzz::IsValidSize(dataSize)) {
        return 0;
    }

    // Exercise version/info APIs
    aiGetVersionMajor();
    aiGetVersionMinor();
    aiGetVersionRevision();
    aiGetCompileFlags();
    aiGetLegalString();
    aiIsExtensionSupported(".obj");
    aiIsExtensionSupported(".fbx");
    aiIsExtensionSupported(".gltf");
    aiString extList;
    aiGetExtensionList(&extList);

    // Exercise logging APIs (covers DefaultLogger.cpp + Assimp.cpp log paths)
    aiEnableVerboseLogging(AI_TRUE);
    aiLogStream logStream;
    logStream.callback = [](const char*, char*) {};
    logStream.user = nullptr;
    aiAttachLogStream(&logStream);

    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);

    // Use C API property store for configuration
    aiPropertyStore* props = aiCreatePropertyStore();
    if (props && dataSize >= 8) {
        aiSetImportPropertyInteger(props, AI_CONFIG_PP_FD_REMOVE, (data[0] & 0x10) ? 1 : 0);
        aiSetImportPropertyFloat(props, AI_CONFIG_PP_GSN_MAX_SMOOTHING_ANGLE,
            20.0f + static_cast<float>(data[1] % 60));
        aiSetImportPropertyInteger(props, AI_CONFIG_PP_RVC_FLAGS, data[2]);
        aiSetImportPropertyInteger(props, AI_CONFIG_PP_LBW_MAX_WEIGHTS, 1 + (data[3] % 8));
        aiSetImportPropertyFloat(props, AI_CONFIG_GLOBAL_SCALE_FACTOR_KEY,
            0.5f + static_cast<float>(data[4] % 20) * 0.1f);

        // Exercise string and matrix property setters
        aiString propStr;
        propStr.Set("fuzz_value");
        aiSetImportPropertyString(props, AI_CONFIG_PP_OG_EXCLUDE_LIST, &propStr);

        aiMatrix4x4 propMat;
        aiIdentityMatrix4(&propMat);
        aiSetImportPropertyMatrix(props, "MAT_PROP", &propMat);
    }

    // Import via C API with property store
    const aiScene* scene = aiImportFileFromMemoryWithProperties(
        reinterpret_cast<const char*>(data), dataSize, flags, "input.obj", props);

    if (props) {
        aiReleasePropertyStore(props);
    }

    if (!scene || !scene->mRootNode) {
        if (scene) {
            aiReleaseImport(scene);
        }
        // Exercise error string API
        aiGetErrorString();
        return 0;
    }

    // Traverse scene to exercise C API accessors
    if (scene->mNumMeshes > 0 && scene->mMeshes) {
        const aiMesh* mesh = scene->mMeshes[0];
        if (mesh) {
            // Exercise mesh queries
            (void)mesh->mNumVertices;
            (void)mesh->mNumFaces;
            (void)mesh->mPrimitiveTypes;
            if (mesh->mNumBones > 0 && mesh->mBones) {
                (void)mesh->mBones[0]->mName;
            }
        }
    }

    // Exercise material C API
    if (scene->mNumMaterials > 0 && scene->mMaterials) {
        const aiMaterial* mat = scene->mMaterials[0];
        if (mat) {
            aiColor4D color;
            aiGetMaterialColor(mat, AI_MATKEY_COLOR_DIFFUSE, &color);
            aiGetMaterialColor(mat, AI_MATKEY_COLOR_SPECULAR, &color);
            aiGetMaterialColor(mat, AI_MATKEY_COLOR_AMBIENT, &color);
            aiGetMaterialColor(mat, AI_MATKEY_COLOR_EMISSIVE, &color);

            float fval;
            unsigned int max = 1;
            aiGetMaterialFloatArray(mat, AI_MATKEY_SHININESS, &fval, &max);
            aiGetMaterialFloatArray(mat, AI_MATKEY_OPACITY, &fval, &max);

            int ival;
            max = 1;
            aiGetMaterialIntegerArray(mat, AI_MATKEY_TWOSIDED, &ival, &max);

            aiString str;
            aiGetMaterialString(mat, AI_MATKEY_NAME, &str);
            aiGetMaterialTexture(mat, aiTextureType_DIFFUSE, 0, &str, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr);
        }
    }

    // Exercise camera, light traversal
    if (scene->mNumCameras > 0 && scene->mCameras) {
        (void)scene->mCameras[0]->mName;
    }
    if (scene->mNumLights > 0 && scene->mLights) {
        (void)scene->mLights[0]->mName;
    }
    if (scene->mNumAnimations > 0 && scene->mAnimations) {
        (void)scene->mAnimations[0]->mName;
    }
    if (scene->mNumTextures > 0 && scene->mTextures) {
        (void)scene->mTextures[0]->mWidth;
    }

    // Apply post-processing via C API
    const aiScene* processed = aiApplyPostProcessing(scene, aiProcess_Triangulate);
    (void)processed;

    // Get memory requirements
    aiMemoryInfo info;
    aiGetMemoryRequirements(scene, &info);

    // Exercise importer info APIs
    size_t importerCount = aiGetImportFormatCount();
    if (importerCount > 0) {
        (void)aiGetImportFormatDescription(0);
    }
    aiGetImporterDesc("obj");

    // Exercise comprehensive math utility APIs from Assimp.cpp
    // This covers lines 608-1283 of Assimp.cpp

    // --- Matrix setup ---
    aiMatrix4x4 m4;
    aiIdentityMatrix4(&m4);
    aiMatrix3x3 m3;
    aiIdentityMatrix3(&m3);
    aiTransposeMatrix4(&m4);
    aiTransposeMatrix3(&m3);

    aiVector3D v3 = {1.0f, 2.0f, 3.0f};
    aiTransformVecByMatrix4(&v3, &m4);
    aiTransformVecByMatrix3(&v3, &m3);

    aiMatrix4x4 m4b;
    aiIdentityMatrix4(&m4b);
    aiMultiplyMatrix4(&m4, &m4b);
    aiMultiplyMatrix3(&m3, &m3);

    aiVector3D scaling, position;
    aiQuaternion rotation;
    aiDecomposeMatrix(&m4, &scaling, &rotation, &position);

    aiQuaternion quat;
    aiCreateQuaternionFromMatrix(&quat, &m3);

    // --- Vector2D API (Assimp.cpp lines 692-797) ---
    aiVector2D v2a = {1.0f, 2.0f};
    aiVector2D v2b = {3.0f, 4.0f};
    (void)aiVector2AreEqual(&v2a, &v2b);
    (void)aiVector2AreEqualEpsilon(&v2a, &v2b, 0.001f);
    aiVector2Add(&v2a, &v2b);
    aiVector2Subtract(&v2a, &v2b);
    aiVector2Scale(&v2a, 2.0f);
    aiVector2SymMul(&v2a, &v2b);
    aiVector2DivideByScalar(&v2a, 2.0f);
    aiVector2DivideByVector(&v2a, &v2b);
    (void)aiVector2Length(&v2a);
    (void)aiVector2SquareLength(&v2a);
    aiVector2Negate(&v2a);
    (void)aiVector2DotProduct(&v2a, &v2b);
    aiVector2Normalize(&v2a);

    // --- Vector3D API (Assimp.cpp lines 800-941) ---
    aiVector3D v3a = {1.0f, 2.0f, 3.0f};
    aiVector3D v3b = {4.0f, 5.0f, 6.0f};
    (void)aiVector3AreEqual(&v3a, &v3b);
    (void)aiVector3AreEqualEpsilon(&v3a, &v3b, 0.001f);
    (void)aiVector3LessThan(&v3a, &v3b);
    aiVector3Add(&v3a, &v3b);
    aiVector3Subtract(&v3a, &v3b);
    aiVector3Scale(&v3a, 2.0f);
    aiVector3SymMul(&v3a, &v3b);
    aiVector3DivideByScalar(&v3a, 2.0f);
    aiVector3DivideByVector(&v3a, &v3b);
    (void)aiVector3Length(&v3a);
    (void)aiVector3SquareLength(&v3a);
    aiVector3Negate(&v3a);
    (void)aiVector3DotProduct(&v3a, &v3b);
    aiVector3D v3cross;
    aiVector3CrossProduct(&v3cross, &v3a, &v3b);
    aiVector3D v3norm = {1.0f, 2.0f, 3.0f};
    aiVector3Normalize(&v3norm);
    aiVector3D v3safe = {0.0f, 0.0f, 0.0f};
    aiVector3NormalizeSafe(&v3safe);
    aiVector3D v3rot = {1.0f, 0.0f, 0.0f};
    aiQuaternion qrot = {1.0f, 0.0f, 0.0f, 0.0f};
    aiVector3RotateByQuaternion(&v3rot, &qrot);

    // --- Matrix3x3 API (Assimp.cpp lines 943-1028) ---
    aiMatrix3x3 m3a, m3b;
    aiIdentityMatrix3(&m3a);
    aiIdentityMatrix3(&m3b);
    aiMatrix3FromMatrix4(&m3a, &m4);
    aiMatrix3FromQuaternion(&m3a, &qrot);
    (void)aiMatrix3AreEqual(&m3a, &m3b);
    (void)aiMatrix3AreEqualEpsilon(&m3a, &m3b, 0.001f);
    aiMatrix3Inverse(&m3a);
    (void)aiMatrix3Determinant(&m3a);
    aiMatrix3RotationZ(&m3a, 0.5f);
    aiVector3D axis3 = {0.0f, 1.0f, 0.0f};
    aiMatrix3FromRotationAroundAxis(&m3a, &axis3, 0.5f);
    aiVector2D trans2 = {1.0f, 2.0f};
    aiMatrix3Translation(&m3a, &trans2);
    aiVector3D from3 = {1.0f, 0.0f, 0.0f};
    aiVector3D to3 = {0.0f, 1.0f, 0.0f};
    aiMatrix3FromTo(&m3a, &from3, &to3);

    // --- Matrix4x4 API (Assimp.cpp lines 1030-1207) ---
    aiMatrix4x4 m4c;
    aiMatrix4FromMatrix3(&m4c, &m3b);
    aiVector3D scl4 = {1.0f, 1.0f, 1.0f};
    aiVector3D pos4 = {0.0f, 0.0f, 0.0f};
    aiQuaternion rot4 = {1.0f, 0.0f, 0.0f, 0.0f};
    aiMatrix4FromScalingQuaternionPosition(&m4c, &scl4, &rot4, &pos4);
    aiMatrix4Add(&m4, &m4b);
    (void)aiMatrix4AreEqual(&m4, &m4b);
    (void)aiMatrix4AreEqualEpsilon(&m4, &m4b, 0.001f);
    aiMatrix4x4 m4inv;
    aiIdentityMatrix4(&m4inv);
    aiMatrix4Inverse(&m4inv);
    (void)aiMatrix4Determinant(&m4inv);
    (void)aiMatrix4IsIdentity(&m4inv);
    aiVector3D dscl, drot_euler, dpos;
    aiMatrix4DecomposeIntoScalingEulerAnglesPosition(&m4inv, &dscl, &drot_euler, &dpos);
    aiVector3D daxis;
    ai_real dangle;
    aiMatrix4DecomposeIntoScalingAxisAnglePosition(&m4inv, &dscl, &daxis, &dangle, &dpos);
    aiQuaternion dqrot;
    aiMatrix4DecomposeNoScaling(&m4inv, &dqrot, &dpos);
    aiMatrix4FromEulerAngles(&m4c, 0.1f, 0.2f, 0.3f);
    aiMatrix4RotationX(&m4c, 0.5f);
    aiMatrix4RotationY(&m4c, 0.5f);
    aiMatrix4RotationZ(&m4c, 0.5f);
    aiVector3D axis4 = {0.0f, 0.0f, 1.0f};
    aiMatrix4FromRotationAroundAxis(&m4c, &axis4, 0.5f);
    aiVector3D trans4 = {1.0f, 2.0f, 3.0f};
    aiMatrix4Translation(&m4c, &trans4);
    aiVector3D scale4 = {2.0f, 2.0f, 2.0f};
    aiMatrix4Scaling(&m4c, &scale4);
    aiVector3D from4 = {1.0f, 0.0f, 0.0f};
    aiVector3D to4 = {0.0f, 0.0f, 1.0f};
    aiMatrix4FromTo(&m4c, &from4, &to4);

    // --- Quaternion API (Assimp.cpp lines 1208-1283) ---
    aiQuaternion q1;
    aiQuaternionFromEulerAngles(&q1, 0.1f, 0.2f, 0.3f);
    aiVector3D qaxis = {0.0f, 1.0f, 0.0f};
    aiQuaternionFromAxisAngle(&q1, &qaxis, 0.5f);
    aiVector3D qnorm = {0.0f, 0.707f, 0.707f};
    aiQuaternionFromNormalizedQuaternion(&q1, &qnorm);
    aiQuaternion q2 = {1.0f, 0.0f, 0.0f, 0.0f};
    (void)aiQuaternionAreEqual(&q1, &q2);
    (void)aiQuaternionAreEqualEpsilon(&q1, &q2, 0.001f);
    aiQuaternionNormalize(&q1);
    aiQuaternionConjugate(&q1);
    aiQuaternionMultiply(&q1, &q2);
    aiQuaternion qinterp;
    aiQuaternionInterpolate(&qinterp, &q1, &q2, 0.5f);

    // Exercise embedded texture API
    aiGetEmbeddedTexture(scene, "*0");

    // Exercise export C API (AssimpCExport.cpp)
    size_t exportCount = aiGetExportFormatCount();
    if (exportCount > 0) {
        const aiExportFormatDesc* desc = aiGetExportFormatDescription(0);
        if (desc) {
            // Export to blob using first available format
            const aiExportDataBlob* blob = aiExportSceneToBlob(scene, desc->id, 0);
            if (blob) {
                aiReleaseExportBlob(blob);
            }
            aiReleaseExportFormatDescription(desc);
        }
    }

    // Exercise aiCopyScene (covers SceneCombiner::CopyScene)
    aiScene* sceneCopy = nullptr;
    aiCopyScene(scene, &sceneCopy);
    if (sceneCopy) {
        aiFreeScene(sceneCopy);
    }

    aiReleaseImport(scene);

    // Detach log streams (covers DefaultLogger detach/kill paths)
    aiDetachAllLogStreams();

    return 0;
}
