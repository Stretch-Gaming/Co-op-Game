import unreal as ue,pathlib,time,json,traceback
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent;C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class();ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in ws if ue.GameplayStatics.get_game_mode(w));locals=[p for w in ws for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()]
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC6_Altar/BP_HC6InputProbe').generated_class());held=[p for p in locals if p.get_component_by_class(AC).get_editor_property('CarriedItem')];state={'stage':0,'at':time.monotonic(),'frames':0,'deadline':time.monotonic()+20}
def inject(p,v):
 sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(p.get_controller(),)));sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/IA_Drop'),ue.Vector(v,0,0),[],[])
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline']
  if now<state['at']:return
  if state['stage']==0:
   for p in held:inject(p,1)
   state['frames']+=1
   if state['frames']>=4:
    for p in held:inject(p,0)
    state.update(stage=1,at=now+2)
  elif state['stage']==1:
   for w in ws:
    for p in ue.GameplayStatics.get_all_actors_of_class(w,C):
     p.set_actor_enable_collision(False);p.get_component_by_class(ue.SkeletalMeshComponent).set_visibility(False,True);p.character_movement.gravity_scale=0;p.character_movement.velocity=ue.Vector();p.set_actor_location(ue.Vector(300,-240,110),False,True)
     if p.is_locally_controlled():p.get_component_by_class(ue.SpringArmComponent).target_arm_length=0
   for t in ['KeyA','KeyB','Wrong']:
    a=ue.GameplayStatics.get_all_actors_with_tag(server,t)[0]
    if a.get_editor_property('CarryState')!=2:a.set_actor_location(ue.Vector(-600,1000,100),False,True)
   state.update(stage=2,at=now+2)
  elif state['stage']==2:
   for p in locals:
    dest=ue.Vector(600,0,80);p.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(p.get_component_by_class(ue.CameraComponent).get_world_location(),dest))
   state.update(stage=3,at=now+2)
  elif state['stage']==3:
   p=locals[-1];ue.SystemLibrary.execute_console_command(p.get_world(),'HighResShot 1 filename="'+(HERE/'altar-contact.png').as_posix()+'"',p.get_controller());ue.unregister_slate_post_tick_callback(handle)
 except Exception:
  HERE.joinpath('render-error.json').write_text(json.dumps({'error':traceback.format_exc()}));ue.unregister_slate_post_tick_callback(handle)
handle=ue.register_slate_post_tick_callback(tick)
RESULT={'native_contact_capture_started':True}

