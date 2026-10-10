"""Sequential transport for the dedicated HC6 editor (never port 8000)."""
import json
import sys
import urllib.request

URL = 'http://127.0.0.1:8016/mcp'
SESSION = None
def rpc(method, params=None, ident=1):
    global SESSION
    body = {'jsonrpc':'2.0','method':method}
    if ident is not None: body['id'] = ident
    if params is not None: body['params'] = params
    headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
    if SESSION: headers['Mcp-Session-Id']=SESSION
    request=urllib.request.Request(URL,json.dumps(body).encode(),headers)
    with urllib.request.urlopen(request,timeout=180) as response:
        SESSION=response.headers.get('Mcp-Session-Id',SESSION)
        raw=response.read().decode()
    if not raw: return {}
    if raw.startswith('event:') or raw.startswith('data:'):
        raw=next(line[5:].strip() for line in raw.splitlines() if line.startswith('data:'))
    result=json.loads(raw)
    if 'error' in result: raise RuntimeError(result['error'])
    return result.get('result',result)
def start():
    rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'hc6-round1','version':'1'}})
    rpc('notifications/initialized',ident=None)
def call(name,arguments):
    result=rpc('tools/call',{'name':name,'arguments':arguments})
    if result.get('isError'): raise RuntimeError(result)
    return result
if __name__=='__main__':
    start()
    if sys.argv[1]=='list':
        data=rpc('tools/list')
        print(json.dumps(data,indent=2))
    else:
        print(json.dumps(call(sys.argv[1],json.loads(sys.argv[2])),indent=2))
