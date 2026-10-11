"""Read-only search for a clear, flat test fixture outside the adventure route."""
import json,unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ignore=[a for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors() if a.actor_has_tag('SixRound.MantleProbe')]
rows=[]
for x,y in [(-600,-600),(-600,-1000),(-300,-600),(0,-1000),(-900,-600)]:
    row={'center':[x,y,75],'failed':[]}
    for complex_trace in (False,True):
        for px,py in [(x,y),(x,y-300)]:
            hit=ue.SystemLibrary.line_trace_single(world,ue.Vector(px,py,200),ue.Vector(px,py,-100),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,complex_trace,ignore,ue.DrawDebugTrace.NONE,True)
            data=hit.to_dict() if hit else {}
            if not hit or abs(data['impact_point'].z)>3 or data['impact_normal'].z<.7:
                actor=data.get('hit_actor');row['failed'].append({'kind':'floor','complex':complex_trace,'xy':[px,py],'z':data['impact_point'].z if hit else None,'actor':actor.get_actor_label() if actor else None})
        for a,b in [(ue.Vector(x,y-300,94),ue.Vector(x,y-240,94)),(ue.Vector(x,y,244),ue.Vector(x,y+30,244))]:
            hit=ue.SystemLibrary.capsule_trace_single(world,a,b,35,90,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,complex_trace,ignore,ue.DrawDebugTrace.NONE,True)
            if hit:row['failed'].append({'kind':'capsule','complex':complex_trace,'actor':hit.to_dict()['hit_actor'].get_actor_label()})
    rows.append(row)
RESULT={'candidates':rows,'clear_candidates':[r['center'] for r in rows if not r['failed']],'no_asset_writes':True}
(QUEUE/'mantle-fixture-calibration.json').write_text(json.dumps(RESULT,indent=2))
