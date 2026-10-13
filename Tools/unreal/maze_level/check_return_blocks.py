"""Read-only editor collision identification for corrected room guide."""
import json,unreal as ue
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();rows=[]
for p,delta in (([-175,22785,692],[0,-100,0]),([-498,22850,692],[-100,0,0]),([-1175,23250,692],[-100,0,0])):
    start=ue.Vector(*p);hit=ue.SystemLibrary.capsule_trace_single(world,start,start+ue.Vector(*delta),42,96,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],ue.DrawDebugTrace.NONE,True)
    d=hit.to_dict() if hit else {};a=d.get('hit_actor');rows.append({'position':p,'actor':a.get_actor_label() if a else None,'class':a.get_class().get_name() if a else None,'point':str(d.get('impact_point')),'normal':str(d.get('impact_normal'))})
(QUEUE/'return-blocks.json').write_text(json.dumps(rows,indent=2));RESULT=rows
