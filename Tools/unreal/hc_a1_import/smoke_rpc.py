"""Restricted localhost MCP controls for this isolated HC-A1 smoke editor."""
import argparse
import json
from pathlib import Path
import urllib.request
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ready=json.loads((HERE/'smoke_ready.json').read_text())
assert Path(ready['project']).resolve()==ROOT
HEADERS={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def rpc(method,params):
 request=urllib.request.Request('http://127.0.0.1:8002/mcp',json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),HEADERS)
 with urllib.request.urlopen(request,timeout=45) as response:
  if response.headers.get('Mcp-Session-Id'):
   HEADERS['Mcp-Session-Id']=response.headers['Mcp-Session-Id']
  text=response.read().decode()
  value=json.loads(text) if text.startswith('{') else json.loads(next(l[5:].strip() for l in text.splitlines() if l.startswith('data:')))
  assert 'error' not in value,value
  return value

def call(toolset,name,args):
 value=rpc('tools/call',{'name':'call_tool','arguments':{'toolset_name':toolset,'tool_name':name,'arguments':args}})
 assert not value['result'].get('isError'),value
 text='\n'.join(c.get('text','') for c in value['result'].get('content',[]))
 try:return json.loads(text)
 except ValueError:return text

rpc('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'hc-a1-validation','version':'1'}})
live=call('EditorToolset.LogsToolset','GetLogEntries',{'pattern':'HC-A1_ISOLATED_PROJECT:','maxEntries':1})
assert ROOT.as_posix() in json.dumps(live),'MCP server is not this isolated project'
parser=argparse.ArgumentParser()
parser.add_argument('action',choices=('snapshot','configure','start','stop','finish'))
parser.add_argument('--clients',type=int,choices=(2,3,4))
args=parser.parse_args()
OBJECT='editor_toolset.toolsets.object.ObjectTools'
APP='EditorToolset.EditorAppToolset'
INSTANCE={'refPath':'/Script/UnrealEd.Default__LevelEditorPlaySettings'}
if args.action=='snapshot':
 result=call(OBJECT,'get_properties',{'instance':INSTANCE,'properties':['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess']})
 (HERE/'smoke_original_play_settings.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
elif args.action=='configure':
 assert args.clients
 values={'PlayNetMode':'PIE_Client','PlayNumberOfClients':args.clients,'RunUnderOneProcess':True}
 print(call(OBJECT,'set_properties',{'instance':INSTANCE,'values':json.dumps(values)}))
 (HERE/'smoke_control.json').write_text(json.dumps({'action':'configure','clients':args.clients})+'\n')
elif args.action in ('start','stop'):
 print(call(APP,'StartPIE' if args.action=='start' else 'StopPIE',{'options':{}} if args.action=='start' else {}))
else:
 original=json.loads((HERE/'smoke_original_play_settings.json').read_text())
 if isinstance(original,dict) and 'returnValue' in original:
  original=json.loads(original['returnValue'])
 print(call(OBJECT,'set_properties',{'instance':INSTANCE,'values':json.dumps(original)}))
 (HERE/'smoke_control.json').write_text(json.dumps({'action':'finish'})+'\n')
