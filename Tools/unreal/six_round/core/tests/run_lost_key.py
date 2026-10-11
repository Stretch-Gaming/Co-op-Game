"""Current-round lost-key regression; naturally reach escape before this test."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from recovery import Recovery
args=dict(globals().get('ARGS',{}));args['case']='lost_key'
suite=Recovery(args);suite.name='core-lost-key-r6';RESULT=suite.run()
