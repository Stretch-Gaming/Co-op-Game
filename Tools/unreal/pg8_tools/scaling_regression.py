"""Read-only packages; disclosed PIE scaling-row fixtures, not 3/4-player proof.

Run in a fresh two-player network Lobby after the saved Ghost compile. Each
server fixture spawn runs the normal Blueprint BeginPlay/ApplyScaling path.
The original RoundState is restored on success or failure; no phase changes.
"""
import json
import time
import traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.data_table import DataTableTools as DT

worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert worlds
server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
gs=ue.GameplayStatics.get_game_state(server)
original=gs.get_editor_property('RoundState')
row_field='ScalingRow_14_43C74C304230A92B6620E1A520A230C0'
rows=json.loads(DT.get_rows(ue.load_asset('/Game/Player/DT_GhostScaling'),['2','3','4']))
ghost_class=ue.load_asset('/Game/Player/Ghosts/BP_Ghost').generated_class()
library=ue.load_object(None,'/Script/Engine.Default__GameplayStatics')
actors=[];checks=[]
try:
    for row in ('2','3','4'):
        current=gs.get_editor_property('RoundState')
        current.set_editor_property(row_field,ue.Name(row))
        gs.set_editor_property('RoundState',current)
        assert str(gs.call_method('GetScalingRow'))==row
        transform=ue.Transform(location=ue.Vector(0,2000,120))
        actor=library.call_method('BeginDeferredActorSpawnFromClass',args=(server,ghost_class,transform,ue.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,ue.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        assert actor;actors.append(actor)
        actor=library.call_method('FinishSpawningActor',args=(actor,transform,ue.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        values={name.lower():float(value) for name,value in rows[row].items()}
        speed=float(actor.get_editor_property('GhostSpeed'));damage=float(actor.get_editor_property('GhostDamage'))
        checks.append({'row':row,'speed':speed,'damage':damage,'expected_speed':values['ghostspeed'],'expected_damage':values['ghostdamage'],'begin_play_path':True})
        assert speed==values['ghostspeed'] and damage==values['ghostdamage'], checks[-1]
    RESULT={'passed':True,'rows':checks,'topology':'Existing two-player network PIE; rows 3 and 4 are fixtures, not additional players','fixtures':['Server PIE-only RoundState property fixture with only ScalingRow changed','PIE-only initial server ghost spawn, native Blueprint BeginPlay/ApplyScaling'],'saved_packages_modified':False}
except Exception:
    RESULT={'passed':False,'rows':checks,'error':traceback.format_exc()}
finally:
    gs.set_editor_property('RoundState',original)
    for actor in actors:
        if ue.SystemLibrary.is_valid(actor):actor.destroy_actor()
    RESULT['original_row_restored']=str(gs.call_method('GetScalingRow'))==str(original.get_editor_property(row_field))
    assert RESULT['original_row_restored']
    (QUEUE/'scaling-regression.json').write_text(json.dumps(RESULT,indent=2))
