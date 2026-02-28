#!/usr/bin/env python3
"""
Generate valid Half-Life 1 MDL format seed files for fuzzing.

Targets uncovered code paths in HL1MDLLoader.cpp by generating MDL files
with various feature combinations: bone controllers, hitboxes, attachments,
sequence transitions, and a full-featured model.

Reference structures from:
  - code/AssetLib/MDL/HalfLife/HalfLifeMDLBaseHeader.h
  - code/AssetLib/MDL/HalfLife/HL1FileData.h
  - code/AssetLib/MDL/HalfLife/HL1MDLLoader.cpp
"""

import struct
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test", "models", "MDL", "fuzz_seeds")

# HL1 MDL magic and version
MAGIC = b"IDST"
VERSION = 10

# ---- Structure sizes (from HL1FileData.h, packed) ----
# Header_HL1: HalfLifeMDLBaseHeader(8) + char[64] + int32 length + float[3] eye
#   + float[3] min + float[3] max + float[3] bbmin + float[3] bbmax
#   + int32 unused (flags) + pairs of (count, offset) for bones, bonecontrollers,
#   hitboxes, seq, seqgroups, textures, texturedataindex, numskinref, numskinfamilies,
#   skinindex, bodyparts, attachments, 4 unused, transitions
# Let's compute it field by field.

SIZEOF_BONE_HL1 = 32 + 4 + 4 + 6 * 4 + 6 * 4 + 6 * 4  # name[32] + parent + unused + bonecontroller[6] + value[6] + scale[6] = 112
SIZEOF_BONECONTROLLER_HL1 = 4 + 4 + 4 + 4 + 4 + 4  # bone, type, start, end, unused, index = 24
SIZEOF_HITBOX_HL1 = 4 + 4 + 3 * 4 + 3 * 4  # bone, group, bbmin[3], bbmax[3] = 32
SIZEOF_SEQDESC_HL1 = (32 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 +
                      3 * 4 + 4 + 4 + 3 * 4 + 3 * 4 + 4 + 4 + 2 * 4 + 2 * 4 +
                      2 * 4 + 4 + 4 + 4 + 4 + 4 + 4)  # = 176
SIZEOF_SEQGROUP_HL1 = 32 + 64 + 4 + 4  # label[32] + name[64] + unused + unused2 = 104
SIZEOF_ATTACHMENT_HL1 = 32 + 4 + 4 + 3 * 4 + 3 * 3 * 4  # unused[32] + unused2 + bone + org[3] + unused3[3][3] = 88
SIZEOF_TEXTURE_HL1 = 64 + 4 + 4 + 4 + 4  # name[64] + flags + width + height + index = 80
SIZEOF_BODYPART_HL1 = 64 + 4 + 4 + 4  # name[64] + nummodels + base + modelindex = 76
SIZEOF_MODEL_HL1 = (64 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 + 4 +
                    4 + 4)  # name[64] + unused + unused2 + nummesh + meshindex + numverts + vertinfoindex + vertindex + numnorms + norminfoindex + normindex + unused3 + unused4 = 112
SIZEOF_MESH_HL1 = 4 + 4 + 4 + 4 + 4  # numtris + triindex + skinref + numnorms + unused = 20
SIZEOF_ANIMVALUEOFFSET_HL1 = 6 * 2  # unsigned short offset[6] = 12
SIZEOF_ANIMEVENT_HL1 = 4 + 4 + 4 + 64  # frame + event + unused + options[64] = 76


def pad_string(s, length):
    """Pad a string to a fixed length with null bytes."""
    encoded = s.encode('ascii')[:length - 1]
    return encoded + b'\x00' * (length - len(encoded))


def float3(x, y, z):
    """Pack 3 floats (vec3_t)."""
    return struct.pack('<fff', x, y, z)


class HL1MDLBuilder:
    """Builder for Half-Life 1 MDL files."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.bones = []
        self.bone_controllers = []
        self.hitboxes = []
        self.sequences = []
        self.seq_groups = []
        self.textures = []
        self.bodyparts = []
        self.attachments = []
        self.num_transitions = 0
        self.transition_data = b''
        self.skin_refs = []
        self.num_skin_families = 0
        self.model_name = "test_model"

    def add_bone(self, name="bone", parent=-1, values=None, scales=None, controllers=None):
        """Add a bone."""
        if values is None:
            values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if scales is None:
            scales = [0.001, 0.001, 0.001, 0.001, 0.001, 0.001]
        if controllers is None:
            controllers = [-1, -1, -1, -1, -1, -1]
        self.bones.append({
            'name': name,
            'parent': parent,
            'controllers': controllers,
            'values': values,
            'scales': scales,
        })

    def add_bone_controller(self, bone=0, type_=0x08, start=0.0, end=1.0, index=0):
        """Add a bone controller. type: motion type flags."""
        self.bone_controllers.append({
            'bone': bone,
            'type': type_,
            'start': start,
            'end': end,
            'index': index,
        })

    def add_hitbox(self, bone=0, group=0, bbmin=None, bbmax=None):
        """Add a hitbox."""
        if bbmin is None:
            bbmin = [-1.0, -1.0, -1.0]
        if bbmax is None:
            bbmax = [1.0, 1.0, 1.0]
        self.hitboxes.append({
            'bone': bone,
            'group': group,
            'bbmin': bbmin,
            'bbmax': bbmax,
        })

    def add_attachment(self, bone=0, org=None):
        """Add an attachment."""
        if org is None:
            org = [0.0, 0.0, 0.0]
        self.attachments.append({
            'bone': bone,
            'org': org,
        })

    def set_transitions(self, num_transitions, data=None):
        """Set sequence transitions. data is a flat list of uint8 values [n*n]."""
        self.num_transitions = num_transitions
        if data is None:
            # Default: identity-like transition matrix
            data = []
            for i in range(num_transitions):
                for j in range(num_transitions):
                    data.append(0 if i != j else 255)
        self.transition_data = struct.pack('<%dB' % len(data), *data)

    def add_texture(self, name="texture.bmp", width=4, height=4, flags=0):
        """Add a texture (small 4x4 indexed image with 256-color palette)."""
        self.textures.append({
            'name': name,
            'width': width,
            'height': height,
            'flags': flags,
        })

    def add_sequence(self, label="idle", fps=30.0, numframes=1, numblends=1,
                     activity=0, actweight=0, numevents=0, events=None,
                     entrynode=0, exitnode=0, nodeflags=0, motiontype=0,
                     motionbone=0, blendtype=None, blendstart=None, blendend=None):
        """Add a sequence description."""
        if blendtype is None:
            blendtype = [0, 0]
        if blendstart is None:
            blendstart = [0.0, 0.0]
        if blendend is None:
            blendend = [0.0, 0.0]
        if events is None:
            events = []
        self.sequences.append({
            'label': label,
            'fps': fps,
            'numframes': numframes,
            'numblends': numblends,
            'activity': activity,
            'actweight': actweight,
            'numevents': numevents,
            'events': events,
            'entrynode': entrynode,
            'exitnode': exitnode,
            'nodeflags': nodeflags,
            'motiontype': motiontype,
            'motionbone': motionbone,
            'blendtype': blendtype,
            'blendstart': blendstart,
            'blendend': blendend,
        })

    def add_seq_group(self, label="default", name=""):
        """Add a sequence group."""
        self.seq_groups.append({
            'label': label,
            'name': name,
        })

    def add_bodypart(self, name="body", num_models=1, models=None):
        """Add a bodypart with models. Each model has vertices, normals, meshes."""
        if models is None:
            models = [self._default_model()]
        self.bodyparts.append({
            'name': name,
            'nummodels': num_models,
            'models': models[:num_models],
        })

    def _default_model(self):
        """Create a default model with a single triangle mesh."""
        return {
            'name': 'model',
            'nummesh': 1,
            'numverts': 3,
            'numnorms': 3,
            'verts': [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
            ],
            'norms': [
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0],
            ],
            'vertbones': [0, 0, 0],
            'normbones': [0, 0, 0],
            'meshes': [{
                'numtris': 1,
                'skinref': 0,
                # Triangle strip: 3 vertices forming one triangle
                'tricmds': [3, 0, 0, 0, 0, 1, 1, 10, 0, 2, 2, 0, 10, 0],
            }],
        }

    def build(self):
        """Build the MDL file and return bytes."""
        # We'll build the file in sections, computing offsets as we go.
        # The header is 244 bytes (measured from the struct fields).
        HEADER_SIZE = 244

        # Phase 1: Compute all section sizes and offsets.
        offset = HEADER_SIZE

        # Bones
        bone_offset = offset
        bone_size = len(self.bones) * SIZEOF_BONE_HL1
        offset += bone_size

        # Bone controllers
        bonecontroller_offset = offset
        bonecontroller_size = len(self.bone_controllers) * SIZEOF_BONECONTROLLER_HL1
        offset += bonecontroller_size

        # Hitboxes
        hitbox_offset = offset
        hitbox_size = len(self.hitboxes) * SIZEOF_HITBOX_HL1
        offset += hitbox_size

        # Sequence groups
        seqgroup_offset = offset
        seqgroup_size = len(self.seq_groups) * SIZEOF_SEQGROUP_HL1
        offset += seqgroup_size

        # Animation data (AnimValueOffset per bone per blend per sequence + AnimValues)
        # We place animation data right after sequence groups.
        anim_data_base = offset
        anim_data = bytearray()

        # For each sequence, we need numblends * numbones AnimValueOffset_HL1 structs.
        # For simplicity, we create static animations (all zeros), so offsets are all 0.
        seq_anim_offsets = []
        for seq in self.sequences:
            seq_anim_offset = anim_data_base + len(anim_data)
            seq_anim_offsets.append(seq_anim_offset)
            num_anim_entries = seq['numblends'] * len(self.bones)
            # Each AnimValueOffset_HL1 has 6 unsigned shorts, all zero (no compressed data)
            anim_data += b'\x00' * (num_anim_entries * SIZEOF_ANIMVALUEOFFSET_HL1)

        offset += len(anim_data)

        # Sequence event data
        seq_event_offsets = []
        events_data = bytearray()
        for seq in self.sequences:
            if seq['numevents'] > 0 and seq['events']:
                seq_event_offsets.append(offset + len(events_data))
                for ev in seq['events']:
                    events_data += struct.pack('<iii', ev.get('frame', 0), ev.get('event', 0), 0)
                    events_data += pad_string(ev.get('options', ''), 64)
            else:
                seq_event_offsets.append(0)
        offset += len(events_data)

        # Sequence descriptions
        seq_offset = offset
        seq_size = len(self.sequences) * SIZEOF_SEQDESC_HL1
        offset += seq_size

        # Textures
        texture_offset = offset
        texture_size = len(self.textures) * SIZEOF_TEXTURE_HL1
        offset += texture_size

        # Texture data (indexed pixels + palette per texture)
        texture_data_offset = offset
        texture_pixel_data = bytearray()
        texture_data_offsets = []
        for tex in self.textures:
            texture_data_offsets.append(offset + len(texture_pixel_data))
            num_pixels = tex['width'] * tex['height']
            # Pixel indices (all 0)
            texture_pixel_data += b'\x00' * num_pixels
            # 256-color palette (768 bytes: 256 * 3)
            palette = bytearray()
            for c in range(256):
                palette += struct.pack('BBB', c, c, c)
            texture_pixel_data += palette
        offset += len(texture_pixel_data)

        # Skin references
        skin_offset = offset
        num_skin_ref = max(len(self.textures), 1)
        num_skin_families = max(self.num_skin_families, 1)
        skin_data = bytearray()
        for fam in range(num_skin_families):
            for ref in range(num_skin_ref):
                skin_data += struct.pack('<h', ref if ref < len(self.textures) else 0)
        offset += len(skin_data)

        # Bodyparts (and their models, meshes, vertices, normals, etc.)
        bodypart_offset = offset
        bodypart_size = len(self.bodyparts) * SIZEOF_BODYPART_HL1
        offset += bodypart_size

        # Build bodypart sub-data (models, meshes, verts, norms, tricmds)
        bodypart_sub_data = bytearray()
        bodypart_model_offsets = []
        for bp in self.bodyparts:
            model_list_offset = offset + len(bodypart_sub_data)
            model_offsets_for_bp = []
            for model in bp['models']:
                model_offset_in_file = offset + len(bodypart_sub_data)
                model_offsets_for_bp.append(model_offset_in_file)

                # We need to know the offsets for verts, norms, mesh, vertinfo, norminfo
                # They come after all models in this bodypart. We'll do two passes.
                # For now, reserve space for the Model_HL1 struct and fill it later.
                bodypart_sub_data += b'\x00' * SIZEOF_MODEL_HL1

            bodypart_model_offsets.append((model_list_offset, model_offsets_for_bp))

        # Now place vertex data, normal data, bone indices, mesh data, and tricmds
        # for each model.
        model_patch_info = []  # (model_sub_data_offset, meshindex, vertinfoindex, vertindex, norminfoindex, normindex, nummesh, numverts, numnorms)
        for bp_idx, bp in enumerate(self.bodyparts):
            for m_idx, model in enumerate(bp['models']):
                numverts = model['numverts']
                numnorms = model['numnorms']

                # Vertex bone indices (uint8 per vertex)
                vertinfo_offset_in_file = offset + len(bodypart_sub_data)
                for vb in model.get('vertbones', [0] * numverts):
                    bodypart_sub_data += struct.pack('B', vb)

                # Normal bone indices (uint8 per normal)
                norminfo_offset_in_file = offset + len(bodypart_sub_data)
                for nb in model.get('normbones', [0] * numnorms):
                    bodypart_sub_data += struct.pack('B', nb)

                # Vertex positions (vec3_t per vertex)
                vert_offset_in_file = offset + len(bodypart_sub_data)
                for v in model.get('verts', [[0.0, 0.0, 0.0]] * numverts):
                    bodypart_sub_data += struct.pack('<fff', *v)

                # Normal vectors (vec3_t per normal)
                norm_offset_in_file = offset + len(bodypart_sub_data)
                for n in model.get('norms', [[0.0, 0.0, 1.0]] * numnorms):
                    bodypart_sub_data += struct.pack('<fff', *n)

                # Mesh structs
                mesh_offset_in_file = offset + len(bodypart_sub_data)
                mesh_structs_data = bytearray()
                mesh_tricmd_offsets = []
                for mesh in model['meshes']:
                    # Reserve space, will patch triindex later
                    mesh_structs_data += b'\x00' * SIZEOF_MESH_HL1
                    mesh_tricmd_offsets.append(None)

                bodypart_sub_data += mesh_structs_data

                # Tricmds for each mesh
                for mesh_idx, mesh in enumerate(model['meshes']):
                    tricmd_offset = offset + len(bodypart_sub_data)
                    mesh_tricmd_offsets[mesh_idx] = tricmd_offset
                    tricmds = mesh.get('tricmds', [])
                    for cmd in tricmds:
                        bodypart_sub_data += struct.pack('<h', cmd)
                    # Terminator (0)
                    bodypart_sub_data += struct.pack('<h', 0)

                # Patch mesh structs
                for mesh_idx, mesh in enumerate(model['meshes']):
                    mesh_struct_offset = mesh_offset_in_file - offset
                    mesh_struct_offset += mesh_idx * SIZEOF_MESH_HL1
                    mesh_bytes = struct.pack('<iiiii',
                                            mesh['numtris'],
                                            mesh_tricmd_offsets[mesh_idx],
                                            mesh.get('skinref', 0),
                                            mesh.get('numnorms', numnorms),
                                            0)  # unused
                    bodypart_sub_data[mesh_struct_offset:mesh_struct_offset + SIZEOF_MESH_HL1] = mesh_bytes

                model_patch_info.append({
                    'bp_idx': bp_idx,
                    'm_idx': m_idx,
                    'meshindex': mesh_offset_in_file,
                    'vertinfoindex': vertinfo_offset_in_file,
                    'vertindex': vert_offset_in_file,
                    'norminfoindex': norminfo_offset_in_file,
                    'normindex': norm_offset_in_file,
                    'nummesh': len(model['meshes']),
                    'numverts': numverts,
                    'numnorms': numnorms,
                    'name': model.get('name', 'model'),
                })

        offset += len(bodypart_sub_data)

        # Attachments
        attachment_offset = offset
        attachment_size = len(self.attachments) * SIZEOF_ATTACHMENT_HL1
        offset += attachment_size

        # Transitions
        transition_offset = offset
        offset += len(self.transition_data)

        total_size = offset

        # Phase 2: Build the actual binary data.
        data = bytearray()

        # ---- HEADER (244 bytes) ----
        # HalfLifeMDLBaseHeader: ident[4] + version(int32)
        data += MAGIC
        data += struct.pack('<i', VERSION)
        # char name[64]
        data += pad_string(self.model_name, 64)
        # int32 length
        data += struct.pack('<i', total_size)
        # float eyeposition[3]
        data += float3(0.0, 0.0, 0.0)
        # float min[3], max[3]
        data += float3(-16.0, -16.0, -16.0)
        data += float3(16.0, 16.0, 16.0)
        # float bbmin[3], bbmax[3]
        data += float3(-16.0, -16.0, -16.0)
        data += float3(16.0, 16.0, 16.0)
        # int32 unused (flags)
        data += struct.pack('<i', 0)
        # int32 numbones, boneindex
        data += struct.pack('<ii', len(self.bones), bone_offset)
        # int32 numbonecontrollers, bonecontrollerindex
        data += struct.pack('<ii', len(self.bone_controllers), bonecontroller_offset)
        # int32 numhitboxes, hitboxindex
        data += struct.pack('<ii', len(self.hitboxes), hitbox_offset)
        # int32 numseq, seqindex
        data += struct.pack('<ii', len(self.sequences), seq_offset)
        # int32 numseqgroups, seqgroupindex
        data += struct.pack('<ii', len(self.seq_groups), seqgroup_offset)
        # int32 numtextures, textureindex, texturedataindex
        data += struct.pack('<iii', len(self.textures), texture_offset, texture_data_offset)
        # int32 numskinref, numskinfamilies, skinindex
        data += struct.pack('<iii', num_skin_ref, num_skin_families, skin_offset)
        # int32 numbodyparts, bodypartindex
        data += struct.pack('<ii', len(self.bodyparts), bodypart_offset)
        # int32 numattachments, attachmentindex
        data += struct.pack('<ii', len(self.attachments), attachment_offset)
        # 4x int32 unused (soundtable, soundindex, soundgroups, soundgroupindex)
        data += struct.pack('<iiii', 0, 0, 0, 0)
        # int32 numtransitions, transitionindex
        data += struct.pack('<ii', self.num_transitions, transition_offset)

        assert len(data) == HEADER_SIZE, f"Header size mismatch: {len(data)} != {HEADER_SIZE}"

        # ---- BONES ----
        for bone in self.bones:
            data += pad_string(bone['name'], 32)
            data += struct.pack('<i', bone['parent'])
            data += struct.pack('<i', 0)  # unused
            for c in bone['controllers']:
                data += struct.pack('<i', c)
            for v in bone['values']:
                data += struct.pack('<f', v)
            for s in bone['scales']:
                data += struct.pack('<f', s)

        # ---- BONE CONTROLLERS ----
        for bc in self.bone_controllers:
            data += struct.pack('<ii', bc['bone'], bc['type'])
            data += struct.pack('<ff', bc['start'], bc['end'])
            data += struct.pack('<i', 0)  # unused (rest)
            data += struct.pack('<i', bc['index'])

        # ---- HITBOXES ----
        for hb in self.hitboxes:
            data += struct.pack('<ii', hb['bone'], hb['group'])
            data += struct.pack('<fff', *hb['bbmin'])
            data += struct.pack('<fff', *hb['bbmax'])

        # ---- SEQUENCE GROUPS ----
        for sg in self.seq_groups:
            data += pad_string(sg['label'], 32)
            data += pad_string(sg['name'], 64)
            data += struct.pack('<i', 0)  # unused
            data += struct.pack('<i', 0)  # unused2 (data offset for seqgroup 0)

        # ---- ANIMATION DATA ----
        data += bytes(anim_data)

        # ---- EVENT DATA ----
        data += bytes(events_data)

        # ---- SEQUENCE DESCRIPTIONS ----
        for seq_idx, seq in enumerate(self.sequences):
            data += pad_string(seq['label'], 32)
            data += struct.pack('<f', seq['fps'])
            data += struct.pack('<i', 0)  # flags
            data += struct.pack('<i', seq['activity'])
            data += struct.pack('<i', seq['actweight'])
            data += struct.pack('<i', seq['numevents'])
            data += struct.pack('<i', seq_event_offsets[seq_idx])  # eventindex
            data += struct.pack('<i', seq['numframes'])
            data += struct.pack('<i', 0)  # unused (numpivots)
            data += struct.pack('<i', 0)  # unused2 (pivotindex)
            data += struct.pack('<i', seq['motiontype'])
            data += struct.pack('<i', seq['motionbone'])
            data += float3(0.0, 0.0, 0.0)  # linearmovement
            data += struct.pack('<i', 0)  # unused3 (automoveposindex)
            data += struct.pack('<i', 0)  # unused4 (automoveangleindex)
            data += float3(-16.0, -16.0, -16.0)  # bbmin
            data += float3(16.0, 16.0, 16.0)  # bbmax
            data += struct.pack('<i', seq['numblends'])
            # animindex: relative to seqgroup data offset for group 0.
            # For seqgroup 0, the code does:
            #   panim = (header + pseqgroup->unused2 + pseqdesc->animindex)
            # So animindex should be seq_anim_offsets[seq_idx] - seqgroup_unused2_value
            # seqgroup[0].unused2 is 0, so animindex = seq_anim_offsets[seq_idx]
            data += struct.pack('<i', seq_anim_offsets[seq_idx])
            data += struct.pack('<ii', *seq['blendtype'])
            data += struct.pack('<ff', *seq['blendstart'])
            data += struct.pack('<ff', *seq['blendend'])
            data += struct.pack('<i', 0)  # unused5 (blendparent)
            data += struct.pack('<i', 0)  # seqgroup (always 0 for single file)
            data += struct.pack('<i', seq['entrynode'])
            data += struct.pack('<i', seq['exitnode'])
            data += struct.pack('<i', seq['nodeflags'])
            data += struct.pack('<i', 0)  # unused6 (nextseq)

        # ---- TEXTURES ----
        for tex_idx, tex in enumerate(self.textures):
            data += pad_string(tex['name'], 64)
            data += struct.pack('<i', tex['flags'])
            data += struct.pack('<i', tex['width'])
            data += struct.pack('<i', tex['height'])
            data += struct.pack('<i', texture_data_offsets[tex_idx])

        # ---- TEXTURE DATA ----
        data += bytes(texture_pixel_data)

        # ---- SKIN DATA ----
        data += bytes(skin_data)

        # ---- BODYPARTS ----
        for bp_idx, bp in enumerate(self.bodyparts):
            model_list_off, _ = bodypart_model_offsets[bp_idx]
            data += pad_string(bp['name'], 64)
            data += struct.pack('<i', bp['nummodels'])
            data += struct.pack('<i', 1)  # base
            data += struct.pack('<i', model_list_off)

        # ---- BODYPART SUB-DATA (Models, vertices, normals, meshes, tricmds) ----
        # First, patch model structs in bodypart_sub_data
        patch_idx = 0
        for bp_idx, bp in enumerate(self.bodyparts):
            _, model_offs = bodypart_model_offsets[bp_idx]
            for m_idx in range(len(bp['models'])):
                info = model_patch_info[patch_idx]
                patch_idx += 1
                model_file_offset = model_offs[m_idx]
                # Model_HL1 struct at bodypart_sub_data[model_file_offset - offset_of_sub_data_start]
                sub_off = model_file_offset - (bodypart_offset + bodypart_size)
                model_bytes = bytearray()
                model_bytes += pad_string(info['name'], 64)
                model_bytes += struct.pack('<i', 0)  # unused (type)
                model_bytes += struct.pack('<f', 0.0)  # unused2 (boundingradius)
                model_bytes += struct.pack('<i', info['nummesh'])
                model_bytes += struct.pack('<i', info['meshindex'])
                model_bytes += struct.pack('<i', info['numverts'])
                model_bytes += struct.pack('<i', info['vertinfoindex'])
                model_bytes += struct.pack('<i', info['vertindex'])
                model_bytes += struct.pack('<i', info['numnorms'])
                model_bytes += struct.pack('<i', info['norminfoindex'])
                model_bytes += struct.pack('<i', info['normindex'])
                model_bytes += struct.pack('<i', 0)  # unused3 (numgroups)
                model_bytes += struct.pack('<i', 0)  # unused4 (groupindex)
                bodypart_sub_data[sub_off:sub_off + SIZEOF_MODEL_HL1] = model_bytes

        data += bytes(bodypart_sub_data)

        # ---- ATTACHMENTS ----
        for att in self.attachments:
            data += b'\x00' * 32  # unused name
            data += struct.pack('<i', 0)  # unused type
            data += struct.pack('<i', att['bone'])
            data += struct.pack('<fff', *att['org'])
            data += b'\x00' * (3 * 3 * 4)  # unused vectors[3][3]

        # ---- TRANSITIONS ----
        data += self.transition_data

        assert len(data) == total_size, f"Size mismatch: {len(data)} != {total_size}"
        return bytes(data)


def generate_seed_bone_controllers():
    """seed_bone_controllers.mdl - MDL with bone controllers."""
    b = HL1MDLBuilder()
    b.model_name = "bone_ctrl_test"

    # Need at least 1 bone for bone controllers to reference
    b.add_bone("bone_root", parent=-1,
               values=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
               controllers=[0, -1, -1, -1, -1, -1])
    b.add_bone("bone_child", parent=0,
               values=[5.0, 0.0, 0.0, 0.0, 0.0, 0.0],
               controllers=[-1, 1, -1, -1, -1, -1])

    # 2 bone controllers
    b.add_bone_controller(bone=0, type_=0x08, start=-90.0, end=90.0, index=0)  # X rotation
    b.add_bone_controller(bone=1, type_=0x10, start=-45.0, end=45.0, index=1)  # Y rotation

    # Need a texture
    b.add_texture("ctrl_tex.bmp", width=4, height=4)

    # Need at least one sequence group and sequence
    b.add_seq_group("default")
    b.add_sequence("idle", fps=30.0, numframes=1)

    return b.build()


def generate_seed_hitboxes():
    """seed_hitboxes.mdl - MDL with hitboxes."""
    b = HL1MDLBuilder()
    b.model_name = "hitbox_test"

    b.add_bone("bone_root", parent=-1)
    b.add_bone("bone_torso", parent=0, values=[0.0, 0.0, 10.0, 0.0, 0.0, 0.0])
    b.add_bone("bone_head", parent=1, values=[0.0, 0.0, 15.0, 0.0, 0.0, 0.0])

    # 3 hitboxes with different groups
    b.add_hitbox(bone=0, group=0, bbmin=[-8, -4, -4], bbmax=[8, 4, 4])    # body
    b.add_hitbox(bone=1, group=1, bbmin=[-6, -3, -3], bbmax=[6, 3, 3])    # torso
    b.add_hitbox(bone=2, group=2, bbmin=[-3, -3, -3], bbmax=[3, 3, 3])    # head

    b.add_texture("hit_tex.bmp", width=4, height=4)
    b.add_seq_group("default")
    b.add_sequence("idle", fps=30.0, numframes=1)

    return b.build()


def generate_seed_attachments():
    """seed_attachments.mdl - MDL with attachments."""
    b = HL1MDLBuilder()
    b.model_name = "attach_test"

    b.add_bone("bone_root", parent=-1)
    b.add_bone("bone_hand", parent=0, values=[10.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    # 2 attachments
    b.add_attachment(bone=0, org=[0.0, 0.0, 5.0])   # muzzle flash
    b.add_attachment(bone=1, org=[12.0, 0.0, 0.0])   # hand

    b.add_texture("att_tex.bmp", width=4, height=4)
    b.add_seq_group("default")
    b.add_sequence("idle", fps=30.0, numframes=1)

    return b.build()


def generate_seed_transitions():
    """seed_transitions.mdl - MDL with sequence transitions."""
    b = HL1MDLBuilder()
    b.model_name = "transition_test"

    b.add_bone("bone_root", parent=-1)

    # 4 transitions (4x4 matrix)
    transition_data = [
        0, 1, 2, 3,
        1, 0, 1, 2,
        2, 1, 0, 1,
        3, 2, 1, 0,
    ]
    b.set_transitions(4, transition_data)

    b.add_texture("trans_tex.bmp", width=4, height=4)
    b.add_seq_group("default")

    # Add sequences that reference transition nodes
    b.add_sequence("walk", fps=30.0, numframes=10, entrynode=1, exitnode=2, nodeflags=0)
    b.add_sequence("run", fps=30.0, numframes=8, entrynode=2, exitnode=3, nodeflags=0)
    b.add_sequence("jump", fps=24.0, numframes=5, entrynode=3, exitnode=1, nodeflags=1)

    return b.build()


def generate_seed_full():
    """seed_full_hl1.mdl - Complete MDL with ALL features."""
    b = HL1MDLBuilder()
    b.model_name = "full_hl1_model"

    # 2 bones
    b.add_bone("Bip01", parent=-1,
               values=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
               scales=[0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
               controllers=[0, -1, -1, -1, -1, -1])
    b.add_bone("Bip01_Head", parent=0,
               values=[0.0, 0.0, 36.0, 0.0, 0.0, 0.0],
               scales=[0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
               controllers=[-1, -1, -1, -1, -1, -1])

    # 1 bone controller (mouth)
    b.add_bone_controller(bone=0, type_=0x08, start=0.0, end=45.0, index=4)

    # 2 hitboxes
    b.add_hitbox(bone=0, group=1, bbmin=[-10, -5, 0], bbmax=[10, 5, 36])
    b.add_hitbox(bone=1, group=2, bbmin=[-4, -4, -4], bbmax=[4, 4, 4])

    # 1 texture
    b.add_texture("skin.bmp", width=8, height=8)

    # 1 sequence group
    b.add_seq_group("default")

    # 1 sequence with animation events and blending
    b.add_sequence(
        "idle",
        fps=30.0,
        numframes=2,
        numblends=1,
        activity=1,
        actweight=1,
        numevents=2,
        events=[
            {'frame': 0, 'event': 1000, 'options': 'weapons/idle.wav'},
            {'frame': 1, 'event': 5004, 'options': ''},
        ],
        entrynode=0,
        exitnode=0,
        motiontype=0,
        motionbone=0,
    )

    # 1 bodypart with 1 model that has a triangle
    b.add_bodypart("body", num_models=1, models=[{
        'name': 'studio',
        'nummesh': 1,
        'numverts': 3,
        'numnorms': 3,
        'verts': [
            [0.0, 0.0, 0.0],
            [5.0, 0.0, 0.0],
            [0.0, 5.0, 0.0],
        ],
        'norms': [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
        ],
        'vertbones': [0, 0, 1],
        'normbones': [0, 0, 1],
        'meshes': [{
            'numtris': 1,
            'skinref': 0,
            # Triangle strip with 3 vertices: count=3, then 3x (vertindex, normindex, s, t)
            'tricmds': [3, 0, 0, 0, 0, 1, 1, 40, 0, 2, 2, 0, 40, 0],
        }],
    }])

    # 1 attachment
    b.add_attachment(bone=1, org=[0.0, 0.0, 4.0])

    # Transitions (2x2)
    b.set_transitions(2, [0, 1, 1, 0])

    return b.build()


def generate_seed_anim_events():
    """seed_anim_events.mdl - MDL with animation events to cover read_sequence_infos event paths."""
    b = HL1MDLBuilder()
    b.model_name = "anim_events_test"

    b.add_bone("bone_root", parent=-1)

    b.add_texture("event_tex.bmp", width=4, height=4)
    b.add_seq_group("default")

    # Sequence with multiple events
    b.add_sequence(
        "attack",
        fps=30.0,
        numframes=5,
        numblends=1,
        numevents=3,
        events=[
            {'frame': 0, 'event': 5001, 'options': 'weapons/fire.wav'},
            {'frame': 2, 'event': 6001, 'options': 'muzzleflash'},
            {'frame': 4, 'event': 5004, 'options': ''},
        ],
    )

    # Another sequence with blend controllers (TwoWayBlending)
    b.add_sequence(
        "look",
        fps=15.0,
        numframes=3,
        numblends=2,  # TwoWayBlending
        blendtype=[0x08, 0],
        blendstart=[-90.0, 0.0],
        blendend=[90.0, 0.0],
    )

    return b.build()


def generate_seed_multi_bodypart():
    """seed_multi_bodypart.mdl - MDL with multiple bodyparts and models."""
    b = HL1MDLBuilder()
    b.model_name = "multi_bp_test"

    b.add_bone("bone_root", parent=-1)

    b.add_texture("bp_tex.bmp", width=4, height=4)
    b.add_seq_group("default")
    b.add_sequence("idle", fps=30.0, numframes=1)

    model_def = {
        'name': 'default_model',
        'nummesh': 1,
        'numverts': 3,
        'numnorms': 3,
        'verts': [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        'norms': [[0, 0, 1], [0, 0, 1], [0, 0, 1]],
        'vertbones': [0, 0, 0],
        'normbones': [0, 0, 0],
        'meshes': [{
            'numtris': 1,
            'skinref': 0,
            'tricmds': [3, 0, 0, 0, 0, 1, 1, 4, 0, 2, 2, 0, 4, 0],
        }],
    }

    b.add_bodypart("heads", num_models=2, models=[
        {**model_def, 'name': 'head_default'},
        {**model_def, 'name': 'head_bald'},
    ])
    b.add_bodypart("weapons", num_models=1, models=[
        {**model_def, 'name': 'gun'},
    ])

    return b.build()


def generate_seed_skin_families():
    """seed_skin_families.mdl - MDL with multiple skin families to cover read_skins."""
    b = HL1MDLBuilder()
    b.model_name = "skin_families_test"

    b.add_bone("bone_root", parent=-1)

    # Multiple textures for skin swapping
    b.add_texture("skin_red.bmp", width=4, height=4, flags=0)
    b.add_texture("skin_blue.bmp", width=4, height=4, flags=0)
    b.add_texture("skin_chrome.bmp", width=4, height=4, flags=0x0002)  # CHROME

    b.num_skin_families = 2  # default + 1 replacement

    b.add_seq_group("default")
    b.add_sequence("idle", fps=30.0, numframes=1)

    b.add_bodypart("body", num_models=1, models=[{
        'name': 'default_model',
        'nummesh': 1,
        'numverts': 3,
        'numnorms': 3,
        'verts': [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
        'norms': [[0, 0, 1], [0, 0, 1], [0, 0, 1]],
        'vertbones': [0, 0, 0],
        'normbones': [0, 0, 0],
        'meshes': [{
            'numtris': 1,
            'skinref': 0,
            'tricmds': [3, 0, 0, 0, 0, 1, 1, 4, 0, 2, 2, 0, 4, 0],
        }],
    }])

    return b.build()


def generate_seed_texture_flags():
    """seed_texture_flags.mdl - MDL with various texture flags (flatshade, chrome, additive, masked)."""
    b = HL1MDLBuilder()
    b.model_name = "texflags_test"

    b.add_bone("bone_root", parent=-1)

    b.add_texture("flat.bmp", width=4, height=4, flags=0x0001)     # FLATSHADE
    b.add_texture("chrome.bmp", width=4, height=4, flags=0x0002)   # CHROME
    b.add_texture("additive.bmp", width=4, height=4, flags=0x0020) # ADDITIVE
    b.add_texture("masked.bmp", width=4, height=4, flags=0x0040)   # MASKED

    b.add_seq_group("default")
    b.add_sequence("idle", fps=30.0, numframes=1)

    return b.build()


def generate_seed_minimal():
    """seed_minimal.mdl - Minimal valid MDL with no bodyparts (texture-only MDL)."""
    b = HL1MDLBuilder()
    b.model_name = "minimal_test"

    b.add_bone("bone_root", parent=-1)
    b.add_texture("min_tex.bmp", width=2, height=2)
    b.add_seq_group("default")
    b.add_sequence("idle", fps=30.0, numframes=1)

    # No bodyparts -- will set AI_SCENE_FLAGS_INCOMPLETE
    return b.build()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    seeds = {
        "seed_bone_controllers.mdl": generate_seed_bone_controllers,
        "seed_hitboxes.mdl": generate_seed_hitboxes,
        "seed_attachments.mdl": generate_seed_attachments,
        "seed_transitions.mdl": generate_seed_transitions,
        "seed_full_hl1.mdl": generate_seed_full,
        "seed_anim_events.mdl": generate_seed_anim_events,
        "seed_multi_bodypart.mdl": generate_seed_multi_bodypart,
        "seed_skin_families.mdl": generate_seed_skin_families,
        "seed_texture_flags.mdl": generate_seed_texture_flags,
        "seed_minimal.mdl": generate_seed_minimal,
    }

    for name, gen_func in seeds.items():
        filepath = os.path.join(OUTPUT_DIR, name)
        data = gen_func()
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"Generated {filepath} ({len(data)} bytes)")

    print(f"\nAll {len(seeds)} seed files generated in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
