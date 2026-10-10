import unreal as ue
world=next(w for w in ue.EditorLevelLibrary.get_pie_worlds(True)if ue.GameplayStatics.get_game_mode(w))
controller=next(p for p in ue.ObjectIterator(ue.PlayerController)if p.get_world()==world and p.is_local_controller()and p.is_primary_player())
controller.call_method('HostAddLocalPlayer')
RESULT={'host_second_local_player_requested':True}
