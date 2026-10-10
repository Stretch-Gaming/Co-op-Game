import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT

from editor_toolset.toolsets.blueprint import ContainerType
owned={}
for folder,name,parent in [('/Game/Puzzles/Run','BP_RunCoordinator',ue.Actor),('/Game/Puzzles','BP_MapExit',ue.TriggerBox),('/Game/Puzzles/UI/Results','AC_RunResults',ue.ActorComponent)]:
 path=folder+'/'+name;bp=ue.load_asset(path) or BP.create(folder,name,parent.static_class());owned[name]=bp
co=owned['BP_RunCoordinator'];ex=owned['BP_MapExit'];ac=owned['AC_RunResults']
for bp,vs in [(co,[('SnapshotCommitted','bool'),('RestartInProgress','bool'),('CapturedCollected','int'),('CapturedAvailable','int'),('CompletionCount','int')]),(ex,[('ExitCommitted','bool'),('AllReady','bool'),('RequiredPlayers','int'),('ReadyPlayers','int')])]:
 for name,kind in vs:
  if name not in BP.list_variables(bp):BP.add_variable(bp,name,kind)
for name in ['SnapshotCommitted','RestartInProgress','CapturedCollected','CapturedAvailable']:
 BP.set_variable_replication(co,name,ue.BlueprintVariableReplication.REPLICATED)
if 'SeenStates' not in BP.list_variables(ex):BP.add_object_variable(ex,'SeenStates',ue.PlayerState.static_class(),container_type=ContainerType.ARRAY)
for name,cls in [('Coordinator',co.generated_class()),('ResultsWidget',ue.UserWidget.static_class()),('ResultsOwner',ue.PlayerController.static_class())]:
 if name not in BP.list_variables(ac):BP.add_object_variable(ac,name,cls)
for bp in owned.values():BP.compile_blueprint(bp)
ue.get_default_object(co.generated_class()).set_editor_property('replicates',True)
ue.get_default_object(co.generated_class()).set_editor_property('always_relevant',True)
ue.get_default_object(ex.generated_class()).set_editor_property('replicates',True)
report={}
for bp in owned.values():
 g=BP.get_graph(bp,'EventGraph');report[bp.get_name()]={q:list(BP.find_node_types(g,q)) for q in ['IsPointInBox','GetPawn','GetPlayerState','GetController','GetComponentByClass','GetLocal','IsPrimary','Array','SpawnActor','GetTransform','GetBoxExtent','IsLocalController','IsLocalPlayerController','Equal(Object)','GetNetMode']}
(HERE/'node-types.json').write_text(json.dumps(report,indent=2))
