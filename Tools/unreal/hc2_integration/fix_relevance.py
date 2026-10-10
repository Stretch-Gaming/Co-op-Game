import unreal as ue,json
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
r=ue.load_asset('/Game/Puzzles/BP_Relic');BP.compile_blueprint(r)
assert r.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
cdo=ue.get_default_object(r.generated_class());cdo.set_editor_property('always_relevant',True)
assert cdo.get_editor_property('always_relevant')
assert ue.EditorAssetLibrary.save_loaded_asset(r)
(HERE/'relevance-fix.json').write_text(json.dumps({'passed':True,'AlwaysRelevant':True,'reason':'hidden collision-disabled StaticMeshActor otherwise fails relevance for fresh client worlds'}))
