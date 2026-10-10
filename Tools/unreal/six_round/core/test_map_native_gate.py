"""Fresh-Lobby native E/movement barrier test for every independent owner."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'tests'))
from native_gate import NativeGate
suite=NativeGate(globals().get('ARGS',{}));RESULT=suite.run()
