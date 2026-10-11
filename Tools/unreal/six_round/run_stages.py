"""Run an explicit ordered list; stop on the first native failure."""
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
for stage in json.loads(sys.argv[1]):
    script,args=stage
    print('Native stage: '+script,flush=True)
    process=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('request.py')),script,json.dumps(args)],cwd=root)
    if process.returncode:raise SystemExit(process.returncode)
