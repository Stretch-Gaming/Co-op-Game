"""Read-only settled checkpoint gate for the new round threat director.
Run0.6s after a fresh transition, before deaths/joins; no gameplay shortcuts.
"""
import sys
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(ue.Paths.project_dir())/'Tools/unreal/six_round/player/tests'))
from pg_harness import load_harness
Harness=load_harness();h=Harness(ARGS,'pg-round-threats')
director_class=ue.load_asset('/Game/Player/Ghosts/BP_RoundGhostDirector').generated_class()
actors=ue.GameplayStatics.get_all_actors_of_class(h.server,director_class);assert len(actors)==1
director=actors[0]
def tick(delta):
 if h.elapsed()<.6:return
 state=h.round();owned=list(director.get_editor_property('OwnedThreats'));slots=list(director.get_editor_property('SpawnedSlots'))
 active=state['phase']==1 and 1<=state['index']<=5
 if active:
  assert director.get_editor_property('ActiveRound')==state['index']
  assert director.get_editor_property('SpawnedAttempt')==state['attempt']
  if state['index'] in (2,4):
   assert all(not h.prop(p,'health','bDead') for p in h.server_pawns),'Use the fresh-path spawn gate before deaths/joins'
   expected_slots=sorted(p.player_state.get_editor_property('ColorSlot') for p in h.server_pawns)
   assert sorted(slots)==expected_slots and len(set(slots))==len(slots)
   expected=len(expected_slots)
  else:
   expected=int(director.call_method('GetRoomThreatCount'));assert expected in (1,2)
   assert not slots
  assert len(owned)==expected and director.get_editor_property('SpawnedCount')==expected
  for world in h.worlds:
   peer=ue.GameplayStatics.get_all_actors_of_class(world,director_class);assert len(peer)==1
   assert peer[0].get_editor_property('SpawnedCount')==expected
   for actor in owned:assert h.actor_peer(world,actor),'Every owned ghost must have its live peer actor'
 else:
  assert not owned and not slots and director.get_editor_property('SpawnedCount')==0
  assert director.get_editor_property('ActiveRound')==0
  for world in h.worlds:
   peer=ue.GameplayStatics.get_all_actors_of_class(world,director_class);assert len(peer)==1
   assert peer[0].get_editor_property('SpawnedCount')==0
 h.check('settled round threat spawn/cleanup and peer actor gate',{'round_state':state,'active':active,'slots':slots,'owned_actor_names':[a.get_name() for a in owned],'scope':'current checkpoint only; repeat per round/attempt and nonPlaying; entering6 may have separate chase actors'})
 h.finish(True)
RESULT=h.register(tick)
