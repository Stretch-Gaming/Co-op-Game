"""Validate saved actor assets in a fresh editor, without compiling or saving."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
report={'project':str(ROOT),'engine':unreal.SystemLibrary.get_engine_version(),'read_only':True,'actors':{},'core_saved':False}
interface=unreal.load_asset('/Game/Core/BPI_RoundReset').generated_class()
for name in ACTORS:
    bp=unreal.load_asset('/Game/Puzzles/'+name)
    cdo=BP.get_default_object(bp)
    assert bp.get_editor_property('status')==unreal.BlueprintStatus.BS_UP_TO_DATE
    assert unreal.SystemLibrary.does_implement_interface(cdo,interface)
    assert cdo.get_editor_property('replicates')
    report['actors'][name]={'status':str(bp.get_editor_property('status')),'round_reset':True,'replicates':True,
     'replication':{str(n):str(BP.get_variable_replication(bp,str(n))) for n in BP.list_variables(bp) if 'REP_NOTIFY' in str(BP.get_variable_replication(bp,str(n)))}}
report['dirty_packages']=[p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
report['passed']=not report['dirty_packages']
(OUT/'saved-audit.json').write_text(json.dumps(report,indent=2))
assert report['passed'],report['dirty_packages']
