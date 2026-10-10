import json,hashlib,pathlib,subprocess,re,wave
root=pathlib.Path.cwd(); folder=root/'Tools/unreal/taker_art_import'; report={'source_pr':123,'source_commit':'534973a06c6702a82b0b4959b0b98427c1ea6722','canonical':'/Game/Player/Art/Audio','asset_sha256':{},'source_wavs':{},'imports_performed_by_this_worker':False}
for p in sorted((root/'Content/Player/Art/Audio').glob('*.uasset')):
 if p.stem.startswith(('ATT_PG_Tak','SFX_Tak','SFX_Chase_')):
  ref=subprocess.check_output(['git','show','origin/pg/pg-a3-sound-import:'+p.relative_to(root).as_posix()])
  oid=re.search(rb'oid sha256:([0-9a-f]{64})',ref); assert oid
  actual=hashlib.sha256(p.read_bytes()).hexdigest(); assert actual==oid[1].decode(),p
  report['asset_sha256'][p.stem]=actual
from wav_inspect import wav_info
for p in sorted((root/'SourceArt/PG/PG-A3').glob('*.wav')):
 info=wav_info(p); assert info['channels']==1 and info['sample_rate']==48000 and info['bit_depth']==24
 report['source_wavs'][p.stem]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),**info}
assert len(report['asset_sha256'])==11 and len(report['source_wavs'])==9
(folder/'audio-delivery.json').write_text(json.dumps(report,indent=2)+'\n'); print('11 imported package hashes match PR123 LFS; 9 mono48k24bit sources checked')
