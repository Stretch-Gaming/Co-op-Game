"""Native collision checks for the retained room, real gaps and carrier corridor."""
import gzip,json,math,sys
sys.path.insert(0,str(HERE))
from context import *
from layout import Floors
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);assert editor.load_level(ENTRY)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();ue.GameplayStatics.flush_level_streaming(world)
actors=list(ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors())
ignore=[a for a in actors if a.get_class()!=ue.StaticMeshActor.static_class() and not a.get_component_by_class(ue.HierarchicalInstancedStaticMeshComponent)]
layout=json.loads((QUEUE/'layout.json').read_text());source=json.loads(gzip.decompress((ROOT/layout['source']).read_bytes()));floors=Floors(source)
report={'passed':False,'floor_failures':[],'capsule_failures':[],'gap_failures':[],'samples':0,
    'method':'Native floor/capsule clearance with puzzle closures excluded; does not establish actual movement, timing or human play.'}
def ray(p,up=125,down=150):
    return ue.SystemLibrary.line_trace_single(world,ue.Vector(p[0],p[1],p[2]+up),ue.Vector(p[0],p[1],p[2]-down),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
def hit_info(hit):
    if not hit:return None
    d=hit.to_dict();a=d.get('hit_actor');p=d.get('impact_point');return {'actor':a.get_actor_label() if a else None,'point':[p.x,p.y,p.z] if p else None}
def sample(nodes):
    prior=None
    for a,b in zip(nodes,nodes[1:]):
        length=math.dist(a,b);steps=max(1,math.ceil(length/75))
        for j in range(steps):
            t=j/steps;p=[a[k]+(b[k]-a[k])*t for k in range(3)]
            candidates=[floors.at(i,p[0],p[1],False) for i in range(318,323)];candidates=[z for z in candidates if z is not None]
            if p[1]>=3200 and candidates:p[2]=min(candidates,key=lambda z:abs(z-p[2]))
            hit=ray(p);report['samples']+=1
            if not hit or abs(hit.to_dict()['impact_point'].z-p[2])>45:report['floor_failures'].append({'sample':p,'hit':hit_info(hit)})
            center=ue.Vector(p[0],p[1],p[2]+102)
            if prior is not None:
                blocked=ue.SystemLibrary.capsule_trace_single(world,prior,center,35,90,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
                if blocked:
                    obstacle=blocked.to_dict().get('hit_actor');origin,extent=obstacle.get_actor_bounds(False) if obstacle else (ue.Vector(),ue.Vector())
                    step_height=ue.get_default_object(ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()).character_movement.max_step_height
                    raised=ue.SystemLibrary.capsule_trace_single(world,prior+ue.Vector(0,0,step_height),center+ue.Vector(0,0,step_height),35,90,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,True)
                    if not (obstacle and origin.z+extent.z-p[2]<=step_height and not raised):report['capsule_failures'].append({'sample':p,'hit':hit_info(blocked)})
                    else:report.setdefault('walkable_low_step_samples',[]).append({'sample':p,'actor':obstacle.get_actor_label(),'top_z':origin.z+extent.z,'max_step_height':step_height,'raised_sweep_clear':True})
            prior=center
    return
sample(layout['return_route']['nodes'])
for gap in layout['gaps']:
    p=gap['center'];hit=ray(p,up=100,down=gap['depth_cm']+100)
    if not hit or abs(hit.to_dict()['impact_point'].z-gap['pit_floor'])>40:report['gap_failures'].append({'id':gap['id'],'expected_pit_floor':gap['pit_floor'],'hit':hit_info(hit)})
    stairs=[p for p in gap['primitives'] if 'MazeLevel.Recovery' in p.get('tags',())]
    for p in stairs:
        top=p['location'][2]+p['size'][2]/2;hit=ray([p['location'][0],p['location'][1],top],up=30,down=100)
        if not hit or abs(hit.to_dict()['impact_point'].z-top)>20:report['gap_failures'].append({'id':p['id'],'expected_top':top,'hit':hit_info(hit)})
report['passed']=not any(report[k] for k in ('floor_failures','capsule_failures','gap_failures'))
(QUEUE/'geometry.json').write_text(json.dumps(report,indent=2));RESULT={k:(len(v) if isinstance(v,list) else v) for k,v in report.items()}
