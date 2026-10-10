"""Dump every graph of the given Blueprints as DSL to Saved/PR119/dump/<name>.txt."""
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
out = QUEUE / 'dump'
out.mkdir(exist_ok=True)
summary = {}
for path in ARGS['paths']:
    bp = ue.load_asset(path)
    lines = [f'# {path}', '# variables: ' + ', '.join(str(v) for v in BP.list_variables(bp))]
    for g in BP.list_graphs(bp):
        try:
            text = BP.read_graph_dsl(g)
        except Exception as e:
            text = f'<error {e}>'
        lines.append(f'\n## graph {g.get_name()}\n{text}')
    name = path.rsplit('/', 1)[-1]
    (out / f'{name}.txt').write_text('\n'.join(lines))
    summary[name] = len(lines)
RESULT = summary
