"""Read saved RPC details through Slate; UE hides these fields from Python."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from rpc import call,ROOT,QUEUE
result=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('request.py')),'open_asset.py',json.dumps({'asset':'/Game/Core/BP_CoopCharacter'})],cwd=ROOT,capture_output=True,text=True)
assert result.returncode==0,result.stdout+result.stderr
def slate(name,**args):return call('SlateInspectorToolset.SlateInspectorToolset',name,args)['returnValue']
def ref(line):return re.search(r'\[ref=([^]]+)\]',line)[1]
def snap(window=''):
    time.sleep(.25)
    return slate('Snapshot',ref=window,maxDepth=60).splitlines()
window=ref(next(line for line in snap() if line.startswith('window "BP_CoopCharacter"')))
evidence={}
for name in ('Server_ThrowFlare','Server_Climb','Server_StopClimb','Server_SetClimbForward','Server_RequestBoost'):
    search=ref(next(line for line in snap(window) if 'textbox "Enter function or event name to find references...' in line))
    assert slate('Type',ref=search,text='',submit=False)
    assert slate('PressKey',key='Ctrl+A') and slate('PressKey',key='BackSpace')
    assert slate('Type',ref=search,text=name,submit=True)
    label=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',name.replace('_',' '))
    deadline=time.monotonic()+10
    hit=None
    while time.monotonic()<deadline:
        hit=next((line for line in snap(window) if 'listitem "'+label+'"' in line),None)
        if hit:break
    assert hit,name
    assert slate('Click',ref=ref(hit),doubleClick=True)
    deadline=time.monotonic()+6
    verified=False
    while time.monotonic()<deadline:
        lines=snap(window)
        start=next((i for i,line in enumerate(lines) if 'generic "Replicates' in line),None)
        if start is None:continue
        section=lines[start:start+23]
        reliable=next((line for line in section if 'checkbox "Reliable"' in line),None)
        verified=bool(reliable and '[checked]' in reliable and any('text "Run on Server"' in line for line in section))
        if verified:break
    assert verified,(name,section)
    evidence[name]={'server':True,'reliable':True,'details':section}
asset=ROOT/'Content/Core/BP_CoopCharacter.uasset'
(QUEUE/'rpc-ui-verification.json').write_text(json.dumps({'character_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'events':evidence,'read_only':True},indent=2))
print(str(len(evidence))+' saved server RPCs verified; no settings changed.')
