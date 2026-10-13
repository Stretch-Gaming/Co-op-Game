"""End climb overlaps below the landing; cosmetic grips must not snag capsules."""
import json,sys
sys.path.insert(0,str(HERE))
from context import *
lease(WORLD)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem);assert editor.load_level(ENTRY)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();ue.GameplayStatics.flush_level_streaming(world)
levels={l.get_outermost().get_name():l for l in ue.EditorLevelUtils.get_levels(world)}
actors={a.get_actor_label():a for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()}
layout=json.loads((QUEUE/'layout.json').read_text());count=0
for cluster in layout['clusters']:
    for p in cluster['primitives']:
        if p['shape']!='climb_volume':continue
        a=actors['MazeVariety_'+p['id']];assert a.get_level()==levels[WORLD]
        a.set_actor_location(ue.Vector(*p['location']),False,True);a.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(*(v/2 for v in p['size'])));count+=1
for hall,y,z in (('A',9250,-300),('B',15500,400)):
    for slot,x in enumerate((-1275,925)):
        a=actors[f'Maze_Hall{hall}_Climb{slot}'];assert a.get_level()==levels[HC]
        a.set_actor_location(ue.Vector(x,y-225,z+97.5),False,True);a.get_component_by_class(ue.BoxComponent).set_box_extent(ue.Vector(220,110,197.5))
        for k in range(5):actors[f'Maze_Hall{hall}_Grip{slot}_{k}'].static_mesh_component.set_collision_profile_name('NoCollision')
save_level(levels[WORLD]);save_level(levels[HC])
RESULT={'path_climb_zones':count,'perch_climb_zones':4,'landing_overlap_ends_5cm_below_top':True,'grips_nonblocking':True}
(QUEUE/'climb-finish.json').write_text(json.dumps(RESULT,indent=2))
