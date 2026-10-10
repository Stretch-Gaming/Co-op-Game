"""Create the HC-A3 local-player HUD component; does not attach it to Core."""
import json
from pathlib import Path
import unreal
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl

REPO=Path(__file__).resolve().parents[3]
PATH="/Game/Puzzles/UI/HCA3/AC_HCA3HUD"

def compile_bp(bp):
    BP.compile_blueprint(bp)
    assert bp.get_editor_property("status")==unreal.BlueprintStatus.BS_UP_TO_DATE

def write(bp,name,text):
    graph=BP.get_graph(bp,name)
    with toolset_registry.tool_raising_exceptions():
        blueprint_dsl.Transpiler(graph,BP.create_node,BP.connect_pins,BP._get_node_info,BP.set_pin_value,
          lambda g:BP.find_nodes(g),delete_node_fn=BP.delete_node,
          find_node_types_fn=lambda f:BP.find_node_types(graph,f)).transpile(text)
    compile_bp(bp)
    entries=BP.get_node_infos(BP.find_nodes(graph,entry_points_only=True))
    assert any(p.connected_pins for e in entries for p in e.output_pins if p.type_id=="Exec")

def require_integration_editor():
    """Reject execution against another checkout or engine before any edits."""
    assert Path(unreal.Paths.project_dir()).resolve()==REPO.resolve(), "Open this script's checkout"
    assert unreal.SystemLibrary.get_engine_version().startswith("5.8.3-"), "Requires Unreal 5.8.3"

def run():
    require_integration_editor()
    bp=unreal.load_asset(PATH) if unreal.EditorAssetLibrary.does_asset_exist(PATH) else BP.create("/Game/Puzzles/UI/HCA3","AC_HCA3HUD",unreal.ActorComponent.static_class())
    assert bp
    assert unreal.load_asset("/Game/Core/BP_CoopCharacter")
    for name,cls in (("HUDWidget",unreal.UserWidget.static_class()),("HUDController",unreal.PlayerController.static_class())):
        if name not in BP.list_variables(bp): BP.add_object_variable(bp,name,cls)
    for name in ("ClearHUD","RefreshHUD","StartHUD","StopHUD","RefreshPromptLayout"):
        BP.add_function_graph(bp,name)
    ensure=BP.add_function_graph(bp,"EnsureHUD")
    if not any(p.name=="Controller" for n in BP.get_node_infos(BP.find_nodes(ensure,entry_points_only=True)) for p in n.output_pins):
        BP.add_object_function_param(ensure,"Controller",unreal.PlayerController.static_class(),True)
    compile_bp(bp)
    write(bp,"ClearHUD",'''(fn ClearHUD ()
      (Utilities|IsValid :InputObject (Variables|Default|GetHUDWidget)
        (:"Is Valid"
          (Widget|RemovefromParent :self (Variables|Default|GetHUDWidget))
          (Variables|Default|SetHUDWidget "None")
          (Variables|Default|SetHUDController "None"))
        (:"Is Not Valid"
          (Variables|Default|SetHUDWidget "None")
          (Variables|Default|SetHUDController "None"))))''')
    write(bp,"EnsureHUD",'''(fn EnsureHUD (Controller)
      (Utilities|IsValid :InputObject (Variables|Default|GetHUDWidget)
        (:"Is Valid" (CallFunction|RefreshPromptLayout))
        (:"Is Not Valid"
          (bind widget (UserInterface|CreateWidget :Class "/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD.WBP_HCA3RoundHUD_C" :OwningPlayer Controller))
          (Variables|Default|SetHUDWidget widget)
          (Variables|Default|SetHUDController Controller)
          (UserInterface|Viewport|AddtoPlayerScreen :self widget)
          (UserInterface|Viewport|SetDesiredSizeinViewport :self widget :Size "(X=0,Y=0)")
          (UserInterface|Viewport|SetAnchorsinViewport :self widget :Anchors "(Minimum=(X=0,Y=0),Maximum=(X=1,Y=1))")
          (UserInterface|Viewport|SetAlignmentinViewport :self widget :Alignment "(X=0,Y=0)")
          (CallFunction|RefreshPromptLayout))))''')
    write(bp,"RefreshPromptLayout",'''(fn RefreshPromptLayout ()
      (bind pawn (Utilities|Casting|CastToBP_CoopCharacter :Object (Components|GetOwner))
        (:then
          (bind widget (Class|BPCoopCharacter|GetPromptWidget :self pawn))
          (Utilities|IsValid :InputObject widget
            (:"Is Valid"
              (Class|BPCoopCharacter|ApplyHCA3PromptLayout :self pawn :Widget widget)
              (UserInterface|Viewport|SetAnchorsinViewport :self widget :Anchors "(Minimum=(X=0.5,Y=0.82),Maximum=(X=0.5,Y=0.82))")
              (UserInterface|Viewport|SetAlignmentinViewport :self widget :Alignment "(X=0.5,Y=0.5)"))
            (:"Is Not Valid")))
        (:CastFailed)))''')
    write(bp,"RefreshHUD",'''(fn RefreshHUD ()
      (bind pawn (Utilities|Casting|CastToPawn :Object (Components|GetOwner))
        (:then
          (if (Pawn|IsLocallyControlled :self pawn)
            (bind pc (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController :self pawn))
              (:then
                (if (!= pc (Variables|Default|GetHUDController))
                  (CallFunction|ClearHUD)
                  (CallFunction|EnsureHUD :Controller pc)
                  (else (CallFunction|EnsureHUD :Controller pc))))
              (:CastFailed (CallFunction|ClearHUD)))
            (else (CallFunction|ClearHUD))))
        (:CastFailed (CallFunction|ClearHUD))))''')
    write(bp,"StartHUD",'''(fn StartHUD ()
      (CallFunction|RefreshHUD)
      (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshHUD" :Time 0.2 :bLooping true))''')
    write(bp,"StopHUD",'''(fn StopHUD ()
      (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshHUD")
      (CallFunction|ClearHUD))''')
    graph=BP.get_graph(bp,"EventGraph")
    for event,handler,y in (("ReceiveBeginPlay","StartHUD",0),("ReceiveEndPlay","StopHUD",240)):
        entry=BP.add_event(bp,event,unreal.IntPoint(0,y))
        info=BP._get_node_info(entry)
        exec_out=next(p for p in info.output_pins if p.type_id=="Exec")
        if not exec_out.connected_pins:
            call=BP.create_node(graph,"CallFunction|"+handler,unreal.IntPoint(260,y))
            exec_in=next(p for p in BP._get_node_info(call).input_pins if p.type_id=="Exec")
            BP.connect_pins(exec_out.pin_id,exec_in.pin_id)
    compile_bp(bp)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp)
    report={"passed":True,"component":bp.get_path_name(),"compile":str(bp.get_editor_property("status")),
      "attached_to_core":False,"owning_pawn_and_controller_only":True,"graphs":{name:BP.read_graph_dsl(BP.get_graph(bp,name)) for name in ("RefreshHUD","ClearHUD","EventGraph")}}
    (REPO/"SourceArt/HC/HC-A3/integration/component-build.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__":
    run()
