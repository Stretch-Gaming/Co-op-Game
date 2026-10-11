"""Primary-run read-only editor collision collector; no actors moved, no packages saved."""
import hashlib,json,pathlib,sys
import unreal as ue
ROOT=pathlib.Path('C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game').resolve()
assert pathlib.Path(ue.Paths.convert_relative_path_to_full(ue.Paths.get_project_file_path())).resolve()==ROOT/'CoopGame.uproject'
assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE; this collector only uses the editor world'
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert world.get_outermost().get_name()=='/Game/Maps/L_ConnectedRoomMaze'
assert sorted(l.get_outermost().get_name()for l in ue.EditorLevelUtils.get_levels(world))==sorted(['/Game/Maps/L_ConnectedRoomMaze','/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze','/Game/Hazards/L_Site01_HZ'])
plan=json.loads((ROOT/'Saved/QualityGeometry/probe-plan.json').read_text());source=ROOT/'SourceArt/HC/EnvironmentConnection/Refresh_fd40cdeb/connection.json.gz';assert hashlib.sha256(source.read_bytes()).hexdigest()==plan['source_sha256']
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()
def snapshot(a):
 t=a.get_actor_transform();return (a.get_path_name(),[t.translation.x,t.translation.y,t.translation.z,t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w,t.scale3d.x,t.scale3d.y,t.scale3d.z],[str(tag)for tag in a.tags])
before=[snapshot(a)for a in actors];dirty_before=[p.get_name()for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
protected=['Content/Maps/L_ConnectedRoomMaze.umap','Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap','Content/Hazards/L_Site01_HZ.umap'];hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in protected}
character=ue.get_default_object(ue.EditorAssetLibrary.load_blueprint_class('/Game/Core/BP_CoopCharacter'));capsule=character.get_component_by_class(ue.CapsuleComponent);movement=character.get_component_by_class(ue.CharacterMovementComponent)
radius=capsule.get_scaled_capsule_radius();half=capsule.get_scaled_capsule_half_height();step=float(movement.get_editor_property('max_step_height'));slope=movement.get_walkable_floor_angle();actual_profile=str(capsule.get_collision_profile_name());profile='Pawn';assert radius>0 and half>=radius
assert capsule.get_collision_object_type()==ue.CollisionChannel.ECC_PAWN,'Re-review query profile for this pawn object type'
solid_channels=[ue.CollisionChannel.ECC_WORLD_STATIC,ue.CollisionChannel.ECC_WORLD_DYNAMIC,ue.CollisionChannel.ECC_PHYSICS_BODY]
assert all(capsule.get_collision_response_to_channel(c)==ue.CollisionResponseType.ECR_BLOCK for c in solid_channels),'Re-review custom solid-object responses'
query_count=0
ignore=[a for a in actors if isinstance(a,ue.Pawn)]
sys.path.insert(0,str(ROOT/'Tools/quality/geometry'))
from hit_codec import decode as decode_hit
component_owners={c.get_path_name():c for a in actors for c in a.get_components_by_class(ue.ActorComponent)}
def hitdata(hit):
 data=decode_hit(hit)
 if data:
  component=component_owners.get(data.get('component_native_path'))
  if component:
   actor=component.get_owner()
   try:hidden=bool(actor.get_editor_property('hidden'))
   except Exception:hidden=None
   data.update(actor_label=actor.get_actor_label(),actor_path=actor.get_path_name(),component=component.get_path_name(),hidden_actor=hidden,identity_method='explicit export component path matched to already loaded component owner')
   pair_blocks=(component.get_collision_response_to_channel(ue.CollisionChannel.ECC_PAWN)==ue.CollisionResponseType.ECR_BLOCK and capsule.get_collision_response_to_channel(component.get_collision_object_type())==ue.CollisionResponseType.ECR_BLOCK)
   data['actual_capsule_component_pair_blocks']=pair_blocks
   if not pair_blocks:return None
 return data
def line(a,b):
 global query_count;query_count+=1
 return hitdata(ue.SystemLibrary.line_trace_single_by_profile(world,ue.Vector(*a),ue.Vector(*b),profile,True,ignore,ue.DrawDebugTrace.NONE,True))
def sweep(a,b):
 global query_count;query_count+=1
 return hitdata(ue.SystemLibrary.capsule_trace_single_by_profile(world,ue.Vector(*a),ue.Vector(*b),radius,half,profile,True,ignore,ue.DrawDebugTrace.NONE,True))
def grounded(p):
 x,y,z=p;floor=line([x,y,z+step+60],[x,y,z-step-80])
 if not floor or not floor['blocking']:return None,floor
 return floor['impact_point'][2],floor
start=int(ARGS.get('start',0));end=min(int(ARGS.get('end',start+10)),len(plan['samples']));assert 0<=start<=end and end-start<=12,'Maximum12 samples per batch'
rows=[]
for sample in plan['samples'][start:end]:
 p=sample['point'];z,floor=grounded(p);row=dict(sample);row['floor_hit']=floor;row['findings']=[]
 if z is None:row['findings'].append('No nearby Pawn-blocking floor at proposed source sample; deliberate gap or collision difference possible.')
 else:
  supports=[]
  for dx,dy in [(radius*.7,0),(-radius*.7,0),(0,radius*.7),(0,-radius*.7)]:
   h=line([p[0]+dx,p[1]+dy,z+step+5],[p[0]+dx,p[1]+dy,z-step-5]);supports.append({'xy':[p[0]+dx,p[1]+dy],'hit':h})
  center=[p[0],p[1],z+half+4];block=sweep(center,[center[0]+.01,*center[1:]]);row.update({'floor_z_cm':z,'footprint_supports':supports,'standing_capsule_hit':block})
  if block:row['findings'].append('Pawn capsule blocked on source-proposed standing point; obstacle intention unresolved.')
  if any(not h['hit']for h in supports):row['findings'].append('Footprint ray lacks nearby support; boundary/pit/jump may be deliberate.')
  sides={}
  for name,dx,dy in [('xplus',250,0),('xminus',-250,0),('yplus',0,250),('yminus',0,-250)]:sides[name]=line(center,[center[0]+dx,center[1]+dy,center[2]])
  widths={axis:sum(sides[axis+sign]['distance_cm']if sides[axis+sign]else 250 for sign in ('plus','minus'))for axis in ('x','y')};row['side_hits']=sides;row['axis_clearance_width_lower_bounds_cm']=widths
  if any(w<2*(radius+4)for w in widths.values()):row['findings'].append('Opposing side-ray spacing below capsule diameter+margin; not proof of blocked route.')
 row['confidence']='native collision observation; design intent unresolved';rows.append(row)
segments=[]
if ARGS.get('segments',False):
 byid={r['id']:r for r in plan['samples']}
 for a,b in plan['nearby_segment_pairs']:
  pa,pb=byid[a]['point'],byid[b]['point'];ground=[];issues=[]
  for t in (0,.25,.5,.75,1):
   p=[u+(v-u)*t for u,v in zip(pa,pb)];z,hit=grounded(p);ground.append({'point':p,'z':z,'hit':hit})
   if z is None:issues.append('Missing ground sample; deliberate gap possible')
  sweeps=[]
  if not issues:
   for first,second in zip(ground,ground[1:]):
    za,zb=first['z'],second['z'];a3=[*first['point'][:2],za+half+4];b3=[*second['point'][:2],zb+half+4];hit=sweep(a3,b3);sweeps.append(hit)
    if abs(za-zb)>step:issues.append('Height change exceeds native step budget; slope/jump intention unresolved')
    if hit:issues.append('Ground-following capsule sweep blocked')
  segments.append({'from':a,'to':b,'ground_samples':ground,'capsule_sweeps':sweeps,'observation':'sampled grounded segment clear'if not issues else'needs review','issues':issues,'scope':'Local sample segment; not a mission route or walking test'})
assert [snapshot(a)for a in actors]==before,'Actor changed during read-only collection'
assert {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in protected}==hashes
report={'plan_selection_mode':plan.get('selection_mode','all collision support surfaces'),'map':plan['map'],'source_sha256':plan['source_sha256'],'start':start,'end':end,'character_defaults':{'capsule_radius_cm':radius,'capsule_half_height_cm':half,'max_step_cm':step,'max_floor_angle_degrees':slope,'actual_capsule_profile':actual_profile,'query_profile':profile,'query_note':'The capsule uses unregistered Custom responses. Geometry queries use registered Pawn; Pawn object type, solid responses and both sides of each component response pair are checked. Complex probes remain observations rather than movement proof.'},'samples':rows,'local_segments':segments,'native_query_count':query_count,'trace_complex':True,'physics_scene_validation':'Unconfirmed until known source floor returns native support; NullRHI can lack a usable physics scene','native_floor_support_count':sum(r.get('floor_z_cm')is not None for r in rows),'actor_transforms_tags_unchanged':True,'protected_saved_hashes_unchanged':True,'dirty_maps_before':dirty_before,'dirty_maps_after':[p.get_name()for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()],'packages_saved':False,'bugs_proven':[],'geometry_fixes_authorized':False}
(ROOT/f'Saved/QualityGeometry/native-{start}-{end}.json').write_text(json.dumps(report,indent=2));RESULT={'rows':len(rows),'queries':query_count,'findings':sum(bool(r['findings'])for r in rows),'report':f'Saved/QualityGeometry/native-{start}-{end}.json'}
