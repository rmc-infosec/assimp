#!/usr/bin/env python3
"""Generate minimal 3MF seed files for fuzzing coverage."""

import os
import zipfile
import io

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>"""

RELS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""


def write_3mf(filename, model_xml):
    """Create a 3MF ZIP file with the required structure."""
    path = os.path.join(SCRIPT_DIR, filename)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML)
        zf.writestr("_rels/.rels", RELS_XML)
        zf.writestr("3D/3dmodel.model", model_xml)
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Generated {path} ({len(buf.getvalue())} bytes)")


def generate_seed_simple():
    """Simple 3MF with one object (triangle mesh)."""
    model_xml = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="10" y="0" z="0"/>
          <vertex x="5" y="10" z="0"/>
          <vertex x="5" y="5" z="10"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
          <triangle v1="0" v2="1" v3="3"/>
          <triangle v1="0" v2="2" v3="3"/>
          <triangle v1="1" v2="2" v3="3"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1"/>
  </build>
</model>"""
    write_3mf("seed_simple.3mf", model_xml)


def generate_seed_materials():
    """3MF with material definitions (basematerials)."""
    model_xml = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <basematerials id="1">
      <base name="Red" displaycolor="#FF0000"/>
      <base name="Green" displaycolor="#00FF00"/>
      <base name="Blue" displaycolor="#0000FFCC"/>
    </basematerials>
    <object id="2" type="model" pid="1" pindex="0">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="20" y="0" z="0"/>
          <vertex x="10" y="20" z="0"/>
          <vertex x="10" y="10" z="15"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2" pid="1" p1="0"/>
          <triangle v1="0" v2="1" v3="3" pid="1" p1="1"/>
          <triangle v1="0" v2="2" v3="3" pid="1" p1="2"/>
          <triangle v1="1" v2="2" v3="3" pid="1" p1="0"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="2"/>
  </build>
</model>"""
    write_3mf("seed_materials.3mf", model_xml)


def generate_seed_multiobject():
    """3MF with multiple objects and transforms."""
    model_xml = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <metadata name="Title">Multi-object test</metadata>
  <resources>
    <basematerials id="1">
      <base name="Material1" displaycolor="#AA3322"/>
      <base name="Material2" displaycolor="#2233AA"/>
    </basematerials>
    <object id="2" type="model" pid="1" pindex="0">
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
    <object id="3" type="model" pid="1" pindex="1">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="5" y="0" z="0"/>
          <vertex x="5" y="5" z="0"/>
          <vertex x="0" y="5" z="0"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
          <triangle v1="0" v2="2" v3="3"/>
        </triangles>
      </mesh>
    </object>
    <object id="4" type="model">
      <components>
        <component objectid="2" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>
        <component objectid="3" transform="1 0 0 0 1 0 0 0 1 20 0 0"/>
      </components>
    </object>
  </resources>
  <build>
    <item objectid="2"/>
    <item objectid="3" transform="1 0 0 0 1 0 0 0 1 15 0 0"/>
    <item objectid="4"/>
  </build>
</model>"""
    write_3mf("seed_multiobject.3mf", model_xml)


if __name__ == "__main__":
    generate_seed_simple()
    generate_seed_materials()
    generate_seed_multiobject()
    print("Done generating 3MF seeds.")
