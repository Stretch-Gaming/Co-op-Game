import json,os,unreal as ue
from pathlib import Path
identity={'project':str(Path(ue.Paths.project_dir()).resolve()),'engine':ue.SystemLibrary.get_engine_version(),'pid':os.getpid(),'port':8017,'requested_renderer':'D3D11; ray tracing disabled only by launch args','blueprint_only':True}
assert Path(identity['project'])==ROOT and identity['engine'].startswith('5.8.3-58210709')
(HERE/'editor-identity.json').write_text(json.dumps(identity,indent=2));ue.log('HC_RUN_ENDING_VERIFIED_IDENTITY: '+json.dumps(identity))
