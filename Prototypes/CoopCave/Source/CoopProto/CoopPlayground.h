#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CoopMeshKit.h"
#include "CoopPlayground.generated.h"

class UDirectionalLightComponent;
class USkyLightComponent;
class USkyAtmosphereComponent;
class UExponentialHeightFogComponent;
class UPointLightComponent;
class UProceduralMeshComponent;
class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class APostProcessVolume;

/** A spot in the play area you can jump straight to (D-pad left/right, or number keys 1-9). */
struct FCoopStation
{
	FString Name;
	FString Status;                          // shown on arrival
	FVector Location = FVector::ZeroVector;  // where the players appear, at ground level
	float Yaw = 0.f;                         // which way they face on arrival
};

/** A spot on a maze path where a co-op moment is built, measured the way the path runs there. */
struct FCoopPathSpot
{
	FVector Origin = FVector::ZeroVector;     // the tile centre, on the floor
	FVector Forward = FVector::ForwardVector; // onward along the path
	FVector Right = FVector::RightVector;
	TArray<float> FloorZ;                     // floor height at the tile centres, from two tiles back to two on
	TArray<float> CeilingZ;                   // underside of the ceiling over the same tiles

	/** Floor height Along cm from the tile centre (+ = onward). */
	float FloorAt(float Along) const;
	/** Lowest ceiling over the tile Along cm from the tile centre. */
	float CeilingAt(float Along) const;
	/** A world point: Along the path, Side across it (+ = right), at height Z. */
	FVector At(float Along, float Side, float Z) const;
};

/** A piece that moves while a player stands (or braces) on one of its plates: the winch lift and the dip gate. */
struct FCoopMover
{
	int32 Piece = INDEX_NONE;                 // index into MoverPieces
	FVector RestLocation = FVector::ZeroVector;
	FVector ActiveLocation = FVector::ZeroVector;
	TArray<FBox> Plates;                      // where a player's feet must be
	bool bNeedsBrace = false;                 // only a braced player works the plates
	bool bGate = false;                       // speed from coop.Maze.GateSpeed instead of coop.Maze.LiftSpeed
	FBox KeepOpen = FBox(ForceInit);          // a gate never closes on a player standing in here
	float Alpha = 0.f;                        // 0 = at rest, 1 = active
};

/** Rocks that share one color, built into one mesh. */
struct FCoopRockGroup
{
	FCoopMeshData Mesh;
	TArray<TArray<FVector>> Hulls;   // one convex collision shape per rock
	FLinearColor Color = FLinearColor::White;
	bool bCollides = true;
	bool bCastShadow = true;
};

/**
 * The play area: a 25 m x 25 m torch-lit mine cave that builds itself in C++ when play starts.
 *
 *  - Faceted rock walls and ceiling, a sandy floor with pebbles
 *  - Rocks in three sizes: small ones you walk straight over, medium ones you jump onto, boulders that block
 *  - Timber mine frames with wall torches (flickering, shadow-casting), plus two standing torches
 *  - A work area: workbench, crates, barrels, a raised scaffold, a mine cart on rails
 *  - A corner of glowing teal crystals (the cool counter-light)
 *  - Cool fill light in the shadows, low haze, and a fixed camera exposure
 *
 * North of the cave, through a door in its north wall, is a maze (BuildMaze): four paths that cross
 * each other on rock bridges, climb and drop, meet in two halls, and end in a relic chamber.
 * Its layout is the table at the top of CoopPlayground.cpp; maze_overview.png is a picture of it.
 * Each path has one co-op moment (BuildMoments), from the CoopMaze::Moments table next to it.
 *
 * Lighting numbers are live console variables (coop.Cave.*), see CoopTuning.h.
 * Positions are in cm (100 = 1 m); the room spans -1250..1250 on X and Y.
 */
UCLASS()
class COOPPROTO_API ACoopPlayground : public AActor
{
	GENERATED_BODY()

public:
	ACoopPlayground();

	virtual void Tick(float DeltaSeconds) override;

	const TArray<FCoopStation>& GetStations() const { return Stations; }

protected:
	virtual void BeginPlay() override;

private:
	// Building
	void BuildShell();
	void BuildRockWalls();
	void BuildTimber();
	void BuildTorches();
	void BuildWorkArea();
	void BuildMineCart();
	void BuildFloorRocks();
	void BuildCrystals();
	void BuildLighting();
	void BuildMaze();
	/** The co-op moments on the maze paths (CoopMaze::Moments), one spot per moment. */
	void BuildMoments(const TArray<FCoopPathSpot>& Spots);
	void FinishRockGroups();

	/** Moves the lift and the gate toward open or shut, depending on who stands on their plates. */
	void UpdateMovers(float DeltaSeconds);

	/** Loads the shared style kit (rock mesh, rock and gold materials) if it has been migrated into this project. */
	void LoadRepoAssets();
	/** One rock of the maze's walls or ceiling: the repo rock mesh if present, otherwise a code-built rock. */
	void AddMazeRock(bool bCeiling, const FVector& Center, const FVector& Size, float Yaw);

	// Pieces
	void AddWallTorch(const FVector& MountPoint, const FVector& WallNormal, bool bKeyLight);
	void AddStandingTorch(const FVector& GroundPoint);
	/** bKeyLight: a torch out in the room. Key torches cast shadows (coop.Cave.TorchShadows 1) and get a bounce light. */
	void AddTorchFlameAndLight(const FVector& FlameBase, const FVector& Outward, float LightOut, bool bKeyLight);
	static bool TorchCastsShadow(bool bKeyLight);
	void AddCrate(const FVector& GroundCenter, float Size, float Yaw);
	void AddBarrel(const FVector& GroundCenter);
	void AddMineFrame(float X);

	// Building blocks
	UStaticMeshComponent* AddShape(UStaticMesh* Mesh, const FVector& Center, const FVector& SizeCm,
		const FRotator& Rotation, const FLinearColor& Color, bool bCollides = true);
	UStaticMeshComponent* AddBox(const FVector& Center, const FVector& SizeCm, const FLinearColor& Color, bool bCollides = true);
	/** A square-section beam from Start to End. */
	UStaticMeshComponent* AddBeam(const FVector& Start, const FVector& End, float Width, float Height, const FLinearColor& Color, bool bCollides = true);
	UProceduralMeshComponent* AddProcMesh(const FCoopMeshData& Data, UMaterialInterface* Material,
		const TArray<TArray<FVector>>& Hulls, bool bCastShadow = true, bool bMovable = false);
	void AddRock(FCoopRockGroup& Group, const FVector& GroundPoint, const FVector& Size, float Yaw,
		int32 Detail, float Jitter, float TopFlat, const FRotator& Tilt = FRotator::ZeroRotator);
	UMaterialInstanceDynamic* MaterialFor(const FLinearColor& Color);
	UMaterialInterface* GlowMaterial() const;

	/** True where random rocks must not go (stations, furniture, the rails). */
	bool IsKeepClear(const FVector2D& Point, float Radius) const;

	void ApplyLiveLighting(float TimeSeconds);

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<USceneComponent> Root;

	/** Never lights the cave itself: it only colors the sky that the sky light turns into cool fill. */
	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UDirectionalLightComponent> Sun;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<USkyLightComponent> SkyLight;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<USkyAtmosphereComponent> SkyAtmosphere;

	UPROPERTY(VisibleAnywhere, Category = "Coop")
	TObjectPtr<UExponentialHeightFogComponent> Fog;

	UPROPERTY(Transient)
	TObjectPtr<APostProcessVolume> PostVolume;

	UPROPERTY()
	TObjectPtr<UStaticMesh> CubeMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> SphereMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> CylinderMesh;

	UPROPERTY()
	TObjectPtr<UStaticMesh> ConeMesh;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> BaseMaterial;

	/** One material per color, shared by every shape of that color. */
	UPROPERTY(Transient)
	TMap<uint32, TObjectPtr<UMaterialInstanceDynamic>> MaterialCache;

	// Torches: one light, one flame and one warm bounce light each
	UPROPERTY(Transient)
	TArray<TObjectPtr<UPointLightComponent>> TorchLights;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UPointLightComponent>> BounceLights;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UProceduralMeshComponent>> TorchFlames;

	TArray<float> TorchPhases;
	TArray<bool> TorchIsKey;

	UPROPERTY(Transient)
	TObjectPtr<UPointLightComponent> CrystalLight;

	/** Teal lights along the maze's crystal path (follow coop.Cave.Crystal). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UPointLightComponent>> MazeCrystalLights;

	// The shared style kit from the main project's Content/Shared/Style, when migrated here
	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> RepoRockMesh;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> RepoRockMaterial;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInterface> RepoGoldMaterial;

	/** The moving pieces of the co-op moments (see Movers). */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> MoverPieces;

	TArray<FCoopMover> Movers;

	// Maze rocks using the repo rock mesh, turned into instanced meshes at the end of BuildMaze
	TArray<FTransform> MazeWallRockTransforms;
	TArray<FTransform> MazeCeilingRockTransforms;

	// Rock groups, turned into meshes at the end of BeginPlay
	FCoopRockGroup WallRocks;
	FCoopRockGroup CeilingRocks;
	FCoopRockGroup Boulders;
	FCoopRockGroup SmallRocks;
	FCoopRockGroup Pebbles;
	FCoopRockGroup FloorStones;
	FCoopRockGroup MazeWallRocks;      // only used when the repo rock mesh isn't in the project
	FCoopRockGroup MazeCeilingRocks;

	FRandomStream Random;
	TArray<FCoopStation> Stations;
	TArray<FBox2D> KeepClearBoxes;
	int32 LastShadowMode = -1;
};
