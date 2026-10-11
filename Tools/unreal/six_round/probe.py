"""Read-only bootstrap inspection for the six-round editor."""
import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

RESULT = {'interfaces_api': [n for n in dir(ue.BlueprintEditorLibrary) if 'interface' in n.lower()],
          'blueprint_interface_methods': [n for n in dir(ue.Blueprint) if 'interface' in n.lower()]}
for path in ['/Game/Core/BP_CoopCharacter', '/Game/Core/BP_CoopGameMode',
             '/Game/Puzzles/Rounds/BP_RoundDirector', '/Game/Player/Ghosts/BP_Ghost']:
    bp = ue.load_asset(path)
    RESULT[path] = {'functions': [str(f) for f in BP.list_functions(bp)],
                    'variables': BP.list_variables(bp)}
(QUEUE/'bootstrap-probe.json').write_text(json.dumps(RESULT, default=str, indent=2))
