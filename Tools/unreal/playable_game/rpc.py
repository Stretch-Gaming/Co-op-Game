"""Sequential MCP transport restricted to this worktree's own editor."""
import json
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
QUEUE=ROOT/'Saved/PlayableGame'
URL='http://127.0.0.1:8060/mcp'
HEADERS={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
ready=json.loads((QUEUE/'ready.json').read_text())
assert Path(ready['project']).resolve()==ROOT.resolve() and ready['port']==8060

def rpc(method,params):
    request=urllib.request.Request(URL,json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode(),HEADERS)
    with urllib.request.urlopen(request,timeout=55) as response:
        if response.headers.get('Mcp-Session-Id'):HEADERS['Mcp-Session-Id']=response.headers['Mcp-Session-Id']
        text=response.read().decode()
    result=json.loads(text) if text.startswith('{') else json.loads([line[5:].strip() for line in text.splitlines() if line.startswith('data:')][-1])
    assert 'error' not in result,result
    return result

def call(toolset,name,args):
    result=rpc('tools/call',{'name':'call_tool','arguments':{'toolset_name':toolset,'tool_name':name,'arguments':args}})['result']
    assert not result.get('isError'),result
    text='\n'.join(c.get('text','') for c in result.get('content',[]))
    try:return json.loads(text)
    except ValueError:return text

rpc('initialize',{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'playable-game-primary','version':'1'}})
identity=call('EditorToolset.LogsToolset','GetLogEntries',{'category':'LogPython','pattern':'PLAYABLE_GAME_ISOLATED_PROJECT:','maxEntries':1})
assert ROOT.as_posix() in json.dumps(identity),'Wrong editor connection'

if __name__=='__main__':
    import sys
    value=call(sys.argv[1],sys.argv[2],json.loads(sys.argv[3]))
    (QUEUE/'last-mcp-result.json').write_text(json.dumps(value,indent=2))
    print(json.dumps(value,indent=2)[:10000])
