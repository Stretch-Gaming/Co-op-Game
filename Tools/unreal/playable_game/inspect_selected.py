import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
report={}
for path,names in ARGS.get('graphs',{}).items():
    bp=ue.load_asset(path)
    report[path]={name:BP.read_graph_dsl(BP.get_graph(bp,name)) for name in names}
for path in ARGS.get('maps',[]):
    assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level(path)
    report[path]=[{'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'level':a.get_level().get_outermost().get_name(),'location':str(a.get_actor_location()),'tags':str(a.tags)} for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()]
(QUEUE/'focused-inspection.json').write_text(json.dumps(report,indent=2))
RESULT=report if not ARGS.get('maps') else {'report':'focused-inspection.json'}
