import json
from pathlib import Path
import unreal
ROOT = Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == ROOT / 'CoopGame.uproject'
QUEUE = ROOT / 'Saved/PGSignatureFix'
opts = json.loads((QUEUE / 'options.json').read_text(encoding='utf-8-sig'))
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(opts.get('map', '/Game/Player/Test/L_PG_Test'))
settings = unreal.load_object(None, '/Script/UnrealEd.Default__LevelEditorPlaySettings')
perf = unreal.load_object(None, '/Script/UnrealEd.Default__EditorPerformanceSettings')
if not (QUEUE / 'original-settings.json').exists():
    (QUEUE / 'original-settings.json').write_text(json.dumps({
        'play': unreal.ToolsetLibrary.get_object_properties(settings, ['PlayNetMode', 'PlayNumberOfClients', 'RunUnderOneProcess', 'ServerPort', 'NewWindowWidth', 'NewWindowHeight']),
        'perf': unreal.ToolsetLibrary.get_object_properties(perf, ['bThrottleCPUWhenNotForeground'])}))
assert unreal.ToolsetLibrary.set_object_properties(settings, json.dumps({
    'PlayNetMode': 'PIE_ListenServer' if opts.get('split') else 'PIE_Client',
    'PlayNumberOfClients': opts['players'], 'RunUnderOneProcess': True, 'ServerPort': 17828,
    'NewWindowWidth': 800, 'NewWindowHeight': 450}))
assert unreal.ToolsetLibrary.set_object_properties(perf, json.dumps({'bThrottleCPUWhenNotForeground': False}))
RESULT = {'prepared': opts}
