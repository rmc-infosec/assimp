#!/usr/bin/env python3
"""Generate minimal valid X3D seed files for fuzzing.

Each seed exercises different X3D element types and attributes
to maximize coverage of the X3D importer code paths.

The seeds are derived from analysis of the actual importer source code:
  - X3DImporter.cpp (main parser, readChildNodes, readScene)
  - X3DImporter_Geometry3D.cpp (Box, Cone, Cylinder, ElevationGrid, Extrusion, IndexedFaceSet, Sphere)
  - X3DImporter_Rendering.cpp (Color, Coordinate, Normal, IndexedLineSet, LineSet, PointSet,
    IndexedTriangleFanSet, IndexedTriangleSet, IndexedTriangleStripSet,
    TriangleFanSet, TriangleSet, TriangleStripSet)
  - X3DImporter_Shape.cpp (Shape, Appearance, Material + all geometry dispatch)
  - X3DImporter_Group.cpp (Group, StaticGroup, Switch, Transform)
  - X3DImporter_Light.cpp (DirectionalLight, PointLight, SpotLight)
  - X3DImporter_Geometry2D.cpp (Arc2D, ArcClose2D, Circle2D, Disk2D, Polyline2D, Polypoint2D, Rectangle2D, TriangleSet2D)
"""

import os
import sys

XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'


def wrap_x3d(scene_content, profile="Interchange", version="3.3"):
    """Wrap scene content in the minimal X3D envelope."""
    return (
        XML_HEADER
        + f'<X3D profile="{profile}" version="{version}">\n'
        + "  <Scene>\n"
        + scene_content
        + "  </Scene>\n"
        + "</X3D>\n"
    )


def wrap_shape(geometry, appearance=None):
    """Wrap geometry in a Shape with optional Appearance."""
    parts = "    <Shape>\n"
    if appearance:
        parts += appearance
    parts += geometry
    parts += "    </Shape>\n"
    return parts


def default_appearance():
    """Simple red material appearance."""
    return '      <Appearance><Material diffuseColor="1 0 0"/></Appearance>\n'


# --------------------------------------------------------------------------
# Seed generators
# --------------------------------------------------------------------------

def seed_box():
    """Box primitive - exercises readBox() with size attribute."""
    geo = '      <Box size="2 2 2" solid="true"/>\n'
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_sphere():
    """Sphere primitive - exercises readSphere() with radius attribute."""
    geo = '      <Sphere radius="1.5" solid="true"/>\n'
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_cylinder():
    """Cylinder primitive - exercises readCylinder() with all attributes."""
    geo = '      <Cylinder radius="1" height="3" top="true" bottom="true" side="true" solid="true"/>\n'
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_cone():
    """Cone primitive - exercises readCone() with all attributes."""
    geo = '      <Cone bottomRadius="1.5" height="3" side="true" bottom="true" solid="true"/>\n'
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_indexed_faceset():
    """IndexedFaceSet - exercises readIndexedFaceSet() with Coordinate child.
    A simple quad (two triangles implicitly) forming a square."""
    geo = (
        '      <IndexedFaceSet coordIndex="0 1 2 3 -1" solid="true" ccw="true" convex="true" creaseAngle="0.5">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 1 1 0, 0 1 0"/>\n'
        '        <Normal vector="0 0 1, 0 0 1, 0 0 1, 0 0 1"/>\n'
        "      </IndexedFaceSet>\n"
    )
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_indexed_lineset():
    """IndexedLineSet - exercises readIndexedLineSet() with Coordinate and Color children."""
    geo = (
        '      <IndexedLineSet coordIndex="0 1 -1 2 3 -1" colorPerVertex="true">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 0 1 0, 1 1 0"/>\n'
        '        <Color color="1 0 0, 0 1 0, 0 0 1, 1 1 0"/>\n'
        "      </IndexedLineSet>\n"
    )
    return wrap_x3d(wrap_shape(geo))


def seed_pointset():
    """PointSet - exercises readPointSet() with Coordinate and ColorRGBA children."""
    geo = (
        "      <PointSet>\n"
        '        <Coordinate point="0 0 0, 1 0 0, 0 1 0, 0 0 1, 1 1 1"/>\n'
        '        <ColorRGBA color="1 0 0 1, 0 1 0 1, 0 0 1 1, 1 1 0 1, 0 1 1 1"/>\n'
        "      </PointSet>\n"
    )
    return wrap_x3d(wrap_shape(geo))


def seed_text():
    """Text node - skipped by the importer but exercises skipUnsupportedNode().
    Also tests that the Shape still processes correctly around a skipped geometry."""
    geo = (
        '      <Text string=\'"Hello" "World"\'>\n'
        '        <FontStyle justify=\'"MIDDLE" "MIDDLE"\'/>\n'
        "      </Text>\n"
    )
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_material():
    """Material/Appearance with all properties - exercises readMaterial() fully."""
    appearance = (
        "      <Appearance>\n"
        '        <Material ambientIntensity="0.5" diffuseColor="0.2 0.6 0.9"'
        ' emissiveColor="0.1 0.0 0.0" shininess="0.8"'
        ' specularColor="1 1 1" transparency="0.1"/>\n'
        "      </Appearance>\n"
    )
    geo = '      <Box size="1 1 1"/>\n'
    return wrap_x3d(wrap_shape(geo, appearance))


def seed_transform():
    """Nested transforms - exercises startReadTransform() with all attributes:
    translation, rotation, scale, center, scaleOrientation."""
    content = (
        '    <Transform translation="1 2 3" rotation="0 1 0 1.5708" scale="2 2 2"'
        ' center="0 0 0" scaleOrientation="0 0 1 0">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0 0.5 0"/></Appearance>\n'
        '        <Box size="1 1 1"/>\n'
        "      </Shape>\n"
        '      <Transform translation="3 0 0" rotation="1 0 0 0.7854">\n'
        "        <Shape>\n"
        '          <Appearance><Material diffuseColor="0 0 0.8"/></Appearance>\n'
        '          <Sphere radius="0.5"/>\n'
        "        </Shape>\n"
        "      </Transform>\n"
        "    </Transform>\n"
    )
    return wrap_x3d(content)


def seed_switch():
    """Switch node with whichChoice - exercises startReadSwitch().
    Also includes a Group and StaticGroup to cover those paths."""
    content = (
        '    <Switch whichChoice="1">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="1 0 0"/></Appearance>\n'
        '        <Box size="1 1 1"/>\n'
        "      </Shape>\n"
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0 1 0"/></Appearance>\n'
        '        <Sphere radius="1"/>\n'
        "      </Shape>\n"
        "    </Switch>\n"
        "    <Group>\n"
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0.5 0.5 0"/></Appearance>\n'
        '        <Cone bottomRadius="0.5" height="1"/>\n'
        "      </Shape>\n"
        "    </Group>\n"
        "    <StaticGroup>\n"
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0 0.5 0.5"/></Appearance>\n'
        '        <Cylinder radius="0.3" height="1"/>\n'
        "      </Shape>\n"
        "    </StaticGroup>\n"
    )
    return wrap_x3d(content)


def seed_animation():
    """TimeSensor + interpolators - these are skipped by the importer,
    but exercising the skip paths is valuable for fuzzing coverage."""
    content = (
        '    <TimeSensor DEF="Timer" cycleInterval="4" loop="true"/>\n'
        '    <PositionInterpolator DEF="PosInt" key="0 0.5 1" keyValue="0 0 0, 0 2 0, 0 0 0"/>\n'
        '    <OrientationInterpolator DEF="OriInt" key="0 0.5 1"'
        ' keyValue="0 1 0 0, 0 1 0 3.14, 0 1 0 6.28"/>\n'
        '    <ROUTE fromNode="Timer" fromField="fraction_changed"'
        ' toNode="PosInt" toField="set_fraction"/>\n'
        '    <Transform DEF="AnimatedBox" translation="0 0 0">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="1 0.5 0"/></Appearance>\n'
        '        <Box size="1 1 1"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    return wrap_x3d(content)


def seed_light():
    """All three light types - exercises readDirectionalLight(), readPointLight(), readSpotLight()."""
    content = (
        '    <DirectionalLight ambientIntensity="0.3" color="1 1 1" direction="0 -1 -1"'
        ' global="false" intensity="0.8" on="true"/>\n'
        '    <PointLight ambientIntensity="0.2" attenuation="1 0 0" color="1 0.9 0.8"'
        ' global="true" intensity="1" location="3 5 3" on="true" radius="50"/>\n'
        '    <SpotLight ambientIntensity="0.1" attenuation="1 0 0" beamWidth="0.5"'
        ' color="1 1 0.9" cutOffAngle="1.0" direction="0 -1 0" global="true"'
        ' intensity="0.9" location="0 10 0" on="true" radius="100"/>\n'
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="0.8 0.8 0.8"/></Appearance>\n'
        '      <Sphere radius="1"/>\n'
        "    </Shape>\n"
    )
    return wrap_x3d(content)


def seed_extrusion():
    """Extrusion geometry - exercises readExtrusion() with spine, crossSection, orientation, scale."""
    geo = (
        '      <Extrusion crossSection="1 1, 1 -1, -1 -1, -1 1, 1 1"'
        ' spine="0 0 0, 0 1 0, 0 2 0" scale="1 1, 0.8 0.8, 0.5 0.5"'
        ' orientation="0 0 1 0, 0 0 1 0, 0 0 1 0"'
        ' beginCap="true" endCap="true" ccw="true" convex="true"'
        ' creaseAngle="1.0" solid="true"/>\n'
    )
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_elevationgrid():
    """ElevationGrid - exercises readElevationGrid() with height array and dimensions."""
    geo = (
        '      <ElevationGrid xDimension="3" zDimension="3"'
        ' xSpacing="1.0" zSpacing="1.0"'
        ' height="0 0.5 0, 0.5 1 0.5, 0 0.5 0"'
        ' solid="true" ccw="true" colorPerVertex="true" normalPerVertex="true"'
        ' creaseAngle="0.8">\n'
        '        <Color color="1 0 0, 0 1 0, 0 0 1, 1 1 0, 1 1 1, 0 1 1, 1 0 1, 0.5 0.5 0.5, 0 0 0"/>\n'
        "      </ElevationGrid>\n"
    )
    return wrap_x3d(wrap_shape(geo, default_appearance()))


def seed_nurbs():
    """NURBS nodes - all skipped by the importer, but exercises skipUnsupportedNode() paths.
    Multiple NURBS-related nodes to cover the skip list."""
    content = (
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="0.5 0.5 1"/></Appearance>\n'
        '      <NurbsPatchSurface uDimension="4" vDimension="4" uOrder="4" vOrder="4"'
        ' uKnot="0 0 0 0 1 1 1 1" vKnot="0 0 0 0 1 1 1 1">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 2 0 0, 3 0 0,'
        " 0 0 1, 1 1 1, 2 1 1, 3 0 1,"
        " 0 0 2, 1 1 2, 2 1 2, 3 0 2,"
        ' 0 0 3, 1 0 3, 2 0 3, 3 0 3"/>\n'
        "      </NurbsPatchSurface>\n"
        "    </Shape>\n"
        '    <NurbsCurve order="4" knot="0 0 0 0 1 1 1 1">\n'
        '      <Coordinate point="0 0 0, 1 1 0, 2 1 0, 3 0 0"/>\n'
        "    </NurbsCurve>\n"
    )
    return wrap_x3d(content)


def seed_triangleset():
    """TriangleSet, TriangleStripSet, and TriangleFanSet -
    exercises readTriangleSet(), readTriangleStripSet(), readTriangleFanSet()."""
    # TriangleSet: every 3 coordinates form a triangle
    ts = (
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="1 0 0"/></Appearance>\n'
        '      <TriangleSet ccw="true" solid="true" colorPerVertex="true" normalPerVertex="true">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 0.5 1 0, 2 0 0, 3 0 0, 2.5 1 0"/>\n'
        '        <Normal vector="0 0 1, 0 0 1, 0 0 1, 0 0 1, 0 0 1, 0 0 1"/>\n'
        '        <Color color="1 0 0, 0 1 0, 0 0 1, 1 1 0, 0 1 1, 1 0 1"/>\n'
        "      </TriangleSet>\n"
        "    </Shape>\n"
    )
    # TriangleStripSet: strip of connected triangles
    tss = (
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="0 1 0"/></Appearance>\n'
        '      <TriangleStripSet stripCount="5" ccw="true" solid="true">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 0.5 1 0, 1.5 1 0, 1 2 0"/>\n'
        "      </TriangleStripSet>\n"
        "    </Shape>\n"
    )
    # TriangleFanSet: fan of triangles from a center
    tfs = (
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="0 0 1"/></Appearance>\n'
        '      <TriangleFanSet fanCount="4" ccw="true" solid="true">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 0.7 0.7 0, 0 1 0"/>\n'
        "      </TriangleFanSet>\n"
        "    </Shape>\n"
    )
    return wrap_x3d(ts + tss + tfs)


def seed_indexed_triangle_sets():
    """IndexedTriangleSet, IndexedTriangleFanSet, IndexedTriangleStripSet -
    exercises the indexed variants with explicit index attributes."""
    its = (
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="0.8 0.2 0.2"/></Appearance>\n'
        '      <IndexedTriangleSet index="0 1 2 0 2 3" ccw="true" solid="true">\n'
        '        <Coordinate point="0 0 0, 2 0 0, 2 2 0, 0 2 0"/>\n'
        '        <TextureCoordinate point="0 0, 1 0, 1 1, 0 1"/>\n'
        "      </IndexedTriangleSet>\n"
        "    </Shape>\n"
    )
    itfs = (
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="0.2 0.8 0.2"/></Appearance>\n'
        '      <IndexedTriangleFanSet index="0 1 2 3 -1" ccw="true" solid="true">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 0.7 0.7 0, 0 1 0"/>\n'
        "      </IndexedTriangleFanSet>\n"
        "    </Shape>\n"
    )
    itss = (
        "    <Shape>\n"
        '      <Appearance><Material diffuseColor="0.2 0.2 0.8"/></Appearance>\n'
        '      <IndexedTriangleStripSet index="0 1 2 3 4 -1" ccw="true" solid="true">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 0.5 1 0, 1.5 1 0, 1 2 0"/>\n'
        "      </IndexedTriangleStripSet>\n"
        "    </Shape>\n"
    )
    return wrap_x3d(its + itfs + itss)


def seed_lineset():
    """LineSet - exercises readLineSet() with vertexCount attribute."""
    geo = (
        '      <LineSet vertexCount="3 2">\n'
        '        <Coordinate point="0 0 0, 1 1 0, 2 0 0, 3 0 0, 4 1 0"/>\n'
        '        <Color color="1 0 0, 0 1 0, 0 0 1, 1 1 0, 0 1 1"/>\n'
        "      </LineSet>\n"
    )
    return wrap_x3d(wrap_shape(geo))


def seed_geometry2d():
    """2D geometry nodes - exercises all Geometry2D parsers:
    Arc2D, ArcClose2D, Circle2D, Disk2D, Polyline2D, Polypoint2D, Rectangle2D, TriangleSet2D."""
    shapes = ""
    # Arc2D
    shapes += (
        '    <Transform translation="-5 0 0">\n'
        "      <Shape>\n"
        '        <Arc2D startAngle="0" endAngle="1.5708" radius="1"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # ArcClose2D with PIE closure
    shapes += (
        '    <Transform translation="-3 0 0">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0.8 0.2 0.2"/></Appearance>\n'
        '        <ArcClose2D startAngle="0" endAngle="2.0" radius="1" closureType="PIE" solid="false"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # Circle2D
    shapes += (
        '    <Transform translation="-1 0 0">\n'
        "      <Shape>\n"
        '        <Circle2D radius="0.8"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # Disk2D (filled)
    shapes += (
        '    <Transform translation="1 0 0">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0 0.6 0"/></Appearance>\n'
        '        <Disk2D innerRadius="0" outerRadius="0.8" solid="false"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # Disk2D (ring)
    shapes += (
        '    <Transform translation="3 0 0">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0 0 0.8"/></Appearance>\n'
        '        <Disk2D innerRadius="0.4" outerRadius="0.8" solid="false"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # Polyline2D
    shapes += (
        '    <Transform translation="5 0 0">\n'
        "      <Shape>\n"
        '        <Polyline2D lineSegments="0 0, 1 0, 1 1, 0 1"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # Polypoint2D
    shapes += (
        '    <Transform translation="0 3 0">\n'
        "      <Shape>\n"
        '        <Polypoint2D point="0 0, 0.5 0.5, 1 0, 0.5 -0.5"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # Rectangle2D
    shapes += (
        '    <Transform translation="3 3 0">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0.5 0.5 0"/></Appearance>\n'
        '        <Rectangle2D size="1.5 1" solid="false"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    # TriangleSet2D
    shapes += (
        '    <Transform translation="-3 3 0">\n'
        "      <Shape>\n"
        '        <Appearance><Material diffuseColor="0.8 0 0.8"/></Appearance>\n'
        '        <TriangleSet2D vertices="0 0, 1 0, 0.5 1" solid="false"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    return wrap_x3d(shapes)


def seed_use_def():
    """DEF/USE mechanism - exercises node reuse via DEF and USE attributes."""
    content = (
        "    <Shape>\n"
        '      <Appearance DEF="SharedAppearance">\n'
        '        <Material DEF="SharedMaterial" diffuseColor="0.9 0.1 0.1"/>\n'
        "      </Appearance>\n"
        '      <Box DEF="SharedBox" size="1 1 1"/>\n'
        "    </Shape>\n"
        '    <Transform translation="3 0 0">\n'
        "      <Shape>\n"
        '        <Appearance USE="SharedAppearance"/>\n'
        '        <Box USE="SharedBox"/>\n'
        "      </Shape>\n"
        "    </Transform>\n"
    )
    return wrap_x3d(content)


def seed_metadata():
    """Head metadata and MetadataString nodes - exercises readHead() meta parsing."""
    return (
        XML_HEADER
        + '<X3D profile="Interchange" version="3.3">\n'
        + "  <head>\n"
        + '    <meta name="title" content="Fuzzing Seed"/>\n'
        + '    <meta name="creator" content="generate_x3d_seeds.py"/>\n'
        + '    <meta name="description" content="Metadata test seed"/>\n'
        + "  </head>\n"
        + "  <Scene>\n"
        + "    <Shape>\n"
        + '      <Appearance><Material diffuseColor="0.5 0.5 0.5"/></Appearance>\n'
        + '      <Box size="1 1 1"/>\n'
        + "    </Shape>\n"
        + "  </Scene>\n"
        + "</X3D>\n"
    )


def seed_complex_indexed_faceset():
    """Complex IndexedFaceSet with colorIndex, normalIndex, texCoordIndex -
    exercises all index array parsing in readIndexedFaceSet()."""
    geo = (
        '      <IndexedFaceSet coordIndex="0 1 2 -1 2 3 0 -1 4 5 6 -1 6 7 4 -1 0 1 5 4 -1 2 3 7 6 -1 1 2 6 5 -1 0 3 7 4 -1"'
        ' colorIndex="0 0 0 -1 1 1 1 -1 2 2 2 -1 3 3 3 -1 4 4 4 -1 5 5 5 -1 0 0 0 -1 1 1 1 -1"'
        ' normalIndex="0 0 0 -1 0 0 0 -1 1 1 1 -1 1 1 1 -1 2 2 2 -1 2 2 2 -1 3 3 3 -1 3 3 3 -1"'
        ' texCoordIndex="0 1 2 -1 2 3 0 -1 0 1 2 -1 2 3 0 -1 0 1 2 -1 2 3 0 -1 0 1 2 -1 2 3 0 -1"'
        ' ccw="true" solid="true" convex="true" creaseAngle="1.0"'
        ' colorPerVertex="true" normalPerVertex="true">\n'
        '        <Coordinate point="0 0 0, 1 0 0, 1 1 0, 0 1 0, 0 0 1, 1 0 1, 1 1 1, 0 1 1"/>\n'
        '        <Color color="1 0 0, 0 1 0, 0 0 1, 1 1 0, 0 1 1, 1 0 1"/>\n'
        '        <Normal vector="0 0 -1, 0 0 1, 0 -1 0, 0 1 0"/>\n'
        '        <TextureCoordinate point="0 0, 1 0, 1 1, 0 1"/>\n'
        "      </IndexedFaceSet>\n"
    )
    return wrap_x3d(wrap_shape(geo, default_appearance()))


# --------------------------------------------------------------------------
# Seed registry
# --------------------------------------------------------------------------

SEEDS = {
    "box": seed_box,
    "sphere": seed_sphere,
    "cylinder": seed_cylinder,
    "cone": seed_cone,
    "indexed_lineset": seed_indexed_lineset,
    "pointset": seed_pointset,
    "text": seed_text,
    "material": seed_material,
    "transform": seed_transform,
    "switch": seed_switch,
    "animation": seed_animation,
    "light": seed_light,
    "extrusion": seed_extrusion,
    "elevationgrid": seed_elevationgrid,
    "nurbs": seed_nurbs,
    "triangleset": seed_triangleset,
    "indexed_faceset": seed_indexed_faceset,
    "indexed_triangle_sets": seed_indexed_triangle_sets,
    "lineset": seed_lineset,
    "geometry2d": seed_geometry2d,
    "use_def": seed_use_def,
    "metadata": seed_metadata,
    "complex_indexed_faceset": seed_complex_indexed_faceset,
}


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test", "models", "X3D", "fuzz_seeds"
    )
    os.makedirs(outdir, exist_ok=True)

    for name, gen in SEEDS.items():
        content = gen()
        path = os.path.join(outdir, f"seed_{name}.x3d")
        with open(path, "w") as f:
            f.write(content)
        print(f"  {path} ({len(content)} bytes)")

    print(f"\nGenerated {len(SEEDS)} X3D seed files in {outdir}/")


if __name__ == "__main__":
    main()
