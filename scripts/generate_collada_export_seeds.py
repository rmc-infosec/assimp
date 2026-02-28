#!/usr/bin/env python3
"""Generate Collada (.dae) seed files designed to exercise ColladaExporter code paths.

These seeds import successfully and produce scenes with features that the Collada
exporter handles during import->export->reimport roundtrip testing.

Targets:
  - Cameras (perspective + orthographic) with node matching
  - Lights (ambient, point, spot) with attenuation and falloff
  - Rich metadata (author, comments, copyright, keywords, etc.)
  - Line primitives
  - Skinning with multiple UV sets
  - Animations with pre/post behavior hints
  - Non-trivial root transforms (Z_UP, non-uniform scaling)

Usage: python3 generate_collada_export_seeds.py /path/to/output
"""

import os
import sys


def seed_export_cameras_lights(outdir):
    """Scene with cameras and lights for export.

    2 cameras: perspective (FOV, aspect, znear, zfar) and orthographic.
    3 lights: ambient, point (with attenuation), spot (with falloff).
    Camera/light nodes named to match camera/light names for exporter node matching.
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01T00:00:00</created>
    <modified>2024-01-01T00:00:00</modified>
  </asset>
  <library_cameras>
    <camera id="PerspCam" name="PerspCam">
      <optics>
        <technique_common>
          <perspective>
            <xfov>60</xfov>
            <aspect_ratio>1.777</aspect_ratio>
            <znear>0.1</znear>
            <zfar>1000</zfar>
          </perspective>
        </technique_common>
      </optics>
    </camera>
    <camera id="OrthoCam" name="OrthoCam">
      <optics>
        <technique_common>
          <orthographic>
            <xmag>5</xmag>
            <ymag>5</ymag>
            <znear>0.01</znear>
            <zfar>500</zfar>
          </orthographic>
        </technique_common>
      </optics>
    </camera>
  </library_cameras>
  <library_lights>
    <light id="AmbientLight" name="AmbientLight">
      <technique_common>
        <ambient>
          <color>0.3 0.3 0.35</color>
        </ambient>
      </technique_common>
    </light>
    <light id="PointLight" name="PointLight">
      <technique_common>
        <point>
          <color>1 0.9 0.8</color>
          <constant_attenuation>1</constant_attenuation>
          <linear_attenuation>0.045</linear_attenuation>
          <quadratic_attenuation>0.0075</quadratic_attenuation>
        </point>
      </technique_common>
    </light>
    <light id="SpotLight" name="SpotLight">
      <technique_common>
        <spot>
          <color>0.2 1 0.5</color>
          <constant_attenuation>1</constant_attenuation>
          <linear_attenuation>0</linear_attenuation>
          <quadratic_attenuation>0.01</quadratic_attenuation>
          <falloff_angle>30</falloff_angle>
          <falloff_exponent>2</falloff_exponent>
        </spot>
      </technique_common>
    </light>
  </library_lights>
  <library_effects>
    <effect id="DefaultFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse><color>0.7 0.7 0.7 1</color></diffuse>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="DefaultMat" name="DefaultMat">
      <instance_effect url="#DefaultFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="TriMesh" name="TriMesh">
      <mesh>
        <source id="tri-pos">
          <float_array id="tri-pos-arr" count="9">0 0 0 1 0 0 0.5 1 0</float_array>
          <technique_common>
            <accessor source="#tri-pos-arr" count="3" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="tri-norm">
          <float_array id="tri-norm-arr" count="9">0 0 1 0 0 1 0 0 1</float_array>
          <technique_common>
            <accessor source="#tri-norm-arr" count="3" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="tri-verts">
          <input semantic="POSITION" source="#tri-pos"/>
        </vertices>
        <triangles count="1" material="mat">
          <input semantic="VERTEX" source="#tri-verts" offset="0"/>
          <input semantic="NORMAL" source="#tri-norm" offset="0"/>
          <p>0 1 2</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="MeshNode" name="MeshNode" type="NODE">
        <instance_geometry url="#TriMesh">
          <bind_material>
            <technique_common>
              <instance_material symbol="mat" target="#DefaultMat"/>
            </technique_common>
          </bind_material>
        </instance_geometry>
      </node>
      <node id="PerspCam" name="PerspCam" type="NODE">
        <translate>0 2 8</translate>
        <rotate>1 0 0 -15</rotate>
        <instance_camera url="#PerspCam"/>
      </node>
      <node id="OrthoCam" name="OrthoCam" type="NODE">
        <translate>5 0 0</translate>
        <rotate>0 1 0 90</rotate>
        <instance_camera url="#OrthoCam"/>
      </node>
      <node id="AmbientLight" name="AmbientLight" type="NODE">
        <instance_light url="#AmbientLight"/>
      </node>
      <node id="PointLight" name="PointLight" type="NODE">
        <translate>3 4 2</translate>
        <instance_light url="#PointLight"/>
      </node>
      <node id="SpotLight" name="SpotLight" type="NODE">
        <translate>0 5 0</translate>
        <rotate>1 0 0 -90</rotate>
        <instance_light url="#SpotLight"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    path = os.path.join(outdir, "seed_export_cameras_lights.dae")
    with open(path, 'w') as f:
        f.write(dae)
    print(f"  Written: {path}")


def seed_export_metadata(outdir):
    """Scene with rich metadata exercising all metadata export paths.

    Asset metadata: author, authoring_tool, comments, copyright, created,
    keywords, revision, subject, title, source_data.
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <contributor>
      <author>Test Author Name</author>
      <authoring_tool>Custom Authoring Tool v1.0</authoring_tool>
      <copyright>Copyright 2024 Test Corp</copyright>
      <source_data>file:///original/source.blend</source_data>
    </contributor>
    <created>2024-06-15T12:00:00</created>
    <modified>2024-06-15T12:00:00</modified>
    <keywords>test fuzzing coverage seed</keywords>
    <revision>42</revision>
    <subject>Test Subject for Export</subject>
    <title>Metadata Export Test Scene</title>
    <comments>This is a test comment for metadata roundtrip</comments>
    <unit name="meter" meter="1"/>
    <up_axis>Y_UP</up_axis>
  </asset>
  <library_effects>
    <effect id="MatFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse><color>0.8 0.4 0.2 1</color></diffuse>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="Mat" name="Mat">
      <instance_effect url="#MatFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="MetaMesh" name="MetaMesh">
      <mesh>
        <source id="pos">
          <float_array id="pos-arr" count="9">0 0 0 1 0 0 0 1 0</float_array>
          <technique_common>
            <accessor source="#pos-arr" count="3" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="verts">
          <input semantic="POSITION" source="#pos"/>
        </vertices>
        <triangles count="1" material="mat">
          <input semantic="VERTEX" source="#verts" offset="0"/>
          <p>0 1 2</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="MetaNode" name="MetaNode" type="NODE">
        <instance_geometry url="#MetaMesh">
          <bind_material>
            <technique_common>
              <instance_material symbol="mat" target="#Mat"/>
            </technique_common>
          </bind_material>
        </instance_geometry>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    path = os.path.join(outdir, "seed_export_metadata.dae")
    with open(path, 'w') as f:
        f.write(dae)
    print(f"  Written: {path}")


def seed_export_line_mesh(outdir):
    """Scene with <lines> primitives (not triangles).

    Exercises the lines code path in the Collada exporter WriteGeometry.
    Multiple line segments with positions and normals, material assigned.
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01T00:00:00</created>
    <modified>2024-01-01T00:00:00</modified>
  </asset>
  <library_effects>
    <effect id="LineFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse><color>1 0 0 1</color></diffuse>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="LineMat" name="LineMat">
      <instance_effect url="#LineFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="LineMesh" name="LineMesh">
      <mesh>
        <source id="line-pos">
          <float_array id="line-pos-arr" count="24">
            0 0 0  1 0 0  1 0 0  1 1 0
            1 1 0  0 1 0  0 1 0  0 0 0
          </float_array>
          <technique_common>
            <accessor source="#line-pos-arr" count="8" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="line-norm">
          <float_array id="line-norm-arr" count="24">
            0 0 1  0 0 1  0 0 1  0 0 1
            0 0 1  0 0 1  0 0 1  0 0 1
          </float_array>
          <technique_common>
            <accessor source="#line-norm-arr" count="8" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="line-verts">
          <input semantic="POSITION" source="#line-pos"/>
        </vertices>
        <lines count="4" material="lineMat">
          <input semantic="VERTEX" source="#line-verts" offset="0"/>
          <input semantic="NORMAL" source="#line-norm" offset="0"/>
          <p>0 1 2 3 4 5 6 7</p>
        </lines>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="LineNode" name="LineNode" type="NODE">
        <instance_geometry url="#LineMesh">
          <bind_material>
            <technique_common>
              <instance_material symbol="lineMat" target="#LineMat"/>
            </technique_common>
          </bind_material>
        </instance_geometry>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    path = os.path.join(outdir, "seed_export_line_mesh.dae")
    with open(path, 'w') as f:
        f.write(dae)
    print(f"  Written: {path}")


def seed_export_skin_multitex(outdir):
    """Scene with skinning AND multiple UV texture coordinate sets.

    Exercises WriteController (skin export) and multi-texcoord paths in
    WriteGeometry. Mesh with positions, normals, 2 UV sets (set=0, set=1),
    a skin controller with 2 joints, bind shape matrix, and vertex weights.
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01T00:00:00</created>
    <modified>2024-01-01T00:00:00</modified>
  </asset>
  <library_effects>
    <effect id="SkinFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse><color>0.6 0.6 0.8 1</color></diffuse>
            <specular><color>1 1 1 1</color></specular>
            <shininess><float>40</float></shininess>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="SkinMat" name="SkinMat">
      <instance_effect url="#SkinFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="SkinMesh" name="SkinMesh">
      <mesh>
        <source id="sk-pos">
          <float_array id="sk-pos-arr" count="18">
            -0.5 0 0  0.5 0 0  -0.5 1 0
             0.5 1 0  -0.5 2 0  0.5 2 0
          </float_array>
          <technique_common>
            <accessor source="#sk-pos-arr" count="6" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="sk-norm">
          <float_array id="sk-norm-arr" count="18">
            0 0 1  0 0 1  0 0 1
            0 0 1  0 0 1  0 0 1
          </float_array>
          <technique_common>
            <accessor source="#sk-norm-arr" count="6" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="sk-uv0">
          <float_array id="sk-uv0-arr" count="12">
            0 0  1 0  0 0.5
            1 0.5  0 1  1 1
          </float_array>
          <technique_common>
            <accessor source="#sk-uv0-arr" count="6" stride="2">
              <param name="S" type="float"/>
              <param name="T" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="sk-uv1">
          <float_array id="sk-uv1-arr" count="12">
            0 0  0.5 0  0 0.5
            0.5 0.5  0 1  0.5 1
          </float_array>
          <technique_common>
            <accessor source="#sk-uv1-arr" count="6" stride="2">
              <param name="S" type="float"/>
              <param name="T" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="sk-verts">
          <input semantic="POSITION" source="#sk-pos"/>
        </vertices>
        <triangles count="4" material="skinMat">
          <input semantic="VERTEX" source="#sk-verts" offset="0"/>
          <input semantic="NORMAL" source="#sk-norm" offset="0"/>
          <input semantic="TEXCOORD" source="#sk-uv0" offset="0" set="0"/>
          <input semantic="TEXCOORD" source="#sk-uv1" offset="0" set="1"/>
          <p>0 1 2  1 3 2  2 3 4  3 5 4</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_controllers>
    <controller id="SkinCtrl" name="SkinCtrl">
      <skin source="#SkinMesh">
        <bind_shape_matrix>
          1 0 0 0
          0 1 0 0
          0 0 1 0
          0 0 0 1
        </bind_shape_matrix>
        <source id="sk-joints">
          <Name_array id="sk-joints-arr" count="2">RootBone TipBone</Name_array>
          <technique_common>
            <accessor source="#sk-joints-arr" count="2" stride="1">
              <param name="JOINT" type="name"/>
            </accessor>
          </technique_common>
        </source>
        <source id="sk-ibm">
          <float_array id="sk-ibm-arr" count="32">
            1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1
            1 0 0 0  0 1 0 -1  0 0 1 0  0 0 0 1
          </float_array>
          <technique_common>
            <accessor source="#sk-ibm-arr" count="2" stride="16">
              <param name="TRANSFORM" type="float4x4"/>
            </accessor>
          </technique_common>
        </source>
        <source id="sk-weights">
          <float_array id="sk-weights-arr" count="4">1.0 0.5 0.5 0.0</float_array>
          <technique_common>
            <accessor source="#sk-weights-arr" count="4" stride="1">
              <param name="WEIGHT" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <joints>
          <input semantic="JOINT" source="#sk-joints"/>
          <input semantic="INV_BIND_MATRIX" source="#sk-ibm"/>
        </joints>
        <vertex_weights count="6">
          <input semantic="JOINT" source="#sk-joints" offset="0"/>
          <input semantic="WEIGHT" source="#sk-weights" offset="1"/>
          <vcount>1 1 2 2 1 1</vcount>
          <v>
            0 0
            0 0
            0 1  1 2
            0 1  1 2
            1 0
            1 0
          </v>
        </vertex_weights>
      </skin>
    </controller>
  </library_controllers>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="Armature" name="Armature" type="NODE">
        <node id="RootBone" name="RootBone" sid="RootBone" type="JOINT">
          <matrix sid="transform">1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1</matrix>
          <node id="TipBone" name="TipBone" sid="TipBone" type="JOINT">
            <matrix sid="transform">1 0 0 0  0 1 0 1  0 0 1 0  0 0 0 1</matrix>
          </node>
        </node>
      </node>
      <node id="SkinNode" name="SkinNode" type="NODE">
        <instance_controller url="#SkinCtrl">
          <skeleton>#RootBone</skeleton>
          <bind_material>
            <technique_common>
              <instance_material symbol="skinMat" target="#SkinMat">
                <bind_vertex_input semantic="CHANNEL0" input_semantic="TEXCOORD" input_set="0"/>
                <bind_vertex_input semantic="CHANNEL1" input_semantic="TEXCOORD" input_set="1"/>
              </instance_material>
            </technique_common>
          </bind_material>
        </instance_controller>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    path = os.path.join(outdir, "seed_export_skin_multitex.dae")
    with open(path, 'w') as f:
        f.write(dae)
    print(f"  Written: {path}")


def seed_export_anim_behaviors(outdir):
    """Scene with animations using matrix transforms and multiple keyframes.

    Exercises WriteAnimationLibrary and WriteAnimationsLibrary paths.
    Animation with position+rotation+scaling keys packed into matrix output.
    The default mPreState=aiAnimBehaviour_DEFAULT produces LINEAR interpolation.
    Multiple keyframes to exercise the matrix composition loop.
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01T00:00:00</created>
    <modified>2024-01-01T00:00:00</modified>
  </asset>
  <library_effects>
    <effect id="AnimFX">
      <profile_COMMON>
        <technique sid="common">
          <lambert>
            <diffuse><color>0.3 0.7 0.3 1</color></diffuse>
          </lambert>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="AnimMat" name="AnimMat">
      <instance_effect url="#AnimFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="AnimMesh" name="AnimMesh">
      <mesh>
        <source id="apos">
          <float_array id="apos-arr" count="12">
            -0.5 -0.5 0  0.5 -0.5 0  0.5 0.5 0  -0.5 0.5 0
          </float_array>
          <technique_common>
            <accessor source="#apos-arr" count="4" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="anorm">
          <float_array id="anorm-arr" count="12">
            0 0 1  0 0 1  0 0 1  0 0 1
          </float_array>
          <technique_common>
            <accessor source="#anorm-arr" count="4" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="averts">
          <input semantic="POSITION" source="#apos"/>
        </vertices>
        <triangles count="2" material="animMat">
          <input semantic="VERTEX" source="#averts" offset="0"/>
          <input semantic="NORMAL" source="#anorm" offset="0"/>
          <p>0 1 2  0 2 3</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_animations>
    <animation id="NodeAnim" name="NodeAnim">
      <source id="anim-input">
        <float_array id="anim-input-arr" count="4">0 0.5 1.0 1.5</float_array>
        <technique_common>
          <accessor source="#anim-input-arr" count="4" stride="1">
            <param name="TIME" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="anim-output">
        <float_array id="anim-output-arr" count="64">
          1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1
          1 0 0 2  0 1 0 0  0 0 1 0  0 0 0 1
          0.707 0.707 0 2  -0.707 0.707 0 1  0 0 1 0  0 0 0 1
          1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1
        </float_array>
        <technique_common>
          <accessor source="#anim-output-arr" count="4" stride="16">
            <param name="TRANSFORM" type="float4x4"/>
          </accessor>
        </technique_common>
      </source>
      <source id="anim-interp">
        <Name_array id="anim-interp-arr" count="4">LINEAR LINEAR LINEAR LINEAR</Name_array>
        <technique_common>
          <accessor source="#anim-interp-arr" count="4" stride="1">
            <param name="INTERPOLATION" type="name"/>
          </accessor>
        </technique_common>
      </source>
      <sampler id="anim-sampler">
        <input semantic="INPUT" source="#anim-input"/>
        <input semantic="OUTPUT" source="#anim-output"/>
        <input semantic="INTERPOLATION" source="#anim-interp"/>
      </sampler>
      <channel source="#anim-sampler" target="AnimatedNode/matrix"/>
    </animation>
  </library_animations>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="AnimatedNode" name="AnimatedNode" type="NODE">
        <matrix sid="matrix">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>
        <instance_geometry url="#AnimMesh">
          <bind_material>
            <technique_common>
              <instance_material symbol="animMat" target="#AnimMat"/>
            </technique_common>
          </bind_material>
        </instance_geometry>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    path = os.path.join(outdir, "seed_export_anim_behaviors.dae")
    with open(path, 'w') as f:
        f.write(dae)
    print(f"  Written: {path}")


def seed_export_root_transform(outdir):
    """Scene with Z_UP axis and non-trivial root transform.

    When Z_UP is specified, the Collada loader applies a rotation to the root
    node. On re-export, the exporter detects Z_UP rotation and writes
    <up_axis>Z_UP</up_axis>. Non-uniform scaling forces mAdd_root_node = true.
    Also tests the root-node-has-meshes path (mScene->mRootNode->mMeshes != nullptr).
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01T00:00:00</created>
    <modified>2024-01-01T00:00:00</modified>
    <unit name="meter" meter="1"/>
    <up_axis>Z_UP</up_axis>
  </asset>
  <library_effects>
    <effect id="RootFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse><color>0.9 0.5 0.1 1</color></diffuse>
            <specular><color>1 1 1 1</color></specular>
            <shininess><float>60</float></shininess>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="RootMat" name="RootMat">
      <instance_effect url="#RootFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="CubeMesh" name="CubeMesh">
      <mesh>
        <source id="cube-pos">
          <float_array id="cube-pos-arr" count="24">
            -1 -1 0  1 -1 0  1 1 0  -1 1 0
            -1 -1 2  1 -1 2  1 1 2  -1 1 2
          </float_array>
          <technique_common>
            <accessor source="#cube-pos-arr" count="8" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="cube-norm">
          <float_array id="cube-norm-arr" count="24">
            0 0 -1  0 0 -1  0 0 -1  0 0 -1
            0 0 1   0 0 1   0 0 1   0 0 1
          </float_array>
          <technique_common>
            <accessor source="#cube-norm-arr" count="8" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="cube-verts">
          <input semantic="POSITION" source="#cube-pos"/>
        </vertices>
        <triangles count="4" material="rootMat">
          <input semantic="VERTEX" source="#cube-verts" offset="0"/>
          <input semantic="NORMAL" source="#cube-norm" offset="0"/>
          <p>0 1 2  0 2 3  4 5 6  4 6 7</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="ScaledNode" name="ScaledNode" type="NODE">
        <scale>2 1 1.5</scale>
        <rotate>0 0 1 45</rotate>
        <instance_geometry url="#CubeMesh">
          <bind_material>
            <technique_common>
              <instance_material symbol="rootMat" target="#RootMat"/>
            </technique_common>
          </bind_material>
        </instance_geometry>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    path = os.path.join(outdir, "seed_export_root_transform.dae")
    with open(path, 'w') as f:
        f.write(dae)
    print(f"  Written: {path}")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} /path/to/output")
        sys.exit(1)

    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)

    generators = [
        ("seed_export_cameras_lights.dae", seed_export_cameras_lights),
        ("seed_export_metadata.dae", seed_export_metadata),
        ("seed_export_line_mesh.dae", seed_export_line_mesh),
        ("seed_export_skin_multitex.dae", seed_export_skin_multitex),
        ("seed_export_anim_behaviors.dae", seed_export_anim_behaviors),
        ("seed_export_root_transform.dae", seed_export_root_transform),
    ]

    print(f"Generating {len(generators)} Collada export seed files...")
    for name, gen_func in generators:
        gen_func(outdir)

    print(f"\nDone. {len(generators)} seeds written to {outdir}/")


if __name__ == "__main__":
    main()
