#!/usr/bin/env python3
"""Generate additional IFC 2x3 seed files targeting uncovered code paths.

Supplements generate_ifc_seeds.py with seeds for:
- IfcRevolvedAreaSolid
- IfcSweptDiskSolid
- IfcTrimmedCurve (trimming IfcCircle)
- IfcCompositeCurve
- IfcIShapeProfileDef
- IfcBooleanClippingResult with two ExtrudedAreaSolid operands
- IfcFaceBasedSurfaceModel
- IfcShellBasedSurfaceModel
- IfcConversionBasedUnit (degrees)
- IfcSurfaceStyleRendering with full properties
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
#1=IFCORGANIZATION($,'Fuzz','Fuzzing seed v2',$,$);
#2=IFCAPPLICATION(#1,'1.0','FuzzGen2','FuzzGen2');
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
#15=IFCPROJECT('1001',#3,'FuzzV2',$,$,$,$,(#14),#8);
#16=IFCLOCALPLACEMENT($,#13);
#17=IFCSITE('1002',#3,'Site',$,$,#16,$,$,.ELEMENT.,$,$,$,$,$);
#18=IFCRELAGGREGATES('1003',#3,$,$,#15,(#17));
#19=IFCBUILDING('1004',#3,'Building',$,$,#16,$,$,.ELEMENT.,$,$,$);
#20=IFCRELAGGREGATES('1005',#3,$,$,#17,(#19));
#21=IFCBUILDINGSTOREY('1006',#3,'Floor',$,$,#16,$,$,.ELEMENT.,0.);
#22=IFCRELAGGREGATES('1007',#3,$,$,#19,(#21));
#23=IFCAXIS2PLACEMENT2D(#24,#25);
#24=IFCCARTESIANPOINT((0.,0.));
#25=IFCDIRECTION((1.,0.));
"""


def seed_v2_revolved_solid():
    """IfcRevolvedAreaSolid revolving a rectangular profile around an axis."""
    return BASE_ENTITIES + """\
#100=IFCRECTANGLEPROFILEDEF(.AREA.,'rect',#23,0.1,0.5);
#101=IFCCARTESIANPOINT((0.3,0.,0.));
#102=IFCAXIS2PLACEMENT3D(#101,#11,#9);
#103=IFCDIRECTION((0.,0.,1.));
#104=IFCAXIS1PLACEMENT(#12,#103);
#105=IFCREVOLVEDAREASOLID(#100,#102,#104,360.0);
#106=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#105));
#107=IFCPRODUCTDEFINITIONSHAPE($,$,(#106));
#108=IFCWALLSTANDARDCASE('RV01',#3,'RevolvedWall',$,$,#16,#107,$);
#109=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC01',#3,$,$,(#108),#21);
"""


def seed_v2_swept_disk():
    """IfcSweptDiskSolid sweeping a disk along a polyline directrix."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.,0.));
#101=IFCCARTESIANPOINT((1.,0.,0.));
#102=IFCCARTESIANPOINT((1.,1.,0.));
#103=IFCCARTESIANPOINT((1.,1.,1.));
#104=IFCPOLYLINE((#100,#101,#102,#103));
#105=IFCSWEPTDISKSOLID(#104,0.05,$,0.0,1.0);
#106=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#105));
#107=IFCPRODUCTDEFINITIONSHAPE($,$,(#106));
#108=IFCBUILDINGELEMENTPROXY('SD01',#3,'SweptDisk',$,$,#16,#107,$,$);
#109=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC02',#3,$,$,(#108),#21);
"""


def seed_v2_trimmed_curve():
    """IfcTrimmedCurve trimming an IfcCircle by parameter values."""
    return BASE_ENTITIES + """\
#100=IFCAXIS2PLACEMENT3D(#12,#11,#9);
#101=IFCCIRCLE(#100,1.0);
#102=IFCTRIMMEDCURVE(#101,(IFCPARAMETERVALUE(0.0)),(IFCPARAMETERVALUE(3.14159)),.T.,.PARAMETER.);
#103=IFCCARTESIANPOINT((-1.,0.));
#104=IFCCARTESIANPOINT((1.,0.));
#105=IFCPOLYLINE((#103,#104));
#106=IFCCOMPOSITECURVE((#107,#108),.F.);
#107=IFCCOMPOSITECURVESEGMENT(.CONTINUOUS.,.T.,#102);
#108=IFCCOMPOSITECURVESEGMENT(.CONTINUOUS.,.T.,#105);
#109=IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,'trimmed',#106);
#110=IFCEXTRUDEDAREASOLID(#109,#13,#11,1.0);
#111=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#110));
#112=IFCPRODUCTDEFINITIONSHAPE($,$,(#111));
#113=IFCBUILDINGELEMENTPROXY('TC01',#3,'TrimmedCurveElem',$,$,#16,#112,$,$);
#114=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC03',#3,$,$,(#113),#21);
"""


def seed_v2_composite_curve():
    """IfcCompositeCurve combining polyline and trimmed-circle segments."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.));
#101=IFCCARTESIANPOINT((2.,0.));
#102=IFCCARTESIANPOINT((2.,1.));
#103=IFCCARTESIANPOINT((0.,1.));
#104=IFCPOLYLINE((#100,#101));
#105=IFCPOLYLINE((#101,#102));
#106=IFCPOLYLINE((#102,#103));
#107=IFCPOLYLINE((#103,#100));
#108=IFCCOMPOSITECURVESEGMENT(.CONTINUOUS.,.T.,#104);
#109=IFCCOMPOSITECURVESEGMENT(.CONTINUOUS.,.T.,#105);
#110=IFCCOMPOSITECURVESEGMENT(.CONTINUOUS.,.T.,#106);
#111=IFCCOMPOSITECURVESEGMENT(.CONTINUOUS.,.T.,#107);
#112=IFCCOMPOSITECURVE((#108,#109,#110,#111),.F.);
#113=IFCARBITRARYCLOSEDPROFILEDEF(.AREA.,'composite',#112);
#114=IFCEXTRUDEDAREASOLID(#113,#13,#11,2.0);
#115=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#114));
#116=IFCPRODUCTDEFINITIONSHAPE($,$,(#115));
#117=IFCBUILDINGELEMENTPROXY('CC01',#3,'CompositeCurveElem',$,$,#16,#116,$,$);
#118=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC04',#3,$,$,(#117),#21);
"""


def seed_v2_ishape():
    """IfcIShapeProfileDef extruded as a beam."""
    return BASE_ENTITIES + """\
#100=IFCISHAPEPROFILEDEF(.AREA.,'I-Beam',#23,0.3,0.6,0.01,0.02);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#9,5.0);
#102=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#101));
#103=IFCPRODUCTDEFINITIONSHAPE($,$,(#102));
#104=IFCBEAM('IB01',#3,'IBeam',$,$,#16,#103,$);
#105=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC05',#3,$,$,(#104),#21);
"""


def seed_v2_boolean_ext_diff():
    """IfcBooleanClippingResult with two IfcExtrudedAreaSolid operands.

    Exercises ProcessBooleanExtrudedAreaSolidDifference().
    """
    return BASE_ENTITIES + """\
#100=IFCRECTANGLEPROFILEDEF(.AREA.,'outer',#23,2.0,1.0);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#11,3.0);
#102=IFCRECTANGLEPROFILEDEF(.AREA.,'inner',#23,1.0,0.5);
#103=IFCCARTESIANPOINT((0.,0.,0.5));
#104=IFCAXIS2PLACEMENT3D(#103,#11,#9);
#105=IFCEXTRUDEDAREASOLID(#102,#104,#11,2.0);
#106=IFCBOOLEANCLIPPINGRESULT(.DIFFERENCE.,#101,#105);
#107=IFCSHAPEREPRESENTATION(#14,'Body','CSG',(#106));
#108=IFCPRODUCTDEFINITIONSHAPE($,$,(#107));
#109=IFCBUILDINGELEMENTPROXY('BD01',#3,'BoolDiffExt',$,$,#16,#108,$,$);
#110=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC06',#3,$,$,(#109),#21);
"""


def seed_v2_face_surface():
    """IfcFaceBasedSurfaceModel with connected faces forming a simple shape."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.,0.));
#101=IFCCARTESIANPOINT((1.,0.,0.));
#102=IFCCARTESIANPOINT((1.,1.,0.));
#103=IFCCARTESIANPOINT((0.,1.,0.));
#104=IFCCARTESIANPOINT((0.5,0.5,1.));
#110=IFCPOLYLOOP((#100,#101,#102,#103));
#111=IFCFACEOUTERBOUND(#110,.T.);
#112=IFCFACE((#111));
#113=IFCPOLYLOOP((#100,#101,#104));
#114=IFCFACEOUTERBOUND(#113,.T.);
#115=IFCFACE((#114));
#116=IFCPOLYLOOP((#101,#102,#104));
#117=IFCFACEOUTERBOUND(#116,.T.);
#118=IFCFACE((#117));
#119=IFCPOLYLOOP((#102,#103,#104));
#120=IFCFACEOUTERBOUND(#119,.T.);
#121=IFCFACE((#120));
#122=IFCPOLYLOOP((#103,#100,#104));
#123=IFCFACEOUTERBOUND(#122,.T.);
#124=IFCFACE((#123));
#125=IFCCONNECTEDFACESET((#112,#115,#118,#121,#124));
#126=IFCFACEBASEDSURFACEMODEL((#125));
#127=IFCSHAPEREPRESENTATION(#14,'Body','SurfaceModel',(#126));
#128=IFCPRODUCTDEFINITIONSHAPE($,$,(#127));
#129=IFCBUILDINGELEMENTPROXY('FS01',#3,'FaceSurface',$,$,#16,#128,$,$);
#130=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC07',#3,$,$,(#129),#21);
"""


def seed_v2_shell_surface():
    """IfcShellBasedSurfaceModel with a closed shell forming a box."""
    return BASE_ENTITIES + """\
#100=IFCCARTESIANPOINT((0.,0.,0.));
#101=IFCCARTESIANPOINT((1.,0.,0.));
#102=IFCCARTESIANPOINT((1.,1.,0.));
#103=IFCCARTESIANPOINT((0.,1.,0.));
#104=IFCCARTESIANPOINT((0.,0.,1.));
#105=IFCCARTESIANPOINT((1.,0.,1.));
#106=IFCCARTESIANPOINT((1.,1.,1.));
#107=IFCCARTESIANPOINT((0.,1.,1.));
#110=IFCPOLYLOOP((#100,#103,#102,#101));
#111=IFCFACEOUTERBOUND(#110,.T.);
#112=IFCFACE((#111));
#113=IFCPOLYLOOP((#104,#105,#106,#107));
#114=IFCFACEOUTERBOUND(#113,.T.);
#115=IFCFACE((#114));
#116=IFCPOLYLOOP((#100,#101,#105,#104));
#117=IFCFACEOUTERBOUND(#116,.T.);
#118=IFCFACE((#117));
#119=IFCPOLYLOOP((#101,#102,#106,#105));
#120=IFCFACEOUTERBOUND(#119,.T.);
#121=IFCFACE((#120));
#122=IFCPOLYLOOP((#102,#103,#107,#106));
#123=IFCFACEOUTERBOUND(#122,.T.);
#124=IFCFACE((#123));
#125=IFCPOLYLOOP((#103,#100,#104,#107));
#126=IFCFACEOUTERBOUND(#125,.T.);
#127=IFCFACE((#126));
#128=IFCCLOSEDSHELL((#112,#115,#118,#121,#124,#127));
#129=IFCSHELLBASEDSURFACEMODEL((#128));
#130=IFCSHAPEREPRESENTATION(#14,'Body','SurfaceModel',(#129));
#131=IFCPRODUCTDEFINITIONSHAPE($,$,(#130));
#132=IFCBUILDINGELEMENTPROXY('SS01',#3,'ShellSurface',$,$,#16,#131,$,$);
#133=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC08',#3,$,$,(#132),#21);
"""


def seed_v2_degree_units():
    """IfcConversionBasedUnit for degrees (exercises SetUnits degree path)."""
    # This seed has a custom header because it uses a different unit assignment.
    return """\
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView_V2.0]'),'2;1');
FILE_NAME('test.ifc','2024-01-01',(''),(''),'','','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCORGANIZATION($,'Fuzz','Fuzzing seed v2',$,$);
#2=IFCAPPLICATION(#1,'1.0','FuzzGen2','FuzzGen2');
#3=IFCOWNERHISTORY(#1,#2,$,.NOCHANGE.,$,$,$,0);
#4=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#5=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#6=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#7=IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.);
#8=IFCDIMENSIONALEXPONENTS(0,0,0,0,0,0,0);
#9=IFCMEASUREWITHUNIT(IFCPLANEANGLEMEASURE(0.0174533),#7);
#10=IFCCONVERSIONBASEDUNIT(#8,.PLANEANGLEUNIT.,'degree',#9);
#11=IFCUNITASSIGNMENT((#4,#5,#6,#10));
#12=IFCDIRECTION((1.,0.,0.));
#13=IFCDIRECTION((0.,1.,0.));
#14=IFCDIRECTION((0.,0.,1.));
#15=IFCCARTESIANPOINT((0.,0.,0.));
#16=IFCAXIS2PLACEMENT3D(#15,#14,#12);
#17=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-5,#16,$);
#18=IFCPROJECT('DU01',#3,'DegreeUnitsProject',$,$,$,$,(#17),#11);
#19=IFCLOCALPLACEMENT($,#16);
#20=IFCSITE('DU02',#3,'Site',$,$,#19,$,$,.ELEMENT.,$,$,$,$,$);
#21=IFCRELAGGREGATES('DU03',#3,$,$,#18,(#20));
#22=IFCBUILDING('DU04',#3,'Building',$,$,#19,$,$,.ELEMENT.,$,$,$);
#23=IFCRELAGGREGATES('DU05',#3,$,$,#20,(#22));
#24=IFCBUILDINGSTOREY('DU06',#3,'Floor',$,$,#19,$,$,.ELEMENT.,0.);
#25=IFCRELAGGREGATES('DU07',#3,$,$,#22,(#24));
#26=IFCAXIS2PLACEMENT2D(#27,#28);
#27=IFCCARTESIANPOINT((0.,0.));
#28=IFCDIRECTION((1.,0.));
#100=IFCRECTANGLEPROFILEDEF(.AREA.,$,#26,2.0,0.2);
#101=IFCEXTRUDEDAREASOLID(#100,#16,#14,3.0);
#102=IFCSHAPEREPRESENTATION(#17,'Body','SweptSolid',(#101));
#103=IFCPRODUCTDEFINITIONSHAPE($,$,(#102));
#104=IFCWALLSTANDARDCASE('DW01',#3,'DegreeWall',$,$,#19,#103,$);
#105=IFCRELCONTAINEDINSPATIALSTRUCTURE('DR01',#3,$,$,(#104),#24);
""" + FOOTER


def seed_v2_rich_materials():
    """IfcSurfaceStyleRendering with all colour/specular properties."""
    return BASE_ENTITIES + """\
#100=IFCRECTANGLEPROFILEDEF(.AREA.,$,#23,2.0,0.2);
#101=IFCEXTRUDEDAREASOLID(#100,#13,#11,3.0);
#102=IFCCOLOURRGB($,0.8,0.2,0.1);
#103=IFCCOLOURRGB($,0.1,0.8,0.2);
#104=IFCCOLOURRGB($,0.2,0.1,0.8);
#105=IFCCOLOURRGB($,0.9,0.9,0.9);
#106=IFCSURFACESTYLERENDERING(#102,0.2,IFCNORMALISEDRATIOMEASURE(0.8),$,#103,#104,#105,IFCSPECULAREXPONENT(32.0),.BLINN.);
#107=IFCSURFACESTYLE('RichMat',.BOTH.,(#106));
#108=IFCPRESENTATIONSTYLEASSIGNMENT((#107));
#109=IFCSTYLEDITEM(#101,(#108),$);
#110=IFCSHAPEREPRESENTATION(#14,'Body','SweptSolid',(#101));
#111=IFCPRODUCTDEFINITIONSHAPE($,$,(#110));
#112=IFCWALLSTANDARDCASE('RM01',#3,'RichMaterialWall',$,$,#16,#111,$);
#113=IFCRELCONTAINEDINSPATIALSTRUCTURE('RC10',#3,$,$,(#112),#21);
"""


SEEDS_V2 = {
    "v2_revolved_solid": seed_v2_revolved_solid,
    "v2_swept_disk": seed_v2_swept_disk,
    "v2_trimmed_curve": seed_v2_trimmed_curve,
    "v2_composite_curve": seed_v2_composite_curve,
    "v2_ishape": seed_v2_ishape,
    "v2_boolean_ext_diff": seed_v2_boolean_ext_diff,
    "v2_face_surface": seed_v2_face_surface,
    "v2_shell_surface": seed_v2_shell_surface,
    "v2_degree_units": seed_v2_degree_units,
    "v2_rich_materials": seed_v2_rich_materials,
}


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "ifc_seeds_v2"
    os.makedirs(outdir, exist_ok=True)

    for name, gen in SEEDS_V2.items():
        content = gen()
        # Add header/footer if not already present (degree_units has its own)
        if not content.startswith("ISO-10303-21"):
            content = HEADER + content + FOOTER

        path = os.path.join(outdir, f"seed_{name}.ifc")
        with open(path, "w") as f:
            f.write(content)
        print(f"  {path} ({len(content)} bytes)")

    print(f"\nGenerated {len(SEEDS_V2)} IFC seed files in {outdir}/")


if __name__ == "__main__":
    main()
