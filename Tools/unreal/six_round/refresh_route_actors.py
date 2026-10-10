"""Remove only changed task scene actors before their referenced mesh rebuild."""
import sys,json,unreal as ue
sys.path.insert(0,str(HERE/'world'))
from target_context import open_target
world,package,path=open_target(ARGS)
plan_name=ARGS.get('plan','world-repair-changed-mesh-ids.json')
assert plan_name in ('world-repair-changed-mesh-ids.json','world-repair2-plan.json','world-repair3-plan.json','world-repair4-plan.json')
changes=json.loads((QUEUE/plan_name).read_text())
ids=set(changes['changed_mesh_ids']+changes.get('source_static_remove',[])+changes.get('source_frame_collision_disable',[])+changes.get('source_actor_collision_disable',[]))
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
removed=[]
for actor in actors.get_all_level_actors():
    if actor.get_level().get_outermost().get_name()!=path or not actor.actor_has_tag('SixRoundConnectionScene'):continue
    label=actor.get_actor_label()
    if label.startswith('SixRoundConnectionScene_') and int(label.rsplit('_',1)[-1]) in ids:
        removed.append(label);assert actors.destroy_actor(actor)
assert ue.EditorLoadingAndSavingUtils.save_packages([package],False)
RESULT={'only_task_scene_actors_removed':removed,'before_mesh_rebuild':True}
