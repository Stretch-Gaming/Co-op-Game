"""Offline scope, raw asset hashes, protected LFS hashes and result gate."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().rstrip('\r\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
owned=['Content/Puzzles/BP_PressurePlate.uasset','Content/Puzzles/BP_PuzzleSetup.uasset','Content/Puzzles/BP_ChamberGate.uasset','Content/Puzzles/BP_StartPad.uasset']
protected=git('ls-files','Content/Core','Content/Maps','Content/Puzzles/UI','Content/Puzzles/DT_RoundScaling.uasset','Content/Puzzles/L_Site01_HC.umap').splitlines()
protection=[]
for path in protected:
    pointer=git('show','origin/main:'+path)
    if pointer.startswith('version https://git-lfs.github.com/spec/v1'):
        expected=next(l.split(':',1)[1] for l in pointer.splitlines() if l.startswith('oid sha256:'))
        actual=sha(ROOT/path)
        assert actual==expected,path
        protection.append({'path':path,'sha256':actual,'matches_origin_main':True})
changes=git('status','--porcelain','--untracked-files=all').splitlines()
allowed=lambda p:p in owned or p.startswith(('Content/Puzzles/Test/HC6/','Tools/unreal/hc6_round1/')) or p=='docs/hc6-round1-verification.md'
assert all(allowed(line[3:]) for line in changes),changes
summary=[]
for prefix in ('clients','split'):
    for count in (2,3,4):
        data=json.loads((HERE/f'{prefix}-{count}.json').read_text())
        assert data['passed'] and len(data['checks'])==25,(prefix,count)
        summary.append({'run':f'{prefix}-{count}','players':count,'split':prefix=='split','checks':len(data['checks']),
          'passed':True,'hold_elapsed_seconds':data.get('start_hold_elapsed_seconds'),'duration_seconds':data['duration_seconds']})
assets=[{'path':p,'sha256':sha(ROOT/p),'size':(ROOT/p).stat().st_size} for p in owned]
for path in sorted((ROOT/'Content/Puzzles/Test/HC6').glob('*')):
    if path.suffix in ('.uasset','.umap'):assets.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'size':path.stat().st_size})
assert json.loads((HERE/'core-comparison.json').read_text())['passed']
assert json.loads((HERE/'configuration-verification.json').read_text())['passed']
report={'baseline':git('rev-parse','origin/main'),'branch':git('branch','--show-current'),'protected_assets':protection,
 'assets':assets,'matrix':summary,'fixture_only':True,'passed':True}
(HERE/'delivery-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'asset_count':len(assets),'protected_assets':len(protection),'matrix_cases':len(summary)}))
