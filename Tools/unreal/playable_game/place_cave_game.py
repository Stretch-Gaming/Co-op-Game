import json
import unreal as ue
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level('/Game/Maps/L_Site01');world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();tag='AdventureCaveSetup'
hc=ue.GameplayStatics.get_streaming_level(world,'L_Site01_HC');pg=ue.GameplayStatics.get_streaming_level(world,'L_Site01_PG')
assert hc and pg
for actor in actors.get_all_level_actors():
 package=actor.get_level().get_outermost().get_name()
 if actor.actor_has_tag(tag) or (package=='/Game/Puzzles/L_Site01_HC' and (actor.actor_has_tag('HC_A2_ArtOnly') or actor.get_class().get_name()=='BP_TestInteractable_C')):assert actors.destroy_actor(actor)
ue.EditorLevelUtils.make_level_current(hc)
def spawn(path,label,location,properties=None,yaw=0,extra_tags=()):
 cls=ue.load_asset(path).generated_class() if isinstance(path,str) else path
 actor=actors.spawn_actor_from_class(cls,ue.Vector(*location),ue.Rotator(yaw=yaw));assert actor
 actor.set_actor_label(label);actor.set_editor_property('tags',[ue.Name(tag)]+[ue.Name(x) for x in extra_tags])
 for key,value in (properties or {}).items():actor.set_editor_property(key,value)
 return actor
def marker(label,location,text):
 actor=spawn(ue.TextRenderActor,label,location,yaw=180);component=actor.text_render;component.set_text(ue.Text(text));component.set_world_size(25);component.set_text_render_color(ue.Color(240,221,162,255));return actor
spawn('/Game/Puzzles/Rounds/BP_RoundDirector','Adventure_RoundDirector',(0,0,0)).set_actor_hidden_in_game(True)
spawn('/Game/Puzzles/Run/BP_RunCoordinator','Adventure_RunCoordinator',(0,0,0)).set_actor_hidden_in_game(True)
for i,x in [(0,-800),(1,2800),(2,5800),(3,11800)]:
 checkpoint=spawn('/Game/Puzzles/BP_Checkpoint','Adventure_Checkpoint_'+str(i),(x,0,100),{'RoundIndex':i})
 for component in checkpoint.get_components_by_class(ue.SceneComponent):
  name=component.get_name()
  for slot in range(4):
   if name=='Spot'+str(slot):component.set_relative_location(ue.Vector(0,(slot-1.5)*150,0),False,False)
pad=spawn('/Game/Puzzles/BP_StartPad','Adventure_StartPad',(800,0,0));pad.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(350,350,160))
visual=spawn(ue.StaticMeshActor,'Adventure_StartPadVisual',(800,0,4));visual.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube'));visual.set_actor_scale3d(ue.Vector(7,7,.08));visual.static_mesh_component.set_material(0,ue.load_asset('/Game/Shared/Style/MI_Stylized_Stone'));visual.static_mesh_component.set_collision_profile_name('NoCollision')
marker('Adventure_StartHint',(800,0,250),'Stand together on the pad for 3 seconds\nF5: add a local teammate | E: interact | V: view | F: headlamp')
for index,x in [(0,2500),(1,5500),(2,11500)]:
 gate=spawn('/Game/Puzzles/BP_ChamberGate','Adventure_ChamberGate_'+str(index),(x,0,0),{'RoundIndex':index,'OpenHeight':650.0},yaw=90)
for index,xy in enumerate([(3200,-800),(3200,800),(4800,-800),(4800,800)]):
 plate=spawn('/Game/Puzzles/BP_PressurePlate','Adventure_Plate_'+str(index),(*xy,0),{'PlateSlot':index},extra_tags=['HC_Round1'])
setup=spawn('/Game/Puzzles/BP_PuzzleSetup','Adventure_PlatePuzzle',(4000,0,0),{'StatueTransforms':[ue.Transform(location=ue.Vector(x,1250,50)) for x in (3500,4000,4500)],'StatueClass':ue.load_asset('/Game/Puzzles/BP_Statue').generated_class()})
marker('Adventure_PlateHint',(4000,0,250),'Carry statues onto plates. Stand on the remaining plates together.')
for index,x in [(2,5700),(3,11700)]:
 entrance=spawn('/Game/Puzzles/BP_RoundStart','Adventure_RoundEntrance_'+str(index),(x,0,120),{'RoundIndex':index});entrance.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(100,190,180))
spawn('/Game/Puzzles/BP_KeyRelic','Adventure_KeyRelic',(7000,2500,50))
spawn('/Game/Puzzles/BP_Altar','Adventure_Altar',(10800,0,0))
marker('Adventure_KeyHint',(7000,0,230),'Find the heavy key in the north tunnel. Carry it to the altar.')
coord=spawn('/Game/Puzzles/Gauntlet/BP_HCGauntletCoordinator','Adventure_GauntletCoordinator',(12500,0,0));coord.set_actor_hidden_in_game(True);coord.set_actor_enable_collision(False)
objective=spawn('/Game/Puzzles/Gauntlet/BP_HCGauntletObjective','Adventure_GauntletObjective',(17000,600,100));objective.get_component_by_class(ue.StaticMeshComponent).set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cylinder'));objective.set_actor_scale3d(ue.Vector(.8,.8,1.8))
marker('Adventure_GauntletHint',(12000,0,250),'Hold the lever to let a teammate through.\nReach the far switch to keep the gate open for everyone.')
for i,loc in enumerate([(-800,1200,75),(1000,-1200,75),(4000,1050,75),(7000,2400,75),(10000,-800,75),(14500,-600,75)]):spawn('/Game/Puzzles/BP_Relic','Adventure_Relic_'+str(i),loc)
ue.EditorLevelUtils.make_level_current(pg)
levers=[]
for actor in actors.get_all_level_actors():
 if actor.get_level().get_outermost().get_name()!='/Game/Player/L_Site01_PG':continue
 if actor.get_class().get_name()=='BP_Lever_C':
  if actor.get_actor_location().x>13000:assert actors.destroy_actor(actor)
  else:
   levers.append(actor);actor.set_editor_property('tags',list(actor.tags)+[ue.Name('HC_GauntletLever')])
 if actor.get_class().get_name()=='BP_GauntletGate_C':actor.set_editor_property('tags',list(actor.tags)+[ue.Name('HC_GauntletGate')])
if len(levers)==1:spawn('/Game/Player/Round3/BP_Lever','Adventure_SecondLever',(12000,600,0),extra_tags=['HC_GauntletLever'])
bridge=spawn('/Game/Player/Round3/BP_PlayableGateBridge','Adventure_GateBridge',(12500,0,0),extra_tags=['HC_GauntletBridge']);bridge.set_actor_hidden_in_game(True);bridge.set_actor_enable_collision(False)
assert editor.set_current_level_by_name('L_Site01')
exit=spawn('/Game/Puzzles/BP_MapExit','Adventure_CaveExit',(26000,0,-1800));exit.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(400,450,300))
assert exit.get_level().get_outermost().get_name()=='/Game/Maps/L_Site01'
assert ue.EditorLoadingAndSavingUtils.save_packages([hc.get_loaded_level().get_outermost(),pg.get_loaded_level().get_outermost(),world.get_outermost()],False)
RESULT={'cave_rounds_placed':3,'map_exit_placed':True,'art_previews_replaced':True,'runtime_acceptance_pending':True}
(QUEUE/'cave-setup.json').write_text(json.dumps(RESULT,indent=2))
