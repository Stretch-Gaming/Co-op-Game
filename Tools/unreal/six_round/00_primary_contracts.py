"""Core contracts shared by the three separately authored lanes."""
import sys
sys.path.insert(0, str(HERE))
from authoring import *

guard()
c = ue.load_asset('/Game/Core/BP_CoopCharacter')
if any(g.get_name() == 'IsCarryingHeavy' for g in BP.list_graphs(c)):
    write(c, 'IsCarryingHeavy', '(return false)')
var(c, 'bTakenProtected', 'bool', False, notify=True)
fn(c, 'SetTakingProtected', [('Protected', 'bool')])
fn(c, 'GetCarryingRelic', outputs=[('Carrying', 'bool')])
fn(c, 'IsCarryingHeavy', outputs=[('Heavy', 'bool')])
write(c, 'SetTakingProtected', '''
 (if (Networking|HasAuthority)
  (Variables|Default|SetTakenProtected Protected))''', 'Protected')
write(c, 'GetCarryingRelic', '''
 (bind carry (Utilities|Casting|CastToAC_Carrying :Object
  (Components|GetComponentbyClass :ComponentClass "/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C"))
  (:then
   (bind item (Class|ACCarrying|GetCarried :self carry))
   (Utilities|IsValid :InputObject item
    (:"Is Valid" (return (Utilities|Casting|IsA :Object item :ObjectClass "/Game/Puzzles/BP_KeyRelic.BP_KeyRelic_C")))
    (:"Is Not Valid" (return false))))
  (:CastFailed (return false)))''')
write(c, 'IsCarryingHeavy', '''
 (bind carry (Utilities|Casting|CastToAC_Carrying :Object
  (Components|GetComponentbyClass :ComponentClass "/Game/Puzzles/Carrying/AC_Carrying.AC_Carrying_C"))
  (:then (bind item (Class|ACCarrying|GetCarried :self carry))
   (Utilities|IsValid :InputObject item
    (:"Is Valid" (bind held (Utilities|Casting|CastToBP_Carryable :Object item)
     (:then (bind heavy (Class|BPCarryable|GetHeavy :self held)) (return heavy)) (:CastFailed (return false))))
    (:"Is Not Valid" (return false))))
  (:CastFailed (return false)))''')
save(c)
RESULT = {'declared': ['bTakenProtected', 'SetTakingProtected', 'GetCarryingRelic', 'IsCarryingHeavy'],
          'gameplay_acceptance': False}
