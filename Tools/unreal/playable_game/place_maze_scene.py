import gzip
import json
import unreal as ue
from editor_toolset.toolsets.actor import ActorTools

assert not ue.EditorLevelLibrary.get_pie_worlds(True)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level('/Game/Maps/L_Maze')
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
hz=ue.GameplayStatics.get_streaming_level(world,'L_Maze_HZ')
assert hz and hz.get_loaded_level()
ue.EditorLevelUtils.make_level_current(hz)
assert world.get_outermost().get_name()=='/Game/Maps/L_Maze'
scene=json.loads(gzip.decompress((ROOT/'SourceArt/HC/MazeIntegration/scene.json.gz').read_bytes()))
base='/Game/Puzzles/Art/MazeIntegration'
tag='PlayableMazeScene'
start=ARGS.get('start',0)
end=ARGS.get('end',len(scene['components']))
tools=ue.AssetToolsHelpers.get_asset_tools()
materials={}

def material(record):
    source=record.get('material')
    tint=record.get('tint',record.get('color',[1,1,1,1]))
    parent=ue.load_asset(source) if source else None
    if parent and not record.get('tint'):
        return parent
    if not parent:
        parent=ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock') if record.get('tint') else ue.load_asset('/Engine/BasicShapes/BasicShapeMaterial')
    key=(parent.get_path_name(),tuple(round(c,4) for c in tint))
    if key in materials:return materials[key]
    suffix='_'.join(str(round(c*10000)) for c in tint[:3])
    name='MI_MazeTint_'+suffix+('_Style' if record.get('tint') else '_Flat')
    path=base+'/Materials/'+name
    result=ue.load_asset(path) or tools.create_asset(name,base+'/Materials',ue.MaterialInstanceConstant,ue.MaterialInstanceConstantFactoryNew())
    ue.MaterialEditingLibrary.set_material_instance_parent(result,parent)
    ue.MaterialEditingLibrary.set_material_instance_vector_parameter_value(result,'Tint' if record.get('tint') else 'Color',ue.LinearColor(*tint))
    ue.MaterialEditingLibrary.update_material_instance(result)
    assert ue.EditorAssetLibrary.save_loaded_asset(result,False)
    materials[key]=result
    return result

def transform(record):
    pitch,yaw,roll=record['rotation']
    return ue.Transform(location=ue.Vector(*record['location']),rotation=ue.Rotator(pitch=pitch,yaw=yaw,roll=roll),scale=ue.Vector(*record['scale']))

def spawn(cls,index,record):
    tr=transform(record)
    actor=actors.spawn_actor_from_class(cls,tr.translation,tr.rotation.rotator())
    assert actor and actor.get_level().get_outermost().get_name()=='/Game/Hazards/L_Maze_HZ'
    actor.set_actor_label('MazeScene_'+str(index))
    actor.set_editor_property('tags',[ue.Name(tag),ue.Name('MazeScene_'+str(index))])
    actor.set_folder_path('Adventure/Maze')
    actor.set_actor_scale3d(tr.scale3d)
    return actor

for candidate in actors.get_all_level_actors():
    if candidate.actor_has_tag(tag) and candidate.get_class() == ue.Actor.static_class() and not candidate.get_component_by_class(ue.HierarchicalInstancedStaticMeshComponent):
        actors.destroy_actor(candidate)
existing={a.get_actor_label() for a in actors.get_all_level_actors() if a.actor_has_tag(tag)}
report={'start':start,'end':end,'actors':0,'instances':0,'colliding_hidden_meshes':0}
for index,record in enumerate(scene['components']):
    if not start<=index<end or 'MazeScene_'+str(index) in existing:continue
    kind=record['kind']
    if kind=='point':
        actor=spawn(ue.PointLight,index,record)
        light=actor.get_component_by_class(ue.PointLightComponent)
        light.set_mobility(ue.ComponentMobility.MOVABLE)
        light.set_editor_property('intensity_units',ue.LightUnits.CANDELAS)
        light.set_editor_property('intensity',record['intensity'])
        light.set_editor_property('attenuation_radius',record['radius'])
        light.set_light_color(ue.LinearColor(*record['color']))
        light.set_editor_property('cast_shadows',record['shadow'])
        light.set_editor_property('max_draw_distance',5000.0)
        light.set_editor_property('max_distance_fade_range',1250.0)
    elif kind=='instanced':
        actor=spawn(ue.Actor,index,{'location':[0,0,0],'rotation':[0,0,0],'scale':[1,1,1]})
        component=ActorTools.add_component(actor,ue.HierarchicalInstancedStaticMeshComponent.static_class(),'MazeRocks')
        assert component
        component.set_mobility(ue.ComponentMobility.STATIC)
        component.set_static_mesh(ue.load_asset(record['mesh']))
        component.set_material(0,material(record))
        component.set_editor_property('cast_shadow',record['shadow'])
        component.set_collision_profile_name('BlockAll' if record['collision'] else 'NoCollision')
        for instance in record['instances']:
            component.add_instance(transform(instance),True)
        report['instances']+=len(record['instances'])
    else:
        assert kind in ('static','procedural','blocker'),kind
        actor=spawn(ue.StaticMeshActor,index,record)
        component=actor.static_mesh_component
        component.set_mobility(ue.ComponentMobility.STATIC)
        if kind=='blocker':
            mesh=ue.load_asset('/Engine/BasicShapes/Cube')
            actor.set_actor_scale3d(ue.Vector(*(n/50 for n in record['extent'])))
            actor.set_actor_hidden_in_game(True)
        else:
            mesh=ue.load_asset(record['mesh']) if kind=='static' else ue.load_asset(base+f'/Meshes/SM_Maze_{index:04}')
            assert mesh,(index,record['name'])
        component.set_static_mesh(mesh)
        if kind=='procedural':
            component.set_material(0,ue.load_asset(base+'/Materials/'+('M_MazeVertexGlow' if record.get('glow') else 'M_MazeVertexLit')))
        elif kind=='static':
            component.set_material(0,material(record))
        component.set_editor_property('cast_shadow',record.get('shadow',False))
        component.set_collision_profile_name('BlockAll' if record.get('collision',kind=='blocker') else 'NoCollision')
        if not record.get('visible',True):
            actor.set_actor_hidden_in_game(True)
            if record.get('collision'):report['colliding_hidden_meshes']+=1
    report['actors']+=1
assert ue.EditorLoadingAndSavingUtils.save_packages([hz.get_loaded_level().get_outermost()],False)
RESULT=report
(QUEUE/f'maze-place-{start}-{end}.json').write_text(json.dumps(report,indent=2))

