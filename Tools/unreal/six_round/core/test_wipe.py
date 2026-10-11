"""Current-round wipe/impossible/lost-key gate; explicit setup fixtures only.
ARGS case=wipe|impossible|lost_key. Run all round/count combinations in manifest.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'tests'))
from recovery import Recovery
suite=Recovery(globals().get('ARGS',{}));suite.name=f'core-{suite.case}-r{suite.index}';RESULT=suite.run()
