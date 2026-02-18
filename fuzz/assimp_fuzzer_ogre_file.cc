/*
---------------------------------------------------------------------------
Open Asset Import Library (assimp)
---------------------------------------------------------------------------
Fuzzer for Ogre XML mesh format via file I/O.
The Ogre importer looks for external .material and .skeleton files alongside
the .mesh.xml file. ReadFileFromMemory can't provide these companion files.
This fuzzer writes the main mesh XML data to a temp file and provides
a companion .material file to exercise the OgreMaterial parser.
---------------------------------------------------------------------------
*/
#include "fuzzer_common.h"
#include <assimp/scene.h>
#include <cstdio>
#include <cstring>
#include <unistd.h>
#include <sys/stat.h>

using namespace Assimp;

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t dataSize) {
    if (!AssimpFuzz::IsValidSize(dataSize, "mesh.xml")) {
        return 0;
    }

    int pid = static_cast<int>(getpid());
    char mesh_path[128], mat_path[128], skel_path[128], dir_path[128];
    snprintf(dir_path, sizeof(dir_path), "/tmp/assimp_fuzz_ogre_%d", pid);
    snprintf(mesh_path, sizeof(mesh_path), "%s/model.mesh.xml", dir_path);
    snprintf(mat_path, sizeof(mat_path), "%s/model.material", dir_path);
    snprintf(skel_path, sizeof(skel_path), "%s/model.skeleton.xml", dir_path);

    mkdir(dir_path, 0755);

    // Write mesh XML data
    FILE *fp = fopen(mesh_path, "wb");
    if (!fp) return 0;
    fwrite(data, 1, dataSize, fp);
    fclose(fp);

    // Write a .material file to exercise OgreMaterial parser
    static const char mat_content[] =
        "material BaseWhite\n"
        "{\n"
        "    technique\n"
        "    {\n"
        "        pass\n"
        "        {\n"
        "            ambient 1.0 1.0 1.0 1.0\n"
        "            diffuse 1.0 1.0 1.0 1.0\n"
        "            specular 0.5 0.5 0.5 1.0 12.5\n"
        "            emissive 0.0 0.0 0.0 1.0\n"
        "            scene_blend alpha_blend\n"
        "            depth_write off\n"
        "            depth_check on\n"
        "            lighting on\n"
        "            cull_hardware none\n"
        "            cull_software none\n"
        "\n"
        "            texture_unit\n"
        "            {\n"
        "                texture diffuse.tga\n"
        "                tex_address_mode wrap\n"
        "                filtering trilinear\n"
        "                colour_op modulate\n"
        "            }\n"
        "            texture_unit\n"
        "            {\n"
        "                texture normal.tga\n"
        "                tex_address_mode clamp\n"
        "                filtering bilinear\n"
        "                colour_op_ex add src_texture src_current\n"
        "            }\n"
        "        }\n"
        "        pass\n"
        "        {\n"
        "            ambient 0.5 0.0 0.0\n"
        "            diffuse 1.0 0.0 0.0\n"
        "            scene_blend add\n"
        "            depth_write off\n"
        "        }\n"
        "    }\n"
        "    technique LOD1\n"
        "    {\n"
        "        pass\n"
        "        {\n"
        "            ambient 0.8 0.8 0.8\n"
        "            diffuse 0.8 0.8 0.8\n"
        "            texture_unit\n"
        "            {\n"
        "                texture lod1.tga\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "}\n"
        "\n"
        "material TransparentGlass\n"
        "{\n"
        "    technique\n"
        "    {\n"
        "        pass\n"
        "        {\n"
        "            ambient 0.1 0.1 0.1\n"
        "            diffuse 0.5 0.5 0.8 0.5\n"
        "            specular 1.0 1.0 1.0 1.0 50.0\n"
        "            scene_blend alpha_blend\n"
        "            depth_write off\n"
        "            cull_hardware none\n"
        "\n"
        "            texture_unit\n"
        "            {\n"
        "                texture glass.tga\n"
        "                tex_address_mode mirror\n"
        "                filtering anisotropic\n"
        "                max_anisotropy 8\n"
        "                colour_op replace\n"
        "                scroll_anim 0.1 0.0\n"
        "                rotate_anim 0.05\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "}\n";

    fp = fopen(mat_path, "w");
    if (fp) {
        fwrite(mat_content, 1, sizeof(mat_content) - 1, fp);
        fclose(fp);
    }

    // Write a skeleton XML to exercise skeleton loading
    static const char skel_content[] =
        "<?xml version=\"1.0\"?>\n"
        "<skeleton>\n"
        "    <bones>\n"
        "        <bone id=\"0\" name=\"Root\">\n"
        "            <position x=\"0\" y=\"0\" z=\"0\"/>\n"
        "            <rotation angle=\"0\"><axis x=\"0\" y=\"1\" z=\"0\"/></rotation>\n"
        "        </bone>\n"
        "        <bone id=\"1\" name=\"Spine\">\n"
        "            <position x=\"0\" y=\"1\" z=\"0\"/>\n"
        "            <rotation angle=\"0\"><axis x=\"0\" y=\"1\" z=\"0\"/></rotation>\n"
        "        </bone>\n"
        "    </bones>\n"
        "    <bonehierarchy>\n"
        "        <boneparent bone=\"Spine\" parent=\"Root\"/>\n"
        "    </bonehierarchy>\n"
        "    <animations>\n"
        "        <animation name=\"walk\" length=\"1.0\">\n"
        "            <tracks>\n"
        "                <track bone=\"Root\">\n"
        "                    <keyframes>\n"
        "                        <keyframe time=\"0\">\n"
        "                            <translate x=\"0\" y=\"0\" z=\"0\"/>\n"
        "                            <rotate angle=\"0\"><axis x=\"0\" y=\"1\" z=\"0\"/></rotate>\n"
        "                        </keyframe>\n"
        "                        <keyframe time=\"1.0\">\n"
        "                            <translate x=\"0\" y=\"0\" z=\"1\"/>\n"
        "                            <rotate angle=\"0.5\"><axis x=\"1\" y=\"0\" z=\"0\"/></rotate>\n"
        "                        </keyframe>\n"
        "                    </keyframes>\n"
        "                </track>\n"
        "            </tracks>\n"
        "        </animation>\n"
        "    </animations>\n"
        "</skeleton>\n";

    fp = fopen(skel_path, "w");
    if (fp) {
        fwrite(skel_content, 1, sizeof(skel_content) - 1, fp);
        fclose(fp);
    }

    Importer importer;
    if (!AssimpFuzz::ForceFormat(importer, "mesh.xml")) {
        unlink(mesh_path); unlink(mat_path); unlink(skel_path);
        rmdir(dir_path);
        return 0;
    }

    AssimpFuzz::ApplyImporterConfigs(importer, data, dataSize);
    unsigned int flags = AssimpFuzz::GetProcessingFlags(data, dataSize);
    importer.ReadFile(mesh_path, flags);

    unlink(mesh_path);
    unlink(mat_path);
    unlink(skel_path);
    rmdir(dir_path);
    return 0;
}
