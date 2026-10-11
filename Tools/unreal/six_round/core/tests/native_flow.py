"""Two full native puzzle transactions with feasible dead regroups and travel.
This is not the walking/traversal/chase presentation gate: approach teleports,
released statue settling, temporary nearby small-relic relocation, and separating
chase ghosts during focused transaction checks are explicit fixtures.
"""
import time
import unreal as ue
import time
from runtime import LAYOUT
from framework import Suite
class NativeFlow(Suite):
 prerequisites='Fresh L_SixRound_Test Lobby; 2/3/4 possessed input owners; local listen-host required when runs=2; all reset/interface/RPC/input assets compiled.'
 fixture_description='Server approach positions, ApplyDamage victims, released statue placement, restoring nearby small relics, moving chase ghosts away for focused transactions. No gameplay RPC shortcuts.'
 def __init__(self,args=None):
  super().__init__('core-two-run-native',args);assert self.rt.map()=='L_SixRound_Test'
  self.prepare_round=self.args.get('prepare_round');self.runs=1 if self.prepare_round else self.args.get('runs',2);self.run_number=1
  if self.runs>1:assert any(self.rt.local(i).get_world()==self.rt.server and self.rt.local(i).get_controller().is_primary_player() for i in range(self.n)),'Native host R restart needs a listen-server local host (dedicated clients have none)'
  if self.args.get('continue_escape') or self.args.get('continue_delivery'):
   assert self.runs==1 and self.rt.round()['index']==6 and self.rt.round()['phase']==1
   self.carrier=next(i for i in range(self.n) if self.rt.carried(i)==self.rt.key())
   self.pending_dead=[];self.name='core-native-delivery' if self.args.get('continue_delivery') else 'core-native-escape'
   self.prerequisites='Actual R6 Playing with a real held key from the owning-input cage/re-pick gates; earlier rounds are separate evidence.'
   if self.args.get('continue_delivery'):
    self.unfocus();self.focus(self.carrier,self.rt.actor('Six_DropoffAltar'));self.score_before=self.rt.gs.get_editor_property('RelicsCollected');self.accept_before=self.rt.actor('Six_DropoffAltar').get_editor_property('AcceptCount');self.step('altar_focus')
    self.record('Delivery continues after actual carrier death, drop and native teammate re-pick; earlier escape checks are separate evidence')
   else:
    self.step('prepare_escape');self.record('Escape starts from actual key lift proven by the dedicated cage input gate; earlier rounds are separate evidence')
  else:
   assert self.rt.round()['index']==0;self.prepare_run()
 def prepare_run(self):
  rt=self.rt;self.victim=0;self.pending_dead=[];self.statue_index=0;self.carrier=None;self.unfocus()
  assert len(set(p.player_state.get_editor_property('ColorSlot') for p in rt.players))==self.n
  for i in range(self.n):assert not rt.dead(i) and rt.carried(i) is None;rt.place(i,(800,(i-(self.n-1)/2)*105,100))
  assert rt.gs.get_editor_property('RelicsCollected')==0
  self.step('pad')
 def living_input_owners(self):
  # Prefer actual remote clients for transaction input; split owners remain independent.
  return sorted(self.rt.alive_roster(),key=lambda i:self.rt.local(i).get_world()==self.rt.server)
 def kill_for_regroup(self):
  rt=self.rt;rt.kill(self.victim);self.pending_dead=[self.victim];rt.place(self.victim,(-1000,-900,100));assert rt.dead(self.victim)
 def assert_dead_until_clear(self):
  for i in self.pending_dead:assert self.rt.dead(i),'Player revived before a round clear'
 def separate_ghosts(self):
  # Focused core transaction fixture; chase behavior has its own PG runtime gate.
  cls=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
  for ghost in ue.GameplayStatics.get_all_actors_of_class(self.rt.server,cls):ghost.set_actor_location(ue.Vector(40000,40000,2000),False,True)
 def verify_travel_delay(self):
  # Server world time restarts when travel replaces the world. The completion
  # observation may be one input tick after the server change, hence 0.1s tolerance.
  delay=time.monotonic()-self.completed_at
  assert delay>=4.9,('Results travel occurred before the five-second hold',delay)
  return delay
 def tick(self,delta):
  rt=self.rt;s=rt.round();elapsed=self.elapsed();step=self.phase
  if self.prepare_round and s['index']==self.prepare_round and s['phase']==1 and all(not rt.dead(i) and not p.get_editor_property('bTakenProtected') for i,p in enumerate(rt.players)) and (self.prepare_round!=2 or (step=='taking' and elapsed>24)):
   self.record('Naturally reached requested test round using prior native puzzle inputs',round=self.prepare_round);self.finish(True);return
  if rt.map()=='L_SixRound_Test' and s['index']<6:assert not rt.actor('Six_DropoffAltar').get_editor_property('Completed'),'Mission completed before escape'
  if step=='pad' and elapsed>4:
   assert s['index']==1 and s['phase']==1;self.kill_for_regroup();self.owner=self.living_input_owners()[0]
   self.focus(self.owner,rt.actor('Six_DropoffAltar'));self.step('early_altar');self.hold(self.owner)
  elif step=='early_altar' and elapsed>1:
   self.assert_dead_until_clear();assert not rt.actor('Six_DropoffAltar').get_editor_property('Completed');assert s['index']==1 and s['phase']==1
   self.unfocus();self.statues=list(rt.actor('Six_PlatePuzzle').get_editor_property('Statues'));assert len(self.statues)==(2 if self.n==2 else 1)
   self.focus(self.owner,self.statues[0]);self.step('statue_focus')
  elif step=='statue_focus' and elapsed>.8:
   self.assert_dead_until_clear();assert rt.focused(self.owner,self.statues[self.statue_index]);self.step('statue_pickup');self.hold(self.owner)
  elif step=='statue_pickup' and elapsed>.8:
   self.assert_dead_until_clear();assert rt.carried(self.owner)==self.statues[self.statue_index]
   self.unfocus();pos=LAYOUT['plates'][self.statue_index];rt.place(self.owner,(pos[0]-120,pos[1],pos[2]+100));self.step('statue_drop');self.hold(self.owner,'IA_Drop')
  elif step=='statue_drop' and elapsed>.8:
   assert rt.carried(self.owner) is None;statue=self.statues[self.statue_index];pos=LAYOUT['plates'][self.statue_index]
   statue.set_actor_location(ue.Vector(pos[0],pos[1],pos[2]+50),False,True);statue.static_mesh_component.set_physics_linear_velocity(ue.Vector(),False)
   self.statue_index+=1
   if self.statue_index<len(self.statues):self.focus(self.owner,self.statues[self.statue_index]);self.step('statue_focus')
   else:
    survivors=rt.alive_roster();first=len(self.statues);plate_count=4 if self.n==4 else 3
    for i,player in enumerate(survivors):pos=LAYOUT['plates'][first+i%(plate_count-first)];rt.place(player,(pos[0],pos[1],pos[2]+100))
    self.step('plates_clear')
  elif step=='plates_clear':
   if s['phase']==1:self.assert_dead_until_clear()
   if s['index']==1 and s['phase']==2:
    rt.assert_regroup(self.pending_dead,1);self.expect_alive_replicas(self.pending_dead);self.pending_dead=[];self.record('Round1 native plate solution revives the dead at first-room regroup',run=self.run_number)
    # Door rises 450cm at 600cm/s after the clear, not after initial plate setup.
    self.step('door_open_wait')
  elif step=='door_open_wait' and elapsed>.9:
   assert s['index']==1 and s['phase']==2
   assert rt.actor('Six_ConnectionDoor').get_actor_location().z>640
   for i in range(self.n):pos=LAYOUT['maze_mouth']['center'];rt.place(i,(pos[0],pos[1]+(i-(self.n-1)/2)*100,pos[2]))
   self.step('taking')
  elif step=='taking' and elapsed>24:
   assert s['index']==2 and s['phase']==1;assert not any(p.get_editor_property('bTakenProtected') for p in rt.players);assert rt.actor('Six_ConnectionDoor').get_actor_location().z<201
   self.kill_for_regroup()
   for i in rt.alive_roster():rt.place(i,LAYOUT['checkpoints']['3'][i])
   self.step('meeting_regroup')
  elif step=='meeting_regroup':
   if s['index']==2:self.assert_dead_until_clear()
   if s['index']==3:
    rt.assert_regroup(self.pending_dead,3);self.expect_alive_replicas(self.pending_dead);self.pending_dead=[];self.record('Round2 every-living regroup immediately restores the dead in meeting hall',run=self.run_number);self.step('prepare_meeting')
  elif step=='prepare_meeting' and elapsed>.9:
    self.kill_for_regroup();owners=self.living_input_owners();self.beam_owners=owners[:(1 if self.n==2 else 2)];self.flare_owners=[owners[i%len(owners)] for i in range(1 if self.n<4 else 2)]
    for bowl,i in enumerate(self.flare_owners):target=rt.actor('Six_braziers_'+str(bowl));pos=target.get_actor_location();rt.place(i,(pos.x-90,pos.y,pos.z+100));rt.local(i).get_controller().set_control_rotation(ue.Rotator(pitch=-60))
    self.step('flare_throw')
    for i in self.flare_owners:self.hold(i,'IA_ThrowFlare')
  elif step=='flare_throw' and elapsed>1:
   self.assert_dead_until_clear()
   for lock,i in enumerate(self.beam_owners):
    self.focus(i,rt.actor('Six_headlamp_locks_'+str(lock)));view=rt.local(i).get_component_by_class(ue.load_asset('/Game/Player/AC_PlayerView').generated_class())
    if not view.call_method('GetHeadlampOn'):rt.inject(i,'IA_Headlamp',1);rt.inject(i,'IA_Headlamp',0)
   self.step('meeting_locks')
  elif step=='meeting_locks':
   if s['index']==3:self.assert_dead_until_clear()
   if s['index']==4:
    rt.assert_regroup(self.pending_dead,3);self.expect_alive_replicas(self.pending_dead);self.pending_dead=[];self.unfocus();self.record('Round3 native headlamp/flare simultaneous locks revive dead at hall regroup',run=self.run_number);self.step('prepare_deep')
  elif step=='prepare_deep' and elapsed>.9:
    self.kill_for_regroup()
    for i in rt.alive_roster():rt.place(i,LAYOUT['checkpoints']['5'][i])
    self.step('relic_regroup')
  elif step=='relic_regroup':
   if s['index']==4:self.assert_dead_until_clear()
   if s['index']==5:
    rt.assert_regroup(self.pending_dead,5);self.expect_alive_replicas(self.pending_dead);self.pending_dead=[];self.record('Round4 every-living relic-chamber regroup restores dead',run=self.run_number);self.step('prepare_relic')
  elif step=='prepare_relic' and elapsed>.9:
    if self.n>=3:self.kill_for_regroup()
    owners=self.living_input_owners();lever_count=2 if self.n==4 else 1;self.lever_owners=owners[:lever_count];self.carrier=owners[-1]
    for lever,i in enumerate(self.lever_owners):self.focus(i,rt.actor('Six_RelicLever_'+str(lever)))
    self.focus(self.carrier,rt.key());self.step('lever_focus')
  elif step=='lever_focus' and elapsed>.8:
    if not all(rt.focused(i,rt.actor('Six_RelicLever_'+str(lever))) for lever,i in enumerate(self.lever_owners)):return
    self.step('cage_hold')
    for i in self.lever_owners:self.hold(i,duration=20)
  elif step=='cage_hold' and elapsed>1:
   if self.pending_dead:self.assert_dead_until_clear()
   assert rt.actor('Six_RelicCage').get_editor_property('bRaised') or rt.actor('Six_RelicCage').get_editor_property('bLatched');assert rt.focused(self.carrier,rt.key())
   # Holders keep their buttons down while another player lifts the key.
   self.phase='key_pickup';self.started=time.monotonic()
   self.hold(self.carrier)
  elif step=='key_pickup':
   if s['index']==5 and self.pending_dead:self.assert_dead_until_clear()
   if s['index']==6:
    if self.pending_dead:rt.assert_regroup(self.pending_dead,5);self.expect_alive_replicas(self.pending_dead)
    self.pending_dead=[];self.unfocus();assert rt.carried(self.carrier)==rt.key();self.record('Native held levers and key lift enter escape; feasible R5 deaths regroup',run=self.run_number);self.step('prepare_escape')
  elif step=='prepare_escape' and elapsed>.9:
    self.separate_ghosts();rt.kill(self.carrier);self.dropped_carrier=self.carrier;self.carrier=next(i for i in self.living_input_owners() if i!=self.dropped_carrier);self.step('carrier_drop')
  elif step=='carrier_drop' and elapsed>.8:
   self.separate_ghosts();assert rt.dead(self.dropped_carrier);assert rt.carried(self.dropped_carrier) is None;assert rt.key().get_editor_property('CarryState')==0;assert s['index']==6 and s['phase']==1
   self.focus(self.carrier,rt.key());self.step('re_pick_focus')
  elif step=='re_pick_focus' and elapsed>.8:
   self.separate_ghosts();assert rt.focused(self.carrier,rt.key());self.step('re_pick');self.hold(self.carrier)
  elif step=='re_pick' and elapsed>.8:
   self.separate_ghosts();assert rt.carried(self.carrier)==rt.key();assert rt.dead(self.dropped_carrier)
   self.record('Carrier lethal damage drops relic; native living teammate re-picks during escape',run=self.run_number)
   self.unfocus();self.focus(self.carrier,rt.actor('Six_DropoffAltar'));self.score_before=rt.gs.get_editor_property('RelicsCollected');self.accept_before=rt.actor('Six_DropoffAltar').get_editor_property('AcceptCount');self.step('altar_focus')
  elif step=='altar_focus' and elapsed>.8:
   self.separate_ghosts();assert rt.focused(self.carrier,rt.actor('Six_DropoffAltar'));self.step('altar_use');self.hold(self.carrier)
  elif step=='altar_use':
   self.separate_ghosts()
   if s['phase']==4:
    self.completed_at=time.monotonic();self.expected_score=self.score_before+1;self.expected_available=rt.gs.get_editor_property('RelicsAvailable');assert rt.gs.get_editor_property('RelicsCollected')==self.expected_score;assert rt.actor('Six_DropoffAltar').get_editor_property('AcceptCount')==self.accept_before+1
    self.unfocus();self.step('completion_hold');self.hold(self.carrier,duration=2)
  elif step=='completion_hold':
   if rt.map()=='L_Site02':
    self.verify_travel_delay()
    self.step('travel');return
   assert rt.map()=='L_SixRound_Test';assert rt.gs.get_editor_property('RelicsCollected')==self.expected_score;assert rt.actor('Six_DropoffAltar').get_editor_property('AcceptCount')==self.accept_before+1
   if time.monotonic()-self.completed_at>4.0:self.record('Altar transaction remains counted exactly once before results travel',run=self.run_number);self.holds={};self.step('travel')
  elif step=='travel':
   if rt.map()=='L_Site02':
    travel_delay=self.verify_travel_delay()
    assert all(ue.GameplayStatics.get_current_level_name(rt.local(i).get_world(),True)=='L_Site02' for i in range(self.n));assert rt.mode().get_class().get_name()=='BP_SixRoundTestGameMode_C';assert rt.gs.get_editor_property('RelicsCollected')==self.expected_score and rt.gs.get_editor_property('RelicsAvailable')==self.expected_available
    self.record('All owners arrive after the five-second hold with persistent counts and test GameMode',run=self.run_number,observed_travel_delay_seconds=travel_delay,minimum_delay_seconds=4.9,clock='monotonic across world replacement');self.step('results')
  elif step=='results' and elapsed>1:
   cls=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults').generated_class()
   for i in range(self.n):widget=rt.local(i).get_controller().get_component_by_class(cls).get_editor_property('ResultsWidget');assert widget and widget.get_owning_player()==rt.local(i).get_controller()
   if self.run_number>=self.runs:self.finish(True);return
   self.host=next(i for i in range(self.n) if rt.local(i).get_world()==rt.server and rt.local(i).get_controller().is_primary_player());self.step('restart');self.hold(self.host,'IA_RunRestart')
  elif step=='restart':
   if rt.map()=='L_SixRound_Test' and s['index']==0:
    self.run_number+=1;self.record('Native host R restarts all clients/split owners into a fresh second run',run=self.run_number);self.prepare_run()
