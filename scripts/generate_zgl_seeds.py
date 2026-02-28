#!/usr/bin/env python3
"""Generate ZGL (compressed XGL) seed files for fuzzing.

ZGL format as handled by assimp's XGLLoader:
- 2-byte CRC16 prefix (skipped during decompression)
- Raw deflate compressed data (NOT gzip - uses -MaxWBits which is raw deflate)

The loader uses Compression::Format::Binary with -MaxWBits, which means
raw deflate without any gzip or zlib wrapper.
"""

import zlib
import os
import struct

SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'test', 'models', 'XGL', 'fuzz_seeds')

def make_zgl(xgl_content: bytes, crc16: int = 0) -> bytes:
    """Create a ZGL file from XGL content.

    Args:
        xgl_content: The raw XGL XML data.
        crc16: 2-byte CRC16 value to prepend (default 0).

    Returns:
        bytes: The ZGL file content (2-byte CRC16 + raw deflate data).
    """
    # Use raw deflate (wbits=-15 means raw deflate, no header)
    # This matches assimp's Compression::Format::Binary with -MaxWBits
    compress_obj = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    compressed = compress_obj.compress(xgl_content)
    compressed += compress_obj.flush()

    # Prepend 2-byte CRC16
    return struct.pack('<H', crc16) + compressed


def main():
    os.makedirs(SEED_DIR, exist_ok=True)

    # Read all existing XGL seeds and create ZGL versions
    xgl_files = [f for f in os.listdir(SEED_DIR) if f.endswith('.xgl')]

    for xgl_file in sorted(xgl_files):
        xgl_path = os.path.join(SEED_DIR, xgl_file)
        with open(xgl_path, 'rb') as f:
            xgl_data = f.read()

        # Create ZGL version with zero CRC
        zgl_name = xgl_file.replace('.xgl', '.zgl')
        zgl_path = os.path.join(SEED_DIR, zgl_name)
        zgl_data = make_zgl(xgl_data, crc16=0)
        with open(zgl_path, 'wb') as f:
            f.write(zgl_data)
        print(f"  Created {zgl_name} ({len(zgl_data)} bytes from {len(xgl_data)} bytes XGL)")

    # Also create a minimal ZGL seed
    minimal_xgl = b'<WORLD><MAT ID="1"><DIFF>0.5,0.5,0.5</DIFF><SHINE>10.0</SHINE><ALPHA>1.0</ALPHA></MAT><MESH><F><MATREF>1</MATREF><FV1><P>0.0,0.0,0.0</P><N>0.0,0.0,1.0</N></FV1><FV2><P>1.0,0.0,0.0</P><N>0.0,0.0,1.0</N></FV2><FV3><P>0.0,1.0,0.0</P><N>0.0,0.0,1.0</N></FV3></F></MESH></WORLD>'
    zgl_path = os.path.join(SEED_DIR, 'seed_minimal.zgl')
    zgl_data = make_zgl(minimal_xgl, crc16=0)
    with open(zgl_path, 'wb') as f:
        f.write(zgl_data)
    print(f"  Created seed_minimal.zgl ({len(zgl_data)} bytes from {len(minimal_xgl)} bytes XGL)")

    # Create one with non-zero CRC to test that path
    zgl_path = os.path.join(SEED_DIR, 'seed_nonzero_crc.zgl')
    zgl_data = make_zgl(minimal_xgl, crc16=0xABCD)
    with open(zgl_path, 'wb') as f:
        f.write(zgl_data)
    print(f"  Created seed_nonzero_crc.zgl ({len(zgl_data)} bytes)")

    print(f"\nTotal ZGL seeds created in {SEED_DIR}")


if __name__ == '__main__':
    main()
