"""Parent-only read-only Unreal inspection. No asset/map mutation; output stays in /tmp."""
import hashlib
import json
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

PRIMARY=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary').resolve()
assert Path(ue.Paths.project_dir()).resolve()==PRIMARY, 'Exact primary checkout required'
assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before inspection'
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
bp=ue.load_asset('/Game/Puzzles/BP_CrystalLock');assert bp

def vec(v):return [float(v.x),float(v.y),float(v.z)]
def bound(o):
    b=o.get_bounds()
    return {'origin':vec(b.origin),'extent':vec(b.box_extent),'dimensions':[2*v for v in vec(b.box_extent)]}
def graph_snapshot():return {g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
graphs=graph_snapshot()
rows=[]
for actor in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
    if actor.get_class()!=bp.generated_class():continue
    root=actor.static_mesh_component;mesh=root.get_editor_property('static_mesh')
    center,extent=actor.get_actor_bounds(False)
    rows.append({'path':actor.get_path_name(),'label':actor.get_actor_label(),
        'level':actor.get_level().get_outermost().get_name(),
        'Brazier':bool(actor.get_editor_property('Brazier')),'Lit':bool(actor.get_editor_property('Lit')),
        'Enabled':bool(actor.get_editor_property('Enabled')),'LockSlot':int(actor.get_editor_property('LockSlot')),
        'tags':[str(t) for t in actor.tags],'actor_location':vec(actor.get_actor_location()),
        'actor_scale':vec(actor.get_actor_scale3d()),'actor_rotation':str(actor.get_actor_rotation()),
        'root_mesh':mesh.get_path_name() if mesh else None,'mesh_local_bounds':bound(mesh) if mesh else None,
        'world_origin':vec(center),'world_dimensions':[2*v for v in vec(extent)],
        'root_relative_location':vec(root.get_editor_property('relative_location')),
        'root_relative_scale':vec(root.get_editor_property('relative_scale3d')),
        'root_visible':bool(root.get_editor_property('visible')),
        'root_collision_profile':str(root.get_collision_profile_name()),
        'root_collision_enabled':str(root.get_collision_enabled()),
        'root_materials':[m.get_path_name() if m else None for m in root.get_materials()],
        'root_overrides':[m.get_path_name() if m else None for m in root.get_editor_property('override_materials')]})
sds=ue.get_engine_subsystem(ue.SubobjectDataSubsystem);lib=ue.SubobjectDataBlueprintFunctionLibrary
components=[]
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    d=lib.get_data(h);o=lib.get_object_for_blueprint(d,bp)
    components.append({'variable':str(lib.get_variable_name(d)),'object':o.get_path_name() if o else None,
        'class':o.get_class().get_name() if o else None,'root_actor':bool(lib.is_root_actor(d))})
g=BP.get_graph(bp,'ApplyLock');assert g
report={'project':str(PRIMARY),'editor_world':world.get_outermost().get_name(),
    'actors':rows,'blueprint_components':components,'graphs':graphs,
    'apply_graph_sha256':hashlib.sha256(graphs['ApplyLock'].encode()).hexdigest(),
    'presentation_node_types':{q:[str(t) for t in BP.find_node_types(g,q)] for q in ['CreateDynamicMaterialInstance','SetScalarParameterValue','SetVisibility']}}
output=Path(globals().get('ARGS',{}).get('report','/tmp/hc-a4-crystal-lock/unreal-inspection.json'))
assert output.resolve().is_relative_to(Path('/tmp').resolve()), 'Inspection output must be external'
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
RESULT={'report':str(output),'editor_world':report['editor_world'],'actors':rows,
    'apply_graph_sha256':report['apply_graph_sha256'],'blueprint_components':components,
    'presentation_node_types':report['presentation_node_types']}
