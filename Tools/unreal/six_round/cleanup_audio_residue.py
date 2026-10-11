"""Editor-only cleanup of five unpublished duplicate SoundWaves.
No filesystem deletion/move and no canonical Art/Audio mutation. Header-verified:
IAssetRegistry.h ScanFilesSynchronous(InFilePaths,bForceRescan), FileHelpers.h
ReloadPackages(packages,out bool,out text,interaction mode), EditorAssetLibrary.h
FindPackageReferencersForAsset/ DeleteAsset. API success alone is not completion:
verify physical residue and report restart needed rather than claim success.
"""
import json,hashlib,traceback
from pathlib import Path
import unreal as ue
ROOT=Path(__file__).resolve().parents[3] if '__file__' in globals() else Path(ROOT)
EXPECTED=Path(r'C:\Users\Stretch\.codex\worktrees\six-round-adventure\Co op Game').resolve()
assert ROOT.resolve()==EXPECTED and Path(ue.Paths.project_dir()).resolve()==EXPECTED
assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE before duplicate cleanup'
QUEUE=ROOT/'Saved/SixRound'
NAMES={'SFX_Taking_FloorShut','SFX_Taking_HeadlampRoll','SFX_Taking_Sting_2D','SFX_Taker_Breath_Loop','SFX_Chase_Build_Loop_2D'}
records=json.loads((QUEUE/'unused-sound-hashes.json').read_text(encoding='utf-8-sig'))
leases=json.loads((QUEUE/'acquired-leases.json').read_text(encoding='utf-8-sig'))
leased={r['path'] for r in leases}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None
canonical_root=ROOT/'Content/Player/Art/Audio'
def canonical_hashes():return {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in canonical_root.rglob('*.uasset')}
canonical_before=canonical_hashes()
report={'writes':[],'rows':[],'errors':[],'restart_needed':False,'canonical_before':canonical_before,'scope':'five unpublished duplicates only; own leases retained','source_headers_verified':True}
registry=ue.AssetRegistryHelpers.get_asset_registry()
selected=[]
def require_preflight(condition,message):
 if not condition:
  report['errors'].append({'error':str(message),'stage':'preflight_no_deletions'});report['passed']=False
  (QUEUE/'audio-residue-cleanup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
  raise AssertionError(message)
# Validate every selected original file/lease/hash before calling a mutating API.
for record in records:
 file=Path(record['Path']);assert file.parent.resolve()==(ROOT/'Content/Player/Audio').resolve()
 if file.stem not in NAMES:
  report['rows'].append({'path':str(file),'status':'outside_five_scope_skipped','exists_on_disk':file.is_file()});continue
 assert file.suffix=='.uasset'
 relative=str(file.relative_to(ROOT)).replace('\\','/');path='/Game/Player/Audio/'+file.stem
 row={'path':path,'relative_path':relative,'sha256_before':sha(file),'exists_before':file.is_file(),'status':'pending','reload':None,'referencers':[],'delete_api_returned':None}
 report['rows'].append(row)
 if not file.is_file():row['status']='already_absent';continue
 require_preflight(relative in leased,('Exact own lease not recorded',relative))
 require_preflight(row['sha256_before']==record['Hash'].upper(),('Original duplicate hash mismatch',relative))
 selected.append((file,path,row))
assert {Path(r['Path']).stem for r in records if Path(r['Path']).stem in NAMES}==NAMES
for file,path,row in selected:
 try:
  # These are physical filenames, not package paths. ForceRescan revisits stale
  # files and waits for in-memory objects per UE5.8 AssetRegistry.cpp implementation.
  registry.scan_files_synchronous([str(file)],True)
  row['registered_after_scan']=bool(ue.EditorAssetLibrary.does_asset_exist(path))
  if not row['registered_after_scan']:
   try:
    package=ue.find_object(None,path)
    if package is None:
     loaded=ue.find_object(None,path+'.'+file.stem)
     package=loaded.get_outermost() if loaded else None
    reload_api=getattr(ue.EditorLoadingAndSavingUtils,'reload_packages',None)
    mode=getattr(getattr(ue,'ReloadPackagesInteractionMode',None),'ASSUME_NEGATIVE',None)
    if package and reload_api and mode is not None:
     assert package.get_name()==path,'Refuse reload of any other package'
     row['reload']=str(reload_api([package],mode))
     registry.scan_files_synchronous([str(file)],True)
    else:row['reload']='unavailable or no loaded exact package; primary restart may be required'
   except Exception:row['reload']=traceback.format_exc()
  row['registered_before_delete']=bool(ue.EditorAssetLibrary.does_asset_exist(path))
  if not row['registered_before_delete']:
   row['status']='registry_missing_physical_residue';report['restart_needed']=True
   raise AssertionError('Physical duplicate remains unregistered after exact rescan/reload')
  row['referencers']=list(ue.EditorAssetLibrary.find_package_referencers_for_asset(path,True))
  assert not row['referencers'],('Duplicate has referencers; refuse force delete',path,row['referencers'])
  assert sha(file)==row['sha256_before'],'Hash changed before delete; refuse'
  row['delete_api_returned']=bool(ue.EditorAssetLibrary.delete_asset(path))
  row['exists_after']=file.is_file();row['registered_after_delete']=bool(ue.EditorAssetLibrary.does_asset_exist(path));row['sha256_after']=sha(file)
  report['writes'].append(path)
  if row['exists_after']:
   row['status']='delete_reported_success_but_physical_residue' if row['delete_api_returned'] else 'delete_failed_physical_residue'
   report['restart_needed']=True;raise AssertionError('Editor deletion left physical file; primary restart required, no disk fallback')
  assert row['delete_api_returned'] and not row['registered_after_delete'],'Editor API/registry deletion not confirmed'
  row['status']='verified_absent_after_editor_delete'
 except Exception:
  row['error']=traceback.format_exc();row['exists_after']=file.is_file();row['sha256_after']=sha(file)
  report['errors'].append({'path':path,'status':row['status'],'error':row['error']})
report['canonical_after']=canonical_hashes()
if report['canonical_after']!=canonical_before:report['errors'].append({'error':'Canonical Art/Audio hashes changed'})
report['passed']=not report['errors'] and all(not (ROOT/'Content/Player/Audio'/(name+'.uasset')).is_file() for name in NAMES)
report['leases_released']=False
(QUEUE/'audio-residue-cleanup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
RESULT=report
assert report['passed'],'Cleanup incomplete; inspect audio-residue-cleanup.json and restart_needed; no filesystem fallback'
