"""Read actual graphs/class contracts without compiling or saving assets."""
import json,inspect
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
paths=['/Game/Core/BP_CoopGameMode','/Game/Core/BP_CoopGameState','/Game/Core/BP_CoopCharacter','/Game/Core/BPI_Interactable','/Game/Core/BPI_RoundReset','/Game/Player/Round3/BP_Lever','/Game/Player/Round3/BP_GauntletGate','/Game/Player/Round3/BP_ExitLever','/Game/Player/Ghosts/BP_Ghost','/Game/Player/Ghosts/BP_GhostSpawner','/Game/Hazards/AC_Health']
if ARGS.get('asset'): paths=[ARGS['asset']]
output=HERE/'contract-inspection.json'
report=json.loads(output.read_text()) if output.exists() else {'project':str(ROOT),'engine':ue.SystemLibrary.get_engine_version(),'assets':{}}
report['session']=SESSION
report['authoring_api']=[name for name in dir(BP) if any(s in name.lower() for s in ['interface','variable','function','compile','create']) and callable(getattr(BP,name))]
report['blueprint_editor_api']=[name for name in dir(ue.BlueprintEditorLibrary) if any(s in name.lower() for s in ['interface','variable','function','blueprint'])]
output.write_text(json.dumps(report,indent=2))
for path in paths:
 (HERE/'inspection-progress.json').write_text(json.dumps({'asset':path,'stage':'load','session':SESSION}))
 ue.log('HC_GAUNTLET_READ_ASSET: '+path)
 bp=ue.load_asset(path)
 if not bp:
  report['assets'][path]={'present':False};continue
 (HERE/'inspection-progress.json').write_text(json.dumps({'asset':path,'stage':'graphs','session':SESSION}))
 graphs=[g for g in BP.list_graphs(bp) if not ARGS.get('graphs') or g.get_name() in ARGS['graphs']]
 report['assets'][path]={'present':True,'variables':list(BP.list_variables(bp)),'graphs':{g.get_name():BP.read_graph_dsl(g) for g in graphs}}
 output.write_text(json.dumps(report,indent=2))
(HERE/'inspection-progress.json').write_text(json.dumps({'stage':'complete','session':SESSION}))
