from pathlib import Path
assert Path(ROOT).resolve()==Path('C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game').resolve()
folder_name=ARGS.pop('folder');assert folder_name in ('performance','geometry','audio')
folder=ROOT/'Tools/quality'/folder_name
script=(folder/ARGS.pop('script')).resolve();assert script.is_relative_to(folder.resolve())
OUTPUT=ROOT/'Saved/Quality'/folder_name;OUTPUT.mkdir(parents=True,exist_ok=True)
exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),globals())
