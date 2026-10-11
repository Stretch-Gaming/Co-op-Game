"""Read-only exact current mapping inventory for native QA evidence."""
import json
import unreal as ue
paths=('/Game/Core/Input/IMC_Coop','/Game/Core/Input/IMC_SixRound','/Game/Core/Input/IMC_RunControls','/Game/Input/IMC_Default')
records=[]
for path in paths:
 context=ue.load_asset(path)
 if not context:continue
 records.append({'context':context.get_path_name(),'mappings':[{'action':mapping.action.get_path_name() if mapping.action else None,'key':str(mapping.key.get_editor_property('key_name'))} for mapping in context.default_key_mappings.mappings]})
RESULT={'contexts':records};(QUEUE/'qa-current-contexts.json').write_text(json.dumps(RESULT,indent=2))
