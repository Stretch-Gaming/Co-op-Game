import pathlib,json,re
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
text=(ROOT/'Saved/Logs/HC6Altar.log').read_text(errors='replace')
interval='\n'.join(l for l in text.splitlines() if l.startswith('[2026.10.10-14.29.') or l.startswith('[2026.10.10-14.30.'))
errors=[l for l in interval.splitlines() if any(t in l for t in ['Blueprint Runtime Error','Accessed None',': Error:'])]
(HERE/'clients-3-runtime.log').write_text(interval)
(HERE/'clients-3-log.json').write_text(json.dumps({'timestamp_interval':'2026-10-10 14:29-14:30 UTC','errors':errors,'passed':not errors},indent=2));print(json.dumps({'errors':errors}))
