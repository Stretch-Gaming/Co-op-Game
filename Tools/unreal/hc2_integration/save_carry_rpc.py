import unreal as ue,json
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
c=ue.load_asset('/Game/Core/BP_CoopCharacter');BP.compile_blueprint(c);assert c.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
assert ue.EditorAssetLibrary.save_loaded_asset(c)
(HERE/'carry-rpc-saved.json').write_text(json.dumps({'passed':True,'event':'Server_DropCarried','compile':str(c.get_editor_property('status'))}))
