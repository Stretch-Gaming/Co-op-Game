"""Editor-owner entry point; replay exact snapshots with explicit path adaptation.

ARGS.stage: inspect, import, or lit. Import additionally requires execute=True.
Lit requires an already running fresh Lobby with joining/2 or host_split/4.
No editor opening, map loading, PIE startup/shutdown or global package save occurs.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTEXT_NAME = 'hc_a4_crystal_lock_replay_context_v1'
context = sys.modules.get(CONTEXT_NAME)
if context is None:
    spec = importlib.util.spec_from_file_location(CONTEXT_NAME, HERE / 'context.py')
    context = importlib.util.module_from_spec(spec)
    sys.modules[CONTEXT_NAME] = context
    try:
        spec.loader.exec_module(context)
    except BaseException:
        sys.modules.pop(CONTEXT_NAME, None)
        raise
assert Path(context.__file__).resolve() == (HERE / 'context.py').resolve()
args = dict(globals().get('ARGS', {}))
stage = args.pop('stage', None)
assert stage in ('inspect', 'import', 'lit'), 'Choose exactly one bounded replay stage'
context.guard(stopped_pie=stage in ('inspect', 'import'))
if stage == 'import':
    assert args.pop('execute', False) is True, 'Import explicitly creates the documented owned assets'
context.QUEUE.mkdir(parents=True, exist_ok=True)
source = HERE / 'executed' / {'inspect': 'inspect_crystal_lock.py',
                              'import': 'import_crystal_lock_fresh.py',
                              'lit': 'test_crystal_lock_lit.py'}[stage]
manifest = json.loads((HERE / 'source-manifest.json').read_text())
for name in ('executed/' + source.name, 'executed/ghost_runtime_support.py'):
    record = manifest['files'][name]
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == record['sha256'], 'Snapshot differs from replay manifest: ' + name
code = source.read_text()
# Only path/namespace adapters change; native guards and authoring logic stay intact.
old_root = "'/Volumes/CoopBuild/Repositories/Co-op-Game-primary'"
assert old_root in code
code = code.replace(old_root, repr(str(context.ROOT)))
code = code.replace('/tmp/hc-a4-crystal-lock', str(context.QUEUE))
code = code.replace('/tmp/coop-audit/ghost_runtime_support.py', str(HERE / 'executed/ghost_runtime_support.py'))
code = code.replace("Path('/tmp').resolve()", 'Path(' + repr(str(context.QUEUE)) + ').resolve()')
code = code.replace('hc_a4_parent_authoring', 'hc_a4_crystal_lock_replay_authoring_v1')
code = code.replace('hc_a4_crystal_lock_native_runtime_support_v1', 'hc_a4_crystal_lock_durable_runtime_support_v1')
if stage == 'lit':
    # The exact harness copy is retained; the runtime loader reads an adapted
    # sibling generated under ignored Saved, keeping source snapshots unchanged.
    harness = HERE / 'executed/ghost_runtime_support.py'
    adapted = harness.read_text()
    assert old_root in adapted
    adapted = adapted.replace(old_root, repr(str(context.ROOT))).replace('/tmp/coop-audit/runtime-evidence', str(context.QUEUE / 'runtime-evidence'))
    adapted_path = context.QUEUE / 'runtime_support_adapted.py'
    adapted_path.write_text(adapted)
    code = code.replace(str(harness), str(adapted_path))
if 'inspection' in args:
    assert Path(args['inspection']).resolve().is_relative_to(context.QUEUE.resolve())
if 'report' in args:
    assert Path(args['report']).resolve().is_relative_to(context.QUEUE.resolve())
scope = {'__name__': 'hc_a4_crystal_lock_replay_' + stage,
         '__file__': str(source), 'ARGS': args}
exec(compile(code, str(source), 'exec'), scope)
RESULT = scope.get('RESULT', {'stage': stage, 'output_directory': str(context.QUEUE)})
