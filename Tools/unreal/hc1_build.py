"""HC-1 Blueprint authoring. Run only inside the root CoopGame editor.

Core assets must be locked first. Gameplay remains in Blueprint assets; this
script uses the installed Unreal editor APIs to create and wire their graphs.
"""
import json
import unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets import blueprint_dsl
import toolset_registry

CORE = '/Game/Core/'
INPUT = CORE + 'Input/'
I = 'Index_11_91104438409472A6DD374BADC8DC29B1'
P = 'Phase_15_0B3D934F45B47D0BD2F25CA01264D4DF'
A = 'Attempt_12_246832B34F4E147660E8729696BDD44A'
T = 'PhaseEndsAt_13_75E3D82F49994607AFA23C8B57E08350'
R = 'ScalingRow_14_43C74C304230A92B6620E1A520A230C0'


def load(name):
    asset = unreal.load_asset(CORE + name)
    assert asset, name
    return asset


def compile_bp(bp):
    BP.compile_blueprint(bp)
    assert bp.get_editor_property('status') == unreal.BlueprintStatus.BS_UP_TO_DATE, bp.get_path_name()


def var(bp, name, kind):
    if name not in BP.list_variables(bp):
        if isinstance(kind, str):
            BP.add_variable(bp, name, kind)
        else:
            BP.add_object_variable(bp, name, kind)


def fn(bp, name, inputs=(), outputs=()):
    graph = BP.add_function_graph(bp, name)
    for param, kind in inputs:
        if isinstance(kind, str): BP.add_function_param(graph, param, kind, True)
        else: BP.add_object_function_param(graph, param, kind, True)
    for param, kind in outputs:
        if isinstance(kind, str): BP.add_function_param(graph, param, kind, False)
        else: BP.add_object_function_param(graph, param, kind, False)
    return graph


def write(bp, name, text):
    graph = BP.get_graph(bp, name)
    # Use the Python transpiler directly so a failed write raises to the caller.
    # The reflected tool wrapper can log an error and leave the old graph intact.
    with toolset_registry.tool_raising_exceptions():
        blueprint_dsl.Transpiler(graph, BP.create_node, BP.connect_pins,
            BP._get_node_info, BP.set_pin_value, lambda g: BP.find_nodes(g),
            delete_node_fn=BP.delete_node,
            find_node_types_fn=lambda f: BP.find_node_types(graph,f)).transpile(text)
    compile_bp(bp)
    entries = BP.get_node_infos(BP.find_nodes(graph,entry_points_only=True))
    assert any(p.connected_pins for entry in entries for p in entry.output_pins if p.type_id=='Exec'), name


def asset(name, cls, factory):
    return unreal.load_asset(INPUT + name) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, INPUT.rstrip('/'), cls, factory)


def key(name):
    result = unreal.Key()
    assert result.import_text('(KeyName="' + name + '")')
    return result


def scaffold():
    c, pc, gm = load('BP_CoopCharacter'), load('BP_CoopPlayerController'), load('BP_CoopGameMode')
    actors = unreal.Actor.static_class()
    for name in ('FocusedTarget', 'LocalUseTarget', 'ActiveTarget'):
        var(c, name, actors)
    for name in ('InputHeld', 'LocalUseActive', 'ActiveUse', 'InputReady'):
        var(c, name, 'bool')
    for name in ('ActiveStartedAt', 'ActiveHoldSeconds', 'LocalStartedAt', 'LocalHoldSeconds'):
        var(c, name, 'float')
    for name in ('ActiveRoundIndex', 'ActiveRoundAttempt'):
        var(c, name, 'int')
    for name, enum in (('ActiveRoundPhase','E_RoundPhase'),('ActiveMode','E_InteractMode')):
        typ = unreal.BlueprintEditorLibrary.get_basic_type_by_name('byte')
        assert typ.import_text(f'(PinCategory="byte",PinSubCategoryObject="/Game/Core/{enum}.{enum}")')
        if name in BP.list_variables(c): unreal.BlueprintEditorLibrary.change_member_variable_type(c, name, typ)
        else: assert unreal.BlueprintEditorLibrary.add_member_variable(c, name, typ)
    var(c, 'InteractionBlocked', 'bool')
    var(c, 'PromptWidget', unreal.UserWidget.static_class())
    var(c, 'InputController', unreal.PlayerController.static_class())
    var(pc, 'DebugInputAdded', 'bool')
    signatures = {
        'UseAllowed': ([('Target', actors)], [('Allowed', 'bool')]),
        'BeginUse': ([('Target', actors)], []),
        'CancelUse': ([], []), 'ValidateUse': ([], []), 'CompleteTimedUse': ([], []),
        'RefreshFocus': ([], []), 'PressInteract': ([], []), 'ReleaseInteract': ([], []),
        'SetupLocalInput': ([], []), 'RemoveLocalInput': ([], []),
        'ConfirmLocalUse': ([], []), 'EndLocalUse': ([], []),
        'ServerNow': ([], [('Seconds','float')]),
        'SetInteractionBlocked': ([('Blocked','bool')], []),
    }
    for name, (ins, outs) in signatures.items(): fn(c, name, ins, outs)
    for name in ('HostStartRound', 'HostClearRound', 'HostFailRound', 'HostCompleteMap'): fn(pc, name)
    fn(gm, 'CancelAllUses')
    for name in ('Server_InteractEnd', 'Client_UseStarted', 'Client_UseEnded'):
        event = BP.add_event(c, name)
        BP.set_node_position(event, unreal.IntPoint(200, {'Server_InteractEnd':300, 'Client_UseStarted':600, 'Client_UseEnded':900}[name]))
    for bp in (c, pc, gm): compile_bp(bp)

    coop = unreal.load_asset(INPUT + 'IMC_Coop') or unreal.EditorAssetLibrary.duplicate_asset('/Game/Input/IMC_Default', INPUT + 'IMC_Coop')
    mouse = unreal.load_asset(INPUT + 'IMC_CoopMouseLook') or unreal.EditorAssetLibrary.duplicate_asset('/Game/Input/IMC_MouseLook', INPUT + 'IMC_CoopMouseLook')
    debug = asset('IMC_Debug', unreal.InputMappingContext, unreal.InputMappingContext_Factory())
    actions = {}
    controls = {
        'IA_Interact': ('E','Gamepad_FaceButton_Bottom'),
        'IA_Drop': ('G','Gamepad_FaceButton_Right'),
        'IA_ToggleView': ('V','Gamepad_RightThumbstick'),
        'IA_Headlamp': ('F','Gamepad_DPad_Up'),
        'IA_DebugStart': ('F1',), 'IA_DebugClear': ('F2',),
        'IA_DebugFail': ('F3',), 'IA_DebugComplete': ('F4',),
    }
    # A/Cross is Interact per the shared contract; move gamepad Jump to X/Square.
    jump = unreal.load_asset('/Game/Input/Actions/IA_Jump')
    if not jump:
        jump = next(m.action for m in coop.get_editor_property('mappings') if m.action.get_name() == 'IA_Jump')
    coop.unmap_key(jump, key('Gamepad_FaceButton_Bottom'))
    if not any(m.action == jump and m.key == key('Gamepad_FaceButton_Left') for m in coop.get_editor_property('mappings')):
        coop.map_key(jump, key('Gamepad_FaceButton_Left'))
    for name, keys in controls.items():
        action = asset(name, unreal.InputAction, unreal.InputAction_Factory())
        action.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
        context = debug if name.startswith('IA_Debug') else coop
        context.unmap_all_keys_from_action(action)
        for k in keys: context.map_key(action, key(k))
        actions[name] = action
    for item in (coop, mouse, debug, *actions.values()):
        assert unreal.EditorAssetLibrary.save_loaded_asset(item, only_if_is_dirty=False)
    return {'input_assets': [a.get_path_name() for a in (coop, mouse, debug, *actions.values())], 'core_scaffolded': True}


def round_logic():
    gm = load('BP_CoopGameMode')
    write(gm, 'CancelAllUses', '''(fn CancelAllUses ()
      (if (Networking|HasAuthority)
        (for pawn (Actor|GetAllActorsOfClass :ActorClass "/Game/Core/BP_CoopCharacter.BP_CoopCharacter_C")
          (bind c (Utilities|Casting|CastToBP_CoopCharacter :Object pawn)
            (:then (Class|BPCoopCharacter|CancelUse :self c)) (:CastFailed)))))''')
    playing = '(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")'
    text = f'''(fn StartRound (Index)
      (if (and (Networking|HasAuthority) (> Index 0))
        (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
          (:then
            (bind (oldIndex phase oldAttempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
            (CallFunction|CancelAllUses)
            (Class|BPCoopGameState|SetRoundState :self gs :RoundState (Utilities|Struct|MakeSRoundState
              :{I} Index :{P} {playing}
              :{A} (select (== Index oldIndex) (+ oldAttempt 1) 1)
              :{T} 0.0 :{R} row))) (:CastFailed))))'''
    write(gm, 'StartRound', text)
    for name, enum in (('ClearRound','NewEnumerator2'), ('FailRound','NewEnumerator3'), ('CompleteMap','NewEnumerator4')):
        write(gm, name, f'''(fn {name} ()
          (if (Networking|HasAuthority)
            (CallFunction|CancelAllUses)
            (CallFunction|SetRoundPhase :Phase (Utilities|Enum|LiteralenumE_RoundPhase :Enum "{enum}"))))''')
    return {'round_functions': ['StartRound','ClearRound','FailRound','CompleteMap'], 'only_round_state_changes': True}


def interaction_logic():
    c = load('BP_CoopCharacter')
    write(c, 'ServerNow', '''(fn ServerNow ()
      (bind gs (Game|GetGameState))
      (Utilities|IsValid :InputObject gs
        (:"Is Valid" (return (GameState|GetServerWorldTimeSeconds :self gs)))
        (:"Is Not Valid" (return 0.0))))''')
    write(c, 'UseAllowed', '''(fn UseAllowed (Target)
      (Utilities|IsValid :InputObject Target
        (:"Is Valid"
          (if (and (and (not (Variables|Default|GetInteractionBlocked))
                   (not (Actor|ActorHasTag :Tag "Downed")))
                   (<= (Transformation|GetDistanceTo :OtherActor Target) 400.0))
            (bind can (Class|BPIInteractable|CanInteract(Message) :self Target :Instigator self))
            (if can
              (bind (eye rotation) (Actor|GetActorEyesViewPoint))
              (bind (hit blocked) (Collision|LineTraceByChannel :Start eye :End (Transformation|GetActorLocation :self Target)
                :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
              (bind (blocking overlap time distance location impact normal impactNormal material hitActor component bone myBone item element face traceStart traceEnd)
                (Collision|BreakHitResult :Hit hit))
              (return (or (not blocked) (== hitActor Target)))
              (else (return false)))
            (else (return false))))
        (:"Is Not Valid" (return false))))''')
    write(c, 'EndLocalUse', '''(fn EndLocalUse ()
      (Variables|Default|SetLocalUseActive false))''')
    write(c, 'ConfirmLocalUse', '''(fn ConfirmLocalUse ()
      (if (and (Pawn|IsLocallyControlled) (Variables|Default|GetInputHeld))
        (Utilities|IsValid :InputObject (Variables|Default|GetLocalUseTarget)
          (:"Is Valid"
            (bind (prompt hold mode) (Class|BPIInteractable|GetInteractInfo(Message) :self (Variables|Default|GetLocalUseTarget) :Instigator self))
            (Variables|Default|SetLocalHoldSeconds (select (Utilities|Enum|Equal(Enum) mode (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator1")) hold 0.0))
            (Variables|Default|SetLocalStartedAt (CallFunction|ServerNow))
            (Variables|Default|SetLocalUseActive true))
          (:"Is Not Valid"))))''')
    write(c, 'CancelUse', '''(fn CancelUse ()
      (if (Networking|HasAuthority)
        (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "CompleteTimedUse")
        (if (Variables|Default|GetActiveUse)
          (Variables|Default|SetActiveUse false)
          (Utilities|IsValid :InputObject (Variables|Default|GetActiveTarget)
            (:"Is Valid"
              (if (Utilities|Enum|Equal(Enum) (Variables|Default|GetActiveMode) (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator2"))
                (Class|BPIInteractable|InteractEnd(Message) :self (Variables|Default|GetActiveTarget) :Instigator self)))
            (:"Is Not Valid")))
        (Variables|Default|SetActiveTarget "None")
        (CallFunction|ClientUseEnded)))''')
    write(c, 'SetInteractionBlocked', '''(fn SetInteractionBlocked (Blocked)
      (if (Networking|HasAuthority)
        (Variables|Default|SetInteractionBlocked Blocked)
        (if Blocked (CallFunction|CancelUse))))''')
    write(c, 'BeginUse', f'''(fn BeginUse (Target)
      (if (Networking|HasAuthority)
        (CallFunction|CancelUse)
        (if (CallFunction|UseAllowed :Target Target)
          (bind (prompt hold mode) (Class|BPIInteractable|GetInteractInfo(Message) :self Target :Instigator self))
          (if (Utilities|Enum|Equal(Enum) mode (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator0"))
            (Class|BPIInteractable|Interact(Message) :self Target :Instigator self)
            (else
              (Variables|Default|SetActiveTarget Target)
              (Variables|Default|SetActiveMode mode)
              (Variables|Default|SetActiveHoldSeconds (select (< hold 0.01) 0.01 hold))
              (Variables|Default|SetActiveStartedAt (CallFunction|ServerNow))
              (Variables|Default|SetActiveUse true)
              (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
                (:then
                  (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
                  (Variables|Default|SetActiveRoundIndex index)
                  (Variables|Default|SetActiveRoundAttempt attempt)
                  (Variables|Default|SetActiveRoundPhase phase)
                  (CallFunction|ClientUseStarted)
                  (if (Utilities|Enum|Equal(Enum) mode (Utilities|Enum|LiteralenumE_InteractMode :Enum "NewEnumerator1"))
                    (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "CompleteTimedUse" :Time (Variables|Default|GetActiveHoldSeconds) :bLooping false)
                    (else (Class|BPIInteractable|InteractBegin(Message) :self Target :Instigator self))))
                (:CastFailed (CallFunction|CancelUse))))))))''')
    write(c, 'ValidateUse', '''(fn ValidateUse ()
      (if (and (Networking|HasAuthority) (Variables|Default|GetActiveUse))
        (if (CallFunction|UseAllowed :Target (Variables|Default|GetActiveTarget))
          (bind gs (Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))
            (:then
              (bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))
              (if (or (or (!= index (Variables|Default|GetActiveRoundIndex))
                      (!= attempt (Variables|Default|GetActiveRoundAttempt)))
                      (Utilities|Enum|NotEqual(Enum) phase (Variables|Default|GetActiveRoundPhase)))
                (CallFunction|CancelUse)))
            (:CastFailed (CallFunction|CancelUse)))
          (else (CallFunction|CancelUse)))))''')
    write(c, 'CompleteTimedUse', '''(fn CompleteTimedUse ()
      (if (Networking|HasAuthority)
        (CallFunction|ValidateUse)
        (if (Variables|Default|GetActiveUse)
          (if (>= (- (CallFunction|ServerNow) (Variables|Default|GetActiveStartedAt)) (Variables|Default|GetActiveHoldSeconds))
            (Class|BPIInteractable|Interact(Message) :self (Variables|Default|GetActiveTarget) :Instigator self)
            (CallFunction|CancelUse)))))''')
    write(c, 'PressInteract', '''(fn PressInteract ()
      (if (Pawn|IsLocallyControlled)
        (Variables|Default|SetInputHeld true)
        (Variables|Default|SetLocalUseTarget (Variables|Default|GetFocusedTarget))
        (CallFunction|ServerInteractBegin :Target (Variables|Default|GetFocusedTarget))))''')
    write(c, 'ReleaseInteract', '''(fn ReleaseInteract ()
      (if (Pawn|IsLocallyControlled)
        (Variables|Default|SetInputHeld false)
        (CallFunction|EndLocalUse)
        (CallFunction|ServerInteractEnd)))''')
    return {'interaction_functions_written':True}


def prompt_logic():
    w = unreal.load_asset('/Game/Puzzles/UI/WBP_InteractPrompt')
    assert w
    # The designer-created root supplies layout; the Blueprint paint override
    # keeps the prompt/progress presentation independent of editor-only fields.
    tree = unreal.find_object(w, 'WidgetTree')
    root = next(obj for obj in unreal.ObjectIterator() if obj.get_outer() == tree and obj.get_class().get_name() == 'VerticalBox')
    for name in ('PromptText', 'HoldProgress'):
        draft_control = unreal.find_object(tree, name)
        if draft_control: root.remove_child(draft_control)
    for name, kind in (('Prompt','text'),('Progress','float'),('ShowPrompt','bool'),('ShowProgress','bool')):
        var(w, name, kind)
    fn(w, 'UpdatePrompt', [('Text','text'),('Percent','float'),('Visible','bool'),('Timed','bool')])
    BP.add_function_graph(w, 'OnPaint')
    compile_bp(w)
    write(w, 'UpdatePrompt', '''(fn UpdatePrompt (Text Percent Visible Timed)
      (Variables|Default|SetPrompt Text)
      (Variables|Default|SetProgress Percent)
      (Variables|Default|SetShowPrompt Visible)
      (Variables|Default|SetShowProgress Timed))''')
    write(w, 'OnPaint', '''(fn OnPaint (Context)
      (if (Variables|Default|GetShowPrompt)
        (Painting|DrawLine :Context Context :PositionA "(X=0,Y=32)" :PositionB "(X=310,Y=32)" :Thickness 62 :Tint "(R=0.015,G=0.018,B=0.025,A=0.9)")
        (Painting|DrawText :Context Context :Text (Utilities|Text|ToText(String) "E / A") :Position "(X=12,Y=6)" :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize 14 :Tint "(R=0.7,G=0.85,B=1,A=1)")
        (Painting|DrawText :Context Context :Text (Variables|Default|GetPrompt) :Position "(X=12,Y=25)" :Font "/Engine/EngineFonts/Roboto.Roboto" :FontSize 18)
        (if (Variables|Default|GetShowProgress)
          (Painting|DrawLine :Context Context :PositionA "(X=12,Y=58)" :PositionB "(X=298,Y=58)" :Thickness 5 :Tint "(R=0.18,G=0.2,B=0.25,A=1)")
          (Painting|DrawLine :Context Context :PositionA "(X=12,Y=58)"
            :PositionB (Math|Vector2D|MakeVector2D :X (+ 12.0 (* 286.0 (Variables|Default|GetProgress))) :Y 58.0)
            :Thickness 5 :Tint "(R=0.3,G=0.75,B=1,A=1)"))))''')
    return {'prompt_blueprint_compiled':True}


def local_input_and_focus():
    c = load('BP_CoopCharacter')
    fn(c, 'ClearOwnedInputMaps')
    fn(c, 'ClearOwnedPrompt')
    compile_bp(c)
    write(c, 'ClearOwnedInputMaps', '''(fn ClearOwnedInputMaps ()
      (if (Variables|Default|GetInputReady)
      (Utilities|IsValid :InputObject (Variables|Default|GetInputController)
        (:"Is Valid"
          (bind sub (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController (Variables|Default|GetInputController)))
          (Utilities|IsValid :InputObject sub
            (:"Is Valid"
              (Input|RemoveMappingContext :self sub :MappingContext "/Game/Core/Input/IMC_Coop.IMC_Coop")
              (Input|RemoveMappingContext :self sub :MappingContext "/Game/Core/Input/IMC_CoopMouseLook.IMC_CoopMouseLook")) (:"Is Not Valid")))
        (:"Is Not Valid"))))''')
    write(c, 'ClearOwnedPrompt', '''(fn ClearOwnedPrompt ()
      (Utilities|IsValid :InputObject (Variables|Default|GetPromptWidget)
        (:"Is Valid" (Widget|RemovefromParent :self (Variables|Default|GetPromptWidget))) (:"Is Not Valid")))''')
    write(c, 'RemoveLocalInput', '''(fn RemoveLocalInput ()
      (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "RefreshFocus")
      (CallFunction|ClearOwnedInputMaps)
      (CallFunction|ClearOwnedPrompt)
      (Variables|Default|SetPromptWidget "None")
      (Variables|Default|SetInputReady false)
      (Variables|Default|SetInputHeld false)
      (Variables|Default|SetLocalUseActive false))''')
    write(c, 'SetupLocalInput', '''(fn SetupLocalInput ()
      (if (and (Pawn|IsLocallyControlled) (not (Variables|Default|GetInputReady)))
        (bind pc (Utilities|Casting|CastToPlayerController :Object (Pawn|GetController))
          (:then
            (bind sub (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController pc))
            (Utilities|IsValid :InputObject sub
              (:"Is Valid"
                (Variables|Default|SetInputController pc)
                (Input|AddMappingContext :self sub :MappingContext "/Game/Core/Input/IMC_Coop.IMC_Coop" :Priority 0)
                (Input|AddMappingContext :self sub :MappingContext "/Game/Core/Input/IMC_CoopMouseLook.IMC_CoopMouseLook" :Priority 0)
                (bind widget (UserInterface|CreateWidget :Class "/Game/Puzzles/UI/WBP_InteractPrompt.WBP_InteractPrompt_C" :OwningPlayer pc))
                (Variables|Default|SetPromptWidget widget)
                (UserInterface|Viewport|AddtoPlayerScreen :self widget)
                (UserInterface|Viewport|SetDesiredSizeinViewport :self widget :Size "(X=310,Y=70)")
                (UserInterface|Viewport|SetAnchorsinViewport :self widget :Anchors "(Minimum=(X=0.5,Y=0.82),Maximum=(X=0.5,Y=0.82))")
                (UserInterface|Viewport|SetAlignmentinViewport :self widget :Alignment "(X=0.5,Y=0.5)")
                (Variables|Default|SetInputReady true)
                (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "RefreshFocus" :Time 0.1 :bLooping true))
              (:"Is Not Valid"))) (:CastFailed))))''')
    write(c, 'RefreshFocus', '''(fn RefreshFocus ()
      (if (and (Pawn|IsLocallyControlled) (Variables|Default|GetInputReady))
        (Variables|Default|SetFocusedTarget "None")
        (bind camera (Variables|Camera|GetFollowCamera))
        (bind start (Transformation|GetWorldLocation :self camera))
        (bind direction (Math|Vector|GetForwardVector :InRot (Transformation|GetWorldRotation :self camera)))
        (bind (hit found) (Collision|SphereTraceByChannel :Start start :End (+ start (* direction 800.0)) :Radius 18.0
          :TraceChannel "TraceTypeQuery1" :bIgnoreSelf true :DrawDebugType "None"))
        (bind (blocking overlap time distance location impact normal impactNormal material target component bone myBone item element face traceStart traceEnd)
          (Collision|BreakHitResult :Hit hit))
        (if (CallFunction|UseAllowed :Target target) (Variables|Default|SetFocusedTarget target))
        (bind displayTarget (select (Variables|Default|GetLocalUseActive) (Variables|Default|GetLocalUseTarget) (Variables|Default|GetFocusedTarget)))
        (bind widget (Utilities|Casting|CastToWBP_InteractPrompt :Object (Variables|Default|GetPromptWidget))
          (:then
            (Utilities|IsValid :InputObject displayTarget
              (:"Is Valid"
                (bind (prompt hold mode) (Class|BPIInteractable|GetInteractInfo(Message) :self displayTarget :Instigator self))
                (bind timed (and (Variables|Default|GetLocalUseActive) (> (Variables|Default|GetLocalHoldSeconds) 0.0)))
                (bind progress (select timed (/ (- (CallFunction|ServerNow) (Variables|Default|GetLocalStartedAt)) (select timed (Variables|Default|GetLocalHoldSeconds) 1.0)) 0.0))
                (Class|WBPInteractPrompt|UpdatePrompt :self widget :Text prompt :Percent (select (> progress 1.0) 1.0 progress) :Visible true :Timed timed))
              (:"Is Not Valid" (Class|WBPInteractPrompt|UpdatePrompt :self widget :Visible false :Percent 0.0 :Timed false))))
          (:CastFailed))))''')
    return {'per_pawn_input_and_focus_compiled':True}


def connect_action(bp, action, handlers):
    graph = BP.get_graph(bp, 'EventGraph')
    matches = [n for n in BP.find_nodes(graph) if BP.get_node_infos([n])[0].type_id == 'AddEvent|EnhancedInputAction'+action]
    event = matches[0] if matches else BP.create_node(graph, 'Input|EnhancedActionEvents|'+action, unreal.IntPoint(0,1800))
    for output, name in handlers.items():
        call = BP.create_node(graph, 'CallFunction|'+name, unreal.IntPoint(400,1800))
        assert event.find_output_pin(output).try_create_connection(call.find_execute_pin()), (action, output)
    compile_bp(bp)


def event_and_debug_logic():
    c, pc = load('BP_CoopCharacter'), load('BP_CoopPlayerController')
    for name in ('HC1BeginPlay','HC1ControllerChanged','HC1EndPlay'): fn(c, name)
    write(c, 'HC1BeginPlay', '''(fn HC1BeginPlay ()
      (CallFunction|SetupLocalInput)
      (if (Networking|HasAuthority)
        (Utilities|Time|SetTimerbyFunctionName :Object self :FunctionName "ValidateUse" :Time 0.2 :bLooping true)))''')
    write(c, 'HC1ControllerChanged', '''(fn HC1ControllerChanged ()
      (CallFunction|RemoveLocalInput)
      (CallFunction|SetupLocalInput)
      (if (Networking|HasAuthority) (CallFunction|CancelUse)))''')
    write(c, 'HC1EndPlay', '''(fn HC1EndPlay ()
      (if (Networking|HasAuthority)
        (CallFunction|CancelUse)
        (Utilities|Time|ClearTimerbyFunctionName :Object self :FunctionName "ValidateUse"))
      (CallFunction|RemoveLocalInput))''')
    # Append only to audited empty event chains; never rewrite an EventGraph.
    for event_name, handler in (
        ('ReceiveBeginPlay','HC1BeginPlay'), ('ReceiveControllerChanged','HC1ControllerChanged'),
        ('ReceiveEndPlay','HC1EndPlay'), ('Server_InteractBegin','BeginUse'),
        ('Server_InteractEnd','CancelUse'), ('Client_UseStarted','ConfirmLocalUse'), ('Client_UseEnded','EndLocalUse')):
        event = BP.add_event(c, event_name)
        then = event.find_then_pin()
        links = list(then.list_connected_pins())
        if links:
            assert len(links)==1 and handler in BP.get_node_infos([links[0].get_owning_node()])[0].type_id, event_name
            continue
        call = BP.create_node(BP.get_graph(c,'EventGraph'), 'CallFunction|'+handler, unreal.IntPoint(500,2000))
        assert then.try_create_connection(call.find_execute_pin())
        if event_name=='Server_InteractBegin':
            assert event.find_output_pin('Target').try_create_connection(call.find_input_pin('Target'))
    compile_bp(c)
    connect_action(c, 'IA_Interact', {'Started':'PressInteract', 'Completed':'ReleaseInteract', 'Canceled':'ReleaseInteract'})
    for name, function in (('HostStartRound','StartRound'), ('HostClearRound','ClearRound'), ('HostFailRound','FailRound'), ('HostCompleteMap','CompleteMap')):
        arg = ':Index 1' if function == 'StartRound' else ''
        write(pc, name, f'''(fn {name} ()
          (if (and (and (Networking|HasAuthority) (Pawn|IsLocalPlayerController)) (Game|Player|IsPrimaryPlayer))
            (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
              (:then (Class|BPCoopGameMode|{function} :self gm {arg})) (:CastFailed))))''')
    # The template controller installs its gameplay context at BeginPlay. This
    # override gives that responsibility to each pawn's controller-change hook.
    fn(pc, 'HC1SetupDebugInput')
    write(pc, 'HC1SetupDebugInput', '''(fn HC1SetupDebugInput ()
      (if (and (and (Networking|HasAuthority) (Pawn|IsLocalPlayerController)) (and (Game|Player|IsPrimaryPlayer) (not (Variables|Default|GetDebugInputAdded))))
        (bind sub (PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem :PlayerController self))
        (Utilities|IsValid :InputObject sub
          (:"Is Valid"
            (Input|AddMappingContext :self sub :MappingContext "/Game/Core/Input/IMC_Debug.IMC_Debug" :Priority 100)
            (Variables|Default|SetDebugInputAdded true)) (:"Is Not Valid"))))''')
    event = BP.add_event(pc,'ReceiveBeginPlay')
    then = event.find_then_pin()
    links = list(then.list_connected_pins())
    if links and 'HC1SetupDebugInput' not in BP.get_node_infos([links[0].get_owning_node()])[0].type_id:
        # The read-only audit proved this sole link invokes only the template's
        # input/touch setup. HC-1 explicitly moves those mappings to the pawn.
        assert len(links)==1
        assert BP.get_node_infos([links[0].get_owning_node()])[0].type_id=='|Parent:BeginPlay'
        then.break_single_pin_link(links[0])
        links=[]
    if not links:
        call = BP.create_node(BP.get_graph(pc,'EventGraph'),'CallFunction|HC1SetupDebugInput',unreal.IntPoint(400,0))
        assert then.try_create_connection(call.find_execute_pin())
    compile_bp(pc)
    for action, function in (('IA_DebugStart','HostStartRound'), ('IA_DebugClear','HostClearRound'), ('IA_DebugFail','HostFailRound'), ('IA_DebugComplete','HostCompleteMap')):
        connect_action(pc, action, {'Started':function})
    return {'character_events_wired':True,'host_debug_keys_wired':True}


def test_actor_logic():
    t = unreal.load_asset('/Game/Puzzles/Test/BP_TestInteractable')
    assert t
    write(t, 'GetInteractInfo', '''(fn GetInteractInfo (Instigator)
      (return (Variables|Default|GetPrompt) (Variables|Default|GetHoldSeconds) (Variables|Default|GetMode)))''')
    write(t, 'CanInteract', '''(fn CanInteract (Instigator)
      (return (Variables|Default|GetInteractionEnabled)))''')
    for name in ('Interact','InteractBegin','InteractEnd'):
        BP.add_event(t, name)
    compile_bp(t)
    graph = BP.get_graph(t,'EventGraph')
    events = {str(e.name):BP.add_event(t,str(e.name)) for e in BP.list_events(t) if str(e.name) in ('Interact','InteractBegin','InteractEnd')}
    # New test-actor event chains; the Core and template graphs are not involved.
    for event, handler in (('Interact','RecordInstant'),('InteractBegin','RecordBegin'),('InteractEnd','RecordEnd')):
        fn(t,handler)
    fn(t,'TestStartRound')
    write(t,'TestStartRound','''(fn TestStartRound ()
      (if (Networking|HasAuthority)
        (bind gm (Utilities|Casting|CastToBP_CoopGameMode :Object (Game|GetGameMode))
          (:then (Class|BPCoopGameMode|StartRound :self gm :Index 1)) (:CastFailed))))''')
    write(t,'RecordInstant','''(fn RecordInstant ()
      (if (Networking|HasAuthority)
        (Variables|Default|SetInstantCount (+ (Variables|Default|GetInstantCount) 1))))''')
    write(t,'RecordBegin','''(fn RecordBegin ()
      (if (Networking|HasAuthority)
        (Variables|Default|SetBeginCount (+ (Variables|Default|GetBeginCount) 1))
        (Variables|Default|SetActiveUsers (+ (Variables|Default|GetActiveUsers) 1))))''')
    write(t,'RecordEnd','''(fn RecordEnd ()
      (if (Networking|HasAuthority)
        (Variables|Default|SetEndCount (+ (Variables|Default|GetEndCount) 1))
        (Variables|Default|SetActiveUsers (select (> (Variables|Default|GetActiveUsers) 0) (- (Variables|Default|GetActiveUsers) 1) 0))))''')
    for event, handler in (('Interact','RecordInstant'),('InteractBegin','RecordBegin'),('InteractEnd','RecordEnd')):
        e = BP.add_event(t,event)
        if not e.find_then_pin().list_connected_pins():
            call = BP.create_node(graph,'CallFunction|'+handler,unreal.IntPoint(400,0))
            assert e.find_then_pin().try_create_connection(call.find_execute_pin())
    compile_bp(t)
    cdo=unreal.get_default_object(t.generated_class())
    cdo.set_editor_property('replicates',True)
    cdo.set_editor_property('InteractionEnabled',True)
    cdo.set_editor_property('HoldSeconds',2.0)
    cdo.set_editor_property('Prompt','Use test object')
    cdo.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    cdo.static_mesh_component.set_collision_profile_name('BlockAll')
    return {'test_actor_interface_implemented':True}


def save_assets():
    paths = [CORE+n for n in ('BP_CoopCharacter','BP_CoopPlayerController','BP_CoopGameMode')]
    paths += ['/Game/Puzzles/Test/BP_TestInteractable','/Game/Puzzles/UI/WBP_InteractPrompt']
    for path in paths:
        bp=unreal.load_asset(path)
        compile_bp(bp)
        for graph in BP.list_graphs(bp): BP.arrange_nodes(BP.find_nodes(graph))
        assert unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
    return {'saved_blueprints':paths}


def create_test_level():
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    path='/Game/Puzzles/Test/L_HC_Test'
    assert not unreal.EditorAssetLibrary.does_asset_exist(path), 'Test level already exists; preserve it.'
    assert editor.new_level(path)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(500,0,-25))
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(unreal.Vector(30,30,0.5))
    floor.set_actor_label('HC1_TestFloor')
    sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,500))
    sun.set_actor_rotation(unreal.Rotator(pitch=-50,yaw=-20,roll=0),False)
    sun.get_component_by_class(unreal.DirectionalLightComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
    actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
    sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500))
    sky.get_component_by_class(unreal.SkyLightComponent).set_mobility(unreal.ComponentMobility.MOVABLE)
    cls=unreal.load_asset('/Game/Puzzles/Test/BP_TestInteractable').generated_class()
    enum=type(unreal.get_default_object(cls).get_editor_property('Mode'))
    for lane,y in enumerate((-600,-200,200,600)):
        actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(0,y,100))
        for mode,name in enumerate(('Instant','Timed','Continuous')):
            actor=actors.spawn_actor_from_class(cls,unreal.Vector(300+mode*350,y,100))
            actor.set_actor_label(f'HC1_{name}_{lane}')
            actor.set_editor_property('Mode',enum.cast(mode))
            actor.set_editor_property('Prompt',name+' interaction test')
            actor.set_editor_property('HoldSeconds',2.0)
            actor.set_editor_property('tags',[unreal.Name('HC1_'+name),unreal.Name('HC1Lane_'+str(lane))])
    assert editor.save_current_level()
    return {'test_level':path,'test_actors':12,'player_starts':4}


def place_main_tests():
    editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert editor.load_level('/Game/Maps/L_Site01')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    stream=unreal.GameplayStatics.get_streaming_level(world,'L_Site01_HC')
    unreal.EditorLevelUtils.make_level_current(stream)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cls=unreal.load_asset('/Game/Puzzles/Test/BP_TestInteractable').generated_class()
    enum=type(unreal.get_default_object(cls).get_editor_property('Mode'))
    records=[]
    for mode,(name,y,prompt) in enumerate((('Instant',-600,'Activate marker'),('Timed',0,'Charge marker'),('Continuous',600,'Hold marker active'))):
        tag='HC1Main'+name
        existing=[a for a in actors.get_all_level_actors() if tag in [str(t) for t in a.tags]]
        actor=existing[0] if existing else actors.spawn_actor_from_class(cls,unreal.Vector(-850,y,100))
        assert actor.get_level().get_outermost().get_name()=='/Game/Puzzles/L_Site01_HC'
        actor.set_actor_label('HC1_'+name)
        actor.set_folder_path('HC1InteractionTests')
        actor.set_editor_property('tags',[unreal.Name(tag)])
        actor.set_editor_property('Mode',enum.cast(mode))
        actor.set_editor_property('Prompt',prompt)
        actor.set_editor_property('HoldSeconds',2.0)
        records.append(actor.get_actor_label())
    assert unreal.EditorLoadingAndSavingUtils.save_packages([stream.get_loaded_level().get_outermost()],False)
    return {'main_hc_fixtures':records}
