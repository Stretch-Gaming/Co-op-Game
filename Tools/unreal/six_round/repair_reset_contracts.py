"""Retire only this task's unimplemented placeholders before adding reset events."""
import sys
sys.path.insert(0, str(HERE))
from authoring import *

guard()
for path, handler in [('/Game/Player/RelicChamber/BP_RelicCage', 'ResetCage'),
                      ('/Game/Player/Taking/BP_TakingDirector', 'ResetTaking'),
                      ('/Game/Player/Ghosts/BP_ChaseDirector', 'ResetChase')]:
    bp = ue.load_asset(path)
    if any(g.get_name() == 'ResetForRound' for g in BP.list_graphs(bp)):
        BP.remove_function_graph(bp, 'ResetForRound')
    fn(bp, handler, [('Index', 'int'), ('Attempt', 'int')])
    save(bp)
RESULT = {'repaired': 'new reset placeholders; existing lever unchanged'}
