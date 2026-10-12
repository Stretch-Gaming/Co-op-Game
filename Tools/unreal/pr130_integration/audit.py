"""Read existing saved assembly and flare implementation; save no assets."""
import hashlib, json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ue.GameplayStatics.flush_level_streaming(world)
rows=[]
for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
    level=a.get_level().get_outermost().get_name()
    if not (a.actor_has_tag('SixRoundConnectionScene') or a.actor_has_tag('ConnectionDoor')): continue
    rows.append({'label':a.get_actor_label(),'level':level,'location':str(a.get_actor_location()),
                 'components':[{'name':c.get_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else None,
                                'materials':[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
                                'instance_count':c.get_instance_count() if isinstance(c,ue.InstancedStaticMeshComponent) else None}
                               for c in a.get_components_by_class(ue.StaticMeshComponent)]})
flare=ue.load_asset('/Game/Player/Tools/BP_Flare')
lib=ue.SubobjectDataBlueprintFunctionLibrary
sds=ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
components=[]
for h in sds.k2_gather_subobject_data_for_blueprint(flare):
    data=lib.get_data(h);obj=lib.get_object_for_blueprint(data,flare)
    if not isinstance(obj,ue.ActorComponent):continue
    props={}
    for name in ('relative_location','relative_scale3d','static_mesh','updated_component','initial_speed','max_speed','projectile_gravity_scale','sound','auto_activate'):
        try:props[name]=str(obj.get_editor_property(name))
        except Exception:pass
    components.append({'name':str(lib.get_variable_name(data)),'class':obj.get_class().get_name(),'props':props})
files=['Content/Puzzles/Test/SixRound/L_SixRound_Test.umap','Content/Puzzles/Test/SixRound/L_CaveEnvironment_Test.umap',
       'Content/Hazards/Test/SixRound/L_WorldRoute_Test.umap','Content/Player/Tools/BP_Flare.uasset',
       'Content/Hazards/L_Site01_HZ.umap','Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap',
       'Content/Shared/Style/M_Stylized.uasset']
report={'levels':[l.get_outermost().get_name() for l in ue.EditorLevelUtils.get_levels(world)],'maze_actors':rows,
        'flare_components':components,'flare_graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(flare)},
        'hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}}
(QUEUE/'baseline.json').write_text(json.dumps(report,indent=2))
RESULT={'levels':report['levels'],'maze_actors':len(rows),'flare_components':components,'report':'baseline.json'}
