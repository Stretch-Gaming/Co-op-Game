"""Read-only walkable-connection probes; transiently open gates then restore."""
import json
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/'CoopGame.uproject'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/Maps/L_Site01')
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
props=[a for a in actors.get_all_level_actors() if a.actor_has_tag('HC_A2_Prop')]
gates=[a for a in props if '_Gate_' in a.get_actor_label()]
originals=[]
for gate in gates:
 leaf=next(c for c in gate.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith('GateLeaf'))
 originals.append((leaf,leaf.get_editor_property('relative_location')));gate.call_method('SetOpenVisual',args=(True,))
segments=[('prototype_exit',(1100,0),(1500,0)),('passage',(1500,0),(2200,0)),('G1',(2200,0),(2800,0)),('hall',(2800,0),(5200,0)),('G2',(5200,0),(5800,0)),('trap_corridor',(5800,0),(8300,0)),('altar_entrance',(8300,0),(8800,0)),('altar_west',(8800,0),(10300,0)),('altar_bypass_west',(10300,0),(10500,300)),('altar_bypass',(10500,300),(11100,300)),('altar_bypass_east',(11100,300),(11200,0)),('G3',(11200,0),(11700,0)),('G3_landing',(11700,0),(11800,0))]
for x,y in [(3200,-650),(3200,650),(4800,-650),(4800,650)]:segments.append(('plate_'+str(x)+'_'+str(y),(x,0),(x,y)))
for x in (3500,4000,4500):
 segments += [('statue_'+str(x)+'_approach',(x,0),(x+150,1100)),('statue_'+str(x)+'_front',(x+150,1100),(x+150,1300))]
segments.append(('altar_front',(11200,0),(11000,0)))
results=[]
try:
 for label,a,b in segments:
  start=unreal.Vector(*a,100);end=unreal.Vector(*b,100)
  hit=unreal.SystemLibrary.box_trace_single(world,start,end,unreal.Vector(34,34,88),unreal.Rotator(),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,True)
  floors=[]
  for t in (0,.25,.5,.75,1):
   x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
   floor=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,80),unreal.Vector(x,y,-150),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,props,unreal.DrawDebugTrace.NONE,True)
   floors.append({'xy_cm':[x,y],'hit':floor.export_text() if floor else None})
  results.append({'name':label,'from_xy_cm':a,'to_xy_cm':b,'pawn_box_clear':hit is None,'blocking_hit':hit.export_text() if hit else None,'floor_samples':floors})
finally:
 for leaf,pos in originals:leaf.set_relative_location(pos,False,False)
report={'status':'passed' if all(r['pawn_box_clear'] and all(f['hit'] for f in r['floor_samples']) for r in results) else 'blocked connections identified','segments':results,'pawn_half_extent_cm':[34,34,88],'pawn_center_z_cm':100,'all_gates_temporarily_open':True,'gate_poses_restored':True,'packages_saved':False}
(root/'Tools/unreal/hc_a2_import/evidence/walkable_connections.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('HCA2_WALK',report['status'])

request=json.loads((root/'Saved/HCA2/request.json').read_text(encoding='utf-8-sig'))
if request.get('scan_prototype_route'):
 import heapq,re
 cache={};edge_cache={};heights={}
 character=unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class('/Game/Core/BP_CoopCharacter'))
 capsule=character.get_component_by_class(unreal.CapsuleComponent);movement=character.get_component_by_class(unreal.CharacterMovementComponent)
 radius=capsule.get_scaled_capsule_radius();half=capsule.get_scaled_capsule_half_height();max_step=movement.get_editor_property('max_step_height')
 def usable(p):
  if p not in cache:
   x,y=p
   samples=[]
   for dx,dy in [(0,0),(radius*.7,0),(-radius*.7,0),(0,radius*.7),(0,-radius*.7),(radius*.5,radius*.5),(-radius*.5,radius*.5),(radius*.5,-radius*.5),(-radius*.5,-radius*.5)]:
    floor=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x+dx,y+dy,60),unreal.Vector(x+dx,y+dy,-100),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,props,unreal.DrawDebugTrace.NONE,True)
    samples.append(float(re.search(r'Location=\([^)]*Z=([-+0-9.eE]+)',floor.export_text())[1]) if floor else None)
   z=max(samples) if all(v is not None for v in samples) else None
   heights[p]=z
   if z is None or not -5<=z<=max_step:cache[p]=False
   else:
    block=unreal.SystemLibrary.capsule_trace_single(world,unreal.Vector(x,y,z+half+4),unreal.Vector(x+.01,y,z+half+4),radius,half,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,True)
    cache[p]=block is None
  return cache[p]
 def clear(a,b):
  if (a,b) not in edge_cache:
   hit=unreal.SystemLibrary.capsule_trace_single(world,unreal.Vector(*a,heights[a]+half+4),unreal.Vector(*b,heights[b]+half+4),radius,half,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,True)
   edge_cache[a,b]=hit is None and abs(heights[a]-heights[b])<=max_step
  return edge_cache[a,b]
 target=(1500,0);routes=[]
 for start in [(-1000,-600),(-1000,-200),(-1000,200),(-1000,600)]:
  queue=[(0,0,start)];came={};distance={start:0};found=False
  while queue:
   _,cost,p=heapq.heappop(queue)
   if cost!=distance[p]:continue
   if not usable(p):continue
   if p==target:found=True;break
   for dx,dy in [(100,0),(-100,0),(0,100),(0,-100)]:
    q=(p[0]+dx,p[1]+dy)
    if not (-1200<=q[0]<=1500 and -1400<=q[1]<=1400) or not usable(q) or not clear(p,q):continue
    new=cost+100
    if new<distance.get(q,float('inf')):
     distance[q]=new;came[q]=p;heapq.heappush(queue,(new+abs(q[0]-target[0])+abs(q[1]-target[1]),new,q))
  route=[]
  if found:
   p=target;route=[p]
   while p!=start:p=came[p];route.append(p)
   route.reverse()
  routes.append({'start_xy_cm':start,'target_xy_cm':target,'found':found,'waypoints_xy_cm':route,'waypoint_floor_heights_cm':[heights[p] for p in route]})
 (root/'Tools/unreal/hc_a2_import/evidence/prototype_connection_scan.json').write_text(json.dumps({'status':'passed' if all(r['found'] for r in routes) else 'routes missing','routes':routes,'grid_spacing_cm':100,'capsule_radius_cm':radius,'capsule_half_height_cm':half,'max_step_cm':max_step,'floor_footprint_rays_per_cell':9,'scope':'Floor-following capsule probes with the existing CharacterMovement step budget; no Core edits','cell_count':len(cache),'clear_cells_xy_cm':[list(p) for p,ok in cache.items() if ok],'original_HZ_actors_preserved':True},indent=2),encoding='utf-8')
 print('HCA2_PROTOTYPE_SCAN',[(r['start_xy_cm'],r['found']) for r in routes])

if request.get('probe_starts'):
 rows=[]
 for x,y in [(-1000,-600),(-1000,-200),(-1000,200),(-1000,600),(1000,0),(1100,0),(1200,0),(1300,0),(1400,0),(1500,0)]:
  floor=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,400),unreal.Vector(x,y,-150),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,props,unreal.DrawDebugTrace.NONE,True)
  hit=unreal.SystemLibrary.capsule_trace_single(world,unreal.Vector(x,y,100),unreal.Vector(x+.01,y,100),34,88,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[],unreal.DrawDebugTrace.NONE,True)
  rows.append({'xy':[x,y],'floor':floor.export_text() if floor else None,'block':hit.export_text() if hit else None})
 (root/'Saved/HCA2/start_probes.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
