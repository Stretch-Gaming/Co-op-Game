"""Give the new chamfered rock a stable simple hull for movement and traces."""
import json,sys
sys.path.insert(0,str(HERE))
from context import *
mesh=ue.load_asset('/Game/Puzzles/Art/MazeLevel/Meshes/SM_MazeTraversalRock');assert mesh
sub=ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
if sub.get_simple_collision_count(mesh)==0:
    result=sub.add_simple_collisions(mesh,ue.ScriptingCollisionShapeType.BOX);assert result>=0
body=mesh.get_editor_property('body_setup');assert body
body.set_editor_property('collision_trace_flag',ue.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
RESULT={'asset':mesh.get_path_name(),'simple_hulls':sub.get_simple_collision_count(mesh),'mode':'simple box for physics and queries; chamfered art retained'}
(QUEUE/'rock-collision.json').write_text(json.dumps(RESULT,indent=2))
