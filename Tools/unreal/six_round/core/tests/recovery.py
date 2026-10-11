"""Current-round recovery regressions. Start each at a naturally reached Playing
round. No direct StartRound/ClearRound/FailRound or ResetHealth setup is used.
"""
import unreal as ue
from runtime import LAYOUT
from framework import Suite
class Recovery(Suite):
 prerequisites='Current L_SixRound_Test Playing round, complete possessed roster alive, no taking protection; run each case separately.'
 fixture_description='ApplyDamage deaths; R1/2p lost-statue position or R3/2p exhausted-stock resource setup; free-key below lost-height setup. Recovery itself must be game-driven.'
 def __init__(self,args=None):
  super().__init__('core-recovery',args);rt=self.rt;s=rt.round();assert rt.map()=='L_SixRound_Test' and s['phase']==1 and s['index'] in range(1,7)
  assert all(not rt.dead(i) and not p.get_editor_property('bTakenProtected') for i,p in enumerate(rt.players))
  self.index=s['index'];self.old_attempt=s['attempt'];self.case=self.args.get('case','wipe');self.pid=rt.players[0].player_state.player_id;self.death_started=rt.clock()
  if self.case=='wipe':
   rt.kill(0);self.dead_location=rt.players[0].get_actor_location()
   if self.index in (2,4,6):self.step('dead_input')
   else:
    for i in range(1,self.n):rt.kill(i)
    self.step('await_failure')
  elif self.case=='impossible':
   assert self.index in (1,3,5)
   if self.index==1:
    living_target=1 if self.n in (2,3) else 2
    for i in range(living_target,self.n):rt.kill(i)
    if self.n==2:
     statues=list(rt.actor('Six_PlatePuzzle').get_editor_property('Statues'));assert len(statues)==2
     statues[0].set_actor_location(ue.Vector(0,0,-2100),False,True)
   elif self.index==3:
    for i in range(1,self.n):rt.kill(i)
    if self.n==2:
     assert not ue.GameplayStatics.get_all_actors_of_class(rt.server,ue.load_asset('/Game/Player/Tools/BP_Flare').generated_class()),'Start resource case before any burning flare exists'
     rt.players[0].get_component_by_class(rt.TOOLS).set_editor_property('FlaresLeft',0)
   else:
    living_target=2 if self.n==4 else 1
    for i in range(living_target,self.n):rt.kill(i)
   self.step('await_failure')
  elif self.case=='lost_key':
   assert self.index==6
   carried=next((i for i in range(self.n) if rt.carried(i)==rt.key()),None)
   if carried is not None:self.step('drop_key');self.hold(carried,'IA_Drop')
   else:self.lose_key()
  else:raise AssertionError('case must be wipe, impossible or lost_key')
 def lose_key(self):
  rt=self.rt;key=rt.key();assert key.get_editor_property('CarryState')==0
  if self.args.get('remove_key'):
   key.destroy_actor();assert rt.alive_roster();self.step('await_failure');return
  threshold=LAYOUT.get('round6_bounds',{}).get('key_lost_z_threshold',-1700);pos=key.get_actor_location();key.set_actor_location(ue.Vector(pos.x,pos.y,threshold-400),False,True);key.static_mesh_component.set_physics_linear_velocity(ue.Vector(),False)
  assert rt.alive_roster();self.step('await_failure')
 def tick(self,delta):
  rt=self.rt;s=rt.round();elapsed=self.elapsed()
  if self.phase=='dead_input':
   rt.inject(0,'IA_Move',ue.Vector(0,1,0));rt.inject(0,'IA_Interact',1 if elapsed<.2 else 0)
   if elapsed>.8:
    rt.replicas_dead(self.pid,True);assert (rt.players[0].get_actor_location()-self.dead_location).length()<15;assert s['phase']==1
    self.record('Dead owner cannot move/use or revive while living teammate continues')
    rt.inject(0,'IA_Move',0)
    for i in range(1,self.n):rt.kill(i)
    self.step('await_failure')
  elif self.phase=='drop_key' and elapsed>.8:self.lose_key()
  elif self.phase=='await_failure':
   assert s['index']==self.index and s['attempt']==self.old_attempt
   if s['phase']==3:
    self.failed_at=rt.clock();self.ends=s['ends'];assert 0<self.ends-self.failed_at<=3.2
    if self.case=='lost_key':assert rt.alive_roster(),'Lost-key retry must not rely on player death'
    self.record('Game detects '+self.case+' and enters Failed with server countdown',round=self.index);self.step('countdown')
   elif elapsed>1.5:raise AssertionError('Softlock was not detected by game within resource-monitor budget')
  elif self.phase=='countdown':
   if rt.clock()<self.ends-.06:assert s['attempt']==self.old_attempt and s['phase']==3,'Retry happened before its three-second server deadline'
   if s['attempt']>self.old_attempt:
    assert rt.clock()>=self.ends-.06;rt.assert_recovered(self.index,self.old_attempt)
    if self.index==6:
     key=rt.key();assert key.get_editor_property('CarryState')==0 and (key.get_actor_location()-ue.Vector(*LAYOUT['relic']['key'])).length()<130
     cage=rt.actor('Six_RelicCage');assert cage.get_editor_property('bLatched') and cage.get_editor_property('bRaised')
    self.record('Exactly one attempt advances at deadline; all players recover at ColorSlot checkpoint with correct flares',round=self.index,case=self.case);self.finish(True)
