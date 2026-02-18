/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for SceneCombiner: exercises MergeScenes, MergeMeshes,
MergeMaterials, Copy(aiMetadata/aiTexture/aiAnimMesh/aiMeshMorphAnim),
and related helper functions that are not reached through normal
import paths in the in-memory fuzzing environment.
---------------------------------------------------------------------------
*/
#include <assimp/SceneCombiner.h>
#include <assimp/scene.h>
#include <assimp/mesh.h>
#include <assimp/material.h>
#include <assimp/anim.h>
#include <assimp/camera.h>
#include <assimp/light.h>
#include <assimp/metadata.h>
#include <assimp/texture.h>
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <vector>

using namespace Assimp;

// Build a simple mesh with optional bones and morph targets
static aiMesh *MakeMesh(uint8_t flags, int id) {
    aiMesh *m = new aiMesh();
    m->mPrimitiveTypes = aiPrimitiveType_TRIANGLE;
    m->mNumVertices = 3;
    m->mVertices = new aiVector3D[3]{
        {0.0f + id, 0.0f, 0.0f},
        {1.0f + id, 0.0f, 0.0f},
        {0.0f + id, 1.0f, 0.0f}};
    m->mNumFaces = 1;
    m->mFaces = new aiFace[1];
    m->mFaces[0].mNumIndices = 3;
    m->mFaces[0].mIndices = new unsigned int[3]{0, 1, 2};
    m->mMaterialIndex = 0;

    // Normals
    if (flags & 0x01) {
        m->mNormals = new aiVector3D[3]{
            {0, 0, 1}, {0, 0, 1}, {0, 0, 1}};
    }

    // Texture coords
    if (flags & 0x02) {
        m->mTextureCoords[0] = new aiVector3D[3]{
            {0, 0, 0}, {1, 0, 0}, {0, 1, 0}};
        m->mNumUVComponents[0] = 2;
    }

    // Vertex colors
    if (flags & 0x04) {
        m->mColors[0] = new aiColor4D[3]{
            {1, 0, 0, 1}, {0, 1, 0, 1}, {0, 0, 1, 1}};
    }

    // Bones
    if (flags & 0x08) {
        m->mNumBones = 1;
        m->mBones = new aiBone *[1];
        m->mBones[0] = new aiBone();
        m->mBones[0]->mName = aiString("Bone0");
        m->mBones[0]->mNumWeights = 3;
        m->mBones[0]->mWeights = new aiVertexWeight[3]{
            {0, 1.0f}, {1, 0.8f}, {2, 0.6f}};
    }

    // AnimMeshes (morph targets)
    if (flags & 0x10) {
        m->mNumAnimMeshes = 1;
        m->mAnimMeshes = new aiAnimMesh *[1];
        m->mAnimMeshes[0] = new aiAnimMesh();
        m->mAnimMeshes[0]->mNumVertices = 3;
        m->mAnimMeshes[0]->mVertices = new aiVector3D[3]{
            {0.1f + id, 0.1f, 0.0f},
            {1.1f + id, 0.1f, 0.0f},
            {0.1f + id, 1.1f, 0.0f}};
        m->mAnimMeshes[0]->mWeight = 0.5f;
    }

    return m;
}

static aiMaterial *MakeMaterial(int id) {
    aiMaterial *mat = new aiMaterial();
    aiString name("Mat" + std::to_string(id));
    mat->AddProperty(&name, AI_MATKEY_NAME);
    aiColor3D color(0.5f + id * 0.1f, 0.3f, 0.2f);
    mat->AddProperty(&color, 1, AI_MATKEY_COLOR_DIFFUSE);
    return mat;
}

static aiAnimation *MakeAnimation(uint8_t flags, int id) {
    aiAnimation *anim = new aiAnimation();
    anim->mName = aiString("Anim" + std::to_string(id));
    anim->mDuration = 1.0;
    anim->mTicksPerSecond = 24.0;

    // Bone animation channel
    anim->mNumChannels = 1;
    anim->mChannels = new aiNodeAnim *[1];
    anim->mChannels[0] = new aiNodeAnim();
    anim->mChannels[0]->mNodeName = aiString("Node" + std::to_string(id));
    anim->mChannels[0]->mNumPositionKeys = 1;
    anim->mChannels[0]->mPositionKeys = new aiVectorKey[1]{{0.0, {0, 0, 0}}};
    anim->mChannels[0]->mNumRotationKeys = 1;
    anim->mChannels[0]->mRotationKeys = new aiQuatKey[1]{{0.0, {1, 0, 0, 0}}};
    anim->mChannels[0]->mNumScalingKeys = 1;
    anim->mChannels[0]->mScalingKeys = new aiVectorKey[1]{{0.0, {1, 1, 1}}};

    // Morph animation channel
    if (flags & 0x20) {
        anim->mNumMorphMeshChannels = 1;
        anim->mMorphMeshChannels = new aiMeshMorphAnim *[1];
        anim->mMorphMeshChannels[0] = new aiMeshMorphAnim();
        anim->mMorphMeshChannels[0]->mName = aiString("Morph" + std::to_string(id));
        anim->mMorphMeshChannels[0]->mNumKeys = 1;
        anim->mMorphMeshChannels[0]->mKeys = new aiMeshMorphKey[1];
        anim->mMorphMeshChannels[0]->mKeys[0].mTime = 0.0;
        anim->mMorphMeshChannels[0]->mKeys[0].mNumValuesAndWeights = 1;
        anim->mMorphMeshChannels[0]->mKeys[0].mValues = new unsigned int[1]{0};
        anim->mMorphMeshChannels[0]->mKeys[0].mWeights = new double[1]{0.5};
    }

    return anim;
}

static aiNode *MakeNodeTree(const char *name, int numMeshRefs) {
    aiNode *n = new aiNode(name);
    if (numMeshRefs > 0) {
        n->mNumMeshes = numMeshRefs;
        n->mMeshes = new unsigned int[numMeshRefs];
        for (int i = 0; i < numMeshRefs; i++) {
            n->mMeshes[i] = i;
        }
    }
    return n;
}

static aiScene *MakeScene(uint8_t flags, int id) {
    aiScene *scene = new aiScene();

    // Always create at least one mesh and one material
    scene->mNumMeshes = 1;
    scene->mMeshes = new aiMesh *[1]{MakeMesh(flags, id)};

    scene->mNumMaterials = 1;
    scene->mMaterials = new aiMaterial *[1]{MakeMaterial(id)};

    // Root node
    scene->mRootNode = MakeNodeTree(("Root" + std::to_string(id)).c_str(), 1);

    // Add a child node
    aiNode *child = MakeNodeTree(("Child" + std::to_string(id)).c_str(), 0);
    scene->mRootNode->addChildren(1, &child);

    // Cameras
    if (flags & 0x01) {
        scene->mNumCameras = 1;
        scene->mCameras = new aiCamera *[1];
        scene->mCameras[0] = new aiCamera();
        scene->mCameras[0]->mName = aiString("Camera" + std::to_string(id));
    }

    // Lights
    if (flags & 0x02) {
        scene->mNumLights = 1;
        scene->mLights = new aiLight *[1];
        scene->mLights[0] = new aiLight();
        scene->mLights[0]->mName = aiString("Light" + std::to_string(id));
        scene->mLights[0]->mType = aiLightSource_POINT;
    }

    // Animations
    if (flags & 0x04) {
        scene->mNumAnimations = 1;
        scene->mAnimations = new aiAnimation *[1]{MakeAnimation(flags, id)};
    }

    // Textures (embedded)
    if (flags & 0x08) {
        scene->mNumTextures = 1;
        scene->mTextures = new aiTexture *[1];
        scene->mTextures[0] = new aiTexture();
        scene->mTextures[0]->mWidth = 2;
        scene->mTextures[0]->mHeight = 2;
        scene->mTextures[0]->pcData = new aiTexel[4];
        memset(scene->mTextures[0]->pcData, 128, sizeof(aiTexel) * 4);
    }

    // Metadata on root node
    if (flags & 0x10) {
        scene->mMetaData = aiMetadata::Alloc(3);
        scene->mMetaData->Set(0, "IntKey", 42);
        scene->mMetaData->Set(1, "FloatKey", 3.14f);
        scene->mMetaData->Set(2, "StringKey", aiString("hello"));
    }

    return scene;
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (dataSize < 4) {
        return 0;
    }

    const uint8_t masterFlags = data[0];
    const uint8_t srcFlags = data[1];
    const uint8_t mergeFlags = data[2];
    const uint8_t opSelect = data[3];

    // --- Exercise MergeScenes with AttachmentInfo (the biggest uncovered block) ---
    if (opSelect & 0x01) {
        aiScene *master = MakeScene(masterFlags, 0);
        aiScene *src1 = MakeScene(srcFlags, 1);

        // AttachmentInfo is in the Assimp namespace, not a member of SceneCombiner
        std::vector<AttachmentInfo> attachments;
        attachments.push_back(AttachmentInfo(src1, master->mRootNode));

        unsigned int flags = 0;
        if (mergeFlags & 0x01) flags |= AI_INT_MERGE_SCENE_GEN_UNIQUE_NAMES;
        if (mergeFlags & 0x02) flags |= AI_INT_MERGE_SCENE_GEN_UNIQUE_MATNAMES;
        if (mergeFlags & 0x04) flags |= AI_INT_MERGE_SCENE_RESOLVE_CROSS_ATTACHMENTS;
        if (mergeFlags & 0x08) flags |= AI_INT_MERGE_SCENE_GEN_UNIQUE_NAMES_IF_NECESSARY;
        if (mergeFlags & 0x10) flags |= AI_INT_MERGE_SCENE_DUPLICATES_DEEP_CPY;

        aiScene *result = nullptr;
        SceneCombiner::MergeScenes(&result, master, attachments, flags);
        delete result;
    }

    // --- Exercise MergeMeshes directly ---
    // MergeMeshes takes ownership of input meshes (deletes them internally),
    // so we must NOT delete them ourselves afterwards.
    if (opSelect & 0x02) {
        uint8_t simpleFlags = masterFlags & 0x07; // normals, texcoords, colors only
        uint8_t simpleFlags2 = srcFlags & 0x07;
        aiMesh *m1 = MakeMesh(simpleFlags, 0);
        aiMesh *m2 = MakeMesh(simpleFlags2, 1);
        std::vector<aiMesh *> meshes = {m1, m2};

        aiMesh *merged = nullptr;
        SceneCombiner::MergeMeshes(&merged, 0, meshes.begin(), meshes.end());
        delete merged;
    }

    // --- Exercise CopyScene with metadata, textures, morph targets ---
    if (opSelect & 0x04) {
        aiScene *src = MakeScene(masterFlags | 0x1F, 0); // all features
        aiScene *copy = nullptr;
        SceneCombiner::CopyScene(&copy, src);
        delete copy;
        delete src;
    }

    // --- Exercise MergeMaterials ---
    if (opSelect & 0x08) {
        aiMaterial *m1 = MakeMaterial(0);
        aiMaterial *m2 = MakeMaterial(1);

        std::vector<aiMaterial *> mats = {m1, m2};
        aiMaterial *merged = nullptr;
        SceneCombiner::MergeMaterials(&merged, mats.begin(), mats.end());
        delete merged;
        delete m1;
        delete m2;
    }

    // --- Exercise the vector<aiScene*> MergeScenes overload ---
    if (opSelect & 0x10) {
        aiScene *s1 = MakeScene(masterFlags, 0);
        aiScene *s2 = MakeScene(srcFlags, 1);

        std::vector<aiScene *> scenes = {s1, s2};
        aiScene *result = nullptr;
        unsigned int flags = 0;
        if (mergeFlags & 0x01) flags |= AI_INT_MERGE_SCENE_GEN_UNIQUE_NAMES;
        SceneCombiner::MergeScenes(&result, scenes, flags);
        delete result;
    }

    // --- Exercise CopyScene with compressed textures (mWidth>0, mHeight==0) ---
    if (opSelect & 0x20) {
        aiScene *src = new aiScene();
        src->mNumMeshes = 1;
        src->mMeshes = new aiMesh *[1]{MakeMesh(0x01, 0)};
        src->mNumMaterials = 1;
        src->mMaterials = new aiMaterial *[1]{MakeMaterial(0)};
        src->mRootNode = MakeNodeTree("Root", 1);

        // Compressed texture: mHeight==0 means compressed, mWidth is byte count
        src->mNumTextures = 1;
        src->mTextures = new aiTexture *[1];
        src->mTextures[0] = new aiTexture();
        src->mTextures[0]->mWidth = 16; // 16 bytes of "compressed" data
        src->mTextures[0]->mHeight = 0; // signals compressed format
        src->mTextures[0]->pcData =
            reinterpret_cast<aiTexel *>(new uint8_t[16]);
        memset(src->mTextures[0]->pcData, 0xAB, 16);
        strncpy(src->mTextures[0]->achFormatHint, "png", 4);

        aiScene *copy = nullptr;
        SceneCombiner::CopyScene(&copy, src);
        delete copy;
        delete src;
    }

    // --- Exercise MergeMeshes with bones (ownership test) ---
    if (opSelect & 0x40) {
        // Both meshes have bones - tests bone merging path
        aiMesh *m1 = MakeMesh(0x09, 0); // normals + bones
        aiMesh *m2 = MakeMesh(0x09, 1); // normals + bones
        std::vector<aiMesh *> meshes = {m1, m2};

        aiMesh *merged = nullptr;
        SceneCombiner::MergeMeshes(&merged, 0, meshes.begin(), meshes.end());
        delete merged;
    }

    // --- Exercise MergeScenes with multiple animations and channels ---
    if (opSelect & 0x80) {
        aiScene *s1 = MakeScene(masterFlags | 0x24, 0); // cameras + animations + morph
        aiScene *s2 = MakeScene(srcFlags | 0x24, 1);

        std::vector<aiScene *> scenes = {s1, s2};
        aiScene *result = nullptr;
        unsigned int flags = AI_INT_MERGE_SCENE_GEN_UNIQUE_NAMES
            | AI_INT_MERGE_SCENE_GEN_UNIQUE_MATNAMES;
        SceneCombiner::MergeScenes(&result, scenes, flags);
        delete result;
    }

    return 0;
}
