"""Read-only texture and HC placement inspection; export evidence only."""
import json
from pathlib import Path
import unreal as ue
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert Path(ue.Paths.project_dir()).resolve()==ROOT
parent=ue.load_asset('/Game/Shared/Style/M_Stylized')
texture=ue.MaterialEditingLibrary.get_material_default_texture_parameter_value(parent,'MaskTexture')
task=ue.AssetExportTask()
task.set_editor_property('object',texture)
task.set_editor_property('filename',str(HERE/'shared_mask_default.tga'))
task.set_editor_property('automated',True)
task.set_editor_property('prompt',False)
task.set_editor_property('replace_identical',False)
task.set_editor_property('exporter',ue.TextureExporterTGA())
assert ue.Exporter.run_asset_export_task(task)
report={'mask_source':texture.get_path_name(),'mask_srgb':texture.get_editor_property('srgb'),'mask_compression':str(texture.get_editor_property('compression_settings')),'mask_size':[texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]}
world=ue.EditorLoadingAndSavingUtils.load_map('/Game/Puzzles/L_Site01_HC')
assert world
report['actors']=[]
for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors():
 record={'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'level':a.get_level().get_outermost().get_name(),'tags':[str(t) for t in a.tags]}
 if isinstance(a,ue.StaticMeshActor):
  mesh=a.static_mesh_component.static_mesh
  record['mesh']=mesh.get_path_name() if mesh else None
 report['actors'].append(record)
(HERE/'placement_preflight.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
ue.log('HC-A1_PLACEMENT_INSPECTION_COMPLETE')
