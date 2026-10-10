#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CoopTether.generated.h"

class ACoopCharacter;
class UStaticMeshComponent;
class UMaterialInterface;
class UMaterialInstanceDynamic;

/**
 * The rope between the two players (Unravel-style). Spawned by the game mode.
 *
 * Rules:
 *  - The rope has a length. Past it, the rope pulls the players back together.
 *  - A braced player never moves. An airborne player gets pulled harder than a grounded one.
 *  - If your partner is hanging and you are NOT braced, you get dragged toward them.
 *  - Brace + Reel shortens the rope to haul your partner up to you.
 *  - Fall out of the world and both players go back to the last spot where both were standing.
 *
 * Rope length, reel speed, drag and airborne weight are live console variables (coop.Rope.*),
 * see CoopTuning.h.
 */
UCLASS()
class COOPPROTO_API ACoopTether : public AActor
{
	GENERATED_BODY()

public:
	ACoopTether();

	virtual void Tick(float DeltaSeconds) override;

	/** Call after moving both players somewhere new (station travel): resets the rope and the safe spot. */
	void NotifyTeleported();

	/** Below this height, both players are put back at their last safe spot. */
	UPROPERTY(EditAnywhere, Category = "Coop|Tether")
	float FallResetHeight = -1500.f;

	/** Where the rope attaches on each character, relative to the character's center. */
	UPROPERTY(EditAnywhere, Category = "Coop|Tether")
	FVector RopeAttachOffset = FVector(0.f, 0.f, 30.f);

	float GetCurrentLength() const { return CurrentLength; }
	bool IsTaut() const { return bTaut; }

private:
	bool FindPlayers();
	void SolveRope(float DeltaSeconds);
	void UpdateSafeSpot(float DeltaSeconds);
	void ResetToSafeSpot();
	void UpdateRopeVisual();

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UStaticMeshComponent> RopeMesh;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> BaseMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> RopeMaterial;

	TWeakObjectPtr<ACoopCharacter> PlayerA;
	TWeakObjectPtr<ACoopCharacter> PlayerB;

	float CurrentLength = 800.f;
	bool bTaut = false;

	bool bHaveSafeSpot = false;
	FVector SafeA = FVector::ZeroVector;
	FVector SafeB = FVector::ZeroVector;
	float SafeSpotTimer = 0.f;
};
