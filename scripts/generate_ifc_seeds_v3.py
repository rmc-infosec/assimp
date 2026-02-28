#!/usr/bin/env python3
"""Generate additional IFC 2x3 seed files targeting uncovered entity types.

Supplements generate_ifc_seeds.py and generate_ifc_seeds_v2.py with seeds for:
- IfcBSplineCurveWithKnots
- IfcRationalBSplineCurveWithKnots
- IfcSurfaceOfRevolution
- IfcSurfaceOfLinearExtrusion
- IfcRectangularTrimmedSurface
- IfcCurveBoundedPlane
- IfcMappedItem with type product
- IfcRelVoidsElement with IfcHalfSpaceSolid
- IfcSpace
- IfcAnnotation with text literal
- IfcStairFlight with slab geometry
- IfcRamp
- IfcArbitraryOpenProfileDef
- IfcEllipseProfileDef
- IfcCartesianTransformationOperator3D in IfcMappedItem
"""

import os
import sys

HEADER = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView_V2.0]'),'2;1');
FILE_NAME('test.ifc','2024-01-01',(''),(''),'','','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
"""

FOOTER = """ENDSEC;
END-ISO-10303-21;
"""

# Common base entities shared by most seeds.
# IDs #1..#25 are reserved for these.
BASE_ENTITIES = """\
#1=IFCORGANIZATION($,'Fuzz','Fuzzing seed v3',$,$);
#2=IFCAPPLICATION(#1,'1.0','FuzzGen3','FuzzGen3');
#3=IFCOWNERHISTORY(#1,#2,$,.NOCHANGE.,$,$,$,0);
#4=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#5=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#6=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#7=IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.);
#8=IFCUNITASSIGNMENT((#4,#5,#6,#7));
#9=IFCDIRECTION((1.,0.,0.));
#10=IFCDIRECTION((0.,1.,0.));
#11=IFCDIRECTION((0.,0.,1.));
#12=IFCCARTESIANPOINT((0.,0.,0.));
#13=IFCAXIS2PLACEMENT3D(#12,#11,#9);
#14=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-5,#13,$);
#15=IFCPROJECT('3001',#3,'FuzzV3',$,$,$,$,(#14),#8);
#16=IFCLOCALPLACEMENT($,#13);
#17=IFCSITE('3002',#3,'Site',$,$,#16,$,$,.ELEMENT.,$,$,$,$,$);
#18=IFCRELAGGREGATES('3003',#3,$,$,#15,(#17));
#19=IFCBUILDING('3004',#3,'Building',$,$,#16,$,$,.ELEMENT.,$,$,$);
#20=IFCRELAGGREGATES('3005',#3,$,$,#17,(#19));
#21=IFCBUILDINGSTOREY('3006',#3,'Floor',$,$,#16,$,$,.ELEMENT.,0.);
#22=IFCRELAGGREGATES('3007',#3,$,$,#19,(#21));
#23=IFCAXIS2PLACEMENT2D(#24,#25);
#24=IFCCARTESIANPOINT((0.,0.));
#25=IFCDIRECTION((1.,0.));
"""


def seed_v3_bspline_curve():
    """IfcBSplineCurveWithKnots as profile boundary, extruded.

    Degree 3, 7 control points forming a closed-ish shape.
    """
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.));
#101=IFCCARTESIANPOINT((1.,0.5));
#102=IFCCARTESIANPOINT((2.,0.));
#103=IFCCARTESIANPOINT((2.,1.));
#104=IFCCARTESIANPOINT((1.,1.5));
#105=IFCCARTESIANPOINT((0.,1.));
#106=IFCCARTESIANPOINT((0.,0.));
#107=IFCBSPLINECURVEWITHKNOTS(3,(#100,#101,#102,#103,#104,#105,#106),.UNSPECIFIED.,.T.,.U.,(4,1,1,1,4),(0.,0.25,0.5,0.75,1.),.UNSPECIFIED.);
#108=IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,'bspline',#107);
#109=IFCEXTRUDEDAREASOLID(#108,#13,#11,1.5);
#110=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#109));
#111=IFCPRODUCTDEFINITIONSHAPE($,$,(#110));
#112=IFCBUILDINGELEMENTPROXY('BS01',#3,'BSplineExtrusion',$,$,#16,#111,$,$);
#113=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC01',#3,$,$,(#112),#21);
"""


def seed_v3_rational_bspline():
    """IfcRationalBSplineCurveWithKnots (weighted) as profile, extruded."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.));
#101=IFCCARTESIANPOINT((0.5,1.));
#102=IFCCARTESIANPOINT((1.5,1.));
#103=IFCCARTESIANPOINT((2.,0.));
#104=IFCCARTESIANPOINT((1.5,-0.5));
#105=IFCCARTESIANPOINT((0.5,-0.5));
#106=IFCCARTESIANPOINT((0.,0.));
#107=IFCRATIONALBSPLINECURVEWITHKNOTS(3,(#100,#101,#102,#103,#104,#105,#106),.UNSPECIFIED.,.T.,.U.,(4,1,1,1,4),(0.,0.25,0.5,0.75,1.),.UNSPECIFIED.,(1.,0.7,1.,0.7,1.,0.7,1.));
#108=IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,'rational',#107);
#109=IFCEXTRUDEDAREASOLID(#108,#13,#11,2.0);
#110=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#109));
#111=IFCPRODUCTDEFINITIONSHAPE($,$,(#110));
#112=IFCBUILDINGELEMENTPROXY('RB01',#3,'RationalBSpline',$,$,#16,#111,$,$);
#113=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC02',#3,$,$,(#112),#21);
"""


def seed_v3_surface_of_revolution():
    """IfcSurfaceOfRevolution with a polyline generatrix."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.5,0.,0.));
#101=IFCCARTESIANPOINT((0.8,0.,0.5));
#102=IFCCARTESIANPOINT((0.3,0.,1.));
#103=IFCCARTESIANPOINT((0.6,0.,1.5));
#104=IFCPOLYLINE((#100,#101,#102,#103));
#105=IFCAXIS1PLACEMENT(#12,#11);
#106=IFCSURFACEOFREVOLUTION(#104,#13,#105);
#107=IFCSHAPEREPRESENTATION(#14,'Body','SurfaceModel',(#106));
#108=IFCPRODUCTDEFINITIONSHAPE($,$,(#107));
#109=IFCBUILDINGELEMENTPROXY('SR01',#3,'SurfRev',$,$,#16,#108,$,$);
#110=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC03',#3,$,$,(#109),#21);
"""


def seed_v3_surface_of_extrusion():
    """IfcSurfaceOfLinearExtrusion with a circle as swept curve."""
    return BASE_ENTITIES + """\
#100=IFCAXIS2PLACEMENT3D(#12,#11,#9);
#101=IFCCIRCLE(#100,0.5);
#102=IFCDIRECTION((0.,0.,1.));
#103=IFCSURFACEOFLINEAREXTRUSION(#101,#13,#102,2.0);
#104=IFCSHAPEREPRESENTATION(#14,'Body','SurfaceModel',(#103));
#105=IFCPRODUCTDEFINITIONSHAPE($,$,(#104));
#106=IFCBUILDINGELEMENTPROXY('SE01',#3,'SurfExt',$,$,#16,#105,$,$);
#107=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC04',#3,$,$,(#106),#21);
"""


def seed_v3_rect_trimmed_surface():
    """IfcRectangularTrimmedSurface trimming a plane."""
    return BASE_ENTITIES + """\
#100=IFCAXIS2PLACEMENT3D(#12,#11,#9);
#101=IFCPLANE(#100);
#102=IFCRECTANGULARTRIMMEDSURFACE(#101,0.0,2.0,0.0,1.5,.T.,.T.);
#103=IFCSHAPEREPRESENTATION(#14,'Body','SurfaceModel',(#102));
#104=IFCPRODUCTDEFINITIONSHAPE($,$,(#103));
#105=IFCBUILDINGELEMENTPROXY('RT01',#3,'RectTrimSurf',$,$,#16,#104,$,$);
#106=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC05',#3,$,$,(#105),#21);
"""


def seed_v3_curve_bounded_plane():
    """IfcCurveBoundedPlane with a polyline boundary."""
    return BASE_ENTITIES + """\
#100=IFCAXIS2PLACEMENT3D(#12,#11,#9);
#101=IFCPLANE(#100);
#102=IFCCARTESIANPOINT((0.,0.,0.));
#103=IFCCARTESIANPOINT((2.,0.,0.));
#104=IFCCARTESIANPOINT((2.,1.,0.));
#105=IFCCARTESIANPOINT((0.,1.,0.));
#106=IFCPOLYLINE((#102,#103,#104,#105,#102));
#107=IFCCURVEBOUNDEDPLANE(#101,#106,());
#108=IFCSHAPEREPRESENTATION(#14,'Body','SurfaceModel',(#107));
#109=IFCPRODUCTDEFINITIONSHAPE($,$,(#108));
#110=IFCBUILDINGELEMENTPROXY('CB01',#3,'CurveBoundPlane',$,$,#16,#109,$,$);
#111=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC06',#3,$,$,(#110),#21);
"""


def seed_v3_mapped_item():
    """IfcMappedItem mapping a representation from a type product to instances."""
    return BASE_ENTITIES + """\
#100=IFCRECTANGLEPROFILEDEF(.AREA.,'col',#23,0.4,0.4);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#11,3.0);
#102=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#101));
#103=IFCREPRESENTATIONMAP(#13,#102);
#104=IFCCOLUMNTYPE('CT01',#3,'ColType',$,$,$,(#103),$,$,.COLUMN.);
#105=IFCCARTESIANTRANSFORMATIONOPERATOR3D($,$,#12,1.0,$);
#106=IFCMAPPEDITEM(#103,#105);
#107=IFCSHAPEREPRESENTATION(#14,'Body','MappedRepresentation',(#106));
#108=IFCPRODUCTDEFINITIONSHAPE($,$,(#107));
#109=IFCCOLUMN('MI01',#3,'MappedCol1',$,$,#16,#108,$);
#110=IFCCARTESIANPOINT((3.,0.,0.));
#111=IFCCARTESIANTRANSFORMATIONOPERATOR3D($,$,#110,1.0,$);
#112=IFCMAPPEDITEM(#103,#111);
#113=IFCSHAPEREPRESENTATION(#14,'Body','MappedRepresentation',(#112));
#114=IFCPRODUCTDEFINITIONSHAPE($,$,(#113));
#115=IFCCOLUMN('MI02',#3,'MappedCol2',$,$,#16,#114,$);
#116=IFCRELDEFINESBYTYPE('RD01',#3,$,$,(#109,#115),#104);
#117=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC07',#3,$,$,(#109,#115),#21);
"""


def seed_v3_rel_voids():
    """IfcRelVoidsElement with IfcOpeningElement using IfcHalfSpaceSolid."""
    return BASE_ENTITIES + """\
#100=IFCRECTANGLEPROFILEDEF(.AREA.,'wall',#23,4.0,0.2);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#11,3.0);
#102=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#101));
#103=IFCPRODUCTDEFINITIONSHAPE($,$,(#102));
#104=IFCWALLSTANDARDCASE('VW01',#3,'VoidedWall',$,$,#16,#103,$);
#105=IFCCARTESIANPOINT((0.,0.,1.5));
#106=IFCDIRECTION((0.,1.,0.));
#107=IFCAXIS2PLACEMENT3D(#105,#106,#9);
#108=IFCPLANE(#107);
#109=IFCHALFSPACESOLID(#108,.T.);
#110=IFCSHAPEREPRESENTATION(#14,'Body','CSG',(#109));
#111=IFCPRODUCTDEFINITIONSHAPE($,$,(#110));
#112=IFCCARTESIANPOINT((1.,0.,0.));
#113=IFCAXIS2PLACEMENT3D(#112,#11,#9);
#114=IFCLOCALPLACEMENT(#16,#113);
#115=IFCOPENINGELEMENT('OE01',#3,'HalfSpaceOpening',$,$,#114,#111,$);
#116=IFCRELVOIDSELEMENT('RV01',#3,$,$,#104,#115);
#117=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC08',#3,$,$,(#104),#21);
"""


def seed_v3_space():
    """IfcSpace entity with bounded geometry."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.));
#101=IFCCARTESIANPOINT((4.,0.));
#102=IFCCARTESIANPOINT((4.,3.));
#103=IFCCARTESIANPOINT((0.,3.));
#104=IFCPOLYLINE((#100,#101,#102,#103,#100));
#105=IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,'space',#104);
#106=IFCEXTRUDEDAREASOLID(#105,#13,#11,2.8);
#107=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#106));
#108=IFCPRODUCTDEFINITIONSHAPE($,$,(#107));
#109=IFCSPACE('SP01',#3,'Room1','A room',$,#16,#108,$,.ELEMENT.,.INTERNAL.,$);
#110=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC09',#3,$,$,(#109),#21);
"""


def seed_v3_annotation():
    """IfcAnnotation with text literal geometry."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((1.,1.,0.));
#101=IFCAXIS2PLACEMENT3D(#100,#11,#9);
#102=IFCTEXTLITERALWITHEXTENT('Room Label',#101,.LEFT.,$,$);
#103=IFCSHAPEREPRESENTATION(#14,'Body','Annotation2D',(#102));
#104=IFCPRODUCTDEFINITIONSHAPE($,$,(#103));
#105=IFCANNOTATION('AN01',#3,'TextAnnotation',$,$,#16,#104);
#106=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC10',#3,$,$,(#105),#21);
"""


def seed_v3_stair():
    """IfcStairFlight with slab geometry for the landing."""
    return BASE_ENTITIES + """\
#100=IFCRECTANGLEPROFILEDEF(.AREA.,'tread',#23,1.0,0.3);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#11,0.17);
#102=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#101));
#103=IFCPRODUCTDEFINITIONSHAPE($,$,(#102));
#104=IFCSTAIRFLIGHT('SF01',#3,'MainFlight',$,$,#16,#103,$,12,1,0.17,0.28);
#105=IFCRECTANGLEPROFILEDEF(.AREA.,'landing',#23,1.0,1.0);
#106=IFCCARTESIANPOINT((0.,0.,2.04));
#107=IFCAXIS2PLACEMENT3D(#106,#11,#9);
#108=IFCEXTRUDEDAREASOLID(#105,#107,#11,0.2);
#109=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#108));
#110=IFCPRODUCTDEFINITIONSHAPE($,$,(#109));
#111=IFCSLAB('SL01',#3,'Landing',$,$,#16,#110,$,.LANDING.);
#112=IFCSTAIR('ST01',#3,'MainStair',$,$,#16,$,$,.HALF_TURN_STAIR.);
#113=IFCRELAGGREGATES('RA01',#3,$,$,#112,(#104,#111));
#114=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC11',#3,$,$,(#112),#21);
"""


def seed_v3_ramp():
    """IfcRamp with a simple extruded geometry."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.));
#101=IFCCARTESIANPOINT((3.,0.));
#102=IFCCARTESIANPOINT((3.,0.5));
#103=IFCCARTESIANPOINT((0.,0.));
#104=IFCPOLYLINE((#100,#101,#102,#103));
#105=IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,'ramp_profile',#104);
#106=IFCEXTRUDEDAREASOLID(#105,#13,#10,1.2);
#107=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#106));
#108=IFCPRODUCTDEFINITIONSHAPE($,$,(#107));
#109=IFCRAMP('RM01',#3,'SimpleRamp',$,$,#16,#108,$,.STRAIGHT_RUN_RAMP.);
#110=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC12',#3,$,$,(#109),#21);
"""


def seed_v3_arbitrary_open_profile():
    """IfcArbitraryOpenProfileDef as swept surface."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.));
#101=IFCCARTESIANPOINT((1.,0.5));
#102=IFCCARTESIANPOINT((2.,0.));
#103=IFCCARTESIANPOINT((3.,0.5));
#104=IFCPOLYLINE((#100,#101,#102,#103));
#105=IFCARBITRARYOPENPROFILEDEF(.CURVE.,'open_wave',#104);
#106=IFCEXTRUDEDAREASOLID(#105,#13,#11,2.0);
#107=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#106));
#108=IFCPRODUCTDEFINITIONSHAPE($,$,(#107));
#109=IFCBUILDINGELEMENTPROXY('AO01',#3,'OpenProfileSwept',$,$,#16,#108,$,$);
#110=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC13',#3,$,$,(#109),#21);
"""


def seed_v3_ellipse_profile():
    """IfcEllipseProfileDef extruded."""
    return BASE_ENTITIES + """\
#100=IFCELLIPSEPROFILEDEF(.AREA.,'ellipse',#23,0.8,0.4);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#11,2.5);
#102=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#101));
#103=IFCPRODUCTDEFINITIONSHAPE($,$,(#102));
#104=IFCCOLUMN('EP01',#3,'EllipseColumn',$,$,#16,#103,$);
#105=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC14',#3,$,$,(#104),#21);
"""


def seed_v3_cartesian_transform():
    """IfcCartesianTransformationOperator3D used within IfcMappedItem.

    Exercises non-uniform scaling and axis vectors in the transform.
    """
    return BASE_ENTITIES + """\
#100=IFCCIRCLEPROFILEDEF(.AREA.,'disc',#23,0.3);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#11,1.0);
#102=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#101));
#103=IFCREPRESENTATIONMAP(#13,#102);
#104=IFCDIRECTION((1.,0.,0.));
#105=IFCDIRECTION((0.,1.,0.));
#106=IFCCARTESIANPOINT((0.,0.,0.));
#107=IFCCARTESIANTRANSFORMATIONOPERATOR3D(#104,#105,#106,1.0,#11);
#108=IFCMAPPEDITEM(#103,#107);
#109=IFCSHAPEREPRESENTATION(#14,'Body','MappedRepresentation',(#108));
#110=IFCPRODUCTDEFINITIONSHAPE($,$,(#109));
#111=IFCCOLUMN('CT01',#3,'TransCol1',$,$,#16,#110,$);
#112=IFCDIRECTION((0.707,0.707,0.));
#113=IFCDIRECTION((-0.707,0.707,0.));
#114=IFCCARTESIANPOINT((2.,0.,0.));
#115=IFCCARTESIANTRANSFORMATIONOPERATOR3D(#112,#113,#114,2.0,#11);
#116=IFCMAPPEDITEM(#103,#115);
#117=IFCSHAPEREPRESENTATION(#14,'Body','MappedRepresentation',(#116));
#118=IFCPRODUCTDEFINITIONSHAPE($,$,(#117));
#119=IFCCOLUMN('CT02',#3,'TransCol2',$,$,#16,#118,$);
#120=IFCDIRECTION((0.,0.,1.));
#121=IFCCARTESIANPOINT((0.,3.,0.));
#122=IFCCARTESIANTRANSFORMATIONOPERATOR3D(#9,#10,#121,0.5,#120);
#123=IFCMAPPEDITEM(#103,#122);
#124=IFCSHAPEREPRESENTATION(#14,'Body','MappedRepresentation',(#123));
#125=IFCPRODUCTDEFINITIONSHAPE($,$,(#124));
#126=IFCCOLUMN('CT03',#3,'TransCol3',$,$,#16,#125,$);
#127=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC15',#3,$,$,(#111,#119,#126),#21);
"""


SEEDS_V3 = {
    "v3_bspline_curve": seed_v3_bspline_curve,
    "v3_rational_bspline": seed_v3_rational_bspline,
    "v3_surface_of_revolution": seed_v3_surface_of_revolution,
    "v3_surface_of_extrusion": seed_v3_surface_of_extrusion,
    "v3_rect_trimmed_surface": seed_v3_rect_trimmed_surface,
    "v3_curve_bounded_plane": seed_v3_curve_bounded_plane,
    "v3_mapped_item": seed_v3_mapped_item,
    "v3_rel_voids": seed_v3_rel_voids,
    "v3_space": seed_v3_space,
    "v3_annotation": seed_v3_annotation,
    "v3_stair": seed_v3_stair,
    "v3_ramp": seed_v3_ramp,
    "v3_arbitrary_open_profile": seed_v3_arbitrary_open_profile,
    "v3_ellipse_profile": seed_v3_ellipse_profile,
    "v3_cartesian_transform": seed_v3_cartesian_transform,
}


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "test", "models", "IFC", "fuzz_seeds")
    os.makedirs(outdir, exist_ok=True)

    for name, gen in SEEDS_V3.items():
        content = gen()
        # Add header/footer if not already present
        if not content.startswith("ISO-10303-21"):
            content = HEADER + content + FOOTER

        path = os.path.join(outdir, f"seed_{name}.ifc")
        with open(path, "w") as f:
            f.write(content)
        print(f"  {path} ({len(content)} bytes)")

    print(f"\nGenerated {len(SEEDS_V3)} IFC seed files in {outdir}/")


if __name__ == "__main__":
    main()
