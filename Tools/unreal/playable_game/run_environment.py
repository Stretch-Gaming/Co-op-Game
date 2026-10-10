from pathlib import Path
ENV=ROOT/'Tools/unreal/environment_connection'
OUTPUT=ROOT/'Saved/EnvironmentConnection';OUTPUT.mkdir(parents=True,exist_ok=True)
script=(ENV/ARGS.pop('script')).resolve();assert script.is_relative_to(ENV.resolve())
exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),globals())
