import json,unreal as ue
rows=[]
for world in ue.EditorLevelLibrary.get_pie_worlds(True):
 bats=ue.GameplayStatics.get_all_actors_of_class(world,ue.load_asset('/Game/Player/Critters/BP_CaveBat').generated_class());rats=ue.GameplayStatics.get_all_actors_of_class(world,ue.load_asset('/Game/Player/Critters/BP_CaveRat').generated_class())
 hanging=[a for a in ue.GameplayStatics.get_all_actors_of_class(world,ue.StaticMeshActor) if a.get_actor_label().startswith('PG_A5_BatHanging_')]
 assert len(bats)==5 and len(rats)==6 and len(hanging)==22,(world,len(bats),len(rats),len(hanging))
 rows.append({'world':world.get_path_name(),'flying_bats':len(bats),'hanging_bats':len(hanging),'rats':len(rats)})
RESULT={'passed':True,'worlds':rows}
(QUEUE/'delivered-critters-runtime.json').write_text(json.dumps(RESULT,indent=2))
