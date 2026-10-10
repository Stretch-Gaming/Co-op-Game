import pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
lines=(ROOT/'Saved/Logs/HC6Altar.log').read_text(errors='replace').splitlines()
interval='\n'.join(l for l in lines if l.startswith('[2026.10.10-14.24.') or l.startswith('[2026.10.10-14.25.'))
errors=[l for l in interval.splitlines() if any(t in l for t in ['Blueprint Runtime Error','Accessed None',': Error:'])]
assert not errors,errors
(HERE/'clients-2-runtime.log').write_text(interval)
(HERE/'clients-2-log.json').write_text(json.dumps({'timestamp_interval':'2026-10-10 14:24-14:25 UTC','errors':errors,'passed':True},indent=2))
print(json.dumps({'clients_2_scoped_log_errors':errors}))
