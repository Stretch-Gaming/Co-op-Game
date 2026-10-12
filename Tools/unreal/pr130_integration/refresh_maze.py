"""Refresh scenery only. Keep six-round gameplay actors and placements intact."""
import gzip, hashlib, json, sys
sys.path.insert(0,str(HERE))
from context import *
from editor_toolset.toolsets.actor import ActorTools
from latest_scene import EXPECTED

target='/Game/Hazards/Test/SixRound/L_WorldRoute_Test'
require_lease(target+'.umap')
base='/Game/Puzzles/Art/PR130Maze'
scene=json.loads(gzip.decompress((QUEUE/'latest-sixround-scene.json.gz').read_bytes()))
assert scene['source_sha256']==EXPECTED
records=[r for r in scene['components'] if r['kind']!='excluded' and not(r['kind']=='procedural' and not r['triangles'])]
sys.path.insert(0,str(ROOT/'Tools/unreal/six_round/world'))
from scene_ops import inside_cut
records=[r for r in records if not(r['kind'] in ('static','point') and inside_cut(r['location']))]
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level(target)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
assert world.get_outermost().get_name()==target
assert editor.set_current_level_by_name('L_WorldRoute_Test')
old=[a for a in actors.get_all_level_actors() if a.actor_has_tag('SixRoundConnectionScene')]
assert len(old)==519, len(old)
preserved=[a for a in actors.get_all_level_actors() if a not in old]
def signature(a):
    t=a.get_actor_transform()
    return (a.get_path_name(),tuple(getattr(t.translation,k) for k in ('x','y','z')),
            tuple(getattr(t.rotation,k) for k in ('x','y','z','w')),
            tuple(getattr(t.scale3d,k) for k in ('x','y','z')),tuple(str(v) for v in a.tags),a.get_class().get_path_name())
before=[signature(a) for a in preserved]
materials_base='/Game/Puzzles/EnvironmentConnection/Refresh_fd40cdeb/Materials/'
masters={key:ue.load_asset(materials_base+key) for key in ('M_MazeVertexLit','M_MazeVertexGlow')}
assert all(masters.values())
def material(r):
    if r.get('material') and not r.get('tint'):
        source=r['material']
        # The existing refreshed preview's private copy is exact and can be reused.
        obj=ue.load_asset(materials_base+'Source_'+hashlib.sha256(source.encode()).hexdigest()[:12]) or ue.load_asset(source)
    else:
        tint=r.get('tint',r.get('color',[1,1,1,1]))
        name='Tint_'+'_'.join(str(round(c*10000)) for c in tint[:3])+('_Style' if r.get('tint') else '_Flat')
        obj=ue.load_asset(materials_base+name)
    assert obj,(r['source_index'],r.get('material'),r.get('tint'),r.get('color'))
    return obj
for r in records:
    if r['kind'] in ('static','instanced'):
        assert ue.load_asset(r['mesh']),r['mesh'];material(r)
mesh_report=[]
for r in records:
    if r['kind']!='procedural':continue
    path=base+f'/SM_PR130Maze_{r["source_index"]:04}'
    fingerprint=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    mesh=ue.load_asset(path)
    if not mesh:
        buffers=ue.GeometryScriptSimpleMeshBuffers()
        buffers.vertices=[ue.Vector(*v) for v in r['vertices']];buffers.normals=[ue.Vector(*v) for v in r['normals']]
        buffers.uv0=[ue.Vector2D(*v) for v in r['uvs']];buffers.vertex_colors=[ue.LinearColor(*v) for v in r['vertex_colors']]
        t=r['triangles'];buffers.triangles=[ue.IntVector(*t[i:i+3]) for i in range(0,len(t),3)]
        dynamic=ue.DynamicMesh();ue.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buffers)
        options=ue.GeometryScriptCreateNewStaticMeshAssetOptions();options.enable_nanite=False
        options.enable_collision=r.get('collision',False);options.collision_mode=ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        mesh,outcome=ue.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,options);assert mesh,(path,outcome)
        mesh.set_material(0,masters['M_MazeVertexGlow' if r.get('glow') else 'M_MazeVertexLit'])
        assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
    mesh_report.append({'path':path,'source_index':r['source_index'],'record_sha256':fingerprint})
meshes={row['source_index']:ue.load_asset(row['path']) for row in mesh_report}
def transform(r):
    pitch,yaw,roll=r['rotation'];loc=list(r['location']);loc[0]-=175
    return ue.Transform(location=ue.Vector(*loc),rotation=ue.Rotator(pitch=pitch,yaw=yaw,roll=roll),scale=ue.Vector(*r['scale']))
staged=[]
try:
    for r in records:
        kind=r['kind'];tr=transform(r)
        cls=ue.PointLight if kind=='point' else ue.Actor if kind=='instanced' else ue.StaticMeshActor
        a=actors.spawn_actor_from_class(cls,tr.translation,tr.rotation.rotator());assert a
        staged.append(a);assert a.get_level().get_outermost().get_name()==target
        a.set_actor_scale3d(tr.scale3d);a.set_actor_label('PR130_Staged_'+str(r['source_index']))
        a.tags=[ue.Name('SixRoundConnectionScene'),ue.Name('SixRoundConnectionScene_'+str(r['source_index'])),ue.Name('PR130.TeamMaze')]
        a.set_folder_path('Adventure/Maze')
        if kind=='point':
            c=a.get_component_by_class(ue.PointLightComponent);c.set_mobility(ue.ComponentMobility.MOVABLE)
            c.set_editor_properties({'intensity_units':ue.LightUnits.CANDELAS,'intensity':r['intensity'],
                                    'attenuation_radius':r['radius'],'cast_shadows':r['shadow'],'max_draw_distance':5000.})
            c.set_light_color(ue.LinearColor(*r['color']))
        else:
            c=ActorTools.add_component(a,ue.HierarchicalInstancedStaticMeshComponent.static_class(),'MazeRocks') if kind=='instanced' else a.static_mesh_component
            c.set_mobility(ue.ComponentMobility.STATIC)
            c.set_static_mesh(meshes[r['source_index']] if kind=='procedural' else ue.load_asset(r['mesh']))
            c.set_material(0,masters['M_MazeVertexGlow' if r.get('glow') else 'M_MazeVertexLit'] if kind=='procedural' else material(r))
            c.set_editor_property('cast_shadow',r.get('shadow',False))
            c.set_collision_profile_name('BlockAll' if r.get('collision',False) else 'NoCollision')
            if kind=='instanced':
                for item in r['instances']:c.add_instance(transform(item),True)
        if not r.get('visible',True):a.set_actor_hidden_in_game(True)
    assert [signature(a) for a in preserved]==before, 'Gameplay placement changed'
except Exception:
    for a in staged:assert actors.destroy_actor(a)
    raise
for a in old:assert actors.destroy_actor(a)
for r,a in zip(records,staged):a.set_actor_label('SixRoundConnectionScene_'+str(r['source_index']))
assert [signature(a) for a in preserved]==before
assert ue.EditorLoadingAndSavingUtils.save_packages([world.get_outermost()],False)
report={'source_capture':'SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/connection.json.gz','source_sha256':EXPECTED,
        'map':target,'old_scenery_actors':len(old),'new_scenery_actors':len(staged),'unchanged_gameplay_actors':len(preserved),
        'meshes':mesh_report,'cuts':'Existing six-round gap/solo-hall/doorway cuts retained; no new layout design',
        'original_sources_saved':False}
(QUEUE/'maze-refresh.json').write_text(json.dumps(report,indent=2))
RESULT={k:v for k,v in report.items() if k!='meshes'}
