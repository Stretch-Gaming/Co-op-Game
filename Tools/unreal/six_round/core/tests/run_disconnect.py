"""Current round4 lifecycle regression. ARGS players=3|4; prerequisite remote
middle-slot client is stated in returned result and suite assertion.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from disconnect import Disconnect
suite=Disconnect(globals().get('ARGS',{}));RESULT=suite.run()
