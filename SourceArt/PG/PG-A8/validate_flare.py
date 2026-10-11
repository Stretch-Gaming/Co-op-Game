"""Fresh-process FBX/collision and PCM acceptance checks; optional finalization."""
import argparse
import json
import math
import sys
import wave
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector


def inspect_mesh(obj):
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = [min(v[a] for v in points)*100 for a in range(3)]
    hi = [max(v[a] for v in points)*100 for a in range(3)]
    obj.data.calc_loop_triangles()
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bad = sum(not e.is_manifold for e in bm.edges)
    volume = bm.calc_volume(signed=True)*1e6
    degenerate = sum(f.calc_area() < 1e-12 for f in bm.faces)
    bm.free()
    uv = obj.data.uv_layers.active
    assert uv and all(math.isfinite(v) for entry in uv.data for v in entry.uv)
    uv_values = [tuple(entry.uv) for entry in uv.data]
    assert len(set(uv_values)) > 4
    result = {'name':obj.name,'triangles':len(obj.data.loop_triangles),'vertices':len(obj.data.vertices),
              'bounds_min_cm':lo,'bounds_max_cm':hi,'dimensions_cm':[hi[a]-lo[a] for a in range(3)],
              'origin_cm':[v*100 for v in obj.location],'scale':list(obj.scale),
              'material_slots':[m.name for m in obj.data.materials],
              'nonmanifold_edges':bad,'degenerate_faces':degenerate,'signed_volume_cm3':volume,
              'uv_layer':uv.name,'finite_uvs':True}
    assert bad == 0 and degenerate == 0 and volume > 0, result
    assert all(abs(v) < 1e-5 for v in obj.location), result
    assert all(abs(v-1) < 1e-5 for v in obj.scale), result
    return result


def inspect_audio(path):
    with wave.open(str(path),'rb') as w:
        fmt = {'channels':w.getnchannels(),'sample_rate_hz':w.getframerate(),
               'bits_per_sample':w.getsampwidth()*8,'frames':w.getnframes(),'compression':w.getcomptype()}
        pcm = np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float64)
    assert fmt == {'channels':1,'sample_rate_hz':48000,'bits_per_sample':16,'frames':192000,'compression':'NONE'}
    seam = pcm[0]-pcm[-1]
    slopes = [pcm[-1]-pcm[-2], pcm[1]-pcm[0]]
    assert seam == 0 and slopes == [0,0]
    peak = max(abs(pcm)); rms = np.sqrt(np.mean(pcm**2))
    assert peak < 32767 and rms > 100
    # 10ms windows straddling the repeated seam retain comparable noise energy.
    seam_rms = float(np.sqrt(np.mean(np.concatenate((pcm[-240:],pcm[:240]))**2)))
    interior_rms = float(np.sqrt(np.mean(pcm[240:720]**2)))
    assert .5 < seam_rms/interior_rms < 1.5
    return {**fmt,'duration_seconds':len(pcm)/48000,'loop_value_delta_lsb':seam,
            'loop_adjacent_slopes_lsb':slopes,'clipped_samples':int(np.sum(abs(pcm)>=32767)),
            'dc_mean_lsb':float(np.mean(pcm)),'peak_dbfs':float(20*np.log10(peak/32768)),
            'rms_dbfs':float(20*np.log10(rms/32768)),
            'seam_10ms_rms_to_next_10ms_ratio':seam_rms/interior_rms,
            'audition':'Not performed in Unreal; source waveform/format/continuity verified only.'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--cleanup',type=Path,required=True)
    p.add_argument('--finalize',action='store_true')
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:]); folder=a.folder.resolve()
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(folder/'SM_HandFlare.fbx'))
    objects = [o for o in bpy.context.scene.objects if o.type=='MESH']
    if a.finalize:
        assert len(objects)==1 and objects[0].name=='SM_HandFlare'
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from build_flare import lathe
        visual=objects[0]
        collision=lathe('UCX_SM_HandFlare_00',[(0,3,0),(22,3,0)],visual.data.materials[0])
        # Smart UVs only for diagnostics; Unreal ignores collision material/UVs.
        bpy.ops.object.select_all(action='DESELECT'); collision.select_set(True)
        bpy.context.view_layer.objects.active=collision
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(); bpy.ops.object.mode_set(mode='OBJECT')
        sys.path.insert(0,str(a.cleanup.resolve().parent))
        from cleanup_export import export_fbx, recalc
        recalc(collision)
        export_fbx([visual,collision],folder/'SM_HandFlare.fbx')
        collision.hide_render=True
        collision.display_type='WIRE'
        visual['license']='Original PK work; CC0 1.0 Universal.'
        bpy.context.scene.unit_settings.system='METRIC'
        bpy.context.scene.unit_settings.length_unit='CENTIMETERS'
        bpy.ops.wm.save_as_mainfile(filepath=str(folder/'PG-A8_HandFlare.blend'))
        return
    assert {o.name for o in objects} == {'SM_HandFlare','UCX_SM_HandFlare_00'}
    metrics={o.name:inspect_mesh(o) for o in objects}
    mesh=metrics['SM_HandFlare']; collision=metrics['UCX_SM_HandFlare_00']
    assert mesh['triangles'] < 2000
    assert all(abs(v-e)<.001 for v,e in zip(mesh['dimensions_cm'],[6,6,22]))
    assert all(abs(v-e)<.001 for v,e in zip(mesh['bounds_min_cm'],[-3,-3,0]))
    assert mesh['material_slots']==['M_FlareMetal','M_FlareGrip','M_FlareBody','M_FlareAmber']
    # Every visual vertex lies in the 12-sided convex collision prism.
    visual=next(o for o in objects if o.name=='SM_HandFlare')
    for vertex in visual.data.vertices:
        point=visual.matrix_world @ vertex.co
        assert -.00001 <= point.z <= .22001
        for i in range(12):
            angle=2*math.pi*(i+.5)/12
            assert point.x*math.cos(angle)+point.y*math.sin(angle) <= .03*math.cos(math.pi/12)+1e-5
    col=next(o for o in objects if o.name=='UCX_SM_HandFlare_00')
    bm=bmesh.new(); bm.from_mesh(col.data)
    assert all(e.is_convex for e in bm.edges if e.is_manifold)
    bm.free()
    from io_scene_fbx.parse_fbx import parse
    root,_=parse(str(folder/'SM_HandFlare.fbx'))
    settings=next(e for e in root.elems if e.id==b'GlobalSettings')
    props=next(e for e in settings.elems if e.id==b'Properties70')
    units=next(v.props[-1] for v in props.elems if v.id==b'P' and v.props[0]==b'UnitScaleFactor')
    assert units==1.0
    bpy.ops.wm.open_mainfile(filepath=str(folder/'PG-A8_HandFlare.blend'))
    reopened = {o.name:inspect_mesh(o) for o in bpy.context.scene.objects if o.type=='MESH'}
    for name in metrics:
        for key, value in metrics[name].items():
            if key == 'signed_volume_cm3':
                assert math.isclose(reopened[name][key], value, rel_tol=1e-6)
            else:
                assert reopened[name][key] == value, (name, key)
    report={'blend_fresh_reopen':'pass','blender_version':bpy.app.version_string,'fbx_centimeter_UnitScaleFactor':units,
            'fresh_process_reimport':'pass','mesh':mesh,'collision':{**collision,'convex':True,'contains_visual':True},
            'audio':inspect_audio(folder/'SFX_Flare_Hiss_Loop.wav'),
            'unreal_import':'not run','style_map_split_screen_windows':'not run'}
    (folder/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
