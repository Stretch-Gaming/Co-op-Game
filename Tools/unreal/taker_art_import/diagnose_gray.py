"""Read-only gray-preview diagnosis: no shader recompilation, saves or mutations."""
import hashlib,importlib,json
from pathlib import Path
import unreal as ue
ROOT=Path(globals().get('ROOT','C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game')).resolve()
assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
lib=ue.MaterialEditingLibrary; parent=ue.load_asset('/Game/Shared/Style/M_Stylized'); base='/Game/Player/Art/Taker'
def color(v): return [v.r,v.g,v.b,v.a]
def safe(obj,key):
 try:
  v=obj.get_editor_property(key)
  if isinstance(v,ue.LinearColor): return color(v)
  if isinstance(v,ue.Object): return v.get_path_name()
  return str(v)
 except Exception as e: return 'unavailable: '+str(e)
def graph(prop):
 visited=set()
 def visit(node):
  if node is None:return None
  key=node.get_path_name()
  if key in visited:return {'ref':key}
  visited.add(key)
  r={'path':key,'class':node.get_class().get_name()}
  for field in ('parameter_name','default_value','texture','const_a','const_b','coordinate_index','sampler_type'):
   v=safe(node,field)
   if not v.startswith('unavailable:'):r[field]=v
  r['inputs']=[visit(n) for n in lib.get_inputs_for_material_expression(parent,node)]
  return r
 return visit(lib.get_material_property_input_node(parent,prop))
rows={}
for prefix in ('Taker','TakerArm'):
 mesh=ue.load_asset(base+'/SM_'+prefix)
 rows['SM_'+prefix]={'materials':[{'slot':str(x.material_slot_name),'imported_slot':str(x.imported_material_slot_name),'bound':x.material_interface.get_path_name() if x.material_interface else None} for x in mesh.get_editor_property('static_materials')], 'nanite':safe(mesh,'nanite_settings'),'lod_fallback_triangles':mesh.get_num_triangles(0),'nanite_triangles':mesh.get_num_nanite_triangles()}
 mi=ue.load_asset(base+'/MI_'+prefix+'_Body')
 rows['MI_'+prefix+'_Body']={'parent':safe(mi,'parent'),'scalars':{str(n):lib.get_material_instance_scalar_parameter_value(mi,n) for n in lib.get_scalar_parameter_names(parent)},'vectors':{str(n):color(lib.get_material_instance_vector_parameter_value(mi,n)) for n in lib.get_vector_parameter_names(parent)},'textures':{str(n):lib.get_material_instance_texture_parameter_value(mi,n).get_path_name() for n in lib.get_texture_parameter_names(parent)},'raw_static_parameters':safe(mi,'static_parameters'),'texture_overrides':safe(mi,'texture_parameter_values')}
 for suffix in ('BaseColor','ORM'):
  texture=ue.load_asset(base+'/T_'+prefix+'_'+suffix)
  rows['T_'+prefix+'_'+suffix]={k:safe(texture,k) for k in ('srgb','compression_settings','never_stream','lod_bias','virtual_texture_streaming','asset_import_data')}
  rows['T_'+prefix+'_'+suffix]['size']=[texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]
  rows['T_'+prefix+'_'+suffix]['import_source']=texture.get_editor_property('asset_import_data').get_first_filename()
modules={}
for name in ('editor_toolset.toolsets.core','editor_toolset'):
 try:
  m=importlib.import_module(name); modules[name]={'file':m.__file__,'capture_methods':[x for x in dir(m) if 'capture' in x.lower() or 'thumbnail' in x.lower()]}
 except Exception as e:modules[name]={'error':str(e)}
RESULT={'mode':'read_only','engine':ue.SystemLibrary.get_engine_version(),'commandline':ue.SystemLibrary.get_command_line(),'modules':modules,'parent':{'blend':safe(parent,'blend_mode'),'default_switches':{str(n):lib.get_material_default_static_switch_parameter_value(parent,n) for n in lib.get_static_switch_parameter_names(parent)},'default_textures':{str(n):lib.get_material_default_texture_parameter_value(parent,n).get_path_name() for n in lib.get_texture_parameter_names(parent)},'base_color_graph':graph(ue.MaterialProperty.MP_BASE_COLOR),'roughness_graph':graph(ue.MaterialProperty.MP_ROUGHNESS)},'assets':rows,'correction_policy':'If bindings/defaultUV/graph are correct, first repeat capture after all shader compile/texture streaming finishes; then compare normal preview or actor render. No material correction justified by thumbnail alone.'}
out=Path(globals().get('OUTPUT',ROOT/'Saved/NextPriorities/taker_art_import')); out.mkdir(parents=True,exist_ok=True); (out/'gray-preview-diagnosis.json').write_text(json.dumps(RESULT,indent=2)+'\n')
