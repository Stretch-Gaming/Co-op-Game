"""Verify and save ONLY the ten already imported PG-A7 packages. Never reimports.
Default mode is verify-only. Primary passes mode=finalize explicitly to save.
"""
import hashlib,json
from pathlib import Path
import unreal as ue
ROOT=Path(globals().get('ROOT','C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game')).resolve()
HERE=ROOT/'Tools/unreal/taker_art_import'
EXPECTED=Path('C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game').resolve()
DEST='/Game/Player/Art/Taker'
NAMES=('SM_Taker','SM_TakerArm','T_Taker_BaseColor','T_Taker_ORM','T_TakerArm_BaseColor','T_TakerArm_ORM','MI_Taker_Body','MI_TakerArm_Body','M_TakerEyes','MI_Taker_Eyes')
OUTPUT=Path(globals().get('OUTPUT',ROOT/'Saved/NextPriorities/taker_art_import'))
ARGS=globals().get('ARGS',{})
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def guard():
    assert ROOT==EXPECTED and Path(ue.Paths.project_dir()).resolve()==ROOT,'Wrong exact checkout'
    assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-'),'Wrong engine'
    assert not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE first'
    assert OUTPUT.resolve().is_relative_to((ROOT/'Saved').resolve()),'Wrong output path'
    baseline=json.loads((OUTPUT/'preflight.json').read_text())
    assert baseline['paths']==[DEST+'/'+n for n in NAMES],'Wrong preflight asset set'
    assert digest(ROOT/'Content/Shared/Style/M_Stylized.uasset')==baseline['parent_sha256'],'Shared parent hash changed'
    manifest=json.loads((HERE/'source-manifest.json').read_text())
    assert manifest['source_commit']=='60ae5e0250e790f943064f54e400574e8285463c','Wrong source commit'
    for f in manifest['files']:
        p=(ROOT/f['path']).resolve(); assert p.is_relative_to((ROOT/'SourceArt/PG/PG-A7').resolve())
        assert p.stat().st_size==f['bytes'] and digest(p)==f['sha256'],'Source hash changed '+f['path']
    registered=ue.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(DEST,True)
    assert {str(a.asset_name) for a in registered}==set(NAMES),'Unexpected or missing registered taker assets'
    return baseline
baseline=guard()
# Read-only native verification before the first save.
exec(compile((HERE/'verify_import.py').read_text(encoding='utf-8-sig'),str(HERE/'verify_import.py'),'exec'),globals())
verification=verify_assets()
mode=ARGS.get('mode','verify-only')
assert mode in ('verify-only','finalize'),'Expected verify-only or finalize'
RESULT={'passed':True,'verification':verification,'saved':False,'parent_sha256':baseline['parent_sha256'],'source_manifest_sha256':digest(HERE/'source-manifest.json')}
if mode=='finalize':
    for name in NAMES:
        asset=ue.load_asset(DEST+'/'+name); assert asset is not None
        assert ue.EditorAssetLibrary.save_loaded_asset(asset,False),'Targeted save failed '+name
    guard()
    RESULT['saved']=True
    RESULT['asset_sha256']={name:digest(ROOT/'Content/Player/Art/Taker'/(name+'.uasset')) for name in NAMES}
    RESULT['paths']=[DEST+'/'+name for name in NAMES]
OUTPUT.mkdir(parents=True,exist_ok=True)
(OUTPUT/('finalize.json' if mode=='finalize' else 'verify-only.json')).write_text(json.dumps(RESULT,indent=2)+'\n')
