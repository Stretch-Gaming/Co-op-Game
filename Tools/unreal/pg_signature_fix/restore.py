import json
from pathlib import Path
import unreal
ROOT = Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == ROOT / 'CoopGame.uproject'
settings = json.loads((ROOT / 'Saved/PGSignatureFix/original-settings.json').read_text())
assert unreal.ToolsetLibrary.set_object_properties(unreal.load_object(None, '/Script/UnrealEd.Default__LevelEditorPlaySettings'), settings['play'])
assert unreal.ToolsetLibrary.set_object_properties(unreal.load_object(None, '/Script/UnrealEd.Default__EditorPerformanceSettings'), settings['perf'])
RESULT = {'restored': True}
