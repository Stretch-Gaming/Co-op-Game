import unreal as ue
bp=ue.load_asset('/Game/Core/BP_CoopCharacter');cls=bp.generated_class();ws=ue.EditorLevelLibrary.get_pie_worlds(True)
RESULT={'bp':str(bp),'status':str(bp.status),'class':str(cls),'worlds':[w.get_path_name() for w in ws],'characters':[[{'path':p.get_path_name(),'class':str(p.get_class())} for p in ue.GameplayStatics.get_all_actors_of_class(w,ue.Character)] for w in ws]}
