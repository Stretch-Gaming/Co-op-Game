import json, urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
HEADERS={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def rpc(method,params):
 req=urllib.request.Request('http://127.0.0.1:8041/mcp',json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),HEADERS)
 with urllib.request.urlopen(req,timeout=45) as res:
  if res.headers.get('Mcp-Session-Id'):HEADERS['Mcp-Session-Id']=res.headers['Mcp-Session-Id']
  txt=res.read().decode();v=json.loads(txt) if txt.startswith('{') else json.loads(next(l[5:].strip() for l in txt.splitlines() if l.startswith('data:')));assert 'error' not in v,v;return v

def call(toolset,name,args):
 v=rpc('tools/call',{'name':'call_tool','arguments':{'toolset_name':toolset,'tool_name':name,'arguments':args}});assert not v['result'].get('isError'),v
 txt='\n'.join(c.get('text','') for c in v['result'].get('content',[]))
 try:return json.loads(txt)
 except ValueError:return txt
rpc('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'hc5-rounds','version':'1'}})
assert ROOT.as_posix() in json.dumps(call('EditorToolset.LogsToolset','GetLogEntries',{'category':'LogPython','pattern':'HC5_ISOLATED_PROJECT:','maxEntries':1}))
if __name__=='__main__':print(json.dumps(rpc('tools/list',{}))[:1000])
