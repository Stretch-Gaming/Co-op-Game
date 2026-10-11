from pathlib import Path
name=ARGS.pop('folder');assert name in ('taker_art_import','connection_refresh')
folder=ROOT/'Tools/unreal'/name
script=(folder/ARGS.pop('script')).resolve();assert script.is_relative_to(folder.resolve())
OUTPUT=ROOT/'Saved/NextPriorities'/name;OUTPUT.mkdir(parents=True,exist_ok=True)
exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),globals())
