import base64,hashlib,importlib.util,json,re,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('ue_client','/tmp/coop-ue.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.start();D=Path('/tmp/coop-runtime');tag=sys.argv[1]
assert re.fullmatch(r'[a-zA-Z0-9_-]+',tag)
snapshot=c.tool(c.SL,'Snapshot',{'ref':'','maxDepth':0});(D/(tag+'-windows.txt')).write_text(snapshot);rows=[]
for line in snapshot.splitlines():
 if 'window "CoopGame Preview [NetMode:' not in line:continue
 title=re.search(r'window "([^"]+)"',line).group(1);ref=re.search(r'\[ref=([^]]+)\]',line).group(1)
 r=c.rpc('tools/call',{'name':'call_tool','arguments':{'toolset_name':c.SL,'tool_name':'Screenshot','arguments':{'ref':ref}}});assert not r.get('isError'),r;encoded=None
 for item in r.get('content',[]):
  if item['type']=='image':encoded=item['data'];mime=item['mimeType'];break
  if item['type']=='text':
   try:v=json.loads(item['text']);v=v.get('returnValue',v)
   except (json.JSONDecodeError,TypeError):continue
   if isinstance(v,dict) and 'data'in v:encoded=v['data'];mime=v.get('mimeType');break
 assert encoded and mime=='image/png';p=D/(tag+'-'+str(len(rows))+'.png');assert not p.exists();p.write_bytes(base64.b64decode(encoded));rows.append({'title':title,'window_ref':ref,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'native_slate_window_capture':True})
assert rows
(D/(tag+'-captures.json')).write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
