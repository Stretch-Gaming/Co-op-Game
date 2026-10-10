#include "CoopTestCourse.h"

#include "CoopCharacter.h"
#include "CoopGameMode.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace CoopCourse
{
	// Heights (relative to the course): start pad top is Z = 0, the upper decks are Z = 350 (too high to jump).
	constexpr float DeckHeight = 350.f;

	// The course sits on a plinth this tall, so the blocks reach down to the playground's ground.
	constexpr float PlinthDepth = 600.f;

	// Landing on the playground floor below this (relative Z) counts as falling off.
	constexpr float FallOffDepth = -400.f;
	constexpr int32 CourseStationIndex = 1;   // the course's slot in the playground's station list

	// Hints only show while a player is this close to the course (cm).
	constexpr float HintRadius = 4500.f;
	const FVector CourseMiddle(1250.f, 0.f, 0.f);

	// Goal pad center and half-size
	const FVector GoalCenter(3000.f, 0.f, DeckHeight);
	constexpr float GoalHalfX = 120.f;
	constexpr float GoalHalfY = 140.f;

	// Star hanging in the pit, just past the upper deck's edge (edge is X = 2000)
	const FVector StarLocation(2075.f, 0.f, -180.f);
	constexpr float StarPickupRadius = 140.f;

	const FLinearColor StartColor(0.35f, 0.38f, 0.45f);
	const FLinearColor DeckColor(0.55f, 0.48f, 0.40f);
	const FLinearColor EdgeColor(1.0f, 0.75f, 0.1f);
	const FLinearColor GoalColor(0.2f, 0.85f, 0.35f);
	const FLinearColor StarColor(1.0f, 0.85f, 0.1f);

	constexpr int32 HintMessageKey = 7001;
	constexpr int32 EventMessageKey = 7002;
}

ACoopTestCourse::ACoopTestCourse()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Root->SetMobility(EComponentMobility::Movable);
	RootComponent = Root;

	// Lighting and sky now live in the playground (CoopPlayground).

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShapeMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

	if (Cube.Succeeded())          { CubeMesh = Cube.Object; }
	if (Sphere.Succeeded())        { SphereMesh = Sphere.Object; }
	if (ShapeMaterial.Succeeded()) { BaseMaterial = ShapeMaterial.Object; }
}

void ACoopTestCourse::BeginPlay()
{
	Super::BeginPlay();

	using namespace CoopCourse;

	// 1. Start pad (players arrive here)
	AddShape(CubeMesh, TEXT("StartPad"), FVector(-700.f, -500.f, -PlinthDepth), FVector(600.f, 500.f, 0.f), StartColor, true);

	// 2. Upper deck: its front face is the wall you boost up
	AddShape(CubeMesh, TEXT("UpperDeck"), FVector(600.f, -500.f, -PlinthDepth), FVector(2000.f, 500.f, DeckHeight), DeckColor, true);

	// Yellow stripes = "brace here". They sit a step back from each ledge, because the
	// anchor needs some distance from the edge to haul a partner up and over the lip.
	AddShape(CubeMesh, TEXT("WallTopStripe"), FVector(720.f, -500.f, DeckHeight), FVector(800.f, 500.f, DeckHeight + 2.f), EdgeColor, false);
	AddShape(CubeMesh, TEXT("PitEdgeStripe"), FVector(1800.f, -500.f, DeckHeight), FVector(1880.f, 500.f, DeckHeight + 2.f), EdgeColor, false);

	// 3. Pit from X = 2000 to 2300 (no floor), star hanging inside
	StarHome = StarLocation;
	Star = AddShape(SphereMesh, TEXT("Star"), StarLocation - FVector(35.f), StarLocation + FVector(35.f), StarColor, false);

	// 4. Goal deck across the gap
	AddShape(CubeMesh, TEXT("GoalDeck"), FVector(2300.f, -500.f, -PlinthDepth), FVector(3200.f, 500.f, DeckHeight), DeckColor, true);

	// Green goal pad
	const FVector GoalHalf(GoalHalfX, GoalHalfY, 0.f);
	AddShape(CubeMesh, TEXT("GoalPad"), GoalCenter - GoalHalf, GoalCenter + GoalHalf + FVector(0.f, 0.f, 3.f), GoalColor, false);
}

UStaticMeshComponent* ACoopTestCourse::AddShape(UStaticMesh* Mesh, const FName Name, const FVector& Min, const FVector& Max,
	const FLinearColor& Color, bool bCollides)
{
	UStaticMeshComponent* Shape = NewObject<UStaticMeshComponent>(this, Name);
	Shape->SetMobility(EComponentMobility::Movable);
	Shape->SetupAttachment(Root);
	Shape->SetStaticMesh(Mesh);

	// Engine shapes are 100 cm across, so scale = size / 100.
	Shape->SetRelativeLocation((Min + Max) * 0.5f);
	Shape->SetRelativeScale3D((Max - Min) / 100.f);
	Shape->SetCollisionEnabled(bCollides ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
	Shape->RegisterComponent();

	if (BaseMaterial)
	{
		UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, this);
		Material->SetVectorParameterValue(TEXT("Color"), Color);
		Shape->SetMaterial(0, Material);
	}
	return Shape;
}

void ACoopTestCourse::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	ACoopCharacter* A = Cast<ACoopCharacter>(UGameplayStatics::GetPlayerCharacter(this, 0));
	ACoopCharacter* B = Cast<ACoopCharacter>(UGameplayStatics::GetPlayerCharacter(this, 1));
	if (!A || !B)
	{
		return;
	}

	// Fell off the course onto the playground floor? Back to the course start.
	// (Hanging in the pit on a full rope never gets this low, so rappelling is safe.)
	auto FellOff = [this](const ACoopCharacter* C)
	{
		const FVector L = ToLocal(C->GetActorLocation());
		return C->IsGrounded() && L.Z < CoopCourse::FallOffDepth
			&& L.X > -900.f && L.X < 3400.f && FMath::Abs(L.Y) < 1200.f;
	};
	if (FellOff(A) || FellOff(B))
	{
		if (ACoopGameMode* GM = GetWorld()->GetAuthGameMode<ACoopGameMode>())
		{
			GM->GoToStation(CoopCourse::CourseStationIndex);
			if (GEngine)
			{
				GEngine->AddOnScreenDebugMessage(CoopCourse::EventMessageKey, 3.f, FColor::Orange, TEXT("Fell off the course: back to the start."));
			}
			return;
		}
	}

	UpdateStar(DeltaSeconds, A, B);
	UpdateGoal(A, B);
	UpdateHints(A, B);
}

void ACoopTestCourse::UpdateStar(float DeltaSeconds, ACoopCharacter* A, ACoopCharacter* B)
{
	if (bStarCollected || !Star)
	{
		return;
	}

	// Bob and spin so it reads as a pickup
	StarTime += DeltaSeconds;
	Star->SetRelativeLocation(StarHome + FVector(0.f, 0.f, FMath::Sin(StarTime * 2.f) * 15.f));
	Star->SetRelativeRotation(FRotator(0.f, StarTime * 90.f, 0.f));

	const FVector StarWorld = Star->GetComponentLocation();
	const bool bTouched =
		FVector::Dist(A->GetActorLocation(), StarWorld) < CoopCourse::StarPickupRadius ||
		FVector::Dist(B->GetActorLocation(), StarWorld) < CoopCourse::StarPickupRadius;

	if (bTouched)
	{
		bStarCollected = true;
		Star->SetVisibility(false);
		if (GEngine)
		{
			GEngine->AddOnScreenDebugMessage(CoopCourse::EventMessageKey, 4.f, FColor::Yellow, TEXT("Star collected!"));
		}
	}
}

void ACoopTestCourse::UpdateGoal(ACoopCharacter* A, ACoopCharacter* B)
{
	if (bCourseComplete)
	{
		return;
	}

	auto OnPad = [this](const ACoopCharacter* C)
	{
		const FVector L = ToLocal(C->GetActorLocation());
		const FVector G = CoopCourse::GoalCenter;
		return C->IsGrounded()
			&& FMath::Abs(L.X - G.X) < CoopCourse::GoalHalfX
			&& FMath::Abs(L.Y - G.Y) < CoopCourse::GoalHalfY
			&& L.Z > G.Z && L.Z < G.Z + 300.f;
	};

	if (OnPad(A) && OnPad(B))
	{
		bCourseComplete = true;
		if (GEngine)
		{
			const FString Message = FString::Printf(TEXT("Course complete! Stars: %d/1"), bStarCollected ? 1 : 0);
			GEngine->AddOnScreenDebugMessage(CoopCourse::EventMessageKey, 10.f, FColor::Green, Message);
		}
	}
}

void ACoopTestCourse::UpdateHints(ACoopCharacter* A, ACoopCharacter* B)
{
	if (!GEngine)
	{
		return;
	}

	// Only coach players who are actually at the course.
	const FVector Middle = GetActorLocation() + CoopCourse::CourseMiddle;
	if (FVector::DistXY(A->GetActorLocation(), Middle) > CoopCourse::HintRadius &&
		FVector::DistXY(B->GetActorLocation(), Middle) > CoopCourse::HintRadius)
	{
		return;
	}

	// "Up" = standing at upper-deck height. A partner hanging in the pit counts as down.
	const float UpThreshold = CoopCourse::DeckHeight - 50.f;
	const bool bAUp = ToLocal(A->GetActorLocation()).Z > UpThreshold;
	const bool bBUp = ToLocal(B->GetActorLocation()).Z > UpThreshold;

	const TCHAR* Hint = nullptr;
	if (bCourseComplete)
	{
		Hint = TEXT("Done! D-pad left/right (or 1-6) to visit another station.");
	}
	else if (!bAUp && !bBUp)
	{
		Hint = TEXT("Wall too high to jump? One player holds BRACE next to it. The other JUMPS right beside them to boost up.");
	}
	else if (bAUp != bBUp)
	{
		Hint = TEXT("Player up top: stand on the yellow stripe, hold BRACE, then hold REEL to pull your partner up.");
	}
	else if (!bStarCollected)
	{
		Hint = TEXT("Star in the pit! One player BRACES on the yellow stripe. The other walks off the edge and hangs on the rope. Then REEL them up.");
	}
	else
	{
		Hint = TEXT("Jump the gap and both stand on the green pad.");
	}

	GEngine->AddOnScreenDebugMessage(CoopCourse::HintMessageKey, 0.5f, FColor::Cyan, Hint);
}
