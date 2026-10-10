import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from pathlib import Path
import sys
sys.path.insert(0,str(HERE))
from build import write,compile_bp
bp=ue.load_asset('/Game/Puzzles/Test/HC2/BP_HC2InputProbe')
if not bp:
 bp=BP.create('/Game/Puzzles/Test/HC2','BP_HC2InputProbe',ue.Actor.static_class())
 graph=BP.add_function_graph(bp,'ResolveInput')
 BP.add_object_function_param(graph,'Controller',ue.PlayerController.static_class(),True)
 BP.add_object_function_param(graph,'Subsystem',ue.EnhancedInputLocalPlayerSubsystem.static_class(),False)
 compile_bp(bp)
graph=BP.get_graph(bp,'ResolveInput')
BP.remove_function_param(graph,'Subsystem',False)
BP.add_object_function_param(graph,'Subsystem',ue.Object.static_class(),False)
write(bp,'ResolveInput','''(fn ResolveInput (Controller)
 (return (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController Controller)))''')
assert ue.EditorAssetLibrary.save_loaded_asset(bp)

