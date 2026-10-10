"""Offline acceptance of authored data; runtime/human play stays explicitly pending."""
import ast,gzip,hashlib,json,math
from pathlib import Path
from scene_ops import scene,BASE
here=Path(__file__).resolve().parent;root=here.parents[3]
files=sorted(here.glob('*.py'))
for f in files:ast.parse(f.read_text())
manifest=json.loads((here/'positions.json').read_text())
assert manifest['units']=='cm'
assert manifest['maze_door']==[325,1400,0]
assert manifest['connection_boundary']=={'y':3200,'opening_min_x':175,'opening_max_x':475,'source_pr':124,'world_geometry_owner':'full modified maze in WorldRoute; never stream original ConnectedMaze alongside'}
assert set(manifest['checkpoints'])==set('123456')
assert all(len(v)==4 for v in manifest['checkpoints'].values())
assert len(manifest['first_routes'])==len(manifest['second_routes'])==4
assert len(manifest['hall_b_connectors'])==4
assert manifest['escape_width']>=400
for a,b in zip(manifest['escape_route'],manifest['escape_route'][1:]):
    assert abs(b[2]-a[2])/max(math.hypot(b[0]-a[0],b[1]-a[1]),1)<.35
assert all(g['length'] in (200,350) and g['width']==500 and g['pit_floor']<g['center'][2] for g in manifest['gaps'])
limits=manifest['round6_bounds']
assert all(limits['walkable_floor_z_min']<=p[2]<=limits['walkable_floor_z_max'] for p in manifest['escape_route'])
assert limits['key_lost_z_threshold']>limits['chasm_overlap_z_max']>limits['chasm_bottom_z']
assert all(g['pit_floor']>limits['key_lost_z_threshold']+1000 for g in manifest['gaps'])
assert all(g['recovery_steps']['rise']<=45 and g['recovery_steps']['count']*g['recovery_steps']['rise']>=350 for g in manifest['gaps'])
capture=scene(root)
assert len(capture['components'])==916
assert capture['source_records']==561 and capture['components'][909]['kind']=='excluded'
from scene_ops import source_scene,floor_z,SHIFT
delivered=source_scene(root)
assert delivered['components'][318]['location']==[0.0,0,0]
assert all(r['source_index']==i for i,r in enumerate(delivered['components']))
for g in manifest['gaps']:
    x,y,z=g['center'];record=capture['components'][318+g['ColorSlot']]
    assert floor_z(record,x-SHIFT,y,None) is None,('Gap was filled by its path-floor mesh',g)
for r in capture['components']:
    if r['kind']=='procedural':
        assert len(r['triangles'])%3==0
        assert not r['triangles'] or max(r['triangles'])<len(r['vertices'])
        assert len(r['vertices'])==len(r['normals'])==len(r['uvs'])==len(r['vertex_colors'])
paths=[BASE+'/Meshes/SM_Maze_'+str(i).zfill(4) for i,r in enumerate(capture['components']) if i>=316 and r['kind']=='procedural' and r['triangles']]
(here/'mesh_writes.json').write_text(json.dumps({'assets':paths,'files':['Content'+p.removeprefix('/Game')+'.uasset' for p in paths]},indent=2)+'\n')
report={'syntax_files':len(files),'connection_source_sha256':hashlib.sha256((root/'SourceArt/HC/EnvironmentConnection/connection.json.gz').read_bytes()).hexdigest(),'original_reference_sha256':capture['metadata']['source_sha256'],'manifest_sha256':hashlib.sha256((here/'positions.json').read_bytes()).hexdigest(),'source_index_slots':916,'connection_records':capture['source_records'],'generated_meshes':len(paths),'offline_gate':'passed','editor_compile_geometry_and_human_gates':'pending'}
print(json.dumps(report,indent=2))
