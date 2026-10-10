"""Consume the reviewed PG input regression without editing its tooling."""
import json
queue=ROOT/'Saved/PGSignatureFix'
queue.mkdir(parents=True,exist_ok=True)
(queue/'options.json').write_text(json.dumps(ARGS))
source=ROOT/'Tools/unreal/pg_signature_fix/test_input.py'
exec(compile(source.read_text(encoding='utf-8-sig'),str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
