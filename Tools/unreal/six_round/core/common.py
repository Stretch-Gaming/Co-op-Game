"""Bootstrap for the isolated six-round authoring queue."""
import sys
from pathlib import Path
# The queue sets ROOT/HERE when executing text; standalone execution has __file__.
_core = Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT) / 'Tools/unreal/six_round/core'
sys.path.insert(0, str(_core.parent))
from authoring import *
T = 'PhaseEndsAt_13_75E3D82F49994607AFA23C8B57E08350'
PLAY='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")'
CLEAR='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2")'
FAIL='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")'
LOBBY='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")'
COMPLETE='(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator4")'
GS='(Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))'
GM='(Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))'
STATE='(bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))'
EQ=lambda a,b:f'(Utilities|Enum|Equal(Enum) {a} {b})'
HEALTH='/Game/Hazards/AC_Health.AC_Health_C'

def replicated(bp):
    BP.get_default_object(bp).set_editor_property('replicates',True)

REQUIRED_INTERFACES = []
def interface(bp,path):
    # Stage 0 records UI work; the installed toolset has no interface mutation API.
    entry={'asset':bp.get_path_name().split('.')[0], 'interface':path}
    if entry not in REQUIRED_INTERFACES: REQUIRED_INTERFACES.append(entry)

def exclusive_event(bp,name,handler,params=()):
    graph=BP.get_graph(bp,'EventGraph');node=BP.add_event(bp,name)
    for pin in list(node.find_then_pin().list_connected_pins()):
        node.find_then_pin().break_single_pin_link(pin)
    event(bp,name,handler,params)
