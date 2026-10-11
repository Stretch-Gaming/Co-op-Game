"""Remove only this task's unpublished duplicate waves after canonical hooks move."""
import json,hashlib,unreal as ue
records=json.loads((QUEUE/'unused-sound-hashes.json').read_text())
deleted=[]
for record in records:
    file=__import__('pathlib').Path(record['Path'])
    assert file.parent==ROOT/'Content/Player/Audio'
    assert file.name.startswith('SFX_') and hashlib.sha256(file.read_bytes()).hexdigest().upper()==record['Hash']
    path='/Game/Player/Audio/'+file.stem
    referencers=list(ue.EditorAssetLibrary.find_package_referencers_for_asset(path,True))
    assert not referencers,(path,referencers)
    assert ue.EditorAssetLibrary.delete_asset(path)
    deleted.append(path)
RESULT={'task_duplicate_waves_removed':deleted,'published_ArtAudio_untouched':True}
