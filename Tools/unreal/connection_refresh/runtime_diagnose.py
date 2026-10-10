import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
settings=ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings');C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
RESULT={'settings':OBJ.get_properties(settings,['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']),'worlds':[{'world':w.get_path_name(),'server':bool(ue.GameplayStatics.get_game_mode(w)),'players':len(ue.GameplayStatics.get_all_actors_of_class(w,C))}for w in ue.EditorLevelLibrary.get_pie_worlds(True)]}
