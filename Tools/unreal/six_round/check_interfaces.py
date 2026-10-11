"""Read back editor interface installation, without changing assets."""
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
pairs = ARGS.get('pairs', [('/Game/Puzzles/BP_CrystalLock', '/Game/Core/BPI_RoundReset'),
         ('/Game/Puzzles/BP_CrystalLock', '/Game/Player/Tools/BPI_Lightable')])
RESULT = []
for asset, interface in pairs:
    bp, iface = ue.load_asset(asset), ue.load_asset(interface)
    RESULT.append({'asset': asset, 'interface': interface,
                   'implemented': ue.SystemLibrary.does_implement_interface(BP.get_default_object(bp), iface.generated_class())})
