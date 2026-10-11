"""Current naturally reached first-room/meeting/relic puzzle impossible gate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from recovery import Recovery
args=dict(globals().get('ARGS',{}));args['case']='impossible'
suite=Recovery(args);suite.name=f'core-impossible-r{suite.index}';RESULT=suite.run()
