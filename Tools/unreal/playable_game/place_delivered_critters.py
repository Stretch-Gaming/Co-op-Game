import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
import toolset_registry
assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level('/Game/Maps/L_Site01')
source=ROOT/'Tools/unreal/pg_a5_critters/place_critters.py'
text=source.read_text(encoding='utf-8-sig').replace('OUT = Path("/tmp/pga5_tools/out.json")',"OUT = QUEUE / 'critter-placement.json'")
namespace={'__file__':str(source),'__name__':'__main__','QUEUE':QUEUE}
exec(compile(text,str(source),'exec'),namespace)
report=json.loads((QUEUE/'critter-placement.json').read_text());assert not report.get('error'),report
assert report['saved'] and not report['outside_pg']
for path in ['/Game/Player/Critters/BP_CaveBat','/Game/Player/Critters/BP_CaveRat']:
 with toolset_registry.tool_raising_exceptions():BP.compile_blueprint(ue.load_asset(path),warnings_as_errors=True)
RESULT={'hanging_bats':len(report['hanging']),'flying_bats':len(report['flying']),'rats':len(report['rats']),'skipped':report['skipped'],'compiled':True}
