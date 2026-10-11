"""Make the colliding flare mesh the actor root so flight moves its light and location."""
import sys
sys.path.insert(0, str(HERE))
from authoring import *
guard()
bp = ue.load_asset('/Game/Player/Tools/BP_Flare')
mesh, mesh_handle = component(bp, 'FlareRoot', ue.StaticMeshComponent)
sds = ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
lib = ue.SubobjectDataBlueprintFunctionLibrary
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
context = next(h for h in handles if lib.is_root_actor(lib.get_data(h)))
assert sds.make_new_scene_root(context, mesh_handle, bp)
save(bp)
RESULT = {'root': 'FlareRoot', 'flight_runtime_pending': True}
