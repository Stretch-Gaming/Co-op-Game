#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CoopTestCourse.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class ACoopCharacter;

/**
 * The co-op course station: a graybox obstacle run that builds itself in C++ when play starts.
 * Spawned by the playground on a raised plinth; everything below is relative to this actor.
 *
 * Layout (course runs along +X):
 *   1. Start pad
 *   2. A wall too high to jump: boost jump up, then reel your partner up
 *   3. A pit with a star hanging in it: brace at the edge, lower your partner, reel them back
 *   4. A short gap to jump, then the green goal pad: both stand on it to finish
 */
UCLASS()
class COOPPROTO_API ACoopTestCourse : public AActor
{
	GENERATED_BODY()

public:
	ACoopTestCourse();

	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

private:
	UStaticMeshComponent* AddShape(UStaticMesh* Mesh, const FName Name, const FVector& Min, const FVector& Max,
		const FLinearColor& Color, bool bCollides);

	/** Position relative to this course (its start pad top is Z = 0). */
	FVector ToLocal(const FVector& WorldLocation) const { return WorldLocation - GetActorLocation(); }

	void UpdateStar(float DeltaSeconds, ACoopCharacter* A, ACoopCharacter* B);
	void UpdateGoal(ACoopCharacter* A, ACoopCharacter* B);
	void UpdateHints(ACoopCharacter* A, ACoopCharacter* B);

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY()
	TObjectPtr<UStaticMesh> CubeMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> SphereMesh;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> BaseMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Star;

	FVector StarHome = FVector::ZeroVector;
	float StarTime = 0.f;
	bool bStarCollected = false;
	bool bCourseComplete = false;
};
