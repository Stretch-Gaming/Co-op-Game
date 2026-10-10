"""Walk owners through the cleared maze mouth; audit server-scheduled taking.
Initial corridor approaches and protected-damage checks are explicit fixtures.
"""
import sys,json
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
Harness=load_harness()
h=Harness(ARGS,'pg-taking');assert h.round()['index']==1 and h.round()['phase']==2,'Run immediately after native plates clear Round1'
layout=json.loads((h.root/'Tools/unreal/six_round/world/positions.json').read_text())
directors=ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['taking']);assert len(directors)==1
director=directors[0];state={'victims':{},'last_active':None,'origins':{}}
mouth=layout['maze_mouth']
for ordinal,pid in enumerate(h.ids):
 approach=(mouth['center'][0],mouth['center'][1]-mouth['extent'][1]-180-ordinal*35,100)
 h.fixture_place(pid,approach);h.locals[pid].get_controller().set_control_rotation(ue.Rotator(yaw=90));h.hold(pid,'move',ue.Vector(0,1,0))
 h.fixtures.append({'kind':'owning controller facing fixture','player_id':pid,'yaw':90})
h.transition('mouth_walk')
def tick(delta):
 elapsed=h.elapsed()
 if h.phase=='mouth_walk':
  if h.round()['index']==2:
   h.release_all();state['origins']={pid:h.pawn(h.server,pid).get_actor_location() for pid in h.ids}
   h.check('all actual owners entered the maze mouth through normal movement input; Round2 started')
   h.transition('taking')
  return
 assert h.round()['index']==2 and h.round()['phase']==1
 victim=director.get_editor_property('Victim')
 now=ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds()
 if victim:
  pid=victim.player_state.player_id;started=director.get_editor_property('TakingStarted')
  origin=director.get_editor_property('VictimOrigin');age=now-started
  if pid not in state['victims']:
   assert victim.get_editor_property('bTakenProtected')
   health=h.prop(victim,'health','Health')
   ue.GameplayStatics.apply_damage(victim,9999,None,None,None)
   assert h.prop(victim,'health','Health')==health and not h.prop(victim,'health','bDead')
   h.fixtures.append({'kind':'ApplyDamage against the already protected scheduled victim','player_id':pid})
   state['victims'][pid]={'scheduled_start':started,'style':director.get_editor_property('ScareStyle'),'origin':[origin.x,origin.y,origin.z],'protected_damage_ignored':True,'teleport_seen':False}
  if age<.60:assert (victim.get_actor_location()-origin).length()<20,'Taking must not teleport before the screen-cover schedule'
  if age>.85:
   slot=victim.player_state.get_editor_property('ColorSlot');expected=ue.Vector(*layout['first_path_starts'][slot])
   assert (victim.get_actor_location()-expected).length()<100,'Taking destination must follow the actual ColorSlot'
   state['victims'][pid]['teleport_seen']=True
  if age>.25:
   for world in h.worlds:
    peer=ue.GameplayStatics.get_all_actors_of_class(world,h.classes['taking']);assert len(peer)==1
    peer_victim=peer[0].get_editor_property('Victim')
    assert peer_victim and peer_victim.player_state.player_id==pid
    assert abs(peer[0].get_editor_property('TakingStarted')-started)<.02
    assert peer[0].get_editor_property('ScareStyle')==director.get_editor_property('ScareStyle')
 else:
  seals=ue.GameplayStatics.get_all_actors_of_class(h.server,ue.load_asset('/Game/Hazards/Maze/BP_MouthSeal').generated_class())
  if len(state['victims'])==h.n-1 and seals and seals[0].get_editor_property('OpenPath')>=0:
   assert all(record['teleport_seen'] for record in state['victims'].values())
   remaining=set(h.ids)-set(state['victims']);assert len(remaining)==1
   remaining_id=next(iter(remaining));remaining_pawn=h.pawn(h.server,remaining_id)
   assert seals[0].get_editor_property('OpenPath')==remaining_pawn.player_state.get_editor_property('ColorSlot')
   assert (remaining_pawn.get_actor_location()-state['origins'][remaining_id]).length()<100
   assert all(not pawn.get_editor_property('bTakenProtected') for pawn in h.server_pawns)
   h.check('exactlyN-1 scheduled victims are immune then moved to their own paths; the real remaining slot stays open',{'victims':state['victims'],'remaining_id':remaining_id})
   h.finish(True)
RESULT=h.register(tick)

