"""Reset test hazards through the shared round contract after UI installation."""
import sys
sys.path.insert(0,str(HERE))
from authoring import *
guard()
pairs=[('/Game/Hazards/Maze/BP_MouthSeal','ResetSeal'),
       ('/Game/Hazards/Traps/SixRound/BP_SixRoundTrap','SRTrapResetSchedule'),
       ('/Game/Hazards/Traps/BP_SprintSequence','SRSequenceResetSchedule')]
interface=ue.load_asset('/Game/Core/BPI_RoundReset').generated_class()
for path,handler in pairs:
    bp=ue.load_asset(path)
    assert ue.SystemLibrary.does_implement_interface(BP.get_default_object(bp),interface),path
    node=BP.add_event(bp,'ResetForRound')
    for pin in list(node.find_then_pin().list_connected_pins()):node.find_then_pin().break_single_pin_link(pin)
    event(bp,'ResetForRound',handler)
    save(bp)
RESULT={'reset_adapters':pairs,'runtime_pending':True}
