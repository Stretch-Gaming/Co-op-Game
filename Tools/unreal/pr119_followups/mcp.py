"""Call one Unreal MCP tool on this worktree's own editor (port 8001), never the primary editor on 8000.

Usage: python3 mcp.py <Toolset> <tool> '<json args>' [out.png]
A base64 PNG result is written to out.png when given.
"""
import base64
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ready = json.loads((ROOT / 'Saved/PR119/ready.json').read_text())
assert Path(ready['project']).resolve() == ROOT.resolve() and ready['port'] == 8001
URL = 'http://127.0.0.1:8001/mcp'
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}

def rpc(method, params):
    req = urllib.request.Request(URL, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(), HEADERS)
    with urllib.request.urlopen(req, timeout=300) as response:
        if response.headers.get('Mcp-Session-Id'):
            HEADERS['Mcp-Session-Id'] = response.headers['Mcp-Session-Id']
        text = response.read().decode()
    result = json.loads(text) if text.startswith('{') else json.loads([l[5:].strip() for l in text.splitlines() if l.startswith('data:')][-1])
    assert 'error' not in result, result
    return result

rpc('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {}, 'clientInfo': {'name': 'pr119-followups', 'version': '1'}})
result = rpc('tools/call', {'name': 'call_tool', 'arguments': {'toolset_name': sys.argv[1], 'tool_name': sys.argv[2], 'arguments': json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}}})['result']
for item in result.get('content', []):
    if item.get('type') == 'image' and len(sys.argv) > 4:
        Path(sys.argv[4]).write_bytes(base64.b64decode(item['data']))
        print('wrote', sys.argv[4])
    elif item.get('type') == 'text':
        text = item['text']
        if len(sys.argv) > 4 and len(text) > 5000:
            try:
                data = json.loads(text)
                stack, blob = [data], None
                while stack and blob is None:
                    node = stack.pop()
                    for v in (node.values() if isinstance(node, dict) else node if isinstance(node, list) else []):
                        if isinstance(v, str) and len(v) > 5000:
                            blob = v
                        elif isinstance(v, (dict, list)):
                            stack.append(v)
                Path(sys.argv[4]).write_bytes(base64.b64decode(blob))
                print('wrote', sys.argv[4])
                continue
            except Exception:
                pass
        print(text[:6000])
