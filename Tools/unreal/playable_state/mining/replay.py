"""Root editor entry point; adapts paths of exact preserved scripts only.

ARGS.stage chooses a bounded stage. Authoring stages require explicit execute
and own lease_owner. Root owns PIE startup/shutdown for the runtime stages.
Outputs live under ignored Saved/PlayableState/Mining.
"""
import json
from pathlib import Path
import unreal as ue

ROOT=Path(ue.Paths.project_dir()).resolve()
assert (ROOT/'CoopGame.uproject').is_file()
HERE=ROOT/'Tools/unreal/playable_state/mining'
OUT=ROOT/'Saved/PlayableState/Mining';OUT.mkdir(parents=True,exist_ok=True)
args=dict(globals().get('ARGS',{}))
stage=args.pop('stage',None)
scripts={'inventory':'inventory.py','retry_inventory':'inventory_retry.py','rpc_inventory':'inventory_rpc.py',
         'place':'integrate_placement.py','prepare_core':'build_core_packet.py',
         'patch_core':'patch_core.py','trigger_pickaxe':'acceptance_trigger_pickaxe_v2.py',
         'transaction':'acceptance_transaction_v6.py'}
assert stage in scripts
source=HERE/'executed'/scripts[stage]
code=source.read_text(encoding='utf-8-sig')
old_root="'/Volumes/CoopBuild/Repositories/Co-op-Game-primary'"
old_out="'/tmp/coop-mining'"
assert old_root in code and old_out in code
code=code.replace(old_root,repr(str(ROOT))).replace(old_out,repr(str(OUT)))
scope={'__name__':'__main__','__file__':str(source),'ARGS':args}
exec(compile(code,str(source),'exec'),scope)
RESULT=scope.get('RESULT',{'stage':stage,'output_directory':str(OUT)})
