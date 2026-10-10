import json
import unreal as ue

assert not ue.EditorLevelLibrary.get_pie_worlds(True)
base='/Game/Puzzles/Art/MazeIntegration/Materials'
assets=ue.AssetToolsHelpers.get_asset_tools()
paths=[]
for name,unlit in [('M_MazeVertexLit',False),('M_MazeVertexGlow',True)]:
    path=base+'/'+name
    material=ue.load_asset(path) or assets.create_asset(name,base,ue.Material,ue.MaterialFactoryNew())
    ue.MaterialEditingLibrary.delete_all_material_expressions(material)
    color=ue.MaterialEditingLibrary.create_material_expression(material,ue.MaterialExpressionVertexColor,-200,0)
    material.set_editor_property('shading_model',ue.MaterialShadingModel.MSM_UNLIT if unlit else ue.MaterialShadingModel.MSM_DEFAULT_LIT)
    assert ue.MaterialEditingLibrary.connect_material_property(color,'',ue.MaterialProperty.MP_EMISSIVE_COLOR if unlit else ue.MaterialProperty.MP_BASE_COLOR)
    if not unlit:
        roughness=ue.MaterialEditingLibrary.create_material_expression(material,ue.MaterialExpressionConstant,-200,150)
        roughness.set_editor_property('r',.8)
        assert ue.MaterialEditingLibrary.connect_material_property(roughness,'',ue.MaterialProperty.MP_ROUGHNESS)
    ue.MaterialEditingLibrary.recompile_material(material)
    assert ue.EditorAssetLibrary.save_loaded_asset(material,False)
    paths.append(path)
style=ue.load_asset('/Game/Shared/Style/M_Stylized')
style.set_editor_property('used_with_instanced_static_meshes',True)
ue.MaterialEditingLibrary.recompile_material(style)
assert ue.EditorAssetLibrary.save_loaded_asset(style,False)
RESULT={'materials':paths,'shared_style_instancing_enabled':True}
(QUEUE/'maze-materials.json').write_text(json.dumps(RESULT,indent=2))
