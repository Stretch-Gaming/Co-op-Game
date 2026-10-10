"""Stable actor preservation checks; no Unreal import, so bounded tests can run offline."""
def signature(actor):
 t=actor.get_actor_transform()
 return {'path':actor.get_path_name(),'translation':[float(t.translation.x),float(t.translation.y),float(t.translation.z)],'rotation_quaternion':[float(t.rotation.x),float(t.rotation.y),float(t.rotation.z),float(t.rotation.w)],'scale':[float(t.scale3d.x),float(t.scale3d.y),float(t.scale3d.z)],'tags':[str(v)for v in actor.tags]}
def first_difference(before,after):
 for index,(old,new)in enumerate(zip(before,after)):
  if old!=new:
   return {'index':index,'path':old.get('path'),'fields':{key:{'before':old.get(key),'after':new.get(key)}for key in set(old)|set(new)if old.get(key)!=new.get(key)}}
 if len(before)!=len(after):return {'count_before':len(before),'count_after':len(after)}
 return None
