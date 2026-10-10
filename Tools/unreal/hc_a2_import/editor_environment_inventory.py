import json
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert levels.load_level('/Game/Maps/L_Site01')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows=[]
for a in actors.get_all_level_actors():
 if a.get_outermost().get_name()!='/Game/Hazards/L_Site01_HZ':continue
 loc=a.get_actor_location();origin,extent=a.get_actor_bounds(False)
 rows.append({'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'location':[loc.x,loc.y,loc.z],'bounds_origin':[origin.x,origin.y,origin.z],'bounds_extent':[extent.x,extent.y,extent.z],'meshes':[c.static_mesh.get_path_name() for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh]})
(root/'Saved/HCA2/hz_inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('HZ_INVENTORY',len(rows))
