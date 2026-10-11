"""Repair only ApplyScaling's two data inputs by named struct fields.

Also used after the legacy builder's positional DSL, so a reordered user struct
cannot assign the lever count to speed or speed to damage again.
"""
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP

def connect_named_scaling_fields(ghost):
    assert ghost.get_path_name().split('.')[0] == '/Game/Player/Ghosts/BP_Ghost'
    assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring'
    graph = BP.get_graph(ghost, 'ApplyScaling')
    nodes = list(BP.find_nodes(graph))
    breaks = [n for n in nodes if 'BreakSGhostScaling' in str(BP._get_node_info(n).type_id)]
    assert len(breaks) == 1
    outputs = BP._list_pins(breaks[0], ue.EdGraphPinDirection.EGPD_OUTPUT)
    result = {}
    for field in ('GhostSpeed', 'GhostDamage'):
        pins = [p for p in outputs if str(p.get_pin_name()).split('_', 1)[0] == field]
        setters = [n for n in nodes if str(BP._get_node_info(n).type_id).endswith('|Set' + field)]
        assert len(pins) == len(setters) == 1, field
        source = pins[0]
        target = setters[0].find_input_pin(field)
        assert source and target
        old = list(target.list_connected_pins())
        result[field] = {'source_pin': str(source.get_pin_name()),
                         'old_sources': [str(p.get_owning_node().get_name()) + '.' + str(p.get_pin_name()) for p in old]}
        for pin in old:
            target.break_single_pin_link(pin)
        assert source.try_create_connection(target), field
        connected = list(target.list_connected_pins())
        assert len(connected) == 1 and connected[0].get_owning_node() == breaks[0]
        assert str(connected[0].get_pin_name()) == str(source.get_pin_name())
    return result

if __name__ == '__main__' or globals().get('ARGS', {}).get('apply', False):
    import json
    import toolset_registry
    ghost = ue.load_asset('/Game/Player/Ghosts/BP_Ghost')
    result = connect_named_scaling_fields(ghost)
    with toolset_registry.tool_raising_exceptions():
        BP.compile_blueprint(ghost, warnings_as_errors=True)
    assert ghost.get_editor_property('status') == ue.BlueprintStatus.BS_UP_TO_DATE
    assert ue.EditorAssetLibrary.save_loaded_asset(ghost, False)
    RESULT = {'wiring': result, 'compile': 'passed, warnings as errors',
              'saved_only': '/Game/Player/Ghosts/BP_Ghost'}
    (QUEUE / 'scaling-fix.json').write_text(json.dumps(RESULT, indent=2))
