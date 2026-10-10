"""Read-only engine inspection; run with Unreal's PythonScript commandlet."""
import hashlib
import json
from pathlib import Path
import sys
import unreal as ue

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
assert Path(ue.Paths.project_dir()).resolve() == ROOT
parent_file = ROOT / 'Content/Shared/Style/M_Stylized.uasset'
parent_hash = hashlib.sha256(parent_file.read_bytes()).hexdigest()
parent = ue.load_asset('/Game/Shared/Style/M_Stylized')
assert isinstance(parent, ue.Material)
lib = ue.MaterialEditingLibrary

def color(value):
    return [value.r, value.g, value.b, value.a]

def graph(prop):
    start = lib.get_material_property_input_node(parent, prop)
    visited = set()
    def visit(node):
        if node is None:
            return None
        key = node.get_path_name()
        if key in visited:
            return {'ref': key}
        visited.add(key)
        result = {'path': key, 'class': node.get_class().get_name()}
        for field in ('parameter_name', 'default_value', 'constant', 'r', 'g', 'b', 'const_a', 'const_b'):
            try:
                value = node.get_editor_property(field)
                result[field] = color(value) if isinstance(value, ue.LinearColor) else str(value)
            except Exception:
                pass
        result['inputs'] = [visit(n) for n in lib.get_inputs_for_material_expression(parent, node)]
        return result
    return visit(start)

report = {'project': str(ROOT), 'engine': ue.SystemLibrary.get_engine_version(), 'parent_path': parent.get_path_name(),
          'parent_sha256_before': parent_hash, 'blend_mode': str(parent.get_editor_property('blend_mode')),
          'scalars': {str(n): lib.get_material_default_scalar_parameter_value(parent,n) for n in lib.get_scalar_parameter_names(parent)},
          'vectors': {str(n): color(lib.get_material_default_vector_parameter_value(parent,n)) for n in lib.get_vector_parameter_names(parent)},
          'textures': {str(n): lib.get_material_default_texture_parameter_value(parent,n).get_path_name() for n in lib.get_texture_parameter_names(parent)},
          'static_switches': {str(n): lib.get_material_default_static_switch_parameter_value(parent,n) for n in lib.get_static_switch_parameter_names(parent)},
          'roughness_graph': graph(ue.MaterialProperty.MP_ROUGHNESS), 'metallic_graph': graph(ue.MaterialProperty.MP_METALLIC),
          'emissive_graph': graph(ue.MaterialProperty.MP_EMISSIVE_COLOR)}
report['parent_sha256_after'] = hashlib.sha256(parent_file.read_bytes()).hexdigest()
assert report['parent_sha256_before'] == report['parent_sha256_after']
(HERE/'engine_preflight.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
ue.log('HC-A1_ENGINE_INSPECTION_COMPLETE')
