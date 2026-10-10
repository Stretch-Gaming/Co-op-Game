"""Capture only the dedicated editor application, avoiding base64 console output."""
import base64,json
from pathlib import Path
from mcp_client import start,call
start()
result=call('call_tool',{'toolset_name':'EditorToolset.EditorAppToolset','tool_name':'CaptureEditorImage','arguments':{}})
path=Path(__file__).with_name('split-screen.png')
for item in result.get('content',[]):
    if item['type']=='image':
        path.write_bytes(base64.b64decode(item['data']));print(str(path));break
else:
    value=json.loads(result['content'][0]['text'])
    def find_image(data):
        if isinstance(data,dict):
            for k,v in data.items():
                if isinstance(v,str) and len(v)>1000:return v
                found=find_image(v)
                if found:return found
        return None
    data=find_image(value)
    assert data, list(value)
    path.write_bytes(base64.b64decode(data));print(str(path))
