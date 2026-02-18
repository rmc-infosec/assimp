#!/usr/bin/env python3
"""Generate Collada (.dae) seed files targeting uncovered ColladaExporter paths.

Targets: cameras, lights, skinning/controllers, animations, material shading models.
"""

import os
import sys


def seed_collada_camera(outdir):
    """Collada scene with perspective and orthographic cameras."""
    dae = """<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><created>2024-01-01</created><modified>2024-01-01</modified></asset>
  <library_cameras>
    <camera id="PerspCamera" name="PerspCamera">
      <optics><technique_common>
        <perspective>
          <xfov>60</xfov><yfov>45</yfov>
          <znear>0.1</znear><zfar>1000</zfar>
        </perspective>
      </technique_common></optics>
    </camera>
    <camera id="OrthoCamera" name="OrthoCamera">
      <optics><technique_common>
        <orthographic>
          <xmag>5</xmag><ymag>5</ymag>
          <znear>0.01</znear><zfar>500</zfar>
        </orthographic>
      </technique_common></optics>
    </camera>
  </library_cameras>
  <library_geometries>
    <geometry id="Mesh" name="Mesh">
      <mesh>
        <source id="pos"><float_array id="pos-arr" count="9">0 0 0 1 0 0 0.5 1 0</float_array>
          <technique_common><accessor source="#pos-arr" count="3" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common></source>
        <vertices id="verts"><input semantic="POSITION" source="#pos"/></vertices>
        <triangles count="1"><input semantic="VERTEX" source="#verts" offset="0"/>
          <p>0 1 2</p></triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="MeshNode" name="MeshNode" type="NODE">
        <instance_geometry url="#Mesh"/>
      </node>
      <node id="CamNode1" name="CamNode1" type="NODE">
        <translate>0 0 5</translate>
        <instance_camera url="#PerspCamera"/>
      </node>
      <node id="CamNode2" name="CamNode2" type="NODE">
        <translate>5 0 0</translate>
        <rotate>0 1 0 90</rotate>
        <instance_camera url="#OrthoCamera"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_dae_cameras.dae"), 'w') as f:
        f.write(dae)


def seed_collada_lights(outdir):
    """Collada scene with point, directional, spot, and ambient lights."""
    dae = """<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><created>2024-01-01</created><modified>2024-01-01</modified></asset>
  <library_lights>
    <light id="PointLight" name="PointLight">
      <technique_common>
        <point>
          <color>1 0.9 0.8</color>
          <constant_attenuation>1</constant_attenuation>
          <linear_attenuation>0.01</linear_attenuation>
          <quadratic_attenuation>0.001</quadratic_attenuation>
        </point>
      </technique_common>
    </light>
    <light id="DirLight" name="DirLight">
      <technique_common>
        <directional><color>1 1 1</color></directional>
      </technique_common>
    </light>
    <light id="SpotLight" name="SpotLight">
      <technique_common>
        <spot>
          <color>0 1 0.5</color>
          <constant_attenuation>1</constant_attenuation>
          <linear_attenuation>0</linear_attenuation>
          <quadratic_attenuation>0.01</quadratic_attenuation>
          <falloff_angle>45</falloff_angle>
          <falloff_exponent>2</falloff_exponent>
        </spot>
      </technique_common>
    </light>
    <light id="AmbLight" name="AmbLight">
      <technique_common>
        <ambient><color>0.2 0.2 0.3</color></ambient>
      </technique_common>
    </light>
  </library_lights>
  <library_geometries>
    <geometry id="Mesh" name="Mesh">
      <mesh>
        <source id="pos"><float_array id="pos-arr" count="9">0 0 0 1 0 0 0.5 1 0</float_array>
          <technique_common><accessor source="#pos-arr" count="3" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common></source>
        <vertices id="verts"><input semantic="POSITION" source="#pos"/></vertices>
        <triangles count="1"><input semantic="VERTEX" source="#verts" offset="0"/><p>0 1 2</p></triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="MeshNode" type="NODE"><instance_geometry url="#Mesh"/></node>
      <node id="PtLightNode" type="NODE">
        <translate>2 3 2</translate>
        <instance_light url="#PointLight"/>
      </node>
      <node id="DirLightNode" type="NODE">
        <rotate>1 0 0 -45</rotate>
        <instance_light url="#DirLight"/>
      </node>
      <node id="SpotLightNode" type="NODE">
        <translate>0 5 0</translate>
        <rotate>1 0 0 -90</rotate>
        <instance_light url="#SpotLight"/>
      </node>
      <node id="AmbLightNode" type="NODE">
        <instance_light url="#AmbLight"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_dae_lights.dae"), 'w') as f:
        f.write(dae)


def seed_collada_skinned(outdir):
    """Collada scene with a skinned mesh and 2-bone skeleton."""
    dae = """<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><created>2024-01-01</created><modified>2024-01-01</modified></asset>
  <library_geometries>
    <geometry id="SkinMesh" name="SkinMesh">
      <mesh>
        <source id="pos">
          <float_array id="pos-arr" count="12">-0.5 0 0 0.5 0 0 -0.5 2 0 0.5 2 0</float_array>
          <technique_common><accessor source="#pos-arr" count="4" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common>
        </source>
        <source id="norm">
          <float_array id="norm-arr" count="12">0 0 1 0 0 1 0 0 1 0 0 1</float_array>
          <technique_common><accessor source="#norm-arr" count="4" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common>
        </source>
        <vertices id="verts">
          <input semantic="POSITION" source="#pos"/>
          <input semantic="NORMAL" source="#norm"/>
        </vertices>
        <triangles count="2">
          <input semantic="VERTEX" source="#verts" offset="0"/>
          <p>0 1 2 1 3 2</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_controllers>
    <controller id="SkinCtrl" name="SkinCtrl">
      <skin source="#SkinMesh">
        <bind_shape_matrix>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</bind_shape_matrix>
        <source id="joints">
          <Name_array id="joints-arr" count="2">Bone0 Bone1</Name_array>
          <technique_common><accessor source="#joints-arr" count="2" stride="1">
            <param name="JOINT" type="name"/>
          </accessor></technique_common>
        </source>
        <source id="ibm">
          <float_array id="ibm-arr" count="32">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 1 0 0 0 0 1 0 0 0 0 1 0 0 -1 0 1</float_array>
          <technique_common><accessor source="#ibm-arr" count="2" stride="16">
            <param name="TRANSFORM" type="float4x4"/>
          </accessor></technique_common>
        </source>
        <source id="weights">
          <float_array id="weights-arr" count="4">1 0 0.2 0.8</float_array>
          <technique_common><accessor source="#weights-arr" count="4" stride="1">
            <param name="WEIGHT" type="float"/>
          </accessor></technique_common>
        </source>
        <joints>
          <input semantic="JOINT" source="#joints"/>
          <input semantic="INV_BIND_MATRIX" source="#ibm"/>
        </joints>
        <vertex_weights count="4">
          <input semantic="JOINT" source="#joints" offset="0"/>
          <input semantic="WEIGHT" source="#weights" offset="1"/>
          <vcount>1 1 2 2</vcount>
          <v>0 0 0 0 0 2 1 3 0 2 1 3</v>
        </vertex_weights>
      </skin>
    </controller>
  </library_controllers>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="Armature" name="Armature" type="NODE">
        <node id="Bone0" name="Bone0" sid="Bone0" type="JOINT">
          <matrix sid="transform">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>
          <node id="Bone1" name="Bone1" sid="Bone1" type="JOINT">
            <matrix sid="transform">1 0 0 0 0 1 0 1 0 0 1 0 0 0 0 1</matrix>
          </node>
        </node>
      </node>
      <node id="MeshNode" name="MeshNode" type="NODE">
        <instance_controller url="#SkinCtrl">
          <skeleton>#Bone0</skeleton>
        </instance_controller>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_dae_skinned.dae"), 'w') as f:
        f.write(dae)


def seed_collada_animation(outdir):
    """Collada scene with node animation (translation + rotation channels)."""
    dae = """<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><created>2024-01-01</created><modified>2024-01-01</modified></asset>
  <library_geometries>
    <geometry id="Mesh" name="Mesh">
      <mesh>
        <source id="pos"><float_array id="pos-arr" count="9">0 0 0 1 0 0 0.5 1 0</float_array>
          <technique_common><accessor source="#pos-arr" count="3" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common></source>
        <vertices id="verts"><input semantic="POSITION" source="#pos"/></vertices>
        <triangles count="1"><input semantic="VERTEX" source="#verts" offset="0"/><p>0 1 2</p></triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_animations>
    <animation id="TransAnim" name="TransAnim">
      <source id="trans-input">
        <float_array id="trans-input-arr" count="3">0 0.5 1</float_array>
        <technique_common><accessor source="#trans-input-arr" count="3" stride="1">
          <param name="TIME" type="float"/>
        </accessor></technique_common>
      </source>
      <source id="trans-output">
        <float_array id="trans-output-arr" count="9">0 0 0 1 2 0 0 0 0</float_array>
        <technique_common><accessor source="#trans-output-arr" count="3" stride="3">
          <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
        </accessor></technique_common>
      </source>
      <source id="trans-interp">
        <Name_array id="trans-interp-arr" count="3">LINEAR LINEAR LINEAR</Name_array>
        <technique_common><accessor source="#trans-interp-arr" count="3" stride="1">
          <param name="INTERPOLATION" type="name"/>
        </accessor></technique_common>
      </source>
      <sampler id="trans-sampler">
        <input semantic="INPUT" source="#trans-input"/>
        <input semantic="OUTPUT" source="#trans-output"/>
        <input semantic="INTERPOLATION" source="#trans-interp"/>
      </sampler>
      <channel source="#trans-sampler" target="AnimNode/translate"/>
    </animation>
    <animation id="RotAnim" name="RotAnim">
      <source id="rot-input">
        <float_array id="rot-input-arr" count="3">0 0.5 1</float_array>
        <technique_common><accessor source="#rot-input-arr" count="3" stride="1">
          <param name="TIME" type="float"/>
        </accessor></technique_common>
      </source>
      <source id="rot-output">
        <float_array id="rot-output-arr" count="12">0 0 0 1 0 0.383 0 0.924 0 0 0 1</float_array>
        <technique_common><accessor source="#rot-output-arr" count="3" stride="4">
          <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/><param name="W" type="float"/>
        </accessor></technique_common>
      </source>
      <source id="rot-interp">
        <Name_array id="rot-interp-arr" count="3">LINEAR LINEAR LINEAR</Name_array>
        <technique_common><accessor source="#rot-interp-arr" count="3" stride="1">
          <param name="INTERPOLATION" type="name"/>
        </accessor></technique_common>
      </source>
      <sampler id="rot-sampler">
        <input semantic="INPUT" source="#rot-input"/>
        <input semantic="OUTPUT" source="#rot-output"/>
        <input semantic="INTERPOLATION" source="#rot-interp"/>
      </sampler>
      <channel source="#rot-sampler" target="AnimNode/rotate"/>
    </animation>
  </library_animations>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="AnimNode" name="AnimNode" type="NODE">
        <translate sid="translate">0 0 0</translate>
        <rotate sid="rotate">0 0 0 1</rotate>
        <instance_geometry url="#Mesh"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_dae_animation.dae"), 'w') as f:
        f.write(dae)


def seed_collada_materials(outdir):
    """Collada scene with different shading models (phong, blinn, lambert, constant)."""
    dae = """<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><created>2024-01-01</created><modified>2024-01-01</modified></asset>
  <library_effects>
    <effect id="PhongFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <emission><color>0.1 0.1 0.1 1</color></emission>
            <ambient><color>0.2 0.2 0.2 1</color></ambient>
            <diffuse><color>0.8 0.2 0.2 1</color></diffuse>
            <specular><color>1 1 1 1</color></specular>
            <shininess><float>50</float></shininess>
            <reflective><color>0.5 0.5 0.5 1</color></reflective>
            <reflectivity><float>0.3</float></reflectivity>
            <transparent opaque="A_ONE"><color>1 1 1 1</color></transparent>
            <transparency><float>1</float></transparency>
            <index_of_refraction><float>1.5</float></index_of_refraction>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="BlinnFX">
      <profile_COMMON>
        <technique sid="common">
          <blinn>
            <diffuse><color>0.2 0.8 0.2 1</color></diffuse>
            <specular><color>1 1 1 1</color></specular>
            <shininess><float>25</float></shininess>
          </blinn>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="LambertFX">
      <profile_COMMON>
        <technique sid="common">
          <lambert>
            <diffuse><color>0.2 0.2 0.8 1</color></diffuse>
            <ambient><color>0.1 0.1 0.1 1</color></ambient>
          </lambert>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="ConstantFX">
      <profile_COMMON>
        <technique sid="common">
          <constant>
            <emission><color>0.8 0.8 0 1</color></emission>
          </constant>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="PhongMat" name="PhongMat"><instance_effect url="#PhongFX"/></material>
    <material id="BlinnMat" name="BlinnMat"><instance_effect url="#BlinnFX"/></material>
    <material id="LambertMat" name="LambertMat"><instance_effect url="#LambertFX"/></material>
    <material id="ConstantMat" name="ConstantMat"><instance_effect url="#ConstantFX"/></material>
  </library_materials>
  <library_geometries>
    <geometry id="Mesh1" name="Mesh1">
      <mesh>
        <source id="pos1"><float_array id="pos1-arr" count="9">0 0 0 1 0 0 0.5 1 0</float_array>
          <technique_common><accessor source="#pos1-arr" count="3" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common></source>
        <vertices id="v1"><input semantic="POSITION" source="#pos1"/></vertices>
        <triangles count="1" material="mat"><input semantic="VERTEX" source="#v1" offset="0"/><p>0 1 2</p></triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="N1" type="NODE">
        <instance_geometry url="#Mesh1">
          <bind_material><technique_common>
            <instance_material symbol="mat" target="#PhongMat"/>
          </technique_common></bind_material>
        </instance_geometry>
      </node>
      <node id="N2" type="NODE">
        <translate>2 0 0</translate>
        <instance_geometry url="#Mesh1">
          <bind_material><technique_common>
            <instance_material symbol="mat" target="#BlinnMat"/>
          </technique_common></bind_material>
        </instance_geometry>
      </node>
      <node id="N3" type="NODE">
        <translate>4 0 0</translate>
        <instance_geometry url="#Mesh1">
          <bind_material><technique_common>
            <instance_material symbol="mat" target="#LambertMat"/>
          </technique_common></bind_material>
        </instance_geometry>
      </node>
      <node id="N4" type="NODE">
        <translate>6 0 0</translate>
        <instance_geometry url="#Mesh1">
          <bind_material><technique_common>
            <instance_material symbol="mat" target="#ConstantMat"/>
          </technique_common></bind_material>
        </instance_geometry>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_dae_materials.dae"), 'w') as f:
        f.write(dae)


def seed_collada_full(outdir):
    """Full Collada scene: cameras + lights + skinned mesh + animation."""
    dae = """<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><created>2024-01-01</created><modified>2024-01-01</modified></asset>
  <library_cameras>
    <camera id="Cam1" name="Cam1">
      <optics><technique_common>
        <perspective><yfov>45</yfov><znear>0.1</znear><zfar>100</zfar></perspective>
      </technique_common></optics>
    </camera>
  </library_cameras>
  <library_lights>
    <light id="Light1" name="Light1">
      <technique_common><point><color>1 1 1</color><constant_attenuation>1</constant_attenuation></point></technique_common>
    </light>
    <light id="Light2" name="Light2">
      <technique_common><spot><color>1 0 0</color><falloff_angle>30</falloff_angle></spot></technique_common>
    </light>
  </library_lights>
  <library_effects>
    <effect id="MatFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse><color>0.8 0.3 0.3 1</color></diffuse>
            <specular><color>1 1 1 1</color></specular>
            <shininess><float>30</float></shininess>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="Mat1" name="Mat1"><instance_effect url="#MatFX"/></material>
  </library_materials>
  <library_geometries>
    <geometry id="Mesh" name="Mesh">
      <mesh>
        <source id="pos">
          <float_array id="pos-arr" count="12">-0.5 0 0 0.5 0 0 -0.5 2 0 0.5 2 0</float_array>
          <technique_common><accessor source="#pos-arr" count="4" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common>
        </source>
        <source id="norm">
          <float_array id="norm-arr" count="12">0 0 1 0 0 1 0 0 1 0 0 1</float_array>
          <technique_common><accessor source="#norm-arr" count="4" stride="3">
            <param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/>
          </accessor></technique_common>
        </source>
        <vertices id="verts">
          <input semantic="POSITION" source="#pos"/>
          <input semantic="NORMAL" source="#norm"/>
        </vertices>
        <triangles count="2" material="mat">
          <input semantic="VERTEX" source="#verts" offset="0"/>
          <p>0 1 2 1 3 2</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_controllers>
    <controller id="SkinCtrl">
      <skin source="#Mesh">
        <bind_shape_matrix>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</bind_shape_matrix>
        <source id="jnames">
          <Name_array id="jn-arr" count="2">Bone0 Bone1</Name_array>
          <technique_common><accessor source="#jn-arr" count="2" stride="1"><param name="JOINT" type="name"/></accessor></technique_common>
        </source>
        <source id="ibm">
          <float_array id="ibm-arr" count="32">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 1 0 0 0 0 1 0 0 0 0 1 0 0 -1 0 1</float_array>
          <technique_common><accessor source="#ibm-arr" count="2" stride="16"><param name="TRANSFORM" type="float4x4"/></accessor></technique_common>
        </source>
        <source id="wts">
          <float_array id="wts-arr" count="3">1 0.3 0.7</float_array>
          <technique_common><accessor source="#wts-arr" count="3" stride="1"><param name="WEIGHT" type="float"/></accessor></technique_common>
        </source>
        <joints>
          <input semantic="JOINT" source="#jnames"/>
          <input semantic="INV_BIND_MATRIX" source="#ibm"/>
        </joints>
        <vertex_weights count="4">
          <input semantic="JOINT" source="#jnames" offset="0"/>
          <input semantic="WEIGHT" source="#wts" offset="1"/>
          <vcount>1 1 2 2</vcount>
          <v>0 0 0 0 0 1 1 2 0 1 1 2</v>
        </vertex_weights>
      </skin>
    </controller>
  </library_controllers>
  <library_animations>
    <animation id="Anim1">
      <source id="a-in">
        <float_array id="a-in-arr" count="3">0 0.5 1</float_array>
        <technique_common><accessor source="#a-in-arr" count="3" stride="1"><param name="TIME" type="float"/></accessor></technique_common>
      </source>
      <source id="a-out">
        <float_array id="a-out-arr" count="48">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0.866 0.5 0 0 -0.5 0.866 0 0 0 0 1 0 0 0 0 1 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</float_array>
        <technique_common><accessor source="#a-out-arr" count="3" stride="16"><param name="TRANSFORM" type="float4x4"/></accessor></technique_common>
      </source>
      <source id="a-interp">
        <Name_array id="a-int-arr" count="3">LINEAR LINEAR LINEAR</Name_array>
        <technique_common><accessor source="#a-int-arr" count="3" stride="1"><param name="INTERPOLATION" type="name"/></accessor></technique_common>
      </source>
      <sampler id="a-samp">
        <input semantic="INPUT" source="#a-in"/>
        <input semantic="OUTPUT" source="#a-out"/>
        <input semantic="INTERPOLATION" source="#a-interp"/>
      </sampler>
      <channel source="#a-samp" target="Bone1/transform"/>
    </animation>
  </library_animations>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="Armature" type="NODE">
        <node id="Bone0" sid="Bone0" type="JOINT">
          <matrix sid="transform">1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>
          <node id="Bone1" sid="Bone1" type="JOINT">
            <matrix sid="transform">1 0 0 0 0 1 0 1 0 0 1 0 0 0 0 1</matrix>
          </node>
        </node>
      </node>
      <node id="MeshNode" type="NODE">
        <instance_controller url="#SkinCtrl">
          <skeleton>#Bone0</skeleton>
          <bind_material><technique_common>
            <instance_material symbol="mat" target="#Mat1"/>
          </technique_common></bind_material>
        </instance_controller>
      </node>
      <node id="CamNode" type="NODE">
        <translate>0 1 5</translate>
        <instance_camera url="#Cam1"/>
      </node>
      <node id="L1Node" type="NODE">
        <translate>3 3 3</translate>
        <instance_light url="#Light1"/>
      </node>
      <node id="L2Node" type="NODE">
        <translate>0 5 0</translate>
        <instance_light url="#Light2"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene><instance_visual_scene url="#Scene"/></scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_dae_full.dae"), 'w') as f:
        f.write(dae)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "collada_seeds"
    os.makedirs(outdir, exist_ok=True)

    generators = [
        seed_collada_camera,
        seed_collada_lights,
        seed_collada_skinned,
        seed_collada_animation,
        seed_collada_materials,
        seed_collada_full,
    ]

    for gen in generators:
        gen(outdir)
        print(f"Generated: {gen.__name__}")

    print(f"\n{len(generators)} seeds written to {outdir}/")


if __name__ == "__main__":
    main()
