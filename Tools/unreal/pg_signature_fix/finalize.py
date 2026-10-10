"""Independent acceptance report from saved assets, logs and observed PIE worlds."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
ROOT = Path(__file__).resolve().parents[3]
saved = ROOT / 'Saved/PGSignatureFix'
evidence = Path(__file__).parent / 'evidence'
evidence.mkdir(exist_ok=True)
compile_log = (saved / 'compile-final.log').read_text(errors='replace')
package_log = (saved / 'package.log').read_text(errors='replace')
runtime_log = (saved / 'runtime-editor.log').read_text(errors='replace')
assert 'Success - 0 error(s), 0 warning(s)' in compile_log
assert 'Success - 0 error(s), 0 warning(s)' in package_log and 'BUILD SUCCESSFUL' in package_log
assert not re.search(r'Accessed None|Blueprint Runtime Error|LogBlueprint: Error|LogScript:.*Error', runtime_log)
assert subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--name-only'], text=True).splitlines() == ['Content/Player/Test/BP_PG_TestCharacter.uasset']
checks = 0
for name in ['input-2.json', 'input-3.json', 'input-4.json', 'input-split.json', 'main-smoke.json']:
    payload = json.loads((saved / name).read_text())
    assert payload['passed'], name
    checks += payload.get('checks', 0)
    shutil.copyfile(saved / name, evidence / name)
shutil.copyfile(saved / 'repair.json', evidence / 'repair.json')
def record(path):
    return {'path': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
asset = ROOT / 'Content/Player/Test/BP_PG_TestCharacter.uasset'
build = ROOT.parents[1] / 'Builds/PG-Signature-Fix-Windows'
assert build.exists()
report = {'passed': True, 'base': '91a5195ec6d31060d4e28d02f2e068ac595cd0b1',
          'asset': record(asset), 'lock_id': '56109203',
          'compiled': re.findall(r"Loading and Compiling: '(/Game/[^']+)'", compile_log),
          'compile_errors': 0, 'compile_warnings': 0, 'cook_errors': 0, 'cook_warnings': 0,
          'runtime_input_assertions': checks, 'network_players': [2, 3, 4],
          'split': 'Two local host owners and two remote clients; four players total',
          'main_map_two_client_smoke': True,
          'runtime_blueprint_script_errors_or_accessed_none': 0,
          'package': str(build),
          'package_artifacts': [record(p) for p in sorted(build.rglob('*')) if p.suffix.lower() in {'.exe', '.pak', '.utoc', '.ucas'}],
          'logs': [record(saved / name) for name in ['compile-final.log', 'package.log', 'runtime-editor.log']],
          'limits': ['Headless Windows PIE; no visual, physical-gamepad or Mac acceptance.',
                    'Core carrying attachment belongs to the active HC-2 integration chat; health/downed integration is separate.',
                    'Earlier Python/MCP harness discovery diagnostics remain in the ignored runtime log; no gameplay Blueprint or Script errors occurred.']}
(evidence / 'verification.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'passed': True, 'compiled_blueprints': len(report['compiled']), 'runtime_input_assertions': checks, 'asset_sha256': report['asset']['sha256']}))
