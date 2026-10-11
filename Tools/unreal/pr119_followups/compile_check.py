"""Compile each Blueprint in ARGS['paths'] with warnings as errors; save the ones in ARGS.get('save', [])."""
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
out = {}
for path in ARGS['paths']:
    bp = ue.load_asset(path)
    try:
        with toolset_registry.tool_raising_exceptions():
            BP.compile_blueprint(bp, warnings_as_errors=True)
        out[path] = str(bp.get_editor_property('status')).split('.')[-1].rstrip('>').split(':')[0]
    except Exception as e:
        out[path] = 'ERROR: ' + str(e)[:400]
for path in ARGS.get('save', []):
    assert ue.EditorAssetLibrary.save_asset(path, True), path
RESULT = out
