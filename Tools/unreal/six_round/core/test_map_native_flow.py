"""Run the bounded owning-input two-run puzzle/round/travel suite.
ARGS runs=1 permits dedicated PlayAsClient; runs=2 requires a local listen host.
"""
import sys,hashlib,importlib.util
from pathlib import Path
folder=Path(__file__).resolve().parent/'tests'
registry=sys.modules.get('six_round_core_test_registry')
assert not registry or not getattr(registry,'handle',None),'Finish/stop the active core suite before loading test repairs'
# The editor executes this entry file anew but retains Python imports. Reload the
# complete dependent chain only between suites, including fresh layout data.
files=[folder/name for name in ('runtime.py','framework.py','native_flow.py')]
layout=folder.parent.parent/'world/positions.json'
digest=hashlib.sha256(b''.join(path.read_bytes() for path in [*files,layout])).hexdigest()
for name in ('recovery','disconnect','native_gate'):
 cached=sys.modules.get(name)
 if cached and Path(getattr(cached,'__file__','')).parent==folder:
  del sys.modules[name]
for path in files:
 name=path.stem
 spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec)
 sys.modules[name]=module
 # Compile source directly: same-second repairs must not reuse stale .pyc.
 exec(compile(path.read_text(encoding='utf-8-sig'),str(path),'exec'),module.__dict__)
NativeFlow=sys.modules['native_flow'].NativeFlow
suite=NativeFlow(globals().get('ARGS',{}));suite.test_source_layout_sha256=digest;RESULT=suite.run()
RESULT['test_source_layout_sha256']=digest
