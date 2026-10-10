"""Full-editor -ExecutePythonScript wrapper; pass -HCA1Execute for creation."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unreal as ue
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import import_relics
execute='-HCA1Execute' in ue.SystemLibrary.get_command_line().split()
args=['--project-root',str(HERE.parents[2]),'--material-bindings',str(HERE/'material_bindings.reviewed.json')]
args+=['--execute'] if execute else ['--editor-check']
stream=io.StringIO()
with contextlib.redirect_stdout(stream):
 code=import_relics.main(args)
text=stream.getvalue()
ue.log(text)
assert code==0,'HC-A1 importer returned '+str(code)
report=json.loads(text)
(HERE/('engine_import.json' if execute else 'engine_import_preflight.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
ue.log('HC-A1_IMPORT_COMPLETE' if execute else 'HC-A1_PREFLIGHT_COMPLETE')
