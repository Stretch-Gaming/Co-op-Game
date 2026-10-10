"""Install interfaces with observed Class Settings controls, then compile/read back."""
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from rpc import call, ROOT, QUEUE

PAIRS = [
    ('/Game/Puzzles/BP_CrystalLock', 'BPI_Lightable'),
    ('/Game/Puzzles/BP_MazeDoor', 'BPI_RoundReset'),
    ('/Game/Player/RelicChamber/BP_RelicCage', 'BPI_RoundReset'),
    ('/Game/Player/Taking/BP_TakingDirector', 'BPI_RoundReset'),
    ('/Game/Player/Ghosts/BP_ChaseDirector', 'BPI_RoundReset'),
    ('/Game/Hazards/Maze/BP_MouthSeal', 'BPI_RoundReset'),
    ('/Game/Hazards/Traps/SixRound/BP_SixRoundTrap', 'BPI_RoundReset'),
    ('/Game/Hazards/Traps/BP_SprintSequence', 'BPI_RoundReset'),
    ('/Game/Player/Ghosts/BP_RoundGhostDirector', 'BPI_RoundReset'),
]

def slate(name, **kwargs):
    return call('SlateInspectorToolset.SlateInspectorToolset', name, kwargs)['returnValue']

def ref(line):
    return re.search(r'\[ref=([^]]+)\]', line)[1]

def snapshot(window=''):
    time.sleep(.25)
    return slate('Snapshot', ref=window, maxDepth=60).splitlines()

def editor(script, args):
    process = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('request.py')),
                              script, json.dumps(args)], cwd=ROOT, capture_output=True, text=True)
    if process.returncode:
        raise RuntimeError(process.stdout + process.stderr)
    return json.loads(process.stdout)['result']

evidence = []
for path, interface in PAIRS:
    interface_path = '/Game/Player/Tools/BPI_Lightable' if interface == 'BPI_Lightable' else '/Game/Core/BPI_RoundReset'
    verified = editor('check_interfaces.py', {'pairs': [[path, interface_path]]})
    if verified[0]['implemented']:
        evidence.append({'asset': path, 'interface': interface, 'already_installed': True})
        continue
    editor('open_asset.py', {'asset': path})
    lines = snapshot()
    window = ref(next(l for l in lines if l.startswith('window "' + path.rsplit('/', 1)[1] + '"')))
    lines = snapshot(window)
    settings = next(l for l in lines if 'checkbox "Class Settings"' in l)
    if '[unchecked]' in settings:
        assert slate('Click', ref=ref(settings))
    deadline=time.monotonic()+8
    start=None
    while time.monotonic()<deadline:
        lines=snapshot(window)
        start=next((i for i,l in enumerate(lines) if 'generic "Implemented Interfaces' in l),None)
        if start is not None:break
    assert start is not None,(path,'Class Settings did not finish opening')
    section = lines[start:]
    # A custom combo opens a picker; its nested Add button handles the click.
    add = next(i for i, l in enumerate(section) if 'text "Add"' in l)
    button = next(l for l in reversed(section[:add]) if 'button ' in l)
    slate('Click', ref=ref(button))
    lines = snapshot()
    start = next(i for i, l in enumerate(lines) if 'text "Implement Interface"' in l)
    search = next(l for l in lines[start:] if 'textbox "Search"' in l)
    assert slate('Type', ref=ref(search), text='', submit=False)
    assert slate('PressKey', key='Ctrl+A')
    assert slate('PressKey', key='BackSpace')
    assert slate('Type', ref=ref(search), text=interface, submit=False)
    deadline = time.monotonic() + 5
    hit = None
    while time.monotonic() < deadline:
        lines = snapshot()
        start = next(i for i, l in enumerate(lines) if 'text "Implement Interface"' in l)
        hit = next((l for l in lines[start:] if 'text "' + interface + '"' in l), None)
        if hit:
            break
    assert hit, (path, interface, '\n'.join(lines[start:]))
    assert slate('Click', ref=ref(hit))
    editor('save_asset.py', {'asset': path})
    assert editor('check_interfaces.py', {'pairs': [[path, interface_path]]})[0]['implemented']
    evidence.append({'asset': path, 'interface': interface, 'compiled': True})
    print(json.dumps(evidence[-1]), flush=True)
(QUEUE/'interface-ui.json').write_text(json.dumps(evidence, indent=2))
