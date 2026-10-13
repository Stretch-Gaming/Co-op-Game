"""Original HC-A4 crystal lock; authored in Blender, CC0 1.0 Universal.

Run in a live Blender with importlib, or in a separate Blender process:
    blender -b --factory-startup --python build_crystal_lock.py -- /tmp/hc-a4-new --repo <repo>
Run only in a dedicated external working file; save your existing scene first.
Live use: create/switch the working scene in a separate MCP call before building.
Candidates stay outside the repository; only chosen A is delivered.
"""
import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

NAME = 'SM_CrystalLock'
SLOTS = ['M_CrystalLockStone', 'M_CrystalLockCrystal']
TARGET = Vector((0.8, 0.8, 1.0))


def kit_at(repo):
    spec = importlib.util.spec_from_file_location('hc_a4_asset_kit', Path(repo)/'Tools/blender/asset_kit.py')
    kit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kit)
    return kit


def material(name, color, roughness, kit):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    p = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = kit.hex_rgba(color)
    p.inputs['Roughness'].default_value = roughness
    mat.diffuse_color = kit.hex_rgba(color)
    return mat


def set_lit(mat, lit, kit):
    p = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    color = '#3FD0C9' if lit else '#263644'
    p.inputs['Base Color'].default_value = kit.hex_rgba(color)
    p.inputs['Emission Color'].default_value = kit.hex_rgba('#3FD0C9')
    p.inputs['Emission Strength'].default_value = .8 if lit else 0.0
    mat.diffuse_color = kit.hex_rgba(color)


def loft(name, rings, mat, kit, bevel=0.012, segments=2):
    count = len(rings[0])
    vertices = [tuple(v) for ring in rings for v in ring]
    faces = [tuple(reversed(range(count)))]
    for j in range(len(rings)-1):
        for i in range(count):
            k = (i+1) % count
            faces.append((j*count+i, j*count+k, (j+1)*count+k, (j+1)*count+i))
    faces.append(tuple((len(rings)-1)*count+i for i in range(count)))
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    kit.chunky_bevel(obj, width=bevel, segments=segments, angle_deg=25, smooth=False)
    return obj


def octagonal(half, z, clip=0.20, dx=0.0, dy=0.0):
    c = half*(1-clip)
    return [(dx+x, dy+y, z) for x,y in [(-c,-half),(c,-half),(half,-c),(half,c),(c,half),(-c,half),(-half,c),(-half,-c)]]


def crystal(name, width, bottom, top, offset, mat, kit):
    height = top-bottom
    r = width/2
    return loft(name, [
        octagonal(r*.64, bottom, .38, *offset),
        octagonal(r, bottom+height*.22, .38, offset[0]-.015, offset[1]+.008),
        octagonal(r*.91, bottom+height*.74, .38, offset[0]+.012, offset[1]-.01),
        octagonal(r*.32, top-.06, .38, offset[0]-.035, offset[1]+.005),
        octagonal(r*.19, top, .38, offset[0]-.028, offset[1]+.009),
    ], mat, kit, bevel=.014)


def bounds(obj):
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return Vector([min(v[i] for v in points) for i in range(3)]), Vector([max(v[i] for v in points) for i in range(3)])


def build(repo, candidate='A'):
    scene=bpy.context.scene
    if not scene.name.startswith('HC_A4_'):
        raise RuntimeError('Build only in a dedicated HC_A4_ working scene')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    return _build(repo,candidate,scene)


def _build(repo, candidate, scene):
    kit = kit_at(repo)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    stone = material(SLOTS[0], '#6B6169', .86, kit)
    gem = material(SLOTS[1], '#263644', .32, kit)
    set_lit(gem, False, kit)
    parts = []
    parts.append(loft('Foot', [octagonal(.35,0),octagonal(.4,.055),octagonal(.4,.17),octagonal(.35,.23,dx=.007,dy=-.003)], stone, kit, .019, 1))
    parts.append(loft('CarvedSocket', [octagonal(.285,.19),octagonal(.325,.235),octagonal(.27,.37,dx=.01,dy=.008)], stone, kit, .025, 1))
    # One broad captive crystal differentiates this mechanism from HZ's natural clusters.
    if candidate == 'A':
        parts.append(crystal('CaptiveCrystal', .44, .255, 1.0, (0,.0), gem, kit))
    else:
        for i,(width,x,y,top) in enumerate([(.25,0,.075,1.0),(.20,-.175,-.015,.76),(.18,.17,-.04,.71)]):
            parts.append(crystal('NarrowCrystal'+str(i),width,.25,top,(x,y),gem,kit))
    # Four broad, slightly canted stone teeth make a visibly authored retaining socket.
    for i,(x,y,rz) in enumerate([(-.235,0,-6),(.245,.025,5),(.0,.235,-3),(.02,-.24,7)]):
        tooth = kit.chunky_block('RetainingTooth'+str(i),size=(.16,.15,.27),bevel=.022,wobble=.008,seed=105+i,material=stone)
        tooth.location = (x,y,.405)
        tooth.rotation_euler.z = math.radians(rz)
        parts.append(tooth)
    # A large carved diamond plaque on the front echoes the style frame's altar carving.
    plaque = kit.chunky_block('DiamondPlaque',size=(.16,.045,.16),bevel=.012,wobble=0,material=stone)
    plaque.rotation_euler.y = math.radians(45)
    plaque.location = (0,-.392,.13)
    parts.append(plaque)
    inset = kit.chunky_block('DiamondInlay',size=(.078,.017,.078),bevel=.007,wobble=0,material=gem)
    inset.rotation_euler.y = math.radians(45)
    inset.location = (0,-.418,.13)
    parts.append(inset)
    obj = kit.join(parts, NAME+'_'+candidate)
    # Stable semantic slots even when Blender joins parts with different local slot lists.
    old = list(obj.data.materials)
    indices = [SLOTS.index(old[p.material_index].name) for p in obj.data.polygons]
    obj.data.materials.clear()
    for m in (stone,gem): obj.data.materials.append(m)
    for p,index in zip(obj.data.polygons,indices): p.material_index=index
    world = obj.matrix_world.copy()
    for v in obj.data.vertices: v.co = world @ v.co
    obj.matrix_world = Matrix.Identity(4)
    lo,hi = bounds(obj)
    # Match the authored greybox's world envelope exactly, with a floor contact pivot.
    for v in obj.data.vertices:
        v.co = Vector(((v.co.x-(lo.x+hi.x)/2)*TARGET.x/(hi.x-lo.x),
                       (v.co.y-(lo.y+hi.y)/2)*TARGET.y/(hi.y-lo.y),
                       (v.co.z-lo.z)*TARGET.z/(hi.z-lo.z)))
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj['source_issue']='https://github.com/StretchGaming/Co-op-Game/issues/105'
    obj['license']='CC0 1.0 Universal; original authored geometry'
    obj['material_contract']='0 stone; 1 crystal; emission 0 when unlit, teal when Lit'
    return scene,obj


def clean_export(repo, obj, stage):
    stage=Path(stage);stage.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    if not scene.name.startswith('HC_A4_'):
        raise RuntimeError('Export only in a dedicated HC_A4_ working scene')
    spec=importlib.util.spec_from_file_location('hc_a4_cleanup',Path(repo)/'Tools/blender/cleanup_export.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.export_fbx([obj],stage/'chosen-input.fbx')
    argv=sys.argv[:]
    try:
        sys.argv=['cleanup_export.py','--',str(stage/'chosen-input.fbx'),str(stage/(NAME+'.fbx')),'--name',NAME,'--target-triangles','1999','--overwrite']
        spec=importlib.util.spec_from_file_location('hc_a4_cleanup',Path(repo)/'Tools/blender/cleanup_export.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.main()
    finally:sys.argv=argv
    visual=next(o for o in scene.objects if o.type=='MESH')
    # Keep semantic FBX slot names stable instead of Blender's import duplicate suffixes.
    canonical=[bpy.data.materials.get(name) for name in SLOTS]
    if not all(canonical): raise RuntimeError('Missing original preview materials')
    for i,mat in enumerate(canonical): visual.data.materials[i]=mat
    # One conservative tapered octagonal prism: 24 vertices, 44 triangles, no concavities.
    rings=[octagonal(.4,0,.07),octagonal(.4,.30,.07),octagonal(.24,1,.07)]
    vertices=[v for ring in rings for v in ring]
    faces=[tuple(reversed(range(8)))]
    for j in range(2):
        for i in range(8):
            k=(i+1)%8
            faces.append((j*8+i,j*8+k,(j+1)*8+k,(j+1)*8+i))
    faces.append(tuple(16+i for i in range(8)))
    mesh=bpy.data.meshes.new('UCX_'+NAME+'_00');mesh.from_pydata(vertices,[],faces);mesh.update()
    hull=bpy.data.objects.new('UCX_'+NAME+'_00',mesh);scene.collection.objects.link(hull)
    hull.display_type='WIRE';hull.hide_render=True
    mod.export_fbx([visual,hull],stage/(NAME+'.fbx'))
    # Only the isolated asset scene is serialized, leaving user's original scene untouched.
    if len(bpy.data.scenes)==1:
        bpy.ops.wm.save_as_mainfile(filepath=str(stage/'HC-A4_CrystalLock.blend'),copy=True,compress=True)
    else:
        bpy.data.libraries.write(str(stage/'HC-A4_CrystalLock.blend'),{scene},fake_user=True,compress=True)
    return scene,visual,hull


def inspect(obj):
    obj.data.calc_loop_triangles();lo,hi=bounds(obj)
    bm=bmesh.new();bm.from_mesh(obj.data)
    report={'name':obj.name,'triangles':len(obj.data.loop_triangles),'vertices':len(obj.data.vertices),
        'dimensions_cm':[round(v*100,5) for v in hi-lo],
        'bounds_min_cm':[round(v*100,5) for v in lo], 'bounds_max_cm':[round(v*100,5) for v in hi],
        'origin_cm':[round(v*100,5) for v in obj.location],'scale':list(obj.scale),
        'slots':[m.name.split('.')[0] if m else None for m in obj.data.materials],
        'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
        'signed_volume_cm3':bm.calc_volume(signed=True)*1e6,
        'uv_layers':list(obj.data.uv_layers.keys()),
        'finite_uvs':all(math.isfinite(c) for uv in obj.data.uv_layers for entry in uv.data for c in entry.uv)}
    bm.free();return report


def validate(stage):
    stage=Path(stage)
    scene=bpy.context.scene
    if not scene.name.startswith('HC_A4_'):
        raise RuntimeError('Reimport only in dedicated HC_A4_ working scene')
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(stage/(NAME+'.fbx')))
    visual=next(o for o in scene.objects if o.type=='MESH' and not o.name.startswith('UCX_'))
    hull=next(o for o in scene.objects if o.name.startswith('UCX_'))
    metrics=inspect(visual);collision=inspect(hull)
    bm=bmesh.new();bm.from_mesh(hull.data);bm.normal_update()
    points=[visual.matrix_world @ v.co for v in visual.data.vertices]
    # Convexity: every collision vertex must lie on/inside each outward face plane.
    planes=[(f.calc_center_median(),f.normal.copy()) for f in bm.faces]
    inside=lambda points:all((p-center).dot(normal)<=1e-5 for p in points for center,normal in planes)
    collision['convex']=inside([v.co for v in bm.verts])
    collision['contains_visual']=inside(points)
    bm.free()
    assert metrics['triangles']<2000 and metrics['nonmanifold_edges']==0 and metrics['degenerate_faces']==0
    assert metrics['signed_volume_cm3']>0 and metrics['finite_uvs']
    assert all(abs(a-b)<.001 for a,b in zip(metrics['dimensions_cm'],(80,80,100)))
    assert all(abs(a-b)<.001 for a,b in zip(metrics['bounds_min_cm'],(-40,-40,0)))
    assert [s.split('.')[0] for s in metrics['slots']]==SLOTS
    assert collision['nonmanifold_edges']==0 and collision['degenerate_faces']==0
    assert collision['signed_volume_cm3']>0 and collision['convex'] and collision['contains_visual']
    from io_scene_fbx.parse_fbx import parse
    root,_=parse(str(stage/(NAME+'.fbx')))
    settings=next(e for e in root.elems if e.id==b'GlobalSettings')
    props=next(e for e in settings.elems if e.id==b'Properties70')
    unit=float(next(e.props[-1] for e in props.elems if e.id==b'P' and e.props[0]==b'UnitScaleFactor'))
    assert unit==1.0
    with bpy.data.libraries.load(str(stage/'HC-A4_CrystalLock.blend'),link=False) as (src,dst):
        dst.scenes=list(src.scenes)
    blend_scene=dst.scenes[0]
    blend_obj=next(o for o in blend_scene.objects if o.type=='MESH' and not o.name.startswith('UCX_'))
    reopened=inspect(blend_obj)
    assert reopened['triangles']==metrics['triangles']
    assert all(abs(a-b)<.001 for a,b in zip(reopened['dimensions_cm'],metrics['dimensions_cm']))
    result={'blender_version':bpy.app.version_string,'fbx_unit_centimeters':unit,'fbx_reimport':'pass',
        'isolated_blend_reload':'pass','mesh':metrics,'collision':collision,
        'unreal_import':'pending','native_client_and_split_screen_15m_check':'pending'}
    (stage/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return scene,visual,hull


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',type=Path)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3])
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not bpy.app.background:parser.error('CLI entry is for a separate background Blender process; use dedicated-scene helpers in live MCP')
    if args.stage.exists() and any(args.stage.iterdir()):parser.error('Use a new empty external staging directory')
    if args.stage.resolve().is_relative_to(args.repo.resolve()):parser.error('Stage candidates outside the repository')
    bpy.context.scene.name='HC_A4_HeadlessWorking'
    _,obj=build(args.repo,'A');clean_export(args.repo,obj,args.stage);validate(args.stage)


if __name__=='__main__':main()
