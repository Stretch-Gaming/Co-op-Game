import sys,importlib
sys.path.insert(0,str(HERE))
from authoring import *
import movement_input;importlib.reload(movement_input)
guard();bp=ue.load_asset('/Game/Core/BP_CoopCharacter')
movement_input.install(bp);save(bp)
RESULT={'owning_move_handler_saved':True,'climbing_axis_preserved':True,'runtime_pending':True}
