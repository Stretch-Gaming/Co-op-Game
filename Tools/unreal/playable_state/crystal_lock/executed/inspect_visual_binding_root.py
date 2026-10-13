import unreal as ue,json
from pathlib import Path
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert Path(ue.Paths.project_dir()).resolve()==Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary') and not ue.EditorLevelLibrary.get_pie_worlds(True)
bp=ue.load_asset('/Game/Puzzles/BP_CrystalLock');sds=ue.get_engine_subsystem(ue.SubobjectDataSubsystem);lib=ue.SubobjectDataBlueprintFunctionLibrary
props=['static_mesh','relative_location','relative_scale3d','absolute_scale','visible','collision_enabled']
def row(o):
 if not isinstance(o,ue.StaticMeshComponent):return {'path':o.get_path_name() if o else None}
 r={'path':o.get_path_name(),'archetype':o.get_archetype().get_path_name() if hasattr(o,'get_archetype') else None}
 for p in props:
  try:
   v=o.get_editor_property(p);r[p]=v.get_path_name() if isinstance(v,ue.Object) else str(v)
  except Exception as e:r[p]=repr(e)
 return r
r={'templates':[],'actors':[],'graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}}
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
 d=lib.get_data(h)
 if str(lib.get_variable_name(d))=='HC_CrystalLockVisual':r['templates'].append({'variable':str(lib.get_variable_name(d)),'for_blueprint':row(lib.get_object_for_blueprint(d,bp)),'object':row(lib.get_object(d))})
for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
 if a.get_class()==bp.generated_class():r['actors'].append({'name':a.get_name(),'brazier':bool(a.get_editor_property('Brazier')),'components':[row(c) for c in a.get_components_by_class(ue.StaticMeshComponent)]})
Path('/tmp/hc-a4-crystal-lock/visual-binding-root.json').write_text(json.dumps(r,indent=2))
