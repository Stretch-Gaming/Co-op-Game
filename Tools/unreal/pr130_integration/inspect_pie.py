import unreal as ue
from editor_toolset.toolsets.object import ObjectTools as OBJ
import json
RESULT={'settings':json.loads(OBJ.get_properties(ue.load_object(None,'/Script/UnrealEd.Default__LevelEditorPlaySettings'),['PlayNetMode','PlayNumberOfClients','RunUnderOneProcess'])),'worlds':[]}
RESULT['performance']=json.loads(OBJ.get_properties(ue.load_object(None,'/Script/UnrealEd.Default__EditorPerformanceSettings'),['bThrottleCPUWhenNotForeground']))
for w in ue.EditorLevelLibrary.get_pie_worlds(True):
    ps=ue.GameplayStatics.get_all_actors_of_class(w,ue.Pawn)
    gm=ue.GameplayStatics.get_game_mode(w)
    RESULT['worlds'].append({'world':w.get_path_name(),'server':bool(gm),'time':ue.GameplayStatics.get_time_seconds(w),
        'paused':ue.GameplayStatics.is_game_paused(w),
        'gm':gm.get_class().get_path_name() if gm else None,'default_pawn_class':str(gm.default_pawn_class) if gm else None,
        'controllers':len(ue.GameplayStatics.get_all_actors_of_class(w,ue.PlayerController)),
        'pawns':[{'class':p.get_class().get_path_name(),'name':p.get_name(),'local':p.is_locally_controlled(),
                  'controller':p.get_controller().get_name() if p.get_controller() else None,
                  'player_state':str(p.player_state)} for p in ps]})
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
for command in ('t.IdleWhenNotForeground 0','Slate.AllowSlateToSleep 0','Slate.bAllowThrottling 0'):
    ue.SystemLibrary.execute_console_command(world,command)
