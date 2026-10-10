"""Summarize earlier attempts and keep result evidence compact and reviewable."""
import json
from pathlib import Path
HERE=Path(__file__).parent.resolve()
names=['clients-2-initial.json','clients-2-prehardening.json','clients-2-roster-harness-attempt.json','clients-3-timing-attempt.json','clients-4-entry-timing-attempt.json','clients-4-return-timing-attempt.json','split-4-playerstate-attempt.json']
attempts=[]
for name in names:
    path=HERE/name
    if path.exists():
        data=json.loads(path.read_text())
        attempts.append({'file':name,'passed':data.get('passed'),'checks':len(data.get('checks',[])),
         'error':data.get('error'),'fixture_only':data.get('fixture_only',True)})
        path.unlink()
(HERE/'attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
log=HERE/'session-authoring-and-tests.log'
if log.exists():
    lines=log.read_text(errors='replace').splitlines()
    selected=[l for l in lines if 'HC6 runtime ' in l or 'HC6 verified project' in l]
    (HERE/'rendered-session-summary.log').write_text('\n'.join(selected)+'\n')
    log.unlink()
for name in ('audit.json','scaffold.json','contracts.json'):
    path=HERE/name
    if path.exists():path.write_text(json.dumps(json.loads(path.read_text()),separators=(',',':'))+'\n')
