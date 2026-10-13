"""Independent joining owner climbs/mantles new ledges during the carrier walk.
Single approach per ledge; all movement thereafter uses its owning subsystem.
"""
import gc,types,json,time,math,traceback,unreal as ue
scopes={id(f.__globals__):f.__globals__ for f in gc.get_objects() if isinstance(f,types.FunctionType) and f.__code__.co_filename.endswith('maze_level\\traversal_runtime.py')}
scope=next(s for s in scopes.values() if s.get('state',{}).get('phase')=='return')
rt=scope['state']['rt'];layout=scope['layout'];floors=scope['floors'];assert rt.ready() and rt.carried(1) is None
cases=[c for c in layout['clusters'] if c['kind']=='amber_mantle']
report={'passed':False,'fixtures':['One approach per authored 150cm ledge; ghosts isolated by carrier harness'],'cases':[],'owner_controller':rt.local(1).get_controller().get_path_name()}
state={'index':int(ARGS.get('start_index',0)),'phase':'approach','at':time.monotonic(),'started':time.monotonic(),'placed':False,'seen_mantle':False}
TR=ue.load_asset('/Game/Player/AC_Traversal').generated_class()
def step(p):state['phase']=p;state['at']=time.monotonic()
def finish(ok,error=None):
    report.update(passed=ok,error=error,phase=state['phase'])
    ue.unregister_slate_post_tick_callback(state['handle'])
    try:rt.inject(1,'IA_Move',0);rt.inject(1,'IA_Jump',0);rt.inject(1,'IA_Climb',0)
    except Exception:report['cleanup_error']=traceback.format_exc()
    (QUEUE/'climb-runtime.json').write_text(json.dumps(report,indent=2))
def tick(delta):
    try:
        assert time.monotonic()-state['started']<120 and rt.ready()
        c=cases[state['index']];piece=next(p for p in c['primitives'] if p['shape']=='rock' and p['size'][2]==150);f=c['forward'];pos=piece['location'];across=piece['across']
        age=time.monotonic()-state['at'];p=rt.players[1].get_actor_location();tr=rt.players[1].get_component_by_class(TR)
        if state['phase']=='approach':
            rt.local(1).get_controller().set_control_rotation(ue.Rotator(yaw=c['yaw']))
            if not state['placed']:
                a=-125;center=c['center'];x=center[0]+f[0]*a-f[1]*across;y=center[1]+f[1]*a+f[0]*across;z=floors.at(c['source_floor'],x,y)
                rt.place(1,(x,y,z+96));rt.local(1).get_controller().set_control_rotation(ue.Rotator(yaw=c['yaw']));state.update(placed=True,floor=z,seen_mantle=False);state['at']=time.monotonic()
            elif age>.8:
                rt.inject(1,'IA_Move',ue.Vector(0,.2 if age<1.1 else 0,0))
                if age>1.1:rt.inject(1,'IA_Jump',1);step('mantle')
        elif state['phase']=='mantle':
            if age>.15:rt.inject(1,'IA_Jump',0)
            state['seen_mantle']=state['seen_mantle'] or tr.get_editor_property('bMantling')
            assert age<6,('Ledge landing timeout',c['id'],str(p),state['seen_mantle'])
            if age>1 and not rt.players[1].character_movement.is_falling() and p.z>piece['floor']+150+80:
                assert state['seen_mantle'];report['cases'].append({'id':c['id'],'passed':True,'method':'Owning Jump requests existing server mantle; lands on authored ledge','position':str(p)})
                (QUEUE/'climb-progress.json').write_text(json.dumps(report,indent=2))
                state['index']+=1
                if state['index']==len(cases):finish(True)
                else:state['placed']=False;step('approach')
    except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':str(QUEUE/'climb-runtime.json'),'ledges':len(cases),'owner':report['owner_controller']}
