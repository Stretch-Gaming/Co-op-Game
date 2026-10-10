import json,unreal as ue
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
assert editor.load_level('/Game/Maps/L_Site01')
rows=[]
for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
 if a.get_level().get_outermost().get_name()!='/Game/Hazards/L_Site01_HZ':continue
 origin,extent=a.get_actor_bounds(True)
 if origin.x+extent.x<50 or origin.x-extent.x>800 or origin.y+extent.y<1050 or origin.y-extent.y>3000 or origin.z+extent.z<0:continue
 c=a.get_component_by_class(ue.StaticMeshComponent)
 rows.append({'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':str(a.get_actor_location()),'bounds_center':[origin.x,origin.y,origin.z],'bounds_extent':[extent.x,extent.y,extent.z],'mesh':c.static_mesh.get_path_name() if c and c.static_mesh else None,'collision':str(c.get_collision_enabled()) if c else None,'hidden':a.get_editor_property('hidden')})
(OUTPUT/'room-doorway-inventory.json').write_text(json.dumps(rows,indent=2))
RESULT=rows
