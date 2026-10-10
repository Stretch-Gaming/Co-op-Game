"""Read-only project identity and existing reset-interface readback."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from build import *
guard()
report={'project':str(Path(unreal.Paths.get_project_file_path()).resolve()),'engine':unreal.SystemLibrary.get_engine_version(),'interfaces':{}}
interface=unreal.load_asset('/Game/Core/BPI_RoundReset').generated_class()
for name in ACTORS:
    if unreal.EditorAssetLibrary.does_asset_exist('/Game/Puzzles/'+name):
        bp=unreal.load_asset('/Game/Puzzles/'+name)
        report['interfaces'][name]=unreal.SystemLibrary.does_implement_interface(BP.get_default_object(bp),interface)
(OUT/'editor-identity.json').write_text(json.dumps(report,indent=2))
