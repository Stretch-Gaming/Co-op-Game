"""Private file/hash loader; never imports or replaces the Core common module."""
import hashlib,importlib.util,sys
from pathlib import Path
def load_harness():
 path=Path(__file__).with_name('common.py');digest=hashlib.sha256(path.read_bytes()).hexdigest()
 name='_six_round_pg_input_harness'
 previous=sys.modules.get(name)
 if previous:
  assert not getattr(previous,'_ACTIVE_HARNESSES',set()),'Finish the existing PG input gate before loading/reloading another'
  if previous._pg_source_sha256==digest:return previous.Harness
 spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec);sys.modules[name]=module
 spec.loader.exec_module(module);module._pg_source_sha256=digest
 return module.Harness
