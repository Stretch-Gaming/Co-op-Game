import unreal as ue,json,sys
sys.path.insert(0,str(HERE))
from build import write,compile_bp,var
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
path='/Game/Core/Audio/SFX_RelicPickup'
assert not ue.EditorAssetLibrary.does_asset_exist(path),'Refuse import overwrite'
task=ue.AssetImportTask();task.filename=str(ROOT/'SourceArt/HC/HC2/SFX_RelicPickup.wav');task.destination_path='/Game/Core/Audio';task.destination_name='SFX_RelicPickup';task.automated=True;task.replace_existing=False;task.save=False
ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
sound=ue.load_asset(path);assert isinstance(sound,ue.SoundWave)
assert ue.EditorAssetLibrary.save_loaded_asset(sound)
r=ue.load_asset('/Game/Puzzles/BP_Relic');var(r,'PickupFeedbackCount','int');compile_bp(r)
write(r,'PlayPickupSound','''(fn PlayPickupSound ()
 (Utilities|IsValid :InputObject (Variables|Default|GetPickupSound)
  (:"Is Valid"
   (Audio|PlaySoundatLocation :Sound (Variables|Default|GetPickupSound) :Location (Transformation|GetActorLocation))
   (Variables|Default|SetPickupFeedbackCount (+ (Variables|Default|GetPickupFeedbackCount) 1)))
  (:"Is Not Valid")))''')
ue.get_default_object(r.generated_class()).set_editor_property('PickupSound',sound)
assert ue.EditorAssetLibrary.save_loaded_asset(r)
from editor_toolset.toolsets.object import ObjectTools
(HERE/'sound-import.json').write_text(json.dumps({'passed':True,'sound':sound.get_path_name(),'properties':json.loads(ObjectTools.get_properties(sound,['Duration','NumChannels','SampleRate'])),'feedback_counter_replication':'None; debug count of received cosmetic event, never drives collection'},indent=2))
