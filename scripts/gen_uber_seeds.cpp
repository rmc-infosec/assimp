// Generate maximally feature-rich export seeds by constructing aiScene programmatically
// Compile: g++ -O2 -o gen_uber_seeds gen_uber_seeds.cpp -I../include -L../build_test/lib -lassimpd -lpthread
#include <assimp/scene.h>
#include <assimp/Importer.hpp>
#include <assimp/Exporter.hpp>
#include <assimp/postprocess.h>
#include <assimp/material.h>
#include <assimp/mesh.h>
#include <assimp/anim.h>
#include <assimp/camera.h>
#include <assimp/light.h>
#include <assimp/texture.h>
#include <assimp/metadata.h>
#include <cstring>
#include <cstdio>
#include <cmath>
#include <vector>
#include <string>

// Create a minimal 4x4 PNG (RGBA, 16 pixels)
static std::vector<unsigned char> makeMiniPNG() {
    // Minimal valid 8x1 PNG
    static const unsigned char png[] = {
        0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A, // PNG signature
        0x00,0x00,0x00,0x0D, 0x49,0x48,0x44,0x52, // IHDR chunk
        0x00,0x00,0x00,0x02, 0x00,0x00,0x00,0x02, // 2x2
        0x08,0x02, 0x00,0x00,0x00, 0xFD,0xD4,0x9A,0x73, // 8-bit RGB, CRC
        0x00,0x00,0x00,0x12, 0x49,0x44,0x41,0x54, // IDAT
        0x78,0x9C,0x62,0xF8,0xCF,0xC0,0x00,0x00,0x00,0x00,
        0x06,0x00,0x02,0x00,0x99,0x7D,0x3C,0xEB,
        0x00,0x00,0x00,0x00, 0x49,0x45,0x4E,0x44, // IEND
        0xAE,0x42,0x60,0x82
    };
    return std::vector<unsigned char>(png, png + sizeof(png));
}

aiScene* buildUberScene() {
    aiScene* scene = new aiScene();

    // ===== ROOT NODE with hierarchy =====
    scene->mRootNode = new aiNode("RootNode");
    scene->mRootNode->mNumChildren = 9;
    scene->mRootNode->mChildren = new aiNode*[9];

    aiNode* meshNode = new aiNode("MeshNode");
    meshNode->mParent = scene->mRootNode;
    meshNode->mNumMeshes = 1;
    meshNode->mMeshes = new unsigned int[1]{0};
    scene->mRootNode->mChildren[0] = meshNode;

    aiNode* skinnedMeshNode = new aiNode("SkinnedMeshNode");
    skinnedMeshNode->mParent = scene->mRootNode;
    skinnedMeshNode->mNumMeshes = 1;
    skinnedMeshNode->mMeshes = new unsigned int[1]{1};
    scene->mRootNode->mChildren[1] = skinnedMeshNode;

    // Bone nodes: Bone0 -> Bone1 -> Bone2, and Bone3 -> Bone4 -> Bone5
    aiNode* bone0 = new aiNode("Bone0");
    bone0->mParent = scene->mRootNode;
    bone0->mNumChildren = 1;
    bone0->mChildren = new aiNode*[1];
    scene->mRootNode->mChildren[2] = bone0;

    aiNode* bone1 = new aiNode("Bone1");
    bone1->mParent = bone0;
    bone0->mChildren[0] = bone1;
    bone1->mNumChildren = 1;
    bone1->mChildren = new aiNode*[1];

    aiNode* bone2 = new aiNode("Bone2");
    bone2->mParent = bone1;
    bone1->mChildren[0] = bone2;

    aiNode* bone3 = new aiNode("Bone3");
    bone3->mParent = scene->mRootNode;
    bone3->mNumChildren = 1;
    bone3->mChildren = new aiNode*[1];
    scene->mRootNode->mChildren[3] = bone3;

    aiNode* bone4 = new aiNode("Bone4");
    bone4->mParent = bone3;
    bone3->mChildren[0] = bone4;
    bone4->mNumChildren = 1;
    bone4->mChildren = new aiNode*[1];

    aiNode* bone5 = new aiNode("Bone5");
    bone5->mParent = bone4;
    bone4->mChildren[0] = bone5;

    // Camera + Light nodes
    aiNode* camNode = new aiNode("Camera1");
    camNode->mParent = scene->mRootNode;
    scene->mRootNode->mChildren[4] = camNode;

    aiNode* camNode2 = new aiNode("OrthoCamera");
    camNode2->mParent = scene->mRootNode;
    scene->mRootNode->mChildren[5] = camNode2;

    aiNode* lightNode = new aiNode("PointLight1");
    lightNode->mParent = scene->mRootNode;
    scene->mRootNode->mChildren[6] = lightNode;

    aiNode* spotLightNode = new aiNode("SpotLight");
    spotLightNode->mParent = scene->mRootNode;
    scene->mRootNode->mChildren[7] = spotLightNode;

    aiNode* dirLightNode = new aiNode("DirLight");
    dirLightNode->mParent = scene->mRootNode;
    scene->mRootNode->mChildren[8] = dirLightNode;

    // ===== MESHES =====
    scene->mNumMeshes = 2;
    scene->mMeshes = new aiMesh*[2];

    // Mesh 0: basic mesh with UVs, normals, tangents, vertex colors, morph targets
    {
        aiMesh* mesh = new aiMesh();
        mesh->mName = aiString("BasicMesh");
        mesh->mNumVertices = 6;
        mesh->mPrimitiveTypes = aiPrimitiveType_TRIANGLE;
        mesh->mMaterialIndex = 0;

        mesh->mVertices = new aiVector3D[6]{
            {0,0,0},{1,0,0},{0,1,0},{1,1,0},{0,0,1},{1,0,1}
        };
        mesh->mNormals = new aiVector3D[6]{
            {0,0,1},{0,0,1},{0,0,1},{0,0,1},{0,1,0},{0,1,0}
        };
        mesh->mTangents = new aiVector3D[6]{
            {1,0,0},{1,0,0},{1,0,0},{1,0,0},{1,0,0},{1,0,0}
        };
        mesh->mBitangents = new aiVector3D[6]{
            {0,1,0},{0,1,0},{0,1,0},{0,1,0},{0,0,-1},{0,0,-1}
        };

        // 2 UV channels
        mesh->mTextureCoords[0] = new aiVector3D[6]{
            {0,0,0},{1,0,0},{0,1,0},{1,1,0},{0,0,0},{1,0,0}
        };
        mesh->mNumUVComponents[0] = 2;
        mesh->mTextureCoords[1] = new aiVector3D[6]{
            {0.5f,0.5f,0},{0,0,0},{1,0,0},{0,1,0},{1,1,0},{0.5f,0.5f,0}
        };
        mesh->mNumUVComponents[1] = 2;

        // Vertex colors
        mesh->mColors[0] = new aiColor4D[6]{
            {1,0,0,1},{0,1,0,1},{0,0,1,1},{1,1,0,1},{1,0,1,1},{0,1,1,1}
        };

        mesh->mNumFaces = 2;
        mesh->mFaces = new aiFace[2];
        mesh->mFaces[0].mNumIndices = 3;
        mesh->mFaces[0].mIndices = new unsigned int[3]{0,1,2};
        mesh->mFaces[1].mNumIndices = 3;
        mesh->mFaces[1].mIndices = new unsigned int[3]{3,4,5};

        // Morph targets (2 targets)
        mesh->mNumAnimMeshes = 2;
        mesh->mAnimMeshes = new aiAnimMesh*[2];

        aiAnimMesh* morph0 = new aiAnimMesh();
        morph0->mName = aiString("MorphTarget0");
        morph0->mNumVertices = 6;
        morph0->mVertices = new aiVector3D[6]{
            {0,0.1f,0},{1,0.1f,0},{0,1.1f,0},{1,1.1f,0},{0,0.1f,1},{1,0.1f,1}
        };
        morph0->mNormals = new aiVector3D[6]{
            {0,0.1f,1},{0,0.1f,1},{0,0.1f,1},{0,0.1f,1},{0,1,0.1f},{0,1,0.1f}
        };
        morph0->mWeight = 0.0f;
        mesh->mAnimMeshes[0] = morph0;

        aiAnimMesh* morph1 = new aiAnimMesh();
        morph1->mName = aiString("MorphTarget1");
        morph1->mNumVertices = 6;
        morph1->mVertices = new aiVector3D[6]{
            {0,-0.2f,0},{1,-0.2f,0},{0,0.8f,0},{1,0.8f,0},{0,-0.2f,1},{1,-0.2f,1}
        };
        morph1->mWeight = 0.0f;
        mesh->mAnimMeshes[1] = morph1;

        scene->mMeshes[0] = mesh;
    }

    // Mesh 1: skinned mesh with 6 bones (>4 per vertex for multi-group)
    {
        aiMesh* mesh = new aiMesh();
        mesh->mName = aiString("SkinnedMesh");
        mesh->mNumVertices = 4;
        mesh->mPrimitiveTypes = aiPrimitiveType_TRIANGLE;
        mesh->mMaterialIndex = 1;

        mesh->mVertices = new aiVector3D[4]{
            {0,0,0},{1,0,0},{0,2,0},{1,2,0}
        };
        mesh->mNormals = new aiVector3D[4]{
            {0,0,1},{0,0,1},{0,0,1},{0,0,1}
        };
        mesh->mTextureCoords[0] = new aiVector3D[4]{
            {0,0,0},{1,0,0},{0,1,0},{1,1,0}
        };
        mesh->mNumUVComponents[0] = 2;

        mesh->mNumFaces = 2;
        mesh->mFaces = new aiFace[2];
        mesh->mFaces[0].mNumIndices = 3;
        mesh->mFaces[0].mIndices = new unsigned int[3]{0,1,2};
        mesh->mFaces[1].mNumIndices = 3;
        mesh->mFaces[1].mIndices = new unsigned int[3]{1,3,2};

        // 6 bones - some vertices affected by >4 bones
        mesh->mNumBones = 6;
        mesh->mBones = new aiBone*[6];
        const char* boneNames[] = {"Bone0","Bone1","Bone2","Bone3","Bone4","Bone5"};
        for (int b = 0; b < 6; b++) {
            aiBone* bone = new aiBone();
            bone->mName = aiString(boneNames[b]);
            bone->mOffsetMatrix = aiMatrix4x4();
            // Each bone affects vertex 0 and 1 with small weight
            bone->mNumWeights = 2;
            bone->mWeights = new aiVertexWeight[2]{
                {0, 1.0f/6.0f},
                {1, 1.0f/6.0f}
            };
            // Also affect vertex 2 and 3 with some bones
            if (b < 3) {
                bone->mNumWeights = 3;
                delete[] bone->mWeights;
                bone->mWeights = new aiVertexWeight[3]{
                    {0, 1.0f/6.0f},
                    {1, 1.0f/6.0f},
                    {(unsigned int)(2 + b%2), 0.33f}
                };
            }
            mesh->mBones[b] = bone;
        }

        scene->mMeshes[1] = mesh;
    }

    // ===== MATERIALS =====
    scene->mNumMaterials = 2;
    scene->mMaterials = new aiMaterial*[2];

    // Material 0: PBR metallic-roughness with textures
    {
        aiMaterial* mat = new aiMaterial();
        aiString name("PBR_Material");
        mat->AddProperty(&name, AI_MATKEY_NAME);

        aiColor4D baseColor(0.8f, 0.2f, 0.1f, 1.0f);
        mat->AddProperty(&baseColor, 1, AI_MATKEY_BASE_COLOR);

        float metallic = 0.5f, roughness = 0.7f;
        mat->AddProperty(&metallic, 1, AI_MATKEY_METALLIC_FACTOR);
        mat->AddProperty(&roughness, 1, AI_MATKEY_ROUGHNESS_FACTOR);

        // Diffuse texture
        aiString texPath("*0");  // embedded texture index 0
        mat->AddProperty(&texPath, AI_MATKEY_TEXTURE_DIFFUSE(0));

        // Texture wrapping modes
        int wrapU = aiTextureMapMode_Wrap;
        int wrapV = aiTextureMapMode_Mirror;
        mat->AddProperty(&wrapU, 1, AI_MATKEY_MAPPINGMODE_U_DIFFUSE(0));
        mat->AddProperty(&wrapV, 1, AI_MATKEY_MAPPINGMODE_V_DIFFUSE(0));

        // Normal map
        aiString normalPath("*0");
        mat->AddProperty(&normalPath, AI_MATKEY_TEXTURE_NORMALS(0));

        // Emissive
        aiColor3D emissive(0.1f, 0.05f, 0.0f);
        mat->AddProperty(&emissive, 1, AI_MATKEY_COLOR_EMISSIVE);

        float opacity = 0.9f;
        mat->AddProperty(&opacity, 1, AI_MATKEY_OPACITY);

        scene->mMaterials[0] = mat;
    }

    // Material 1: Phong material
    {
        aiMaterial* mat = new aiMaterial();
        aiString name("Phong_Material");
        mat->AddProperty(&name, AI_MATKEY_NAME);

        aiColor3D diffuse(0.5f, 0.5f, 0.8f);
        aiColor3D specular(1.0f, 1.0f, 1.0f);
        aiColor3D ambient(0.1f, 0.1f, 0.1f);
        float shininess = 32.0f;

        mat->AddProperty(&diffuse, 1, AI_MATKEY_COLOR_DIFFUSE);
        mat->AddProperty(&specular, 1, AI_MATKEY_COLOR_SPECULAR);
        mat->AddProperty(&ambient, 1, AI_MATKEY_COLOR_AMBIENT);
        mat->AddProperty(&shininess, 1, AI_MATKEY_SHININESS);

        int shadingModel = aiShadingMode_Phong;
        mat->AddProperty(&shadingModel, 1, AI_MATKEY_SHADING_MODEL);

        scene->mMaterials[1] = mat;
    }

    // ===== EMBEDDED TEXTURE =====
    scene->mNumTextures = 1;
    scene->mTextures = new aiTexture*[1];
    {
        aiTexture* tex = new aiTexture();
        auto png = makeMiniPNG();
        tex->mWidth = png.size();
        tex->mHeight = 0;  // compressed
        memcpy(tex->achFormatHint, "png", 4);
        tex->pcData = (aiTexel*)new unsigned char[png.size()];
        memcpy(tex->pcData, png.data(), png.size());
        scene->mTextures[0] = tex;
    }

    // ===== CAMERAS =====
    scene->mNumCameras = 2;
    scene->mCameras = new aiCamera*[2];
    {
        aiCamera* cam = new aiCamera();
        cam->mName = aiString("Camera1");
        cam->mPosition = aiVector3D(5, 5, 5);
        cam->mLookAt = aiVector3D(0, 0, 0);
        cam->mUp = aiVector3D(0, 1, 0);
        cam->mHorizontalFOV = 0.7854f;  // ~45 degrees
        cam->mClipPlaneNear = 0.1f;
        cam->mClipPlaneFar = 100.0f;
        cam->mAspect = 1.778f;  // 16:9
        scene->mCameras[0] = cam;
    }
    {
        // Orthographic camera
        aiCamera* cam = new aiCamera();
        cam->mName = aiString("OrthoCamera");
        cam->mPosition = aiVector3D(0, 10, 0);
        cam->mLookAt = aiVector3D(0, 0, 0);
        cam->mUp = aiVector3D(0, 0, -1);
        cam->mHorizontalFOV = 0.0f;  // triggers ortho mode in some exporters
        cam->mOrthographicWidth = 5.0f;
        cam->mClipPlaneNear = 0.5f;
        cam->mClipPlaneFar = 50.0f;
        scene->mCameras[1] = cam;
    }

    // ===== LIGHTS =====
    scene->mNumLights = 3;
    scene->mLights = new aiLight*[3];
    {
        aiLight* light = new aiLight();
        light->mName = aiString("PointLight1");
        light->mType = aiLightSource_POINT;
        light->mPosition = aiVector3D(2, 3, 2);
        light->mColorDiffuse = aiColor3D(1, 1, 1);
        light->mColorSpecular = aiColor3D(1, 1, 1);
        light->mAttenuationConstant = 1.0f;
        light->mAttenuationLinear = 0.09f;
        light->mAttenuationQuadratic = 0.032f;
        scene->mLights[0] = light;
    }
    {
        aiLight* light = new aiLight();
        light->mName = aiString("SpotLight");
        light->mType = aiLightSource_SPOT;
        light->mPosition = aiVector3D(0, 5, 0);
        light->mDirection = aiVector3D(0, -1, 0);
        light->mColorDiffuse = aiColor3D(1, 0.9f, 0.8f);
        light->mAngleInnerCone = 0.3f;
        light->mAngleOuterCone = 0.5f;
        scene->mLights[1] = light;
    }
    {
        aiLight* light = new aiLight();
        light->mName = aiString("DirLight");
        light->mType = aiLightSource_DIRECTIONAL;
        light->mDirection = aiVector3D(-0.5f, -1, -0.3f);
        light->mColorDiffuse = aiColor3D(0.8f, 0.8f, 1.0f);
        scene->mLights[2] = light;
    }

    // ===== ANIMATIONS =====
    // Single animation with BOTH bone channels AND morph mesh channels
    // (Validator requires mNumChannels > 0 for each animation)
    scene->mNumAnimations = 1;
    scene->mAnimations = new aiAnimation*[1];

    {
        aiAnimation* anim = new aiAnimation();
        anim->mName = aiString("UberAnimation");
        anim->mDuration = 2.0;
        anim->mTicksPerSecond = 24.0;

        // Node channels (bone animation)
        anim->mNumChannels = 2;
        anim->mChannels = new aiNodeAnim*[2];

        // Bone0 rotation
        aiNodeAnim* ch0 = new aiNodeAnim();
        ch0->mNodeName = aiString("Bone0");
        ch0->mNumPositionKeys = 3;
        ch0->mPositionKeys = new aiVectorKey[3]{
            {0.0, {0,0,0}}, {1.0, {0,1,0}}, {2.0, {0,0,0}}
        };
        ch0->mNumRotationKeys = 3;
        ch0->mRotationKeys = new aiQuatKey[3]{
            {0.0, aiQuaternion(0,0,0,1)},
            {1.0, aiQuaternion(0.707f,0,0,0.707f)},
            {2.0, aiQuaternion(0,0,0,1)}
        };
        ch0->mNumScalingKeys = 3;
        ch0->mScalingKeys = new aiVectorKey[3]{
            {0.0, {1,1,1}}, {1.0, {1.2f,1.2f,1.2f}}, {2.0, {1,1,1}}
        };
        anim->mChannels[0] = ch0;

        // Bone1 rotation
        aiNodeAnim* ch1 = new aiNodeAnim();
        ch1->mNodeName = aiString("Bone1");
        ch1->mNumPositionKeys = 2;
        ch1->mPositionKeys = new aiVectorKey[2]{
            {0.0, {0,1,0}}, {2.0, {0,1,0}}
        };
        ch1->mNumRotationKeys = 3;
        ch1->mRotationKeys = new aiQuatKey[3]{
            {0.0, aiQuaternion(0,0,0,1)},
            {1.0, aiQuaternion(0,0.5f,0,0.866f)},
            {2.0, aiQuaternion(0,0,0,1)}
        };
        ch1->mNumScalingKeys = 1;
        ch1->mScalingKeys = new aiVectorKey[1]{{0.0, {1,1,1}}};
        anim->mChannels[1] = ch1;

        // Morph mesh channels (morph target animation)
        anim->mNumMorphMeshChannels = 1;
        anim->mMorphMeshChannels = new aiMeshMorphAnim*[1];

        aiMeshMorphAnim* morph = new aiMeshMorphAnim();
        morph->mName = aiString("BasicMesh");
        morph->mNumKeys = 3;
        morph->mKeys = new aiMeshMorphKey[3];

        // Key 0: both targets at 0
        morph->mKeys[0].mTime = 0.0;
        morph->mKeys[0].mNumValuesAndWeights = 2;
        morph->mKeys[0].mValues = new unsigned int[2]{0, 1};
        morph->mKeys[0].mWeights = new double[2]{0.0, 0.0};

        // Key 1: target 0 at 1.0, target 1 at 0.5
        morph->mKeys[1].mTime = 1.0;
        morph->mKeys[1].mNumValuesAndWeights = 2;
        morph->mKeys[1].mValues = new unsigned int[2]{0, 1};
        morph->mKeys[1].mWeights = new double[2]{1.0, 0.5};

        // Key 2: both back to 0
        morph->mKeys[2].mTime = 2.0;
        morph->mKeys[2].mNumValuesAndWeights = 2;
        morph->mKeys[2].mValues = new unsigned int[2]{0, 1};
        morph->mKeys[2].mWeights = new double[2]{0.0, 0.0};

        anim->mMorphMeshChannels[0] = morph;
        scene->mAnimations[0] = anim;
    }

    // ===== METADATA =====
    scene->mMetaData = new aiMetadata();
    scene->mMetaData->mNumProperties = 4;
    scene->mMetaData->mKeys = new aiString[4]{
        aiString("generator"), aiString("version"), aiString("scale"), aiString("flag")
    };
    scene->mMetaData->mValues = new aiMetadataEntry[4];

    // String metadata
    scene->mMetaData->mValues[0].mType = AI_AISTRING;
    scene->mMetaData->mValues[0].mData = new aiString("uber_seed_gen");
    // Int metadata
    scene->mMetaData->mValues[1].mType = AI_INT32;
    scene->mMetaData->mValues[1].mData = new int32_t(1);
    // Float metadata
    scene->mMetaData->mValues[2].mType = AI_FLOAT;
    scene->mMetaData->mValues[2].mData = new float(1.0f);
    // Bool metadata
    scene->mMetaData->mValues[3].mType = AI_BOOL;
    scene->mMetaData->mValues[3].mData = new bool(true);

    return scene;
}

void exportScene(const aiScene* scene, const char* formatId, const char* filename,
                 Assimp::ExportProperties* props = nullptr) {
    Assimp::Exporter exporter;
    aiReturn ret = exporter.Export(scene, formatId, filename,
        aiProcess_Triangulate | aiProcess_ValidateDataStructure, props);
    if (ret == aiReturn_SUCCESS) {
        printf("  Exported %s (%s)\n", filename, formatId);
    } else {
        printf("  FAILED %s: %s\n", filename, exporter.GetErrorString());
    }
}

int main(int argc, char** argv) {
    const char* outDir = argc > 1 ? argv[1] : "/tmp/uber_seeds";
    printf("Output dir: %s\n", outDir);

    char cmd[512];
    snprintf(cmd, sizeof(cmd), "mkdir -p %s", outDir);
    system(cmd);

    aiScene* scene = buildUberScene();
    printf("Built uber scene: %d meshes, %d materials, %d cameras, %d lights, %d anims, %d textures\n",
           scene->mNumMeshes, scene->mNumMaterials, scene->mNumCameras,
           scene->mNumLights, scene->mNumAnimations, scene->mNumTextures);
    printf("  Mesh 0: %d verts, %d morphs, tangents=%d, colors=%d\n",
           scene->mMeshes[0]->mNumVertices, scene->mMeshes[0]->mNumAnimMeshes,
           scene->mMeshes[0]->mTangents != nullptr, scene->mMeshes[0]->mColors[0] != nullptr);
    printf("  Mesh 1: %d verts, %d bones\n",
           scene->mMeshes[1]->mNumVertices, scene->mMeshes[1]->mNumBones);

    char path[512];

    // Export to all formats
    snprintf(path, sizeof(path), "%s/uber.fbx", outDir);
    exportScene(scene, "fbx", path);

    snprintf(path, sizeof(path), "%s/uber.fbxa", outDir);
    exportScene(scene, "fbxa", path);

    snprintf(path, sizeof(path), "%s/uber.dae", outDir);
    exportScene(scene, "collada", path);

    // glTF2 with various properties
    {
        Assimp::ExportProperties props;
        props.SetPropertyBool("GLTF2_SPARSE_ACCESSOR_EXP", true);
        props.SetPropertyBool("GLTF2_TARGET_NORMAL_EXP", true);
        props.SetPropertyBool("GLTF2_TARGETNAMES_EXP", true);

        snprintf(path, sizeof(path), "%s/uber_sparse.gltf", outDir);
        exportScene(scene, "gltf2", path, &props);

        snprintf(path, sizeof(path), "%s/uber_sparse.glb", outDir);
        exportScene(scene, "glb2", path, &props);
    }

    // glTF2 with unlimited bones
    {
        Assimp::ExportProperties props;
        props.SetPropertyBool(AI_CONFIG_EXPORT_GLTF_UNLIMITED_SKINNING_BONES_PER_VERTEX, true);
        props.SetPropertyBool("GLTF2_TARGETNAMES_EXP", true);

        snprintf(path, sizeof(path), "%s/uber_unlimitedbones.gltf", outDir);
        exportScene(scene, "gltf2", path, &props);

        snprintf(path, sizeof(path), "%s/uber_unlimitedbones.glb", outDir);
        exportScene(scene, "glb2", path, &props);
    }

    // glTF2 basic
    snprintf(path, sizeof(path), "%s/uber.gltf", outDir);
    exportScene(scene, "gltf2", path);

    snprintf(path, sizeof(path), "%s/uber.glb", outDir);
    exportScene(scene, "glb2", path);

    // glTF v1
    snprintf(path, sizeof(path), "%s/uber_v1.gltf", outDir);
    exportScene(scene, "gltf", path);

    // Other formats
    snprintf(path, sizeof(path), "%s/uber.obj", outDir);
    exportScene(scene, "obj", path);

    snprintf(path, sizeof(path), "%s/uber.stl", outDir);
    exportScene(scene, "stl", path);

    snprintf(path, sizeof(path), "%s/uber.x", outDir);
    exportScene(scene, "x", path);

    snprintf(path, sizeof(path), "%s/uber.3ds", outDir);
    exportScene(scene, "3ds", path);

    snprintf(path, sizeof(path), "%s/uber.assbin", outDir);
    exportScene(scene, "assbin", path);

    snprintf(path, sizeof(path), "%s/uber.assxml", outDir);
    exportScene(scene, "assxml", path);

    snprintf(path, sizeof(path), "%s/uber.assjson", outDir);
    exportScene(scene, "assjson", path);

    snprintf(path, sizeof(path), "%s/uber.m3d", outDir);
    exportScene(scene, "m3d", path);

    snprintf(path, sizeof(path), "%s/uber.x3d", outDir);
    exportScene(scene, "x3d", path);

    snprintf(path, sizeof(path), "%s/uber.pbrt", outDir);
    exportScene(scene, "pbrt", path);

    delete scene;
    printf("\nDone!\n");
    return 0;
}
