"""Only controls the exact primary-verified isolated editor on loopback8045."""
import json,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ready=json.loads((HERE/'ready.json').read_text())
assert Path(ready['project']).resolve()==ROOT and ready['mcp_port']==8045
HEADERS={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def rpc(method,params):
 request=urllib.request.Request('http://127.0.0.1:8045/mcp',json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),HEADERS)
 with urllib.request.urlopen(request,timeout=45) as response:
  if response.headers.get('Mcp-Session-Id'):HEADERS['Mcp-Session-Id']=response.headers['Mcp-Session-Id']
  result=response.read().decode()
  value=json.loads(result) if result.startswith('{') else json.loads(next(l[5:].strip() for l in result.splitlines() if l.startswith('data:')))
  assert 'error' not in value,value
  return value
def call(toolset,name,args):
 value=rpc('tools/call',{'name':'call_tool','arguments':{'toolset_name':toolset,'tool_name':name,'arguments':args}})
 assert not value['result'].get('isError'),value
 result='\n'.join(c.get('text','') for c in value['result'].get('content',[]))
 try:return json.loads(result)
 except ValueError:return result
rpc('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'hc-gauntlet-owned','version':'1'}})
live=call('EditorToolset.LogsToolset','GetLogEntries',{'category':'LogPython','pattern':'HC_GAUNTLET_ISOLATED_PROJECT:','maxEntries':1})
assert ROOT.as_posix() in json.dumps(live) and ready['session'] in json.dumps(live),'Wrong editor identity'
if __name__=='__main__':
 import sys
 print(json.dumps(call(sys.argv[1],sys.argv[2],json.loads(sys.argv[3])),indent=2))
