import sys,json,re
sys.path.insert(0,str(HERE));from authoring import *
from editor_toolset.toolsets.object import ObjectTools
assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
paths=['/Game/Puzzles/BP_Checkpoint','/Game/Puzzles/BP_RoundStart']+list(unreal.EditorAssetLibrary.list_assets('/Game/Puzzles/Rounds',True,False))+list(unreal.EditorAssetLibrary.list_assets('/Game/Puzzles/Test/HC5',True,False))
report={'passed':True,'project':str(ROOT),'engine':unreal.SystemLibrary.get_engine_version(),'blueprints':[],'graphs':{},'checks':[]}
for p in paths:
 b=unreal.load_asset(p)
 if not isinstance(b,unreal.Blueprint):continue
 compile_bp(b);report['blueprints'].append({'path':b.get_path_name(),'status':str(b.get_editor_property('status')),'warnings_as_errors':True})
 gs={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(b)};report['graphs'][b.get_path_name()]=gs
 for name,dsl in gs.items():assert not re.search(r'GetPlayer(Character|Controller|Pawn)\b',dsl),name
 if b.get_name()=='BP_RoundDirector':
  defaults=BP.get_default_object(b)
  assert defaults.get_editor_property('CurrentCheckpoint') is None and defaults.get_editor_property('CandidateCheckpoint') is None
  assert not any('SetRoundState' in x or 'SetRoundPhase' in x for x in gs.values())
  report['checks'].append({'null_saved_actor_references':True,'only_GameMode_writes_phase':True})
report['core_contracts']={name:BP.read_graph_dsl(BP.get_graph(unreal.load_asset('/Game/Core/BP_CoopGameMode'),name)) for name in ['StartRound','ClearRound','FailRound']}
(HERE/'audit.json').write_text(json.dumps(report,indent=2))

