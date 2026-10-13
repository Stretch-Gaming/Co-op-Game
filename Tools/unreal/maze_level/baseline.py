"""Capture actual saved scene and gameplay graphs before any level correction."""
import json,hashlib,sys
sys.path.insert(0,str(HERE))
from context import *
assert ue.get_editor_subsystem(ue.LevelEditorSubsystem).load_level(ENTRY)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();ue.GameplayStatics.flush_level_streaming(world)
rows=[]
for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
    t=a.get_actor_transform();origin,extent=a.get_actor_bounds(False)
    rows.append({'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'level':a.get_level().get_outermost().get_name(),
        'path':a.get_path_name(),'location':[t.translation.x,t.translation.y,t.translation.z],
        'rotation':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w],'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z],
        'tags':[str(v) for v in a.tags],'bounds_origin':[origin.x,origin.y,origin.z],'bounds_extent':[extent.x,extent.y,extent.z],
        'meshes':[c.static_mesh.get_path_name() if c.static_mesh else None for c in a.get_components_by_class(ue.StaticMeshComponent)]})
paths=[MODE,'/Game/Core/BP_CoopGameMode','/Game/Puzzles/BP_Checkpoint','/Game/Puzzles/Rounds/BP_RoundDirector',
    '/Game/Puzzles/BP_CrystalLock','/Game/Puzzles/BP_MazeDoor','/Game/Hazards/Maze/BP_MouthSeal']
graphs={p:{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(ue.load_asset(p))} for p in paths}
protected=['Content/Core/BP_CoopGameMode.uasset','Content/Core/BP_CoopCharacter.uasset','Content/Player/Tools/BP_Flare.uasset',
    'Content/Hazards/L_Site01_HZ.umap','Content/Puzzles/EnvironmentConnection/L_ConnectedMaze.umap',
    'Content/Puzzles/Test/SixRound/L_SixRound_Test.umap']
report={'actors':rows,'graphs':graphs,'protected_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected}}
(QUEUE/'baseline.json').write_text(json.dumps(report,indent=2));RESULT={'actors':len(rows),'levels':sorted(set(r['level'] for r in rows))}
