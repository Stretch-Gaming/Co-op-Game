import sys
sys.path.insert(0, str(HERE))
from authoring import *
path = ARGS['asset']
bp = ue.load_asset(path)
owned(bp)
save(bp)
RESULT = {'saved': path}
