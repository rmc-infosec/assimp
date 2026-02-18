#!/usr/bin/env python3
"""Generate 3MF seed files targeting uncovered code paths in XmlSerializer.cpp.

Targets:
  - seed_components.3mf: Objects with component references (assembly tree)
  - seed_materials_textures.3mf: texture2d, texture2dgroup, colorgroup with per-triangle pids
  - seed_metadata.3mf: Metadata under resources, build items with transforms
"""

import os
import zipfile
import io

SEED_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "test", "models", "3MF", "fuzz_seeds"
)

CONTENT_TYPES_XML = '<?xml version="1.0" encoding="UTF-8"?>' \
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' \
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' \
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>' \
    '</Types>'

RELS_XML = '<?xml version="1.0" encoding="UTF-8"?>' \
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' \
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" ' \
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>' \
    '</Relationships>'


def write_3mf(filename, model_xml):
    """Create a 3MF ZIP file with the required structure."""
    os.makedirs(SEED_DIR, exist_ok=True)
    path = os.path.join(SEED_DIR, filename)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", RELS_XML)
        zf.writestr("3D/3dmodel.model", model_xml)
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    print(f"  {path} ({len(buf.getvalue())} bytes)")


def generate_seed_components():
    """Objects with component references forming an assembly tree.

    Covers:
      - ReadObject: component parsing branch (line 385-401)
      - addObjectToNode: recursive component traversal (line 309-314)
      - parseTransformMatrix: component transform parsing (line 116-158)
      - Build item with transform (line 256-266)
    """
    model_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="10" y="0" z="0"/>
          <vertex x="5" y="10" z="0"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
        </triangles>
      </mesh>
    </object>
    <object id="2" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="5" y="0" z="0"/>
          <vertex x="2" y="5" z="0"/>
          <vertex x="2" y="2" z="5"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
          <triangle v1="0" v2="1" v3="3"/>
          <triangle v1="1" v2="2" v3="3"/>
          <triangle v1="0" v2="2" v3="3"/>
        </triangles>
      </mesh>
    </object>
    <object id="3" type="model">
      <components>
        <component objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
        <component objectid="2" transform="2 0 0 0 2 0 0 0 2 10 0 0"/>
      </components>
    </object>
    <object id="4" type="model">
      <components>
        <component objectid="3" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
        <component objectid="1" transform="0.7 0.7 0 -0.7 0.7 0 0 0 1 20 0 0"/>
      </components>
    </object>
  </resources>
  <build>
    <item objectid="4" transform="1 0 0 0 1 0 0 0 1 5 5 5"/>
    <item objectid="1"/>
    <item objectid="2" transform="1 0 0 0 1 0 0 0 1 -10 0 0"/>
  </build>
</model>"""
    write_3mf("seed_components.3mf", model_xml)


def generate_seed_materials_textures():
    """Multiple material types: texture2d, tex2dgroup, colorgroup, basematerials.

    Covers:
      - ReadEmbeddecTexture (line 563-591): m:texture2d element with path,
        contenttype, tilestyleu, tilestylev attributes
      - StoreEmbeddedTexture (line 593-608): material creation from texture
      - ReadTextureGroup / ReadTextureCoords2D (line 610-647): m:texture2dgroup
        with m:tex2coord children having u/v attributes
      - ReadColorGroup / ReadColor (line 675-705): m:colorgroup with m:color
        children having "color" attribute
      - ImportTriangles RT_Texture2DGroup branch (line 481-512): per-triangle
        texture coord assignment via pid pointing to tex2dgroup
      - ImportTriangles RT_ColorGroup branch (line 514-531): per-triangle
        vertex color assignment via pid pointing to colorgroup
      - ReadObject RT_Texture2DGroup branch (line 340-368): object-level pid
        pointing to tex2dgroup, sets default UVs from pindex
      - ReadObject RT_ColorGroup branch (line 369-378): object-level pid
        pointing to colorgroup, sets default vertex colors from pindex
      - ReadBaseMaterials (line 546-561): basematerials with named bases
      - parseColor with #RRGGBB and #RRGGBBAA formats (line 160-190)
    """
    # The m: prefix tags must match XmlTag constants exactly:
    #   texture_2d = "m:texture2d"
    #   texture_group = "m:texture2dgroup"
    #   texture_2d_coord = "m:tex2coord"
    #   colorgroup = "m:colorgroup"
    #   color_item = "m:color"
    model_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter"
       xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
       xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">
  <resources>
    <basematerials id="1">
      <base name="Red" displaycolor="#FF0000"/>
      <base name="GreenAlpha" displaycolor="#00FF0080"/>
    </basematerials>

    <m:texture2d id="10" path="/3D/Textures/wood.png"
                 contenttype="image/png"
                 tilestyleu="wrap" tilestylev="mirror"/>

    <m:texture2dgroup id="11" texid="10">
      <m:tex2coord u="0.0" v="0.0"/>
      <m:tex2coord u="1.0" v="0.0"/>
      <m:tex2coord u="0.5" v="1.0"/>
      <m:tex2coord u="0.5" v="0.5"/>
    </m:texture2dgroup>

    <m:colorgroup id="20">
      <m:color color="#FF0000"/>
      <m:color color="#00FF00FF"/>
      <m:color color="#0000FF"/>
    </m:colorgroup>

    <object id="2" type="model" pid="11" pindex="0">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="10" y="0" z="0"/>
          <vertex x="5" y="10" z="0"/>
          <vertex x="5" y="5" z="8"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2" pid="11" p1="0" p2="1" p3="2"/>
          <triangle v1="0" v2="1" v3="3" pid="11" p1="0" p2="1" p3="3"/>
          <triangle v1="1" v2="2" v3="3"/>
          <triangle v1="0" v2="2" v3="3"/>
        </triangles>
      </mesh>
    </object>

    <object id="3" type="model" pid="20" pindex="0">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="6" y="0" z="0"/>
          <vertex x="3" y="6" z="0"/>
          <vertex x="3" y="3" z="6"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2" pid="20" p1="0" p2="1" p3="2"/>
          <triangle v1="0" v2="1" v3="3" pid="20" p1="0" p2="1" p3="2"/>
          <triangle v1="1" v2="2" v3="3"/>
          <triangle v1="0" v2="2" v3="3"/>
        </triangles>
      </mesh>
    </object>

    <object id="4" type="model" pid="1" pindex="0">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="8" y="0" z="0"/>
          <vertex x="4" y="8" z="0"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2" pid="1" p1="0" p2="1" p3="0"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="2"/>
    <item objectid="3" transform="1 0 0 0 1 0 0 0 1 15 0 0"/>
    <item objectid="4"/>
  </build>
</model>"""
    write_3mf("seed_materials_textures.3mf", model_xml)


def generate_seed_metadata():
    """Metadata entries under resources, build items with transforms.

    Covers:
      - ReadMetadata (line 425-437): metadata elements with name attribute
        and text value, stored in mMetaData vector
      - ImportXml metadata import (line 271-278): scene metadata allocation
        and population from mMetaData
      - Build items with transform (line 252-266): parseTransformMatrix
        covering all 12 matrix elements
      - Object with hasName (readMaterialDef hasName=true branch, line 660)
      - Object without material (no pid) to cover the default path
    """
    model_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <metadata name="Title">Fuzzing Test Model</metadata>
    <metadata name="Designer">Assimp Fuzzer</metadata>
    <metadata name="Description">Coverage seed for metadata paths</metadata>
    <metadata name="Copyright">2026 Test</metadata>
    <metadata name="LicenseTerms">MIT</metadata>

    <basematerials id="1">
      <base name="MatA" displaycolor="#AABB22"/>
      <base displaycolor="#112233FF"/>
    </basematerials>

    <object id="2" type="model" pid="1" pindex="0">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="10" y="0" z="0"/>
          <vertex x="5" y="10" z="0"/>
          <vertex x="5" y="5" z="10"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2" pid="1" p1="0"/>
          <triangle v1="0" v2="1" v3="3" pid="1" p1="1"/>
          <triangle v1="0" v2="2" v3="3"/>
          <triangle v1="1" v2="2" v3="3"/>
        </triangles>
      </mesh>
    </object>

    <object id="3" type="model">
      <mesh>
        <vertices>
          <vertex x="-5" y="-5" z="0"/>
          <vertex x="5" y="-5" z="0"/>
          <vertex x="0" y="5" z="0"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="2" transform="0.5 0 0 0 0.5 0 0 0 0.5 10 20 30"/>
    <item objectid="3" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
  </build>
</model>"""
    write_3mf("seed_metadata.3mf", model_xml)


if __name__ == "__main__":
    print("Generating 3MF coverage seeds...")
    generate_seed_components()
    generate_seed_materials_textures()
    generate_seed_metadata()
    print("Done.")
