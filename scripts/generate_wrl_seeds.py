#!/usr/bin/env python3
"""
Generate diverse VRML 2.0 (.wrl) seed files for fuzzing the assimp VRML importer.

The assimp VRML importer uses a meshlab-derived parser that converts VRML97 to X3D XML,
which is then processed by the X3D importer. This script generates small seed files that
cover a wide range of VRML 2.0 features to maximize parser code coverage.

Output: test/models/WRL/fuzz_seeds/
"""

import os
import sys

HEADER = "#VRML V2.0 utf8\n"

SEEDS = {}

# 1. Basic shapes with Appearance
SEEDS["basic_box.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0.8 0.2 0.2
    }
  }
  geometry Box { size 2.0 3.0 1.5 }
}
"""

SEEDS["basic_sphere.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0.2 0.8 0.2
      specularColor 1 1 1
      shininess 0.9
    }
  }
  geometry Sphere { radius 1.5 }
}
"""

SEEDS["basic_cylinder.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0.2 0.2 0.8
    }
  }
  geometry Cylinder { height 3.0 radius 0.5 bottom TRUE top TRUE side TRUE }
}
"""

SEEDS["basic_cone.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0.8 0.8 0.2
    }
  }
  geometry Cone { height 2.0 bottomRadius 1.0 bottom TRUE side TRUE }
}
"""

# 2. IndexedFaceSet with coordIndex and Coordinate
SEEDS["indexed_faceset.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { diffuseColor 0.6 0.6 0.6 }
  }
  geometry IndexedFaceSet {
    solid FALSE
    ccw TRUE
    convex TRUE
    creaseAngle 1.57
    coord Coordinate {
      point [
        0 0 0, 1 0 0, 1 1 0, 0 1 0,
        0 0 1, 1 0 1, 1 1 1, 0 1 1
      ]
    }
    coordIndex [
      0 1 2 3 -1,
      4 5 6 7 -1,
      0 1 5 4 -1,
      2 3 7 6 -1,
      0 3 7 4 -1,
      1 2 6 5 -1
    ]
    color Color {
      color [ 1 0 0, 0 1 0, 0 0 1, 1 1 0, 1 0 1, 0 1 1 ]
    }
    colorIndex [ 0, 1, 2, 3, 4, 5 ]
    colorPerVertex FALSE
  }
}
"""

SEEDS["indexed_faceset_normals.wrl"] = HEADER + """
Shape {
  geometry IndexedFaceSet {
    coord Coordinate {
      point [ 0 0 0, 1 0 0, 0.5 1 0, 0 0 1, 1 0 1, 0.5 1 1 ]
    }
    coordIndex [ 0 1 2 -1, 3 4 5 -1, 0 1 4 3 -1 ]
    normal Normal {
      vector [ 0 0 -1, 0 0 1, 0 -1 0 ]
    }
    normalIndex [ 0, 1, 2 ]
    normalPerVertex FALSE
  }
}
"""

SEEDS["indexed_faceset_texcoords.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { diffuseColor 1 1 1 }
    texture ImageTexture { url "test.png" }
  }
  geometry IndexedFaceSet {
    coord Coordinate {
      point [ 0 0 0, 1 0 0, 1 1 0, 0 1 0 ]
    }
    coordIndex [ 0 1 2 3 -1 ]
    texCoord TextureCoordinate {
      point [ 0 0, 1 0, 1 1, 0 1 ]
    }
    texCoordIndex [ 0 1 2 3 -1 ]
  }
}
"""

# 3. IndexedLineSet with coordIndex
SEEDS["indexed_lineset.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { emissiveColor 0 1 0 }
  }
  geometry IndexedLineSet {
    coord Coordinate {
      point [ 0 0 0, 1 0 0, 1 1 0, 0 1 0, 0.5 1.5 0 ]
    }
    coordIndex [ 0 1 2 3 0 -1, 3 4 2 -1 ]
    color Color {
      color [ 1 0 0, 0 1 0, 0 0 1, 1 1 0, 1 0 1 ]
    }
    colorPerVertex TRUE
    colorIndex [ 0 1 2 3 0 -1, 3 4 2 -1 ]
  }
}
"""

# 4. PointSet with Coordinate
SEEDS["pointset.wrl"] = HEADER + """
Shape {
  geometry PointSet {
    coord Coordinate {
      point [
        0 0 0, 1 0 0, 0 1 0, 0 0 1,
        -1 0 0, 0 -1 0, 0 0 -1,
        0.5 0.5 0.5, -0.5 -0.5 -0.5
      ]
    }
    color Color {
      color [
        1 0 0, 0 1 0, 0 0 1, 1 1 0,
        1 0 1, 0 1 1, 1 1 1,
        0.5 0.5 0.5, 0.2 0.2 0.2
      ]
    }
  }
}
"""

# 5. ElevationGrid
SEEDS["elevation_grid.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { diffuseColor 0.4 0.7 0.3 }
  }
  geometry ElevationGrid {
    xDimension 4
    zDimension 4
    xSpacing 1.0
    zSpacing 1.0
    height [
      0.0 0.5 0.3 0.0,
      0.2 1.0 0.8 0.1,
      0.1 0.7 1.2 0.3,
      0.0 0.2 0.4 0.0
    ]
    solid FALSE
    ccw TRUE
    creaseAngle 0.78
    colorPerVertex TRUE
    color Color {
      color [
        0.2 0.8 0.2, 0.3 0.7 0.2, 0.3 0.6 0.3, 0.2 0.8 0.2,
        0.3 0.9 0.3, 0.5 0.5 0.2, 0.4 0.4 0.3, 0.2 0.7 0.2,
        0.2 0.7 0.3, 0.4 0.5 0.2, 0.5 0.3 0.2, 0.3 0.6 0.3,
        0.2 0.8 0.2, 0.3 0.7 0.3, 0.3 0.6 0.2, 0.2 0.8 0.2
      ]
    }
  }
}
"""

# 6. Extrusion
SEEDS["extrusion.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { diffuseColor 0.7 0.3 0.1 }
  }
  geometry Extrusion {
    crossSection [
      1 0, 0.7 0.7, 0 1, -0.7 0.7,
      -1 0, -0.7 -0.7, 0 -1, 0.7 -0.7, 1 0
    ]
    spine [
      0 0 0, 0 1 0, 0 2 0, 0 3 0, 0 4 0
    ]
    scale [ 1 1, 0.8 0.8, 0.6 0.6, 0.4 0.4, 0.2 0.2 ]
    orientation [
      0 1 0 0, 0 1 0 0.5, 0 1 0 1.0, 0 1 0 1.5, 0 1 0 2.0
    ]
    beginCap TRUE
    endCap TRUE
    solid TRUE
    ccw TRUE
    convex TRUE
    creaseAngle 1.0
  }
}
"""

# 7. Transform with translation, rotation, scale
SEEDS["transform_nested.wrl"] = HEADER + """
Transform {
  translation 1.0 2.0 3.0
  rotation 0 1 0 1.5708
  scale 2.0 2.0 2.0
  scaleOrientation 0 0 1 0.0
  center 0 0 0
  children [
    Shape {
      geometry Box { size 1 1 1 }
      appearance Appearance {
        material Material { diffuseColor 1 0 0 }
      }
    }
    Transform {
      translation 3 0 0
      rotation 1 0 0 0.7854
      children [
        Shape {
          geometry Sphere { radius 0.5 }
          appearance Appearance {
            material Material { diffuseColor 0 1 0 }
          }
        }
      ]
    }
  ]
}
"""

# 8. DEF/USE for instancing
SEEDS["def_use.wrl"] = HEADER + """
Transform {
  translation -2 0 0
  children [
    DEF MyShape Shape {
      appearance DEF MyAppearance Appearance {
        material DEF MyMaterial Material {
          diffuseColor 0.8 0.4 0.1
          specularColor 1 1 1
          shininess 0.5
        }
      }
      geometry DEF MyBox Box { size 1 1 1 }
    }
  ]
}
Transform {
  translation 2 0 0
  children [
    USE MyShape
  ]
}
Transform {
  translation 0 2 0
  children [
    Shape {
      appearance USE MyAppearance
      geometry Sphere { radius 0.5 }
    }
  ]
}
"""

# 9. Group and Switch nodes
SEEDS["group_switch.wrl"] = HEADER + """
Group {
  children [
    Transform {
      translation -2 0 0
      children [
        Shape {
          geometry Box { size 1 1 1 }
          appearance Appearance {
            material Material { diffuseColor 1 0 0 }
          }
        }
      ]
    }
    Transform {
      translation 0 0 0
      children [
        Shape {
          geometry Sphere { radius 0.5 }
          appearance Appearance {
            material Material { diffuseColor 0 1 0 }
          }
        }
      ]
    }
  ]
}
Switch {
  whichChoice 0
  choice [
    Shape {
      geometry Cone { height 2 bottomRadius 1 }
      appearance Appearance {
        material Material { diffuseColor 0 0 1 }
      }
    }
    Shape {
      geometry Cylinder { height 2 radius 0.5 }
      appearance Appearance {
        material Material { diffuseColor 1 1 0 }
      }
    }
  ]
}
"""

# 10. DirectionalLight, PointLight, SpotLight
SEEDS["lights.wrl"] = HEADER + """
Group {
  children [
    DirectionalLight {
      direction 0 -1 -1
      color 1 1 1
      intensity 0.8
      ambientIntensity 0.2
      on TRUE
    }
    PointLight {
      location 3 3 3
      color 1 0.5 0
      intensity 1.0
      ambientIntensity 0.1
      attenuation 1 0 0
      radius 10
      on TRUE
    }
    SpotLight {
      location 0 5 0
      direction 0 -1 0
      color 0 0 1
      intensity 1.0
      ambientIntensity 0.0
      attenuation 1 0 0
      beamWidth 0.5
      cutOffAngle 0.78
      radius 20
      on TRUE
    }
    Shape {
      geometry Sphere { radius 1 }
      appearance Appearance {
        material Material {
          diffuseColor 0.8 0.8 0.8
          specularColor 1 1 1
          shininess 0.9
        }
      }
    }
  ]
}
"""

# 11. Material with all properties
SEEDS["material_full.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material {
      diffuseColor 0.4 0.6 0.8
      specularColor 1.0 1.0 1.0
      emissiveColor 0.05 0.05 0.1
      ambientIntensity 0.3
      shininess 0.7
      transparency 0.2
    }
  }
  geometry Sphere { radius 1.0 }
}
"""

# 12. ImageTexture with TextureTransform
SEEDS["texture_transform.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { diffuseColor 1 1 1 }
    texture ImageTexture {
      url [ "texture.png" "fallback.jpg" ]
      repeatS TRUE
      repeatT TRUE
    }
    textureTransform TextureTransform {
      center 0.5 0.5
      rotation 0.785
      scale 2.0 2.0
      translation 0.0 0.0
    }
  }
  geometry Box { size 2 2 2 }
}
"""

SEEDS["multi_texture.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { diffuseColor 1 1 1 }
    texture MovieTexture {
      url "video.mpg"
      loop TRUE
      speed 1.0
      startTime 0
      stopTime -1
    }
  }
  geometry Box { size 1 1 1 }
}
"""

# 13. NavigationInfo and Viewpoint
SEEDS["navigation_viewpoint.wrl"] = HEADER + """
NavigationInfo {
  type [ "EXAMINE" "WALK" "FLY" "ANY" ]
  speed 1.0
  headlight TRUE
  avatarSize [ 0.25 1.75 0.75 ]
  visibilityLimit 0.0
}
Viewpoint {
  position 0 1.6 10
  orientation 1 0 0 -0.1
  fieldOfView 0.785
  description "Main View"
  jump TRUE
}
DEF TopView Viewpoint {
  position 0 10 0
  orientation 1 0 0 -1.5708
  description "Top View"
}
Background {
  skyColor [ 0.2 0.2 0.5, 0.5 0.5 0.8, 0.8 0.8 1.0 ]
  skyAngle [ 1.309, 1.571 ]
  groundColor [ 0.1 0.3 0.1, 0.2 0.5 0.2 ]
  groundAngle [ 1.309 ]
}
"""

# 14. Inline (reference external WRL)
SEEDS["inline_node.wrl"] = HEADER + """
Group {
  children [
    Transform {
      translation 0 0 0
      children [
        Inline {
          url [ "other_model.wrl" "fallback.wrl" ]
        }
      ]
    }
    Transform {
      translation 5 0 0
      children [
        Inline {
          url "another_model.wrl"
        }
      ]
    }
  ]
}
"""

# 15. PROTO definition (user-defined prototypes)
SEEDS["proto_simple.wrl"] = HEADER + """
PROTO ColoredBox [
  field SFColor boxColor 0.8 0.2 0.2
  field SFVec3f boxSize 1.0 1.0 1.0
] {
  Shape {
    appearance Appearance {
      material Material { diffuseColor IS boxColor }
    }
    geometry Box { size IS boxSize }
  }
}
ColoredBox { boxColor 0 1 0 boxSize 2 1 3 }
Transform {
  translation 3 0 0
  children [
    ColoredBox { boxColor 0 0 1 }
  ]
}
"""

SEEDS["proto_complex.wrl"] = HEADER + """
PROTO Chair [
  field SFColor seatColor 0.5 0.3 0.1
  field SFFloat legHeight 0.8
] {
  Group {
    children [
      Transform {
        translation 0 0 0
        children [
          Shape {
            appearance Appearance {
              material Material { diffuseColor IS seatColor }
            }
            geometry Box { size 1.0 0.1 1.0 }
          }
        ]
      }
      Transform {
        translation -0.4 -0.4 -0.4
        children [
          Shape {
            geometry Cylinder { height IS legHeight radius 0.05 }
          }
        ]
      }
    ]
  }
}
Chair { seatColor 0.7 0.4 0.2 legHeight 1.0 }
"""

SEEDS["externproto.wrl"] = HEADER + """
EXTERNPROTO Tree [
  field SFFloat height
  field SFColor trunkColor
] "trees.wrl#Tree"
Tree { height 5.0 trunkColor 0.4 0.2 0.1 }
"""

# 16. ROUTE for animation/events
SEEDS["route_basic.wrl"] = HEADER + """
DEF TS TimeSensor {
  cycleInterval 5.0
  loop TRUE
}
DEF PI PositionInterpolator {
  key [ 0 0.5 1 ]
  keyValue [ 0 0 0, 2 2 0, 0 0 0 ]
}
DEF T Transform {
  children [
    Shape {
      geometry Box { size 1 1 1 }
      appearance Appearance {
        material Material { diffuseColor 1 0.5 0 }
      }
    }
  ]
}
ROUTE TS.fraction_changed TO PI.set_fraction
ROUTE PI.value_changed TO T.set_translation
"""

# 17. TimeSensor + OrientationInterpolator + PositionInterpolator
SEEDS["interpolators.wrl"] = HEADER + """
DEF Clock TimeSensor {
  cycleInterval 10.0
  loop TRUE
  startTime 0
  stopTime -1
  enabled TRUE
}
DEF OI OrientationInterpolator {
  key [ 0 0.25 0.5 0.75 1 ]
  keyValue [
    0 1 0 0,
    0 1 0 1.5708,
    0 1 0 3.1416,
    0 1 0 4.7124,
    0 1 0 6.2832
  ]
}
DEF PI PositionInterpolator {
  key [ 0 0.25 0.5 0.75 1 ]
  keyValue [
    0 0 0,
    2 1 0,
    0 2 0,
    -2 1 0,
    0 0 0
  ]
}
DEF Mover Transform {
  children [
    Shape {
      geometry Cone { height 1.5 bottomRadius 0.5 }
      appearance Appearance {
        material Material { diffuseColor 0.9 0.1 0.1 }
      }
    }
  ]
}
ROUTE Clock.fraction_changed TO OI.set_fraction
ROUTE Clock.fraction_changed TO PI.set_fraction
ROUTE OI.value_changed TO Mover.set_rotation
ROUTE PI.value_changed TO Mover.set_translation
"""

# 18. ColorInterpolator
SEEDS["color_interpolator.wrl"] = HEADER + """
DEF Timer TimeSensor {
  cycleInterval 4.0
  loop TRUE
}
DEF CI ColorInterpolator {
  key [ 0 0.25 0.5 0.75 1 ]
  keyValue [
    1 0 0,
    0 1 0,
    0 0 1,
    1 1 0,
    1 0 0
  ]
}
DEF Mat Material {
  diffuseColor 1 0 0
}
Shape {
  appearance Appearance {
    material USE Mat
  }
  geometry Sphere { radius 1.0 }
}
ROUTE Timer.fraction_changed TO CI.set_fraction
ROUTE CI.value_changed TO Mat.set_diffuseColor
"""

SEEDS["scalar_interpolator.wrl"] = HEADER + """
DEF Timer TimeSensor {
  cycleInterval 3.0
  loop TRUE
}
DEF SI ScalarInterpolator {
  key [ 0 0.5 1 ]
  keyValue [ 0.0 1.0 0.0 ]
}
DEF Mat Material {
  transparency 0
}
Shape {
  appearance Appearance { material USE Mat }
  geometry Box { size 2 2 2 }
}
ROUTE Timer.fraction_changed TO SI.set_fraction
ROUTE SI.value_changed TO Mat.set_transparency
"""

# 19. Text with FontStyle
SEEDS["text_fontstyle.wrl"] = HEADER + """
Transform {
  translation 0 0 0
  children [
    Shape {
      geometry Text {
        string [ "Hello" "VRML" "World" ]
        fontStyle FontStyle {
          family [ "SERIF" ]
          style "BOLD"
          size 1.5
          spacing 1.0
          justify [ "MIDDLE" "MIDDLE" ]
          horizontal TRUE
          leftToRight TRUE
          topToBottom TRUE
          language "en"
        }
        maxExtent 0.0
        length [ 0 0 0 ]
      }
      appearance Appearance {
        material Material {
          diffuseColor 1 1 0
          emissiveColor 0.2 0.2 0
        }
      }
    }
  ]
}
"""

SEEDS["text_multiline.wrl"] = HEADER + """
Shape {
  geometry Text {
    string [ "Line1" "Line2" ]
    fontStyle FontStyle {
      family [ "SANS" ]
      style "ITALIC"
      size 0.8
      justify [ "BEGIN" "FIRST" ]
    }
  }
  appearance Appearance {
    material Material { diffuseColor 1 1 1 }
  }
}
"""

# 20. NurbsCurve / NurbsSurface
SEEDS["nurbs_curve.wrl"] = HEADER + """
Shape {
  geometry NurbsCurve {
    order 4
    knot [ 0 0 0 0 1 1 1 1 ]
    controlPoint Coordinate {
      point [
        -2 0 0, -1 2 0, 1 2 0, 2 0 0
      ]
    }
    weight [ 1 1 1 1 ]
  }
  appearance Appearance {
    material Material { emissiveColor 1 1 0 }
  }
}
"""

SEEDS["nurbs_surface.wrl"] = HEADER + """
Shape {
  geometry NurbsSurface {
    uOrder 3
    vOrder 3
    uDimension 3
    vDimension 3
    uKnot [ 0 0 0 1 1 1 ]
    vKnot [ 0 0 0 1 1 1 ]
    controlPoint Coordinate {
      point [
        -1 0 -1, 0 0 -1, 1 0 -1,
        -1 1  0, 0 2  0, 1 1  0,
        -1 0  1, 0 0  1, 1 0  1
      ]
    }
    weight [ 1 1 1 1 1 1 1 1 1 ]
    solid FALSE
  }
  appearance Appearance {
    material Material { diffuseColor 0.6 0.6 0.9 }
  }
}
"""

# Additional coverage seeds for parser edge cases

# WorldInfo node
SEEDS["worldinfo.wrl"] = HEADER + """
WorldInfo {
  title "Test World"
  info [ "Created for fuzzing" "VRML 2.0" ]
}
Shape {
  geometry Box { size 1 1 1 }
}
"""

# Anchor node
SEEDS["anchor.wrl"] = HEADER + """
Anchor {
  url "http://example.com"
  description "Click to visit"
  parameter [ "target=_blank" ]
  children [
    Shape {
      geometry Sphere { radius 1 }
      appearance Appearance {
        material Material { diffuseColor 0 0.5 1 }
      }
    }
  ]
}
"""

# Billboard
SEEDS["billboard.wrl"] = HEADER + """
Billboard {
  axisOfRotation 0 1 0
  children [
    Shape {
      geometry Text {
        string [ "Billboard" ]
        fontStyle FontStyle { size 0.5 }
      }
      appearance Appearance {
        material Material { diffuseColor 1 1 1 }
      }
    }
  ]
}
"""

# Collision
SEEDS["collision.wrl"] = HEADER + """
Collision {
  collide TRUE
  children [
    Shape {
      geometry Box { size 2 2 2 }
      appearance Appearance {
        material Material { diffuseColor 0.5 0.5 0.5 transparency 0.3 }
      }
    }
  ]
}
"""

# LOD (Level of Detail)
SEEDS["lod.wrl"] = HEADER + """
LOD {
  range [ 10 50 ]
  level [
    Shape {
      geometry Sphere { radius 1 }
      appearance Appearance {
        material Material { diffuseColor 1 0 0 }
      }
    }
    Shape {
      geometry Box { size 2 2 2 }
      appearance Appearance {
        material Material { diffuseColor 0 1 0 }
      }
    }
    Shape {
      geometry Cone { height 2 bottomRadius 1 }
    }
  ]
}
"""

# Fog
SEEDS["fog.wrl"] = HEADER + """
Fog {
  color 0.5 0.5 0.5
  fogType "LINEAR"
  visibilityRange 50
}
Shape {
  geometry Sphere { radius 2 }
  appearance Appearance {
    material Material { diffuseColor 1 0.8 0.6 }
  }
}
"""

# TouchSensor, ProximitySensor, VisibilitySensor
SEEDS["sensors.wrl"] = HEADER + """
Group {
  children [
    DEF TS TouchSensor {}
    DEF PS ProximitySensor {
      center 0 0 0
      size 10 10 10
      enabled TRUE
    }
    DEF VS VisibilitySensor {
      center 0 0 0
      size 5 5 5
    }
    DEF PD PlaneSensor {
      minPosition -5 -5
      maxPosition 5 5
      enabled TRUE
      autoOffset TRUE
    }
    DEF CS CylinderSensor {
      minAngle 0
      maxAngle 6.28
      enabled TRUE
    }
    DEF SS SphereSensor {
      enabled TRUE
      autoOffset TRUE
    }
    Shape {
      geometry Box { size 1 1 1 }
      appearance Appearance {
        material Material { diffuseColor 0.5 0.8 0.5 }
      }
    }
  ]
}
"""

# Sound + AudioClip
SEEDS["sound.wrl"] = HEADER + """
Sound {
  source AudioClip {
    url "sound.wav"
    loop TRUE
    pitch 1.0
    startTime 0
    stopTime -1
    description "ambient sound"
  }
  location 0 1 0
  direction 0 0 1
  intensity 1.0
  maxBack 10
  maxFront 10
  minBack 1
  minFront 1
  priority 0.5
  spatialize TRUE
}
"""

# PixelTexture
SEEDS["pixel_texture.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    material Material { diffuseColor 1 1 1 }
    texture PixelTexture {
      image 2 2 3 0xFF0000 0x00FF00 0x0000FF 0xFFFF00
      repeatS TRUE
      repeatT TRUE
    }
  }
  geometry Box { size 2 2 2 }
}
"""

# CoordinateInterpolator + NormalInterpolator
SEEDS["coord_interp.wrl"] = HEADER + """
DEF T TimeSensor {
  cycleInterval 2.0
  loop TRUE
}
DEF CoordI CoordinateInterpolator {
  key [ 0 0.5 1 ]
  keyValue [
    0 0 0, 1 0 0, 0.5 1 0,
    0 0.5 0, 1 0.5 0, 0.5 1.5 0,
    0 0 0, 1 0 0, 0.5 1 0
  ]
}
DEF NormI NormalInterpolator {
  key [ 0 1 ]
  keyValue [
    0 0 1, 0 0 1, 0 0 1,
    0 1 0, 0 1 0, 0 1 0
  ]
}
ROUTE T.fraction_changed TO CoordI.set_fraction
"""

# Script node
SEEDS["script.wrl"] = HEADER + """
DEF Clk TimeSensor {
  cycleInterval 5.0
  loop TRUE
}
DEF S Script {
  eventIn SFFloat fraction
  eventOut SFVec3f position
  field SFFloat amplitude 3.0
  url "javascript:
    function fraction(val) {
      position = new SFVec3f(Math.sin(val*6.28)*amplitude, 0, 0);
    }
  "
}
DEF T Transform {
  children [
    Shape { geometry Sphere { radius 0.3 } }
  ]
}
ROUTE Clk.fraction_changed TO S.fraction
ROUTE S.position TO T.set_translation
"""

# Complex scene combining multiple features
SEEDS["complex_scene.wrl"] = HEADER + """
NavigationInfo { type [ "EXAMINE" ] headlight TRUE }
DEF MainView Viewpoint {
  position 0 2 10
  description "Main"
}
DirectionalLight { direction 0 -1 -0.5 intensity 0.8 }
DEF Root Transform {
  children [
    DEF Table Shape {
      appearance Appearance {
        material Material { diffuseColor 0.6 0.3 0.1 }
      }
      geometry Box { size 3 0.1 2 }
    }
    Transform {
      translation 0 0.5 0
      children [
        DEF Vase Shape {
          appearance Appearance {
            material Material {
              diffuseColor 0.8 0.8 0.9
              transparency 0.1
            }
          }
          geometry Cylinder { height 0.8 radius 0.2 }
        }
      ]
    }
    Transform {
      translation 1 0.1 0
      children [ USE Vase ]
    }
  ]
}
"""

# Multiple DEF/USE chains
SEEDS["def_use_chain.wrl"] = HEADER + """
DEF A Transform {
  translation -3 0 0
  children [
    DEF ShpA Shape {
      geometry Box { size 0.5 0.5 0.5 }
      appearance DEF AppA Appearance {
        material DEF MatA Material { diffuseColor 1 0 0 }
      }
    }
  ]
}
DEF B Transform {
  translation 0 0 0
  children [
    Shape {
      geometry Sphere { radius 0.3 }
      appearance USE AppA
    }
  ]
}
DEF C Transform {
  translation 3 0 0
  children [ USE ShpA ]
}
"""

# Empty and minimal cases (good for edge case testing)
SEEDS["empty_group.wrl"] = HEADER + """
Group {
  children [ ]
}
"""

SEEDS["minimal_shape.wrl"] = HEADER + """
Shape {
  geometry Box {}
}
"""

SEEDS["nested_transforms.wrl"] = HEADER + """
Transform {
  translation 1 0 0
  children [
    Transform {
      rotation 0 1 0 0.5
      children [
        Transform {
          scale 0.5 0.5 0.5
          children [
            Shape { geometry Sphere {} }
          ]
        }
      ]
    }
  ]
}
"""

# Header variations
SEEDS["header_comment.wrl"] = HEADER + """# This is a comment
# Another comment line
# Third comment line
Shape { geometry Box { size 1 1 1 } }
"""

# VRML with PROFILE/COMPONENT/META statements (X3D classic style accepted by parser)
SEEDS["profile_meta.wrl"] = HEADER + """
PROFILE Immersive
COMPONENT Geometry3D:2
META "title" "Test Scene"
META "creator" "fuzzer"
Shape {
  geometry Sphere { radius 1 }
}
"""

# Multiple shapes at root level
SEEDS["multi_root.wrl"] = HEADER + """
Shape {
  geometry Box { size 1 1 1 }
  appearance Appearance {
    material Material { diffuseColor 1 0 0 }
  }
}
Shape {
  geometry Sphere { radius 0.5 }
  appearance Appearance {
    material Material { diffuseColor 0 1 0 }
  }
}
Shape {
  geometry Cylinder { height 2 radius 0.3 }
  appearance Appearance {
    material Material { diffuseColor 0 0 1 }
  }
}
"""

# IndexedFaceSet with all optional fields
SEEDS["ifs_full.wrl"] = HEADER + """
Shape {
  geometry IndexedFaceSet {
    solid FALSE
    ccw TRUE
    convex TRUE
    creaseAngle 3.14
    colorPerVertex TRUE
    normalPerVertex TRUE
    coord Coordinate {
      point [ 0 0 0, 2 0 0, 2 2 0, 0 2 0 ]
    }
    coordIndex [ 0 1 2 3 -1 ]
    color Color {
      color [ 1 0 0, 0 1 0, 0 0 1, 1 1 0 ]
    }
    colorIndex [ 0 1 2 3 -1 ]
    normal Normal {
      vector [ 0 0 1, 0 0 1, 0 0 1, 0 0 1 ]
    }
    normalIndex [ 0 1 2 3 -1 ]
    texCoord TextureCoordinate {
      point [ 0 0, 1 0, 1 1, 0 1 ]
    }
    texCoordIndex [ 0 1 2 3 -1 ]
  }
  appearance Appearance {
    material Material { diffuseColor 1 1 1 }
  }
}
"""

# Coordinate and color data edge cases
SEEDS["large_indices.wrl"] = HEADER + """
Shape {
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        -1 -1 0, 1 -1 0, 1 1 0, -1 1 0,
        -1 -1 1, 1 -1 1, 1 1 1, -1 1 1
      ]
    }
    coordIndex [
      0 1 2 -1, 0 2 3 -1,
      4 5 6 -1, 4 6 7 -1,
      0 4 7 -1, 0 7 3 -1,
      1 5 6 -1, 1 6 2 -1,
      0 1 5 -1, 0 5 4 -1,
      3 2 6 -1, 3 6 7 -1
    ]
  }
}
"""

# Boolean field values
SEEDS["booleans.wrl"] = HEADER + """
Shape {
  geometry IndexedFaceSet {
    solid TRUE
    ccw FALSE
    convex TRUE
    colorPerVertex FALSE
    normalPerVertex FALSE
    coord Coordinate {
      point [ 0 0 0, 1 0 0, 0.5 1 0 ]
    }
    coordIndex [ 0 1 2 -1 ]
  }
}
"""

# Negative and zero values
SEEDS["negative_values.wrl"] = HEADER + """
Transform {
  translation -5.5 -3.2 -1.0
  rotation -1 0 0 -1.5708
  scale 0.001 0.001 0.001
  children [
    Shape {
      geometry Box { size 0.001 0.001 0.001 }
      appearance Appearance {
        material Material {
          diffuseColor 0 0 0
          transparency 0.0
          shininess 0.0
          ambientIntensity 0.0
        }
      }
    }
  ]
}
"""

# Multiple ROUTE statements
SEEDS["multi_route.wrl"] = HEADER + """
DEF T1 TimeSensor { cycleInterval 3 loop TRUE }
DEF T2 TimeSensor { cycleInterval 5 loop TRUE }
DEF PI1 PositionInterpolator {
  key [ 0 1 ]
  keyValue [ 0 0 0, 3 0 0 ]
}
DEF OI1 OrientationInterpolator {
  key [ 0 1 ]
  keyValue [ 0 1 0 0, 0 1 0 6.28 ]
}
DEF CI1 ColorInterpolator {
  key [ 0 0.5 1 ]
  keyValue [ 1 0 0, 0 1 0, 0 0 1 ]
}
DEF Obj Transform {
  children [
    Shape {
      geometry Box { size 1 1 1 }
      appearance Appearance {
        material DEF ObjMat Material { diffuseColor 1 0 0 }
      }
    }
  ]
}
ROUTE T1.fraction_changed TO PI1.set_fraction
ROUTE T1.fraction_changed TO OI1.set_fraction
ROUTE T2.fraction_changed TO CI1.set_fraction
ROUTE PI1.value_changed TO Obj.set_translation
ROUTE OI1.value_changed TO Obj.set_rotation
ROUTE CI1.value_changed TO ObjMat.set_diffuseColor
"""

# GeoCoordinate / Geo nodes (listed in x3dNode set)
SEEDS["geo_nodes.wrl"] = HEADER + """
GeoViewpoint {
  position "39.75 -104.99 1650"
  orientation 1 0 0 -1.2
  description "Denver View"
}
GeoLocation {
  geoCoords "39.75 -104.99 1600"
  children [
    Shape {
      geometry Box { size 100 100 100 }
      appearance Appearance {
        material Material { diffuseColor 0.8 0.2 0.2 }
      }
    }
  ]
}
"""

# Multiple URL strings in brackets
SEEDS["url_list.wrl"] = HEADER + """
Shape {
  appearance Appearance {
    texture ImageTexture {
      url [
        "tex1.png"
        "tex2.jpg"
        "tex3.gif"
        "http://example.com/tex4.png"
      ]
    }
  }
  geometry Sphere { radius 1 }
}
Inline {
  url [ "model1.wrl" "model2.wrl" "http://example.com/model3.wrl" ]
}
"""

# Deeply nested structure
SEEDS["deep_nesting.wrl"] = HEADER + """
Group { children [
  Transform { translation 0 0 0 children [
    Group { children [
      Transform { rotation 0 1 0 1.57 children [
        Switch { whichChoice 0 choice [
          Shape {
            geometry IndexedFaceSet {
              coord Coordinate {
                point [ 0 0 0, 1 0 0, 0.5 1 0 ]
              }
              coordIndex [ 0 1 2 -1 ]
            }
          }
        ] }
      ] }
    ] }
  ] }
] }
"""

# Comma-separated vs space-separated syntax
SEEDS["comma_syntax.wrl"] = HEADER + """
Shape {
  geometry IndexedFaceSet {
    coord Coordinate {
      point [
        0 0 0,
        1 0 0,
        1 1 0,
        0 1 0
      ]
    }
    coordIndex [ 0, 1, 2, 3, -1 ]
  }
}
"""

def main():
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test", "models", "WRL", "fuzz_seeds"
    )
    os.makedirs(output_dir, exist_ok=True)

    total_size = 0
    for name, content in sorted(SEEDS.items()):
        filepath = os.path.join(output_dir, name)
        # Strip leading/trailing whitespace but keep the content clean
        clean_content = content.strip() + "\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(clean_content)
        size = len(clean_content.encode("utf-8"))
        total_size += size
        print(f"  {name}: {size} bytes")

    print(f"\nGenerated {len(SEEDS)} seed files in {output_dir}")
    print(f"Total size: {total_size} bytes ({total_size / 1024:.1f} KB)")

    # Verify all files start with the correct header
    errors = 0
    for name in sorted(SEEDS.keys()):
        filepath = os.path.join(output_dir, name)
        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        if first_line != "#VRML V2.0 utf8":
            print(f"ERROR: {name} does not start with correct header: {first_line!r}")
            errors += 1

    if errors:
        print(f"\n{errors} file(s) have incorrect headers!")
        return 1

    # Check all files are under 2KB
    oversized = 0
    for name in sorted(SEEDS.keys()):
        filepath = os.path.join(output_dir, name)
        size = os.path.getsize(filepath)
        if size > 2048:
            print(f"WARNING: {name} is {size} bytes (over 2KB limit)")
            oversized += 1

    if oversized:
        print(f"\n{oversized} file(s) exceed 2KB limit!")
        return 1

    print("\nAll files validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
