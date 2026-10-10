"""Call only the dedicated HC-4 MCP endpoint. Arguments are JSON files."""
import json
import pathlib
import sys
import urllib.request
import urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[3]
assert ROOT==pathlib.Path('C:/Users/Stretch/.codex/worktrees/altar-challenge/Co op Game')
identity=json.loads((ROOT/'Saved/HC6Altar/identity.json').read_text())
assert pathlib.Path(identity['project'])==ROOT/'CoopGame.uproject'
assert identity['port']==8042
payload=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
session=ROOT/'Saved/HC6Altar/mcp_session.txt'
if not session.exists() and payload['method']!='initialize':
    init={'jsonrpc':'2.0','id':0,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'HC6Altar','version':'1'}}}
    initial=urllib.request.Request('http://127.0.0.1:8042/mcp',data=json.dumps(init).encode(),headers=headers)
    with urllib.request.urlopen(initial,timeout=50) as response:
        response.read()
        assert response.headers.get('Mcp-Session-Id')
        session.write_text(response.headers['Mcp-Session-Id'])
if session.exists(): headers['Mcp-Session-Id']=session.read_text()
req=urllib.request.Request('http://127.0.0.1:8042/mcp',data=json.dumps({'jsonrpc':'2.0','id':1,**payload}).encode(),headers=headers)
try:
    with urllib.request.urlopen(req,timeout=50) as response:
        if response.headers.get('Mcp-Session-Id'): session.write_text(response.headers['Mcp-Session-Id'])
        raw=response.read().decode()
except urllib.error.HTTPError as e:
    print(e.read().decode())
    raise
if raw.startswith('event:') or raw.startswith('data:'):
    data=[json.loads(line[5:]) for line in raw.splitlines() if line.startswith('data:')][-1]
else: data=json.loads(raw)
(ROOT/'Saved/HC6Altar/mcp_response.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(data)[:int(sys.argv[2]) if len(sys.argv)>2 else 6000])

