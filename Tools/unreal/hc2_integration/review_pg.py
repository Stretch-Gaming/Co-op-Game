"""Compile the integrated project and inspect the exact reviewed PG subclass."""
import hashlib,json
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
asset='/Game/Player/Test/BP_PG_TestCharacter'
bp=ue.load_asset(asset)
review=json.loads((ROOT/'Tools/unreal/pg_signature_fix/evidence/repair.json').read_text())
assert hashlib.sha256((ROOT/'Content/Player/Test/BP_PG_TestCharacter.uasset').read_bytes()).hexdigest()==review['sha256']
assert ue.BlueprintEditorLibrary.get_blueprint_parent_class(bp).get_path_name()=='/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C'
for name in review['preserved_graphs']:
 assert BP.read_graph_dsl(BP.get_graph(bp,name))==review['after'][name],name
report={'delivery':'a54a2e692ccac00b1e95442de1b64877ef79ee0a','project':str(ROOT),'engine':ue.SystemLibrary.get_engine_version(),'asset_sha256':review['sha256'],'preserved_graphs':review['preserved_graphs'],'compiled':[],'missing_pg':[]}
with toolset_registry.tool_raising_exceptions():
 for path in ue.EditorAssetLibrary.list_assets('/Game',True,False):
  obj=ue.load_asset(path)
  if isinstance(obj,ue.Blueprint):
   BP.compile_blueprint(obj,warnings_as_errors=True)
   assert obj.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE,path
   report['compiled'].append(path)
report['missing_pg']=[p for p in ['/Game/Player/AC_PlayerView','/Game/Player/BPFL_SplitScreen'] if not ue.EditorAssetLibrary.does_asset_exist(p)]
report['passed']=True
(HERE/'pg-compatibility-review.json').write_text(json.dumps(report,indent=2))
# Compiling does not authorize saving unrelated assets.
