import unreal as ue
world=next(w for w in ue.EditorLevelLibrary.get_pie_worlds(True)if ue.GameplayStatics.get_game_mode(w))
ue.SystemLibrary.execute_console_command(world,'Shot SHOWUI')
RESULT={'screenshot_requested':True}
