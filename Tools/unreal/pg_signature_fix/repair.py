"""Explicit editor repair; saves only the locked PG test character."""
import hashlib
import json
from pathlib import Path
import unreal
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

ROOT = Path(__file__).resolve().parents[3]
assert ROOT == Path('C:/Users/Stretch/Development/Co op Game/Saved/MergeBuild/Source')
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == ROOT / 'CoopGame.uproject'
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-')
ASSET = '/Game/Player/Test/BP_PG_TestCharacter'
disk = ROOT / 'Content/Player/Test/BP_PG_TestCharacter.uasset'
assert hashlib.sha256(disk.read_bytes()).hexdigest() == 'a9a85c98aca731a39035537322ceedd7419081e7bd93116b199dc180cc42d8b9'
bp = unreal.load_asset(ASSET)
assert unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp).get_path_name() == '/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C'
graph = BP.get_graph(bp, 'EventGraph')
protected = {name: BP.read_graph_dsl(BP.get_graph(bp, name)) for name in
             ['UserConstructionScript', 'SpawnTestGhost', 'AddTestInput']}
before = {g.get_name(): BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
def key(node):
    return BP.get_node_infos([node])[0].type_id.split('|')[-1].replace('_', '').lower()
def inherited_call(function, position):
    # The action-menu search excludes these inherited functions. Resolve the
    # existing skeleton function by name through the editor's call-node API.
    node = unreal.BlueprintGraphEditor.get_graph_editor(graph).add_call_function_node(function)
    assert node, function
    BP.set_node_position(node, position)
    return node

with toolset_registry.tool_raising_exceptions():
    removed = []
    for node in list(BP.find_nodes(graph)):
        if key(node) in {'serverinteractbegin', 'serverinteractend', 'dointeractbegin', 'dointeractend'}:
            removed.append(BP.get_node_infos([node])[0].type_id)
            BP.delete_node(node)
    for name in ['FindInteractable', 'DoInteractBegin', 'DoInteractEnd']:
        BP.remove_function_graph(bp, name)
    # Refresh the skeleton after removing obsolete RPC declarations and calls.
    BP.compile_blueprint(bp, warnings_as_errors=True)
    action_nodes = [n for n in BP.find_nodes(graph) if 'IA_PG_Interact' in BP.get_node_infos([n])[0].type_id]
    assert len(action_nodes) == 1
    action = action_nodes[0]
    links = {}
    for index, (pin_name, function) in enumerate([
            ('Started', 'PressInteract'), ('Completed', 'ReleaseInteract'), ('Canceled', 'ReleaseInteract')]):
        pin = action.find_output_pin(pin_name)
        for old in list(pin.list_connected_pins()):
            pin.break_single_pin_link(old)
        call = inherited_call(function, unreal.IntPoint(700, 1000 + index * 180))
        assert pin.try_create_connection(call.find_execute_pin())
        links[pin_name] = function
    # This subclass overrides controller changes for its test mapping context.
    # Run the parent's existing setup/cleanup before its preserved PG chain.
    controller_events = [n for n in BP.find_nodes(graph) if key(n) == 'eventreceivecontrollerchanged']
    assert len(controller_events) == 1
    event_pin = controller_events[0].find_then_pin()
    previous = list(event_pin.list_connected_pins())
    assert len(previous) == 1
    parent_setup = inherited_call('HC1ControllerChanged', unreal.IntPoint(400, 100))
    for pin in previous:
        event_pin.break_single_pin_link(pin)
        assert parent_setup.find_then_pin().try_create_connection(pin)
    assert event_pin.try_create_connection(parent_setup.find_execute_pin())
    BP.compile_blueprint(bp, warnings_as_errors=True)
assert bp.get_editor_property('status') == unreal.BlueprintStatus.BS_UP_TO_DATE
for name, dsl in protected.items():
    assert BP.read_graph_dsl(BP.get_graph(bp, name)) == dsl, name
assert not any(key(n) in {'serverinteractbegin', 'serverinteractend'} and isinstance(n, unreal.K2Node_CustomEvent)
               for n in BP.find_nodes(graph))
assert unreal.EditorAssetLibrary.save_loaded_asset(bp, False)
after = {g.get_name(): BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
report = {'asset': ASSET, 'compiled': True, 'removed_nodes': removed,
          'inherited_input_calls': links, 'controller_setup': 'HC1ControllerChanged',
          'preserved_graphs': list(protected), 'before': before, 'after': after,
          'sha256': hashlib.sha256(disk.read_bytes()).hexdigest()}
out = ROOT / 'Saved/PGSignatureFix/repair.json'
out.write_text(json.dumps(report, indent=2))
