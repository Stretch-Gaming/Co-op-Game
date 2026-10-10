#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "CoopCharacter.generated.h"

class USpringArmComponent;
class UCameraComponent;
class UStaticMeshComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class UCoopInput;
class ACoopGameMode;

/** How a player's camera is set up. Each player picks their own. */
enum class ECoopCameraMode : uint8
{
	OverShoulder,
	FirstPerson
};

/**
 * A playable co-op character.
 *
 * Moves:
 *  - Move, look, jump
 *  - Brace (hold): plant your feet. You can't move, but you become the anchor
 *    for the tether, so your partner can hang off ledges without dragging you.
 *  - Reel (hold while bracing): shorten the tether to pull your partner up to you.
 *  - Boost jump: jump while standing next to your braced partner to launch high.
 *
 * Camera: over-the-shoulder or first person, toggled per player.
 * Feel numbers (speeds, jump, camera) are live console variables: see CoopTuning.h.
 *
 * Graybox visuals (engine shapes) so there are no art assets to import yet.
 */
UCLASS()
class COOPPROTO_API ACoopCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	ACoopCharacter();

	virtual void Tick(float DeltaSeconds) override;

	// ---------- Input API ----------
	// Called by this player's own controls, or by Player 1's shared keyboard.
	void InputMove(const FVector2D& Axis);
	void InputLookDegrees(float YawDegrees, float PitchDegrees);
	void InputJumpPressed();
	void InputJumpReleased();
	void SetBraceHeld(bool bHeld);
	void SetReelHeld(bool bHeld);

	// ---------- Camera ----------
	void ToggleCameraMode();
	void SetCameraMode(ECoopCameraMode NewMode);
	ECoopCameraMode GetCameraMode() const { return CameraMode; }

	// ---------- State used by the tether ----------
	bool IsBraced() const { return bBraced; }
	bool IsReeling() const { return bBraced && bReelHeld; }
	bool IsGrounded() const;

	/** 0 = Player 1, 1 = Player 2, -1 = not controlled by a local player. */
	int32 GetLocalPlayerIndex() const;

	/** The other player's character, or null if there isn't one yet. */
	ACoopCharacter* GetPartner() const;

	/** Called by the tether when the rope is taut: moves this character by Offset, sliding along walls. */
	void ApplyTetherPull(const FVector& Offset, const FVector& DirToPartner);

	/** Instantly puts the character somewhere (respawn, station travel). */
	void ResetTo(const FVector& Location);

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void PawnClientRestart() override;
	virtual void PossessedBy(AController* NewController) override;

private:
	// Own controls
	void OnMove(const FInputActionValue& Value);
	void OnLookStick(const FInputActionValue& Value);
	void OnLookMouse(const FInputActionValue& Value);
	void OnJumpStarted();
	void OnJumpCompleted();
	void OnBraceStarted();
	void OnBraceCompleted();
	void OnReelStarted();
	void OnReelCompleted();
	void OnCameraToggle();

	// Playground travel
	void OnStationNext();
	void OnStationPrev();
	void OnStationReset();
	void OnStationSelect(const FInputActionValue& Value);

	// Player 1's keyboard driving Player 2 (solo testing)
	void OnP2Move(const FInputActionValue& Value);
	void OnP2Turn(const FInputActionValue& Value);
	void OnP2JumpStarted();
	void OnP2JumpCompleted();
	void OnP2BraceStarted();
	void OnP2BraceCompleted();
	void OnP2ReelStarted();
	void OnP2ReelCompleted();
	void OnP2CameraToggle();

	void EnsureInputConfig();
	void StartBrace();
	void EndBrace();
	void ApplyPlayerColor();
	void UpdateBraceVisual();
	void ApplyCameraMode();
	void ApplyLiveTuning();
	ACoopGameMode* GetCoopGameMode() const;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UCameraComponent> FollowCamera;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UStaticMeshComponent> BodyMesh;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UStaticMeshComponent> HeadMesh;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UStaticMeshComponent> NoseMesh;

	/** Simple hands, only shown to this player and only in first person. */
	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UStaticMeshComponent> HandLeft;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UStaticMeshComponent> HandRight;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> BaseMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> BodyMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UCoopInput> CoopInputConfig;

	ECoopCameraMode CameraMode = ECoopCameraMode::OverShoulder;

	bool bBraced = false;
	bool bBraceHeld = false;
	bool bReelHeld = false;
};
