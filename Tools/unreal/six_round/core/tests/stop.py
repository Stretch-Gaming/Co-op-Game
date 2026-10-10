"""Stop/release a running core test; does not reset gameplay."""
import sys
module=sys.modules.get('six_round_core_test_registry')
if module and getattr(module,'handle',None):module.suite.finish(False,'Stopped explicitly before completing its acceptance gate')
RESULT={'test_callback_stopped':True,'gameplay_not_reset':True}
