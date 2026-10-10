#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "CoopGameMode.generated.h"

class ACoopPlayground;
class ACoopTether;

/**
 * Sets up a couch co-op session:
 *  - spawns Player 2 on the same machine (split screen comes from the project settings)
 *  - builds the play area (the torch-lit cave) and places both players at its entrance
 *  - the tether between the players is off; set coop.Tether 1 and press Play again to bring it back
 *  - station travel: moves both players to a spot in the cave (D-pad left/right/down, number keys 1-5)
 */
UCLASS()
class COOPPROTO_API ACoopGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ACoopGameMode();

	virtual void StartPlay() override;
	virtual void RestartPlayer(AController* NewPlayer) override;

	/** Moves both players to station Index (0 = hub). */
	void GoToStation(int32 Index);

	/** +1 = next station, -1 = previous (wraps around). */
	void StepStation(int32 Direction);

	/** Puts both players back at the start of the current station. */
	void ResetStation();

protected:
	virtual void BeginPlay() override;

	/** Build the C++ play area (the cave) when play starts. Turn off once you have real levels. */
	UPROPERTY(EditAnywhere, Category = "Coop")
	bool bBuildPlayground = true;

	UPROPERTY(EditAnywhere, Category = "Coop")
	FVector Player1Start = FVector(-600.f, -150.f, 120.f);

	UPROPERTY(EditAnywhere, Category = "Coop")
	FVector Player2Start = FVector(-600.f, 150.f, 120.f);

private:
	void ShowControls() const;

	UPROPERTY(Transient)
	TObjectPtr<ACoopPlayground> Playground;

	UPROPERTY(Transient)
	TObjectPtr<ACoopTether> Tether;

	int32 CurrentStation = 0;
};
