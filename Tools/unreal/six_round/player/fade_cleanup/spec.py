"""PG93 presentation-only helpers. Existing taking graphs are never rebuilt."""

BASELINE = '42762fcaa07a396f06098131dc1184c468556794'
ASSET = '/Game/Player/Taking/BP_TakingDirector'
PACKAGE = 'Content/Player/Taking/BP_TakingDirector.uasset'
MARK = 'PG93_FADE_V1'
MEMBERS = {
    'PresentedTakingController': ('PlayerController', None),
    'PresentedTakingPawn': ('Pawn', None),
    'PresentedTakingStarted': ('float', -1.0),
    'bPresentedTakingFadeOwned': ('bool', False),
}
V = lambda name: f'(Variables|Default|Get{name})'
S = lambda name, value: f'(Variables|Default|Set{name} {value})'

# Execution validity guards precede every object dereference. There is no new
# phase/attempt/ViewTarget rule; the original local-victim fade policy remains.
HELPERS = {
    'CanPresentTakingLocally': {
        'inputs': [('PresentedPawn', 'Pawn'), ('PresentedController', 'PlayerController')],
        'outputs': [('Allowed', 'bool')],
        'body': f'''
 (Utilities|IsValid :InputObject PresentedPawn
  (:"Is Valid" (Utilities|IsValid :InputObject PresentedController
   (:"Is Valid" (Utilities|IsValid :InputObject {V('Victim')}
    (:"Is Valid" (return (and (Pawn|IsLocallyControlled :self PresentedPawn)
     (and (Pawn|IsLocalController :self PresentedController)
      (and (== PresentedPawn {V('Victim')})
       (and (== (Pawn|GetController :self PresentedPawn) PresentedController)
        (>= {V('TakingStarted')} 0.0)))))))
    (:"Is Not Valid" (return false))))
   (:"Is Not Valid" (return false))))
  (:"Is Not Valid" (return false)))''',
    },
    'ClearPresentedTakingFade': {
        'inputs': [], 'outputs': [],
        'body': f'''
 (Utilities|FlowControl|Sequence
  (:then_0 (if {V('PresentedTakingFadeOwned')}
  (Utilities|IsValid :InputObject {V('PresentedTakingController')}
   (:"Is Valid" (if (Pawn|IsLocalController :self {V('PresentedTakingController')})
    (bind camera (Class|PlayerController|GetPlayerCameraManager :self {V('PresentedTakingController')}))
    (Utilities|IsValid :InputObject camera
     (:"Is Valid" (CameraFades|SetManualCameraFade :self camera :InFadeAmount 0.0
      :Color (Utilities|Struct|MakeLinearColor :R 0.0 :G 0.0 :B 0.0 :A 0.0) :bInFadeAudio true))
     (:"Is Not Valid"))))
   (:"Is Not Valid"))))
  (:then_1 {S('PresentedTakingFadeOwned', 'false')}
 {S('PresentedTakingController', '"None"')}
 {S('PresentedTakingPawn', '"None"')}
 {S('PresentedTakingStarted', '-1.0')}))''',
    },
    'ReconcilePresentedTakingFade': {
        'inputs': [], 'outputs': [],
        'body': f'''
 (bind allowed (CallFunction|CanPresentTakingLocally
  :PresentedPawn {V('PresentedTakingPawn')} :PresentedController {V('PresentedTakingController')}))
 (if (and allowed (== {V('PresentedTakingStarted')} {V('TakingStarted')}))
  (bind gs (Game|GetGameState))
  (Utilities|IsValid :InputObject gs
   (:"Is Valid" (bind age (- (GameState|GetServerWorldTimeSeconds :self gs) {V('PresentedTakingStarted')}))
    (if (not (and (>= age 0.35) (< age 1.15))) (CallFunction|ClearPresentedTakingFade)))
   (:"Is Not Valid" (CallFunction|ClearPresentedTakingFade)))
  (else (CallFunction|ClearPresentedTakingFade)))''',
    },
    'ApplyOwnedTakingFade': {
        'inputs': [('PresentedPawn', 'Pawn'), ('PresentedController', 'PlayerController'),
                   ('FadeAmount', 'float'), ('FadeColor', 'LinearColor'), ('FadeAudio', 'bool')],
        'outputs': [],
        'body': f'''
 (bind allowed (CallFunction|CanPresentTakingLocally :PresentedPawn PresentedPawn :PresentedController PresentedController))
 (if allowed
  (if (or (!= {V('PresentedTakingController')} PresentedController)
   (or (!= {V('PresentedTakingPawn')} PresentedPawn) (!= {V('PresentedTakingStarted')} {V('TakingStarted')})))
   (CallFunction|ClearPresentedTakingFade))
  {S('PresentedTakingController', 'PresentedController')}
  {S('PresentedTakingPawn', 'PresentedPawn')}
  {S('PresentedTakingStarted', V('TakingStarted'))}
  (bind camera (Class|PlayerController|GetPlayerCameraManager :self PresentedController))
  (Utilities|IsValid :InputObject camera
   (:"Is Valid" (CameraFades|SetManualCameraFade :self camera :InFadeAmount FadeAmount :Color FadeColor :bInFadeAudio FadeAudio)
    {S('PresentedTakingFadeOwned', '(> FadeAmount 0.0)')})
   (:"Is Not Valid" (CallFunction|ClearPresentedTakingFade)))
  (else (CallFunction|ClearPresentedTakingFade)))''',
    },
}

SPLICES = {
    'PlayTakingVisual': 'ReconcilePresentedTakingFade',
    'FinishTaking': 'ClearPresentedTakingFade',
    'HideTakingPresentation': 'ReconcilePresentedTakingFade',
}
