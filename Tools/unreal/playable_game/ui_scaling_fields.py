"""Configure the reserved user-defined struct through its native editor."""
import re
import time
from rpc import call, QUEUE

def slate(name,**kwargs):
    result=call('SlateInspectorToolset.SlateInspectorToolset',name,kwargs)
    return result.get('returnValue')

def snapshot(ref):
    time.sleep(.25)
    return slate('Snapshot',ref=ref,maxDepth=60)

def ref(line):
    return re.search(r'\[ref=([^]]+)\]',line)[1]

root=snapshot('')
window=ref(next(l for l in root.splitlines() if l.startswith('window "S_HazardScaling"')))
slate('Observe',ref=window,maxDepth=60)
for field in ['DartInterval','SwingSpeed','ReviveSeconds']:
    tree=snapshot(window)
    if f'textbox "{field}"' in tree:
        continue
    lines=tree.splitlines()
    member=next((i for i,l in enumerate(lines) if re.search(r'textbox "MemberVar_\d+"',l)),None)
    if member is None:
        button=ref(next(l for l in lines if 'button "Add Variable"' in l))
        assert slate('Click',ref=button)
        lines=snapshot(window).splitlines()
        member=next(i for i,l in enumerate(lines) if re.search(r'textbox "MemberVar_\d+"',l))
    textbox=ref(lines[member+1])
    assert 'textbox ' in lines[member+1]
    assert slate('Click',ref=textbox)
    assert slate('PressKey',key='Ctrl+A')
    assert slate('PressKey',key='BackSpace')
    assert slate('Type',ref=textbox,text=field,submit=True)
    assert f'textbox "{field}"' in snapshot(window),field
    print(field+' defined',flush=True)
final=snapshot(window)
assert all(f'textbox "{field}"' in final for field in ['SpikeDelay','DartInterval','SwingSpeed','ReviveSeconds'])
(QUEUE/'scaling-struct-ui.txt').write_text(final)
print('Four numeric hazard/revive fields configured through the editor',flush=True)
