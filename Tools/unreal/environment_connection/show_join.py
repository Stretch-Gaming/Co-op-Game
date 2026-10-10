import unreal as ue
world=next(w for w in ue.EditorLevelLibrary.get_pie_worlds(True)if ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();pawn=next(p for p in ue.GameplayStatics.get_all_actors_of_class(world,C)if p.is_locally_controlled());pawn.set_actor_location(ue.Vector(325,1200,100),False,True);pawn.character_movement.stop_movement_immediately();pawn.get_controller().set_control_rotation(ue.Rotator(yaw=90))
if ARGS.get('open'):
 door=ue.GameplayStatics.get_all_actors_with_tag(world,'ConnectionDoor')[0];door.call_method('OpenFromPlayer',args=(pawn,))
RESULT={'near_door':True,'opened':ARGS.get('open',False)}
