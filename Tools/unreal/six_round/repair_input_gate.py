import sys
sys.path.insert(0, str(HERE))
from authoring import *
guard()
c = ue.load_asset('/Game/Core/BP_CoopCharacter')
write(c, 'CanAcceptSixInput', '(return false)')
RESULT = {'repaired': 'incomplete input gate before rebuilding its graph'}
