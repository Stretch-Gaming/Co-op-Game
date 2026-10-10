"""CLI for this repair's dedicated local editor; no default MCP endpoint."""
import json
from pathlib import Path
import sys
import urllib.request
ROOT = Path(__file__).resolve().parents[3]
assert ROOT == Path('C:/Users/Stretch/Development/Co op Game/Saved/MergeBuild/Source')
queue = ROOT / 'Saved/PGSignatureFix'
assert json.loads((queue / 'identity.json').read_text())['project'] == str(ROOT / 'CoopGame.uproject')
headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
def request(payload):
    req = urllib.request.Request('http://127.0.0.1:8028/mcp', data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=50) as response:
        if response.headers.get('Mcp-Session-Id'):
            headers['Mcp-Session-Id'] = response.headers['Mcp-Session-Id']
        raw = response.read().decode()
    if not raw:
        return {}
    return [json.loads(line[5:]) for line in raw.splitlines() if line.startswith('data:')][-1] if raw.startswith(('event:', 'data:')) else json.loads(raw)
request({'jsonrpc': '2.0', 'id': 0, 'method': 'initialize', 'params': {
    'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'PGSignatureFix', 'version': '1'}}})
request({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
name = sys.argv[1]
args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
result = request({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'call_tool', 'arguments': {
    'toolset_name': 'EditorToolset.EditorAppToolset', 'tool_name': name, 'arguments': args}}})
print(json.dumps(result))
assert not result.get('error'), result
assert not result.get('result', {}).get('isError'), result
