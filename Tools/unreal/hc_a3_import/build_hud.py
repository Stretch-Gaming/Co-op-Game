"""Build only HC-A3 presentation assets through Unreal editor APIs."""
import json
from pathlib import Path
import unreal
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl

REPO=Path(__file__).resolve().parents[3]
UI="/Game/Puzzles/UI/HCA3/"
ART="/Game/Puzzles/Art/HCA3_UI/"
OUT=REPO/"SourceArt/HC/HC-A3/integration"

def compile_bp(bp):
    BP.compile_blueprint(bp)
    assert bp.get_editor_property("status")==unreal.BlueprintStatus.BS_UP_TO_DATE,bp.get_path_name()

def write(bp,name,dsl):
    graph=BP.get_graph(bp,name)
    with toolset_registry.tool_raising_exceptions():
        blueprint_dsl.Transpiler(graph,BP.create_node,BP.connect_pins,BP._get_node_info,BP.set_pin_value,
            lambda g:BP.find_nodes(g),delete_node_fn=BP.delete_node,
            find_node_types_fn=lambda f:BP.find_node_types(graph,f)).transpile(dsl)
    compile_bp(bp)
    entries=BP.get_node_infos(BP.find_nodes(graph,entry_points_only=True))
    assert any(p.connected_pins for entry in entries for p in entry.output_pins if p.type_id=="Exec"),name

def require_integration_editor():
    """Reject execution against another checkout or engine before any edits."""
    assert Path(unreal.Paths.project_dir()).resolve()==REPO.resolve(), "Open this script's checkout"
    assert unreal.SystemLibrary.get_engine_version().startswith("5.8.3-"), "Requires Unreal 5.8.3"

def run():
    require_integration_editor()
    for path in ("/Game/Core/BP_CoopGameState","/Game/Core/S_RoundState","/Game/Core/E_RoundPhase"):
        assert unreal.load_asset(path)
    saved=[]
    for suffix,texture_name in (("Relic","RelicIcon"),("Round","RoundBannerFrame"),("Interact","InteractPromptFrame")):
        path=ART+"DA_HCA3_"+suffix+"Brush"
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            asset=unreal.load_asset(path)
        else:
            texture=unreal.load_asset(ART+"T_HUD_"+texture_name)
            factory=unreal.SlateBrushAssetFactory()
            asset=unreal.AssetToolsHelpers.get_asset_tools().create_asset("DA_HCA3_"+suffix+"Brush",ART.rstrip("/"),unreal.SlateBrushAsset,factory)
        assert asset
        texture=unreal.load_asset(ART+"T_HUD_"+texture_name)
        brush=unreal.WidgetLibrary.make_brush_from_texture(texture,512,512)
        asset.set_editor_property("brush",brush)
        assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
        saved.append(asset.get_path_name())
    widget=unreal.load_asset(UI+"WBP_HCA3RoundHUD")
    assert widget
    graph=BP.get_graph(widget,"OnPaint")
    dsl='''(fn OnPaint (Context)
      (bind size (UserInterface|Geometry|GetLocalSize :Geometry (Widget|GetCachedGeometry)))
      (bind (width height) (Math|Vector2D|BreakVector2D :InVec size))
      (bind dpi (Math|Float|Max(Float) :A (UserInterface|Viewport|GetViewportScale) :B 0.01))
      (bind scale (/ (Math|Float|Clamp(Float)
        :Value (Math|Float|Min(Float) :A (/ (* width dpi) 1280.0) :B (/ (* height dpi) 720.0))
        :Min 0.85 :Max 1.25) dpi))
      (bind center (/ width 2.0))
      (Painting|DrawBox :Context Context :Position (Math|Vector2D|MakeVector2D :X (* 24.0 scale) :Y (* 24.0 scale))
        :Size (Math|Vector2D|MakeVector2D :X (* 64.0 scale) :Y (* 64.0 scale))
        :Brush "/Game/Puzzles/Art/HCA3_UI/DA_HCA3_RelicBrush.DA_HCA3_RelicBrush")
      (Painting|DrawBox :Context Context :Position (Math|Vector2D|MakeVector2D :X (- center (* 170.0 scale)) :Y (* -94.0 scale))
        :Size (Math|Vector2D|MakeVector2D :X (* 340.0 scale) :Y (* 340.0 scale))
        :Brush "/Game/Puzzles/Art/HCA3_UI/DA_HCA3_RoundBrush.DA_HCA3_RoundBrush")
      (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
        (:then
          (bind collected (Utilities|String|BuildString(Integer) :InInt (Class|BPCoopGameState|GetRelicsCollected :self gs) :Suffix " / "))
          (bind total (Utilities|String|BuildString(Integer) :AppendTo collected :InInt (Class|BPCoopGameState|GetRelicsAvailable :self gs)))
          (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) total)
            :Position (Math|Vector2D|MakeVector2D :X (* 96.0 scale) :Y (* 40.0 scale))
            :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize (* 22.0 scale) :Tint "(R=0.93,G=0.82,B=0.55,A=1)")
          (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
          (bind round (Utilities|String|BuildString(Integer) :Prefix "ROUND " :InInt index :Suffix " / 3"))
          (bind cleared (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2")))
          (bind failed (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator3")))
          (bind lobby (Utilities|Enum|Equal(Enum) phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator0")))
          (bind label (select cleared "ROUND CLEARED" (select failed "ROUND FAILED" (select lobby "READY" round))))
          (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) label)
            :Position (Math|Vector2D|MakeVector2D :X (- center (* (select cleared 94.0 (select failed 85.0 74.0)) scale)) :Y (* 61.0 scale))
            :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize (* 20.0 scale) :Tint "(R=0.93,G=0.82,B=0.55,A=1)")
          (if (or cleared failed)
            (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) round)
              :Position (Math|Vector2D|MakeVector2D :X (- center (* 58.0 scale)) :Y (* 153.0 scale))
              :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize (* 16.0 scale) :Tint "(R=0.93,G=0.82,B=0.55,A=1)"))
        ) (:CastFailed)))'''
    viewport_nodes=list(BP.find_node_types(graph,"GetViewportScale"))
    assert len(viewport_nodes)==1,viewport_nodes
    dsl=dsl.replace("UserInterface|Viewport|GetViewportScale",viewport_nodes[0])
    write(widget,"OnPaint",dsl)
    assert unreal.EditorAssetLibrary.save_loaded_asset(widget)
    saved.append(widget.get_path_name())
    (OUT/"hud-build.json").write_text(json.dumps({"passed":True,"saved_assets":saved,
        "widget_compile":str(widget.get_editor_property("status")),"gameplay_state_read_only":True,
        "paint_graph":BP.read_graph_dsl(graph)},indent=2)+"\n",encoding="utf-8")
    unreal.log("HC-A3 presentation assets compiled and saved.")

if __name__ == "__main__":
    run()
