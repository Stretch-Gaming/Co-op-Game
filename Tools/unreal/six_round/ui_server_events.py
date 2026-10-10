import json
import re
import time
from rpc import call,QUEUE

def slate(name,**kwargs):
    value=call('SlateInspectorToolset.SlateInspectorToolset',name,kwargs)
    return value.get('returnValue')
def ref(line):return re.search(r'\[ref=([^]]+)\]',line)[1]
def snapshot(window):
    time.sleep(.2)
    return slate('Snapshot',ref=window,maxDepth=60)

root=snapshot('')
window=ref(next(l for l in root.splitlines() if l.startswith('window "BP_CoopCharacter"')))
slate('Observe',ref=window,maxDepth=60)
events=['Server_ThrowFlare','Server_Climb','Server_StopClimb','Server_SetClimbForward']
evidence={}
for name in events:
    lines=snapshot(window).splitlines()
    search=ref(next(l for l in lines if 'textbox "Enter function or event name to find references..."' in l))
    assert slate('Type',ref=search,text='',submit=False)
    assert slate('PressKey',key='Ctrl+A')
    assert slate('PressKey',key='BackSpace')
    assert slate('Type',ref=search,text=name,submit=True)
    label=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',name.replace('_',' '))
    deadline=time.monotonic()+10
    hit=None
    while time.monotonic()<deadline:
        lines=snapshot(window).splitlines()
        hit=next((l for l in lines if 'listitem "'+label+'"' in l),None)
        if hit:break
        time.sleep(.25)
    assert hit,name+' search result not ready'
    assert slate('Click',ref=ref(hit),doubleClick=True)
    deadline=time.monotonic()+5
    i=None
    while time.monotonic()<deadline:
        lines=snapshot(window).splitlines()
        i=next((i for i,l in enumerate(lines) if 'generic "Replicates' in l),None)
        if i is not None:break
    assert i is not None,name+' details not ready'
    panel=lines[i:i+23]
    combo=ref(next(l for l in panel if 'combobox ' in l))
    if not any('text "Run on Server"' in l for l in panel):
        assert slate('SelectOption',ref=combo,value='Run on Server')
    deadline=time.monotonic()+5
    reliable=None
    while time.monotonic()<deadline:
        lines=snapshot(window).splitlines()
        reliable=next((l for l in lines if 'checkbox "Reliable"' in l),None)
        if reliable and '[disabled' not in reliable and any('text "Run on Server"' in l for l in lines):break
    assert reliable and '[disabled' not in reliable,name
    if '[unchecked]' in reliable:
        assert slate('Click',ref=ref(reliable))
    deadline=time.monotonic()+5
    checked=None
    while time.monotonic()<deadline:
        final=snapshot(window)
        checked=next((l for l in final.splitlines() if 'checkbox "Reliable"' in l),None)
        if 'text "Run on Server"' in final and checked and '[checked]' in checked:
            break
    assert 'text "Run on Server"' in final and checked and '[checked]' in checked,name
    evidence[name]={'server':True,'reliable':True,'observed':checked}
    print(name+' configured',flush=True)
(QUEUE/'server-events-ui.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
