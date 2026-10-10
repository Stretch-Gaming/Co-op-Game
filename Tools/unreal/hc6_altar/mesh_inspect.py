import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
key=BP.get_default_object(ue.load_asset('/Game/Puzzles/BP_KeyRelic'));mesh=key.static_mesh_component
RESULT={'key_mesh':str(mesh.static_mesh),'scale':str(mesh.relative_scale3d),'bounds':str(mesh.static_mesh.get_bounds()),'altar_bounds':str(ue.load_asset('/Game/Puzzles/Art/HCA2_Props/SM_Altar').get_bounds())}
