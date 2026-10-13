"""Bake private full-maze geometry and obstacle primitives through the editor only."""
import gzip,hashlib,json,math,sys
sys.path.insert(0,str(HERE))
from context import *
from editor_toolset.toolsets.actor import ActorTools
lease(WORLD)
data=json.loads(gzip.decompress((QUEUE/'scene.json.gz').read_bytes()))
records=data['components'];layout=data['layout']
base='/Game/Puzzles/Art/MazeLevel/Meshes'
materials_base='/Game/Puzzles/EnvironmentConnection/Refresh_fd40cdeb/Materials/'
masters={key:ue.load_asset(materials_base+key) for key in ('M_MazeVertexLit','M_MazeVertexGlow')};assert all(masters.values())
ledger_path=QUEUE/'bake-ledger.json'
ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
def material(r):
    if r.get('material') and not r.get('tint'):
        source=r['material'];m=ue.load_asset(materials_base+'Source_'+hashlib.sha256(source.encode()).hexdigest()[:12]) or ue.load_asset(source)
    else:
        tint=r.get('tint',r.get('color',[1,1,1,1]));name='Tint_'+'_'.join(str(round(c*10000)) for c in tint[:3])+('_Style' if r.get('tint') else '_Flat')
        m=ue.load_asset(materials_base+name)
    assert m,(r['source_index'],r.get('material'),r.get('tint'));return m
def make_mesh(path,r,m):
    fingerprint=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    existing=ue.load_asset(path)
    if existing:
        assert ledger.get(path)==fingerprint,('Private mesh requires explicit reviewed rebuild',path)
        return existing
    buffers=ue.GeometryScriptSimpleMeshBuffers()
    buffers.vertices=[ue.Vector(*v) for v in r['vertices']];buffers.normals=[ue.Vector(*v) for v in r['normals']]
    buffers.uv0=[ue.Vector2D(*v) for v in r['uvs']];buffers.vertex_colors=[ue.LinearColor(*v) for v in r['vertex_colors']]
    t=r['triangles'];buffers.triangles=[ue.IntVector(*t[i:i+3]) for i in range(0,len(t),3)]
    dynamic=ue.DynamicMesh();ue.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buffers)
    options=ue.GeometryScriptCreateNewStaticMeshAssetOptions();options.enable_nanite=False
    options.enable_collision=r.get('collision',True);options.collision_mode=ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    mesh,outcome=ue.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,options);assert mesh,(path,outcome)
    mesh.set_material(0,m);assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
    ledger[path]=fingerprint;ledger_path.write_text(json.dumps(ledger,indent=2));return mesh
meshes={r['source_index']:make_mesh(base+f'/SM_MazeLevel_{r["source_index"]:04}',r,masters['M_MazeVertexGlow' if r.get('glow') else 'M_MazeVertexLit']) for r in records if r['kind']=='procedural'}
# A flat-topped, chamfered rock gives useful collision and a readable landing.
def rock_record():
    outline=[(-42,-50),(42,-50),(50,-42),(50,42),(42,50),(-42,50),(-50,42),(-50,-42)]
    rings=[[(x,y,-50) for x,y in outline],[(x,y,35) for x,y in outline],[(x*.90,y*.90,50) for x,y in outline]]
    faces=[list(reversed(rings[0])),rings[2]]
    for lo,hi in zip(rings,rings[1:]):
        for i in range(8):j=(i+1)%8;faces.append([lo[i],lo[j],hi[j],hi[i]])
    result={'vertices':[],'normals':[],'uvs':[],'vertex_colors':[],'triangles':[],'collision':True}
    for face in faces:
        a,b,c=face[:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)]
        n=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];length=math.sqrt(sum(x*x for x in n));n=[x/length for x in n]
        offset=len(result['vertices'])
        for v in face:result['vertices'].append(v);result['normals'].append(n);result['uvs'].append([v[0]/100,v[1]/100]);result['vertex_colors'].append([1,1,1,1])
        for i in range(1,len(face)-1):result['triangles'].extend([offset,offset+i,offset+i+1])
    return result
rock=make_mesh(base+'/SM_MazeTraversalRock',rock_record(),ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock'))
sub=ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
if sub.get_simple_collision_count(rock)==0:assert sub.add_simple_collisions(rock,ue.ScriptingCollisionShapeType.BOX)>=0
rock.get_editor_property('body_setup').set_editor_property('collision_trace_flag',ue.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
assert ue.EditorAssetLibrary.save_loaded_asset(rock,False)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level(WORLD);assert editor.set_current_level_by_name('L_WorldRoute_Test')
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_outermost().get_name()==WORLD
all_actors=list(actors.get_all_level_actors());old=[a for a in all_actors if a.actor_has_tag('SixRoundConnectionScene')]
assert len(old)==516,len(old)
remove=[a for a in all_actors if a.actor_has_tag('SixRoundWorld') and not a.actor_has_tag('SixRoundMining')
        and a.get_actor_label() not in ('MazeMouthFloor','MazeMouthWall150','MazeMouthWall500','ConnectionJoin_West','ConnectionJoin_East','SixRound_MouthSeal')
        and a.get_class().get_name() not in ('BP_SixRoundTrap_C',)]
# Dynamic hazards on the removed tubes or outside return cannot remain active.
obsolete={'SixRound_ReturnTrap_'+str(i) for i in range(8)}|{'SixRound_second_0_Trap'+str(i) for i in (8,9)}|{'SixRound_second_'+str(s)+'_Trap'+str(i) for s in (1,2,3) for i in range(4,8)}
remove+= [a for a in all_actors if a.get_actor_label() in obsolete and a not in remove]
kept=[a for a in all_actors if a not in old and a not in remove]
def signature(a):
    t=a.get_actor_transform();return (a.get_path_name(),tuple(getattr(t.translation,k) for k in ('x','y','z')),tuple(getattr(t.rotation,k) for k in ('x','y','z','w')),tuple(getattr(t.scale3d,k) for k in ('x','y','z')),tuple(str(t) for t in a.tags))
before=[signature(a) for a in kept];staged=[]
def spawn(cls,label,pos,yaw=0):
    a=actors.spawn_actor_from_class(cls,ue.Vector(*pos),ue.Rotator(yaw=yaw));assert a and a.get_level().get_outermost().get_name()==WORLD
    a.set_actor_label(label);a.set_folder_path('MazeLevel');staged.append(a);return a
def transform(r):
    pitch,yaw,roll=r['rotation'];return ue.Transform(location=ue.Vector(*r['location']),rotation=ue.Rotator(pitch=pitch,yaw=yaw,roll=roll),scale=ue.Vector(*r['scale']))
try:
    for r in records:
        kind=r['kind'];tr=transform(r)
        cls=ue.PointLight if kind=='point' else ue.Actor if kind=='instanced' else ue.StaticMeshActor
        a=spawn(cls,'MazeLevel_Source_'+str(r['source_index']),r['location']);a.set_actor_rotation(tr.rotation.rotator(),False);a.set_actor_scale3d(tr.scale3d)
        a.tags=[ue.Name('SixRoundConnectionScene'),ue.Name('SixRoundConnectionScene_'+str(r['source_index'])),ue.Name('MazeLevel.TeamSource')]
        if kind=='point':
            c=a.get_component_by_class(ue.PointLightComponent);c.set_mobility(ue.ComponentMobility.MOVABLE)
            c.set_editor_properties({'intensity_units':ue.LightUnits.CANDELAS,'intensity':r['intensity'],'attenuation_radius':r['radius'],'cast_shadows':r['shadow'],'max_draw_distance':5000.})
            c.set_light_color(ue.LinearColor(*r['color']))
        else:
            c=ActorTools.add_component(a,ue.HierarchicalInstancedStaticMeshComponent.static_class(),'MazeRocks') if kind=='instanced' else a.static_mesh_component
            c.set_mobility(ue.ComponentMobility.STATIC);c.set_static_mesh(meshes[r['source_index']] if kind=='procedural' else ue.load_asset(r['mesh']))
            c.set_material(0,masters['M_MazeVertexGlow' if r.get('glow') else 'M_MazeVertexLit'] if kind=='procedural' else material(r))
            c.set_collision_profile_name('BlockAll' if r.get('collision',False) else 'NoCollision');c.set_editor_property('cast_shadow',r.get('shadow',False))
            if kind=='instanced':
                for item in r['instances']:c.add_instance(transform(item),True)
        if not r.get('visible',True):a.set_actor_hidden_in_game(True)
    pieces=[p for cluster in layout['clusters'] for p in cluster['primitives']]+layout['shoulder_rubble']
    amber=ue.load_asset('/Game/Hazards/Art/SixRoundMaze/Materials/MI_SixRound_ClimbAmber');assert amber
    for p in pieces:
        if p['shape']=='climb_volume':
            cls=ue.load_asset('/Game/Hazards/Maze/BP_ClimbVolume').generated_class()
            a=spawn(cls,'MazeVariety_'+p['id'],p['location'],p['yaw']);box=a.get_component_by_class(ue.BoxComponent)
            box.set_box_extent(ue.Vector(*(x/2 for x in p['size'])));box.set_collision_profile_name('OverlapAllDynamic');box.set_collision_enabled(ue.CollisionEnabled.QUERY_ONLY);box.set_editor_property('generate_overlap_events',True)
        else:
            a=spawn(ue.StaticMeshActor,'MazeVariety_'+p['id'],p['location'],p['yaw']);a.static_mesh_component.set_mobility(ue.ComponentMobility.STATIC)
            a.static_mesh_component.set_static_mesh(rock if p['shape']=='rock' else ue.load_asset('/Engine/BasicShapes/Cube'))
            a.set_actor_scale3d(ue.Vector(*(x/100 for x in p['size'])));a.static_mesh_component.set_material(0,amber if p['material']=='amber' else ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock'))
            a.static_mesh_component.set_collision_profile_name('BlockAll' if p['collision'] else 'NoCollision')
        a.tags=[ue.Name('MazeLevel.Variety'),*[ue.Name(t) for t in p.get('tags',())]]
    assert [signature(a) for a in kept]==before
except Exception:
    for a in reversed(staged):actors.destroy_actor(a)
    raise
removed_labels=[a.get_actor_label() for a in remove]
for a in old+remove:assert actors.destroy_actor(a)
assert [signature(a) for a in kept]==before
save_level(next(l for l in ue.EditorLevelUtils.get_levels(world) if l.get_outermost().get_name()==WORLD))
report={'source_scenery':len(records),'private_meshes':len(meshes)+1,'variety_actors':len(pieces),
        'major_clusters':len(layout['clusters']),'gaps':len(layout['gaps']),'removed_old_scenery':len(old),
        'retired_additions':removed_labels,'preserved_actors':len(kept),'source_hall_b_restored':True,
        'source_sha256':data['source_sha256'],'native_collision_pending':True}
(QUEUE/'bake-scene.json').write_text(json.dumps(report,indent=2));RESULT=report
