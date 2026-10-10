import json,pathlib,hashlib,re
HERE=pathlib.Path(__file__).parent;ROOT=HERE.parents[2]
checks=[]
for n in [2,3,4]:
 p=HERE/f'clients-{n}.json'
 if not p.exists():continue
 d=json.loads(p.read_text());assert d['passed'],p
 for label,count in [('placed1',1),('placed2',2)]:
  rows=d['snapshots'][label];assert len(rows)==n+1
  for r in rows:
   assert r['completed'] and '=2,Phase_' in r['round'] and '=NewEnumerator2,' in r['round'],(label,r)
   keys=[x for x in r['items'] if x['tag'].startswith('Key')]
   assert sum(k['state']==2 for k in keys)==1
   if count==2:assert sum(k['state']==1 for k in keys)==1
  server=next(r for r in rows if r['server']);assert server['clear_calls']==count and server['accept_count']==count
  if count==2:
   assert sorted(p['speed'] for p in server['players'])==[300.0]+[600.0]*(n-1)
 checks.append({'clients':n,'independent_snapshot_assertions':'passed','per_attempt_exactly_once':True,'replicated_phase_cleared':True,'competition_one_placed_one_still_carried':True})
for name in ['fresh-client-latejoin.json','stale-key-rejection.json']:
 p=HERE/name
 if p.exists():assert json.loads(p.read_text())['passed'],name
owned=[ROOT/'Content/Puzzles/BP_Altar.uasset',*sorted((ROOT/'Content/Puzzles/Test/HC6_Altar').glob('*'))]
report={'checks':checks,'artifact_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in owned if p.is_file()}}
(HERE/'independent-evidence.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
