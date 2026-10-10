import pathlib,json,subprocess,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
rows=json.loads(subprocess.check_output(['git','lfs','ls-files','--json'],cwd=ROOT,text=True))
if isinstance(rows,dict):rows=rows['files']
checks=[]
for item in rows:
 p=ROOT/item['name'];actual=hashlib.sha256(p.read_bytes()).hexdigest();oid=item['oid'].removeprefix('sha256:')
 assert actual==oid,(p,actual,oid)
 checks.append({'path':item['name'],'sha256':actual})
(HERE/'hydrated-baseline.json').write_text(json.dumps({'checked':len(checks),'baseline_head':'4be3f85cff446901bbf88bdf918cfb2050d6fa18','all_lfs_match':True,'files':checks},indent=2));print(json.dumps({'all_lfs_match':len(checks)}))
