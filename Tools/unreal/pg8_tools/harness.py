"""Reuse shipped owning-input harness with isolated path and truthful Mac metadata."""
import importlib.util
import sys
from pathlib import Path
import unreal as ue

ROOT = Path(ue.Paths.project_dir()).resolve()
EXPECTED = Path(__file__).resolve().parents[3]
assert ROOT == EXPECTED
source = ROOT / 'Tools/unreal/six_round/player/tests/common.py'
name = '_pg8_private_harness'
if name not in sys.modules:
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    module.EXPECTED = EXPECTED
else:
    module = sys.modules[name]

class Harness(module.Harness):
    def __init__(self, args, name):
        super().__init__(args, name)
        self.queue = ROOT / 'Saved/PG8Tools'
        self.report = self.queue / (name + '-' + self.profile + '-' + str(self.n) + '.json')

    def finish(self, passed, error=None):
        result = super().finish(passed, error)
        if result:
            result['platform'] = 'Mac, NullRHI, Unreal ' + ue.SystemLibrary.get_engine_version()
            result['mac_runtime_tested'] = True
            result['mac_or_packet_emulation_tested'] = None
            result['packet_emulation_tested'] = False
            self.report.write_text(__import__('json').dumps(result, indent=2))
        return result
