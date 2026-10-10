"""Finish the failed results dispatch graph; preserve earlier green overrides."""
import sys
sys.path.insert(0,str(HERE/'core'))
from common import *
guard()
bp=ue.load_asset('/Game/Puzzles/Test/SixRound/BP_SixRoundTestGameMode')
write(bp,'CompleteMap','''
 (if (Networking|HasAuthority)
  (if (Utilities|String|EqualExactly(String) :A (Game|GetCurrentLevelName :bRemovePrefixString true) :B "L_Site02")
   (CallFunction|RestartAdventure)
   (else (CallFunction|TravelToResults))))''')
save(bp)
RESULT={'test_mode_saved':bp.get_path_name(),'runtime_travel_restart_pending':True}
