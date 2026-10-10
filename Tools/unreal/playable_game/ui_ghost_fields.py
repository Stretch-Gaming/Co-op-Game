import re,time
from rpc import call,QUEUE
def slate(name,**kwargs):return call('SlateInspectorToolset.SlateInspectorToolset',name,kwargs).get('returnValue')
def snapshot(ref):time.sleep(.2);return slate('Snapshot',ref=ref,maxDepth=60)
def ref(line):return re.search(r'\[ref=([^]]+)\]',line)[1]
root=snapshot('');window=ref(next(l for l in root.splitlines() if l.startswith('window "S_GhostScaling"')))
slate('Observe',ref=window,maxDepth=60)
for previous,target in [('SpikeDelay','GhostCount'),('DartInterval','GhostSpeed'),('SwingSpeed','GhostDamage'),('ReviveSeconds','LeverCount')]:
 lines=snapshot(window).splitlines()
 if any(f'textbox "{target}"' in l for l in lines):continue
 index=next(i for i,l in enumerate(lines) if f'textbox "{previous}"' in l);textbox=ref(lines[index+1])
 assert slate('Click',ref=textbox);assert slate('PressKey',key='Ctrl+A');assert slate('PressKey',key='BackSpace');assert slate('Type',ref=textbox,text=target,submit=True)
 assert f'textbox "{target}"' in snapshot(window)
 print(target+' defined',flush=True)
(QUEUE/'ghost-struct-ui.txt').write_text(snapshot(window))
