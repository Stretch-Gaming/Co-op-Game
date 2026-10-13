"""Native capsule head clearance along all authored recovery steps."""
import json,unreal as ue
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
layout=json.loads((QUEUE/'layout.json').read_text());rows=[]
for g in layout['gaps']:
    for p in [x for x in g['primitives'] if 'MazeLevel.Recovery' in x.get('tags',[])]:
        loc=p['location'];top=loc[2]+p['size'][2]/2;start=ue.Vector(loc[0],loc[1],top+98)
        hit=ue.SystemLibrary.capsule_trace_single(world,start,start+ue.Vector(0,0,1),42,96,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],ue.DrawDebugTrace.NONE,True)
        d=hit.to_dict() if hit else {};a=d.get('hit_actor');rows.append({'id':p['id'],'clear':not hit,'actor':a.get_actor_label() if a else None,'top':top,'impact':str(d.get('impact_point'))})
(QUEUE/'stair-clearance.json').write_text(json.dumps(rows,indent=2));RESULT=rows
