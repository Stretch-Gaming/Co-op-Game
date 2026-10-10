#include "CoopTether.h"

#include "CoopCharacter.h"
#include "CoopTuning.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ACoopTether::ACoopTether()
{
	PrimaryActorTick.bCanEverTick = true;
	// Run after character movement each frame, so the rope corrects where they ended up.
	PrimaryActorTick.TickGroup = TG_PostPhysics;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShapeMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

	// The rope is drawn as a thin cylinder stretched between the two players.
	RopeMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("RopeMesh"));
	RootComponent = RopeMesh;
	RopeMesh->SetMobility(EComponentMobility::Movable);
	RopeMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	RopeMesh->SetVisibility(false);

	if (CylinderMesh.Succeeded())  { RopeMesh->SetStaticMesh(CylinderMesh.Object); }
	if (ShapeMaterial.Succeeded()) { BaseMaterial = ShapeMaterial.Object; }
}

void ACoopTether::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!FindPlayers())
	{
		RopeMesh->SetVisibility(false);
		return;
	}

	ACoopCharacter* A = PlayerA.Get();
	ACoopCharacter* B = PlayerB.Get();

	if (A->GetActorLocation().Z < FallResetHeight || B->GetActorLocation().Z < FallResetHeight)
	{
		ResetToSafeSpot();
		return;
	}

	SolveRope(DeltaSeconds);
	UpdateSafeSpot(DeltaSeconds);
	UpdateRopeVisual();
}

bool ACoopTether::FindPlayers()
{
	if (!PlayerA.IsValid())
	{
		PlayerA = Cast<ACoopCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
	}
	if (!PlayerB.IsValid())
	{
		PlayerB = Cast<ACoopCharacter>(UGameplayStatics::GetPlayerCharacter(this, 1));
	}

	const bool bFound = PlayerA.IsValid() && PlayerB.IsValid();

	// First time we see both players, their spawn points are the first safe spot.
	if (bFound && !bHaveSafeSpot)
	{
		SafeA = PlayerA->GetActorLocation();
		SafeB = PlayerB->GetActorLocation();
		bHaveSafeSpot = true;
		CurrentLength = CoopTuning::RopeMaxLength();
	}
	return bFound;
}

void ACoopTether::NotifyTeleported()
{
	if (!PlayerA.IsValid() || !PlayerB.IsValid())
	{
		return;
	}
	SafeA = PlayerA->GetActorLocation();
	SafeB = PlayerB->GetActorLocation();
	bHaveSafeSpot = true;
	SafeSpotTimer = 0.f;
	CurrentLength = CoopTuning::RopeMaxLength();
}

void ACoopTether::SolveRope(float DeltaSeconds)
{
	ACoopCharacter* A = PlayerA.Get();
	ACoopCharacter* B = PlayerB.Get();

	const FVector Delta = B->GetActorLocation() - A->GetActorLocation();
	const float Dist = static_cast<float>(Delta.Size());

	// Live-tunable values (coop.Rope.*)
	const float RopeMax = CoopTuning::RopeMaxLength();
	const float RopeMin = CoopTuning::RopeMinLength();
	const float ReelRate = CoopTuning::ReelSpeed();
	const float DragRate = CoopTuning::DragSpeed();
	const float AirWeight = CoopTuning::AirborneWeight();

	// --- Rope length ---
	const bool bReeling = A->IsReeling() || B->IsReeling();
	const bool bAnyBraced = A->IsBraced() || B->IsBraced();

	if (bReeling)
	{
		// Start from the actual distance so reeling bites immediately.
		CurrentLength = FMath::Max(RopeMin, FMath::Min(CurrentLength, Dist) - ReelRate * DeltaSeconds);
	}
	else if (!bAnyBraced)
	{
		// Nobody is holding the rope: it pays back out to full length.
		CurrentLength = RopeMax;
	}
	// Never longer than the current maximum (in case it was just lowered in the console).
	CurrentLength = FMath::Min(CurrentLength, RopeMax);
	// Braced but not reeling: length holds, so a partner you hauled up doesn't slide back down.

	bTaut = Dist >= CurrentLength - 5.f;
	if (Dist <= CurrentLength || Dist < UE_KINDA_SMALL_NUMBER)
	{
		return;
	}

	// --- Pull the players back within the rope length ---
	const FVector DirAtoB = Delta / Dist;
	const float Excess = Dist - CurrentLength;

	auto Weight = [AirWeight](const ACoopCharacter* C) -> float
	{
		if (C->IsBraced())
		{
			return 0.f;
		}
		return C->IsGrounded() ? 1.f : AirWeight;
	};

	const float WA = Weight(A);
	const float WB = Weight(B);
	const float Sum = WA + WB;
	if (Sum <= 0.f)
	{
		return; // both braced: neither can move, nothing to fix
	}

	if (WA > 0.f) { A->ApplyTetherPull( DirAtoB * (Excess * WA / Sum),  DirAtoB); }
	if (WB > 0.f) { B->ApplyTetherPull(-DirAtoB * (Excess * WB / Sum), -DirAtoB); }

	// --- Drag: a hanging partner pulls an unbraced, grounded player toward the edge ---
	auto Drag = [DragRate, DeltaSeconds](ACoopCharacter* Grounded, ACoopCharacter* Hanging, const FVector& DirToHanging)
	{
		if (Grounded->IsBraced() || !Grounded->IsGrounded() || Hanging->IsGrounded())
		{
			return;
		}
		const FVector Flat = FVector(DirToHanging.X, DirToHanging.Y, 0.f).GetSafeNormal();
		if (!Flat.IsNearlyZero())
		{
			Grounded->ApplyTetherPull(Flat * DragRate * DeltaSeconds, DirToHanging);
		}
	};
	Drag(A, B, DirAtoB);
	Drag(B, A, -DirAtoB);
}

void ACoopTether::UpdateSafeSpot(float DeltaSeconds)
{
	SafeSpotTimer += DeltaSeconds;
	if (SafeSpotTimer < 0.5f)
	{
		return;
	}
	SafeSpotTimer = 0.f;

	ACoopCharacter* A = PlayerA.Get();
	ACoopCharacter* B = PlayerB.Get();
	if (A->IsGrounded() && B->IsGrounded())
	{
		SafeA = A->GetActorLocation();
		SafeB = B->GetActorLocation();
		bHaveSafeSpot = true;
	}
}

void ACoopTether::ResetToSafeSpot()
{
	const FVector Lift(0.f, 0.f, 20.f);
	PlayerA->ResetTo(SafeA + Lift);
	PlayerB->ResetTo(SafeB + Lift);
	CurrentLength = CoopTuning::RopeMaxLength();

	if (GEngine)
	{
		GEngine->AddOnScreenDebugMessage(-1, 3.f, FColor::Orange, TEXT("Fell! Back to the last spot you were both standing."));
	}
}

void ACoopTether::UpdateRopeVisual()
{
	const FVector Start = PlayerA->GetActorLocation() + RopeAttachOffset;
	const FVector End = PlayerB->GetActorLocation() + RopeAttachOffset;
	const FVector Span = End - Start;
	const float Length = static_cast<float>(Span.Size());

	if (Length < 1.f)
	{
		RopeMesh->SetVisibility(false);
		return;
	}
	RopeMesh->SetVisibility(true);

	// The engine cylinder is 100 cm tall along Z: stretch it to the rope length and point it at the partner.
	const FRotator Rotation = FRotationMatrix::MakeFromZ(Span / Length).Rotator();
	RopeMesh->SetWorldLocationAndRotation((Start + End) * 0.5f, Rotation);
	RopeMesh->SetWorldScale3D(FVector(0.06f, 0.06f, Length / 100.f));

	if (!RopeMaterial && BaseMaterial)
	{
		RopeMaterial = UMaterialInstanceDynamic::Create(BaseMaterial, this);
		RopeMesh->SetMaterial(0, RopeMaterial);
	}
	if (RopeMaterial)
	{
		// Yellow when slack, red when taut
		const FLinearColor Slack(1.0f, 0.8f, 0.2f);
		const FLinearColor Taut(1.0f, 0.15f, 0.1f);
		RopeMaterial->SetVectorParameterValue(TEXT("Color"), bTaut ? Taut : Slack);
	}
}
