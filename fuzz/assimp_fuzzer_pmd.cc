/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for MMD PMD parser (MMDPmdParser.h).
The PMD parser is compiled into assimp but not reached via the normal
import path (which only handles PMX). This fuzzer exercises the PMD
Read() methods directly to get coverage.

Note: PmdHeader, PmdVertex, PmdMaterial::Read() take std::ifstream*
(not std::istream*), so we read their bytes manually and exercise
the remaining struct Read methods which accept std::istream*.
---------------------------------------------------------------------------
*/
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <sstream>
#include <string>
#include <memory>

// PMD parser header - it's a header-only parser
#include "code/AssetLib/MMD/MMDPmdParser.h"

// Cap array sizes to prevent OOM from large fuzz counts
static constexpr uint32_t kMaxCount = 256;

static uint32_t ReadU32Capped(std::istream *s) {
    uint32_t v = 0;
    s->read(reinterpret_cast<char *>(&v), sizeof(v));
    return (v > kMaxCount) ? kMaxCount : v;
}

static uint16_t ReadU16Capped(std::istream *s) {
    uint16_t v = 0;
    s->read(reinterpret_cast<char *>(&v), sizeof(v));
    return (v > kMaxCount) ? static_cast<uint16_t>(kMaxCount) : v;
}

static uint8_t ReadU8Capped(std::istream *s) {
    uint8_t v = 0;
    s->read(reinterpret_cast<char *>(&v), sizeof(v));
    return (v > kMaxCount) ? static_cast<uint8_t>(kMaxCount) : v;
}

// Read PmdHeader fields manually (its Read method takes ifstream*)
static void ReadPmdHeaderManual(std::istream &s) {
    char buffer[256] = {};
    s.read(buffer, 20);   // name (20 bytes)
    s.read(buffer, 256);  // comment (256 bytes)
}

// Read PmdVertex fields manually (its Read method takes ifstream*)
static void ReadPmdVertexManual(std::istream &s) {
    float position[3], normal[3], uv[2];
    uint16_t bone_index[2];
    uint8_t bone_weight, edge_invisible;
    s.read(reinterpret_cast<char *>(position), sizeof(float) * 3);
    s.read(reinterpret_cast<char *>(normal), sizeof(float) * 3);
    s.read(reinterpret_cast<char *>(uv), sizeof(float) * 2);
    s.read(reinterpret_cast<char *>(bone_index), sizeof(uint16_t) * 2);
    s.read(reinterpret_cast<char *>(&bone_weight), sizeof(uint8_t));
    s.read(reinterpret_cast<char *>(&edge_invisible), sizeof(uint8_t));
}

// Read PmdMaterial fields manually (its Read method takes ifstream*)
static void ReadPmdMaterialManual(std::istream &s) {
    float diffuse[4], power, specular[3], ambient[3];
    uint8_t toon_index, edge_flag;
    uint32_t index_count;
    char buffer[20] = {};
    s.read(reinterpret_cast<char *>(diffuse), sizeof(float) * 4);
    s.read(reinterpret_cast<char *>(&power), sizeof(float));
    s.read(reinterpret_cast<char *>(specular), sizeof(float) * 3);
    s.read(reinterpret_cast<char *>(ambient), sizeof(float) * 3);
    s.read(reinterpret_cast<char *>(&toon_index), sizeof(uint8_t));
    s.read(reinterpret_cast<char *>(&edge_flag), sizeof(uint8_t));
    s.read(reinterpret_cast<char *>(&index_count), sizeof(uint32_t));
    s.read(buffer, 20);
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (dataSize < 16 || dataSize > 4 * 1024 * 1024) {
        return 0;
    }

    std::string str(reinterpret_cast<const char *>(data), dataSize);
    std::istringstream iss(str);

    // Replicate PmdModel::LoadFromStream logic using std::istream
    // Skip magic check (Pmd) - just read past 3 bytes
    char magic[3];
    iss.read(magic, 3);

    // version
    float version = 0.0f;
    iss.read(reinterpret_cast<char *>(&version), sizeof(float));

    // header (PmdHeader::Read takes ifstream*, so read manually)
    ReadPmdHeaderManual(iss);

    if (!iss.good()) return 0;

    // vertices (PmdVertex::Read takes ifstream*, so read manually)
    uint32_t vertex_num = ReadU32Capped(&iss);
    for (uint32_t i = 0; i < vertex_num && iss.good(); i++) {
        ReadPmdVertexManual(iss);
    }

    if (!iss.good()) return 0;

    // indices
    uint32_t index_num = ReadU32Capped(&iss);
    std::vector<uint16_t> indices(index_num);
    for (uint32_t i = 0; i < index_num && iss.good(); i++) {
        iss.read(reinterpret_cast<char *>(&indices[i]), sizeof(uint16_t));
    }

    // materials (PmdMaterial::Read takes ifstream*, so read manually)
    uint32_t material_num = ReadU32Capped(&iss);
    for (uint32_t i = 0; i < material_num && iss.good(); i++) {
        ReadPmdMaterialManual(iss);
    }

    // bones - PmdBone::Read takes istream*, so call it directly
    uint16_t bone_num = ReadU16Capped(&iss);
    std::vector<pmd::PmdBone> bones(bone_num);
    for (uint32_t i = 0; i < bone_num && iss.good(); i++) {
        bones[i].Read(&iss);
    }

    // iks
    uint16_t ik_num = ReadU16Capped(&iss);
    std::vector<pmd::PmdIk> iks(ik_num);
    for (uint32_t i = 0; i < ik_num && iss.good(); i++) {
        iks[i].Read(&iss);
    }

    // faces
    uint16_t face_num = ReadU16Capped(&iss);
    std::vector<pmd::PmdFace> faces(face_num);
    for (uint32_t i = 0; i < face_num && iss.good(); i++) {
        faces[i].Read(&iss);
    }

    // face frames
    uint8_t face_frame_num = ReadU8Capped(&iss);
    std::vector<uint16_t> faces_indices(face_frame_num);
    for (uint32_t i = 0; i < face_frame_num && iss.good(); i++) {
        iss.read(reinterpret_cast<char *>(&faces_indices[i]), sizeof(uint16_t));
    }

    // bone display names
    uint8_t bone_disp_num = ReadU8Capped(&iss);
    std::vector<pmd::PmdBoneDispName> bone_disp_name(bone_disp_num);
    for (uint32_t i = 0; i < bone_disp_num && iss.good(); i++) {
        bone_disp_name[i].Read(&iss);
    }

    // bone display
    uint32_t bone_frame_num = ReadU32Capped(&iss);
    std::vector<pmd::PmdBoneDisp> bone_disp(bone_frame_num);
    for (uint32_t i = 0; i < bone_frame_num && iss.good(); i++) {
        bone_disp[i].Read(&iss);
    }

    // english extension - skip PmdHeader::ReadExtension (ifstream*)
    // but exercise bone/face/boneDispName ReadExpantion (istream*)
    bool english = false;
    iss.read(reinterpret_cast<char *>(&english), sizeof(char));
    if (english && iss.good()) {
        // Skip header extension (20 + 256 bytes)
        char skip_buf[256];
        iss.read(skip_buf, 20);
        iss.read(skip_buf, 256);

        for (uint32_t i = 0; i < bone_num && iss.good(); i++) {
            bones[i].ReadExpantion(&iss);
        }
        for (uint32_t i = 0; i < face_num && iss.good(); i++) {
            faces[i].ReadExpantion(&iss);
        }
        for (uint32_t i = 0; i < bone_disp_name.size() && iss.good(); i++) {
            bone_disp_name[i].ReadExpantion(&iss);
        }
    }

    // toon textures
    if (iss.good() && iss.peek() != std::istringstream::traits_type::eof()) {
        char buffer[100];
        for (uint32_t i = 0; i < 10 && iss.good(); i++) {
            iss.read(buffer, 100);
        }
    }

    // rigid bodies
    if (iss.good() && iss.peek() != std::istringstream::traits_type::eof()) {
        uint32_t rigid_body_num = ReadU32Capped(&iss);
        std::vector<pmd::PmdRigidBody> rigid_bodies(rigid_body_num);
        for (uint32_t i = 0; i < rigid_body_num && iss.good(); i++) {
            rigid_bodies[i].Read(&iss);
        }

        // constraints
        uint32_t constraint_num = ReadU32Capped(&iss);
        std::vector<pmd::PmdConstraint> constraints(constraint_num);
        for (uint32_t i = 0; i < constraint_num && iss.good(); i++) {
            constraints[i].Read(&iss);
        }
    }

    return 0;
}
