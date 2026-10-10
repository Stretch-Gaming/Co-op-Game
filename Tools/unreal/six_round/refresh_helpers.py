"""Refresh task helpers after source corrections in this long-lived editor."""
import sys
import importlib
sys.path.insert(0, str(HERE))
import authoring
importlib.reload(authoring)
if 'common' in sys.modules and '/six_round/core/' in sys.modules['common'].__file__.replace('\\', '/'):
    importlib.reload(sys.modules['common'])
RESULT = {'helper_source_refreshed': True}
