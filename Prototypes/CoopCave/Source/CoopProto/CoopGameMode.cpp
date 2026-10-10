#include "CoopGameMode.h"

#include "CoopCharacter.h"
#include "CoopPlayground.h"
#include "CoopTether.h"
#include "CoopTuning.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

ACoopGameMode::ACoopGameMode()
{
	DefaultPawnClass = ACoopCharacter::StaticClass();
}

void ACoopGameMode::StartPlay()
{
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	if (bBuildPlayground)
	{
		Playground = GetWorld()->SpawnActor<ACoopPlayground>(ACoopPlayground::StaticClass(), FTransform::Identity, Params);
	}
	// The rope between the players is off by default. coop.Tether 1, then Play again, brings it back.
	if (CoopTuning::TetherEnabled())
	{
		Tether = GetWorld()->SpawnActor<ACoopTether>(ACoopTether::StaticClass(), FTransform::Identity, Params);
	}

	Super::StartPlay();
}

void ACoopGameMode::BeginPlay()
{
	Super::BeginPlay();

	// Add Player 2 on this machine. With two local players, the screen splits automatically.
	if (!UGameplayStatics::GetPlayerController(this, 1))
	{
		UGameplayStatics::CreatePlayer(this, 1, true);
	}

	ShowControls();
}

void ACoopGameMode::RestartPlayer(AController* NewPlayer)
{
	if (!NewPlayer || NewPlayer->IsPendingKillPending())
	{
		return;
	}

	// Player 2 is the second player controller in the world; everyone else uses Player 1's spot.
	const bool bIsPlayer2 = (UGameplayStatics::GetPlayerController(this, 1) == NewPlayer);
	const FVector Location = bIsPlayer2 ? Player2Start : Player1Start;

	RestartPlayerAtTransform(NewPlayer, FTransform(FRotator::ZeroRotator, Location));

	// Start each camera looking slightly down. This has to happen after
	// RestartPlayerAtTransform, which resets the camera to the spawn rotation.
	if (APawn* SpawnedPawn = NewPlayer->GetPawn())
	{
		NewPlayer->SetControlRotation(FRotator(-10.f, SpawnedPawn->GetActorRotation().Yaw, 0.f));
	}
}

// ---------------------------------------------------------------------------
// Station travel
// ---------------------------------------------------------------------------

void ACoopGameMode::GoToStation(int32 Index)
{
	if (!Playground)
	{
		return;
	}

	const TArray<FCoopStation>& AllStations = Playground->GetStations();
	if (!AllStations.IsValidIndex(Index))
	{
		return;
	}

	CurrentStation = Index;
	const FCoopStation& Station = AllStations[Index];
	const FRotator Facing(0.f, Station.Yaw, 0.f);
	const FVector Side = FRotationMatrix(Facing).GetUnitAxis(EAxis::Y);

	for (int32 PlayerIndex = 0; PlayerIndex < 2; ++PlayerIndex)
	{
		ACoopCharacter* CoopChar = Cast<ACoopCharacter>(UGameplayStatics::GetPlayerCharacter(this, PlayerIndex));
		if (!CoopChar)
		{
			continue;
		}

		// Side by side, 3 m apart, a little above the ground so they drop into place.
		const float SideOffset = (PlayerIndex == 0) ? -150.f : 150.f;
		CoopChar->ResetTo(Station.Location + Side * SideOffset + FVector(0.f, 0.f, 120.f));
		CoopChar->SetActorRotation(Facing);
		if (AController* PlayerCtrl = CoopChar->GetController())
		{
			PlayerCtrl->SetControlRotation(FRotator(-10.f, Station.Yaw, 0.f));
		}
	}

	if (Tether)
	{
		Tether->NotifyTeleported();
	}

	if (GEngine)
	{
		const FString Message = FString::Printf(TEXT("Station %d/%d: %s. %s"),
			Index + 1, AllStations.Num(), *Station.Name, *Station.Status);
		GEngine->AddOnScreenDebugMessage(7100, 5.f, FColor::Yellow, Message);
	}
}

void ACoopGameMode::StepStation(int32 Direction)
{
	if (!Playground)
	{
		return;
	}
	const int32 Count = Playground->GetStations().Num();
	if (Count == 0)
	{
		return;
	}
	GoToStation(((CurrentStation + Direction) % Count + Count) % Count);
}

void ACoopGameMode::ResetStation()
{
	GoToStation(CurrentStation);
}

// ---------------------------------------------------------------------------
// On-screen help
// ---------------------------------------------------------------------------

void ACoopGameMode::ShowControls() const
{
	if (!GEngine)
	{
		return;
	}

	// On-screen messages stack newest-on-top, so add the bottom line first.
	const float Seconds = 30.f;
	const FColor Color = FColor::White;
	GEngine->AddOnScreenDebugMessage(-1, Seconds, FColor::Cyan, TEXT("Tune live: press ` (left of 1), type coop. and press Tab (lighting is coop.Cave.*)"));
	GEngine->AddOnScreenDebugMessage(-1, Seconds, FColor::Cyan, TEXT("Keys: 1-5 jump to a spot, V switch camera, C switch P2's camera"));
	GEngine->AddOnScreenDebugMessage(-1, Seconds, FColor::Cyan, TEXT("THE CAVE - D-pad: left/right travel, down reset, up switch camera (first person / over-the-shoulder)"));
	GEngine->AddOnScreenDebugMessage(-1, Seconds, Color, TEXT("Solo test - P2 from keyboard: Arrows move, / jump, Right Shift brace, Comma/Period turn"));
	GEngine->AddOnScreenDebugMessage(-1, Seconds, Color, TEXT("Gamepad: Left stick move, Right stick look, A/Cross jump, LT brace (your partner jumps beside you to boost)"));
	GEngine->AddOnScreenDebugMessage(-1, Seconds, Color, TEXT("P1 keyboard: WASD move, Mouse look, Space jump, Left Shift brace"));
	GEngine->AddOnScreenDebugMessage(-1, Seconds, Color, TEXT("CO-OP PROTOTYPE - P1 = coral (keyboard or gamepad 1), P2 = teal (gamepad 2)"));
}
