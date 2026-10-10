"""Read-only PR123 native sound metadata verification; never imports or saves audio."""
import hashlib,json,math,wave
from pathlib import Path
import unreal as ue
import sys
sys.dont_write_bytecode=True
ROOT=Path(globals().get('ROOT','C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game')).resolve()
sys.path.insert(0,str(ROOT/'Tools/unreal/taker_art_import'))
from wav_inspect import wav_info
CANONICAL='/Game/Player/Art/Audio'
SOUNDS={
 'SFX_Taking_HandDrag':('ATT_PG_Taking',False,1.),
 'SFX_Taking_FloorCrack':('ATT_PG_Taking',False,1.),
 'SFX_Taking_FloorShut':('ATT_PG_Taking',False,1.),
 'SFX_Taking_LightsOut':('ATT_PG_Taking',False,1.),
 'SFX_Taking_HeadlampRoll':('ATT_PG_Taking',False,1.),
 'SFX_Taking_Sting_2D':(None,False,1.),
 'SFX_Taker_Breath_Loop':('ATT_PG_Taker',True,1.),
 'SFX_Chase_Loop_2D':(None,True,1.),
 'SFX_Chase_Build_Loop_2D':(None,True,.5)}
def check(ok,msg):
 if not ok: raise RuntimeError(msg)
check(Path(ue.Paths.project_dir()).resolve()==ROOT,'Wrong project')
check(not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE first')
manifest=json.loads((ROOT/'Tools/unreal/taker_art_import/audio-delivery.json').read_text())
rows={}
for name,(att,loop,volume) in SOUNDS.items():
 asset=ue.load_asset(CANONICAL+'/'+name); check(isinstance(asset,ue.SoundWave),'Missing sound '+name)
 source=ROOT/'SourceArt/PG/PG-A3'/(name+'.wav')
 info=wav_info(source); check(info['channels']==1 and info['sample_rate']==48000 and info['bit_depth']==24,'Source WAV format mismatch')
 duration=info['duration']
 check(asset.get_editor_property('num_channels')==1,'Native channels mismatch '+name)
 check(math.isclose(asset.get_editor_property('duration'),duration,abs_tol=.002),'Native duration mismatch '+name)
 check(asset.get_editor_property('looping')==loop,'Loop flag mismatch '+name)
 check(math.isclose(asset.get_editor_property('volume'),volume,abs_tol=.00001),'Volume mismatch '+name)
 attenuation=asset.get_editor_property('attenuation_settings')
 check(attenuation== (ue.load_asset(CANONICAL+'/'+att) if att else None),'Attenuation binding mismatch '+name)
 if loop: check(asset.get_editor_property('virtualization_mode')==ue.VirtualizationMode.RESTART,'Virtualization mismatch')
 p=ROOT/'Content/Player/Art/Audio'/(name+'.uasset')
 check(hashlib.sha256(p.read_bytes()).hexdigest()==manifest['asset_sha256'][name],'Delivered sound package bytes changed '+name)
 rows[name]={'path':asset.get_path_name(),'duration':duration,'channels':1,'source_sample_rate':48000,'source_bit_depth':24,'looping':loop,'volume':volume,'attenuation':att,'sha256':manifest['asset_sha256'][name]}
for name,(radius,falloff) in {'ATT_PG_Taking':(300.,3000.),'ATT_PG_Taker':(150.,1500.)}.items():
 a=ue.load_asset(CANONICAL+'/'+name); check(isinstance(a,ue.SoundAttenuation),'Missing attenuation')
 s=a.get_editor_property('attenuation')
 check(s.attenuate and s.spatialize and s.attenuation_shape==ue.AttenuationShape.SPHERE and s.distance_algorithm==ue.AttenuationDistanceModel.NATURAL_SOUND,'Wrong 3D attenuation shape/mode')
 check(math.isclose(s.attenuation_shape_extents.x,radius,abs_tol=.001) and math.isclose(s.falloff_distance,falloff,abs_tol=.001),'Wrong attenuation distances')
 p=ROOT/'Content/Player/Art/Audio'/(name+'.uasset'); check(hashlib.sha256(p.read_bytes()).hexdigest()==manifest['asset_sha256'][name],'Attenuation package bytes changed')
 rows[name]={'radius':radius,'falloff':falloff,'distance':'Natural Sound','shape':'Sphere'}
RESULT={'passed':True,'mode':'read_only','rows':rows,'native_sample_rate':'Source WAV48k validated; native SoundWave compressed platform rate not exposed/checked','pending':['Listen for levels/seams','Coordinator repoints future hooks to canonical Art/Audio himself','Both local split-screen 2D chase layers start together; sting owner-only']}
out=Path(globals().get('OUTPUT',ROOT/'Saved/NextPriorities/taker_art_import')); out.mkdir(parents=True,exist_ok=True); (out/'audio-verification.json').write_text(json.dumps(RESULT,indent=2)+'\n')
