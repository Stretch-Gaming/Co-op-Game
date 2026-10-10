"""Offline final report and hashes. Refuses files outside the approved slice."""
import ast,hashlib,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
assert ROOT==pathlib.Path('C:/Users/Stretch/.codex/worktrees/hc4-carrying/Co op Game')
E=pathlib.Path(__file__).parent/'evidence'
def owned(path):
    return path in ['Content/Puzzles/BP_Carryable.uasset','Content/Puzzles/BP_KeyRelic.uasset','Content/Puzzles/BP_Statue.uasset','docs/hc4-verification.md'] or path.startswith(('Content/Puzzles/Carrying/','Content/Puzzles/Test/HC4/','Tools/unreal/hc4_carrying/'))
status=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=ROOT,text=True)
files=[line[3:].strip('"') for line in status.splitlines()]
assert all(owned(p) for p in files),files
for source in pathlib.Path(__file__).parent.glob('*.py'): ast.parse(source.read_text(encoding='utf-8-sig'),filename=str(source))
assert json.loads((E/'assertions.json').read_text())['passed']
saved=json.loads((E/'saved_assets.json').read_text())
for name in ['BP_Carryable','BP_KeyRelic','BP_Statue']:
    assert saved['/Game/Puzzles/'+name]['overlaps']
# Startup unified-error self-tests are engine diagnostics; assess the actual PIE period.
log=(ROOT/'Saved/Logs/HC4.log').read_text(encoding='utf-8-sig',errors='replace')
start=log.find('LogModelContextProtocol: Dispatching toolset tool: \'EditorToolset.EditorAppToolset.StartPIE\'')
assert start>=0
runtime=log[start:]
bad=[line for line in runtime.splitlines() if re.search(r'Accessed None|Log(?:Blueprint|Script|Python|Material|PlayerManagement): (?:Error|Warning)',line)]
assert not bad,bad
(E/'acceptance_runtime.log').write_text('\n'.join(line.rstrip() for line in runtime.splitlines())+'\n',encoding='utf-8')
report={'passed':True,'engine':'5.8.3-58210709','branch':'codex/hc4-carrying','base':'dcecbab75999f1cc976d847a24912f4246ddbc8e','worktree':str(ROOT),'mcp_port':8024,'pie_port':17774,
 'runtime_assertions':json.loads((E/'assertions.json').read_text())['checks'],
 'coverage':['2/3/4 Play As Client input pickup/drop/re-pickup/heavy/reset','competing pickup requests','client authority rejection','late reconnect with carried heavy item','heavy velocity and correction samples','placed handoff without physics','server-only plate overlap weights','two local host players with two remote clients','fresh editor class reload','L_Site01 client smoke'],
 'pending':['Core component attachment and production input/RPC forwarding','AC_Health/downed event hookup and actual health integration tests','merged art assignment and production cave placement/camera fit','physical gamepad and teammate Mac checks'],
 'preserved_pr70':'1e2904c9d42fc6f56c3cb4712441217383d2e247','scope_files':files,'runtime_log_errors':bad,'runtime_log_normalization':'Trailing whitespace removed; messages unchanged.'}
(E/'final_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
targets=[p for p in (ROOT/'Content/Puzzles').rglob('*') if p.is_file() and owned(p.relative_to(ROOT).as_posix())]
targets += [ROOT/'docs/hc4-verification.md']
targets += [p for p in pathlib.Path(__file__).parent.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact_hashes.json']
hashes={p.relative_to(ROOT).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(set(targets))}
(E/'artifact_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print(json.dumps({'passed':True,'runtime_assertions':report['runtime_assertions'],'files':len(hashes),'scope_verified':True,'runtime_log_errors':0}))
