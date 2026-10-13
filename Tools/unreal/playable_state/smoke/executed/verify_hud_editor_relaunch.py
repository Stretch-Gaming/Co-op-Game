import json, hashlib, os
from pathlib import Path
import unreal as ue

ROOT = Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
OUT = Path('/tmp/coop-runtime/editor-relaunch-hud-final.json')
TEMP = '/Temp/CoopAudit/BP_InternalGeometry_81093_1f13b18378'
report = {'packages_saved': [], 'original_editor_pid': 81093}
try:
    assert Path(ue.Paths.project_dir()).resolve() == ROOT
    report.update({
        'editor_pid': os.getpid(),
        'project_dir': str(Path(ue.Paths.project_dir()).resolve()),
        'pie_stopped': not ue.EditorLevelLibrary.get_pie_worlds(True),
        'editor_map': ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world().get_path_name(),
        'dirty_content': [p.get_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()],
        'dirty_maps': [p.get_name() for p in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()],
        'temporary_diagnostic_loaded': any(o.get_path_name().startswith(TEMP) for o in ue.ObjectIterator(ue.Blueprint)),
    })
    binding = json.loads((ROOT/'Tools/unreal/playable_state/smoke/source-manifest.json').read_text())['final_asset_binding']
    report['final_binding_manifest'] = binding
    report['template_sha256'] = hashlib.sha256((ROOT/'Content/VehicleTemplate/UI/UI_Vehicle.uasset').read_bytes()).hexdigest()
    repair = json.loads(Path('/tmp/coop-runtime/hud-panel-tint-repair.json').read_text())
    report['final_widget_sha256'] = {p: hashlib.sha256((ROOT/'Content'/(p[6:] + '.uasset')).read_bytes()).hexdigest() for p in repair['packages_saved']}
    assert report['editor_pid'] != 81093 and report['pie_stopped']
    assert not report['dirty_content'] and not report['dirty_maps'] and not report['temporary_diagnostic_loaded']
    assert report['final_widget_sha256'] == repair['final_widget_sha256']
    assert report['editor_map'] == '/Game/Puzzles/Test/SixRound/L_SixRound_Test.L_SixRound_Test'
    report['passed'] = True
except Exception as exc:
    report.update(passed=False, error=repr(exc))
finally:
    OUT.write_text(json.dumps(report, indent=2))
