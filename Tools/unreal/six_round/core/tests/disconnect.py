"""Native remote disconnect at round4 with noncontiguous surviving ColorSlots.
The client uses its local console disconnect; no server destroys its PlayerState.
This is a lifecycle fixture, not an interaction/round RPC shortcut.
"""
import unreal as ue
from framework import Suite
class Disconnect(Suite):
 prerequisites='Round4 Playing in 3/4-player listen/client PIE; remote client owns a middle ColorSlot; this case intentionally removes that client.'
 fixture_description='A remote owner issues native disconnect. Remaining checkpoint/row/door updates must come from GameMode retry.'
 allow_roster_change=True
 def __init__(self,args=None):
  super().__init__('core-disconnect-noncontiguous',args);rt=self.rt;assert self.n in (3,4) and rt.round()['index']==4 and rt.round()['phase']==1
  self.original_slots=[p.player_state.get_editor_property('ColorSlot') for p in rt.players];self.old_attempt=rt.round()['attempt']
  candidates=[i for i,p in enumerate(rt.players) if 0<p.player_state.get_editor_property('ColorSlot')<max(self.original_slots) and rt.local(i).get_world()!=rt.server]
  assert candidates,'Arrange a remote middle-slot client; removing last slot does not test noncontiguous routing'
  i=candidates[0];self.removed_slot=rt.players[i].player_state.get_editor_property('ColorSlot');self.remaining=set(self.original_slots)-{self.removed_slot}
  ue.SystemLibrary.execute_console_command(rt.local(i),'disconnect',rt.local(i).get_controller());self.step('departure')
 def tick(self,delta):
  rt=self.rt;s=rt.round();elapsed=self.elapsed()
  if self.phase=='departure':
   if len(rt.players)==self.n-1:
    assert {p.player_state.get_editor_property('ColorSlot') for p in rt.players}==self.remaining;assert self.remaining!=set(range(self.n-1))
    if s['phase']==3:self.ends=s['ends'];self.step('retry')
   elif elapsed>4:raise AssertionError('Native remote disconnect did not remove roster member')
  elif self.phase=='retry':
   if rt.clock()<self.ends-.06:assert s['attempt']==self.old_attempt
   if s['attempt']>self.old_attempt:
    rt.assert_recovered(4,self.old_attempt);assert s['row']==str(self.n-1)
    for slot in range(4):door=rt.actor('Six_PathDoor_'+str(slot));assert door.get_editor_property('Open')==(slot in self.remaining)
    self.record('Native disconnect retries under new row; original noncontiguous ColorSlots retain their checkpoint/door routes',remaining_slots=sorted(self.remaining));self.finish(True)
