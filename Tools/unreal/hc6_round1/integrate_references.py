"""Bind already-merged prop/carrying assets, editing only owned actor defaults."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
base='/Game/Puzzles/Art/HCA2_Props/'
plate=unreal.load_asset('/Game/Puzzles/BP_PressurePlate')
gate=unreal.load_asset('/Game/Puzzles/BP_ChamberGate')
setup=unreal.load_asset('/Game/Puzzles/BP_PuzzleSetup')
refs={'PlateMesh':unreal.load_asset(base+'SM_PressurePlate_Top'),
 'ReleasedMaterial':unreal.load_asset(base+'Materials/MI_HCA2_Stone'),
 'PressedMaterial':unreal.load_asset(base+'Materials/MI_HCA2_StoneCarving')}
assert all(refs.values())
for name,value in refs.items():BP.get_default_object(plate).set_editor_property(name,value)
mesh=unreal.load_asset(base+'SM_ChamberGate_Leaf');assert mesh
BP.get_default_object(gate).set_editor_property('GateMesh',mesh)
statue=unreal.load_asset('/Game/Puzzles/BP_Statue');assert statue
BP.get_default_object(setup).set_editor_property('StatueClass',statue.generated_class())
for bp in (plate,gate,setup):compile_bp(bp);assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
(OUT/'prepared-references.json').write_text(json.dumps({'plate':{k:v.get_path_name() for k,v in refs.items()},
 'gate_mesh':mesh.get_path_name(),'statue_class':statue.generated_class().get_path_name(),
 'imported_art_edited':False,'carrying_assets_edited':False},indent=2))
