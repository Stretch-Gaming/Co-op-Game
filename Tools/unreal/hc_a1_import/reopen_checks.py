"""Read-only persisted HC-A1 asset/dependency/reimport verification."""
import hashlib
import json
import math
from pathlib import Path
import unreal as ue
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert Path(ue.Paths.project_dir()).resolve()==ROOT
manifest=json.loads((HERE/'manifest.json').read_text())
registry=ue.AssetRegistryHelpers.get_asset_registry()
options=ue.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)
report={'engine':ue.SystemLibrary.get_engine_version(),'assets':[],'dependencies':{},'master_unchanged':True}
for item in manifest['assets']:
 mesh=ue.load_asset(item['destination'])
 filenames=list(mesh.get_editor_property('asset_import_data').extract_filenames())
 assert len(filenames)==1 and Path(filenames[0]).resolve()==(ROOT/item['fbx_path']).resolve()
 assert mesh.get_num_nanite_triangles()==item['source_validation']['triangles_after']
 bounds=mesh.get_bounds()
 assert abs(bounds.origin.z-bounds.box_extent.z)<0.001
 boxes=list(mesh.get_editor_property('body_setup').get_editor_property('agg_geom').get_editor_property('box_elems'))
 assert len(boxes)==1
 box=boxes[0]
 center=box.get_editor_property('center')
 dims=[box.get_editor_property(f) for f in ('x','y','z')]
 if item['name']=='SM_KeyRelic_StoneHeart':
  assert dims[1]<61 and math.isclose(center.z,31,abs_tol=0.001)
  assert mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag')==ue.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX
 report['assets'].append({'path':item['destination'],'reimport_sources':filenames,'source_nanite_triangles_match':True,'base_center_pivot_confirmed':True,'box_center_cm':[center.x,center.y,center.z],'box_dimensions_cm':dims})
for path in [a['destination'] for a in manifest['assets']]+[m['destination'] for m in manifest['material_proposals']]:
 dependencies=[str(n) for n in registry.get_dependencies(path,options)]
 assert all(not n.startswith('/Game/') or n.startswith('/Game/Puzzles/Art/HCA1_Relics/') or n=='/Game/Shared/Style/M_Stylized' for n in dependencies),dependencies
 report['dependencies'][path]=dependencies
assert hashlib.sha256((ROOT/'Content/Shared/Style/M_Stylized.uasset').read_bytes()).hexdigest()=='ed0865b6345022cdf19fde9bf660756f0ea17b2bedece13a1e860ecd4e20e1d9'
(HERE/'engine_persistence_validation.json').write_text(json.dumps(report,indent=2)+'\n')
ue.log('HC-A1_PERSISTENCE_VALIDATION_COMPLETE')
