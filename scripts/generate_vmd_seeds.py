#!/usr/bin/env python3
"""Generate VMD (Vocaloid Motion Data) binary seed files for fuzzing.

VMD binary format (little-endian):
  Header:
    - 30 bytes: magic "Vocaloid Motion Data 0002" + null padding
    - 20 bytes: model name (Shift-JIS, null-padded)
  Bone keyframes:
    - uint32: count
    - Per frame (111 bytes each):
        - 15 bytes: bone name (null-padded)
        - int32: frame number
        - float[3]: position (x, y, z)
        - float[4]: orientation quaternion (x, y, z, w)
        - char[64]: interpolation parameters (4x4x4)
  Face/Morph keyframes:
    - uint32: count
    - Per frame (23 bytes each):
        - 15 bytes: face name (null-padded)
        - uint32: frame number
        - float: weight
  Camera keyframes:
    - uint32: count
    - Per frame (63 bytes each):
        - int32: frame number
        - float: distance
        - float[3]: position (x, y, z)
        - float[3]: orientation (x, y, z) in radians
        - char[24]: interpolation parameters (6x4)
        - float: viewing angle
        - char[3]: unknown (perspective flag etc.)
  Light keyframes:
    - uint32: count
    - Per frame (28 bytes each):
        - int32: frame number
        - float[3]: color (r, g, b)
        - float[3]: position (x, y, z)
  Self-shadow:
    - uint32: count (4 bytes, always 0 for our seeds)
  IK keyframes:
    - uint32: count
    - Per frame:
        - int32: frame number
        - uint8: display flag
        - int32: ik_count
        - Per IK entry:
            - 20 bytes: ik name (null-padded)
            - uint8: enable flag
"""

import struct
import os

MAGIC = b"Vocaloid Motion Data 0002"
MAGIC_PADDED = MAGIC + b"\x00" * (30 - len(MAGIC))
assert len(MAGIC_PADDED) == 30

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "test", "models", "MMD", "fuzz_seeds"
)


def pad_bytes(data, length):
    """Pad or truncate bytes to exact length, null-padded."""
    if isinstance(data, str):
        data = data.encode("ascii")
    return data[:length].ljust(length, b"\x00")


def make_header(model_name="TestModel"):
    """Create a 50-byte VMD header (30 magic + 20 model name)."""
    return MAGIC_PADDED + pad_bytes(model_name, 20)


def make_bone_frame(name, frame_no, pos=(0.0, 0.0, 0.0),
                    orient=(0.0, 0.0, 0.0, 1.0), interpolation=None):
    """Create a 111-byte bone keyframe.

    Args:
        name: Bone name string (max 15 bytes)
        frame_no: Frame number (int32)
        pos: (x, y, z) position floats
        orient: (x, y, z, w) quaternion floats
        interpolation: 64 bytes of interpolation data, or None for defaults
    """
    data = pad_bytes(name, 15)
    data += struct.pack("<i", frame_no)
    data += struct.pack("<3f", *pos)
    data += struct.pack("<4f", *orient)
    if interpolation is None:
        # Default linear interpolation: diagonal pattern
        interp = bytearray(64)
        for i in range(4):
            interp[i * 16 + 0] = 20   # x1
            interp[i * 16 + 4] = 20   # y1
            interp[i * 16 + 8] = 107  # x2
            interp[i * 16 + 12] = 107  # y2
        data += bytes(interp)
    else:
        assert len(interpolation) == 64
        data += interpolation
    assert len(data) == 111, f"Bone frame size: {len(data)}, expected 111"
    return data


def make_face_frame(name, frame_no, weight):
    """Create a 23-byte face/morph keyframe.

    Args:
        name: Morph name string (max 15 bytes)
        frame_no: Frame number (uint32)
        weight: Morph weight (float)
    """
    data = pad_bytes(name, 15)
    data += struct.pack("<I", frame_no)
    data += struct.pack("<f", weight)
    assert len(data) == 23, f"Face frame size: {len(data)}, expected 23"
    return data


def make_camera_frame(frame_no, distance, pos=(0.0, 0.0, 0.0),
                      orient=(0.0, 0.0, 0.0), angle=30.0):
    """Create a 63-byte camera keyframe.

    Args:
        frame_no: Frame number (int32)
        distance: Camera distance (float)
        pos: (x, y, z) position
        orient: (x, y, z) rotation in radians
        angle: Viewing angle (float)
    """
    data = struct.pack("<i", frame_no)
    data += struct.pack("<f", distance)
    data += struct.pack("<3f", *pos)
    data += struct.pack("<3f", *orient)
    # Interpolation: 24 bytes (6 axes x 4 control points)
    interp = bytearray(24)
    for i in range(6):
        interp[i * 4 + 0] = 20   # x1
        interp[i * 4 + 1] = 20   # y1
        interp[i * 4 + 2] = 107  # x2
        interp[i * 4 + 3] = 107  # y2
    data += bytes(interp)
    data += struct.pack("<f", angle)
    # unknown 3 bytes (perspective flag etc.)
    data += b"\x01\x00\x00"
    assert len(data) == 63, f"Camera frame size: {len(data)}, expected 63"
    return data


def make_light_frame(frame_no, color=(1.0, 1.0, 1.0), pos=(0.0, 10.0, 0.0)):
    """Create a 28-byte light keyframe.

    Args:
        frame_no: Frame number (int32)
        color: (r, g, b) color values
        pos: (x, y, z) position
    """
    data = struct.pack("<i", frame_no)
    data += struct.pack("<3f", *color)
    data += struct.pack("<3f", *pos)
    assert len(data) == 28, f"Light frame size: {len(data)}, expected 28"
    return data


def make_ik_frame(frame_no, display=True, ik_entries=None):
    """Create an IK keyframe.

    Args:
        frame_no: Frame number (int32)
        display: Display flag (bool/uint8)
        ik_entries: List of (name, enable) tuples, or None for empty
    """
    data = struct.pack("<i", frame_no)
    data += struct.pack("<B", 1 if display else 0)
    if ik_entries is None:
        ik_entries = []
    data += struct.pack("<i", len(ik_entries))
    for name, enable in ik_entries:
        data += pad_bytes(name, 20)
        data += struct.pack("<B", 1 if enable else 0)
    return data


def write_vmd(filepath, bone_frames=None, face_frames=None,
              camera_frames=None, light_frames=None, ik_frames=None,
              model_name="TestModel"):
    """Write a complete VMD file.

    The file format is sequential: header, bones, faces, cameras, lights,
    self-shadow count (0), then IK frame count and IK frames.
    """
    bone_frames = bone_frames or []
    face_frames = face_frames or []
    camera_frames = camera_frames or []
    light_frames = light_frames or []
    ik_frames = ik_frames or []

    with open(filepath, "wb") as f:
        # Header
        f.write(make_header(model_name))

        # Bone keyframes
        f.write(struct.pack("<I", len(bone_frames)))
        for frame in bone_frames:
            f.write(frame)

        # Face/Morph keyframes
        f.write(struct.pack("<I", len(face_frames)))
        for frame in face_frames:
            f.write(frame)

        # Camera keyframes
        f.write(struct.pack("<I", len(camera_frames)))
        for frame in camera_frames:
            f.write(frame)

        # Light keyframes
        f.write(struct.pack("<I", len(light_frames)))
        for frame in light_frames:
            f.write(frame)

        # Self-shadow data: always 0 entries (4 bytes read by parser as "unknown2")
        f.write(struct.pack("<I", 0))

        # IK keyframes: always write count (parser checks EOF before reading)
        f.write(struct.pack("<I", len(ik_frames)))
        for frame in ik_frames:
            f.write(frame)

    size = os.path.getsize(filepath)
    print(f"  Written: {filepath} ({size} bytes)")


def generate_vmd_ik_frames():
    """Seed 1: vmd_ik_frames.vmd - IK frames with 3 IK entries with different enable states."""
    ik_frames = [
        make_ik_frame(
            frame_no=0,
            display=True,
            ik_entries=[
                ("LeftFootIK", True),
                ("RightFootIK", False),
                ("LeftToeIK", True),
            ],
        ),
    ]

    filepath = os.path.join(OUTPUT_DIR, "vmd_ik_frames.vmd")
    write_vmd(filepath, ik_frames=ik_frames, model_name="IKTestModel")


def generate_vmd_camera_light():
    """Seed 2: vmd_camera_light.vmd - 3 camera frames + 2 light frames, no bone/face frames."""
    cameras = [
        make_camera_frame(
            frame_no=0,
            distance=-45.0,
            pos=(0.0, 15.0, 0.0),
            orient=(0.0, 0.0, 0.0),
            angle=30.0,
        ),
        make_camera_frame(
            frame_no=30,
            distance=-20.0,
            pos=(5.0, 10.0, -3.0),
            orient=(0.2, -0.1, 0.0),
            angle=45.0,
        ),
        make_camera_frame(
            frame_no=60,
            distance=-35.0,
            pos=(-2.0, 12.0, 5.0),
            orient=(-0.15, 0.3, 0.05),
            angle=27.0,
        ),
    ]

    lights = [
        make_light_frame(
            frame_no=0,
            color=(0.6, 0.6, 0.6),
            pos=(-0.5, -1.0, 0.5),
        ),
        make_light_frame(
            frame_no=30,
            color=(1.0, 0.9, 0.8),
            pos=(0.3, -0.8, -0.2),
        ),
    ]

    filepath = os.path.join(OUTPUT_DIR, "vmd_camera_light.vmd")
    write_vmd(filepath, camera_frames=cameras, light_frames=lights,
              model_name="CameraLightModel")


def generate_vmd_all_sections():
    """Seed 3: vmd_all_sections.vmd - All sections: 1 bone, 1 face, 2 camera, 1 light, 1 IK with 2 IK entries."""
    bones = [
        make_bone_frame(
            name="Center",
            frame_no=0,
            pos=(0.0, 0.0, 0.0),
            orient=(0.0, 0.0, 0.0, 1.0),
        ),
    ]

    faces = [
        make_face_frame("Smile", frame_no=0, weight=0.75),
    ]

    cameras = [
        make_camera_frame(
            frame_no=0,
            distance=-30.0,
            pos=(0.0, 12.0, 0.0),
            orient=(0.0, 0.0, 0.0),
            angle=27.0,
        ),
        make_camera_frame(
            frame_no=20,
            distance=-25.0,
            pos=(3.0, 10.0, -1.0),
            orient=(0.1, -0.05, 0.0),
            angle=35.0,
        ),
    ]

    lights = [
        make_light_frame(
            frame_no=0,
            color=(1.0, 0.95, 0.9),
            pos=(-0.5, -1.0, 0.5),
        ),
    ]

    ik_frames = [
        make_ik_frame(
            frame_no=0,
            display=True,
            ik_entries=[
                ("LeftLegIK", True),
                ("RightLegIK", False),
            ],
        ),
    ]

    filepath = os.path.join(OUTPUT_DIR, "vmd_all_sections.vmd")
    write_vmd(filepath, bone_frames=bones, face_frames=faces,
              camera_frames=cameras, light_frames=lights,
              ik_frames=ik_frames, model_name="AllSectionsModel")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating VMD seed files in: {OUTPUT_DIR}")
    print()

    generate_vmd_ik_frames()
    generate_vmd_camera_light()
    generate_vmd_all_sections()

    print()
    print("Done! Generated 3 VMD seed files.")


if __name__ == "__main__":
    main()
