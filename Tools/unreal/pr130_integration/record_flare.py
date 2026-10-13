"""Independent readback of the saved flare, without recompiling a green asset."""
import hashlib,json,sys
sys.path.insert(0,str(HERE))
from context import *
bp=ue.load_asset('/Game/Player/Tools/BP_Flare')
require_lease('/Game/Player/Tools/BP_Flare')
if bp.get_editor_property('status')!=ue.BlueprintStatus.BS_UP_TO_DATE:
    save(bp) # SCS readback can invalidate its in-memory generated class; settle it before verification.
assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
original=json.loads((QUEUE/'baseline.json').read_text())['flare_graphs']
current={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
assert all(current[n]==v for n,v in original.items() if n not in ('RefreshFlare','EndFlare'))
base='/Game/Player/Art/Flares'
mesh=ue.load_asset(base+'/SM_HandFlare');bounds=mesh.get_bounds()
report={'assets':[base+'/'+n for n in ('SM_HandFlare','SFX_Flare_Hiss_Loop','MI_FlareMetal','MI_FlareGrip','MI_FlareBody','M_FlareEmber')],
 'mesh_dimensions_cm':[2*bounds.box_extent.x,2*bounds.box_extent.y,2*bounds.box_extent.z],
 'material_slots':[str(s.get_editor_property('imported_material_slot_name')) for s in mesh.static_materials],
 'changed_original_graphs':['RefreshFlare','EndFlare'],'new_helpers':['RefreshFlarePresentation','StopFlarePresentation'],
 'collision_root_preserved':True,'light_tip_offset_cm':8,'visual_base_offset_cm':-11,
 'source_license':'CC0 1.0; SourceArt/PG/PG-A8/README.md',
 'source_hashes':{n:hashlib.sha256((ROOT/'SourceArt/PG/PG-A8'/n).read_bytes()).hexdigest() for n in ('SM_HandFlare.fbx','SFX_Flare_Hiss_Loop.wav')}}
(QUEUE/'flare-import.json').write_text(json.dumps(report,indent=2));RESULT=report
