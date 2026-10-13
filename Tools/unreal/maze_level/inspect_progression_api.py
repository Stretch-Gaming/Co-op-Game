import json,sys
sys.path.insert(0,str(HERE))
from context import *
bp=ue.load_asset(MODE);graph=BP.get_graph(bp,'PollMeetingLocks')
RESULT={'functions':[str(f) for f in ue.BlueprintEditorLibrary.list_functions(bp)],
        'refresh_types':BP.find_node_types(graph,'RefreshSixObjective'),
        'clear_types':BP.find_node_types(graph,'ClearRound'),
        'custom_helpers':BP.find_node_types(graph,'PrepareMazeRound')}
(QUEUE/'progression-api.json').write_text(json.dumps(RESULT,indent=2))
