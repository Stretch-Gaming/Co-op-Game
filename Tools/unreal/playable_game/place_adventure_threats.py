import unreal as ue
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
tag='AdventureThreatSetup'
def world_map(path):
 assert editor.load_level(path)
 world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
 for actor in actors.get_all_level_actors():
  if actor.actor_has_tag(tag):assert actors.destroy_actor(actor)
 return world
def spawn(path,label,position,props=None):
 actor=actors.spawn_actor_from_class(ue.load_asset(path).generated_class(),ue.Vector(*position),ue.Rotator());assert actor
 actor.set_actor_label(label);actor.set_editor_property('tags',[ue.Name(tag)])
 for name,value in (props or {}).items():actor.set_editor_property(name,value)
 return actor
world=world_map('/Game/Maps/L_Site01');hz=ue.GameplayStatics.get_streaming_level(world,'L_Site01_HZ');pg=ue.GameplayStatics.get_streaming_level(world,'L_Site01_PG')
ue.EditorLevelUtils.make_level_current(hz)
traps=[('Spikes',(2000,0,0)),('Darts',(6200,0,0)),('Swing',(7200,0,0)),('Spikes',(8000,0,0)),('Spikes',(7000,1200,0)),('Swing',(14000,0,0)),('Swing',(15500,0,0)),('Spikes',(14800,0,0)),('Darts',(16000,0,0))]
for i,(kind,pos) in enumerate(traps):spawn('/Game/Hazards/Traps/BP_Trap_'+kind,'Adventure_Trap_'+str(i),pos)
fall=spawn('/Game/Hazards/Traps/BP_FallVolume','Adventure_CaveFall',(23000,0,-3300));fall.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(7000,3000,150))
assert ue.EditorLoadingAndSavingUtils.save_packages([hz.get_loaded_level().get_outermost()],False)
ue.EditorLevelUtils.make_level_current(pg)
for actor in actors.get_all_level_actors():
 if actor.get_level().get_outermost().get_name()=='/Game/Player/L_Site01_PG' and actor.get_class().get_name()=='BP_Ghost_C':assert actors.destroy_actor(actor)
for index,x,offset in [(1,4000,1200),(2,10000,900),(3,15000,600)]:spawn('/Game/Player/Ghosts/BP_GhostSpawner','Adventure_GhostSpawner_'+str(index),(x,0,0),{'RoundIndex':index,'SpawnOffset':ue.Vector(0,offset,150)})
assert ue.EditorLoadingAndSavingUtils.save_packages([pg.get_loaded_level().get_outermost()],False)
world=world_map('/Game/Maps/L_Maze');hc=ue.GameplayStatics.get_streaming_level(world,'L_Maze_HC');pg=ue.GameplayStatics.get_streaming_level(world,'L_Maze_PG');hz=ue.GameplayStatics.get_streaming_level(world,'L_Maze_HZ')
ue.EditorLevelUtils.make_level_current(hc)
spawn('/Game/Puzzles/Rounds/BP_RoundDirector','Maze_RoundDirector',(0,0,0)).set_actor_hidden_in_game(True)
spawn('/Game/Puzzles/Maze/BP_MazeProgress','Maze_Progress',(0,0,0)).set_actor_hidden_in_game(True)
for index in (0,1):
 checkpoint=spawn('/Game/Puzzles/BP_Checkpoint','Maze_Checkpoint_'+str(index),(-500,0,100),{'RoundIndex':index})
 for component in checkpoint.get_components_by_class(ue.SceneComponent):
  for slot in range(4):
   if component.get_name()=='Spot'+str(slot):component.set_relative_location(ue.Vector(0,(slot-1.5)*150,0),False,False)
pad=spawn('/Game/Puzzles/BP_StartPad','Maze_StartPad',(-500,0,0));pad.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(350,400,160))
assert ue.EditorLoadingAndSavingUtils.save_packages([hc.get_loaded_level().get_outermost()],False)
ue.EditorLevelUtils.make_level_current(pg)
spawn('/Game/Player/Ghosts/BP_GhostSpawner','Maze_GhostSpawner',(0,9250,-300),{'RoundIndex':1,'SpawnOffset':ue.Vector(900,0,150)})
assert ue.EditorLoadingAndSavingUtils.save_packages([pg.get_loaded_level().get_outermost()],False)
ue.EditorLevelUtils.make_level_current(hz)
fall=spawn('/Game/Hazards/Traps/BP_FallVolume','Maze_Fall',(0,13000,-1800));fall.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(10000,14000,150))
assert ue.EditorLoadingAndSavingUtils.save_packages([hz.get_loaded_level().get_outermost()],False)
RESULT={'cave_traps':len(traps),'ghost_spawners':4,'maze_checkpoints':True,'falls_recover':True,'runtime_acceptance_pending':True}
