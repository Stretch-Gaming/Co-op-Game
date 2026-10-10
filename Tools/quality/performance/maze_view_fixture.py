import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert len(worlds)==1 and 'L_ConnectedRoomMaze' in worlds[0].get_path_name()
world=worlds[0];C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();players=ue.GameplayStatics.get_all_actors_of_class(world,C);assert len(players)==1
pawn=next(iter(players));assert pawn.is_locally_controlled();pawn.character_movement.stop_movement_immediately()
pawn.set_actor_location(ue.Vector(325,3600,100),False,True);pawn.get_controller().set_control_rotation(ue.Rotator(yaw=90))
RESULT={'fixture':'Fixed maze-fork camera for performance; only our temporary test pawn moved.','user_game_untouched':True}
