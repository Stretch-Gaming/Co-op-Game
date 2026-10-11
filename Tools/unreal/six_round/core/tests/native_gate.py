"""Every owning client/local pair attempts native closed entrance bypass."""
import unreal as ue
from framework import Suite
class NativeGate(Suite):
 prerequisites='Fresh L_SixRound_Test Lobby, 2/3/4 input owners; no other active test callback.'
 fixture_description='Only server approach positions and facing; movement and Interact are actual owning input.'
 def __init__(self,args=None):
  super().__init__('core-native-door',args);assert self.rt.map()=='L_SixRound_Test' and self.rt.round()['index']==0;self.owner=0;self.approach()
 def approach(self):self.rt.place(self.owner,(325,1200,100));self.rt.local(self.owner).get_controller().set_control_rotation(ue.Rotator(yaw=90));self.step('blocked')
 def tick(self,delta):
  rt=self.rt;elapsed=self.elapsed();rt.inject(self.owner,'IA_Move',ue.Vector(0,1,0));rt.inject(self.owner,'IA_Interact',1 if elapsed<.3 else 0)
  if elapsed>2:
   for world in rt.worlds:
    doors=rt.tagged('ConnectionDoor',world);assert len(doors)==1;assert not doors[0].get_editor_property('Open') and abs(doors[0].get_actor_location().z-200)<1
   assert rt.players[self.owner].get_actor_location().y<1380;assert rt.round()['index']==0
   self.record('Native E cannot bypass puzzle door; native walking meets closed collision',owner_id=rt.players[self.owner].player_state.player_id,owner_world=rt.local(self.owner).get_world().get_name())
   rt.inject(self.owner,'IA_Move',0);rt.place(self.owner,(-1000,100*self.owner,100));self.owner+=1
   if self.owner==self.n:self.finish(True)
   else:self.approach()
