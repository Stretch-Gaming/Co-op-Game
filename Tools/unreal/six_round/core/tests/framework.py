"""Bounded runtime suite runner; reports failure and releases injected controls."""
import sys,types,time,json,traceback
import unreal as ue
from runtime import Runtime,QUEUE
registry=sys.modules.setdefault('six_round_core_test_registry',types.ModuleType('six_round_core_test_registry'))
class Suite:
 def __init__(self,name,args=None):
  assert not getattr(registry,'handle',None),'Stop the active core test before starting another'
  self.name=name;self.args=args or {};self.rt=Runtime(self.args.get('players'),self.args.get('profile'));assert self.rt.ready()
  self.n=len(self.rt.players);self.phase='start';self.started=time.monotonic();self.deadline=self.started+self.args.get('timeout',240);self.checks=[];self.holds={};self.hold_states={};self.action_injections=[];self.aims={};self.fixtures=[];self.replica_expectations=[]
 def step(self,name):
  for i in self.holds:self.release_hold(i,'phase_change')
  self.holds={};self.hold_states={};self.phase=name;self.started=time.monotonic()
 def hold(self,i,action='IA_Interact',duration=.2):
  assert duration>=0
  if self.holds.get(i)==(action,duration):return
  if i in self.holds:self.release_hold(i,'replaced_hold')
  self.holds[i]=(action,duration)
  event={'phase':self.phase,'owner_index':i,'action':action,'requested_duration_seconds':duration,'value1_injections':0,'value0_injections':0,'first_injection_phase_elapsed':None,'actual_hold_seconds':None,'release_reason':None}
  self.hold_states[i]={'first':None,'released':False,'event':event};self.action_injections.append(event)
 def release_hold(self,i,reason):
  state=self.hold_states[i]
  if state['released']:return
  self.rt.inject(i,self.holds[i][0],0)
  state['event']['value0_injections']+=1
  state['event']['actual_hold_seconds']=None if state['first'] is None else time.monotonic()-state['first']
  state['event']['release_reason']=reason;state['released']=True
 def inject_holds(self):
  for i,(action,duration) in self.holds.items():
   state=self.hold_states[i]
   if state['released']:continue
   # A delayed first callback must still inject one press. The hold deadline
   # begins at this owner's first successful injection, never phase entry.
   if state['first'] is None or time.monotonic()-state['first']<duration:
    self.rt.inject(i,action,1);now=time.monotonic()
    if state['first'] is None:
     state['first']=now;state['event']['first_injection_phase_elapsed']=now-self.started
    state['event']['value1_injections']+=1
   else:self.release_hold(i,'duration_elapsed')
 def focus(self,i,target):
  self.rt.focus(i,target);self.aims[i]=target;self.fixtures.extend(self.rt.silence_occluding_small_relics(target))
 def unfocus(self):self.aims={};self.rt.restore_occluders(self.fixtures);self.fixtures=[]
 def expect_alive_replicas(self,indices):
  self.replica_expectations.extend((self.rt.players[i].player_state.player_id,self.rt.clock()+.8) for i in indices)
 def elapsed(self):return time.monotonic()-self.started
 def record(self,text,**data):self.checks.append({'check':text,**data})
 def finish(self,passed,error=None):
  cleanup_errors=[]
  try:
   for operation in (self.rt.cleanup_input,self.unfocus):
    try:operation()
    except Exception:cleanup_errors.append(traceback.format_exc())
  finally:
   try:ue.unregister_slate_post_tick_callback(self.handle)
   except Exception:cleanup_errors.append(traceback.format_exc())
   else:registry.handle=None
  if cleanup_errors:
   passed=False;error='\n'.join([error or '',*cleanup_errors]).strip()
  for state in self.hold_states.values():
   if not state['released']:
    state['event']['actual_hold_seconds']=None if state['first'] is None else time.monotonic()-state['first']
    state['event']['release_reason']='finish_cleanup_attempted'
  report={'action_injections':self.action_injections,'passed':passed,'error':error,'cleanup_errors':cleanup_errors,'players':self.n,'phase':self.phase,'checks':self.checks,'owner_network_evidence':self.rt.world_inventory,'method':'Real owning Enhanced Input for gameplay actions; setup fixtures explicitly described by each case. No direct interaction/round RPC.','wall_clock_deadline_seconds':self.args.get('timeout',240),'test_gate_complete':passed,'full_mission_acceptance_pending':True,'prerequisites':self.prerequisites,'fixtures':self.fixture_description}
  report['test_source_layout_sha256']=getattr(self,'test_source_layout_sha256',None)
  (QUEUE/(self.name+f'-{self.n}.json')).write_text(json.dumps(report,indent=2));self.result=report
 def run(self):
  def tick(delta):
   try:
    assert time.monotonic()<self.deadline,'Test deadline exceeded'
    if getattr(self,'allow_roster_change',False):
     if not self.rt.refresh():return
    elif not self.rt.ready():return
    for pid,deadline in list(self.replica_expectations):
     try:self.rt.replicas_dead(pid,False);self.replica_expectations.remove((pid,deadline))
     except AssertionError:
      if self.rt.clock()>deadline:raise
    for i,target in self.aims.items():self.rt.aim(i,target)
    self.inject_holds()
    self.tick(delta)
   except Exception:self.finish(False,traceback.format_exc())
  self.handle=ue.register_slate_post_tick_callback(tick);registry.handle=self.handle;registry.suite=self
  return {'queued':self.name,'players':self.n,'prerequisites':self.prerequisites,'fixtures':self.fixture_description,'acceptance_pending':True}
