import sys
r=sys.modules.get('six_round_core_test_registry')
s=getattr(r,'suite',None)
if s and getattr(r,'handle',None):s.finish(False,'Primary stopped diagnostic to correct its observation code; no asset writes.')
RESULT={'stopped':bool(s)}
