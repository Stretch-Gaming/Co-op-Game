"""All actual owners walk distinct paths concurrently; one initial approach each."""
import importlib.util,json
from pathlib import Path
world_dir=Path(__file__).resolve().parent
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,world_dir/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
native=module('six_world_paths_native','native_support.py');driver=module('six_world_path_driver','path_driver.py')
stage=ARGS['stage'];assert stage in ('first','second')
case=ARGS.get('case_id','normal');assert all(c.isalnum() or c in '-_' for c in case)
h=native.Harness(ARGS,'world-parallel-'+stage+'-'+case)
assert 'SixRound' in h.server.get_path_name()
assert h.round()['phase']==1 and h.round()['index']==(2 if stage=='first' else 4),'Use a genuinely started path round after taking/doors are ready'
layout=json.loads((world_dir/'positions.json').read_text())
slots=dict(h.slots)
if 'path_slots' in ARGS:
 slots={int(k):int(v) for k,v in ARGS['path_slots'].items()};assert set(slots)==set(h.ids)
 assert len(set(slots.values()))==h.n and all(0<=slot<4 for slot in slots.values())
 h.fixtures.append({'kind':'explicit physical path coverage override; does not prove normal ColorSlot assignment','path_slots':slots})
start_round=h.round();drivers=[driver.Driver(h,layout,pid,stage,slots[pid]) for pid in h.ids]
h.transition('parallel_owning_paths')
def tick(delta):
 assert h.round()['attempt']==start_round['attempt'],'Round restarted during physical path gate'
 for d in drivers:d.tick()
 if all(d.done for d in drivers):
  assert len({d.slot for d in drivers})==h.n
  h.check('every actual owner completed a different path with native jump/climb/mantle',{'stage':stage,'path_slots':slots,'normal_assignment':slots==h.slots})
  h.finish(True)
RESULT=h.register(tick)
