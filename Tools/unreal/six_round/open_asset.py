"""Open only the specified task-owned asset for missing editor UI operations."""
import unreal as ue
path = ARGS['asset']
assert path.startswith(('/Game/Puzzles/', '/Game/Player/', '/Game/Hazards/', '/Game/Core/'))
asset = ue.load_asset(path)
assert asset, path
ue.get_editor_subsystem(ue.AssetEditorSubsystem).open_editor_for_assets([asset])
RESULT = {'opened': path}
