"""Blender 5: clean a GLB/FBX to a static-mesh FBX, centimeter metadata, +Z up.
Usage: blender -b --python cleanup_export.py -- input.glb output.fbx --name SM_Name
       [--target-triangles 3000] [--source-unit auto|meters|centimeters]
       [--combine] [--overwrite]
Blender importers normalize FBX unit/axis metadata and GLB meters/Y-up into
Blender meters/Z-up. 'auto' trusts that metadata; override only for mislabelled files.
Explicit unit overrides reinterpret the raw source coordinates, correcting bad
unit metadata (FBX metadata is inspected; GLB is always specified in meters).
Materials and UVs are retained. Decimation can distort UVs: rebake/check afterwards.
Armatures/animation are deliberately rejected; this is for static props only.
"""
import argparse, sys, json, re
from pathlib import Path
import bpy, bmesh
from mathutils import Vector


def triangles(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def bounds(objects):
    points = [obj.matrix_world @ Vector(c) for obj in objects for c in obj.bound_box]
    return Vector([min(p[a] for p in points) for a in range(3)]), Vector([max(p[a] for p in points) for a in range(3)])


def recalc(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()


def export_fbx(objects, path):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0
    # Blender coordinates are meters; exporter multiplies vertex coordinates by
    # 100 and writes UnitScaleFactor=1 (centimeters). Do NOT also scale objects 100x.
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
        object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE', axis_forward='-Y', axis_up='Z',
        use_space_transform=True, bake_space_transform=False,
        use_mesh_modifiers=True, mesh_smooth_type='FACE', use_triangles=True,
        add_leaf_bones=False, bake_anim=False, path_mode='RELATIVE', embed_textures=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path); p.add_argument('output', type=Path)
    p.add_argument('--name', required=True)
    p.add_argument('--target-triangles', type=int)
    p.add_argument('--source-unit', choices=['auto','meters','centimeters'], default='auto')
    p.add_argument('--combine', action='store_true'); p.add_argument('--overwrite', action='store_true')
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not args.input.is_file(): p.error('Input does not exist')
    if args.input.resolve() == args.output.resolve(): p.error('Input/output must differ')
    if args.output.suffix != '.fbx': p.error('Output extension must be lowercase .fbx')
    if not re.fullmatch(r'SM_[A-Za-z][A-Za-z0-9_]*', args.name): p.error('Name must be SM_Name (AGENTS.md static mesh prefix)')
    if args.output.stem != args.name: p.error('Output filename stem must match --name')
    if args.output.exists() and not args.overwrite: p.error('Output exists; pass --overwrite')
    if args.target_triangles is not None and args.target_triangles < 12: p.error('Target must be >= 12')
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    ext = args.input.suffix.lower()
    if ext in ('.glb','.gltf'): bpy.ops.import_scene.gltf(filepath=str(args.input))
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=str(args.input), use_custom_normals=True)
    else: p.error('Input must be GLB, glTF or FBX')
    if any(o.type=='ARMATURE' for o in bpy.context.scene.objects): p.error('Rigged asset rejected: static props only')
    objs = [o for o in bpy.context.scene.objects if o.type=='MESH']
    if not objs: p.error('No meshes in input')
    # Freeze complete world matrices before removing parent hierarchy.
    for o in objs:
        matrix = o.matrix_world.copy(); o.parent=None; o.matrix_world=matrix
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    override_factor=1.0
    if args.source_unit!='auto':
        metadata_meters=1.0  # GLB spec
        if ext=='.fbx':
            from io_scene_fbx.parse_fbx import parse
            root,_=parse(str(args.input))
            node=next(e for e in root.elems if e.id==b'GlobalSettings')
            props=next(e for e in node.elems if e.id==b'Properties70')
            unit=next((v.props[-1] for v in props.elems if v.id==b'P' and v.props[0]==b'UnitScaleFactor'),1.0)
            metadata_meters=float(unit)/100.0
        if metadata_meters<=0: p.error('Invalid FBX unit scale')
        desired_meters=1.0 if args.source_unit=='meters' else .01
        override_factor=desired_meters/metadata_meters
        for o in objs:
            o.location *= override_factor
            for v in o.data.vertices: v.co *= override_factor
    if args.combine and len(objs)>1:
        bpy.ops.object.join(); objs=[bpy.context.object]
    before=sum(triangles(o) for o in objs)
    counts=[triangles(o) for o in objs]
    allocations=None
    if args.target_triangles and before>args.target_triangles:
        if args.target_triangles < 12*len(objs): p.error('Too many mesh parts for target; use --combine')
        remaining=args.target_triangles-12*len(objs)
        allocations=[12+int(remaining*c/before) for c in counts]
    for idx,o in enumerate(objs):
        o.name=args.name if len(objs)==1 else f'{args.name}_{idx+1:02d}'
        bpy.context.view_layer.objects.active=o
        if allocations and triangles(o)>allocations[idx]:
            budget=allocations[idx]
            # Leave 2% margin: Blender ratios refer to faces, not exact triangles.
            dec=o.modifiers.new('OptionalTriangleBudget','DECIMATE')
            dec.ratio=max(.00001,(budget*.98)/triangles(o)); dec.use_collapse_triangulate=True
            bpy.ops.object.modifier_apply(modifier=dec.name)
            if triangles(o)>budget: raise RuntimeError('Decimation exceeded target')
        recalc(o)
        tri=o.modifiers.new('ExportTriangles','TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=tri.name)
    lo,hi=bounds(objs); base=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    # One assembly pivot for multi-part props; all parts have origin at base-center.
    for o in objs:
        world=o.matrix_world.copy()
        for v in o.data.vertices: v.co=world@v.co-base
        o.matrix_world.identity()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    export_fbx(objs,args.output)
    lo,hi=bounds(objs)
    result={'input':str(args.input),'output':str(args.output),'source_unit':args.source_unit,
        'explicit_unit_correction_factor':override_factor,'triangles_before':before,'triangles_after':sum(triangles(o) for o in objs),
        'dimensions_cm':[round(x*100,4) for x in hi-lo], 'bounds_min_cm':[round(x*100,5) for x in lo],
        'pivot':'base center','fbx_unit':'centimeters','up_axis':'+Z','forward_axis':'-Y',
        'UV_warning':'Inspect UVs and rebake maps if decimated.' if allocations else None}
    args.output.with_suffix('.validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__': main()
