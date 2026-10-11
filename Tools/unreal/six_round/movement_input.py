"""Owning move input also forwards climbing axes; dead/taken/zipline guards apply."""
from authoring import *
def install(bp):
    fn(bp,'HandleSixMovement',[('Axis','Vector2D')])
    write(bp,'HandleSixMovement','''
     (if (Pawn|IsLocallyControlled)
      (CallFunction|RequestClimbAxis :Axis Axis)
      (bind allowed (CallFunction|CanAcceptSixInput))
      (if allowed
       (bind movement (Class|Character|GetCharacterMovement))
       (if (not (AI|Components|NavMovement|IsFlying :self movement))
        (bind (x y) (Math|Vector2D|BreakVector2D :InVec Axis))
        (bind rotation (Pawn|GetControlRotation :self (Pawn|GetController)))
        (bind yaw (.yaw rotation))
        (bind facing (Math|Rotator|MakeRotator :Yaw yaw))
        (Pawn|Input|AddMovementInput :WorldDirection (Math|Vector|GetForwardVector :InRot facing) :ScaleValue y)
        (Pawn|Input|AddMovementInput :WorldDirection (Math|Vector|GetRightVector :InRot facing) :ScaleValue x))))''','Axis')
    graph=BP.get_graph(bp,'EventGraph')
    node=next(n for n in BP.find_nodes(graph) if BP._get_node_info(n).type_id.rsplit('|',1)[-1] in ('IA_Move','EnhancedInputActionIA_Move'))
    for name in ('Triggered','Completed','Canceled'):
        pin=node.find_output_pin(name)
        for target in list(pin.list_connected_pins()):pin.break_single_pin_link(target)
        call=BP.create_node(graph,'CallFunction|HandleSixMovement',ue.IntPoint(800,7600),declaring_class=bp.generated_class())
        assert pin.try_create_connection(call.find_execute_pin())
        assert node.find_output_pin('ActionValue').try_create_connection(call.find_input_pin('Axis'))
    compile_bp(bp)
