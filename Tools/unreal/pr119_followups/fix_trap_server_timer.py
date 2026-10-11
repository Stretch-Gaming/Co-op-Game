"""BP_AdventureTrap: start the RefreshTrap timer on every machine, not only on clients.

The HC-INT2 graph wired the timer to the authority branch's False pin, so the server never ran RefreshTrap:
traps applied no damage and never read their DT_HazardScaling row. The timer now starts first, then the
server sets the replicated StartTime, with the same values as playable_game/build_traps.py.
"""
import importlib
import sys
from pathlib import Path
import unreal as ue
sys.path.insert(0, str(ROOT / 'Tools/unreal/playable_game'))
import authoring
importlib.reload(authoring)
authoring.EXPECTED = ROOT.resolve()
authoring.guard = lambda: None if not ue.EditorLevelLibrary.get_pie_worlds(True) else (_ for _ in ()).throw(AssertionError('Stop PIE before authoring'))
from authoring import write, save, S, BP

bp = ue.load_asset('/Game/Hazards/Traps/BP_AdventureTrap')
write(bp, 'BeginTrap', f'''
 (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshTrap" :Time 0.05 :bLooping true)
 (if (Networking|HasAuthority)
  (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState)) (:then {S('StartTime','(+ (GameState|GetServerWorldTimeSeconds :self gs) 3.0)')}) (:CastFailed)))''')
save(bp)
for name in ('BP_Trap_Spikes', 'BP_Trap_Darts', 'BP_Trap_Swing'):
    child = ue.load_asset('/Game/Hazards/Traps/' + name)
    authoring.compile_bp(child)
RESULT = {'BeginTrap': BP.read_graph_dsl(BP.get_graph(bp, 'BeginTrap')), 'status': str(bp.get_editor_property('status'))}
