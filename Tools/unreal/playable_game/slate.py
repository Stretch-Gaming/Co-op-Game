import json
import re
import sys
from pathlib import Path
from rpc import call, QUEUE
result=call('SlateInspectorToolset.SlateInspectorToolset',sys.argv[1],json.loads(sys.argv[2]))
value=result.get('returnValue',result) if isinstance(result,dict) else result
if sys.argv[1]=='Snapshot':
    (QUEUE/'slate-latest.txt').write_text(str(value),encoding='utf-8')
if len(sys.argv)>3:
    print('\n'.join(line for line in str(value).splitlines() if re.search(sys.argv[3],line)))
else:
    print(str(value)[:12000])
