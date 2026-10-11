"""Read-only saved packages; authoritative scenario fixtures and real owning input only."""
import sys,json,time,traceback,base64,re,os
import unreal as ue
assert os.getpid()==int((QUEUE/'pid').read_text())
sys.path.insert(0,str(QUEUE))
from pg_harness import load_harness
h=load_harness()(ARGS,'fade-'+ARGS.get('run','test')+'-'+ARGS['case']);gm=ue.GameplayStatics.get_game_mode(h.server);case=ARGS['case'];capture_prefix=ARGS.get('run','test')+'-'+case+'-'+ARGS['profile']+'-'+str(ARGS.get('target_slot','auto'))+'-'+str(ARGS.get('style','auto'));timeline=[];state={};began=time.time()
def event(name,details=None):
 timeline.append({'epoch':time.time(),'elapsed':time.time()-began,'server_time':ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds(),'event':name,'details':details,'round':h.round(),'snapshot':h.snapshot()})
def screens(label):
 snap=ue.load_object(None,'/Script/SlateInspectorToolset.Default__SlateInspectorToolset').call_method('Snapshot',args=('',0,False));(QUEUE/(capture_prefix+'-'+label+'-windows.txt')).write_text(snap)
 refs=re.findall(r'^window .*?\[ref=([^\]]+)\]',snap,re.M)
 out=[]
 for ref in refs:
  image=ue.load_object(None,'/Script/SlateInspectorToolset.Default__SlateInspectorToolset').call_method('Screenshot',args=(ref,))
  if image.data:
   p=QUEUE/(capture_prefix+'-'+label+'-'+ref+'.png');p.write_bytes(base64.b64decode(image.data));out.append(str(p))
 event('rendered windows '+label,{'paths':out,'slate':snap})
 return out
original_finish=h.finish
def finish(passed,error=None):
 try:event('finish',{'passed':passed,'error':error})
 except Exception:
  passed=False;error=(error or '')+'\nEvidence capture at finish failed: '+traceback.format_exc()
 r=original_finish(passed,error)
 r.update({'timeline':timeline,'native_mac_tested':True,'packet_emulation_tested':False,'case':case,'began_epoch':began});h.report.write_text(json.dumps(r,default=str,indent=2))
 if not passed:ue.get_editor_subsystem(ue.LevelEditorSubsystem).editor_request_end_play()
 return r
h.finish=finish
assert h.round()['phase']==0,h.round()
gm.call_method('StartRound',args=(1,));gm.call_method('ClearRound');gm.call_method('StartRound',args=(2,))
h.fixtures.append({'kind':'server round setup fixture','calls':['StartRound(1)','ClearRound()','StartRound(2)'],'natural_route_proven':False});event('R2 setup')
directors=ue.GameplayStatics.get_all_actors_of_class(h.server,h.classes['taking']);assert len(directors)==1;director=directors[0]
def caches():
 result=[]
 for pid,p in h.locals.items():
  d=h.actor_peer(p.get_world(),director)
  row={'owner':pid,'slot':p.player_state.get_editor_property('ColorSlot'),'world':p.get_world().get_name(),'view_target':p.get_controller().get_view_target().get_path_name()}
  for name in ('PresentedTakingController','PresentedTakingPawn','PresentedTakingStarted','bPresentedTakingFadeOwned'):
   try:
    value=d.get_editor_property(name);row[name]=value.get_path_name() if isinstance(value,ue.Object) else value
   except Exception:row[name]='baseline absent'
  result.append(row)
 return result
old_event=event
def event(name,details=None):
 old_event(name,details);timeline[-1]['fade_caches']=caches()
def taking():
 v=director.get_editor_property('Victim');start=director.get_editor_property('TakingStarted');now=ue.GameplayStatics.get_game_state(h.server).get_server_world_time_seconds()
 return v,start,now-start
h.transition('wait_taking')
def tick(delta):
 elapsed=h.elapsed()
 if (QUEUE/'STOP').exists():raise AssertionError('Resource stop marker')
 if 'configured' not in state and director.get_editor_property('StartedAttempt')==1 and not director.get_editor_property('Victim'):
  if 'target_slot' in ARGS:
   assert h.n==2;slot=int(ARGS['target_slot']);target=next(p for p in h.server_pawns if p.player_state.get_editor_property('ColorSlot')==slot)
   ue.GameplayStatics.apply_damage(target,9999,None,None,None)
   director.call_method('ChooseRemainingPlayer')
   assert director.get_editor_property('RemainingSlot')==1-slot
   h.comp(target,'health').call_method('ResetHealth')
   h.fixtures.append({'kind':'disclosed bounded server survivor selection fixture before unchanged native taking','victim_slot':slot,'player_id':target.player_state.player_id,'calls':['ApplyDamage(target,9999)','ChooseRemainingPlayer()','target.AC_Health.ResetHealth()'],'remaining_slot':director.get_editor_property('RemainingSlot'),'natural_survivor_transaction_proven':False,'owning_network_input_proof':False})
  if 'style' in ARGS:
   desired=int(ARGS['style']);assert desired in (0,1,2);previous=[]
   for i in range(3):
    value=director.call_method('NextPresentationStyle');previous.append(value)
    if value==(desired+2)%3:break
   else:raise AssertionError(('Bounded style fixture failed',previous))
   h.fixtures.append({'kind':'PIE-only server style-sequence fixture before unchanged native taking','desired_next_style':desired,'calls':'NextPresentationStyle()','returned_styles':previous,'natural_style_sequence_proven':False,'owning_network_input_proof':False})
  state['configured']=True
 if case=='normal':
  v,start,age=taking()
  if h.phase=='wait_taking' and v and age>=.4:
   assert age<.65,age;state['victim']=v.player_state.player_id;state['start']=start;state['style']=director.get_editor_property('ScareStyle')
   if 'style' in ARGS:assert state['style']==ARGS['style']
   if 'target_slot' in ARGS:assert v.player_state.get_editor_property('ColorSlot')==ARGS['target_slot']
   event('normal black interval before Hide',{'age':age,**state});screens('normal-black')
   owner=h.locals[state['victim']];d=h.actor_peer(owner.get_world(),director);d.call_method('HideTakingPresentation');h.fixtures.append({'kind':'owning presentation Hide fixture during valid black interval; not network input proof','victim':state['victim'],'age':age})
   if ARGS.get('patched'):assert d.get_editor_property('bPresentedTakingFadeOwned') and d.get_editor_property('PresentedTakingController')==owner.get_controller()
   h.transition('normal_post')
  elif h.phase=='normal_post' and age>=.8:
   assert director.get_editor_property('Teleported');event('normal after teleport',{'age':age});screens('normal-post-teleport');h.transition('normal_finish')
  elif h.phase=='normal_finish' and (not v) and elapsed>.7:
   event('normal completed');screens('normal-restored')
   for row in caches():
    if ARGS.get('patched'):assert not row['bPresentedTakingFadeOwned'] and row['PresentedTakingController'] is None,row
   h.check('normal taking telemetry: teleport occurred; cached owning fade preserved through active Hide and cleared after completion; rendered screenshots require review',state.copy());h.finish(True)
  return
 if case.startswith('cancel'):
  v,start,age=taking()
  if h.phase=='wait_taking' and v and age>=float(ARGS.get('cancel_age',.45)):
   assert age<float(ARGS.get('cancel_age',.45))+.3,('Missed bounded cancellation window',age)
   state['victim']=v.player_state.player_id;state['age']=age;state['style']=director.get_editor_property('ScareStyle');state['origin']=str(director.get_editor_property('VictimOrigin'));state['teleported']=director.get_editor_property('Teleported')
   if ARGS.get('patched'):
    own=h.locals[state['victim']];d=h.actor_peer(own.get_world(),director);assert d.get_editor_property('bPresentedTakingFadeOwned') and d.get_editor_property('PresentedTakingController')==own.get_controller()
   event('taking cancellation fixture before',state.copy());screens('before-cancel')
   gm.call_method('FailRound');h.fixtures.append({'kind':'server FailRound interruption fixture','victim':state['victim'],'taking_age':age,'style':state['style'],'owning_network_input_proof':False});event('FailRound fixture');h.transition('cancelled')
  elif h.phase=='cancelled' and elapsed>.65:
   event('cancelled readback');screens('cancelled')
   assert director.get_editor_property('Victim') is None,'Taking Victim not cleared on failure'
   for world in h.worlds:
    p=h.pawn(world,state['victim']);assert not p.get_editor_property('bTakenProtected');assert not h.prop(p,'health','bDead')
   if ARGS.get('patched'):
    for row in caches():assert not row['bPresentedTakingFadeOwned'] and row['PresentedTakingController'] is None,row
   h.check('interruption clears Victim/protection without death across peers',state.copy());h.transition('retry')
  elif h.phase=='retry' and h.round()['phase']==1 and h.round()['attempt']==2:
   event('same-index retry');screens('retry');h.transition('no_replay')
  elif h.phase=='no_replay' and elapsed>6:
   assert h.round()=={'index':2,'attempt':2,'phase':1},h.round()
   for world in h.worlds:
    d=h.actor_peer(world,director);assert d.get_editor_property('Victim') is None
    for pid in h.ids:
     p=h.pawn(world,pid);assert not p.get_editor_property('bTakenProtected');assert not h.prop(p,'health','bDead')
   for pid,p in h.locals.items():assert p.get_controller().get_view_target()==p
   h.check('R2 attempt2 no taking replay; owners retain own view targets (rendered fade needs screenshot review)')
   if ARGS.get('repeat_cleanup'):
    director.call_method('ResetTaking',args=(2,2));director.call_method('FinishTaking')
    for p in h.locals.values():h.actor_peer(p.get_world(),director).call_method('HideTakingPresentation')
    h.fixtures.append({'kind':'late repeated presentation/reset fixture after completed retry, not network delay proof','calls':['server.ResetTaking(2,2)','server.FinishTaking()','each owner world.HideTakingPresentation()']});h.transition('late_cleanup')
   else:h.finish(True)
  elif h.phase=='late_cleanup' and elapsed>.6:
   assert director.get_editor_property('Victim') is None
   for row in caches():assert not row['bPresentedTakingFadeOwned'] and row['PresentedTakingController'] is None,row
   event('late repeated cleanup complete');screens('late-cleanup');h.check('late repeated ResetTaking/FinishTaking/Hide remains idempotent with cleared Victim/cache; no packet emulation claim');h.finish(True)
  return
 raise AssertionError('Unsupported fade regression case: '+case)
RESULT=h.register(tick)
