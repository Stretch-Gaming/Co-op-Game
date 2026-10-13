"""Resume presentation after the imported art has passed its native checks."""
import hashlib,sys,json
sys.path.insert(0,str(HERE))
from context import *
base='/Game/Player/Art/Flares'
paths=[base+'/'+n for n in ('SM_HandFlare','SFX_Flare_Hiss_Loop','MI_FlareMetal','MI_FlareGrip','MI_FlareBody','M_FlareEmber')]
for p in paths:require_lease(p)
require_lease('/Game/Player/Tools/BP_Flare')
mesh=ue.load_asset(paths[0]);sound=ue.load_asset(paths[1]);assert mesh and sound
b=mesh.get_bounds();dims=[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z]
slots=[str(s.get_editor_property('imported_material_slot_name')) for s in mesh.static_materials]
source=(HERE/'import_flare.py').read_text()
body=source[source.index("bp=ue.load_asset('/Game/Player/Tools/BP_Flare')"):]
exec(compile(body,str(HERE/'import_flare.py'),'exec'),globals())
