#include "CoopInput.h"

#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputCoreTypes.h"

UInputAction* UCoopInput::MakeAction(const TCHAR* Name, EInputActionValueType Type)
{
	UInputAction* Action = NewObject<UInputAction>(this, FName(Name));
	Action->ValueType = Type;
	return Action;
}

void UCoopInput::Bind(UInputMappingContext* Context, UInputAction* Action, const FKey& Key,
	bool bSwizzleYX, bool bNegate, bool bDeadZone)
{
	FEnhancedActionKeyMapping& Mapping = Context->MapKey(Action, Key);

	if (bDeadZone)
	{
		Mapping.Modifiers.Add(NewObject<UInputModifierDeadZone>(Context));
	}
	if (bSwizzleYX)
	{
		UInputModifierSwizzleAxis* Swizzle = NewObject<UInputModifierSwizzleAxis>(Context);
		Swizzle->Order = EInputAxisSwizzle::YXZ;
		Mapping.Modifiers.Add(Swizzle);
	}
	if (bNegate)
	{
		Mapping.Modifiers.Add(NewObject<UInputModifierNegate>(Context));
	}
}

void UCoopInput::Build()
{
	// ---------- Actions ----------
	Move      = MakeAction(TEXT("IA_Move"),      EInputActionValueType::Axis2D);
	LookStick = MakeAction(TEXT("IA_LookStick"), EInputActionValueType::Axis2D);
	LookMouse = MakeAction(TEXT("IA_LookMouse"), EInputActionValueType::Axis2D);
	Jump      = MakeAction(TEXT("IA_Jump"),      EInputActionValueType::Boolean);
	Brace     = MakeAction(TEXT("IA_Brace"),     EInputActionValueType::Boolean);
	Reel      = MakeAction(TEXT("IA_Reel"),      EInputActionValueType::Boolean);
	CameraToggle = MakeAction(TEXT("IA_CameraToggle"), EInputActionValueType::Boolean);

	StationNext   = MakeAction(TEXT("IA_StationNext"),   EInputActionValueType::Boolean);
	StationPrev   = MakeAction(TEXT("IA_StationPrev"),   EInputActionValueType::Boolean);
	StationReset  = MakeAction(TEXT("IA_StationReset"),  EInputActionValueType::Boolean);
	StationSelect = MakeAction(TEXT("IA_StationSelect"), EInputActionValueType::Axis1D);

	P2CameraToggle = MakeAction(TEXT("IA_P2CameraToggle"), EInputActionValueType::Boolean);
	P2Move  = MakeAction(TEXT("IA_P2Move"),  EInputActionValueType::Axis2D);
	P2Turn  = MakeAction(TEXT("IA_P2Turn"),  EInputActionValueType::Axis1D);
	P2Jump  = MakeAction(TEXT("IA_P2Jump"),  EInputActionValueType::Boolean);
	P2Brace = MakeAction(TEXT("IA_P2Brace"), EInputActionValueType::Boolean);
	P2Reel  = MakeAction(TEXT("IA_P2Reel"),  EInputActionValueType::Boolean);

	// ---------- Player context: keyboard/mouse + gamepad ----------
	PlayerContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Player"));

	// Move: WASD + left stick
	Bind(PlayerContext, Move, EKeys::W, /*Swizzle*/ true);
	Bind(PlayerContext, Move, EKeys::S, /*Swizzle*/ true, /*Negate*/ true);
	Bind(PlayerContext, Move, EKeys::D);
	Bind(PlayerContext, Move, EKeys::A, false, /*Negate*/ true);
	Bind(PlayerContext, Move, EKeys::Gamepad_Left2D, false, false, /*DeadZone*/ true);

	// Look: mouse + right stick
	Bind(PlayerContext, LookMouse, EKeys::Mouse2D);
	Bind(PlayerContext, LookStick, EKeys::Gamepad_Right2D, false, false, /*DeadZone*/ true);

	// Jump: Space / bottom face button (A on Xbox, Cross on PlayStation)
	Bind(PlayerContext, Jump, EKeys::SpaceBar);
	Bind(PlayerContext, Jump, EKeys::Gamepad_FaceButton_Bottom);

	// Brace: Left Shift / left trigger
	Bind(PlayerContext, Brace, EKeys::LeftShift);
	Bind(PlayerContext, Brace, EKeys::Gamepad_LeftTrigger);

	// Reel: R / right trigger
	Bind(PlayerContext, Reel, EKeys::R);
	Bind(PlayerContext, Reel, EKeys::Gamepad_RightTrigger);

	// Camera toggle (first person / over-the-shoulder): V / D-pad up
	Bind(PlayerContext, CameraToggle, EKeys::V);
	Bind(PlayerContext, CameraToggle, EKeys::Gamepad_DPad_Up);

	// Playground travel: D-pad right/left = next/previous station, D-pad down = reset to this station
	Bind(PlayerContext, StationNext, EKeys::Gamepad_DPad_Right);
	Bind(PlayerContext, StationPrev, EKeys::Gamepad_DPad_Left);
	Bind(PlayerContext, StationReset, EKeys::Gamepad_DPad_Down);

	// Number keys 1-9 jump straight to a station. The Scalar modifier turns each key's
	// value into its number, so one action covers all nine keys.
	const FKey NumberKeys[] = { EKeys::One, EKeys::Two, EKeys::Three, EKeys::Four, EKeys::Five, EKeys::Six, EKeys::Seven, EKeys::Eight, EKeys::Nine };
	int32 StationNumber = 1;
	for (const FKey& NumberKey : NumberKeys)
	{
		FEnhancedActionKeyMapping& Mapping = PlayerContext->MapKey(StationSelect, NumberKey);
		UInputModifierScalar* Scalar = NewObject<UInputModifierScalar>(PlayerContext);
		Scalar->Scalar = FVector(static_cast<double>(StationNumber), 1.0, 1.0);
		Mapping.Modifiers.Add(Scalar);
		++StationNumber;
	}

	// ---------- Shared keyboard: Player 1's keyboard drives Player 2 ----------
	SharedKeyboardContext = NewObject<UInputMappingContext>(this, TEXT("IMC_SharedKeyboard"));

	// Move: arrow keys
	Bind(SharedKeyboardContext, P2Move, EKeys::Up, /*Swizzle*/ true);
	Bind(SharedKeyboardContext, P2Move, EKeys::Down, /*Swizzle*/ true, /*Negate*/ true);
	Bind(SharedKeyboardContext, P2Move, EKeys::Right);
	Bind(SharedKeyboardContext, P2Move, EKeys::Left, false, /*Negate*/ true);

	// Turn camera: comma / period
	Bind(SharedKeyboardContext, P2Turn, EKeys::Period);
	Bind(SharedKeyboardContext, P2Turn, EKeys::Comma, false, /*Negate*/ true);

	// Jump: Slash (/) or Right Ctrl.  Brace: Right Shift.  Reel: Enter/Return.
	// Slash is there because Mac keyboards have no Right Ctrl.
	Bind(SharedKeyboardContext, P2Jump, EKeys::Slash);
	Bind(SharedKeyboardContext, P2Jump, EKeys::RightControl);
	Bind(SharedKeyboardContext, P2Brace, EKeys::RightShift);
	Bind(SharedKeyboardContext, P2Reel, EKeys::Enter);

	// Player 2's camera toggle from the keyboard: C
	Bind(SharedKeyboardContext, P2CameraToggle, EKeys::C);
}
