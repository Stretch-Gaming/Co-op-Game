"""Read-only Git asset inventory; writes JSON evidence, never binary assets.
Run externally immediately before audit_saved_assets.py. Includes staged,
unstaged and non-ignored untracked Content assets. Missing/deleted entries stay
in the inventory for explicit native reporting rather than disappearing.
"""
import subprocess,json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
EXPECTED=Path(r'C:\Users\Stretch\.codex\worktrees\six-round-adventure\Co op Game')
ALLOWED=('Content/Core/','Content/Hazards/','Content/Player/','Content/Puzzles/','Content/Shared/')
PROTECTED=('Content/Hazards/L_Site01_HZ.umap','Content/Hazards/L_Site02_HZ.umap','Content/Hazards/L_Maze_HZ.umap','Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap','Content/Puzzles/EnvironmentConnection/BP_EnvironmentDoor.uasset','SourceArt/HC/EnvironmentConnection/connection.json.gz')
UNPUBLISHED_AUDIO={f'Content/Player/Audio/{name}.uasset' for name in ('SFX_Taking_FloorShut','SFX_Taking_HeadlampRoll','SFX_Taking_Sting_2D','SFX_Taker_Breath_Loop','SFX_Chase_Build_Loop_2D')}
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def file_hash(relative):
 path=ROOT/relative
 return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def collect():
 assert ROOT.resolve()==EXPECTED.resolve()
 changed=set(git('diff','HEAD','--name-only','-z','--','Content').decode('utf-8').split('\0'))
 changed.update(git('ls-files','--others','--exclude-standard','-z','--','Content').decode('utf-8').split('\0'))
 excluded=sorted(p for p in changed if p in UNPUBLISHED_AUDIO)
 tracked=set(git('ls-files','-z','--','Content/Player/Audio').decode('utf-8').split('\0'))
 assert not tracked.intersection(excluded),'Never exclude a tracked asset from the candidate audit'
 paths=sorted(p for p in changed if p and p.endswith(('.uasset','.umap')) and p not in UNPUBLISHED_AUDIO)
 for p in paths:
  assert p.startswith(ALLOWED) and '..' not in Path(p).parts and '\\' not in p,p
  assert (ROOT/p).resolve().is_relative_to(ROOT.resolve()),p
 leases=json.loads(git('lfs','locks','--json'))
 if isinstance(leases,dict):leases=leases['locks']
 report={'schema':1,'head':git('rev-parse','HEAD').decode().strip(),'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'project':str(ROOT.resolve()),'allowed_roots':list(ALLOWED),'assets':[{'relative_path':p,'asset_path':'/Game/'+p[len('Content/'):].rsplit('.',1)[0],'exists_on_disk':(ROOT/p).is_file(),'sha256':file_hash(p)} for p in paths],'leases':leases,'required_lease_owner':'StretchGaming','protected_hashes':{p:file_hash(p) for p in PROTECTED},'gameplay_acceptance':False}
 report['excluded_unpublished_audio']=[{'path':p,'sha256':file_hash(p),'reason':'unused duplicate; editor deletion leaves physical residue; not staged or published'} for p in excluded]
 queue=ROOT/'Saved/SixRound';queue.mkdir(parents=True,exist_ok=True)
 (queue/'changed-assets.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 return report
if __name__=='__main__':
 report=collect();print(json.dumps({'asset_count':len(report['assets']),'missing_on_disk':[a['relative_path'] for a in report['assets'] if not a['exists_on_disk']],'output':'Saved/SixRound/changed-assets.json'}))
