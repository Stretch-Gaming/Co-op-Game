"""Attach the HC-A3 presentation component and replace only prompt painting."""
import hashlib
import json
from pathlib import Path
import unreal
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/"SourceArt/HC/HC-A3/integration"

def compile_bp(bp):
    BP.compile_blueprint(bp)
    assert bp.get_editor_property("status")==unreal.BlueprintStatus.BS_UP_TO_DATE,bp.get_path_name()

def write(bp,name,text):
    g=BP.get_graph(bp,name)
    viewport=list(BP.find_node_types(g,"GetViewportScale"))
    assert len(viewport)==1
    text=text.replace("Viewport|GetViewportScale",viewport[0])
    with toolset_registry.tool_raising_exceptions():
        blueprint_dsl.Transpiler(g,BP.create_node,BP.connect_pins,BP._get_node_info,BP.set_pin_value,
          lambda x:BP.find_nodes(x),delete_node_fn=BP.delete_node,
          find_node_types_fn=lambda f:BP.find_node_types(g,f)).transpile(text)
    compile_bp(bp)

def require_integration_editor():
    """Reject execution against another checkout or engine before any edits."""
    assert Path(unreal.Paths.project_dir()).resolve()==REPO.resolve(), "Open this script's checkout"
    assert unreal.SystemLibrary.get_engine_version().startswith("5.8.3-"), "Requires Unreal 5.8.3"

def run():
    require_integration_editor()
    char=unreal.load_asset("/Game/Core/BP_CoopCharacter")
    prompt=unreal.load_asset("/Game/Puzzles/UI/WBP_InteractPrompt")
    component=unreal.load_asset("/Game/Puzzles/UI/HCA3/AC_HCA3HUD")
    assert char and prompt and component
    protected={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(char) if g.get_name()!="SetupLocalInput"}
    update_before=BP.read_graph_dsl(BP.get_graph(prompt,"UpdatePrompt"))
    subsystem=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles=subsystem.k2_gather_subobject_data_for_blueprint(char)
    lib=unreal.SubobjectDataBlueprintFunctionLibrary
    objects=[lib.get_object_for_blueprint(lib.get_data(h),char) for h in handles]
    if not any(obj and obj.get_class()==component.generated_class() for obj in objects):
        root=next(h for h in handles if lib.is_root_actor(lib.get_data(h)))
        params=unreal.AddNewSubobjectParams(parent_handle=root,new_class=component.generated_class(),blueprint_context=char)
        handle,reason=subsystem.add_new_subobject(params=params)
        assert lib.is_handle_valid(handle),str(reason)
    layout=BP.add_function_graph(char,"ApplyHCA3PromptLayout")
    entry_infos=BP.get_node_infos(BP.find_nodes(layout,entry_points_only=True))
    if not any(p.name=="Widget" for n in entry_infos for p in n.output_pins):
        BP.add_object_function_param(layout,"Widget",unreal.UserWidget.static_class(),True)
    compile_bp(char)
    write(char,"ApplyHCA3PromptLayout",'''(fn ApplyHCA3PromptLayout (Widget)
      (bind dpi (Math|Float|Max(Float) :A (Viewport|GetViewportScale) :B 0.01))
      (UserInterface|Viewport|SetDesiredSizeinViewport :self Widget
        :Size (Math|Vector2D|MakeVector2D :X (/ 330.0 dpi) :Y (/ 170.0 dpi))))''')
    g=BP.get_graph(char,"SetupLocalInput")
    infos=BP.get_node_infos(BP.find_nodes(g))
    sizing=next(n for n in infos if n.type_id.lower().endswith("setdesiredsizeinviewport"))
    existing=next((n for n in infos if "ApplyHCA3PromptLayout" in n.type_id),None)
    if not existing:
        self_pin=next(p for p in sizing.input_pins if p.name.lower()=="self")
        old_out=next(p for p in sizing.output_pins if p.type_id=="Exec")
        assert len(self_pin.connected_pins)==1 and len(old_out.connected_pins)==1
        target=old_out.connected_pins[0]
        call=BP.create_node(g,"CallFunction|ApplyHCA3PromptLayout",unreal.IntPoint(780,500))
        call_info=BP._get_node_info(call)
        inp=next(p for p in call_info.input_pins if p.type_id=="Exec")
        out=next(p for p in call_info.output_pins if p.type_id=="Exec")
        widget_pin=next(p for p in call_info.input_pins if p.name=="Widget")
        BP.connect_pins(self_pin.connected_pins[0],widget_pin.pin_id)
        # Splice one presentation call into the existing sizing chain.
        BP.connect_pins(out.pin_id,target)
        BP.connect_pins(old_out.pin_id,inp.pin_id)
    compile_bp(char)
    write(prompt,"OnPaint",'''(fn OnPaint (Context)
      (if (Variables|Default|GetShowPrompt)
        (bind dpi (Math|Float|Max(Float) :A (Viewport|GetViewportScale) :B 0.01))
        (bind scale (/ 1.0 dpi))
        (Painting|DrawBox :Context Context
          :Position (Math|Vector2D|MakeVector2D :X (* 15.0 scale) :Y (* -87.0 scale))
          :Size (Math|Vector2D|MakeVector2D :X (* 300.0 scale) :Y (* 300.0 scale))
          :Brush "/Game/Puzzles/Art/HCA3_UI/DA_HCA3_InteractBrush.DA_HCA3_InteractBrush")
        (bind full (Utilities|String|ToString(Text) (Variables|Default|GetPrompt)))
        (bind short (select (> (Utilities|String|Len full) 19)
          (Utilities|String|Append (Utilities|String|Left :SourceString full :Count 16) "...") full))
        (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) short)
          :Position (Math|Vector2D|MakeVector2D :X (* 42.0 scale) :Y (* 44.0 scale))
          :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize (* 18.0 scale) :Tint "(R=0.93,G=0.82,B=0.55,A=1)")
        (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String)
          (select (Variables|Default|GetShowProgress) "Hold E / A" "E / A"))
          :Position (Math|Vector2D|MakeVector2D :X (* 42.0 scale) :Y (* 73.0 scale))
          :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize (* 16.0 scale) :Tint "(R=0.93,G=0.82,B=0.55,A=1)")
        (if (Variables|Default|GetShowProgress)
          (Painting|DrawLine :Context Context
            :PositionA (Math|Vector2D|MakeVector2D :X (* 36.0 scale) :Y (* 139.0 scale))
            :PositionB (Math|Vector2D|MakeVector2D :X (* 294.0 scale) :Y (* 139.0 scale))
            :Thickness (* 6.0 scale) :Tint "(R=0.012,G=0.018,B=0.033,A=1)")
          (Painting|DrawLine :Context Context
            :PositionA (Math|Vector2D|MakeVector2D :X (* 36.0 scale) :Y (* 139.0 scale))
            :PositionB (Math|Vector2D|MakeVector2D :X (* (+ 36.0 (* 258.0 (Variables|Default|GetProgress))) scale) :Y (* 139.0 scale))
            :Thickness (* 6.0 scale) :Tint "(R=0.05,G=0.63,B=0.59,A=1)"))))''')
    assert BP.read_graph_dsl(BP.get_graph(prompt,"UpdatePrompt"))==update_before,"Interaction update contract changed"
    after={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(char) if g.get_name() in protected}
    assert after==protected,"Non-presentation character graph changed"
    for bp in (char,prompt):
        compile_bp(bp)
        assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
    report={"passed":True,"character_compile":str(char.get_editor_property("status")),"prompt_compile":str(prompt.get_editor_property("status")),
        "protected_character_graphs_unchanged":list(protected),"update_prompt_contract_unchanged":True,
        "component":component.get_path_name(),"prompt_paint":BP.read_graph_dsl(BP.get_graph(prompt,"OnPaint"))}
    (OUT/"integration-build.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    unreal.log("HC-A3 character component and prompt art integrated.")

if __name__ == "__main__":
    run()
