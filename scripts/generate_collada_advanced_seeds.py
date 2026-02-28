#!/usr/bin/env python3
"""Generate advanced Collada (.dae) seed files targeting uncovered code paths.

Targets uncovered paths in ColladaParser.cpp and ColladaExporter.cpp:
- All light types with full attenuation + FCOLLADA/OpenCOLLADA extensions
- Perspective + orthographic cameras with all parameters
- Skin controllers with bind_shape_matrix, joints, vertex_weights
- Morph controllers with NORMALIZED method and MORPH_TARGET/MORPH_WEIGHT
- Effects with phong/lambert/blinn, newparam sampler2D/surface, bump maps,
  transparent with RGB_ZERO/A_ZERO opaque modes, wireframe/faceted/double_sided
- Animations with LINEAR/STEP/BEZIER interpolation and IN_TANGENT/OUT_TANGENT
- Vertex colors, multiple UV sets, lines primitives, multiple material bindings
"""

import os
import sys


def seed_lights_cameras(outdir):
    """Collada with all 4 light types (point/spot/directional/ambient) and
    both camera types (perspective/orthographic) with full parameters.

    Targets:
    - ColladaParser.cpp ReadLight: point, spot, directional, ambient types,
      color, constant/linear/quadratic_attenuation, falloff_angle/exponent,
      outer_cone, penumbra_angle, intensity, falloff, hotspot_beam, decay_falloff
    - ColladaParser.cpp ReadCamera: orthographic flag, xfov/yfov, xmag/ymag,
      aspect_ratio, znear, zfar
    - ColladaExporter.cpp WritePointLight, WriteSpotLight, WriteDirectionalLight,
      WriteAmbientLight, WriteCamera
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01</created>
    <modified>2024-01-01</modified>
  </asset>
  <library_cameras>
    <camera id="PerspCam" name="PerspCam">
      <optics>
        <technique_common>
          <perspective>
            <xfov>60</xfov>
            <yfov>45</yfov>
            <aspect_ratio>1.333</aspect_ratio>
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
            <xmag>10</xmag>
            <ymag>7.5</ymag>
            <aspect_ratio>1.333</aspect_ratio>
            <znear>0.01</znear>
            <zfar>500</zfar>
          </orthographic>
        </technique_common>
      </optics>
    </camera>
  </library_cameras>
  <library_lights>
    <light id="PointLight1" name="PointLight1">
      <technique_common>
        <point>
          <color>1 0.9 0.8</color>
          <constant_attenuation>1.0</constant_attenuation>
          <linear_attenuation>0.045</linear_attenuation>
          <quadratic_attenuation>0.0075</quadratic_attenuation>
        </point>
      </technique_common>
      <extra>
        <technique profile="FCOLLADA">
          <intensity>1.5</intensity>
        </technique>
      </extra>
    </light>
    <light id="SpotLight1" name="SpotLight1">
      <technique_common>
        <spot>
          <color>0.2 1.0 0.5</color>
          <constant_attenuation>1.0</constant_attenuation>
          <linear_attenuation>0.0</linear_attenuation>
          <quadratic_attenuation>0.01</quadratic_attenuation>
          <falloff_angle>30</falloff_angle>
          <falloff_exponent>2.5</falloff_exponent>
        </spot>
      </technique_common>
      <extra>
        <technique profile="FCOLLADA">
          <outer_cone>60</outer_cone>
          <penumbra_angle>10</penumbra_angle>
          <falloff>45</falloff>
          <hotspot_beam>25</hotspot_beam>
        </technique>
        <technique profile="OpenCOLLADA">
          <decay_falloff>50</decay_falloff>
        </technique>
      </extra>
    </light>
    <light id="DirLight1" name="DirLight1">
      <technique_common>
        <directional>
          <color>1 1 0.95</color>
        </directional>
      </technique_common>
    </light>
    <light id="AmbLight1" name="AmbLight1">
      <technique_common>
        <ambient>
          <color>0.15 0.15 0.2</color>
        </ambient>
      </technique_common>
    </light>
  </library_lights>
  <library_geometries>
    <geometry id="BoxGeo" name="BoxGeo">
      <mesh>
        <source id="box-pos">
          <float_array id="box-pos-arr" count="24">-1 -1 -1 1 -1 -1 1 1 -1 -1 1 -1 -1 -1 1 1 -1 1 1 1 1 -1 1 1</float_array>
          <technique_common>
            <accessor source="#box-pos-arr" count="8" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="box-verts">
          <input semantic="POSITION" source="#box-pos"/>
        </vertices>
        <triangles count="4">
          <input semantic="VERTEX" source="#box-verts" offset="0"/>
          <p>0 1 2 0 2 3 4 5 6 4 6 7</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="MeshNode" name="MeshNode" type="NODE">
        <instance_geometry url="#BoxGeo"/>
      </node>
      <node id="PerspCamNode" name="PerspCamNode" type="NODE">
        <translate>0 0 10</translate>
        <instance_camera url="#PerspCam"/>
      </node>
      <node id="OrthoCamNode" name="OrthoCamNode" type="NODE">
        <translate>10 0 0</translate>
        <rotate>0 1 0 90</rotate>
        <instance_camera url="#OrthoCam"/>
      </node>
      <node id="PointLightNode" name="PointLightNode" type="NODE">
        <translate>3 4 3</translate>
        <instance_light url="#PointLight1"/>
      </node>
      <node id="SpotLightNode" name="SpotLightNode" type="NODE">
        <translate>0 6 0</translate>
        <rotate>1 0 0 -90</rotate>
        <instance_light url="#SpotLight1"/>
      </node>
      <node id="DirLightNode" name="DirLightNode" type="NODE">
        <rotate>1 0 0 -45</rotate>
        <instance_light url="#DirLight1"/>
      </node>
      <node id="AmbLightNode" name="AmbLightNode" type="NODE">
        <instance_light url="#AmbLight1"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_lights_cameras.dae"), 'w') as f:
        f.write(dae)


def seed_skin_controller(outdir):
    """Collada with skin controller: bind_shape_matrix, joints with
    JOINT + INV_BIND_MATRIX, vertex_weights with vcount + v arrays.

    Targets:
    - ColladaParser.cpp ReadController: skin source, bind_shape_matrix parsing
    - ReadControllerJoints: JOINT + INV_BIND_MATRIX semantics
    - ReadControllerWeights: count attribute, input JOINT/WEIGHT offsets
    - ReadControllerWeightsVCount: vcount parsing
    - ReadControllerWeightsJoint2verts: v index pair parsing
    - ReadSource/ReadDataArray: Name_array + float_array
    - ReadAccessor: float4x4 type for IBMs
    - Visual scene: instance_controller + skeleton reference
    """
    # 6 vertices forming a simple arm-like shape
    # 3 bones: Root, Upper, Lower
    # Identity bind shape matrix
    # 3 inverse bind matrices (identity, translate -1 on Y, translate -2 on Y)
    # Weights: first 2 verts -> bone0 100%, next 2 -> bone0 50% bone1 50%, last 2 -> bone1 50% bone2 50%
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01</created>
    <modified>2024-01-01</modified>
  </asset>
  <library_geometries>
    <geometry id="ArmMesh" name="ArmMesh">
      <mesh>
        <source id="arm-pos">
          <float_array id="arm-pos-arr" count="18">\
-0.5 0 0  0.5 0 0  -0.5 1 0  0.5 1 0  -0.5 2 0  0.5 2 0</float_array>
          <technique_common>
            <accessor source="#arm-pos-arr" count="6" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="arm-norm">
          <float_array id="arm-norm-arr" count="18">\
0 0 1  0 0 1  0 0 1  0 0 1  0 0 1  0 0 1</float_array>
          <technique_common>
            <accessor source="#arm-norm-arr" count="6" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="arm-verts">
          <input semantic="POSITION" source="#arm-pos"/>
          <input semantic="NORMAL" source="#arm-norm"/>
        </vertices>
        <triangles count="4">
          <input semantic="VERTEX" source="#arm-verts" offset="0"/>
          <p>0 1 2  1 3 2  2 3 4  3 5 4</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_controllers>
    <controller id="ArmSkinCtrl" name="ArmSkinCtrl">
      <skin source="#ArmMesh">
        <bind_shape_matrix>\
1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1</bind_shape_matrix>
        <source id="skin-joints">
          <Name_array id="skin-joints-arr" count="3">Root Upper Lower</Name_array>
          <technique_common>
            <accessor source="#skin-joints-arr" count="3" stride="1">
              <param name="JOINT" type="name"/>
            </accessor>
          </technique_common>
        </source>
        <source id="skin-ibm">
          <float_array id="skin-ibm-arr" count="48">\
1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1  \
1 0 0 0  0 1 0 -1  0 0 1 0  0 0 0 1  \
1 0 0 0  0 1 0 -2  0 0 1 0  0 0 0 1</float_array>
          <technique_common>
            <accessor source="#skin-ibm-arr" count="3" stride="16">
              <param name="TRANSFORM" type="float4x4"/>
            </accessor>
          </technique_common>
        </source>
        <source id="skin-weights">
          <float_array id="skin-weights-arr" count="5">1.0 0.5 0.5 0.3 0.7</float_array>
          <technique_common>
            <accessor source="#skin-weights-arr" count="5" stride="1">
              <param name="WEIGHT" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <joints>
          <input semantic="JOINT" source="#skin-joints"/>
          <input semantic="INV_BIND_MATRIX" source="#skin-ibm"/>
        </joints>
        <vertex_weights count="6">
          <input semantic="JOINT" source="#skin-joints" offset="0"/>
          <input semantic="WEIGHT" source="#skin-weights" offset="1"/>
          <vcount>1 1 2 2 2 2</vcount>
          <v>\
0 0  \
0 0  \
0 1  1 2  \
0 1  1 2  \
1 3  2 4  \
1 3  2 4</v>
        </vertex_weights>
      </skin>
    </controller>
  </library_controllers>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="Armature" name="Armature" type="NODE">
        <matrix sid="transform">1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1</matrix>
        <node id="Root" name="Root" sid="Root" type="JOINT">
          <matrix sid="transform">1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1</matrix>
          <node id="Upper" name="Upper" sid="Upper" type="JOINT">
            <matrix sid="transform">1 0 0 0  0 1 0 1  0 0 1 0  0 0 0 1</matrix>
            <node id="Lower" name="Lower" sid="Lower" type="JOINT">
              <matrix sid="transform">1 0 0 0  0 1 0 1  0 0 1 0  0 0 0 1</matrix>
            </node>
          </node>
        </node>
      </node>
      <node id="ArmMeshNode" name="ArmMeshNode" type="NODE">
        <instance_controller url="#ArmSkinCtrl">
          <skeleton>#Root</skeleton>
        </instance_controller>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_skin_controller.dae"), 'w') as f:
        f.write(dae)


def seed_morph_controller(outdir):
    """Collada with morph controller: method=NORMALIZED, morph targets,
    MORPH_TARGET and MORPH_WEIGHT inputs in <targets>.

    Targets:
    - ColladaParser.cpp ReadController: morph type, source attribute,
      method attribute (NORMALIZED default, RELATIVE branch)
    - ReadController targets block: MORPH_TARGET + MORPH_WEIGHT semantics
    - ReadSource for IDREF_array (morph target references)
    - ColladaLoader morph weight channel resolution
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01</created>
    <modified>2024-01-01</modified>
  </asset>
  <library_geometries>
    <geometry id="BaseMesh" name="BaseMesh">
      <mesh>
        <source id="base-pos">
          <float_array id="base-pos-arr" count="12">\
0 0 0  1 0 0  0.5 1 0  0.5 0.5 0.5</float_array>
          <technique_common>
            <accessor source="#base-pos-arr" count="4" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="base-verts">
          <input semantic="POSITION" source="#base-pos"/>
        </vertices>
        <triangles count="2">
          <input semantic="VERTEX" source="#base-verts" offset="0"/>
          <p>0 1 2  0 2 3</p>
        </triangles>
      </mesh>
    </geometry>
    <geometry id="MorphTarget1" name="MorphTarget1">
      <mesh>
        <source id="mt1-pos">
          <float_array id="mt1-pos-arr" count="12">\
0 0 0  1 0 0  0.5 1.5 0  0.5 0.75 0.8</float_array>
          <technique_common>
            <accessor source="#mt1-pos-arr" count="4" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="mt1-verts">
          <input semantic="POSITION" source="#mt1-pos"/>
        </vertices>
        <triangles count="2">
          <input semantic="VERTEX" source="#mt1-verts" offset="0"/>
          <p>0 1 2  0 2 3</p>
        </triangles>
      </mesh>
    </geometry>
    <geometry id="MorphTarget2" name="MorphTarget2">
      <mesh>
        <source id="mt2-pos">
          <float_array id="mt2-pos-arr" count="12">\
-0.2 0 0  1.2 0 0  0.5 0.8 0  0.5 0.4 1.0</float_array>
          <technique_common>
            <accessor source="#mt2-pos-arr" count="4" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="mt2-verts">
          <input semantic="POSITION" source="#mt2-pos"/>
        </vertices>
        <triangles count="2">
          <input semantic="VERTEX" source="#mt2-verts" offset="0"/>
          <p>0 1 2  0 2 3</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_controllers>
    <controller id="MorphCtrl" name="MorphCtrl">
      <morph source="#BaseMesh" method="NORMALIZED">
        <source id="morph-targets">
          <IDREF_array id="morph-targets-arr" count="2">MorphTarget1 MorphTarget2</IDREF_array>
          <technique_common>
            <accessor source="#morph-targets-arr" count="2" stride="1">
              <param name="MORPH_TARGET" type="IDREF"/>
            </accessor>
          </technique_common>
        </source>
        <source id="morph-weights">
          <float_array id="morph-weights-arr" count="2">0.4 0.6</float_array>
          <technique_common>
            <accessor source="#morph-weights-arr" count="2" stride="1">
              <param name="MORPH_WEIGHT" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <targets>
          <input semantic="MORPH_TARGET" source="#morph-targets"/>
          <input semantic="MORPH_WEIGHT" source="#morph-weights"/>
        </targets>
      </morph>
    </controller>
  </library_controllers>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="MorphNode" name="MorphNode" type="NODE">
        <instance_controller url="#MorphCtrl"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_morph_controller.dae"), 'w') as f:
        f.write(dae)


def seed_effects_advanced(outdir):
    """Collada with advanced effects: phong (all properties), lambert, blinn,
    newparam with sampler2D/surface, bump map via extra/technique,
    transparent with RGB_ZERO and A_ZERO opaque modes, double_sided,
    wireframe, faceted.

    Targets:
    - ColladaParser.cpp ReadEffectProfileCommon: phong/lambert/blinn shade types,
      emission/ambient/diffuse/specular/reflective/transparent/shininess/
      reflectivity/transparency/index_of_refraction, double_sided, wireframe, faceted
    - ReadEffectColor: color parsing, texture reference, opaque attribute (RGB_ZERO,
      A_ZERO, RGB_ONE, A_ONE), mRGBTransparency, mInvertTransparency
    - ReadEffectFloat: float child parsing
    - ReadEffectParam: surface + sampler2D (1.4 format with <source> child),
      sampler2D (1.5 format with <instance_image>)
    - ReadEffectColor technique profile MAYA/MAX3D/OKINO -> ReadSamplerProperties:
      wrapU/V, mirrorU/V, repeatU/V, offsetU/V, rotateUV, blend_mode, weighting,
      mix_with_previous_layer, amount
    - bump -> ReadEffectColor for mTexBump
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01</created>
    <modified>2024-01-01</modified>
  </asset>
  <library_images>
    <image id="DiffTex" name="DiffTex">
      <init_from>texture.png</init_from>
    </image>
    <image id="BumpTex" name="BumpTex">
      <init_from>bump.png</init_from>
    </image>
  </library_images>
  <library_effects>
    <effect id="PhongAdvFX">
      <profile_COMMON>
        <newparam sid="DiffSurface">
          <surface type="2D">
            <init_from>DiffTex</init_from>
          </surface>
        </newparam>
        <newparam sid="DiffSampler">
          <sampler2D>
            <source>DiffSurface</source>
          </sampler2D>
        </newparam>
        <newparam sid="BumpSurface">
          <surface type="2D">
            <init_from>BumpTex</init_from>
          </surface>
        </newparam>
        <newparam sid="BumpSampler">
          <sampler2D>
            <source>BumpSurface</source>
          </sampler2D>
        </newparam>
        <technique sid="common">
          <phong>
            <emission>
              <color>0.05 0.05 0.05 1.0</color>
            </emission>
            <ambient>
              <color>0.15 0.15 0.15 1.0</color>
            </ambient>
            <diffuse>
              <texture texture="DiffSampler" texcoord="UVMap">
                <extra>
                  <technique profile="MAYA">
                    <wrapU>1</wrapU>
                    <wrapV>1</wrapV>
                    <mirrorU>0</mirrorU>
                    <mirrorV>0</mirrorV>
                    <repeatU>2.0</repeatU>
                    <repeatV>2.0</repeatV>
                    <offsetU>0.1</offsetU>
                    <offsetV>0.2</offsetV>
                    <rotateUV>45.0</rotateUV>
                    <blend_mode>MULTIPLY</blend_mode>
                  </technique>
                  <technique profile="OKINO">
                    <weighting>0.8</weighting>
                    <mix_with_previous_layer>0.5</mix_with_previous_layer>
                  </technique>
                  <technique profile="MAX3D">
                    <amount>0.9</amount>
                  </technique>
                </extra>
              </texture>
            </diffuse>
            <specular>
              <color>1.0 1.0 1.0 1.0</color>
            </specular>
            <shininess>
              <float>64.0</float>
            </shininess>
            <reflective>
              <color>0.3 0.3 0.3 1.0</color>
            </reflective>
            <reflectivity>
              <float>0.25</float>
            </reflectivity>
            <transparent opaque="RGB_ZERO">
              <color>0.0 0.0 0.0 1.0</color>
            </transparent>
            <transparency>
              <float>0.9</float>
            </transparency>
            <index_of_refraction>
              <float>1.52</float>
            </index_of_refraction>
          </phong>
        </technique>
        <extra>
          <technique>
            <bump>
              <texture texture="BumpSampler" texcoord="UVMap"/>
            </bump>
          </technique>
        </extra>
        <extra>
          <technique profile="GOOGLEEARTH">
            <double_sided>1</double_sided>
          </technique>
          <technique profile="MAX3D">
            <wireframe>0</wireframe>
            <faceted>0</faceted>
          </technique>
        </extra>
      </profile_COMMON>
    </effect>
    <effect id="LambertFX">
      <profile_COMMON>
        <technique sid="common">
          <lambert>
            <emission>
              <color>0.0 0.0 0.0 1.0</color>
            </emission>
            <ambient>
              <color>0.1 0.1 0.1 1.0</color>
            </ambient>
            <diffuse>
              <color>0.6 0.3 0.1 1.0</color>
            </diffuse>
            <transparent opaque="A_ZERO">
              <color>1.0 1.0 1.0 0.8</color>
            </transparent>
            <transparency>
              <float>0.8</float>
            </transparency>
          </lambert>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="BlinnFX">
      <profile_COMMON>
        <technique sid="common">
          <blinn>
            <emission>
              <color>0.02 0.02 0.02 1.0</color>
            </emission>
            <ambient>
              <color>0.2 0.2 0.2 1.0</color>
            </ambient>
            <diffuse>
              <color>0.1 0.5 0.8 1.0</color>
            </diffuse>
            <specular>
              <color>0.9 0.9 0.9 1.0</color>
            </specular>
            <shininess>
              <float>32.0</float>
            </shininess>
            <reflective>
              <color>0.1 0.1 0.1 1.0</color>
            </reflective>
            <reflectivity>
              <float>0.1</float>
            </reflectivity>
            <transparent opaque="A_ONE">
              <color>1.0 1.0 1.0 1.0</color>
            </transparent>
            <transparency>
              <float>1.0</float>
            </transparency>
            <index_of_refraction>
              <float>1.33</float>
            </index_of_refraction>
          </blinn>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="PhongAdvMat" name="PhongAdvMat">
      <instance_effect url="#PhongAdvFX"/>
    </material>
    <material id="LambertMat" name="LambertMat">
      <instance_effect url="#LambertFX"/>
    </material>
    <material id="BlinnMat" name="BlinnMat">
      <instance_effect url="#BlinnFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="Plane" name="Plane">
      <mesh>
        <source id="plane-pos">
          <float_array id="plane-pos-arr" count="12">\
-1 0 -1  1 0 -1  1 0 1  -1 0 1</float_array>
          <technique_common>
            <accessor source="#plane-pos-arr" count="4" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="plane-uv">
          <float_array id="plane-uv-arr" count="8">0 0  1 0  1 1  0 1</float_array>
          <technique_common>
            <accessor source="#plane-uv-arr" count="4" stride="2">
              <param name="S" type="float"/>
              <param name="T" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="plane-verts">
          <input semantic="POSITION" source="#plane-pos"/>
        </vertices>
        <triangles count="2" material="phong_group">
          <input semantic="VERTEX" source="#plane-verts" offset="0"/>
          <input semantic="TEXCOORD" source="#plane-uv" offset="1" set="0"/>
          <p>0 0  1 1  2 2  0 0  2 2  3 3</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="PlaneNode" name="PlaneNode" type="NODE">
        <instance_geometry url="#Plane">
          <bind_material>
            <technique_common>
              <instance_material symbol="phong_group" target="#PhongAdvMat">
                <bind_vertex_input semantic="UVMap" input_semantic="2" input_set="0"/>
              </instance_material>
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
    with open(os.path.join(outdir, "seed_effects_advanced.dae"), 'w') as f:
        f.write(dae)


def seed_animation_interp(outdir):
    """Collada with animations using LINEAR, STEP, and BEZIER interpolation,
    including IN_TANGENT and OUT_TANGENT sources.

    Targets:
    - ColladaParser.cpp ReadAnimationSampler: INPUT, OUTPUT, INTERPOLATION,
      IN_TANGENT, OUT_TANGENT semantic parsing
    - ReadAnimation: sampler + channel pairing, source_name with '#' prefix,
      target attribute parsing
    - ReadSource/ReadDataArray: Name_array for interpolation types
    - ColladaExporter.cpp WriteAnimationLibrary: animation source/sampler/channel
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01</created>
    <modified>2024-01-01</modified>
  </asset>
  <library_geometries>
    <geometry id="Cube" name="Cube">
      <mesh>
        <source id="cube-pos">
          <float_array id="cube-pos-arr" count="24">\
-1 -1 -1  1 -1 -1  1 1 -1  -1 1 -1  -1 -1 1  1 -1 1  1 1 1  -1 1 1</float_array>
          <technique_common>
            <accessor source="#cube-pos-arr" count="8" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="cube-verts">
          <input semantic="POSITION" source="#cube-pos"/>
        </vertices>
        <triangles count="4">
          <input semantic="VERTEX" source="#cube-verts" offset="0"/>
          <p>0 1 2  0 2 3  4 5 6  4 6 7</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_animations>
    <animation id="LinearTranslateAnim" name="LinearTranslateAnim">
      <source id="lt-input">
        <float_array id="lt-input-arr" count="4">0.0 0.5 1.0 1.5</float_array>
        <technique_common>
          <accessor source="#lt-input-arr" count="4" stride="1">
            <param name="TIME" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="lt-output">
        <float_array id="lt-output-arr" count="12">\
0 0 0  2 0 0  2 3 0  0 0 0</float_array>
        <technique_common>
          <accessor source="#lt-output-arr" count="4" stride="3">
            <param name="X" type="float"/>
            <param name="Y" type="float"/>
            <param name="Z" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="lt-interp">
        <Name_array id="lt-interp-arr" count="4">LINEAR LINEAR LINEAR LINEAR</Name_array>
        <technique_common>
          <accessor source="#lt-interp-arr" count="4" stride="1">
            <param name="INTERPOLATION" type="name"/>
          </accessor>
        </technique_common>
      </source>
      <sampler id="lt-sampler">
        <input semantic="INPUT" source="#lt-input"/>
        <input semantic="OUTPUT" source="#lt-output"/>
        <input semantic="INTERPOLATION" source="#lt-interp"/>
      </sampler>
      <channel source="#lt-sampler" target="AnimCube/translate"/>
    </animation>
    <animation id="StepVisibilityAnim" name="StepVisibilityAnim">
      <source id="sv-input">
        <float_array id="sv-input-arr" count="3">0.0 0.75 1.5</float_array>
        <technique_common>
          <accessor source="#sv-input-arr" count="3" stride="1">
            <param name="TIME" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="sv-output">
        <float_array id="sv-output-arr" count="3">1.0 0.0 1.0</float_array>
        <technique_common>
          <accessor source="#sv-output-arr" count="3" stride="1">
            <param name="X" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="sv-interp">
        <Name_array id="sv-interp-arr" count="3">STEP STEP STEP</Name_array>
        <technique_common>
          <accessor source="#sv-interp-arr" count="3" stride="1">
            <param name="INTERPOLATION" type="name"/>
          </accessor>
        </technique_common>
      </source>
      <sampler id="sv-sampler">
        <input semantic="INPUT" source="#sv-input"/>
        <input semantic="OUTPUT" source="#sv-output"/>
        <input semantic="INTERPOLATION" source="#sv-interp"/>
      </sampler>
      <channel source="#sv-sampler" target="AnimCube/visibility"/>
    </animation>
    <animation id="BezierRotateAnim" name="BezierRotateAnim">
      <source id="br-input">
        <float_array id="br-input-arr" count="3">0.0 0.75 1.5</float_array>
        <technique_common>
          <accessor source="#br-input-arr" count="3" stride="1">
            <param name="TIME" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="br-output">
        <float_array id="br-output-arr" count="48">\
1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1  \
0.707 -0.707 0 0  0.707 0.707 0 0  0 0 1 0  0 0 0 1  \
1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1</float_array>
        <technique_common>
          <accessor source="#br-output-arr" count="3" stride="16">
            <param name="TRANSFORM" type="float4x4"/>
          </accessor>
        </technique_common>
      </source>
      <source id="br-interp">
        <Name_array id="br-interp-arr" count="3">BEZIER BEZIER BEZIER</Name_array>
        <technique_common>
          <accessor source="#br-interp-arr" count="3" stride="1">
            <param name="INTERPOLATION" type="name"/>
          </accessor>
        </technique_common>
      </source>
      <source id="br-intangent">
        <float_array id="br-intangent-arr" count="6">\
-0.1 0.0  0.55 0.0  1.3 0.0</float_array>
        <technique_common>
          <accessor source="#br-intangent-arr" count="3" stride="2">
            <param name="X" type="float"/>
            <param name="Y" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <source id="br-outtangent">
        <float_array id="br-outtangent-arr" count="6">\
0.1 0.0  0.95 0.0  1.6 0.0</float_array>
        <technique_common>
          <accessor source="#br-outtangent-arr" count="3" stride="2">
            <param name="X" type="float"/>
            <param name="Y" type="float"/>
          </accessor>
        </technique_common>
      </source>
      <sampler id="br-sampler">
        <input semantic="INPUT" source="#br-input"/>
        <input semantic="OUTPUT" source="#br-output"/>
        <input semantic="INTERPOLATION" source="#br-interp"/>
        <input semantic="IN_TANGENT" source="#br-intangent"/>
        <input semantic="OUT_TANGENT" source="#br-outtangent"/>
      </sampler>
      <channel source="#br-sampler" target="AnimCube/matrix"/>
    </animation>
    <animation id="SubAnimParent" name="SubAnimParent">
      <animation id="SubAnimChild" name="SubAnimChild">
        <source id="sub-input">
          <float_array id="sub-input-arr" count="2">0.0 1.0</float_array>
          <technique_common>
            <accessor source="#sub-input-arr" count="2" stride="1">
              <param name="TIME" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="sub-output">
          <float_array id="sub-output-arr" count="6">0 0 0  0 2 0</float_array>
          <technique_common>
            <accessor source="#sub-output-arr" count="2" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="sub-interp">
          <Name_array id="sub-interp-arr" count="2">LINEAR LINEAR</Name_array>
          <technique_common>
            <accessor source="#sub-interp-arr" count="2" stride="1">
              <param name="INTERPOLATION" type="name"/>
            </accessor>
          </technique_common>
        </source>
        <sampler id="sub-sampler">
          <input semantic="INPUT" source="#sub-input"/>
          <input semantic="OUTPUT" source="#sub-output"/>
          <input semantic="INTERPOLATION" source="#sub-interp"/>
        </sampler>
        <channel source="#sub-sampler" target="AnimCube/translate"/>
      </animation>
    </animation>
  </library_animations>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="AnimCube" name="AnimCube" type="NODE">
        <translate sid="translate">0 0 0</translate>
        <rotate sid="rotate">0 0 1 0</rotate>
        <matrix sid="matrix">\
1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1</matrix>
        <instance_geometry url="#Cube"/>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>"""
    with open(os.path.join(outdir, "seed_animation_interp.dae"), 'w') as f:
        f.write(dae)


def seed_multimaterial_colors(outdir):
    """Collada with vertex colors, multiple UV sets, lines primitive,
    and multiple material bindings.

    Targets:
    - ColladaParser.cpp ExtractDataObjectFromChannel: IT_Color branch (set index),
      IT_Texcoord with different set indices, mNumUVComponents
    - ReadInputChannel: set attribute for TEXCOORD and COLOR
    - ReadIndexData: lines primitive type (Prim_Lines), multiple submeshes
    - ReadPrimitives: Prim_Lines case with numPoints=2
    - ReadNodeGeometry/bind_material: multiple instance_material entries
    - ColladaExporter: multi-material round-trip
    """
    dae = """\
<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <created>2024-01-01</created>
    <modified>2024-01-01</modified>
  </asset>
  <library_effects>
    <effect id="RedFX">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <diffuse><color>0.9 0.1 0.1 1.0</color></diffuse>
            <specular><color>1 1 1 1</color></specular>
            <shininess><float>30</float></shininess>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="BlueFX">
      <profile_COMMON>
        <technique sid="common">
          <lambert>
            <diffuse><color>0.1 0.1 0.9 1.0</color></diffuse>
          </lambert>
        </technique>
      </profile_COMMON>
    </effect>
    <effect id="WireFX">
      <profile_COMMON>
        <technique sid="common">
          <constant>
            <emission><color>1 1 0 1</color></emission>
          </constant>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="RedMat" name="RedMat">
      <instance_effect url="#RedFX"/>
    </material>
    <material id="BlueMat" name="BlueMat">
      <instance_effect url="#BlueFX"/>
    </material>
    <material id="WireMat" name="WireMat">
      <instance_effect url="#WireFX"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="ColorMesh" name="ColorMesh">
      <mesh>
        <source id="cm-pos">
          <float_array id="cm-pos-arr" count="18">\
0 0 0  2 0 0  2 2 0  0 2 0  1 3 0  1 -1 0</float_array>
          <technique_common>
            <accessor source="#cm-pos-arr" count="6" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="cm-norm">
          <float_array id="cm-norm-arr" count="18">\
0 0 1  0 0 1  0 0 1  0 0 1  0 0 1  0 0 1</float_array>
          <technique_common>
            <accessor source="#cm-norm-arr" count="6" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="cm-color0">
          <float_array id="cm-color0-arr" count="24">\
1 0 0 1  0 1 0 1  0 0 1 1  1 1 0 1  1 0 1 1  0 1 1 1</float_array>
          <technique_common>
            <accessor source="#cm-color0-arr" count="6" stride="4">
              <param name="R" type="float"/>
              <param name="G" type="float"/>
              <param name="B" type="float"/>
              <param name="A" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="cm-uv0">
          <float_array id="cm-uv0-arr" count="12">\
0 0  1 0  1 1  0 1  0.5 1.5  0.5 -0.5</float_array>
          <technique_common>
            <accessor source="#cm-uv0-arr" count="6" stride="2">
              <param name="S" type="float"/>
              <param name="T" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="cm-uv1">
          <float_array id="cm-uv1-arr" count="12">\
0 0  0.5 0  0.5 0.5  0 0.5  0.25 0.75  0.25 -0.25</float_array>
          <technique_common>
            <accessor source="#cm-uv1-arr" count="6" stride="2">
              <param name="S" type="float"/>
              <param name="T" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="cm-verts">
          <input semantic="POSITION" source="#cm-pos"/>
        </vertices>
        <triangles count="2" material="red_group">
          <input semantic="VERTEX" source="#cm-verts" offset="0"/>
          <input semantic="NORMAL" source="#cm-norm" offset="1"/>
          <input semantic="COLOR" source="#cm-color0" offset="2" set="0"/>
          <input semantic="TEXCOORD" source="#cm-uv0" offset="3" set="0"/>
          <input semantic="TEXCOORD" source="#cm-uv1" offset="4" set="1"/>
          <p>\
0 0 0 0 0  1 1 1 1 1  2 2 2 2 2  \
0 0 0 0 0  2 2 2 2 2  3 3 3 3 3</p>
        </triangles>
        <triangles count="1" material="blue_group">
          <input semantic="VERTEX" source="#cm-verts" offset="0"/>
          <input semantic="NORMAL" source="#cm-norm" offset="1"/>
          <input semantic="COLOR" source="#cm-color0" offset="2" set="0"/>
          <input semantic="TEXCOORD" source="#cm-uv0" offset="3" set="0"/>
          <p>2 2 2 2  3 3 3 3  4 4 4 4</p>
        </triangles>
        <lines count="2" material="wire_group">
          <input semantic="VERTEX" source="#cm-verts" offset="0"/>
          <input semantic="COLOR" source="#cm-color0" offset="1" set="0"/>
          <p>0 0  5 5  1 1  5 5</p>
        </lines>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="ColorMeshNode" name="ColorMeshNode" type="NODE">
        <instance_geometry url="#ColorMesh">
          <bind_material>
            <technique_common>
              <instance_material symbol="red_group" target="#RedMat">
                <bind_vertex_input semantic="UVMap0" input_semantic="2" input_set="0"/>
                <bind_vertex_input semantic="UVMap1" input_semantic="2" input_set="1"/>
              </instance_material>
              <instance_material symbol="blue_group" target="#BlueMat">
                <bind_vertex_input semantic="UVMap0" input_semantic="2" input_set="0"/>
              </instance_material>
              <instance_material symbol="wire_group" target="#WireMat"/>
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
    with open(os.path.join(outdir, "seed_multimaterial_colors.dae"), 'w') as f:
        f.write(dae)


def main():
    outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "test", "models", "Collada", "fuzz_seeds")
    os.makedirs(outdir, exist_ok=True)

    seed_lights_cameras(outdir)
    seed_skin_controller(outdir)
    seed_morph_controller(outdir)
    seed_effects_advanced(outdir)
    seed_animation_interp(outdir)
    seed_multimaterial_colors(outdir)

    print(f"Generated 6 advanced Collada seed files in {outdir}")
    for fname in sorted(os.listdir(outdir)):
        if fname.startswith("seed_") and fname.endswith(".dae"):
            fpath = os.path.join(outdir, fname)
            print(f"  {fname}: {os.path.getsize(fpath)} bytes")


if __name__ == "__main__":
    main()
