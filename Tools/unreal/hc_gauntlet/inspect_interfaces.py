import json
import unreal as ue
report={}
for p in ['/Game/Puzzles/Test/BP_TestInteractable','/Game/Puzzles/BP_Carryable','/Game/Player/Round3/BP_Lever','/Game/Player/Round3/BP_GauntletGate']:
 bp=ue.load_asset(p)
 cdo=ue.get_default_object(bp.generated_class())
 report[p]={'interfaces':{n:ue.SystemLibrary.does_implement_interface(cdo,ue.load_asset('/Game/Core/'+n).generated_class()) for n in ['BPI_Interactable','BPI_RoundReset']},'parent':ue.BlueprintEditorLibrary.get_blueprint_parent_class(bp).get_path_name(),'components':[c.get_name() for c in cdo.get_components_by_class(ue.ActorComponent)]}
(HERE/'interfaces.json').write_text(json.dumps(report,indent=2))
