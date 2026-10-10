#include "CoopMeshKit.h"

#include "KismetProceduralMeshLibrary.h"
#include "ProceduralMeshComponent.h"

namespace CoopMeshKitInternal
{
	/**
	 * Which way round a triangle has to be listed for its front to face its normal.
	 * Rather than guess the engine's convention, read it off the engine's own box generator once.
	 * Returns +1 if the front of (A, B, C) faces CrossProduct(B - A, C - A), otherwise -1.
	 */
	float FrontSign()
	{
		static float Sign = 0.f;
		if (Sign == 0.f)
		{
			TArray<FVector> Verts;
			TArray<int32> Tris;
			TArray<FVector> Norms;
			TArray<FVector2D> UVs;
			TArray<FProcMeshTangent> Tangents;
			UKismetProceduralMeshLibrary::GenerateBoxMesh(FVector(50.f), Verts, Tris, Norms, UVs, Tangents);

			Sign = 1.f;
			if (Tris.Num() >= 3 && Norms.IsValidIndex(Tris[0]))
			{
				const FVector Cross = FVector::CrossProduct(Verts[Tris[1]] - Verts[Tris[0]], Verts[Tris[2]] - Verts[Tris[0]]);
				Sign = (FVector::DotProduct(Cross, Norms[Tris[0]]) >= 0.0) ? 1.f : -1.f;
			}
		}
		return Sign;
	}

	/** Unit icosphere: 12 points / 20 faces at Detail 0, 42 points / 80 faces at Detail 1. */
	void MakeIcosphere(int32 Detail, TArray<FVector>& Points, TArray<FIntVector>& Faces)
	{
		const double T = (1.0 + FMath::Sqrt(5.0)) * 0.5;
		Points = {
			FVector(-1.0, T, 0.0), FVector(1.0, T, 0.0), FVector(-1.0, -T, 0.0), FVector(1.0, -T, 0.0),
			FVector(0.0, -1.0, T), FVector(0.0, 1.0, T), FVector(0.0, -1.0, -T), FVector(0.0, 1.0, -T),
			FVector(T, 0.0, -1.0), FVector(T, 0.0, 1.0), FVector(-T, 0.0, -1.0), FVector(-T, 0.0, 1.0) };
		for (FVector& P : Points)
		{
			P.Normalize();
		}
		Faces = {
			FIntVector(0, 11, 5), FIntVector(0, 5, 1), FIntVector(0, 1, 7), FIntVector(0, 7, 10), FIntVector(0, 10, 11),
			FIntVector(1, 5, 9), FIntVector(5, 11, 4), FIntVector(11, 10, 2), FIntVector(10, 7, 6), FIntVector(7, 1, 8),
			FIntVector(3, 9, 4), FIntVector(3, 4, 2), FIntVector(3, 2, 6), FIntVector(3, 6, 8), FIntVector(3, 8, 9),
			FIntVector(4, 9, 5), FIntVector(2, 4, 11), FIntVector(6, 2, 10), FIntVector(8, 6, 7), FIntVector(9, 8, 1) };

		for (int32 Level = 0; Level < Detail; ++Level)
		{
			TMap<uint64, int32> Midpoints;
			auto Midpoint = [&Points, &Midpoints](int32 A, int32 B)
			{
				const uint64 Key = (uint64(FMath::Min(A, B)) << 32) | uint64(FMath::Max(A, B));
				if (const int32* Found = Midpoints.Find(Key))
				{
					return *Found;
				}
				const int32 Index = Points.Add(((Points[A] + Points[B]) * 0.5).GetSafeNormal());
				Midpoints.Add(Key, Index);
				return Index;
			};

			TArray<FIntVector> Finer;
			Finer.Reserve(Faces.Num() * 4);
			for (const FIntVector& F : Faces)
			{
				const int32 AB = Midpoint(F.X, F.Y);
				const int32 BC = Midpoint(F.Y, F.Z);
				const int32 CA = Midpoint(F.Z, F.X);
				Finer.Add(FIntVector(F.X, AB, CA));
				Finer.Add(FIntVector(F.Y, BC, AB));
				Finer.Add(FIntVector(F.Z, CA, BC));
				Finer.Add(FIntVector(AB, BC, CA));
			}
			Faces = MoveTemp(Finer);
		}
	}

	FColor LerpColor(const FColor& A, const FColor& B, float Alpha)
	{
		const float T = FMath::Clamp(Alpha, 0.f, 1.f);
		return FColor(
			uint8(FMath::RoundToInt(FMath::Lerp(float(A.R), float(B.R), T))),
			uint8(FMath::RoundToInt(FMath::Lerp(float(A.G), float(B.G), T))),
			uint8(FMath::RoundToInt(FMath::Lerp(float(A.B), float(B.B), T))),
			255);
	}
}

void FCoopMeshData::AddTriangle(const FVector& A, const FVector& B, const FVector& C, const FVector& OutwardHint,
	const FColor& ColorA, const FColor& ColorB, const FColor& ColorC)
{
	FVector P1 = B;
	FVector P2 = C;
	FColor C1 = ColorB;
	FColor C2 = ColorC;

	FVector Normal = FVector::CrossProduct(B - A, C - A) * CoopMeshKitInternal::FrontSign();
	if (FVector::DotProduct(Normal, OutwardHint) < 0.0)
	{
		Swap(P1, P2);
		Swap(C1, C2);
		Normal = -Normal;
	}
	if (!Normal.Normalize())
	{
		return; // degenerate (zero-area) triangle
	}

	const int32 Start = Vertices.Num();
	Vertices.Add(A);
	Vertices.Add(P1);
	Vertices.Add(P2);
	Normals.Add(Normal);
	Normals.Add(Normal);
	Normals.Add(Normal);
	UVs.Add(FVector2D::ZeroVector);
	UVs.Add(FVector2D::ZeroVector);
	UVs.Add(FVector2D::ZeroVector);
	Colors.Add(ColorA);
	Colors.Add(C1);
	Colors.Add(C2);
	Triangles.Add(Start);
	Triangles.Add(Start + 1);
	Triangles.Add(Start + 2);
}

TArray<FVector> CoopMeshKit::AddRock(FCoopMeshData& Mesh, FRandomStream& Random, const FTransform& Base, const FVector& Size,
	int32 Detail, float Jitter, float TopFlat)
{
	TArray<FVector> Unit;
	TArray<FIntVector> Faces;
	CoopMeshKitInternal::MakeIcosphere(FMath::Clamp(Detail, 0, 1), Unit, Faces);

	// Lumpy sphere, with a flat base and (optionally) a sliced-flat top.
	const double BottomCut = -0.42;
	const double TopCut = 1.0 - FMath::Clamp(TopFlat, 0.f, 1.f) * 0.55;
	TArray<FVector> Local;
	Local.SetNum(Unit.Num());
	for (int32 i = 0; i < Unit.Num(); ++i)
	{
		FVector V = Unit[i] * (1.0 + Jitter * Random.FRandRange(-1.f, 1.f));
		V.Z = FMath::Max(V.Z, BottomCut + Random.FRandRange(0.f, 0.03f));
		if (V.Z > TopCut)
		{
			V.Z = TopCut + (V.Z - TopCut) * 0.15;
		}
		Local[i] = V;
	}

	// Stretch to the requested size, standing on Z = 0.
	double MaxX = UE_SMALL_NUMBER, MaxY = UE_SMALL_NUMBER, MinZ = UE_BIG_NUMBER, MaxZ = -UE_BIG_NUMBER;
	for (const FVector& V : Local)
	{
		MaxX = FMath::Max(MaxX, FMath::Abs(V.X));
		MaxY = FMath::Max(MaxY, FMath::Abs(V.Y));
		MinZ = FMath::Min(MinZ, V.Z);
		MaxZ = FMath::Max(MaxZ, V.Z);
	}
	const double HeightRange = FMath::Max(MaxZ - MinZ, UE_SMALL_NUMBER);

	TArray<FVector> Points;
	Points.SetNum(Local.Num());
	for (int32 i = 0; i < Local.Num(); ++i)
	{
		const FVector& V = Local[i];
		const FVector Sized(
			V.X / MaxX * Size.X * 0.5,
			V.Y / MaxY * Size.Y * 0.5,
			(V.Z - MinZ) / HeightRange * Size.Z);
		Points[i] = Base.TransformPosition(Sized);
	}

	const FVector Center = Base.TransformPosition(FVector(0.0, 0.0, Size.Z * 0.45));
	for (const FIntVector& F : Faces)
	{
		const FVector& A = Points[F.X];
		const FVector& B = Points[F.Y];
		const FVector& C = Points[F.Z];
		Mesh.AddTriangle(A, B, C, (A + B + C) / 3.0 - Center);
	}
	return Points;
}

TArray<FVector> CoopMeshKit::AddCrystal(FCoopMeshData& Mesh, const FTransform& Base, float Radius, float Length,
	const FColor& BaseColor, const FColor& TipColor)
{
	constexpr int32 Sides = 6;
	const float ShaftTop = Length * 0.72f;

	TArray<FVector> Bottom, Top;
	for (int32 i = 0; i < Sides; ++i)
	{
		const float Angle = 2.f * PI * i / Sides;
		Bottom.Add(Base.TransformPosition(FVector(FMath::Cos(Angle) * Radius, FMath::Sin(Angle) * Radius, 0.f)));
		Top.Add(Base.TransformPosition(FVector(FMath::Cos(Angle) * Radius * 0.9f, FMath::Sin(Angle) * Radius * 0.9f, ShaftTop)));
	}
	const FVector Tip = Base.TransformPosition(FVector(0.f, 0.f, Length));
	const FVector RootCenter = Base.TransformPosition(FVector::ZeroVector);
	const FVector Center = Base.TransformPosition(FVector(0.f, 0.f, Length * 0.4f));
	const FColor MidColor = CoopMeshKitInternal::LerpColor(BaseColor, TipColor, 0.72f);

	for (int32 i = 0; i < Sides; ++i)
	{
		const int32 j = (i + 1) % Sides;
		const FVector SideHint = ((Bottom[i] + Bottom[j] + Top[i] + Top[j]) * 0.25) - Center;
		Mesh.AddTriangle(Bottom[i], Bottom[j], Top[j], SideHint, BaseColor, BaseColor, MidColor);
		Mesh.AddTriangle(Bottom[i], Top[j], Top[i], SideHint, BaseColor, MidColor, MidColor);
		Mesh.AddTriangle(Top[i], Top[j], Tip, ((Top[i] + Top[j] + Tip) / 3.0) - Center, MidColor, MidColor, TipColor);
		Mesh.AddTriangle(RootCenter, Bottom[j], Bottom[i], RootCenter - Center, BaseColor);
	}

	TArray<FVector> Points = Bottom;
	Points.Append(Top);
	Points.Add(Tip);
	return Points;
}

void CoopMeshKit::AddFlame(FCoopMeshData& Mesh, const FTransform& Base, float Radius, float Height,
	const FColor& CoreColor, const FColor& TipColor)
{
	constexpr int32 Sides = 6;
	struct FRing { float Z; float R; float Twist; };
	const FRing Rings[] = { { 0.22f, 1.f, 0.f }, { 0.5f, 0.78f, 30.f }, { 0.76f, 0.42f, 0.f } };

	TArray<TArray<FVector>> RingPoints;
	TArray<FColor> RingColors;
	for (const FRing& Ring : Rings)
	{
		TArray<FVector>& Pts = RingPoints.AddDefaulted_GetRef();
		for (int32 i = 0; i < Sides; ++i)
		{
			const float Angle = FMath::DegreesToRadians(Ring.Twist + 360.f * i / Sides);
			Pts.Add(Base.TransformPosition(FVector(FMath::Cos(Angle) * Radius * Ring.R, FMath::Sin(Angle) * Radius * Ring.R, Ring.Z * Height)));
		}
		RingColors.Add(CoopMeshKitInternal::LerpColor(CoreColor, TipColor, Ring.Z));
	}
	const FVector BottomPoint = Base.TransformPosition(FVector::ZeroVector);
	const FVector TipPoint = Base.TransformPosition(FVector(0.f, 0.f, Height));
	const FVector Center = Base.TransformPosition(FVector(0.f, 0.f, Height * 0.4f));

	for (int32 i = 0; i < Sides; ++i)
	{
		const int32 j = (i + 1) % Sides;
		// bottom cap
		const TArray<FVector>& R0 = RingPoints[0];
		Mesh.AddTriangle(BottomPoint, R0[i], R0[j], (BottomPoint + R0[i] + R0[j]) / 3.0 - Center, CoreColor, RingColors[0], RingColors[0]);
		// bands between rings
		for (int32 r = 0; r + 1 < RingPoints.Num(); ++r)
		{
			const TArray<FVector>& Lo = RingPoints[r];
			const TArray<FVector>& Hi = RingPoints[r + 1];
			const FVector Hint = (Lo[i] + Lo[j] + Hi[i] + Hi[j]) * 0.25 - Center;
			Mesh.AddTriangle(Lo[i], Lo[j], Hi[j], Hint, RingColors[r], RingColors[r], RingColors[r + 1]);
			Mesh.AddTriangle(Lo[i], Hi[j], Hi[i], Hint, RingColors[r], RingColors[r + 1], RingColors[r + 1]);
		}
		// tip
		const TArray<FVector>& Last = RingPoints.Last();
		Mesh.AddTriangle(Last[i], Last[j], TipPoint, (Last[i] + Last[j] + TipPoint) / 3.0 - Center, RingColors.Last(), RingColors.Last(), TipColor);
	}
}
