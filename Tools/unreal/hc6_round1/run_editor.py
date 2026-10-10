"""Run an explicitly selected authoring/inspection script in isolated editor."""
import json
import sys
import re,time
from pathlib import Path
from mcp_client import start,call
start()
def slate(name,**args):
    r=call('call_tool',{'toolset_name':'SlateInspectorToolset.SlateInspectorToolset','tool_name':name,'arguments':args})
    return json.loads(r['content'][0]['text']).get('returnValue')
slate('Observe',ref='w1',maxDepth=40)
tree=slate('Snapshot',ref='w1',maxDepth=40)
button=next(l for l in tree.splitlines() if 'button "Output Log"' in l)
slate('Click',ref=re.search(r'\[ref=([^]]+)\]',button)[1])
time.sleep(.4)
tree=slate('Snapshot',ref='w1',maxDepth=40)
if 'text "Cmd"' not in tree:
    slate('Click',ref=re.search(r'\[ref=([^]]+)\]',button)[1]);time.sleep(.4)
    tree=slate('Snapshot',ref='w1',maxDepth=40)
cmd=tree.split('text "Cmd"',1)[1]
textbox=next(l for l in cmd.splitlines() if 'textbox' in l)
ref=re.search(r'\[ref=([^]]+)\]',textbox)[1]
command='py '+str(Path(sys.argv[1]).resolve()).replace('\\','/')
assert slate('Type',ref=ref,text=command,submit=True)
print('Submitted '+Path(sys.argv[1]).name)
