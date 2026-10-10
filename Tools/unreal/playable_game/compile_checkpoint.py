import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
import toolset_registry
prefixes=['/Game/Core','/Game/Puzzles','/Game/Player','/Game/Hazards']
report={'blueprints':[],'errors':[]}
for prefix in prefixes:
 for path in ue.EditorAssetLibrary.list_assets(prefix,True,False):
  obj=ue.load_asset(path)
  if isinstance(obj,ue.Blueprint):
   try:
    with toolset_registry.tool_raising_exceptions():BP.compile_blueprint(obj,warnings_as_errors=True)
    assert obj.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE
    report['blueprints'].append(obj.get_path_name())
   except Exception as error:report['errors'].append({'asset':obj.get_path_name(),'error':str(error)})
(QUEUE/'checkpoint-compile.json').write_text(json.dumps(report,indent=2))
RESULT={'compiled':len(report['blueprints']),'errors':report['errors']}
