"""Match the measured solo gap sizes; heavy pickup saves walking, never sprint speed."""
import sys,json
sys.path.insert(0,str(HERE))
from authoring import *
guard()
traversal=ue.load_asset('/Game/Player/AC_Traversal')
BP.get_default_object(traversal).set_editor_properties({'WalkSpeed':330.,'SprintSpeed':600.})
save(traversal)
character=ue.load_asset('/Game/Core/BP_CoopCharacter')
movement=BP.get_default_object(character).get_component_by_class(ue.CharacterMovementComponent)
movement.set_editor_properties({'max_walk_speed':330.,'jump_z_velocity':580.})
save(character)
carry=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying')
fn(carry,'PickupWalkSpeed',outputs=[('Speed','float')])
write(carry,'PickupWalkSpeed','''
 (bind traversal (Utilities|Casting|CastToAC_Traversal :Object (Actor|GetComponentbyClass :self (Components|GetOwner) :ComponentClass "/Game/Player/AC_Traversal.AC_Traversal_C"))
  (:then (return (Class|ACTraversal|GetWalkSpeed :self traversal))) (:CastFailed (return 330.0)))''')
graph=BP.get_graph(carry,'TryPickup')
setter=next(node for node in BP.find_nodes(graph) if BP._get_node_info(node).type_id.endswith('|SetSavedSpeed'))
execute=setter.find_execute_pin();prior=list(execute.list_connected_pins());assert len(prior)==1
call=BP.create_node(graph,'CallFunction|PickupWalkSpeed',ue.IntPoint(1500,1000),declaring_class=carry.generated_class())
for pin in prior:execute.break_single_pin_link(pin);assert pin.try_create_connection(call.find_execute_pin())
assert call.find_then_pin().try_create_connection(execute)
value=setter.find_input_pin('SavedSpeed');assert value
for pin in list(value.list_connected_pins()):value.break_single_pin_link(pin)
assert call.find_output_pin('Speed').try_create_connection(value)
save(carry)
RESULT={'walk':330.,'sprint':600.,'jump_z':580.,'gravity_scale':movement.gravity_scale,'heavy_speed':165.,'actual_gap_landing_and_sprint_pickup_tests_pending':True}
(QUEUE/'movement-tuning.json').write_text(json.dumps(RESULT,indent=2))
