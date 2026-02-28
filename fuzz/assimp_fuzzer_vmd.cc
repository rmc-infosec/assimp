/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for MMD VMD parser (MMDVmdParser.h).
The VMD parser is compiled into assimp but not reached via the normal
import path (which only handles PMX). This fuzzer exercises the VMD
Read() methods directly to get coverage.
---------------------------------------------------------------------------
*/
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <sstream>
#include <string>
#include <memory>

// VMD parser header - it's a header-only parser
#include "code/AssetLib/MMD/MMDVmdParser.h"

static constexpr int kMaxCount = 256;

static int ReadIntCapped(std::istream *s) {
    int v = 0;
    s->read(reinterpret_cast<char *>(&v), sizeof(v));
    if (v < 0) v = 0;
    return (v > kMaxCount) ? kMaxCount : v;
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (dataSize < 64 || dataSize > 4 * 1024 * 1024) {
        return 0;
    }

    std::string str(reinterpret_cast<const char *>(data), dataSize);
    std::istringstream iss(str);

    // Replicate VmdMotion::LoadFromStream logic using std::istream

    // magic + version (30 bytes)
    char buffer[30];
    iss.read(buffer, 30);

    // model name (20 bytes)
    char name_buf[20];
    iss.read(name_buf, 20);

    if (!iss.good()) return 0;

    // bone frames
    int bone_frame_num = ReadIntCapped(&iss);
    std::vector<vmd::VmdBoneFrame> bone_frames(bone_frame_num);
    for (int i = 0; i < bone_frame_num && iss.good(); i++) {
        bone_frames[i].Read(&iss);
    }

    if (!iss.good()) return 0;

    // face frames
    int face_frame_num = ReadIntCapped(&iss);
    std::vector<vmd::VmdFaceFrame> face_frames(face_frame_num);
    for (int i = 0; i < face_frame_num && iss.good(); i++) {
        face_frames[i].Read(&iss);
    }

    // camera frames
    int camera_frame_num = ReadIntCapped(&iss);
    std::vector<vmd::VmdCameraFrame> camera_frames(camera_frame_num);
    for (int i = 0; i < camera_frame_num && iss.good(); i++) {
        camera_frames[i].Read(&iss);
    }

    // light frames
    int light_frame_num = ReadIntCapped(&iss);
    std::vector<vmd::VmdLightFrame> light_frames(light_frame_num);
    for (int i = 0; i < light_frame_num && iss.good(); i++) {
        light_frames[i].Read(&iss);
    }

    // unknown2 (4 bytes)
    iss.read(buffer, 4);

    // ik frames
    if (iss.good() && iss.peek() != std::istringstream::traits_type::eof()) {
        int ik_num = ReadIntCapped(&iss);
        std::vector<vmd::VmdIkFrame> ik_frames(ik_num);
        for (int i = 0; i < ik_num && iss.good(); i++) {
            ik_frames[i].Read(&iss);
        }
    }

    return 0;
}
