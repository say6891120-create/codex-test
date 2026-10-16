"""Parametric toothbrush exterior concept, mm; not production tooling geometry."""
from pathlib import Path
import json
import math
import cadquery as cq

OUT = Path(__file__).resolve().parent
parts = []
def add(name, shape):
    solid = shape.val() if isinstance(shape, cq.Workplane) else shape
    assert solid.isValid(), name
    assert solid.Volume() > 0, name
    parts.append((name, solid))
    return solid

# Body: rounded elliptical section, gently varying grip width, closed exterior.
body = (cq.Workplane('XY').workplane(offset=3).ellipse(12,10)
        .workplane(offset=12).ellipse(12.5,10.5)
        .workplane(offset=85).ellipse(12,10)
        .workplane(offset=32).ellipse(10,9)
        .workplane(offset=13).ellipse(7,6.5).loft())
add('Handle_exterior', body)
add('Bottom_cap', cq.Workplane('XY').ellipse(12,10).extrude(2.8))
add('Upper_trim', cq.Workplane('XY').workplane(offset=145.2).ellipse(7,6.5).extrude(2))
neck = (cq.Workplane('XY').workplane(offset=147.4).ellipse(6.8,6.3)
        .workplane(offset=12).ellipse(4,4)
        .workplane(offset=28).ellipse(3.2,3.2).loft())
add('Replaceable_head_neck',neck)
# Brushing head is a rounded capsule, lying in XZ, front faces toward negative Y.
head = cq.Workplane('XZ',origin=(0,0,198)).slot2D(27,10,angle=90).extrude(4,both=True)
add('Brush_head',head)
# Forty-two individual bristle tufts on the front; length varies toward edges.
for row in range(7):
    z = 188.5 + row*3.1
    for col in range(3):
        x = (col-1)*2.7
        length = 6.5 if col==1 else 7.2
        tuft=cq.Solid.makeCylinder(0.85,length,cq.Vector(x,-4,z),cq.Vector(0,-1,0))
        add(f'Bristle_tuft_{row}_{col}',tuft)
# Front circular power button and three status LEDs, separate geometric solids.
add('Power_button',cq.Solid.makeCylinder(3.4,1.6,cq.Vector(0,-10.1,111),cq.Vector(0,-1,0)))
for i in range(3):
    add(f'Status_LED_{i+1}',cq.Solid.makeCylinder(.65,.7,cq.Vector(0,-10.1,93-i*4),cq.Vector(0,-1,0)))
# Charging base, a distinct solid with a shallow recess beneath the handle.
base = cq.Workplane('XY').workplane(offset=-15).circle(19).extrude(14.8)
base = base.edges('%Circle').fillet(2)
base = base.cut(cq.Workplane('XY').workplane(offset=-2).ellipse(12.8,10.8).extrude(3))
add('Charging_base',base)
assembly=cq.Assembly(name='Electric_toothbrush_concept_mm')
for name, solid in parts:
    color = cq.Color(.93,.92,.88)
    if 'trim' in name.lower(): color = cq.Color(.67,.61,.50)
    if 'Bristle' in name: color = cq.Color(.51,.80,.70)
    if 'LED' in name: color=cq.Color(.60,.85,.90)
    assembly.add(solid,name=name,color=color)
step=OUT/'electric_toothbrush.step'
assembly.export(str(step))
restored = cq.importers.importStep(str(step))
solids = restored.solids().vals()
assert len(solids)==len(parts),(len(solids),len(parts))
assert all(s.isValid() and s.Volume()>0 for s in solids)
expected=sum(s.Volume() for _,s in parts)
actual=sum(s.Volume() for s in solids)
assert math.isclose(actual,expected,rel_tol=1e-6)
bounds=restored.val().BoundingBox()
report={'units':'mm','solid_count':len(solids),'all_solids_valid':True,'volume_roundtrip_pass':True,'size_mm':{'x':round(bounds.xlen,3),'y':round(bounds.ylen,3),'z':round(bounds.zlen,3)},'step_bytes':step.stat().st_size,'scope':'Exterior concept assembly; no motor, battery, waterproofing, internal fittings or tooling validation.'}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
