import json,pathlib,inspect,unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
HERE=pathlib.Path(__file__).parent
out={'identity':guard(),'methods':[m for m in dir(BP) if 'interface' in m.lower()]}
for name in ['/Game/Puzzles/BP_Carryable','/Game/Puzzles/BP_KeyRelic','/Game/Puzzles/BP_Relic','/Game/Core/BP_CoopCharacter','/Game/Core/BP_CoopGameMode','/Game/Core/BP_CoopGameState']:
 bp=unreal.load_asset(name)
 out[name]={'functions':[str(x.name) for x in BP.list_functions(bp)]}
 for f in ['ResetForRound','ResetItem','ReleaseCarried','GetCarried','ClearRound','CanInteract','GetInteractInfo','Interact','Server_InteractBegin']:
  try: out[name][f]=BP.read_graph_dsl(BP.get_graph(bp,f))
  except: pass
HERE.joinpath('contract-inspection.json').write_text(json.dumps(out,default=str,indent=2))
RESULT=out

