"""Read-only native roster/state snapshot for serialized QA preparation."""
import json
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
classes={key:ue.load_asset(path).generated_class() for key,path in {'pawn':'/Game/Core/BP_CoopCharacter','health':'/Game/Hazards/AC_Health','tools':'/Game/Player/Tools/AC_Tools','traversal':'/Game/Player/AC_Traversal'}.items()}
data=[]
for world in worlds:
 players=[]
 for pawn in ue.GameplayStatics.get_all_actors_of_class(world,classes['pawn']):
  position=pawn.get_actor_location();health=pawn.get_component_by_class(classes['health']);tools=pawn.get_component_by_class(classes['tools']);traversal=pawn.get_component_by_class(classes['traversal'])
  players.append({'id':pawn.player_state.player_id if pawn.player_state else None,'slot':pawn.player_state.get_editor_property('ColorSlot') if pawn.player_state else None,'local':pawn.is_locally_controlled(),'controller':pawn.get_controller().get_name() if pawn.get_controller() else None,'dead':health.get_editor_property('bDead'),'flares':tools.get_editor_property('FlaresLeft'),'six_input_ready':pawn.get_editor_property('SixInputReady'),'walk_speed':pawn.character_movement.max_walk_speed,'traversal_walk':traversal.get_editor_property('WalkSpeed'),'traversal_sprint':traversal.get_editor_property('SprintSpeed'),'position':[position.x,position.y,position.z]})
 data.append({'world':world.get_name(),'server':ue.SystemLibrary.is_server(world),'dedicated':ue.SystemLibrary.is_dedicated_server(world),'players':players})
RESULT={'worlds':data};(QUEUE/'qa-roster.json').write_text(json.dumps(RESULT,indent=2))
