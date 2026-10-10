#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "InputActionValue.h"
#include "CoopInput.generated.h"

class UInputAction;
class UInputMappingContext;
struct FKey;

/**
 * Every input action and key binding in the game, built in C++.
 * No input assets to create in the editor: change controls here.
 *
 * Player 1: keyboard + mouse, and the first gamepad.
 * Player 2: the second gamepad.
 * Solo testing: Player 1's keyboard can also drive Player 2 (arrow keys etc.).
 */
UCLASS()
class COOPPROTO_API UCoopInput : public UObject
{
	GENERATED_BODY()

public:
	/** Creates all actions and mapping contexts. Call once right after NewObject. */
	void Build();

	// --- Actions for the player who owns the character ---
	UPROPERTY() TObjectPtr<UInputAction> Move;
	UPROPERTY() TObjectPtr<UInputAction> LookStick;   // gamepad right stick (rate based)
	UPROPERTY() TObjectPtr<UInputAction> LookMouse;   // mouse (delta based)
	UPROPERTY() TObjectPtr<UInputAction> Jump;
	UPROPERTY() TObjectPtr<UInputAction> Brace;       // hold: plant your feet, become the anchor
	UPROPERTY() TObjectPtr<UInputAction> Reel;        // hold while bracing: pull your partner in
	UPROPERTY() TObjectPtr<UInputAction> CameraToggle; // first person <-> over-the-shoulder

	// --- Playground travel (either player; moves both players) ---
	UPROPERTY() TObjectPtr<UInputAction> StationNext;
	UPROPERTY() TObjectPtr<UInputAction> StationPrev;
	UPROPERTY() TObjectPtr<UInputAction> StationReset;
	UPROPERTY() TObjectPtr<UInputAction> StationSelect; // number keys: value = station number (1-6)

	// --- Actions that let Player 1's keyboard also drive Player 2 ---
	UPROPERTY() TObjectPtr<UInputAction> P2Move;
	UPROPERTY() TObjectPtr<UInputAction> P2Turn;
	UPROPERTY() TObjectPtr<UInputAction> P2Jump;
	UPROPERTY() TObjectPtr<UInputAction> P2Brace;
	UPROPERTY() TObjectPtr<UInputAction> P2Reel;
	UPROPERTY() TObjectPtr<UInputAction> P2CameraToggle;

	/** Keyboard/mouse and gamepad bindings, added for every player. */
	UPROPERTY() TObjectPtr<UInputMappingContext> PlayerContext;

	/** Extra keyboard bindings, added for Player 1 only, that drive Player 2. */
	UPROPERTY() TObjectPtr<UInputMappingContext> SharedKeyboardContext;

private:
	UInputAction* MakeAction(const TCHAR* Name, EInputActionValueType Type);

	/**
	 * Binds a key to an action.
	 * bSwizzleYX: send a 1D key press to the Y axis (forward/back).
	 * bNegate:    flip the value (back / left).
	 * bDeadZone:  ignore tiny stick movement.
	 */
	void Bind(UInputMappingContext* Context, UInputAction* Action, const FKey& Key,
		bool bSwizzleYX = false, bool bNegate = false, bool bDeadZone = false);
};
