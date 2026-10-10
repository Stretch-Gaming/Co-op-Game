import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.data_table import DataTableTools
from editor_toolset.toolsets.object import ObjectTools
assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Compile audit requires stopped PIE'
report={'engine':ue.SystemLibrary.get_engine_version(),'project':str(ROOT),'compiles':{},'replication':{},'table':json.loads(DataTableTools.get_rows(ue.load_asset('/Game/Puzzles/DT_RoundScaling'),['2','3','4']))}
for path in ['/Game/Core/BP_CoopCharacter','/Game/Core/BP_CoopPlayerController','/Game/Core/BP_CoopGameMode','/Game/Core/BP_CoopGameState','/Game/Core/BP_CoopPlayerState','/Game/Puzzles/BP_Relic','/Game/Puzzles/Test/HC2/BP_HC2InputProbe','/Game/Puzzles/UI/HCA3/AC_HCA3HUD','/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD','/Game/Puzzles/UI/WBP_InteractPrompt']:
 bp=ue.load_asset(path);BP.compile_blueprint(bp);status=str(bp.get_editor_property('status'));assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE,path;report['compiles'][path]=status
 if path in ['/Game/Core/BP_CoopGameState','/Game/Core/BP_CoopPlayerState','/Game/Puzzles/BP_Relic']:
  report['replication'][path]={name:str(BP.get_variable_replication(bp,name)) for name in BP.list_variables(bp) if name in ['RoundState','RelicsCollected','RelicsAvailable','ColorSlot','Collected','Available']}
# Never save incidental compiles or unrelated packages here.
r=ue.load_asset('/Game/Puzzles/BP_Relic')
report['relic_defaults']=json.loads(ObjectTools.get_properties(ue.get_default_object(r.generated_class()),['Value','MinPlayers','Available','Collected','bReplicates','bAlwaysRelevant','PickupSound']))
report['missing_pg']=[p for p in ['/Game/Player/AC_PlayerView','/Game/Player/BPFL_SplitScreen'] if not ue.EditorAssetLibrary.does_asset_exist(p)]
report['table_struct']=ue.load_asset('/Game/Puzzles/DT_RoundScaling').get_editor_property('row_struct').get_path_name()
report['passed']=True
(HERE/'engine-audit.json').write_text(json.dumps(report,indent=2))
