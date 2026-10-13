import json,sys
sys.path.insert(0,str(HERE))
from context import *
import latest_scene
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
script=ROOT/'Tools/unreal/six_round/world/check_geometry.py'
code=script.read_text(encoding='utf-8-sig')
needle='captured=scene_ops.scene(ROOT)';assert code.count(needle)==1
code=code.replace(needle,'captured=latest_scene.scene(ROOT)')
exec(compile(code,str(script),'exec'),{'__file__':str(script),'ROOT':ROOT,'QUEUE':QUEUE,'ARGS':{'target_map':'/Game/Puzzles/Test/SixRound/L_SixRound_Test'},'latest_scene':latest_scene})
report=json.loads((QUEUE/'world-geometry.json').read_text())
RESULT={'report':'Saved/PR130Integration/world-geometry.json','passed':report['passed'],'samples':report['samples']}
assert report['passed'], 'Geometry gate failed; inspect its detailed report'
