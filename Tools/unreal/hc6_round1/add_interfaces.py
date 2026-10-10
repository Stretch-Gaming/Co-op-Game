"""Use Slate's Class Settings picker to implement the existing reset contract."""
import json,re,time,subprocess,sys
from pathlib import Path
from mcp_client import start,call
start()
here=Path(__file__).resolve().parent
began=time.time()
subprocess.run([sys.executable,str(here/'run_editor.py'),str(here/'verify_editor.py')],cwd=here.parents[2],check=True)
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    identity=here/'editor-identity.json'
    if identity.exists() and identity.stat().st_mtime>=began:break
    time.sleep(.2)
else:raise TimeoutError('Project identity was not verified')
verified=json.loads(identity.read_text())
assert Path(verified['project']).parent.resolve()==here.parents[2]
def slate(name,**args):
    r=call('call_tool',{'toolset_name':'SlateInspectorToolset.SlateInspectorToolset','tool_name':name,'arguments':args})
    return json.loads(r['content'][0]['text']).get('returnValue')
def snapshot(ref):return slate('Snapshot',ref=ref,maxDepth=40)
def ref_for(text,pattern):
    line=next(l for l in text.splitlines() if re.search(pattern,l))
    return re.search(r'\[ref=([^]]+)\]',line)[1]
def seen(ref):
    slate('Observe',ref=ref,maxDepth=40)
    time.sleep(.5)
    return snapshot(ref)
for name in ('BP_PressurePlate','BP_PuzzleSetup','BP_ChamberGate','BP_StartPad'):
    if verified['interfaces'].get(name):continue
    call('call_tool',{'toolset_name':'EditorToolset.EditorAppToolset','tool_name':'OpenEditorForAsset','arguments':{'AssetPath':'/Game/Puzzles/'+name}})
    time.sleep(.8)
    w=ref_for(snapshot(''),r'^window "'+name+'"')
    tree=seen(w)
    slate('Click',ref=ref_for(tree,r'checkbox "Class Settings"'))
    time.sleep(.5)
    tree=seen(w)
    row=ref_for(tree,r'generic "Implemented Interfaces')
    tree=seen(row)
    slate('Click',ref=ref_for(tree,r'^  +button .*\[ref=')) if False else None
    combo=ref_for(tree,r'combobox .*\[ref=')
    slate('Click',ref=combo)
    time.sleep(.3)
    menu=ref_for(snapshot(''),r'^window \[pos=')
    tree=seen(menu)
    slate('Type',ref=ref_for(tree,r'textbox "Search"'),text='BPI_RoundReset')
    time.sleep(.5)
    tree=seen(menu)
    listing=ref_for(tree,r'listview "List"')
    tree=seen(listing)
    slate('Click',ref=ref_for(tree,r'generic "BPI_RoundReset"'))
    print(name+' reset interface added',flush=True)
