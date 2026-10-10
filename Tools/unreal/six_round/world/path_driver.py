"""Asynchronous owning-input path driver. Navigation aims are disclosed fixtures."""
import math,time
import unreal as ue
class Driver:
 def __init__(self,h,layout,pid,stage,slot):
  self.h=h;self.layout=layout;self.pid=pid;self.stage=stage;self.slot=slot;self.pawn=h.pawn(h.server,pid)
  self.half=self.pawn.get_component_by_class(ue.CapsuleComponent).get_scaled_capsule_half_height()
  route=next(r for r in layout[stage+'_routes'] if r['ColorSlot']==slot)
  original=route['nodes']
  self.nodes=[]
  def append(node):
   if not self.nodes or self.nodes[-1]!=list(node):self.nodes.append(list(node))
  for node in route.get('approach_nodes',[]):append(node)
  for i,node in enumerate(original):
   append(node)
   if stage=='second' and i+1<len(original):
    tube=next((t for t in layout['hall_b_connectors'] if t['ColorSlot']==slot and node==t['nodes'][2] and original[i+1]==t['nodes'][3]),None)
    if tube:
     for upper in tube.get('upper_walk_nodes',[]):append(upper)
  for node in route.get('arrival_nodes',[]):append(node)
  assert route.get('arrival_nodes'),'Manifest must provide a safe room arrival route'
  self.gap=next(g for g in layout['gaps'] if g['stage']==stage and g['ColorSlot']==slot)
  self.index=1;self.mode='walk';self.done=False;self.jump_at=None;self.gap_started=False;self.gap_airborne=False;self.gap_landed=False
  self.phase_started=time.monotonic();self.last_progress=time.monotonic();self.last_pos=None;self.metric={'path_slot':slot,'owner_color_slot':h.slots[pid],'waypoints':[],'climbs':[],'gap':{'length':self.gap['length'],'airborne':False,'sprint':False,'landed':False}}
  self.trap_mode=None;self.trap=None
  self.traps=[a for a in ue.GameplayStatics.get_all_actors_with_tag(h.server,'SixRound.ResettableHazard') if a.get_class().get_name().startswith('BP_SixRound')]
  start=self.nodes[0];hit=ue.SystemLibrary.line_trace_single(h.server,ue.Vector(start[0],start[1],start[2]+250),ue.Vector(start[0],start[1],start[2]-600),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,h.server_pawns,ue.DrawDebugTrace.NONE,True)
  assert hit,('Path start has no native floor',stage,slot)
  h.fixture_place(pid,[start[0],start[1],hit.to_dict()['impact_point'].z+self.half+4])
  self.initial_settled=False;self.mantle_samples=set();self.max_z=self.pawn.get_actor_location().z
  self.aim(self.nodes[1])
 def position(self):
  p=self.pawn.get_actor_location();return [p.x,p.y,p.z]
 def pause(self):
  for action in ('move','climb','jump','sprint'):self.h.release(self.pid,action)
 def aim(self,target):
  p=self.position();self.h.aim_yaw(self.pid,math.degrees(math.atan2(target[1]-p[1],target[0]-p[0])))
 def walking(self,target,sprint=False,value=1):
  self.aim(target);self.h.hold(self.pid,'move',ue.Vector(0,value,0))
  if sprint:self.h.hold(self.pid,'sprint',1)
  else:self.h.release(self.pid,'sprint')
 def advance(self):
  p=self.position();self.metric['waypoints'].append({'index':self.index,'target':self.nodes[self.index],'actual':p});self.index+=1;self.last_progress=time.monotonic()
  if self.index==len(self.nodes):
   assert self.gap_landed,'Full path gate must include a real jump and landing'
   self.pause();self.done=True;self.h.check('owner completed isolated '+self.stage+' path',{'id':self.pid,**self.metric})
 def start_climb(self,top,explicit):
  self.climb_top=top;self.climb_explicit=explicit;self.mode='climb';self.phase_started=time.monotonic();self.h.release(self.pid,'sprint');self.h.aim_yaw(self.pid,90);self.h.hold(self.pid,'climb',1);self.h.hold(self.pid,'move',ue.Vector(0,1,0))
 def hazard_wait(self,target,now):
  p=self.position();dx,dy=target[0]-p[0],target[1]-p[1];distance=max(math.hypot(dx,dy),1);ux,uy=dx/distance,dy/distance
  if self.trap_mode:
   trap=self.trap;age=trap.get_editor_property('Now')-trap.get_editor_property('TriggeredAt');delay=trap.get_editor_property('SpikeDelay')
   if self.trap_mode=='bait':
    if age>=0 and age<delay+1:
     self.trap_mode='retreat';self.phase_started=now;self.walking(target,False,-1)
    else:self.walking(target,False,.1)
   elif self.trap_mode=='retreat':
    if now-self.phase_started<.3:self.walking(target,False,-1)
    else:self.h.release(self.pid,'move');self.trap_mode='wait'
   elif self.trap_mode=='wait':
    self.h.release(self.pid,'move')
    if delay+1.05<=age<delay+1.6:self.trap_mode='cross';self.phase_started=now
   elif self.trap_mode=='cross':
    self.walking(target,True)
    tp=trap.get_actor_location()
    if (p[0]-tp.x)*ux+(p[1]-tp.y)*uy>300:self.trap_mode=None;self.trap=None
   return self.trap_mode is not None
  for trap in self.traps:
   tp=trap.get_actor_location();tx,ty=tp.x-p[0],tp.y-p[1];ahead=tx*ux+ty*uy;side=abs(tx*uy-ty*ux)
   if not (0<ahead<450 and side<220 and abs(tp.z-(p[2]-self.half))<150):continue
   kind=trap.get_editor_property('Kind');clock=trap.get_editor_property('Now')-trap.get_editor_property('StartTime')
   speed=max(self.pawn.character_movement.max_walk_speed,1);cross=(ahead+260)/speed+.15
   wait=False
   if kind==0:
    self.trap=trap;self.trap_mode='bait';return True
   if kind==1:
    interval=trap.get_editor_property('Interval');fraction=clock%interval
    wait=fraction<.25 or interval-fraction<cross
   if kind==2:
    swing=trap.get_editor_property('SwingSpeed');phase=clock*swing
    # Wait at safe edge until enough time remains before the next centre sweep.
    wait=abs(math.sin(phase))<.7 or math.pi-(phase%math.pi)<cross*swing+.4
   if wait:self.h.release(self.pid,'move');return True
  return False
 def tick(self):
  if self.done:return
  h=self.h;pid=self.pid;p=self.position();feet=p[2]-self.half;now=time.monotonic()
  if not self.initial_settled:
   if not h.fixture_settled(pid):return
   self.initial_settled=True;self.phase_started=now;self.last_progress=now
  self.max_z=max(self.max_z,p[2]);h.motion_evidence[pid]={'path_stage':self.stage,'path_slot':self.slot,'max_server_z':self.max_z,'mantle_observed':bool(getattr(self,'mantle_observed',False)),'movement_mode':str(self.pawn.character_movement.movement_mode)}
  assert not h.prop(self.pawn,'health','bDead'),('Owner died on physical path',pid,self.stage,self.slot)
  assert not self.pawn.get_editor_property('bTakenProtected') and not self.pawn.call_method('IsCarryingHeavy')
  if self.last_pos is None or math.dist(p,self.last_pos)>20:self.last_progress=now;self.last_pos=p
  assert now-self.last_progress<12,('Native movement stalled',pid,self.mode,self.index,p)
  mode=self.pawn.character_movement.movement_mode
  if self.gap_started:
   self.gap_airborne|=mode==ue.MovementMode.MOVE_FALLING
   if self.jump_at is not None and now-self.jump_at>.12:h.release(pid,'jump');self.jump_at=None
   if p[1]>self.gap['center'][1]+self.gap['length']/2+100 and mode==ue.MovementMode.MOVE_WALKING:
    self.gap_landed=True;self.metric['gap']['airborne']=self.gap_airborne;self.metric['gap']['landed']=True;assert self.gap_airborne
  if self.mode=='climb':
   if feet>=self.climb_top-155:
    # Preserve climb eligibility until the owning Jump is actually injected.
    for action in ('move','sprint','jump'):h.release(pid,action)
    self.mode='mantle_request';self.phase_started=now
   return
  if self.mode=='mantle_request':
   if now-self.phase_started>.12:
    h.mantle_diagnostic(pid,'before path climb exit jump');h.hold(pid,'jump',1);self.mode='mantle';self.phase_started=now;self.mantle_observed=False;self.mantle_samples=set()
   return
  if self.mode=='mantle':
   self.mantle_observed|=bool(h.prop(self.pawn,'traversal','bMantling'))
   for delay in (.05,.2,.6):
    if now-self.phase_started>=delay and delay not in self.mantle_samples:
     h.mantle_diagnostic(pid,'after path climb exit jump '+str(delay)+'s');self.mantle_samples.add(delay)
   if now-self.phase_started>.12:h.release(pid,'jump');h.release(pid,'climb')
   if self.mantle_observed and not h.prop(self.pawn,'traversal','bMantling') and mode==ue.MovementMode.MOVE_WALKING and feet>=self.climb_top-25:
    self.metric['climbs'].append({'top':self.climb_top,'native_mantle':True,'landing':p});self.mode='walk'
    if self.climb_explicit:self.advance()
   return
  target=self.nodes[self.index];previous=self.nodes[self.index-1];xy=math.hypot(target[0]-p[0],target[1]-p[1])
  vertical=math.hypot(target[0]-previous[0],target[1]-previous[1])<1
  if vertical and target[2]>previous[2]+100:
   self.start_climb(target[2],True);return
  if vertical and target[2]<previous[2]-100:
   h.release(pid,'climb');h.release(pid,'sprint')
   if xy>35:self.walking(target,False,.3)
   else:h.release(pid,'move')
   if xy<85 and abs(feet-target[2])<40 and mode==ue.MovementMode.MOVE_WALKING:self.advance()
   return
  next_node=self.nodes[self.index+1] if self.index+1<len(self.nodes) else None
  if next_node and next_node[:2]==target[:2] and next_node[2]<target[2]-100 and xy<55:
   # Walk through the open shaft head; subsequent descent uses real gravity.
   self.advance();return
  if xy<65 and abs(feet-target[2])<50 and mode==ue.MovementMode.MOVE_WALKING:self.advance();return
  volumes=[a for a in self.pawn.get_overlapping_actors(ue.Actor.static_class()) if a.get_class().get_name()=='BP_ClimbVolume_C']
  if h.prop(self.pawn,'traversal','bClimbing') and volumes:
   origin,extent=volumes[0].get_actor_bounds(True);self.start_climb(origin.z+extent.z+5,False);return
  gx,gy,gz=self.gap['center']
  launch_offset=100 if self.gap['length']>250 else 30
  near_edge=gy-self.gap['length']/2
  if not self.gap_started and abs(p[0]-gx)<160 and near_edge-launch_offset<=p[1]<near_edge:
   if self.gap['length']>250:assert h.prop(self.pawn,'traversal','bSprinting')
   else:assert not h.prop(self.pawn,'traversal','bSprinting')
   h.hold(pid,'jump',1);self.jump_at=now;self.gap_started=True;self.metric['gap']['sprint']=bool(h.prop(self.pawn,'traversal','bSprinting'));self.metric['gap']['launch_fixture']={'kind':'owning-input jump triggered by manifest edge','requested_offset_cm':launch_offset,'actual_before_edge_cm':near_edge-p[1],'position':p}
  if not self.gap_started and self.hazard_wait(target,now):return
  self.walking(target,self.stage=='second')
