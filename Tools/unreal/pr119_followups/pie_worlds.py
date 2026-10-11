import unreal as ue
RESULT = [w.get_name() for w in ue.EditorLevelLibrary.get_pie_worlds(True)]
