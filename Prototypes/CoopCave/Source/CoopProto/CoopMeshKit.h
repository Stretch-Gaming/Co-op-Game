#pragma once

#include "CoreMinimal.h"
#include "Math/RandomStream.h"

/**
 * Geometry for one procedural mesh section, built in code.
 * Every triangle gets its own three vertices and a face normal, so shapes come out
 * flat-shaded and faceted (the chunky low-poly look of the reference art).
 */
struct FCoopMeshData
{
	TArray<FVector> Vertices;
	TArray<int32> Triangles;
	TArray<FVector> Normals;
	TArray<FVector2D> UVs;
	TArray<FColor> Colors;

	/** Adds one flat-shaded triangle whose visible side faces OutwardHint. */
	void AddTriangle(const FVector& A, const FVector& B, const FVector& C, const FVector& OutwardHint,
		const FColor& ColorA, const FColor& ColorB, const FColor& ColorC);

	void AddTriangle(const FVector& A, const FVector& B, const FVector& C, const FVector& OutwardHint, const FColor& Color = FColor::White)
	{
		AddTriangle(A, B, C, OutwardHint, Color, Color, Color);
	}

	bool IsEmpty() const { return Triangles.Num() == 0; }
};

/** Shapes for the cave: rocks, crystals, flames. All sizes in cm. */
namespace CoopMeshKit
{
	/**
	 * A chunky low-poly rock resting on Z = 0 of Base (its bottom is flattened).
	 * Size = full width (X), depth (Y) and height (Z).
	 * Detail 0 = 20 faces (pebbles, small rocks), 1 = 80 faces (boulders, walls).
	 * Jitter = how lumpy (0.1 smooth .. 0.35 craggy). TopFlat = 0..1, how much of the top is sliced flat
	 * (flat tops are easier to stand on).
	 * Returns the rock's corner points, for convex collision.
	 */
	TArray<FVector> AddRock(FCoopMeshData& Mesh, FRandomStream& Random, const FTransform& Base, const FVector& Size,
		int32 Detail, float Jitter, float TopFlat);

	/** A six-sided crystal growing along +Z of Base, colored from BaseColor at the root to TipColor at the point. */
	TArray<FVector> AddCrystal(FCoopMeshData& Mesh, const FTransform& Base, float Radius, float Length,
		const FColor& BaseColor, const FColor& TipColor);

	/** A low-poly flame (teardrop) growing along +Z of Base. */
	void AddFlame(FCoopMeshData& Mesh, const FTransform& Base, float Radius, float Height,
		const FColor& CoreColor, const FColor& TipColor);
}
