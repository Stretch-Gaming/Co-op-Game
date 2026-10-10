#include "CoopPlayground.h"

#include "CoopCharacter.h"
#include "CoopTuning.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SkyAtmosphereComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/Engine.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "ProceduralMeshComponent.h"
#include "UObject/ConstructorHelpers.h"

namespace CoopCave
{
	// The room: 25 m x 25 m, floor at Z = 0.
	constexpr float Half = 1250.f;
	constexpr float CeilingZ = 720.f;          // underside of the ceiling rocks
	constexpr float BlockerCeilingZ = 700.f;   // invisible lid, so a boost jump can't leave the cave

	// Timber mine frames: posts against the north and south walls, a beam across the room
	const float FrameXs[] = { -650.f, 50.f, 750.f };
	constexpr float FramePostY = 1040.f;
	constexpr float FrameBeamZ = 640.f;
	constexpr float PostSize = 34.f;

	// Furniture
	const FVector WorkbenchCenter(830.f, 280.f, 0.f);
	const FVector ScaffoldCenter(985.f, 900.f, 0.f);
	constexpr float ScaffoldHeight = 170.f;
	constexpr float RailY = -930.f;
	constexpr float RailStartX = -1080.f;
	constexpr float RailEndX = 640.f;
	constexpr float CartX = -280.f;
	const FVector CrystalCorner(1010.f, -1010.f, 0.f);
	const FVector StandingTorchA(500.f, -90.f, 0.f);
	const FVector StandingTorchB(-720.f, -430.f, 0.f);

	// The door to the maze in the north wall, between the timber posts (the maze's tile column 23)
	constexpr float DoorMinX = 250.f;
	constexpr float DoorMaxX = 750.f;

	// Surface colors (linear)
	const FLinearColor Sand(0.20f, 0.17f, 0.16f);
	const FLinearColor WallRock(0.30f, 0.16f, 0.085f);
	const FLinearColor CeilingRock(0.15f, 0.085f, 0.05f);
	const FLinearColor BoulderRock(0.34f, 0.20f, 0.11f);
	const FLinearColor SmallRock(0.30f, 0.22f, 0.15f);
	const FLinearColor Pebble(0.17f, 0.14f, 0.12f);
	const FLinearColor FloorStone(0.25f, 0.21f, 0.19f);
	const FLinearColor Wood(0.30f, 0.15f, 0.06f);
	const FLinearColor WoodDark(0.15f, 0.075f, 0.03f);
	const FLinearColor WoodLight(0.42f, 0.24f, 0.11f);
	const FLinearColor Iron(0.045f, 0.045f, 0.05f);
	const FLinearColor Rust(0.20f, 0.09f, 0.04f);
	const FLinearColor Cloth(0.12f, 0.07f, 0.04f);
	const FLinearColor Backstop(0.02f, 0.015f, 0.012f);

	// Light colors
	const FLinearColor TorchLightColor(1.0f, 0.56f, 0.26f);
	const FLinearColor BounceLightColor(1.0f, 0.45f, 0.20f);
	const FLinearColor CrystalLightColor(0.22f, 0.95f, 0.88f);
	const FLinearColor AmbientTint(0.55f, 0.85f, 1.0f);
	const FLinearColor FogColor(0.025f, 0.06f, 0.075f);

	// Glowing parts (vertex colors)
	const FColor FlameCore(255, 236, 160);
	const FColor FlameTip(255, 110, 25);
	const FColor CrystalRoot(10, 90, 100);
	const FColor CrystalTip(150, 255, 235);
}

namespace CoopMaze
{
	// The maze north of the cave, on a grid of 5 m tiles. Tile (Col, Row) is centred on
	// X = (Col - 22) * 5 m, Y = (41 - Row) * 5 m: the cave is cols 20-24, rows 39-43, and rows count down going north.
	// Heights in the tables are metres; everything else is cm. maze_overview.png in the project folder pictures this layout.
	constexpr float Tile = 500.f;
	constexpr int32 OriginCol = 22;
	constexpr int32 OriginRow = 41;
	constexpr float Free = -1000.f;            // waypoint height: work it out from the waypoints either side
	constexpr float CorridorHeadroom = 550.f;
	constexpr float RoomHeadroom = 750.f;
	constexpr float Slab = 60.f;               // floor and bridge deck thickness
	constexpr float CeilingThickness = 300.f;
	constexpr float MaxRampStep = 205.f;       // most a floor rises from one tile to the next: about 22 degrees
	constexpr int32 TorchEvery = 6;            // tiles between torches along a path (30 m)

	enum ERoom : int32 { Hub, Door, Fork, HallA, HallB, Goal, RoomCount };
	struct FRoomSpec { const TCHAR* Name; int32 C0, R0, C1, R1; float Z; };
	const FRoomSpec Rooms[RoomCount] = {
		{ TEXT("Start cave"),      20, 39, 24, 43,  0.f },   // the cave itself, built by the rest of this file
		{ TEXT("Door"),            23, 36, 23, 38,  0.f },
		{ TEXT("Fork"),            17, 33, 27, 35,  0.f },
		{ TEXT("Meeting point A"), 18, 21, 26, 24, -3.f },   // sunken hall
		{ TEXT("Meeting point B"), 18,  9, 26, 11,  4.f },   // raised hall
		{ TEXT("Relic chamber"),   18, -8, 26, -5,  6.f },
	};
	// Each path has three segments: fork to hall A, hall A to hall B, hall B to the relic chamber.
	const ERoom SegmentRooms[] = { Fork, HallA, HallB, Goal };

	/** A corner (or a fixed height) along a path. Consecutive waypoints share a row or a column. */
	struct FWaypoint { int32 Col, Row; float Z; };
	struct FTileRef { int32 Col, Row; };
	struct FPathSpec
	{
		FColor Color;
		TArray<TArray<FWaypoint>> Segments;
		TArray<TArray<FTileRef>> DeadEnds;   // each starts on a tile of the path and keeps its height
	};

	/**
	 * Where two paths cross, the higher one is a bridge over the lower (at least 6 m apart).
	 * Ramps only go on straight runs: corners, bridges, path ends and dead-end junctions stay flat.
	 */
	TArray<FPathSpec> MakePaths()
	{
		const float F = Free;
		return {
			// Path 1 (orange): over path 3, down into a trench under path 2, up to hall B, under path 2 again
			{ FColor(232, 121, 74), {
				{ {25,32,0}, {25,30,F}, {32,30,F}, {32,28,5}, {32,23,F}, {27,23,-3} },
				{ {24,20,-3}, {24,18,-3}, {24,15,F}, {15,15,F}, {15,13,4}, {15,11,F}, {17,11,4} },
				{ {23,8,4}, {23,3,4}, {23,1,F}, {20,1,F}, {20,-4,6} } },
			  { { {20,0}, {14,0}, {14,3} } } },
			// Path 2 (yellow): under path 4, over path 1, under path 3, then up onto the highest bridge over path 1
			{ FColor(224, 189, 69), {
				{ {19,32,0}, {19,30,F}, {12,30,F}, {12,28,-1}, {12,23,F}, {17,23,-3} },
				{ {18,20,-3}, {18,18,F}, {24,18,3}, {29,18,F}, {29,13,4}, {29,11,F}, {27,11,4} },
				{ {21,8,4}, {21,3,F}, {23,3,10}, {25,3,F}, {25,-4,6} } },
			  { { {12,25}, {15,25} } } },
			// Path 3 (teal, crystal-lit): under path 1, a long climb over path 2, a +10 m lookout
			{ FColor(63, 201, 184), {
				{ {28,34,0}, {38,34,F}, {38,28,F}, {32,28,-1}, {24,28,F}, {24,25,-3} },
				{ {27,21,-3}, {36,21,F}, {36,13,F}, {29,13,10}, {24,13,F}, {24,12,4} },
				{ {26,8,4}, {26,6,F}, {34,6,10}, {34,-6,F}, {27,-6,6} } },
			  { { {38,31}, {41,31} }, { {34,0}, {38,0} } } },
			// Path 4 (purple, the long way): over path 2, down to hall A, under path 1, a dip before the end
			{ FColor(165, 140, 240), {
				{ {16,34,0}, {4,34,F}, {4,28,F}, {12,28,5}, {20,28,F}, {20,25,-3} },
				{ {17,21,-3}, {8,21,F}, {8,13,F}, {15,13,-2}, {20,13,F}, {20,12,4} },
				{ {18,8,4}, {18,6,F}, {10,6,F}, {10,0,0}, {10,-6,F}, {17,-6,6} } },
			  { { {4,31}, {1,31} }, { {8,17}, {13,17} } } },
		};
	}

	/**
	 * One co-op moment per path, in engine shapes and flat colors (graybox). Each needs a boost jump off a braced
	 * partner, then a way for the partner to follow. Positions are cm from the tile centre: Along the path (+ = onward)
	 * and across it (+ = right).
	 *
	 * The heights come from the default tuning. coop.Gravity 1.6 makes g = 1568 cm/s^2, and a player is 192 cm tall.
	 *  - A jump (coop.JumpVelocity 760) lifts your feet 760^2 / (2 * 1568) = 184 cm.
	 *  - A boost jump (coop.Boost.Up 1300) would lift them 539 cm, but a corridor's 550 cm ceiling stops your feet
	 *    at 550 - 192 = 358 cm.
	 *  - So the climb one player can't make is 250 cm: a jump falls 66 cm short (and your shoulders, 42 cm above your
	 *    feet, stay under the edge), a boost clears it by 108 cm. A step you can jump onto alone is 120 cm.
	 *  - coop.StepHeight 45 cm: the plates and the lift at rest stand 4 cm proud, so you walk straight onto them.
	 *  - A boost needs your braced partner within coop.Boost.Range (200 cm) across and 150 cm up or down. Through a
	 *    30 cm wall you're 42 + 30 + 42 = 114 cm apart, so you can boost off someone braced on the other side. A 150 cm
	 *    block puts you 234 cm apart, too far.
	 */
	enum class EMoment : uint8 { Wall, Lift, Split, Gate };
	struct FMomentSpec
	{
		const TCHAR* Name;
		const TCHAR* Status;   // shown when you travel to its station
		EMoment Kind;
		int32 Path;            // 0-3
		int32 Col, Row;        // the path tile it's built on (a straight run, no bridge)
		float Station;         // where its station is, cm along the path
		float Along;           // where its main piece is, cm along the path
		float Height;          // the climb one player can't make alone, cm above the floor
		float Depth;           // the main piece's depth along the path, cm
		float Helper;          // how the partner follows (see below), cm
		float Span;            // (see below), cm
	};
	// Wall:  a wall across the path. Behind it a Helper-high, Span-deep drop-down ledge: brace there to boost your partner over.
	// Lift:  a cliff in the climb; its top runs on until the ramp meets it. In front, a Span-long lift rises to the top
	//        while a player braces on the winch plate up there.
	// Split: a Span-long divider makes two tunnels. Each has a block, Helper apart along the path: you can't boost off
	//        someone behind your own block, so you take turns across the divider.
	// Gate:  a gate across the dip. A Height-high switch ledge before it (Helper along) and a floor plate Span past it
	//        each hold it open.
	const FMomentSpec Moments[] = {
		// Name                Status                                                                                          Kind            Path Col Row  Station  Along  Height Depth  Helper  Span
		{ TEXT("Boost wall"),    TEXT("Boost your partner over the wall. Then brace on the ledge behind it and boost them over."),      EMoment::Wall,  0, 24, 19, -350.f,    0.f, 250.f,  30.f,  120.f,  150.f },
		{ TEXT("Winch lift"),    TEXT("Boost your partner up the cliff. Then they brace on the plate up there to lift you."),          EMoment::Lift,  1, 21,  7, -400.f,    0.f, 250.f,   0.f,    0.f,  200.f },
		{ TEXT("Split tunnels"), TEXT("One of you in each tunnel. Boost each other over the blocks through the divider, in turn."),    EMoment::Split, 2, 33, 34, -800.f,    0.f, 250.f, 150.f,  400.f, 1000.f },
		{ TEXT("Dip gate"),      TEXT("Boost your partner onto the ledge to open the gate. Go through and stand on the plate."),       EMoment::Gate,  3, 10,  0, -600.f,  150.f, 250.f,  40.f, -300.f,  200.f },
	};

	FVector2D TileCenter(const FIntPoint& T)
	{
		return FVector2D((T.X - OriginCol) * Tile, (OriginRow - T.Y) * Tile);
	}

	/** Tile-grid direction to world direction (rows count down going north, +Y). */
	FVector WorldDir(const FIntPoint& D)
	{
		return FVector(D.X, -D.Y, 0.f);
	}

	FVector RoomCenter(ERoom Room)
	{
		const FRoomSpec& R = Rooms[Room];
		return FVector(((R.C0 + R.C1) * 0.5f - OriginCol) * Tile, (OriginRow - (R.R0 + R.R1) * 0.5f) * Tile, R.Z * 100.f);
	}

	/** One walkable floor on a tile. A tile under a bridge has two. */
	struct FLevel
	{
		int32 Owner = 0;                   // 0-3 = a path, RoomOwner + ERoom = a room
		float Z = 0.f;                     // floor height at the tile centre
		float FloorMin = 0.f;              // lowest and highest floor point on the tile (ramps)
		float FloorMax = 0.f;
		float Headroom = CorridorHeadroom;
		int32 LinkOwner = INDEX_NONE;      // a path's end tile: the room it opens into
		bool bBridge = false;              // the upper path at a crossing
		bool bUnderBridge = false;         // the lower path at a crossing
	};
	constexpr int32 RoomOwner = 100;

	bool Connected(const FLevel& A, const FLevel& B)
	{
		const float Rise = FMath::Abs(A.Z - B.Z);
		if (A.Owner == B.Owner)
		{
			return Rise <= MaxRampStep;
		}
		if (A.LinkOwner == B.Owner || B.LinkOwner == A.Owner)
		{
			return Rise < 1.f;
		}
		return A.Owner >= RoomOwner && B.Owner >= RoomOwner && Rise < 1.f;   // the door opens into the cave and the fork
	}

	/** A solid box as triangles plus a convex collision shape. */
	void AddBlock(FCoopMeshData& Mesh, TArray<TArray<FVector>>& Hulls, const FTransform& Frame, const FVector& Half)
	{
		TArray<FVector> Corners;
		for (int32 i = 0; i < 8; ++i)
		{
			Corners.Add(Frame.TransformPosition(FVector((i & 1) ? Half.X : -Half.X, (i & 2) ? Half.Y : -Half.Y, (i & 4) ? Half.Z : -Half.Z)));
		}
		for (int32 Axis = 0; Axis < 3; ++Axis)
		{
			for (const float Sign : { -1.f, 1.f })
			{
				// The face's four corners, in bit order: (-,-), (+,-), (-,+), (+,+) along the other two axes
				int32 Face[4];
				int32 Count = 0;
				for (int32 i = 0; i < 8; ++i)
				{
					if ((((i >> Axis) & 1) == 1) == (Sign > 0.f))
					{
						Face[Count++] = i;
					}
				}
				const FVector Normal = Frame.TransformVectorNoScale(FVector(Axis == 0 ? Sign : 0.f, Axis == 1 ? Sign : 0.f, Axis == 2 ? Sign : 0.f));
				Mesh.AddTriangle(Corners[Face[0]], Corners[Face[1]], Corners[Face[3]], Normal);
				Mesh.AddTriangle(Corners[Face[0]], Corners[Face[3]], Corners[Face[2]], Normal);
			}
		}
		Hulls.Add(MoveTemp(Corners));
	}

	FColor Scaled(const FColor& C, float S)
	{
		return FColor(FMath::Clamp(FMath::RoundToInt(C.R * S), 0, 255), FMath::Clamp(FMath::RoundToInt(C.G * S), 0, 255), FMath::Clamp(FMath::RoundToInt(C.B * S), 0, 255));
	}

	FColor Lighter(const FColor& C)
	{
		return FColor((C.R + 255) / 2, (C.G + 255) / 2, (C.B + 255) / 2);
	}

	template <typename T>
	T* LoadIfPresent(const TCHAR* PackageName, const TCHAR* ObjectPath)
	{
		return FPackageName::DoesPackageExist(FString(PackageName)) ? LoadObject<T>(nullptr, ObjectPath) : nullptr;
	}
}

ACoopPlayground::ACoopPlayground()
{
	PrimaryActorTick.bCanEverTick = true;

	// The cave never moves, so its shadows can be cached. Lights and flames are movable.
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Root->SetMobility(EComponentMobility::Static);
	RootComponent = Root;

	// The sun lights no surface (no lighting channels): it only colors the sky,
	// which the sky light turns into the cool fill you see in the shadows.
	Sun = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("Sun"));
	Sun->SetupAttachment(Root);
	Sun->SetMobility(EComponentMobility::Movable);
	Sun->SetRelativeRotation(FRotator(-50.f, -40.f, 0.f));
	Sun->Intensity = 10.f;
	Sun->bAtmosphereSunLight = true;
	Sun->CastShadows = false;
	Sun->LightingChannels.bChannel0 = false;
	Sun->LightingChannels.bChannel1 = false;
	Sun->LightingChannels.bChannel2 = false;

	SkyLight = CreateDefaultSubobject<USkyLightComponent>(TEXT("SkyLight"));
	SkyLight->SetupAttachment(Root);
	SkyLight->SetMobility(EComponentMobility::Movable);
	SkyLight->bRealTimeCapture = true;
	SkyLight->Intensity = 0.55f;
	SkyLight->LightColor = CoopCave::AmbientTint.ToFColor(true);

	SkyAtmosphere = CreateDefaultSubobject<USkyAtmosphereComponent>(TEXT("SkyAtmosphere"));
	SkyAtmosphere->SetupAttachment(Root);

	// Low haze that sits on the floor
	Fog = CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("Fog"));
	Fog->SetupAttachment(Root);
	Fog->SetMobility(EComponentMobility::Movable);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cylinder(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cone(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShapeMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

	if (Cube.Succeeded())          { CubeMesh = Cube.Object; }
	if (Sphere.Succeeded())        { SphereMesh = Sphere.Object; }
	if (Cylinder.Succeeded())      { CylinderMesh = Cylinder.Object; }
	if (Cone.Succeeded())          { ConeMesh = Cone.Object; }
	if (ShapeMaterial.Succeeded()) { BaseMaterial = ShapeMaterial.Object; }

	// Spots to jump to (number keys / D-pad). Players appear side by side, 3 m apart.
	auto AddStation = [this](const TCHAR* Name, const TCHAR* Status, const FVector& Location, float Yaw)
	{
		FCoopStation& Station = Stations.AddDefaulted_GetRef();
		Station.Name = Name;
		Station.Status = Status;
		Station.Location = Location;
		Station.Yaw = Yaw;
	};
	AddStation(TEXT("Entrance"), TEXT("Small rocks: walk over them. Medium rocks: jump on."), FVector(-600.f, 0.f, 0.f), 0.f);
	AddStation(TEXT("Workbench"), TEXT("The work area."), FVector(480.f, 280.f, 0.f), 0.f);
	AddStation(TEXT("Mine cart"), TEXT("Jump into the cart."), FVector(-280.f, -600.f, 0.f), -90.f);
	AddStation(TEXT("Scaffold"), TEXT("Jump onto the crate, then up onto the platform."), FVector(540.f, 900.f, 0.f), 0.f);
	AddStation(TEXT("Crystals"), TEXT("The glowing corner."), FVector(620.f, -620.f, 0.f), -45.f);

	// The maze, through the door in the north wall. Facing north (+Y) is yaw 90.
	using namespace CoopMaze;
	AddStation(TEXT("Maze fork"), TEXT("Four tunnels: pick a path. They cross on bridges and meet again in two halls."), RoomCenter(Fork), 90.f);
	AddStation(TEXT("Meeting point A"), TEXT("The sunken hall (-3 m) where all four paths meet."), RoomCenter(HallA), 90.f);
	AddStation(TEXT("Meeting point B"), TEXT("The raised hall (+4 m), the second meeting point."), RoomCenter(HallB), 90.f);
	AddStation(TEXT("Relic chamber"), TEXT("The end of the maze (+6 m)."), FVector(TileCenter(FIntPoint(22, Rooms[Goal].R1)), Rooms[Goal].Z * 100.f), 90.f);
}

void ACoopPlayground::BeginPlay()
{
	Super::BeginPlay();

	using namespace CoopCave;
	Random.Initialize(2610);

	WallRocks.Color = WallRock;
	CeilingRocks.Color = CeilingRock;
	CeilingRocks.bCollides = false;
	// The walls and ceiling are huge: skipping their shadows makes the torch shadows much cheaper.
	WallRocks.bCastShadow = false;
	CeilingRocks.bCastShadow = false;
	Boulders.Color = BoulderRock;
	SmallRocks.Color = SmallRock;
	Pebbles.Color = Pebble;
	Pebbles.bCollides = false;
	Pebbles.bCastShadow = false;
	FloorStones.Color = FloorStone;
	FloorStones.bCollides = false;
	FloorStones.bCastShadow = false;
	MazeWallRocks.Color = WallRock;
	MazeWallRocks.bCollides = false;      // the maze has its own invisible walls
	MazeWallRocks.bCastShadow = false;
	MazeCeilingRocks.Color = CeilingRock;
	MazeCeilingRocks.bCollides = false;
	MazeCeilingRocks.bCastShadow = false;

	LoadRepoAssets();
	bMazeDetail = CoopTuning::MazeDetail();

	// Places random rocks must stay out of (cm, with some margin)
	auto Clear = [this](float X0, float Y0, float X1, float Y1) { KeepClearBoxes.Add(FBox2D(FVector2D(X0, Y0), FVector2D(X1, Y1))); };
	for (const FCoopStation& Station : Stations)
	{
		const FVector2D P(Station.Location);
		const FVector2D Side = FVector2D(FRotationMatrix(FRotator(0.f, Station.Yaw, 0.f)).GetUnitAxis(EAxis::Y));
		for (const float Offset : { -150.f, 150.f })
		{
			const FVector2D Spot = P + Side * Offset;
			Clear(Spot.X - 130.f, Spot.Y - 130.f, Spot.X + 130.f, Spot.Y + 130.f);
		}
	}
	Clear(WorkbenchCenter.X - 140.f, WorkbenchCenter.Y - 200.f, WorkbenchCenter.X + 140.f, WorkbenchCenter.Y + 200.f);
	Clear(ScaffoldCenter.X - 380.f, ScaffoldCenter.Y - 200.f, ScaffoldCenter.X + 200.f, ScaffoldCenter.Y + 200.f);
	Clear(RailStartX - 60.f, RailY - 120.f, RailEndX + 120.f, RailY + 120.f);
	Clear(-1180.f, 780.f, -460.f, 1180.f);   // crates and barrels
	Clear(CrystalCorner.X - 320.f, CrystalCorner.Y - 200.f, CrystalCorner.X + 200.f, CrystalCorner.Y + 320.f);
	Clear(DoorMinX - 60.f, 850.f, DoorMaxX + 60.f, 1300.f);   // the way to the maze door
	for (const FVector& T : { StandingTorchA, StandingTorchB })
	{
		Clear(T.X - 80.f, T.Y - 80.f, T.X + 80.f, T.Y + 80.f);
	}

	BuildLighting();
	BuildShell();
	BuildRockWalls();
	BuildTimber();
	BuildTorches();
	BuildWorkArea();
	BuildMineCart();
	BuildCrystals();
	BuildFloorRocks();
	BuildMaze();
	FinishRockGroups();
}

void ACoopPlayground::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UpdateMovers(DeltaSeconds);
	if (UWorld* World = GetWorld())
	{
		ApplyLiveLighting(World->GetTimeSeconds());
	}
}

// ---------------------------------------------------------------------------
// Light, haze and exposure
// ---------------------------------------------------------------------------

void ACoopPlayground::BuildLighting()
{
	Fog->SetFogDensity(CoopTuning::CaveFog());
	Fog->SetFogHeightFalloff(2.f);
	Fog->SetFogInscatteringColor(CoopCave::FogColor);
	Fog->SetDirectionalInscatteringColor(FLinearColor::Black);
	Fog->SetSkyAtmosphereAmbientContributionColorScale(FLinearColor::Black);
	Fog->SetStartDistance(150.f);

	// A fixed exposure, so the dark stays dark instead of the camera brightening it.
	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	PostVolume = GetWorld()->SpawnActor<APostProcessVolume>(APostProcessVolume::StaticClass(), FTransform::Identity, Params);
	if (PostVolume)
	{
		PostVolume->bUnbound = true;
		PostVolume->Priority = 1.f;
		FPostProcessSettings& Settings = PostVolume->Settings;
		Settings.bOverride_AutoExposureMethod = true;
		Settings.AutoExposureMethod = EAutoExposureMethod::AEM_Manual;
		Settings.bOverride_AutoExposureApplyPhysicalCameraExposure = true;
		Settings.AutoExposureApplyPhysicalCameraExposure = 0;
		Settings.bOverride_AutoExposureBias = true;
		Settings.AutoExposureBias = CoopTuning::CaveExposure();
		Settings.bOverride_BloomIntensity = true;
		Settings.BloomIntensity = 0.8f;
		Settings.bOverride_VignetteIntensity = true;
		Settings.VignetteIntensity = 0.55f;
		Settings.bOverride_AmbientOcclusionIntensity = true;
		Settings.AmbientOcclusionIntensity = 0.8f;
		Settings.bOverride_AmbientOcclusionRadius = true;
		Settings.AmbientOcclusionRadius = 150.f;
	}
}

void ACoopPlayground::ApplyLiveLighting(float TimeSeconds)
{
	const float Base = CoopTuning::TorchBrightness();
	const float Flicker = CoopTuning::TorchFlicker();
	const float Bounce = CoopTuning::TorchBounce();
	const float Radius = CoopTuning::TorchRadius();
	const int32 ShadowMode = CoopTuning::TorchShadowMode();

	// Lights past this distance from the camera stop drawing (they fade out over the last quarter).
	const float LightDistance = FMath::Max(0.f, CoopTuning::LightDrawDistance());
	auto ApplyDistance = [LightDistance](UPointLightComponent* Light)
	{
		if (Light && !FMath::IsNearlyEqual(Light->MaxDrawDistance, LightDistance))
		{
			Light->SetMaxDrawDistance(LightDistance);
			Light->SetMaxDistanceFadeRange(LightDistance * 0.25f);
		}
	};

	for (int32 i = 0; i < TorchLights.Num(); ++i)
	{
		const float Phase = TorchPhases.IsValidIndex(i) ? TorchPhases[i] : 0.f;
		const float Wobble =
			0.55f * FMath::Sin(TimeSeconds * 8.3f + Phase) +
			0.30f * FMath::Sin(TimeSeconds * 13.7f + Phase * 1.7f) +
			0.15f * FMath::Sin(TimeSeconds * 23.1f + Phase * 0.6f);
		const float Scale = FMath::Max(0.f, 1.f + Flicker * Wobble);

		if (UPointLightComponent* Light = TorchLights[i])
		{
			Light->SetIntensity(Base * Scale);
			if (!FMath::IsNearlyEqual(Light->AttenuationRadius, Radius))
			{
				Light->SetAttenuationRadius(Radius);
			}
			if (ShadowMode != LastShadowMode)
			{
				Light->SetCastShadows(TorchCastsShadow(TorchIsKey.IsValidIndex(i) && TorchIsKey[i]));
			}
			ApplyDistance(Light);
		}
		if (BounceLights.IsValidIndex(i) && BounceLights[i])
		{
			BounceLights[i]->SetIntensity(Base * Bounce * Scale);
			ApplyDistance(BounceLights[i]);
		}
		if (TorchFlames.IsValidIndex(i) && TorchFlames[i])
		{
			const float Grow = Scale - 1.f;
			TorchFlames[i]->SetRelativeScale3D(FVector(1.f + 0.4f * Grow, 1.f + 0.4f * Grow, 1.f + 1.1f * Grow));
		}
	}
	LastShadowMode = ShadowMode;

	const float Pulse = 1.f + 0.06f * FMath::Sin(TimeSeconds * 1.3f);
	if (CrystalLight)
	{
		CrystalLight->SetIntensity(CoopTuning::CrystalBrightness() * Pulse);
	}
	for (UPointLightComponent* Light : MazeCrystalLights)
	{
		if (Light)
		{
			Light->SetIntensity(CoopTuning::CrystalBrightness() * 0.6f * Pulse);
			ApplyDistance(Light);
		}
	}

	const float Ambient = CoopTuning::CaveAmbient();
	if (SkyLight && !FMath::IsNearlyEqual(SkyLight->Intensity, Ambient))
	{
		SkyLight->SetIntensity(Ambient);
	}
	const float FogDensity = CoopTuning::CaveFog();
	if (Fog && !FMath::IsNearlyEqual(Fog->FogDensity, FogDensity))
	{
		Fog->SetFogDensity(FogDensity);
	}
	if (PostVolume)
	{
		PostVolume->Settings.AutoExposureBias = CoopTuning::CaveExposure();
	}
}

// ---------------------------------------------------------------------------
// Floor, invisible walls, dark backstop
// ---------------------------------------------------------------------------

void ACoopPlayground::BuildShell()
{
	using namespace CoopCave;

	// Sandy floor, top at Z = 0. It only receives shadows.
	if (UStaticMeshComponent* Floor = AddBox(FVector(0.f, 0.f, -20.f), FVector(3400.f, 3400.f, 40.f), Sand))
	{
		Floor->SetCastShadow(false);
	}

	// Invisible walls and lid: nobody leaves the cave through a gap between rocks.
	auto AddBlocker = [this](const FVector& Center, const FVector& HalfExtent)
	{
		UBoxComponent* Box = NewObject<UBoxComponent>(this);
		Box->SetupAttachment(Root);
		Box->SetMobility(EComponentMobility::Static);
		Box->SetBoxExtent(HalfExtent, false);
		Box->SetRelativeLocation(Center);
		Box->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
		Box->SetHiddenInGame(true);
		Box->RegisterComponent();
	};
	const float Wall = Half + 60.f;
	const float Reach = Half + 200.f;
	AddBlocker(FVector(Wall, 0.f, 500.f), FVector(60.f, Reach, 600.f));
	AddBlocker(FVector(-Wall, 0.f, 500.f), FVector(60.f, Reach, 600.f));
	// North wall: either side of the maze door
	AddBlocker(FVector((-Reach + DoorMinX) * 0.5f, Wall, 500.f), FVector((DoorMinX + Reach) * 0.5f, 60.f, 600.f));
	AddBlocker(FVector((DoorMaxX + Reach) * 0.5f, Wall, 500.f), FVector((Reach - DoorMaxX) * 0.5f, 60.f, 600.f));
	AddBlocker(FVector(0.f, -Wall, 500.f), FVector(Reach, 60.f, 600.f));
	AddBlocker(FVector(0.f, 0.f, BlockerCeilingZ + 50.f), FVector(Half + 200.f, Half + 200.f, 50.f));

	// Dark backstop far behind the rock walls, in case a gap shows through.
	// Not to the north, where the maze is: BuildMaze puts one round the whole maze.
	auto AddBackstop = [this](const FVector& Center, const FVector& Size)
	{
		if (UStaticMeshComponent* Box = AddBox(Center, Size, Backstop, false))
		{
			Box->SetCastShadow(false);
		}
	};
	AddBackstop(FVector(2000.f, 0.f, 600.f), FVector(100.f, 4200.f, 1600.f));
	AddBackstop(FVector(-2000.f, 0.f, 600.f), FVector(100.f, 4200.f, 1600.f));
	AddBackstop(FVector(0.f, -2000.f, 600.f), FVector(4200.f, 100.f, 1600.f));
	AddBackstop(FVector(0.f, 0.f, 1450.f), FVector(4200.f, 4200.f, 100.f));
}

// ---------------------------------------------------------------------------
// Rock walls and ceiling
// ---------------------------------------------------------------------------

void ACoopPlayground::BuildRockWalls()
{
	using namespace CoopCave;

	// Side 0 = north (+Y), 1 = south (-Y), 2 = east (+X), 3 = west (-X)
	auto SidePoint = [](int32 Side, float Along, float Out)
	{
		switch (Side)
		{
		case 0:  return FVector(Along, Out, 0.f);
		case 1:  return FVector(Along, -Out, 0.f);
		case 2:  return FVector(Out, Along, 0.f);
		default: return FVector(-Out, Along, 0.f);
		}
	};

	// Rocks that would block the maze door go here and are never built. Building them anyway
	// keeps the random sequence, so the rest of the cave comes out exactly as before.
	FCoopRockGroup DoorGap;

	for (int32 Side = 0; Side < 4; ++Side)
	{
		const float SideYaw = (Side < 2) ? 0.f : 90.f;
		float Along = -Half - 250.f;
		while (Along < Half + 250.f)
		{
			const float Width = Random.FRandRange(380.f, 560.f);
			const float Depth = Random.FRandRange(320.f, 460.f);
			const float Height = Random.FRandRange(430.f, 760.f);
			float Out = Half + Depth * Random.FRandRange(0.12f, 0.3f);

			// On the north and south walls, keep the rock face behind the timber posts, their torches and the plank walls.
			// Same behind the torch panels on the east and west walls.
			const bool bBehindTimber = (Side < 2 && Along > FrameXs[0] - 260.f && Along < FrameXs[2] + 260.f);
			const bool bBehindPanel = (Side == 2 && FMath::Abs(Along + 350.f) < 320.f) || (Side == 3 && FMath::Abs(Along) < 320.f);
			if (bBehindTimber || bBehindPanel)
			{
				Out += 110.f;
			}

			const bool bInDoor = (Side == 0 && Along + Width * 0.6f > DoorMinX - 40.f && Along - Width * 0.6f < DoorMaxX + 40.f);
			FCoopRockGroup& Group = bInDoor ? DoorGap : WallRocks;

			AddRock(Group, SidePoint(Side, Along, Out) + FVector(0.f, 0.f, -40.f), FVector(Width, Depth, Height),
				SideYaw + Random.FRandRange(-18.f, 18.f), 1, 0.22f, 0.25f);

			// Upper tier up to the ceiling
			if (Height < 700.f)
			{
				const float UpperHeight = CeilingZ + 220.f - (Height - 140.f);
				AddRock(Group, SidePoint(Side, Along + Random.FRandRange(-80.f, 80.f), Out + 90.f) + FVector(0.f, 0.f, Height - 140.f),
					FVector(Width * 0.95f, Depth, UpperHeight), SideYaw + Random.FRandRange(-25.f, 25.f), 1, 0.2f, 0.f);
			}
			Along += Width * Random.FRandRange(0.62f, 0.78f);
		}
	}

	// Corners
	for (const FVector2D Corner : { FVector2D(1.0, 1.0), FVector2D(1.0, -1.0), FVector2D(-1.0, 1.0), FVector2D(-1.0, -1.0) })
	{
		AddRock(WallRocks, FVector(Corner.X * (Half + 120.f), Corner.Y * (Half + 120.f), -40.f), FVector(640.f, 640.f, CeilingZ + 200.f),
			Random.FRandRange(0.f, 90.f), 1, 0.2f, 0.f);
	}

	// Ceiling: flipped rocks, so their lumpy side hangs down
	const FRotator UpsideDown(0.f, 0.f, 180.f);
	for (float X = -Half - 100.f; X <= Half + 200.f; X += 620.f)
	{
		for (float Y = -Half - 100.f; Y <= Half + 200.f; Y += 620.f)
		{
			const float Height = Random.FRandRange(260.f, 380.f);
			const FVector Top(X + Random.FRandRange(-80.f, 80.f), Y + Random.FRandRange(-80.f, 80.f), CeilingZ + Height + Random.FRandRange(0.f, 70.f));
			AddRock(CeilingRocks, Top, FVector(Random.FRandRange(780.f, 920.f), Random.FRandRange(780.f, 920.f), Height),
				Random.FRandRange(0.f, 360.f), 1, 0.2f, 0.45f, UpsideDown);
		}
	}

	// Stalactites, kept away from the frame beams
	int32 Placed = 0;
	for (int32 Attempt = 0; Attempt < 60 && Placed < 12; ++Attempt)
	{
		const FVector2D P(Random.FRandRange(-Half + 150.f, Half - 150.f), Random.FRandRange(-Half + 150.f, Half - 150.f));
		bool bNearBeam = false;
		for (const float FrameX : FrameXs)
		{
			bNearBeam |= FMath::Abs(P.X - FrameX) < 120.f;
		}
		if (bNearBeam)
		{
			continue;
		}
		const float Length = Random.FRandRange(110.f, 230.f);
		const float Width = Random.FRandRange(50.f, 110.f);
		AddRock(CeilingRocks, FVector(P.X, P.Y, CeilingZ + 60.f), FVector(Width, Width * Random.FRandRange(0.8f, 1.1f), Length + 60.f),
			Random.FRandRange(0.f, 360.f), 0, 0.25f, 0.f, UpsideDown);
		++Placed;
	}
}

// ---------------------------------------------------------------------------
// Timber: mine frames and plank walls
// ---------------------------------------------------------------------------

void ACoopPlayground::AddMineFrame(float X)
{
	using namespace CoopCave;

	for (const float Sign : { 1.f, -1.f })
	{
		const float Y = Sign * FramePostY;
		AddBox(FVector(X, Y, FrameBeamZ * 0.5f), FVector(PostSize, PostSize, FrameBeamZ), Wood);

		// Iron straps with bolts, like the reference beam
		for (const float Z : { 110.f, 480.f })
		{
			AddBox(FVector(X, Y - Sign * (PostSize * 0.5f + 1.f), Z), FVector(PostSize + 6.f, 4.f, 24.f), Iron, false);
			for (const float BoltX : { -9.f, 9.f })
			{
				AddBox(FVector(X + BoltX, Y - Sign * (PostSize * 0.5f + 4.f), Z), FVector(6.f, 4.f, 6.f), Iron, false);
			}
		}

		// Diagonal brace from the post up to the beam
		AddBeam(FVector(X, Y, FrameBeamZ - 160.f), FVector(X, Y - Sign * 180.f, FrameBeamZ - 6.f), 20.f, 20.f, WoodDark, false);
	}

	// The beam across the room, resting on the posts
	AddBeam(FVector(X, -FramePostY - 60.f, FrameBeamZ + 18.f), FVector(X, FramePostY + 60.f, FrameBeamZ + 18.f), 38.f, 36.f, Wood);
}

void ACoopPlayground::BuildTimber()
{
	using namespace CoopCave;

	for (const float X : FrameXs)
	{
		AddMineFrame(X);
	}

	// Plank walls between frames: north wall (behind the crates) and south wall (behind the rails)
	auto PlankWall = [this](float X0, float X1, float Y, float Height)
	{
		const float BoardWidth = 30.f;
		for (float X = X0; X < X1; X += BoardWidth + 3.f)
		{
			const float BoardHeight = Height + Random.FRandRange(-25.f, 15.f);
			const FLinearColor& Color = (FMath::RoundToInt(X / BoardWidth) % 3 == 0) ? CoopCave::WoodDark : CoopCave::Wood;
			AddBox(FVector(X + BoardWidth * 0.5f, Y, BoardHeight * 0.5f), FVector(BoardWidth, 7.f, BoardHeight), Color);
		}
		// Two cross rails
		for (const float Z : { Height * 0.25f, Height * 0.8f })
		{
			const float Sign = (Y > 0.f) ? -1.f : 1.f;
			AddBox(FVector((X0 + X1) * 0.5f, Y + Sign * 7.f, Z), FVector(X1 - X0, 6.f, 18.f), CoopCave::WoodDark, false);
		}
	};
	PlankWall(FrameXs[0] + 30.f, FrameXs[1] - 30.f, FramePostY + 15.f, 330.f);
	PlankWall(FrameXs[1] + 30.f, FrameXs[2] - 30.f, -FramePostY - 15.f, 300.f);

	// Plank panels on the east and west walls, for their torches
	auto PlankPanel = [this](float X, float Y0, float Y1, float Height)
	{
		const float BoardWidth = 30.f;
		for (float Y = Y0; Y < Y1; Y += BoardWidth + 3.f)
		{
			const float BoardHeight = Height + Random.FRandRange(-25.f, 15.f);
			const FLinearColor& Color = (FMath::RoundToInt(Y / BoardWidth) % 3 == 0) ? CoopCave::WoodDark : CoopCave::Wood;
			AddBox(FVector(X, Y + BoardWidth * 0.5f, BoardHeight * 0.5f), FVector(7.f, BoardWidth, BoardHeight), Color);
		}
		const float Sign = (X > 0.f) ? -1.f : 1.f;
		for (const float Z : { Height * 0.25f, Height * 0.8f })
		{
			AddBox(FVector(X + Sign * 7.f, (Y0 + Y1) * 0.5f, Z), FVector(6.f, Y1 - Y0, 18.f), CoopCave::WoodDark, false);
		}
	};
	PlankPanel(-Half + 150.f, -130.f, 130.f, 330.f);
	PlankPanel(Half - 150.f, -480.f, -220.f, 330.f);
}

// ---------------------------------------------------------------------------
// Torches
// ---------------------------------------------------------------------------

void ACoopPlayground::BuildTorches()
{
	using namespace CoopCave;

	// On the inner face of every frame post. The middle frame's pair are key lights (they cast shadows).
	for (const float X : FrameXs)
	{
		for (const float Sign : { 1.f, -1.f })
		{
			AddWallTorch(FVector(X, Sign * (FramePostY - PostSize * 0.5f), 235.f), FVector(0.f, -Sign, 0.f), X == FrameXs[1]);
		}
	}

	// On the east and west plank panels
	AddWallTorch(FVector(-Half + 160.f, 0.f, 235.f), FVector(1.f, 0.f, 0.f), false);
	AddWallTorch(FVector(Half - 160.f, -350.f, 235.f), FVector(-1.f, 0.f, 0.f), false);

	// Standing torches out in the room
	AddStandingTorch(StandingTorchA);
	AddStandingTorch(StandingTorchB);
}

void ACoopPlayground::AddWallTorch(const FVector& MountPoint, const FVector& WallNormal, bool bKeyLight)
{
	using namespace CoopCave;
	const FVector Up(0.f, 0.f, 1.f);

	// The torch's own parts don't cast shadows: right next to the light they'd throw huge, ugly ones.
	auto NoShadow = [](UStaticMeshComponent* Part) { if (Part) { Part->SetCastShadow(false); } };

	// Iron wall plate and an arm sticking out
	const FRotator PlateRotation = WallNormal.Rotation();
	NoShadow(AddShape(CubeMesh, MountPoint + WallNormal * 2.f, FVector(4.f, 14.f, 22.f), PlateRotation, Iron, false));
	NoShadow(AddBeam(MountPoint, MountPoint + WallNormal * 20.f, 5.f, 5.f, Iron, false));

	// Wooden handle, leaning away from the wall
	const FVector HandleBase = MountPoint + WallNormal * 20.f - Up * 18.f;
	const FVector HandleDir = (Up * FMath::Cos(FMath::DegreesToRadians(22.f)) + WallNormal * FMath::Sin(FMath::DegreesToRadians(22.f))).GetSafeNormal();
	const FVector HandleTop = HandleBase + HandleDir * 48.f;
	NoShadow(AddBeam(HandleBase, HandleTop, 6.f, 6.f, WoodDark, false));
	NoShadow(AddBeam(HandleTop - HandleDir * 4.f, HandleTop + HandleDir * 8.f, 11.f, 11.f, Cloth, false));   // oily rag head
	NoShadow(AddBeam(MountPoint + WallNormal * 18.f - Up * 2.f, MountPoint + WallNormal * 22.f + Up * 2.f, 10.f, 10.f, Iron, false)); // ring

	AddTorchFlameAndLight(HandleTop + HandleDir * 6.f, WallNormal, 40.f, bKeyLight);
}

void ACoopPlayground::AddStandingTorch(const FVector& GroundPoint)
{
	using namespace CoopCave;

	// A pole wedged in a pile of stones
	AddShape(CylinderMesh, GroundPoint + FVector(0.f, 0.f, 95.f), FVector(9.f, 9.f, 190.f), FRotator::ZeroRotator, WoodDark);
	for (int32 i = 0; i < 4; ++i)
	{
		const float Angle = i * 90.f + Random.FRandRange(-20.f, 20.f);
		const FVector Offset = FRotator(0.f, Angle, 0.f).Vector() * 20.f;
		AddRock(SmallRocks, GroundPoint + Offset, FVector(26.f, 22.f, 16.f), Random.FRandRange(0.f, 360.f), 0, 0.2f, 0.5f);
	}
	if (UStaticMeshComponent* Rag = AddShape(CylinderMesh, GroundPoint + FVector(0.f, 0.f, 188.f), FVector(15.f, 15.f, 18.f), FRotator::ZeroRotator, Cloth, false))
	{
		Rag->SetCastShadow(false);
	}

	// Light from a little in front of the flame, toward the room's middle
	const FVector ToMiddle = FVector(-GroundPoint.X, -GroundPoint.Y, 0.f).GetSafeNormal();
	AddTorchFlameAndLight(GroundPoint + FVector(0.f, 0.f, 196.f), ToMiddle, 14.f, true);
}

void ACoopPlayground::AddTorchFlameAndLight(const FVector& FlameBase, const FVector& Outward, float LightOut, bool bKeyLight)
{
	using namespace CoopCave;

	// The flame: a glowing low-poly teardrop, animated in Tick
	FCoopMeshData FlameMesh;
	CoopMeshKit::AddFlame(FlameMesh, FTransform::Identity, 7.5f, 26.f, FlameCore, FlameTip);
	UProceduralMeshComponent* Flame = AddProcMesh(FlameMesh, GlowMaterial(), {}, false, true);
	if (Flame)
	{
		Flame->SetRelativeLocation(FlameBase);
		TorchFlames.Add(Flame);
	}

	// The torch light
	UPointLightComponent* Light = NewObject<UPointLightComponent>(this);
	Light->SetupAttachment(Root);
	Light->SetMobility(EComponentMobility::Movable);
	// A little in front of the flame: a light right against a wall burns a white hot spot into it.
	Light->SetRelativeLocation(FlameBase + Outward * LightOut + FVector(0.f, 0.f, 10.f));
	Light->IntensityUnits = ELightUnits::Candelas;
	Light->SetIntensity(CoopTuning::TorchBrightness());
	Light->SetLightColor(TorchLightColor);
	Light->SetAttenuationRadius(CoopTuning::TorchRadius());
	Light->SetSourceRadius(5.f);
	Light->SetCastShadows(TorchCastsShadow(bKeyLight));
	Light->ShadowResolutionScale = 0.6f;
	Light->RegisterComponent();
	TorchLights.Add(Light);
	TorchIsKey.Add(bKeyLight);
	TorchPhases.Add(Random.FRandRange(0.f, 100.f));

	// Key torches (out in the room) also get a warm "bounce" fill near the floor,
	// faking light bouncing off the ground. Every extra light costs, so the wall torches don't.
	if (!bKeyLight)
	{
		BounceLights.Add(nullptr);
		return;
	}
	UPointLightComponent* BounceLight = NewObject<UPointLightComponent>(this);
	BounceLight->SetupAttachment(Root);
	BounceLight->SetMobility(EComponentMobility::Movable);
	BounceLight->SetRelativeLocation(FlameBase + Outward * 170.f + FVector(0.f, 0.f, -120.f));
	BounceLight->IntensityUnits = ELightUnits::Candelas;
	BounceLight->SetIntensity(CoopTuning::TorchBrightness() * CoopTuning::TorchBounce());
	BounceLight->SetLightColor(BounceLightColor);
	BounceLight->SetAttenuationRadius(500.f);
	BounceLight->SetSourceRadius(80.f);
	BounceLight->SetCastShadows(false);
	BounceLight->SpecularScale = 0.f;
	BounceLight->RegisterComponent();
	BounceLights.Add(BounceLight);
}

bool ACoopPlayground::TorchCastsShadow(bool bKeyLight)
{
	// coop.Cave.TorchShadows: 0 = none, 1 = key torches only, 2 = every torch
	const int32 Mode = CoopTuning::TorchShadowMode();
	return Mode >= 2 || (Mode == 1 && bKeyLight);
}

// ---------------------------------------------------------------------------
// The work area: workbench, crates, barrels, scaffold
// ---------------------------------------------------------------------------

void ACoopPlayground::AddCrate(const FVector& GroundCenter, float Size, float Yaw)
{
	using namespace CoopCave;
	const FRotator Rotation(0.f, Yaw, 0.f);
	const FVector Center = GroundCenter + FVector(0.f, 0.f, Size * 0.5f);
	AddShape(CubeMesh, Center, FVector(Size - 4.f), Rotation, WoodLight);

	// Dark frame: four corner posts and a band round the top and bottom
	const float Edge = Size * 0.12f;
	for (const float SX : { -1.f, 1.f })
	{
		for (const float SY : { -1.f, 1.f })
		{
			const FVector Corner = Rotation.RotateVector(FVector(SX, SY, 0.f) * (Size * 0.5f - Edge * 0.5f + 1.f));
			AddShape(CubeMesh, Center + Corner, FVector(Edge, Edge, Size), Rotation, Wood, false);
		}
	}
	for (const float SZ : { -1.f, 1.f })
	{
		AddShape(CubeMesh, Center + FVector(0.f, 0.f, SZ * (Size * 0.5f - Edge * 0.5f)), FVector(Size + 1.f, Size + 1.f, Edge), Rotation, Wood, false);
	}
}

void ACoopPlayground::AddBarrel(const FVector& GroundCenter)
{
	using namespace CoopCave;
	const float Height = 95.f;
	AddShape(CylinderMesh, GroundCenter + FVector(0.f, 0.f, Height * 0.5f), FVector(64.f, 64.f, Height), FRotator::ZeroRotator, Wood);
	for (const float Z : { 18.f, Height - 18.f })
	{
		AddShape(CylinderMesh, GroundCenter + FVector(0.f, 0.f, Z), FVector(67.f, 67.f, 7.f), FRotator::ZeroRotator, Iron, false);
	}
	AddShape(CylinderMesh, GroundCenter + FVector(0.f, 0.f, Height * 0.5f), FVector(70.f, 70.f, 20.f), FRotator::ZeroRotator, Wood, false); // bulge
}

void ACoopPlayground::BuildWorkArea()
{
	using namespace CoopCave;

	// Workbench: a thick plank top on X-braced trestle legs (like the big wooden piece in the reference)
	{
		const FVector C = WorkbenchCenter;
		AddBox(C + FVector(0.f, 0.f, 89.f), FVector(118.f, 310.f, 12.f), WoodLight);
		for (const float SY : { -1.f, 1.f })
		{
			const float Y = C.Y + SY * 120.f;
			AddBeam(FVector(C.X - 52.f, Y, 0.f), FVector(C.X + 46.f, Y, 84.f), 12.f, 12.f, Wood);
			AddBeam(FVector(C.X + 52.f, Y, 0.f), FVector(C.X - 46.f, Y, 84.f), 12.f, 12.f, Wood);
			AddBox(FVector(C.X, Y, 78.f), FVector(104.f, 14.f, 10.f), WoodDark, false);
		}
		AddBeam(FVector(C.X, C.Y - 120.f, 40.f), FVector(C.X, C.Y + 120.f, 40.f), 10.f, 10.f, WoodDark, false);

		// On the bench: a small crate, a tool box, a hammer
		AddCrate(C + FVector(-5.f, -85.f, 95.f), 46.f, 12.f);
		AddBox(C + FVector(10.f, 55.f, 103.f), FVector(36.f, 60.f, 16.f), Rust, false);
		AddBeam(C + FVector(-30.f, 10.f, 97.f), C + FVector(-28.f, 50.f, 97.f), 4.f, 4.f, WoodDark, false);
		AddBox(C + FVector(-29.f, 52.f, 98.f), FVector(16.f, 7.f, 7.f), Iron, false);

		// A pickaxe leaning on the bench
		const FVector Foot = C + FVector(-80.f, 140.f, 0.f);
		const FVector Top = C + FVector(-64.f, 150.f, 112.f);
		AddBeam(Foot, Top, 6.f, 6.f, WoodDark, false);
		AddBeam(Top + FVector(-6.f, -28.f, -6.f), Top + FVector(-6.f, 30.f, 4.f), 7.f, 6.f, Iron, false);
	}

	// Crates and barrels along the north wall
	AddCrate(FVector(-1010.f, 930.f, 0.f), 100.f, 6.f);
	AddCrate(FVector(-1010.f, 930.f, 100.f), 70.f, -14.f);
	AddCrate(FVector(-880.f, 1010.f, 0.f), 80.f, 24.f);
	AddBarrel(FVector(-760.f, 1000.f, 0.f));
	AddBarrel(FVector(-680.f, 950.f, 0.f));
	AddCrate(FVector(-570.f, 1010.f, 0.f), 60.f, 38.f);

	// Scaffold in the north-east corner, reached from a crate
	{
		const FVector S = ScaffoldCenter;
		const float Deck = ScaffoldHeight;
		AddBox(S + FVector(0.f, 0.f, Deck), FVector(280.f, 280.f, 16.f), WoodLight);
		for (const float SX : { -1.f, 1.f })
		{
			for (const float SY : { -1.f, 1.f })
			{
				AddBox(S + FVector(SX * 125.f, SY * 125.f, Deck * 0.5f), FVector(18.f, 18.f, Deck), Wood);
			}
		}
		// X braces on the open west and south sides
		AddBeam(S + FVector(-125.f, -125.f, 12.f), S + FVector(-125.f, 125.f, Deck - 14.f), 10.f, 10.f, WoodDark, false);
		AddBeam(S + FVector(-125.f, 125.f, 12.f), S + FVector(-125.f, -125.f, Deck - 14.f), 10.f, 10.f, WoodDark, false);
		AddBeam(S + FVector(-125.f, -125.f, 12.f), S + FVector(125.f, -125.f, Deck - 14.f), 10.f, 10.f, WoodDark, false);
		AddBeam(S + FVector(125.f, -125.f, 12.f), S + FVector(-125.f, -125.f, Deck - 14.f), 10.f, 10.f, WoodDark, false);
		// Railing on the wall sides
		const float RailZ = Deck + 8.f + 90.f;
		for (const FVector2D Corner : { FVector2D(125.0, 125.0), FVector2D(125.0, -125.0), FVector2D(-125.0, 125.0) })
		{
			AddBox(S + FVector(Corner.X, Corner.Y, Deck + 8.f + 50.f), FVector(10.f, 10.f, 100.f), Wood);
		}
		AddBeam(S + FVector(125.f, -130.f, RailZ), S + FVector(125.f, 130.f, RailZ), 10.f, 10.f, Wood);
		AddBeam(S + FVector(-130.f, 125.f, RailZ), S + FVector(130.f, 125.f, RailZ), 10.f, 10.f, Wood);
		AddBarrel(S + FVector(60.f, 60.f, Deck + 8.f));

		// The step up
		AddCrate(FVector(S.X - 225.f, S.Y, 0.f), 90.f, 0.f);
	}
}

// ---------------------------------------------------------------------------
// Mine cart on rails
// ---------------------------------------------------------------------------

void ACoopPlayground::BuildMineCart()
{
	using namespace CoopCave;

	// Sleepers (5 cm) and rails (12 cm): low enough to walk over
	for (float X = RailStartX; X <= RailEndX; X += 70.f)
	{
		AddBox(FVector(X, RailY, 2.5f), FVector(18.f, 130.f, 5.f), WoodDark, false);
	}
	const float RailLength = RailEndX - RailStartX + 40.f;
	for (const float SY : { -40.f, 40.f })
	{
		AddBox(FVector((RailStartX + RailEndX) * 0.5f, RailY + SY, 8.5f), FVector(RailLength, 6.f, 7.f), Iron);
	}

	// Buffer stop at the end of the line
	AddBox(FVector(RailEndX + 40.f, RailY, 40.f), FVector(22.f, 150.f, 24.f), Wood);
	for (const float SY : { -60.f, 60.f })
	{
		AddBox(FVector(RailEndX + 52.f, RailY + SY, 30.f), FVector(16.f, 16.f, 60.f), WoodDark);
	}

	// The cart: an open iron box on four wheels
	const FVector Cart(CartX, RailY, 0.f);
	const float FloorZ = 38.f;
	const float WallHeight = 75.f;
	for (const float SX : { -55.f, 55.f })
	{
		for (const float SY : { -44.f, 44.f })
		{
			AddShape(CylinderMesh, Cart + FVector(SX, SY, 18.f), FVector(34.f, 34.f, 8.f), FRotator(0.f, 0.f, 90.f), Iron, false);
		}
	}
	AddBox(Cart + FVector(0.f, 0.f, FloorZ), FVector(170.f, 104.f, 8.f), Rust);
	for (const float SX : { -1.f, 1.f })
	{
		AddBox(Cart + FVector(SX * 81.f, 0.f, FloorZ + WallHeight * 0.5f), FVector(8.f, 110.f, WallHeight), Rust);
	}
	for (const float SY : { -1.f, 1.f })
	{
		AddBox(Cart + FVector(0.f, SY * 51.f, FloorZ + WallHeight * 0.5f), FVector(170.f, 8.f, WallHeight), Rust);
		AddBox(Cart + FVector(0.f, SY * 55.f, FloorZ + WallHeight - 4.f), FVector(176.f, 4.f, 8.f), Iron, false);
	}
	// Ore in the cart
	for (int32 i = 0; i < 6; ++i)
	{
		const FVector P = Cart + FVector(Random.FRandRange(-55.f, 55.f), Random.FRandRange(-30.f, 30.f), FloorZ + 4.f);
		AddRock(Pebbles, P, FVector(Random.FRandRange(30.f, 50.f), Random.FRandRange(28.f, 45.f), Random.FRandRange(25.f, 45.f)), Random.FRandRange(0.f, 360.f), 0, 0.25f, 0.f);
	}
}

// ---------------------------------------------------------------------------
// Crystals: the cool counter-light in the south-east corner
// ---------------------------------------------------------------------------

void ACoopPlayground::BuildCrystals()
{
	using namespace CoopCave;

	FCoopMeshData CrystalMesh;
	TArray<TArray<FVector>> CrystalHulls;

	// A rock bed for them to grow from
	AddRock(Boulders, CrystalCorner + FVector(60.f, -60.f, 0.f), FVector(300.f, 280.f, 70.f), 30.f, 1, 0.2f, 0.6f);

	struct FCrystalSpec { FVector2D Offset; float Radius; float Length; float Tilt; };
	const FCrystalSpec Specs[] = {
		{ FVector2D(40.0, -40.0), 34.f, 230.f, 12.f },
		{ FVector2D(-40.0, -90.0), 26.f, 170.f, 28.f },
		{ FVector2D(90.0, 30.0), 24.f, 160.f, 30.f },
		{ FVector2D(-90.0, -10.0), 20.f, 120.f, 40.f },
		{ FVector2D(10.0, 60.0), 18.f, 110.f, 38.f },
		{ FVector2D(-120.0, -130.0), 14.f, 80.f, 50.f },
		{ FVector2D(120.0, 110.0), 15.f, 85.f, 46.f },
		{ FVector2D(-20.0, -160.0), 12.f, 70.f, 45.f },
	};
	const FVector2D Away = FVector2D(-1.f, 1.f).GetSafeNormal();   // toward the room's middle
	for (const FCrystalSpec& Spec : Specs)
	{
		const FVector2D Spread = (Spec.Offset.GetSafeNormal() + Away * 0.6f).GetSafeNormal();
		const float TiltRad = FMath::DegreesToRadians(Spec.Tilt);
		const FVector Dir = FVector(Spread.X * FMath::Sin(TiltRad), Spread.Y * FMath::Sin(TiltRad), FMath::Cos(TiltRad)).GetSafeNormal();
		const FVector RootPoint = CrystalCorner + FVector(Spec.Offset.X, Spec.Offset.Y, 30.f);
		const FTransform Frame(FRotationMatrix::MakeFromZ(Dir).Rotator(), RootPoint);
		TArray<FVector> Hull = CoopMeshKit::AddCrystal(CrystalMesh, Frame, Spec.Radius, Spec.Length, CrystalRoot, CrystalTip);
		if (Spec.Length > 100.f)
		{
			CrystalHulls.Add(MoveTemp(Hull));
		}
	}

	// A few small ones scattered nearby
	for (int32 i = 0; i < 6; ++i)
	{
		const FVector Root2D = CrystalCorner + FVector(Random.FRandRange(-380.f, -160.f), Random.FRandRange(160.f, 380.f) * (i % 2 ? 1.f : 0.4f), 0.f);
		const FVector Dir = FVector(Random.FRandRange(-0.4f, 0.4f), Random.FRandRange(-0.4f, 0.4f), 1.f).GetSafeNormal();
		CoopMeshKit::AddCrystal(CrystalMesh, FTransform(FRotationMatrix::MakeFromZ(Dir).Rotator(), Root2D),
			Random.FRandRange(5.f, 9.f), Random.FRandRange(25.f, 45.f), CrystalRoot, CrystalTip);
	}

	AddProcMesh(CrystalMesh, GlowMaterial(), CrystalHulls, true);

	CrystalLight = NewObject<UPointLightComponent>(this);
	CrystalLight->SetupAttachment(Root);
	CrystalLight->SetMobility(EComponentMobility::Movable);
	CrystalLight->SetRelativeLocation(CrystalCorner + FVector(-170.f, 170.f, 140.f));
	CrystalLight->IntensityUnits = ELightUnits::Candelas;
	CrystalLight->SetIntensity(CoopTuning::CrystalBrightness());
	CrystalLight->SetLightColor(CrystalLightColor);
	CrystalLight->SetAttenuationRadius(800.f);
	CrystalLight->SetSourceRadius(40.f);
	CrystalLight->SetCastShadows(false);
	CrystalLight->RegisterComponent();
}

// ---------------------------------------------------------------------------
// Rocks on the floor: boulders, medium rocks, small step-over rocks, pebbles
// ---------------------------------------------------------------------------

void ACoopPlayground::BuildFloorRocks()
{
	using namespace CoopCave;

	struct FRockSpec { FVector2D Where; FVector Size; };
	TArray<FVector> Taken;   // X, Y, radius

	// Boulders: too tall to jump onto, they shape the space
	const FRockSpec BigRocks[] = {
		{ FVector2D(-1020.0, 1060.0), FVector(330.0, 300.0, 260.0) },
		{ FVector2D(-830.0, 1130.0), FVector(240.0, 220.0, 170.0) },
		{ FVector2D(-1130.0, 820.0), FVector(260.0, 240.0, 190.0) },
		{ FVector2D(-1100.0, -1110.0), FVector(300.0, 280.0, 230.0) },
		{ FVector2D(160.0, -470.0), FVector(190.0, 170.0, 140.0) },
		{ FVector2D(-260.0, 560.0), FVector(230.0, 200.0, 160.0) },
		{ FVector2D(920.0, -380.0), FVector(210.0, 190.0, 150.0) },
	};
	for (const FRockSpec& Spec : BigRocks)
	{
		AddRock(Boulders, FVector(Spec.Where, 0.f), Spec.Size, Random.FRandRange(0.f, 360.f), 1, 0.22f, 0.35f);
		Taken.Add(FVector(Spec.Where, FMath::Max(Spec.Size.X, Spec.Size.Y) * 0.5f));
	}

	// Medium rocks: jump onto them (50-100 cm)
	const FRockSpec MediumRocks[] = {
		{ FVector2D(-420.0, 300.0), FVector(120.0, 110.0, 70.0) },
		{ FVector2D(-110.0, 470.0), FVector(110.0, 90.0, 55.0) },
		{ FVector2D(380.0, -280.0), FVector(130.0, 120.0, 85.0) },
		{ FVector2D(280.0, 640.0), FVector(100.0, 110.0, 60.0) },
		{ FVector2D(-620.0, -250.0), FVector(110.0, 100.0, 65.0) },
		{ FVector2D(40.0, -720.0), FVector(120.0, 100.0, 75.0) },
		{ FVector2D(-40.0, 880.0), FVector(140.0, 120.0, 95.0) },
	};
	for (const FRockSpec& Spec : MediumRocks)
	{
		AddRock(Boulders, FVector(Spec.Where, 0.f), Spec.Size, Random.FRandRange(0.f, 360.f), 1, 0.2f, 0.65f);
		Taken.Add(FVector(Spec.Where, FMath::Max(Spec.Size.X, Spec.Size.Y) * 0.5f));
	}

	// Small rocks (12-32 cm): you walk straight over these. A few sit right on the path from the entrance.
	auto AddSmallRock = [this, &Taken](const FVector2D& Where, const FVector& Size)
	{
		AddRock(SmallRocks, FVector(Where, 0.f), Size, Random.FRandRange(0.f, 360.f), 0, 0.18f, 0.6f);
		Taken.Add(FVector(Where, FMath::Max(Size.X, Size.Y) * 0.5f));
	};
	AddSmallRock(FVector2D(-330.0, -150.0), FVector(55.0, 50.0, 26.0));   // straight ahead of Player 1
	AddSmallRock(FVector2D(-220.0, 150.0), FVector(50.0, 46.0, 20.0));    // straight ahead of Player 2
	AddSmallRock(FVector2D(-760.0, 70.0), FVector(45.0, 40.0, 20.0));
	AddSmallRock(FVector2D(-140.0, 40.0), FVector(42.0, 46.0, 16.0));
	AddSmallRock(FVector2D(160.0, -40.0), FVector(56.0, 50.0, 30.0));
	AddSmallRock(FVector2D(330.0, 150.0), FVector(40.0, 38.0, 14.0));

	auto IsFree = [this, &Taken](const FVector2D& P, float Radius)
	{
		if (IsKeepClear(P, Radius))
		{
			return false;
		}
		for (const FVector& T : Taken)
		{
			if (FVector2D::Distance(P, FVector2D(T.X, T.Y)) < T.Z + Radius + 25.f)
			{
				return false;
			}
		}
		return true;
	};

	int32 SmallCount = 0;
	for (int32 Attempt = 0; Attempt < 400 && SmallCount < 20; ++Attempt)
	{
		const FVector2D P(Random.FRandRange(-1050.f, 1050.f), Random.FRandRange(-1000.f, 1000.f));
		const FVector Size(Random.FRandRange(30.f, 70.f), Random.FRandRange(28.f, 60.f), Random.FRandRange(12.f, 32.f));
		if (!IsFree(P, Size.X * 0.5f))
		{
			continue;
		}
		AddSmallRock(P, Size);
		++SmallCount;
	}

	// Pebbles: decoration only, no collision
	for (int32 i = 0; i < 170; ++i)
	{
		const FVector2D P(Random.FRandRange(-1150.f, 1150.f), Random.FRandRange(-1150.f, 1150.f));
		if (IsKeepClear(P, 0.f) && Random.FRand() < 0.7f)
		{
			continue;
		}
		const float Width = Random.FRandRange(5.f, 15.f);
		AddRock(Pebbles, FVector(P, 0.f), FVector(Width, Width * Random.FRandRange(0.6f, 1.f), Width * Random.FRandRange(0.4f, 0.7f)),
			Random.FRandRange(0.f, 360.f), 0, 0.3f, 0.f);
	}

	// Flat stones set into the sand
	for (int32 i = 0; i < 14; ++i)
	{
		const FVector2D P(Random.FRandRange(-1050.f, 1050.f), Random.FRandRange(-1050.f, 1050.f));
		const float Width = Random.FRandRange(60.f, 150.f);
		AddRock(FloorStones, FVector(P, -1.f), FVector(Width, Width * Random.FRandRange(0.6f, 0.9f), Random.FRandRange(3.f, 5.f)),
			Random.FRandRange(0.f, 360.f), 0, 0.15f, 0.9f);
	}
}

// ---------------------------------------------------------------------------
// The maze: four paths that cross on bridges, climb and drop, and meet in two halls
// ---------------------------------------------------------------------------

void ACoopPlayground::LoadRepoAssets()
{
	// The shared style kit lives in the main CoopGame project (Content/Shared/Style). To use it here, migrate
	// these three assets into this project's Content folder; they keep the same /Game/Shared/Style path.
	// Until then the maze uses code-built rocks and a flat gold color.
	using CoopMaze::LoadIfPresent;
	RepoRockMesh = LoadIfPresent<UStaticMesh>(TEXT("/Game/Shared/Style/SM_StyleTest_Rock"), TEXT("/Game/Shared/Style/SM_StyleTest_Rock.SM_StyleTest_Rock"));
	RepoRockMaterial = LoadIfPresent<UMaterialInterface>(TEXT("/Game/Shared/Style/MI_Stylized_Rock"), TEXT("/Game/Shared/Style/MI_Stylized_Rock.MI_Stylized_Rock"));
	RepoGoldMaterial = LoadIfPresent<UMaterialInterface>(TEXT("/Game/Shared/Style/MI_Stylized_Gold"), TEXT("/Game/Shared/Style/MI_Stylized_Gold.MI_Stylized_Gold"));
	UE_LOG(LogTemp, Display, TEXT("CoopPlayground: repo rock mesh %s, rock material %s, gold material %s"),
		RepoRockMesh ? TEXT("found") : TEXT("missing (using code-built rocks)"),
		RepoRockMaterial ? TEXT("found") : TEXT("missing"),
		RepoGoldMaterial ? TEXT("found") : TEXT("missing"));
}

void ACoopPlayground::AddMazeRock(bool bCeiling, const FVector& Center, const FVector& Size, float Yaw)
{
	if (RepoRockMesh)
	{
		// Scale the mesh to the wanted size and put its middle on Center. Ceiling rocks hang upside down.
		const FBox Bounds = RepoRockMesh->GetBoundingBox();
		const FVector MeshSize = Bounds.GetSize().ComponentMax(FVector(1.f));
		const FVector Scale = Size / MeshSize;
		const FQuat Rotation(FRotator(0.f, Yaw, bCeiling ? 180.f : 0.f));
		const FVector Location = Center - Rotation.RotateVector(Bounds.GetCenter() * Scale);
		(bCeiling ? MazeCeilingRockTransforms : MazeWallRockTransforms).Add(FTransform(Rotation, Location, Scale));
		return;
	}
	if (bCeiling)
	{
		AddRock(MazeCeilingRocks, Center + FVector(0.f, 0.f, Size.Z * 0.5f), Size, Yaw, 0, 0.22f, 0.3f, FRotator(0.f, 0.f, 180.f));
	}
	else
	{
		AddRock(MazeWallRocks, Center - FVector(0.f, 0.f, Size.Z * 0.5f), Size, Yaw, 0, 0.22f, 0.25f);
	}
}

// ---------------------------------------------------------------------------
// The maze's detail pass (coop.Maze.Detail): dressing that breaks up the uniform tunnels and rooms
// ---------------------------------------------------------------------------

namespace CoopMazeDetail
{
	using namespace CoopMaze;

	// Across a path tile, from its middle (cm). The walls' rocks face the tunnel at about WallFace.
	constexpr float Lane = 125.f;           // the clear walking lane: nothing in it but the floor
	constexpr float BandIn = 145.f;         // anything you can bump into stays at least this far from the middle
	constexpr float WallFace = 218.f;
	constexpr float Clearance = 260.f;      // nothing you can see hangs lower than this over the walking lane
	constexpr float RouteClear = 175.f;     // half the clear route from each of a room's ways in to its middle
	constexpr float AltarClear = 650.f;     // the relic chamber's altar and relics
	constexpr float StationClear = 130.f;   // round each player's spot at a station

	/**
	 * The co-op moments' tiles (CoopMaze::Moments in the mechanics pass). Their pieces use the whole 5 m width and their
	 * boosts need the air up to MomentHeadroom, so these tiles get no dressing at all, and nothing hangs lower than
	 * MomentHeadroom on the tiles next to them. Path is 0-3.
	 */
	struct FPathTile { int32 Path, Col, Row; };
	const FPathTile MomentTiles[] = {
		{ 0, 24, 19 },                                                                   // path 1: boost wall
		{ 1, 21, 7 }, { 1, 21, 6 },                                                      // path 2: winch lift
		{ 2, 31, 34 }, { 2, 32, 34 }, { 2, 33, 34 }, { 2, 34, 34 }, { 2, 35, 34 },       // path 3: split tunnels
		{ 3, 10, 0 }, { 3, 10, -1 },                                                     // path 4: dip gate
	};
	constexpr float MomentHeadroom = 360.f;

	/** 0 = a moment's tile, 1 = next to one (sides or corners), 2 = neither. */
	int32 MomentDistance(int32 Path, const FIntPoint& At)
	{
		int32 Best = 2;
		for (const FPathTile& M : MomentTiles)
		{
			if (M.Path == Path)
			{
				Best = FMath::Min(Best, FMath::Max(FMath::Abs(M.Col - At.X), FMath::Abs(M.Row - At.Y)));
			}
		}
		return Best;
	}

	/** A smooth wave, -1..1, so a tunnel narrows and widens over a few tiles rather than tile by tile. */
	float Wave(float S, float Seed)
	{
		return 0.6f * FMath::Sin(S * 0.83f + Seed) + 0.4f * FMath::Sin(S * 2.17f + Seed * 1.7f);
	}

	float DistToSegment(const FVector2D& P, const FVector2D& A, const FVector2D& B)
	{
		const FVector2D AB = B - A;
		const float T = FMath::Clamp(FVector2D::DotProduct(P - A, AB) / FMath::Max(AB.SizeSquared(), 1.f), 0.f, 1.f);
		return FVector2D::Distance(P, A + AB * T);
	}

	FLinearColor Shade(const FLinearColor& C, float S)
	{
		return FLinearColor(C.R * S, C.G * S, C.B * S, 1.f);
	}

	FQuat Upright(float Yaw)
	{
		return FQuat(FRotator(0.f, Yaw, 0.f));
	}

	/** Upside down: the rock's base is its top, and it hangs from there. */
	FQuat Hanging(float Yaw)
	{
		return FQuat(FRotator(0.f, 0.f, 180.f)) * FQuat(FRotator(0.f, Yaw, 0.f));
	}
}

void ACoopPlayground::BuildMazeDetail(const TMap<FIntPoint, TArray<CoopMaze::FLevel>>& Cells, FCoopMeshData& Glow)
{
	using namespace CoopMazeDetail;
	if (!bMazeDetail)
	{
		return;
	}
	DetailRandom.Initialize(4417);
	FRandomStream& Rand = DetailRandom;
	const FIntPoint Dirs[4] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1) };
	const FVector Up(0.f, 0.f, 1.f);

	// Everything you see goes into a few shared meshes per 40 m square of the maze (one draw each, and off-screen squares
	// aren't drawn), with no shadows. Everything you can bump into also gets a convex shape in one hidden collision mesh.
	struct FKind
	{
		FLinearColor Color;
		TMap<FIntPoint, FCoopMeshData> Chunks;
		FCoopMeshData& At(const FVector& Where)
		{
			constexpr float ChunkSize = 4000.f;
			return Chunks.FindOrAdd(FIntPoint(FMath::FloorToInt(Where.X / ChunkSize), FMath::FloorToInt(Where.Y / ChunkSize)));
		}
	};
	FKind DWall, DCeiling, DBoulders, DSmall, DPebbles, DStones, DPuddles;
	DWall.Color = MazeWallRocks.Color;
	DCeiling.Color = MazeCeilingRocks.Color;
	DBoulders.Color = Shade(MazeWallRocks.Color, 1.15f);
	DSmall.Color = Shade(MazeWallRocks.Color, 0.9f);
	DPebbles.Color = Shade(MazeWallRocks.Color, 0.55f);
	DStones.Color = Shade(MazeWallRocks.Color, 0.75f);
	DPuddles.Color = FLinearColor(0.006f, 0.008f, 0.011f);
	FKind Wood, WoodDark;
	Wood.Color = CoopCave::Wood;
	WoodDark.Color = CoopCave::WoodDark;
	FCoopMeshData BlockerMesh;
	TArray<TArray<FVector>> BlockerHulls;
	TArray<FTransform> RepoRocks;
	int32 Colliders = 0;

	auto Collide = [&](TArray<FVector>&& Hull)
	{
		const FBox Box(Hull);
		TArray<TArray<FVector>> Unused;
		AddBlock(BlockerMesh, Unused, FTransform(Box.GetCenter()), Box.GetExtent());
		BlockerHulls.Add(MoveTemp(Hull));
		++Colliders;
	};
	// A rock standing on (or, Hanging, hanging from) Base. Large rocks use the repo rock mesh when it's in the project.
	auto Rock = [&](FKind& Kind, const FVector& Base, const FVector& Size, const FQuat& Rotation, bool bCollides,
		bool bLarge = false, float TopFlat = 0.3f, int32 Detail = 0)
	{
		const bool bRepo = bLarge && RepoRockMesh;
		FCoopMeshData Unseen;
		TArray<FVector> Hull = CoopMeshKit::AddRock(bRepo ? Unseen : Kind.At(Base), Rand, FTransform(Rotation, Base), Size, Detail, 0.22f, TopFlat);
		if (bRepo)
		{
			// As AddMazeRock: scale the mesh to the size and put its middle where the code-built rock's would be
			const FBox Bounds = RepoRockMesh->GetBoundingBox();
			const FVector Scale = Size / Bounds.GetSize().ComponentMax(FVector(1.f));
			const FVector Middle = FTransform(Rotation, Base).TransformPosition(FVector(0.f, 0.f, Size.Z * 0.5f));
			RepoRocks.Add(FTransform(Rotation, Middle - Rotation.RotateVector(Bounds.GetCenter() * Scale), Scale));
		}
		if (bCollides)
		{
			Collide(MoveTemp(Hull));
		}
	};
	// A stalactite or stalagmite: a six-sided spike from Base along Dir
	auto Spike = [&](FKind& Kind, const FVector& Base, const FVector& Dir, float Radius, float Length, bool bCollides)
	{
		TArray<FVector> Hull = CoopMeshKit::AddCrystal(Kind.At(Base), FTransform(FRotationMatrix::MakeFromZ(Dir).Rotator(), Base),
			Radius, Length, FColor::White, FColor::White);
		if (bCollides)
		{
			Collide(MoveTemp(Hull));
		}
	};
	// A pebble: a low four-sided pyramid (4 faces; there are thousands, so they stay cheaper than a rock)
	auto Pebble = [&](const FVector& Base, float Width)
	{
		FCoopMeshData& Mesh = DPebbles.At(Base);
		const float Turn = Rand.FRandRange(0.f, 0.5f * PI);
		FVector Corners[4];
		for (int32 c = 0; c < 4; ++c)
		{
			const float Angle = Turn + c * 0.5f * PI + Rand.FRandRange(-0.3f, 0.3f);
			Corners[c] = Base + FVector(FMath::Cos(Angle), FMath::Sin(Angle), 0.f) * Width * 0.5f * Rand.FRandRange(0.6f, 1.f);
		}
		const FVector Top = Base + FVector(Rand.FRandRange(-0.15f, 0.15f) * Width, Rand.FRandRange(-0.15f, 0.15f) * Width, Width * Rand.FRandRange(0.35f, 0.6f));
		for (int32 c = 0; c < 4; ++c)
		{
			const FVector& A = Corners[c];
			const FVector& B = Corners[(c + 1) % 4];
			Mesh.AddTriangle(A, B, Top, (A + B) * 0.5f - Base + FVector(0.f, 0.f, Width * 0.2f));
		}
	};
	// Glowing teal crystals growing from Base, leaning along Axis
	auto Crystals = [&](const FVector& Base, const FVector& Axis, const FVector& Spread, int32 Count, float Scale, bool bCollides)
	{
		for (int32 k = 0; k < Count; ++k)
		{
			const FVector At = Base + Spread * Rand.FRandRange(-1.f, 1.f);
			const FVector Dir = (Axis + Spread.GetSafeNormal() * Rand.FRandRange(-0.35f, 0.35f) + Up * Rand.FRandRange(-0.15f, 0.25f)).GetSafeNormal();
			TArray<FVector> Hull = CoopMeshKit::AddCrystal(Glow, FTransform(FRotationMatrix::MakeFromZ(Dir).Rotator(), At),
				Rand.FRandRange(8.f, 16.f) * Scale, Rand.FRandRange(45.f, 100.f) * Scale, CoopCave::CrystalRoot, CoopCave::CrystalTip);
			if (bCollides)
			{
				Collide(MoveTemp(Hull));
			}
		}
	};
	// Old mine timber: a square beam from A to B
	auto Timber = [&](FKind& Kind, const FVector& A, const FVector& B, float Width, bool bCollides)
	{
		const FVector Span = B - A;
		TArray<TArray<FVector>> Hull;
		AddBlock(Kind.At(A), Hull, FTransform(Span.Rotation(), (A + B) * 0.5f), FVector(Span.Size() * 0.5f, Width * 0.5f, Width * 0.5f));
		if (bCollides)
		{
			Collide(MoveTemp(Hull[0]));
		}
	};

	// What must stay clear: torches and crystal markers on the walls, and the players' spots at every station
	TArray<FVector> WallFixtures(MazeWallMarkers);
	for (const UPointLightComponent* Light : TorchLights)
	{
		if (Light)
		{
			WallFixtures.Add(Light->GetRelativeLocation());
		}
	}
	auto NearFixture = [&WallFixtures](const FVector& At, float Radius)
	{
		for (const FVector& F : WallFixtures)
		{
			if (FVector::Dist2D(F, At) < Radius && FMath::Abs(F.Z - At.Z) < 450.f)
			{
				return true;
			}
		}
		return false;
	};
	TArray<FVector> StationSpots;
	for (const FCoopStation& Station : Stations)
	{
		const FVector Side = FRotationMatrix(FRotator(0.f, Station.Yaw, 0.f)).GetUnitAxis(EAxis::Y);
		StationSpots.Add(Station.Location - Side * 150.f);
		StationSpots.Add(Station.Location + Side * 150.f);
	}
	auto NearStation = [&StationSpots](const FVector2D& At, float Z, float Radius)
	{
		for (const FVector& S : StationSpots)
		{
			if (FVector2D::Distance(FVector2D(S), At) < StationClear + Radius && FMath::Abs(S.Z - Z) < 300.f)
			{
				return true;
			}
		}
		return false;
	};

	auto Neighbour = [&Cells](const FIntPoint& At, const FLevel& Level, const FIntPoint& Dir) -> const FLevel*
	{
		if (const TArray<FLevel>* Next = Cells.Find(At + Dir))
		{
			for (const FLevel& Other : *Next)
			{
				if (Connected(Level, Other))
				{
					return &Other;
				}
			}
		}
		return nullptr;
	};
	// The floor under a point of a tile. On ramps, the lower of the two slabs that can be under it, so nothing floats.
	auto FloorAt = [&](const FIntPoint& At, const FLevel& Level, const FVector2D& Point)
	{
		if (Level.Owner >= RoomOwner)
		{
			return Level.Z;
		}
		const FVector2D Local = Point - TileCenter(At);
		float Slope = TNumericLimits<float>::Lowest();
		for (const FIntPoint& Dir : Dirs)
		{
			if (const FLevel* Next = Neighbour(At, Level, Dir))
			{
				const FVector W = WorldDir(Dir);
				const float T = FVector2D::DotProduct(Local, FVector2D(W.X, W.Y)) / Tile;
				if (T >= 0.f)
				{
					Slope = FMath::Max(Slope, Level.Z + (Next->Z - Level.Z) * T);
				}
			}
		}
		return (Slope == TNumericLimits<float>::Lowest()) ? Level.Z : FMath::Min(Slope, Level.Z);
	};

	// Dressing along one wall edge of a tile, in its own frame: N across from the tile's middle toward the wall, A along it.
	struct FEdge
	{
		FVector2D Center;
		FVector2D Out;
		FVector2D Along;
		FVector2D At(float N, float A) const { return Center + Out * N + Along * A; }
	};
	auto ScatterPebbles = [&](const FEdge& E, const FIntPoint& At, const FLevel& Level, int32 Count, float NearN, float FarN)
	{
		for (int32 i = 0; i < Count; ++i)
		{
			const FVector2D P = E.At(Rand.FRandRange(NearN, FarN), Rand.FRandRange(-235.f, 235.f));
			Pebble(FVector(P, FloorAt(At, Level, P) - 1.f), Rand.FRandRange(5.f, 15.f));
		}
	};
	auto SmallRock = [&](const FVector2D& P, const FIntPoint& At, const FLevel& Level)
	{
		// 12-40 cm: you walk straight over these, so they need no collision
		const FVector Size(Rand.FRandRange(25.f, 60.f), Rand.FRandRange(22.f, 50.f), Rand.FRandRange(12.f, 40.f));
		Rock(DSmall, FVector(P, FloorAt(At, Level, P) - 3.f), Size, Upright(Rand.FRandRange(0.f, 360.f)), false, false, 0.6f);
	};
	auto MediumRock = [&](const FVector2D& P, float Height, const FIntPoint& At, const FLevel& Level)
	{
		const FVector Size(Height * Rand.FRandRange(1.4f, 1.9f), Height * Rand.FRandRange(1.2f, 1.6f), Height);
		Rock(DBoulders, FVector(P, FloorAt(At, Level, P) - 5.f), Size, Upright(Rand.FRandRange(0.f, 360.f)), true, false, 0.65f);
	};
	auto FloorStone = [&](const FVector2D& P, const FIntPoint& At, const FLevel& Level, float Width)
	{
		Rock(DStones, FVector(P, FloorAt(At, Level, P) - 2.f), FVector(Width, Width * Rand.FRandRange(0.55f, 0.9f), Rand.FRandRange(3.f, 6.f)),
			Upright(Rand.FRandRange(0.f, 360.f)), false, false, 0.9f);
	};
	auto Puddle = [&](const FVector2D& P, float Z)
	{
		Rock(DPuddles, FVector(P, Z - 0.5f), FVector(Rand.FRandRange(110.f, 220.f), Rand.FRandRange(60.f, 110.f), 2.f),
			Upright(Rand.FRandRange(0.f, 360.f)), false, false, 1.f);
	};
	auto Stalagmites = [&](const FVector2D& P, float Z, int32 Count, float MaxLength, float Spread)
	{
		for (int32 k = 0; k < Count; ++k)
		{
			const FVector2D At = P + FVector2D(Rand.FRandRange(-Spread, Spread), Rand.FRandRange(-Spread, Spread));
			const FVector Dir = (Up + FVector(Rand.FRandRange(-0.08f, 0.08f), Rand.FRandRange(-0.08f, 0.08f), 0.f)).GetSafeNormal();
			Spike(DBoulders, FVector(At, Z - 10.f), Dir, Rand.FRandRange(14.f, 30.f), Rand.FRandRange(60.f, MaxLength), true);
		}
	};
	// Rock standing out from a wall: its face Depth in from WallFace, Width along the wall, from the floor up Height
	auto Bulge = [&](const FEdge& E, const FIntPoint& At, const FLevel& Level, float A, float Width, float Depth, float Height)
	{
		constexpr float Thick = 200.f;
		// The rock's middle sits back so its face, turned up to 8 degrees off the wall, stays Depth in
		const float N = WallFace - Depth + Thick * 0.5f + Width * 0.5f * FMath::Sin(FMath::DegreesToRadians(8.f)) + 8.f;
		float Ground = TNumericLimits<float>::Max();
		for (const float Side : { -0.5f, 0.f, 0.5f })
		{
			Ground = FMath::Min(Ground, FloorAt(At, Level, E.At(N - Thick * 0.5f, A + Side * Width)));
		}
		const float Yaw = FVector(E.Along, 0.f).Rotation().Yaw + Rand.FRandRange(-8.f, 8.f);
		Rock(DWall, FVector(E.At(N, A), Ground - 40.f), FVector(Width, Thick, Height + 40.f), Upright(Yaw), true, true);
	};

	// -----------------------------------------------------------------------
	// The paths
	// -----------------------------------------------------------------------
	const float Seeds[4] = { 0.4f, 1.9f, 3.1f, 4.6f };
	for (const TPair<FIntPoint, TArray<FLevel>>& Cell : Cells)
	{
		const FIntPoint At = Cell.Key;
		const FVector2D Center = TileCenter(At);
		for (const FLevel& Level : Cell.Value)
		{
			const int32 Path = Level.Owner;
			if (Path >= RoomOwner)
			{
				continue;   // the rooms come below
			}
			const FLevel* Next[4];
			int32 OpenCount = 0;
			for (int32 d = 0; d < 4; ++d)
			{
				Next[d] = Neighbour(At, Level, Dirs[d]);
				OpenCount += Next[d] ? 1 : 0;
			}
			const bool bStraight = OpenCount == 2 && ((Next[0] && Next[1]) || (Next[2] && Next[3]));
			const bool bCorner = OpenCount == 2 && !bStraight;
			const bool bTip = OpenCount == 1;
			const bool bMouth = Level.LinkOwner != INDEX_NONE;
			if (MomentDistance(Path, At) == 0)
			{
				continue;   // a co-op moment: no dressing at all
			}
			const bool bNearMoment = MomentDistance(Path, At) == 1;
			// A station's spots on a path (the co-op moments have them) take nothing you could land on
			const bool bMoment = bNearMoment || NearStation(Center, Level.Z, 250.f);
			const bool bFlat = Level.FloorMax - Level.FloorMin < 1.f;
			const float Ceiling = Level.FloorMax + Level.Headroom;   // the invisible lid; under a bridge, the deck's underside
			const bool bOpenUp = bCorner || OpenCount >= 3 || bMouth;   // corners and junctions keep the full height
			const bool bCollapsed = (Path == 3 && At.X <= 9 && At.Y >= 13 && At.Y <= 21);   // the Long haul's caved-in stretch
			const bool bTimber = (Path == 0 && bStraight && !Level.bBridge && !Level.bUnderBridge && Level.Z < 150.f && (At.X + At.Y) % 3 == 0);
			const bool bSolid = !Level.bBridge && !bMouth && !bMoment;   // may take dressing you bump into
			const float RunS = (Center.X + Center.Y) / Tile;

			// Walls: each edge with no neighbour
			for (int32 d = 0; d < 4; ++d)
			{
				if (Next[d])
				{
					continue;
				}
				const FVector Out3 = WorldDir(Dirs[d]);
				const FEdge E{ Center, FVector2D(Out3.X, Out3.Y), FVector2D(-Out3.Y, Out3.X) };
				if (Level.bBridge)
				{
					// A rocky lip along the bridge's edge, low enough to walk over
					for (float A = -230.f; A <= 230.f; A += Rand.FRandRange(45.f, 70.f))
					{
						const FVector2D P = E.At(Rand.FRandRange(195.f, 225.f), A);
						Rock(DSmall, FVector(P, Level.Z - 4.f), FVector(Rand.FRandRange(40.f, 75.f), Rand.FRandRange(35.f, 60.f), Rand.FRandRange(20.f, 40.f)),
							Upright(Rand.FRandRange(0.f, 360.f)), false, false, 0.5f);
					}
					ScatterPebbles(E, At, Level, 4, 170.f, 225.f);
					continue;
				}

				const float S = ((Dirs[d].Y != 0) ? Center.X : Center.Y) / Tile;
				const float W = Wave(S, Seeds[Path] + d * 0.7f);
				const bool bClearWall = !NearFixture(FVector(E.At(WallFace, 0.f), Level.Z + 150.f), 330.f);
				float Depth = 0.f;   // how far the wall stands in here
				if (bSolid && bClearWall && !bTimber)
				{
					if (W > 0.2f)
					{
						// The tunnel narrows: rock stands out from the wall
						Depth = FMath::Lerp(25.f, WallFace - BandIn, FMath::Min(1.f, (W - 0.2f) / 0.6f));
						Bulge(E, At, Level, Rand.FRandRange(-40.f, 40.f), Rand.FRandRange(330.f, 430.f), Depth, Rand.FRandRange(230.f, 380.f));
						if (!bNearMoment && Rand.FRand() < 0.5f)
						{
							// and leans out over you higher up
							const float Height = Rand.FRandRange(160.f, 230.f);
							const float N = WallFace - Depth - 30.f + 90.f;
							Rock(DWall, FVector(E.At(N, Rand.FRandRange(-80.f, 80.f)), Ceiling + 40.f), FVector(Rand.FRandRange(260.f, 340.f), 180.f, Height),
								Hanging(FVector(E.Along, 0.f).Rotation().Yaw + Rand.FRandRange(-8.f, 8.f)), true, true);
						}
					}
					else if (W < -0.45f && Rand.FRand() < 0.6f)
					{
						// A shallow niche: rock stands out either side of the middle of the edge
						for (const float Sign : { -1.f, 1.f })
						{
							Bulge(E, At, Level, Sign * Rand.FRandRange(175.f, 200.f), Rand.FRandRange(150.f, 190.f), WallFace - BandIn - Rand.FRandRange(0.f, 10.f),
								Rand.FRandRange(300.f, 420.f));
						}
						if (Path == 2)
						{
							Crystals(FVector(E.At(WallFace - 15.f, 0.f), FloorAt(At, Level, E.At(WallFace - 15.f, 0.f))), -FVector(E.Out, 0.f) + Up * 1.4f,
								FVector(E.Along, 0.f) * 60.f, 4, 1.1f, true);
						}
						else
						{
							SmallRock(E.At(Rand.FRandRange(175.f, 205.f), Rand.FRandRange(-60.f, 60.f)), At, Level);
						}
					}
					else if (!bNearMoment && Rand.FRand() < 0.25f)
					{
						// An overhang high up the wall
						const float Height = Rand.FRandRange(170.f, 240.f);
						Rock(DWall, FVector(E.At(WallFace - 20.f, Rand.FRandRange(-100.f, 100.f)), Ceiling + 40.f), FVector(Rand.FRandRange(280.f, 380.f), 200.f, Height),
							Hanging(FVector(E.Along, 0.f).Rotation().Yaw + Rand.FRandRange(-8.f, 8.f)), true, true);
					}
				}
				const float Face = WallFace - Depth;

				// The floor along the wall
				ScatterPebbles(E, At, Level, Rand.RandRange(4, 9), BandIn, Face + 10.f);
				for (int32 k = Rand.RandRange(0, 2); k > 0; --k)
				{
					SmallRock(E.At(Rand.FRandRange(BandIn + 20.f, Face + 10.f), Rand.FRandRange(-220.f, 220.f)), At, Level);
				}
				if (Rand.FRand() < 0.35f)
				{
					FloorStone(E.At(Rand.FRandRange(BandIn + 40.f, Face - 20.f), Rand.FRandRange(-180.f, 180.f)), At, Level, Rand.FRandRange(60.f, 110.f));
				}
				if (Level.Z <= -150.f && bFlat && Rand.FRand() < 0.3f)
				{
					Puddle(E.At(Rand.FRandRange(BandIn + 40.f, 185.f), Rand.FRandRange(-150.f, 150.f)), Level.Z);
				}
				if (bSolid && bClearWall && !bTimber && Depth < 30.f)
				{
					const float Roll = Rand.FRand();
					if (bCollapsed || Roll < 0.16f)
					{
						const float Height = Rand.FRandRange(50.f, 95.f);
						MediumRock(E.At(FMath::Max(BandIn + Height * 0.95f + 12.f, Face - 20.f), Rand.FRandRange(-170.f, 170.f)), Height, At, Level);
					}
					else if (Roll < 0.3f && Path != 2)
					{
						const FVector2D P = E.At(Rand.FRandRange(195.f, 215.f), Rand.FRandRange(-170.f, 170.f));
						Stalagmites(P, FloorAt(At, Level, P), Rand.RandRange(1, 3), 210.f, 25.f);
					}
				}

				// Per path: more crystals on the Crystal run, rubble where the Long haul caved in
				if (Path == 2 && bClearWall && Rand.FRand() < 0.6f)
				{
					const float A = Rand.FRandRange(-170.f, 170.f);
					if (Rand.FRand() < 0.5f && bSolid && Depth < 30.f)
					{
						const FVector2D P = E.At(Face - 12.f, A);
						Crystals(FVector(P, FloorAt(At, Level, P) - 5.f), -FVector(E.Out, 0.f) * 0.45f + Up, FVector(E.Along, 0.f) * 55.f, Rand.RandRange(3, 5), 0.9f, true);
					}
					else
					{
						const FVector2D P = E.At(Face + 5.f, A);
						Crystals(FVector(P, FloorAt(At, Level, P) + Rand.FRandRange(230.f, 380.f)), -FVector(E.Out, 0.f) + Up * 0.2f, FVector(E.Along, 0.f) * 50.f,
							Rand.RandRange(2, 4), 0.7f, false);
					}
				}
				if (bCollapsed && bSolid)
				{
					for (int32 k = Rand.RandRange(3, 6); k > 0; --k)
					{
						SmallRock(E.At(Rand.FRandRange(BandIn + 15.f, Face), Rand.FRandRange(-230.f, 230.f)), At, Level);
					}
					ScatterPebbles(E, At, Level, 8, BandIn, Face);
					if (bClearWall && Rand.FRand() < 0.5f)
					{
						// A slab fallen from the roof, leaning on the wall
						const FVector2D P = E.At(BandIn + 40.f, Rand.FRandRange(-120.f, 120.f));
						const FQuat Lean = FQuat(FVector(E.Along, 0.f), FMath::DegreesToRadians(Rand.FRandRange(18.f, 30.f))) * Upright(FVector(E.Out, 0.f).Rotation().Yaw);
						Rock(DBoulders, FVector(P, FloorAt(At, Level, P) - 10.f), FVector(55.f, Rand.FRandRange(220.f, 300.f), Rand.FRandRange(230.f, 300.f)), Lean, true, false, 0.2f);
					}
					if (Rand.FRand() < 0.4f)
					{
						// An old beam that came down with it, lying along the wall
						const float A = Rand.FRandRange(-60.f, 60.f);
						const FVector2D P0 = E.At(Rand.FRandRange(175.f, 200.f), A - 170.f);
						const FVector2D P1 = E.At(Rand.FRandRange(175.f, 200.f), A + 170.f);
						Timber(WoodDark, FVector(P0, FloorAt(At, Level, P0) + 11.f), FVector(P1, FloorAt(At, Level, P1) + Rand.FRandRange(11.f, 30.f)), 22.f, false);
					}
				}
			}

			// Corners: round off the square turn. The far corner gets a rock from floor to ceiling; the near one a column.
			if (bCorner && bSolid)
			{
				FIntPoint WallA = FIntPoint::ZeroValue, WallB = FIntPoint::ZeroValue;
				for (int32 d = 0; d < 4; ++d)
				{
					if (!Next[d])
					{
						(WallA == FIntPoint::ZeroValue ? WallA : WallB) = Dirs[d];
					}
				}
				const FVector2D OutA(WorldDir(WallA).X, WorldDir(WallA).Y);
				const FVector2D OutB(WorldDir(WallB).X, WorldDir(WallB).Y);
				const FVector2D Far = Center + (OutA + OutB) * (Tile * 0.5f + 15.f);
				if (!NearFixture(FVector(Far, Level.Z + 150.f), 260.f))
				{
					const float Height = Ceiling - Level.Z;
					const float Size = Rand.FRandRange(300.f, 340.f);
					Rock(DWall, FVector(Far, Level.Z - 30.f), FVector(Size, Size * Rand.FRandRange(0.9f, 1.f), Height * Rand.FRandRange(0.5f, 0.65f)),
						Upright(Rand.FRandRange(0.f, 360.f)), true, true);
					Rock(DWall, FVector(Far, Ceiling + 60.f), FVector(Size * 1.05f, Size, Height * 0.6f), Hanging(Rand.FRandRange(0.f, 360.f)), true, true);
				}
				const FIntPoint Diagonal = At - WallA - WallB;
				bool bDiagonalFree = true;
				if (const TArray<FLevel>* Levels = Cells.Find(Diagonal))
				{
					for (const FLevel& Other : *Levels)
					{
						bDiagonalFree &= FMath::Abs(Other.Z - Level.Z) > 900.f;
					}
				}
				const FLevel* SideA = Neighbour(At, Level, FIntPoint::ZeroValue - WallA);
				const FLevel* SideB = Neighbour(At, Level, FIntPoint::ZeroValue - WallB);
				const FVector2D Near = Center - (OutA + OutB) * (Tile * 0.5f);
				if (bDiagonalFree && SideA && SideB && !SideA->bBridge && !SideA->bUnderBridge && !SideB->bBridge && !SideB->bUnderBridge
					&& SideA->Owner < RoomOwner && SideB->Owner < RoomOwner && MomentDistance(Path, At - WallA) > 0 && MomentDistance(Path, At - WallB) > 0
					&& !NearFixture(FVector(Near, Level.Z + 150.f), 200.f))
				{
					const float Floor = FMath::Min(SideA->Z, SideB->Z);
					Rock(DWall, FVector(Near, FMath::Min(Floor, Level.Z) - 30.f), FVector(150.f, 145.f, Rand.FRandRange(250.f, 380.f)),
						Upright(Rand.FRandRange(0.f, 360.f)), true, true);
					Rock(DCeiling, FVector(Near, Ceiling + 60.f), FVector(220.f, 210.f, Rand.FRandRange(120.f, 170.f)), Hanging(Rand.FRandRange(0.f, 360.f)), true, true);
				}
			}

			// Dead ends: a rubble pile and a boulder at the far end, clear of the tile's middle
			if (bTip && !bMoment)
			{
				int32 Open = 0;
				for (int32 d = 0; d < 4; ++d)
				{
					Open = Next[d] ? d : Open;
				}
				const FVector Far3 = -WorldDir(Dirs[Open]);
				const FEdge E{ Center, FVector2D(Far3.X, Far3.Y), FVector2D(-Far3.Y, Far3.X) };
				Rock(DBoulders, FVector(E.At(240.f, Rand.FRandRange(-70.f, 70.f)), Level.Z - 20.f),
					FVector(Rand.FRandRange(220.f, 280.f), 170.f, Rand.FRandRange(150.f, 200.f)), Upright(FVector(E.Along, 0.f).Rotation().Yaw), true, true);
				for (const float Sign : { -1.f, 1.f })
				{
					MediumRock(E.At(Rand.FRandRange(165.f, 190.f), Sign * Rand.FRandRange(130.f, 180.f)), Rand.FRandRange(50.f, 85.f), At, Level);
				}
				for (int32 k = 0; k < 6; ++k)
				{
					SmallRock(E.At(Rand.FRandRange(110.f, 200.f), Rand.FRandRange(-200.f, 200.f)), At, Level);
				}
				ScatterPebbles(E, At, Level, 12, 80.f, 220.f);
			}

			// Old mine timber in the Trench: a frame across the tunnel, posts against the walls
			if (bTimber && !bMoment)
			{
				const FVector Run = WorldDir(Next[0] ? Dirs[0] : Dirs[2]);
				const FVector Side(-Run.Y, Run.X, 0.f);
				const FVector Middle = FVector(Center, 0.f) + Run * -170.f;
				const float Top = Ceiling - 70.f;
				if (!NearFixture(Middle + FVector(0.f, 0.f, Level.Z + 150.f), 260.f))
				{
					for (const float Sign : { -1.f, 1.f })
					{
						const FVector Foot = Middle + Side * (Sign * 200.f);
						const float Floor = FloorAt(At, Level, FVector2D(Foot));
						Timber(Wood, FVector(Foot.X, Foot.Y, Floor - 15.f), FVector(Foot.X, Foot.Y, Top), 30.f, true);
						Timber(WoodDark, FVector(Foot.X, Foot.Y, Top - 150.f), Middle + Side * (Sign * 110.f) + FVector(0.f, 0.f, Top - 8.f), 16.f, false);
					}
					Timber(Wood, Middle + Side * -255.f + FVector(0.f, 0.f, Top + 18.f), Middle + Side * 255.f + FVector(0.f, 0.f, Top + 18.f), 34.f, false);
				}
			}

			// Ceilings
			if (Level.bUnderBridge)
			{
				// The bridge deck overhead gets a rough rock underside
				for (int32 k = Rand.RandRange(3, 5); k > 0; --k)
				{
					const FVector2D P = Center + FVector2D(Rand.FRandRange(-190.f, 190.f), Rand.FRandRange(-190.f, 190.f));
					Rock(DCeiling, FVector(P, Ceiling + 25.f), FVector(Rand.FRandRange(150.f, 240.f), Rand.FRandRange(130.f, 200.f), Rand.FRandRange(45.f, 85.f)),
						Hanging(Rand.FRandRange(0.f, 360.f)), false);
				}
				continue;
			}
			float Drop = 0.f;
			if (!bOpenUp && !bMoment && !Level.bBridge)
			{
				// Stretches of lower roof between the corners and junctions, which keep the full height
				Drop = bCollapsed ? Rand.FRandRange(80.f, 130.f) : FMath::Max(0.f, Wave(RunS * 0.6f, Seeds[Path] + 5.f)) * 115.f;
			}
			if (Drop > 25.f)
			{
				for (int32 k = Rand.RandRange(1, 2); k > 0; --k)
				{
					const FVector2D P = Center + FVector2D(Rand.FRandRange(-90.f, 90.f), Rand.FRandRange(-90.f, 90.f));
					Rock(DCeiling, FVector(P, Ceiling + 60.f), FVector(Rand.FRandRange(330.f, 470.f), Rand.FRandRange(300.f, 440.f), 80.f + Drop),
						Hanging(Rand.FRandRange(0.f, 360.f)), true, true);
				}
			}
			else if (bOpenUp && !bMouth)
			{
				// Where the tunnel opens up, a lip of rock hangs over each way in, like an arch
				for (int32 d = 0; d < 4; ++d)
				{
					if (Next[d] && Next[d]->Owner < RoomOwner && !Next[d]->bUnderBridge && !Next[d]->bBridge)
					{
						const FVector W3 = WorldDir(Dirs[d]);
						Rock(DCeiling, FVector(Center + FVector2D(W3.X, W3.Y) * (Tile * 0.5f), Ceiling + 60.f),
							FVector(Rand.FRandRange(120.f, 170.f), Rand.FRandRange(420.f, 500.f), Rand.FRandRange(120.f, 150.f)),
							Hanging(FVector(W3.X, W3.Y, 0.f).Rotation().Yaw + Rand.FRandRange(-6.f, 6.f)), true, true);
					}
				}
			}
			// Stalactites hang from the tunnel's own roof (through any lower rock, so none float where it doesn't reach)
			const float Roof = Ceiling - 20.f;
			const float Shortest = 40.f + Drop * 0.7f;
			for (int32 k = Rand.RandRange(0, 3) + (bOpenUp ? 2 : 0); k > 0; --k)
			{
				const FVector2D Offset(Rand.FRandRange(-210.f, 210.f), Rand.FRandRange(-210.f, 210.f));
				const float Lowest = Level.FloorMax + FMath::Max(bNearMoment ? MomentHeadroom : 0.f, Offset.Size() < Lane + 60.f ? Clearance + 80.f : Clearance);
				const float Longest = FMath::Min(Roof - Lowest, 180.f + Drop);
				if (Longest < Shortest)
				{
					continue;
				}
				if (Path == 2 && Rand.FRand() < 0.4f && Drop < 25.f)
				{
					Crystals(FVector(Center + Offset, Roof + 10.f), -Up, FVector(40.f, 40.f, 0.f), 3, FMath::Min(1.f, Longest / 110.f), false);
				}
				else
				{
					Spike(DCeiling, FVector(Center + Offset, Roof + 15.f), -Up, Rand.FRandRange(10.f, 26.f), Rand.FRandRange(Shortest, Longest), false);
				}
			}
		}
	}

	// -----------------------------------------------------------------------
	// The rooms: the fork, both halls and the relic chamber
	// -----------------------------------------------------------------------
	const TArray<FPathSpec> Paths = MakePaths();
	for (int32 RoomIndex = Fork; RoomIndex < RoomCount; ++RoomIndex)
	{
		const FRoomSpec& Room = Rooms[RoomIndex];
		const ERoom Id = ERoom(RoomIndex);
		const FVector Middle = RoomCenter(Id);
		const FVector2D Middle2D(Middle);
		const float Z = Room.Z * 100.f;
		const float Ceiling = Z + RoomHeadroom;
		const bool bHall = (Id == HallA || Id == HallB);
		const int32 MidCol = (Room.C0 + Room.C1) / 2;
		auto InRoom = [&Room](const FIntPoint& T) { return T.X >= Room.C0 && T.X <= Room.C1 && T.Y >= Room.R0 && T.Y <= Room.R1; };
		auto RoomLevel = [&Cells, RoomIndex](const FIntPoint& T) -> const FLevel*
		{
			if (const TArray<FLevel>* Levels = Cells.Find(T))
			{
				for (const FLevel& L : *Levels)
				{
					if (L.Owner == RoomOwner + RoomIndex) { return &L; }
				}
			}
			return nullptr;
		};

		// The ways in, and a clear route from each to the middle
		TArray<FVector2D> Mouths;
		for (int32 Row = Room.R0; Row <= Room.R1; ++Row)
		{
			for (int32 Col = Room.C0; Col <= Room.C1; ++Col)
			{
				const FIntPoint T(Col, Row);
				const FLevel* L = RoomLevel(T);
				for (const FIntPoint& Dir : Dirs)
				{
					if (L && !InRoom(T + Dir) && Neighbour(T, *L, Dir))
					{
						const FVector W3 = WorldDir(Dir);
						Mouths.Add(TileCenter(T) + FVector2D(W3.X, W3.Y) * (Tile * 0.5f));
					}
				}
			}
		}
		// Clear routes: each way in to the middle, and the straight line from where each path comes in to where it goes on
		// (from the door, in the fork)
		TArray<TPair<FVector2D, FVector2D>> Routes;
		for (const FVector2D& M : Mouths)
		{
			Routes.Add({ M, Middle2D });
		}
		auto Inside = [&Room](int32 Col, int32 Row)
		{
			return TileCenter(FIntPoint(FMath::Clamp(Col, Room.C0, Room.C1), FMath::Clamp(Row, Room.R0, Room.R1)));
		};
		for (const FPathSpec& Spec : Paths)
		{
			for (int32 Seg = 0; Seg < Spec.Segments.Num(); ++Seg)
			{
				const FWaypoint& First = Spec.Segments[Seg][0];
				if (SegmentRooms[Seg] == Id)
				{
					const FVector2D From = (Seg > 0) ? Inside(Spec.Segments[Seg - 1].Last().Col, Spec.Segments[Seg - 1].Last().Row)
						: Inside(Rooms[Door].C0, Rooms[Door].R1);
					Routes.Add({ From, Inside(First.Col, First.Row) });
				}
			}
		}
		// Statues stand in the halls' corners and against the middle of their north and south walls (the style pass)
		auto StatueTile = [&](const FIntPoint& T)
		{
			return bHall && (T.Y == Room.R0 || T.Y == Room.R1) && (T.X == Room.C0 || T.X == Room.C1 || T.X == MidCol);
		};
		auto Blocked = [&](const FVector2D& P, float Radius)
		{
			for (const FVector2D& M : Mouths)
			{
				if (FVector2D::Distance(P, M) < 300.f + Radius)
				{
					return true;
				}
			}
			for (const TPair<FVector2D, FVector2D>& Route : Routes)
			{
				if (DistToSegment(P, Route.Key, Route.Value) < RouteClear + Radius)
				{
					return true;
				}
			}
			const FIntPoint T(FMath::RoundToInt(P.X / Tile) + OriginCol, OriginRow - FMath::RoundToInt(P.Y / Tile));
			return NearStation(P, Z, Radius) || StatueTile(T) || (Id == Goal && FVector2D::Distance(P, Middle2D) < AltarClear + Radius)
				|| NearFixture(FVector(P, Z + 150.f), 150.f + Radius);
		};

		// Along the walls: rock standing out, terraces you can step up onto, boulders, stalagmites, rubble
		for (int32 Row = Room.R0; Row <= Room.R1; ++Row)
		{
			for (int32 Col = Room.C0; Col <= Room.C1; ++Col)
			{
				const FIntPoint T(Col, Row);
				const FLevel* L = RoomLevel(T);
				if (!L)
				{
					continue;
				}
				for (const FIntPoint& Dir : Dirs)
				{
					if (InRoom(T + Dir) || Neighbour(T, *L, Dir))
					{
						continue;
					}
					const FVector Out3 = WorldDir(Dir);
					const FEdge E{ TileCenter(T), FVector2D(Out3.X, Out3.Y), FVector2D(-Out3.Y, Out3.X) };
					ScatterPebbles(E, T, *L, Rand.RandRange(5, 10), 120.f, WallFace);
					if (Rand.FRand() < 0.4f)
					{
						FloorStone(E.At(Rand.FRandRange(120.f, 180.f), Rand.FRandRange(-180.f, 180.f)), T, *L, Rand.FRandRange(70.f, 140.f));
					}
					if (StatueTile(T) || NearFixture(FVector(E.At(WallFace, 0.f), Z + 150.f), 330.f))
					{
						continue;   // kept low: only pebbles and stones
					}
					const float W = Wave(((Dir.Y != 0) ? E.Center.X : E.Center.Y) / Tile, 2.3f + RoomIndex + Dir.X * 0.5f);
					float Depth = 0.f;
					if (W > 0.3f && !Blocked(E.At(WallFace - 110.f, 0.f), 100.f))
					{
						Depth = FMath::Lerp(30.f, 110.f, FMath::Min(1.f, (W - 0.3f) / 0.5f));
						Bulge(E, T, *L, Rand.FRandRange(-40.f, 40.f), Rand.FRandRange(360.f, 460.f), Depth, Rand.FRandRange(300.f, 520.f));
					}
					const float Face = WallFace - Depth;
					const float Roll = Rand.FRand();
					if (Roll < 0.28f)
					{
						// A terrace: a flat-topped ledge low enough to step onto, sometimes with a second, higher one behind it
						const float Deep = Rand.FRandRange(150.f, 200.f);
						const FVector2D P = E.At(Face - Deep * 0.5f + 30.f, Rand.FRandRange(-30.f, 30.f));
						if (!Blocked(P, Deep * 0.5f))
						{
							Rock(DBoulders, FVector(P, Z - 8.f), FVector(Rand.FRandRange(380.f, 470.f), Deep, Rand.FRandRange(40.f, 48.f)),
								Upright(FVector(E.Along, 0.f).Rotation().Yaw + Rand.FRandRange(-5.f, 5.f)), true, false, 0.95f, 1);
							if (Rand.FRand() < 0.5f)
							{
								Rock(DBoulders, FVector(E.At(Face - 20.f, Rand.FRandRange(-60.f, 60.f)), Z - 8.f), FVector(Rand.FRandRange(240.f, 320.f), 120.f, Rand.FRandRange(85.f, 100.f)),
									Upright(FVector(E.Along, 0.f).Rotation().Yaw + Rand.FRandRange(-5.f, 5.f)), true, false, 0.95f, 1);
							}
						}
					}
					else if (Roll < 0.5f)
					{
						// A boulder against the wall
						const FVector Size(Rand.FRandRange(180.f, 260.f), Rand.FRandRange(160.f, 220.f), Rand.FRandRange(140.f, 220.f));
						const FVector2D P = E.At(Face - Size.Y * 0.3f, Rand.FRandRange(-120.f, 120.f));
						if (!Blocked(P, Size.X * 0.5f))
						{
							Rock(DBoulders, FVector(P, Z - 15.f), Size, Upright(Rand.FRandRange(0.f, 360.f)), true, true);
						}
					}
					else if (Roll < 0.72f)
					{
						// A cluster of stalagmites
						const FVector2D P = E.At(Face - 80.f, Rand.FRandRange(-120.f, 120.f));
						if (!Blocked(P, 110.f))
						{
							Stalagmites(P, Z, Rand.RandRange(3, 5), 280.f, 70.f);
							MediumRock(P, Rand.FRandRange(50.f, 70.f), T, *L);
						}
					}
					else
					{
						// Rubble
						for (int32 k = 0; k < 2; ++k)
						{
							const float Height = Rand.FRandRange(50.f, 95.f);
							const FVector2D P = E.At(Face - Height, Rand.FRandRange(-180.f, 180.f));
							if (!Blocked(P, Height))
							{
								MediumRock(P, Height, T, *L);
							}
						}
						for (int32 k = 0; k < 4; ++k)
						{
							SmallRock(E.At(Rand.FRandRange(Face - 160.f, Face), Rand.FRandRange(-220.f, 220.f)), T, *L);
						}
					}
				}
			}
		}

		// Out in the room: rock pillars from floor to ceiling, and a heap of collapsed boulders
		const FVector2D Low = TileCenter(FIntPoint(Room.C0, Room.R1)) + FVector2D(150.f, 150.f);
		const FVector2D High = TileCenter(FIntPoint(Room.C1, Room.R0)) - FVector2D(150.f, 150.f);
		TArray<FVector2D> Placed;
		const int32 Pillars = (Id == Fork) ? 2 : 3;
		for (int32 Attempt = 0, Count = 0; Attempt < 80 && Count < Pillars + 1; ++Attempt)
		{
			const FVector2D P(Rand.FRandRange(Low.X, High.X), Rand.FRandRange(Low.Y, High.Y));
			const bool bPillar = Count < Pillars;
			const float Radius = bPillar ? 150.f : 230.f;
			bool bFree = !Blocked(P, Radius);
			for (const FVector2D& Other : Placed)
			{
				bFree &= FVector2D::Distance(P, Other) > 700.f;
			}
			if (!bFree)
			{
				continue;
			}
			Placed.Add(P);
			++Count;
			UE_LOG(LogTemp, Verbose, TEXT("CoopPlayground: %s gets a %s at (%.0f, %.0f)"), Room.Name, bPillar ? TEXT("pillar") : TEXT("boulder heap"), P.X, P.Y);
			if (bPillar)
			{
				const float Base = Rand.FRandRange(320.f, 420.f);
				Rock(DWall, FVector(P, Z - 20.f), FVector(Rand.FRandRange(230.f, 270.f), Rand.FRandRange(210.f, 250.f), Base),
					Upright(Rand.FRandRange(0.f, 360.f)), true, true, 0.3f, 1);
				Rock(DWall, FVector(P + FVector2D(Rand.FRandRange(-20.f, 20.f), Rand.FRandRange(-20.f, 20.f)), Ceiling + 60.f),
					FVector(Rand.FRandRange(240.f, 300.f), Rand.FRandRange(230.f, 290.f), Ceiling + 60.f - (Z - 20.f + Base) + 120.f),
					Hanging(Rand.FRandRange(0.f, 360.f)), true, true, 0.3f, 1);
				for (int32 k = 0; k < 5; ++k)
				{
					const float Angle = Rand.FRandRange(0.f, 2.f * PI);
					const FVector2D Q = P + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * Rand.FRandRange(150.f, 210.f);
					Rock(DSmall, FVector(Q, Z - 3.f), FVector(Rand.FRandRange(25.f, 55.f), Rand.FRandRange(22.f, 45.f), Rand.FRandRange(12.f, 35.f)),
						Upright(Rand.FRandRange(0.f, 360.f)), false, false, 0.6f);
				}
			}
			else
			{
				for (int32 k = 0; k < 3; ++k)
				{
					const FVector2D Q = P + FVector2D(Rand.FRandRange(-90.f, 90.f), Rand.FRandRange(-90.f, 90.f));
					Rock(DBoulders, FVector(Q, Z - 15.f), FVector(Rand.FRandRange(160.f, 230.f), Rand.FRandRange(150.f, 210.f), Rand.FRandRange(140.f, 200.f)),
						Upright(Rand.FRandRange(0.f, 360.f)), true, true);
				}
				for (int32 k = 0; k < 6; ++k)
				{
					const float Angle = Rand.FRandRange(0.f, 2.f * PI);
					const FVector2D Q = P + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * Rand.FRandRange(170.f, 240.f);
					Rock(DSmall, FVector(Q, Z - 3.f), FVector(Rand.FRandRange(25.f, 60.f), Rand.FRandRange(22.f, 50.f), Rand.FRandRange(12.f, 38.f)),
						Upright(Rand.FRandRange(0.f, 360.f)), false, false, 0.6f);
				}
			}
		}

		// The floor and the roof
		const int32 Tiles = (Room.C1 - Room.C0 + 1) * (Room.R1 - Room.R0 + 1);
		const FVector2D Min = TileCenter(FIntPoint(Room.C0, Room.R1)) - FVector2D(220.f, 220.f);
		const FVector2D Max = TileCenter(FIntPoint(Room.C1, Room.R0)) + FVector2D(220.f, 220.f);
		for (int32 k = Tiles * 5; k > 0; --k)
		{
			const FVector2D P(Rand.FRandRange(Min.X, Max.X), Rand.FRandRange(Min.Y, Max.Y));
			const float Width = Rand.FRandRange(5.f, 15.f);
			if (Id != Goal || FVector2D::Distance(P, Middle2D) > 250.f)
			{
				Pebble(FVector(P, Z - 1.f), Width);
			}
		}
		for (int32 k = Tiles / 2; k > 0; --k)
		{
			const FVector2D P(Rand.FRandRange(Min.X, Max.X), Rand.FRandRange(Min.Y, Max.Y));
			if (!Blocked(P, 30.f))
			{
				Rock(DSmall, FVector(P, Z - 3.f), FVector(Rand.FRandRange(25.f, 60.f), Rand.FRandRange(22.f, 50.f), Rand.FRandRange(12.f, 38.f)),
					Upright(Rand.FRandRange(0.f, 360.f)), false, false, 0.6f);
			}
			const FVector2D S(Rand.FRandRange(Min.X, Max.X), Rand.FRandRange(Min.Y, Max.Y));
			if (Id != Goal || FVector2D::Distance(S, Middle2D) > 300.f)
			{
				Rock(DStones, FVector(S, Z - 2.f), FVector(Rand.FRandRange(70.f, 150.f), Rand.FRandRange(50.f, 110.f), Rand.FRandRange(3.f, 6.f)),
					Upright(Rand.FRandRange(0.f, 360.f)), false, false, 0.9f);
			}
		}
		if (Id == HallA)
		{
			// The sunken hall holds water
			for (int32 k = Rand.RandRange(4, 6); k > 0; --k)
			{
				Puddle(FVector2D(Rand.FRandRange(Min.X + 100.f, Max.X - 100.f), Rand.FRandRange(Min.Y + 100.f, Max.Y - 100.f)), Z);
			}
		}
		for (int32 k = Tiles; k > 0; --k)
		{
			const FVector2D P(Rand.FRandRange(Min.X, Max.X), Rand.FRandRange(Min.Y, Max.Y));
			Spike(DCeiling, FVector(P, Ceiling - 5.f), -Up, Rand.FRandRange(14.f, 34.f), Rand.FRandRange(60.f, 260.f), false);
		}
		for (int32 k = Rand.RandRange(2, 4); k > 0; --k)
		{
			// Patches of lower roof
			const FVector2D P(Rand.FRandRange(Min.X + 200.f, Max.X - 200.f), Rand.FRandRange(Min.Y + 200.f, Max.Y - 200.f));
			Rock(DCeiling, FVector(P, Ceiling + 60.f), FVector(Rand.FRandRange(400.f, 600.f), Rand.FRandRange(350.f, 550.f), Rand.FRandRange(150.f, 240.f)),
				Hanging(Rand.FRandRange(0.f, 360.f)), true, true);
		}
	}

	// Into meshes: one per kind per square, no shadows
	int32 Triangles = 0;
	int32 Meshes = 0;
	for (FKind* Kind : { &DWall, &DCeiling, &DBoulders, &DSmall, &DPebbles, &DStones, &DPuddles, &Wood, &WoodDark })
	{
		for (const TPair<FIntPoint, FCoopMeshData>& Chunk : Kind->Chunks)
		{
			Triangles += Chunk.Value.Triangles.Num() / 3;
			Meshes += AddProcMesh(Chunk.Value, MaterialFor(Kind->Color), {}, false) ? 1 : 0;
		}
	}
	if (UProceduralMeshComponent* Collision = AddProcMesh(BlockerMesh, nullptr, BlockerHulls, false))
	{
		Collision->SetHiddenInGame(true);
	}
	if (RepoRockMesh && RepoRocks.Num() > 0)
	{
		UInstancedStaticMeshComponent* Rocks = NewObject<UInstancedStaticMeshComponent>(this);
		Rocks->SetupAttachment(Root);
		Rocks->SetMobility(EComponentMobility::Static);
		Rocks->SetStaticMesh(RepoRockMesh);
		if (RepoRockMaterial)
		{
			Rocks->SetMaterial(0, RepoRockMaterial);
		}
		Rocks->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Rocks->SetCastShadow(false);
		Rocks->RegisterComponent();
		Rocks->AddInstances(RepoRocks, false);
	}
	UE_LOG(LogTemp, Display, TEXT("CoopPlayground: maze detail built, %d triangles in %d meshes, %d colliders, %d repo rocks"), Triangles, Meshes, Colliders, RepoRocks.Num());
}

void ACoopPlayground::BuildMaze()
{
	using namespace CoopCave;
	using namespace CoopMaze;
	const TArray<FPathSpec> Paths = MakePaths();
	const FIntPoint Dirs[4] = { FIntPoint(1, 0), FIntPoint(-1, 0), FIntPoint(0, 1), FIntPoint(0, -1) };

	// 1. Each path segment, tile by tile, with its corners and the heights the table fixes
	struct FSegment
	{
		TArray<FIntPoint> Tiles;
		TArray<float> Z;
		TArray<bool> Anchor;      // flat tiles: corners, ends, bridges, dead-end junctions
		TMap<int32, float> Keys;  // tile index -> fixed height
		TSet<int32> Corners;
		int32 FromRoom = 0;
		int32 ToRoom = 0;
	};
	TArray<TArray<FSegment>> Segments;
	Segments.SetNum(Paths.Num());
	TMap<FIntPoint, int32> UseCount;
	TSet<FIntPoint> DeadEndRoots;

	for (int32 P = 0; P < Paths.Num(); ++P)
	{
		for (int32 S = 0; S < Paths[P].Segments.Num(); ++S)
		{
			const TArray<FWaypoint>& Points = Paths[P].Segments[S];
			FSegment& Seg = Segments[P].AddDefaulted_GetRef();
			Seg.FromRoom = SegmentRooms[S];
			Seg.ToRoom = SegmentRooms[S + 1];
			Seg.Tiles.Add(FIntPoint(Points[0].Col, Points[0].Row));
			Seg.Keys.Add(0, Points[0].Z * 100.f);
			for (int32 K = 1; K < Points.Num(); ++K)
			{
				const FIntPoint From(Points[K - 1].Col, Points[K - 1].Row);
				const FIntPoint To(Points[K].Col, Points[K].Row);
				const FIntPoint Step(FMath::Sign(To.X - From.X), FMath::Sign(To.Y - From.Y));
				if (Step.X != 0 && Step.Y != 0)
				{
					UE_LOG(LogTemp, Error, TEXT("Maze: path %d waypoints (%d,%d) and (%d,%d) don't share a row or column"), P + 1, From.X, From.Y, To.X, To.Y);
					continue;
				}
				for (FIntPoint T = From; T != To;)
				{
					T += Step;
					Seg.Tiles.Add(T);
				}
				if (Points[K].Z != Free)
				{
					Seg.Keys.Add(Seg.Tiles.Num() - 1, Points[K].Z * 100.f);
				}
				if (K + 1 < Points.Num())
				{
					const FIntPoint Next(Points[K + 1].Col, Points[K + 1].Row);
					if (FIntPoint(FMath::Sign(Next.X - To.X), FMath::Sign(Next.Y - To.Y)) != Step)
					{
						Seg.Corners.Add(Seg.Tiles.Num() - 1);
					}
				}
			}
			TSet<FIntPoint> Unique;
			for (const FIntPoint& T : Seg.Tiles)
			{
				Unique.Add(T);
			}
			for (const FIntPoint& T : Unique)
			{
				UseCount.FindOrAdd(T)++;
			}
		}
		for (const TArray<FTileRef>& Dead : Paths[P].DeadEnds)
		{
			DeadEndRoots.Add(FIntPoint(Dead[0].Col, Dead[0].Row));
		}
	}

	// 2. Heights: ramps spread evenly over the steps between two non-flat tiles
	for (int32 P = 0; P < Segments.Num(); ++P)
	{
		for (FSegment& Seg : Segments[P])
		{
			const int32 Num = Seg.Tiles.Num();
			Seg.Anchor.Init(false, Num);
			Seg.Anchor[0] = true;
			Seg.Anchor[Num - 1] = true;
			for (const int32 Corner : Seg.Corners)
			{
				Seg.Anchor[Corner] = true;
			}
			for (int32 i = 0; i < Num; ++i)
			{
				if (UseCount.FindRef(Seg.Tiles[i]) > 1 || DeadEndRoots.Contains(Seg.Tiles[i]))
				{
					Seg.Anchor[i] = true;
				}
			}
			TArray<int32> RampSteps;   // ramp steps before each tile
			RampSteps.Init(0, Num);
			for (int32 i = 1; i < Num; ++i)
			{
				RampSteps[i] = RampSteps[i - 1] + ((!Seg.Anchor[i] && !Seg.Anchor[i - 1]) ? 1 : 0);
			}
			TArray<int32> KeyTiles;
			Seg.Keys.GenerateKeyArray(KeyTiles);
			KeyTiles.Sort();

			Seg.Z.SetNum(Num);
			for (int32 i = 0; i < Num; ++i)
			{
				int32 A = KeyTiles[0];
				int32 B = KeyTiles.Last();
				for (const int32 K : KeyTiles)
				{
					if (K <= i) { A = K; }
					if (K >= i) { B = K; break; }
				}
				const float ZA = Seg.Keys[A];
				const float ZB = Seg.Keys[B];
				if (A == B || ZA == ZB)
				{
					Seg.Z[i] = ZA;
					continue;
				}
				const int32 Span = RampSteps[B] - RampSteps[A];
				if (Span <= 0)
				{
					UE_LOG(LogTemp, Warning, TEXT("Maze: path %d has no straight run to ramp between tiles %d and %d"), P + 1, A, B);
					Seg.Z[i] = FMath::Lerp(ZA, ZB, float(i - A) / float(B - A));
					continue;
				}
				Seg.Z[i] = FMath::Lerp(ZA, ZB, float(RampSteps[i] - RampSteps[A]) / float(Span));
			}
			for (int32 i = 1; i < Num; ++i)
			{
				if (FMath::Abs(Seg.Z[i] - Seg.Z[i - 1]) > MaxRampStep)
				{
					UE_LOG(LogTemp, Warning, TEXT("Maze: path %d is too steep at tile (%d,%d)"), P + 1, Seg.Tiles[i].X, Seg.Tiles[i].Y);
				}
			}
		}
	}

	// 3. Every walkable floor on every tile: rooms, path tiles, dead ends
	TMap<FIntPoint, TArray<FLevel>> Cells;
	for (int32 R = 0; R < RoomCount; ++R)
	{
		const FRoomSpec& Room = Rooms[R];
		for (int32 Row = Room.R0; Row <= Room.R1; ++Row)
		{
			for (int32 Col = Room.C0; Col <= Room.C1; ++Col)
			{
				FLevel& Level = Cells.FindOrAdd(FIntPoint(Col, Row)).AddDefaulted_GetRef();
				Level.Owner = RoomOwner + R;
				Level.Z = Level.FloorMin = Level.FloorMax = Room.Z * 100.f;
				Level.Headroom = (R == Door) ? CorridorHeadroom : RoomHeadroom;
			}
		}
	}
	for (int32 P = 0; P < Segments.Num(); ++P)
	{
		for (const FSegment& Seg : Segments[P])
		{
			const int32 Num = Seg.Tiles.Num();
			for (int32 i = 0; i < Num; ++i)
			{
				FLevel& Level = Cells.FindOrAdd(Seg.Tiles[i]).AddDefaulted_GetRef();
				Level.Owner = P;
				Level.Z = Level.FloorMin = Level.FloorMax = Seg.Z[i];
				for (const int32 j : { i - 1, i + 1 })
				{
					if (Seg.Z.IsValidIndex(j))
					{
						const float Edge = (Seg.Z[i] + Seg.Z[j]) * 0.5f;
						Level.FloorMin = FMath::Min(Level.FloorMin, Edge);
						Level.FloorMax = FMath::Max(Level.FloorMax, Edge);
					}
				}
				Level.LinkOwner = (i == 0) ? RoomOwner + Seg.FromRoom : (i == Num - 1) ? RoomOwner + Seg.ToRoom : INDEX_NONE;
			}
		}
	}
	struct FDeadTile { FIntPoint At; float Z; int32 Path; };
	TArray<FDeadTile> DeadTiles;
	for (int32 P = 0; P < Paths.Num(); ++P)
	{
		for (const TArray<FTileRef>& Dead : Paths[P].DeadEnds)
		{
			const FIntPoint RootTile(Dead[0].Col, Dead[0].Row);
			float RootZ = 0.f;
			if (const TArray<FLevel>* RootLevels = Cells.Find(RootTile))
			{
				for (const FLevel& Level : *RootLevels)
				{
					if (Level.Owner == P) { RootZ = Level.Z; }
				}
			}
			for (int32 K = 1; K < Dead.Num(); ++K)
			{
				const FIntPoint From(Dead[K - 1].Col, Dead[K - 1].Row);
				const FIntPoint To(Dead[K].Col, Dead[K].Row);
				const FIntPoint Step(FMath::Sign(To.X - From.X), FMath::Sign(To.Y - From.Y));
				if (Step.X != 0 && Step.Y != 0)
				{
					continue;
				}
				for (FIntPoint T = From; T != To;)
				{
					T += Step;
					FLevel& Level = Cells.FindOrAdd(T).AddDefaulted_GetRef();
					Level.Owner = P;
					Level.Z = Level.FloorMin = Level.FloorMax = RootZ;
					DeadTiles.Add({ T, RootZ, P });
				}
			}
		}
	}
	// Crossings: the lower path's ceiling is the bridge deck
	int32 CrossingCount = 0;
	for (TPair<FIntPoint, TArray<FLevel>>& Cell : Cells)
	{
		if (Cell.Value.Num() == 2)
		{
			Cell.Value.Sort([](const FLevel& A, const FLevel& B) { return A.Z < B.Z; });
			FLevel& Lower = Cell.Value[0];
			FLevel& Upper = Cell.Value[1];
			Lower.bUnderBridge = true;
			Lower.Headroom = Upper.Z - Slab - Lower.Z;
			Upper.bBridge = true;
			++CrossingCount;
		}
	}
	auto FindLevel = [&Cells](const FIntPoint& At, int32 PathOwner) -> const FLevel*
	{
		if (const TArray<FLevel>* Levels = Cells.Find(At))
		{
			for (const FLevel& Level : *Levels)
			{
				if (Level.Owner == PathOwner) { return &Level; }
			}
		}
		return nullptr;
	};
	auto HasWall = [&Cells](const FIntPoint& At, const FLevel& Level, const FIntPoint& Dir)
	{
		if (const TArray<FLevel>* Next = Cells.Find(At + Dir))
		{
			for (const FLevel& Other : *Next)
			{
				if (Connected(Level, Other)) { return false; }
			}
		}
		return true;
	};

	// 4. Floors: a slab from each path tile to the next (sloped on ramps), a flat pad on each flat tile, one block per room.
	//    Each path's floor is tinted with its color so you can tell which way you're going.
	TArray<FCoopMeshData> PathFloors;
	TArray<TArray<TArray<FVector>>> PathFloorHulls;
	PathFloors.SetNum(Paths.Num());
	PathFloorHulls.SetNum(Paths.Num());
	FCoopMeshData RoomFloors;
	TArray<TArray<FVector>> RoomFloorHulls;

	auto AddSlab = [](FCoopMeshData& Mesh, TArray<TArray<FVector>>& Hulls, const FVector& From, const FVector& To)
	{
		const FVector Span = To - From;
		const FRotator Rotation = Span.Rotation();
		const FVector Up = FRotationMatrix(Rotation).GetUnitAxis(EAxis::Z);
		AddBlock(Mesh, Hulls, FTransform(Rotation, (From + To) * 0.5f - Up * Slab * 0.5f), FVector(Span.Size() * 0.5f + 2.f, Tile * 0.5f, Slab * 0.5f));
	};
	auto AddPad = [](FCoopMeshData& Mesh, TArray<TArray<FVector>>& Hulls, const FIntPoint& Tile2D, float Z)
	{
		AddBlock(Mesh, Hulls, FTransform(FVector(TileCenter(Tile2D), Z - Slab * 0.5f)), FVector(Tile * 0.5f, Tile * 0.5f, Slab * 0.5f));
	};
	for (int32 P = 0; P < Segments.Num(); ++P)
	{
		for (const FSegment& Seg : Segments[P])
		{
			for (int32 i = 0; i < Seg.Tiles.Num(); ++i)
			{
				if (Seg.Anchor[i])
				{
					AddPad(PathFloors[P], PathFloorHulls[P], Seg.Tiles[i], Seg.Z[i]);
				}
				if (i + 1 < Seg.Tiles.Num())
				{
					AddSlab(PathFloors[P], PathFloorHulls[P], FVector(TileCenter(Seg.Tiles[i]), Seg.Z[i]), FVector(TileCenter(Seg.Tiles[i + 1]), Seg.Z[i + 1]));
				}
			}
		}
	}
	for (const FDeadTile& Dead : DeadTiles)
	{
		AddPad(PathFloors[Dead.Path], PathFloorHulls[Dead.Path], Dead.At, Dead.Z);
	}
	for (int32 R = 0; R < RoomCount; ++R)
	{
		if (R == Hub)
		{
			continue;
		}
		const FRoomSpec& Room = Rooms[R];
		const FVector Center = RoomCenter(ERoom(R));
		AddBlock(RoomFloors, RoomFloorHulls, FTransform(Center - FVector(0.f, 0.f, Slab * 0.5f)),
			FVector((Room.C1 - Room.C0 + 1) * Tile * 0.5f, (Room.R1 - Room.R0 + 1) * Tile * 0.5f, Slab * 0.5f));
	}
	for (int32 P = 0; P < Paths.Num(); ++P)
	{
		const FLinearColor Tint = FLinearColor::LerpUsingHSV(CoopCave::Sand, FLinearColor::FromSRGBColor(Paths[P].Color) * 0.3f, 0.35f);
		AddProcMesh(PathFloors[P], MaterialFor(Tint), PathFloorHulls[P], false);
	}
	AddProcMesh(RoomFloors, MaterialFor(CoopCave::Sand), RoomFloorHulls, false);

	// 5. Walls and ceilings: invisible boxes that stop you, and rocks you see.
	//    A wall goes wherever a floor has no connected floor next to it, from just under the floor to the ceiling.
	FCoopMeshData Blockers;
	TArray<TArray<FVector>> BlockerHulls;
	for (const TPair<FIntPoint, TArray<FLevel>>& Cell : Cells)
	{
		const FVector2D Center = TileCenter(Cell.Key);
		for (const FLevel& Level : Cell.Value)
		{
			if (Level.Owner == RoomOwner + Hub)
			{
				continue;   // the cave has its own walls
			}
			const float LevelCeilingZ = Level.FloorMax + Level.Headroom;
			const float Bottom = Level.bBridge ? Level.Z - Slab : Level.FloorMin - Slab - 40.f;
			const float Top = Level.bUnderBridge ? LevelCeilingZ : LevelCeilingZ + CeilingThickness;

			for (const FIntPoint& Dir : Dirs)
			{
				if (!HasWall(Cell.Key, Level, Dir))
				{
					continue;
				}
				const FVector Out = WorldDir(Dir);
				const FVector Along(-Out.Y, Out.X, 0.f);
				const FVector Edge = FVector(Center, 0.f) + Out * (Tile * 0.5f);

				// Each end overlaps the next wall by 50 cm, except into an opening (where a path meets a room):
				// there the overhang would narrow the way in and snag you on an invisible corner.
				float Overlap[2] = { 50.f, 50.f };   // toward +Along, toward -Along
				for (int32 End = 0; End < 2; ++End)
				{
					const FIntPoint Beside = Cell.Key + (End == 0 ? FIntPoint(Dir.Y, -Dir.X) : FIntPoint(-Dir.Y, Dir.X));
					if (const TArray<FLevel>* BesideLevels = Cells.Find(Beside))
					{
						for (const FLevel& Other : *BesideLevels)
						{
							if (Connected(Level, Other) && !HasWall(Beside, Other, Dir))
							{
								Overlap[End] = 0.f;
							}
						}
					}
				}
				AddBlock(Blockers, BlockerHulls,
					FTransform(Out.Rotation(), FVector(Edge.X, Edge.Y, (Bottom + Top) * 0.5f) + Out * 50.f + Along * ((Overlap[0] - Overlap[1]) * 0.5f)),
					FVector(50.f, Tile * 0.5f + (Overlap[0] + Overlap[1]) * 0.5f, (Top - Bottom) * 0.5f));

				// Rocks: two along the edge, stacked to fill the height, set back so their faces line the tunnel
				const float RockBottom = Level.bBridge ? Level.Z - Slab : Level.FloorMin - 80.f;
				const float RockTop = Level.bUnderBridge ? LevelCeilingZ : LevelCeilingZ + 60.f;
				const int32 Tiers = FMath::Max(1, FMath::CeilToInt((RockTop - RockBottom) / 330.f));
				const float TierHeight = (RockTop - RockBottom) / Tiers;
				for (int32 Tier = 0; Tier < Tiers; ++Tier)
				{
					for (const float SideSign : { -1.f, 1.f })
					{
						const float Depth = Random.FRandRange(180.f, 240.f);
						const FVector Spot = Edge + Out * (Depth * 0.35f) + Along * (SideSign * Tile * 0.25f * Random.FRandRange(0.85f, 1.15f));
						AddMazeRock(false, FVector(Spot.X, Spot.Y, RockBottom + (Tier + 0.5f) * TierHeight),
							FVector(Random.FRandRange(280.f, 340.f), Depth, TierHeight * 1.12f), Along.Rotation().Yaw + Random.FRandRange(-12.f, 12.f));
					}
				}
			}

			// Ceiling (under a bridge, the bridge deck is the ceiling)
			if (!Level.bUnderBridge)
			{
				AddBlock(Blockers, BlockerHulls, FTransform(FVector(Center, LevelCeilingZ + CeilingThickness * 0.5f)),
					FVector(Tile * 0.5f, Tile * 0.5f, CeilingThickness * 0.5f));
				AddMazeRock(true, FVector(Center, LevelCeilingZ + 100.f), FVector(540.f, 540.f, 240.f) * Random.FRandRange(0.95f, 1.05f),
					90.f * Random.RandRange(0, 3) + Random.FRandRange(-4.f, 4.f));
			}
		}
	}
	if (UProceduralMeshComponent* Collision = AddProcMesh(Blockers, nullptr, BlockerHulls, false))
	{
		Collision->SetHiddenInGame(true);
	}

	// Fill the cave's north wall either side of the door
	for (const float Along : { DoorMinX - 170.f, DoorMaxX + 170.f })
	{
		AddRock(WallRocks, FVector(Along, Half + 190.f, -40.f), FVector(340.f, 380.f, CeilingZ + 220.f), 0.f, 1, 0.2f, 0.f);
	}

	// 6. Light and markers. Torches along paths 1, 2 and 4; glowing teal crystals along path 3.
	//    Crystals in each path's color mark where it leaves and enters a room.
	FCoopMeshData Glow;
	auto AddCluster = [this, &Glow](const FVector& Base, const FVector& Inward, const FColor& RootColor, const FColor& TipColor, float Scale)
	{
		const FVector Side(-Inward.Y, Inward.X, 0.f);
		MazeWallMarkers.Add(Base);
		for (int32 k = 0; k < 4; ++k)
		{
			const FVector Spot = Base + Side * Random.FRandRange(-70.f, 70.f) + Inward * Random.FRandRange(0.f, 30.f);
			const FVector Dir = (FVector(0.f, 0.f, 1.f) + Inward * Random.FRandRange(0.3f, 0.8f) + Side * Random.FRandRange(-0.3f, 0.3f)).GetSafeNormal();
			CoopMeshKit::AddCrystal(Glow, FTransform(FRotationMatrix::MakeFromZ(Dir).Rotator(), Spot),
				Random.FRandRange(10.f, 18.f) * Scale, Random.FRandRange(50.f, 110.f) * Scale, RootColor, TipColor);
		}
	};
	// A wall beside the path at tile i, across from the way it runs. Returns false if there's none.
	auto SideWall = [&](const FSegment& Seg, int32 i, const FLevel& Level, bool bPreferLeft, FVector& OutDir)
	{
		const FIntPoint Run = (i + 1 < Seg.Tiles.Num()) ? Seg.Tiles[i + 1] - Seg.Tiles[i] : Seg.Tiles[i] - Seg.Tiles[i - 1];
		const FIntPoint Left(Run.Y, -Run.X);
		const FIntPoint Right(-Run.Y, Run.X);
		for (const FIntPoint& Dir : { bPreferLeft ? Left : Right, bPreferLeft ? Right : Left })
		{
			if (HasWall(Seg.Tiles[i], Level, Dir))
			{
				OutDir = WorldDir(Dir);
				return true;
			}
		}
		return false;
	};
	for (int32 P = 0; P < Segments.Num(); ++P)
	{
		const FColor PathColor = Paths[P].Color;
		const bool bCrystalPath = (P == 2);
		for (const FSegment& Seg : Segments[P])
		{
			const int32 Num = Seg.Tiles.Num();
			for (int32 i = 0; i < Num; ++i)
			{
				const FLevel* Level = FindLevel(Seg.Tiles[i], P);
				if (!Level || Level->bBridge || Level->bUnderBridge)
				{
					continue;
				}
				const FVector Floor(TileCenter(Seg.Tiles[i]), Level->Z);
				FVector Out;

				// Path color at both ends of the segment
				if ((i == 0 || i == Num - 1) && SideWall(Seg, i, *Level, true, Out))
				{
					AddCluster(Floor + Out * (Tile * 0.5f - 45.f), -Out, Scaled(PathColor, 0.3f), Lighter(PathColor), 0.9f);
				}

				const bool bLightSpot = (i % TorchEvery == TorchEvery / 2) && i != 0 && i != Num - 1;
				if (bCrystalPath && (bLightSpot || i % 2 == 1) && SideWall(Seg, i, *Level, (i / 2) % 2 == 0, Out))
				{
					AddCluster(Floor + Out * (Tile * 0.5f - 45.f), -Out, CoopCave::CrystalRoot, CoopCave::CrystalTip, bLightSpot ? 1.2f : 0.6f);
					if (bLightSpot)
					{
						UPointLightComponent* Light = NewObject<UPointLightComponent>(this);
						Light->SetupAttachment(Root);
						Light->SetMobility(EComponentMobility::Movable);
						Light->SetRelativeLocation(Floor + Out * (Tile * 0.5f - 160.f) + FVector(0.f, 0.f, 150.f));
						Light->IntensityUnits = ELightUnits::Candelas;
						Light->SetIntensity(CoopTuning::CrystalBrightness() * 0.6f);
						Light->SetLightColor(CoopCave::CrystalLightColor);
						Light->SetAttenuationRadius(750.f);
						Light->SetSourceRadius(30.f);
						Light->SetCastShadows(false);
						Light->RegisterComponent();
						MazeCrystalLights.Add(Light);
					}
				}
				else if (!bCrystalPath && bLightSpot && SideWall(Seg, i, *Level, (i / TorchEvery) % 2 == 0, Out))
				{
					AddWallTorch(Floor + Out * (Tile * 0.5f - 30.f) + FVector(0.f, 0.f, 235.f), -Out, false);
				}
			}
		}
	}
	// Torches round the rooms' walls
	for (int32 R = Fork; R < RoomCount; ++R)
	{
		const FRoomSpec& Room = Rooms[R];
		for (int32 Row = Room.R0; Row <= Room.R1; ++Row)
		{
			for (int32 Col = Room.C0; Col <= Room.C1; ++Col)
			{
				const FIntPoint Tile2D(Col, Row);
				const FLevel* Level = FindLevel(Tile2D, RoomOwner + R);
				for (const FIntPoint& Dir : Dirs)
				{
					const bool bSpot = (Dir.Y != 0) ? ((Col - Room.C0) % 4 == 2) : ((Row - Room.R0) % 3 == 1);
					if (Level && bSpot && HasWall(Tile2D, *Level, Dir))
					{
						const FVector Out = WorldDir(Dir);
						AddWallTorch(FVector(TileCenter(Tile2D), Level->Z + 260.f) + Out * (Tile * 0.5f - 30.f), -Out, false);
					}
				}
			}
		}
	}

	// 6b. The co-op moments, one per path, and a station in front of each
	TArray<FCoopPathSpot> MomentSpots;
	for (const FMomentSpec& Moment : Moments)
	{
		FCoopPathSpot& Spot = MomentSpots.AddDefaulted_GetRef();
		const FIntPoint At(Moment.Col, Moment.Row);
		for (const FSegment& Seg : Segments[Moment.Path])
		{
			const int32 i = Seg.Tiles.Find(At);
			if (i == INDEX_NONE)
			{
				continue;
			}
			const FIntPoint Run = (i + 1 < Seg.Tiles.Num()) ? Seg.Tiles[i + 1] - Seg.Tiles[i] : Seg.Tiles[i] - Seg.Tiles[i - 1];
			Spot.Forward = WorldDir(Run);
			Spot.Right = FVector(-Spot.Forward.Y, Spot.Forward.X, 0.f);
			Spot.Origin = FVector(TileCenter(At), Seg.Z[i]);
			for (int32 k = i - 2; k <= i + 2; ++k)
			{
				const int32 j = FMath::Clamp(k, 0, Seg.Tiles.Num() - 1);
				const FLevel* Level = FindLevel(Seg.Tiles[j], Moment.Path);
				Spot.FloorZ.Add(Seg.Z[j]);
				Spot.CeilingZ.Add(Level ? Level->FloorMax + Level->Headroom : Seg.Z[j] + CorridorHeadroom);
			}
			break;
		}
		if (Spot.FloorZ.IsEmpty())
		{
			UE_LOG(LogTemp, Error, TEXT("Maze: %s's tile (%d,%d) isn't on path %d"), Moment.Name, Moment.Col, Moment.Row, Moment.Path + 1);
			MomentSpots.Pop();
			continue;
		}
		FCoopStation& Station = Stations.AddDefaulted_GetRef();
		Station.Name = Moment.Name;
		Station.Status = Moment.Status;
		Station.Location = Spot.At(Moment.Station, 0.f, Spot.FloorAt(Moment.Station));
		Station.Yaw = Spot.Forward.Rotation().Yaw;
	}
	if (MomentSpots.Num() == UE_ARRAY_COUNT(Moments))
	{
		BuildMoments(MomentSpots);
	}

	// 7. The relic: a gold idol on a stone pedestal in the middle of the chamber
	{
		const FVector Spot = RoomCenter(Goal);
		AddShape(CylinderMesh, Spot + FVector(0.f, 0.f, 50.f), FVector(150.f, 150.f, 100.f), FRotator::ZeroRotator, CoopCave::FloorStone);
		UStaticMeshComponent* Body = AddShape(SphereMesh, Spot + FVector(0.f, 0.f, 140.f), FVector(60.f, 60.f, 80.f), FRotator::ZeroRotator, FLinearColor(0.8f, 0.55f, 0.12f));
		UStaticMeshComponent* Head = AddShape(ConeMesh, Spot + FVector(0.f, 0.f, 200.f), FVector(40.f, 40.f, 45.f), FRotator::ZeroRotator, FLinearColor(0.8f, 0.55f, 0.12f));
		for (UStaticMeshComponent* Part : { Body, Head })
		{
			if (Part && RepoGoldMaterial)
			{
				Part->SetMaterial(0, RepoGoldMaterial);
			}
		}
		UPointLightComponent* RelicLight = NewObject<UPointLightComponent>(this);
		RelicLight->SetupAttachment(Root);
		RelicLight->SetMobility(EComponentMobility::Movable);
		RelicLight->SetRelativeLocation(Spot + FVector(0.f, -150.f, 320.f));
		RelicLight->IntensityUnits = ELightUnits::Candelas;
		RelicLight->SetIntensity(40.f);
		RelicLight->SetLightColor(FLinearColor(1.f, 0.78f, 0.4f));
		RelicLight->SetAttenuationRadius(1000.f);
		RelicLight->SetCastShadows(false);
		RelicLight->RegisterComponent();
	}

	// 7b. The detail pass: rocks, rubble, timber and crystals that break up the tunnels and rooms (coop.Maze.Detail)
	BuildMazeDetail(Cells, Glow);

	AddProcMesh(Glow, GlowMaterial(), {}, false);

	// 8. Repo rocks as two instanced meshes (one draw each), when the mesh is in the project
	for (TArray<FTransform>* Transforms : { &MazeWallRockTransforms, &MazeCeilingRockTransforms })
	{
		if (!RepoRockMesh || Transforms->IsEmpty())
		{
			continue;
		}
		UInstancedStaticMeshComponent* Rocks = NewObject<UInstancedStaticMeshComponent>(this);
		Rocks->SetupAttachment(Root);
		Rocks->SetMobility(EComponentMobility::Static);
		Rocks->SetStaticMesh(RepoRockMesh);
		if (RepoRockMaterial)
		{
			Rocks->SetMaterial(0, RepoRockMaterial);
		}
		Rocks->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Rocks->SetCastShadow(false);
		Rocks->RegisterComponent();
		Rocks->AddInstances(*Transforms, false);
	}

	// 9. A dark box round the whole maze, in case a gap between rocks shows through. Its floor catches anyone who falls.
	FIntPoint MinTile(TNumericLimits<int32>::Max()), MaxTile(TNumericLimits<int32>::Lowest());
	for (const TPair<FIntPoint, TArray<FLevel>>& Cell : Cells)
	{
		MinTile = FIntPoint(FMath::Min(MinTile.X, Cell.Key.X), FMath::Min(MinTile.Y, Cell.Key.Y));
		MaxTile = FIntPoint(FMath::Max(MaxTile.X, Cell.Key.X), FMath::Max(MaxTile.Y, Cell.Key.Y));
	}
	const FVector2D Low = TileCenter(FIntPoint(MinTile.X, MaxTile.Y)) - FVector2D(2.f * Tile);
	const FVector2D High = TileCenter(FIntPoint(MaxTile.X, MinTile.Y)) + FVector2D(2.f * Tile);
	const FVector2D Mid = (Low + High) * 0.5f;
	const FVector2D Extent = High - Low;
	constexpr float ShellBottom = -1500.f;
	constexpr float ShellTop = 2600.f;
	auto AddShell = [this](const FVector& Center, const FVector& Size, bool bCollides)
	{
		if (UStaticMeshComponent* Box = AddBox(Center, Size, CoopCave::Backstop, bCollides))
		{
			Box->SetCastShadow(false);
		}
	};
	const float ShellMidZ = (ShellBottom + ShellTop) * 0.5f;
	const float ShellHeight = ShellTop - ShellBottom;
	AddShell(FVector(Low.X, Mid.Y, ShellMidZ), FVector(100.f, Extent.Y, ShellHeight), false);
	AddShell(FVector(High.X, Mid.Y, ShellMidZ), FVector(100.f, Extent.Y, ShellHeight), false);
	AddShell(FVector(Mid.X, Low.Y, ShellMidZ), FVector(Extent.X, 100.f, ShellHeight), false);
	AddShell(FVector(Mid.X, High.Y, ShellMidZ), FVector(Extent.X, 100.f, ShellHeight), false);
	AddShell(FVector(Mid.X, Mid.Y, ShellTop), FVector(Extent.X, Extent.Y, 100.f), false);
	AddShell(FVector(Mid.X, Mid.Y, ShellBottom), FVector(Extent.X, Extent.Y, 100.f), true);

	UE_LOG(LogTemp, Display, TEXT("CoopPlayground: maze built, %d tiles, %d bridges, %.0f x %.0f m, %d torches, %d repo rocks"),
		Cells.Num(), CrossingCount, (Extent.X - 2.f * Tile) / 100.f, (Extent.Y - 2.f * Tile) / 100.f, TorchLights.Num(),
		MazeWallRockTransforms.Num() + MazeCeilingRockTransforms.Num());
}

// ---------------------------------------------------------------------------
// The maze's co-op moments
// ---------------------------------------------------------------------------

float FCoopPathSpot::FloorAt(float Along) const
{
	const float Index = FMath::Clamp(Along / CoopMaze::Tile + 2.f, 0.f, float(FloorZ.Num() - 1));
	const int32 Low = FMath::Min(FMath::FloorToInt(Index), FloorZ.Num() - 2);
	return FMath::Lerp(FloorZ[Low], FloorZ[Low + 1], Index - Low);
}

float FCoopPathSpot::CeilingAt(float Along) const
{
	return CeilingZ[FMath::Clamp(FMath::RoundToInt(Along / CoopMaze::Tile) + 2, 0, CeilingZ.Num() - 1)];
}

FVector FCoopPathSpot::At(float Along, float Side, float Z) const
{
	return FVector(Origin.X, Origin.Y, 0.f) + Forward * Along + Right * Side + FVector(0.f, 0.f, Z);
}

void ACoopPlayground::BuildMoments(const TArray<FCoopPathSpot>& Spots)
{
	using namespace CoopMaze;
	const TArray<FPathSpec> Paths = MakePaths();
	constexpr float HalfWidth = Tile * 0.5f + 5.f;   // pieces reach 5 cm into the corridor's walls
	constexpr float Thin = 30.f;                     // the split tunnels' divider
	constexpr float PlateProud = 4.f;                // plates and the lift at rest, above the floor
	const FLinearColor PlateColor(0.85f, 0.62f, 0.12f);

	// A box between two distances along the path and two across it, from Bottom to Top
	auto Block = [this](const FCoopPathSpot& Spot, float Along0, float Along1, float Side0, float Side1, float Bottom, float Top, const FLinearColor& Color)
	{
		return AddShape(CubeMesh, Spot.At((Along0 + Along1) * 0.5f, (Side0 + Side1) * 0.5f, (Bottom + Top) * 0.5f),
			FVector(Along1 - Along0, Side1 - Side0, Top - Bottom), Spot.Forward.Rotation(), Color);
	};
	// The same, but movable: Active is where its centre goes when its plates are pressed
	auto MoverBlock = [this](const FCoopPathSpot& Spot, float Along0, float Along1, float Side0, float Side1, float Bottom, float Top,
		const FLinearColor& Color, const FVector& ActiveOffset) -> FCoopMover&
	{
		UStaticMeshComponent* Piece = NewObject<UStaticMeshComponent>(this);
		Piece->SetMobility(EComponentMobility::Movable);
		Piece->SetupAttachment(Root);
		Piece->SetStaticMesh(CubeMesh);
		Piece->SetRelativeLocationAndRotation(Spot.At((Along0 + Along1) * 0.5f, (Side0 + Side1) * 0.5f, (Bottom + Top) * 0.5f), Spot.Forward.Rotation());
		Piece->SetRelativeScale3D(FVector(Along1 - Along0, Side1 - Side0, Top - Bottom) / 100.f);
		Piece->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		Piece->SetCastShadow(false);
		Piece->RegisterComponent();
		Piece->SetMaterial(0, MaterialFor(Color));

		FCoopMover& Mover = Movers.AddDefaulted_GetRef();
		Mover.Piece = MoverPieces.Add(Piece);
		Mover.RestLocation = Piece->GetRelativeLocation();
		Mover.ActiveLocation = Mover.RestLocation + ActiveOffset;
		return Mover;
	};
	// A plate on the floor (tilted to match a ramp), and the box a player's feet must be in to press it
	auto Plate = [this](const FCoopPathSpot& Spot, float Along0, float Along1, float Side0, float Side1, float Z0, float Z1, const FLinearColor& Color)
	{
		const float Length = FVector2D(Along1 - Along0, Z1 - Z0).Size();
		const float Pitch = FMath::RadiansToDegrees(FMath::Atan2(Z1 - Z0, Along1 - Along0));
		AddShape(CubeMesh, Spot.At((Along0 + Along1) * 0.5f, (Side0 + Side1) * 0.5f, (Z0 + Z1) * 0.5f),
			FVector(Length, Side1 - Side0, PlateProud * 2.f), FRotator(Pitch, Spot.Forward.Rotation().Yaw, 0.f), Color);
		FBox Feet(ForceInit);
		Feet += Spot.At(Along0, Side0, FMath::Min(Z0, Z1) - 20.f);
		Feet += Spot.At(Along1, Side1, FMath::Max(Z0, Z1) + 40.f);
		return Feet;
	};

	for (int32 M = 0; M < Spots.Num(); ++M)
	{
		const FMomentSpec& Moment = Moments[M];
		const FCoopPathSpot& Spot = Spots[M];
		const FLinearColor PathColor = FLinearColor::FromSRGBColor(Paths[Moment.Path].Color);
		const FLinearColor Barrier = PathColor * 0.5f;
		const FLinearColor Helper = PathColor * 0.9f;
		const float A = Moment.Along;
		const float D = Moment.Depth;

		switch (Moment.Kind)
		{
		case EMoment::Wall:
		{
			// The wall, and the drop-down ledge behind it
			const float Floor = Spot.FloorAt(A);
			Block(Spot, A - D * 0.5f, A + D * 0.5f, -HalfWidth, HalfWidth, Floor - Slab, Floor + Moment.Height, Barrier);
			Block(Spot, A + D * 0.5f, A + D * 0.5f + Moment.Span, -HalfWidth, HalfWidth, Floor - Slab, Floor + Moment.Helper, Helper);
			break;
		}
		case EMoment::Lift:
		{
			// The cliff runs on until the ramp reaches its top
			const float Floor = Spot.FloorAt(A);
			const float Top = Floor + Moment.Height;
			float End = A + 50.f;
			while (End < A + 2.f * Tile && Spot.FloorAt(End) < Top)
			{
				End += 5.f;
			}
			Block(Spot, A, End, -HalfWidth, HalfWidth, Floor - Slab, Top, Barrier);

			// The lift, on the right in front of the cliff, and the winch plate on the left up top
			const float RestTop = Spot.FloorAt(A - Moment.Span * 0.5f) + PlateProud;
			FCoopMover& Lift = MoverBlock(Spot, A - Moment.Span - 5.f, A - 5.f, 5.f, HalfWidth - 15.f, RestTop - Moment.Height - Slab - 20.f, RestTop,
				Helper, FVector(0.f, 0.f, Top - RestTop));
			Lift.bNeedsBrace = true;
			Lift.Plates.Add(Plate(Spot, A + 30.f, A + 230.f, 15.f - HalfWidth, -30.f, Top, Top, PlateColor));
			break;
		}
		case EMoment::Split:
		{
			// The divider, from just under the floor into the ceiling
			const float Ends[] = { A - Moment.Span * 0.5f, A, A + Moment.Span * 0.5f };
			float Low = TNumericLimits<float>::Max();
			float High = TNumericLimits<float>::Lowest();
			for (const float At : Ends)
			{
				Low = FMath::Min(Low, Spot.FloorAt(At));
				High = FMath::Max(High, Spot.CeilingAt(At));
			}
			Block(Spot, Ends[0], Ends[2], -Thin * 0.5f, Thin * 0.5f, Low - Slab, High + 50.f, Barrier);

			// A block in each tunnel: the left one first
			for (const float Sign : { -1.f, 1.f })
			{
				const float Center = A + Sign * Moment.Helper * 0.5f;
				const float Floor = FMath::Min(Spot.FloorAt(Center - D * 0.5f), Spot.FloorAt(Center + D * 0.5f));
				Block(Spot, Center - D * 0.5f, Center + D * 0.5f, Sign < 0.f ? -HalfWidth : Thin * 0.5f, Sign < 0.f ? -Thin * 0.5f : HalfWidth,
					Floor - Slab, Spot.FloorAt(Center) + Moment.Height, Helper);
			}
			break;
		}
		case EMoment::Gate:
		{
			// The gate sinks into the floor to open
			const float Floor = FMath::Min(Spot.FloorAt(A - D * 0.5f), Spot.FloorAt(A + D * 0.5f));
			const float Bottom = Floor - Slab - 20.f;
			const float Top = Spot.CeilingAt(A) + 100.f;
			FCoopMover& Gate = MoverBlock(Spot, A - D * 0.5f, A + D * 0.5f, -HalfWidth, HalfWidth, Bottom, Top, Barrier,
				FVector(0.f, 0.f, Floor - 10.f - Top));
			Gate.bGate = true;
			Gate.KeepOpen += Spot.At(A - D * 0.5f - 45.f, -HalfWidth, Floor - 50.f);
			Gate.KeepOpen += Spot.At(A + D * 0.5f + 45.f, HalfWidth, Floor + 300.f);

			// The switch ledge against the left wall before it, and the plate past it
			const float LedgeAt = A + Moment.Helper;
			const float LedgeTop = Spot.FloorAt(LedgeAt) + Moment.Height;
			Block(Spot, LedgeAt - 100.f, LedgeAt + 100.f, -HalfWidth, 140.f - HalfWidth, Spot.FloorAt(LedgeAt - 100.f) - Slab, LedgeTop, Helper);
			Gate.Plates.Add(Plate(Spot, LedgeAt - 90.f, LedgeAt + 90.f, 15.f - HalfWidth, 125.f - HalfWidth, LedgeTop, LedgeTop, PlateColor));
			const float PlateAt = A + Moment.Span;
			Gate.Plates.Add(Plate(Spot, PlateAt - 80.f, PlateAt + 80.f, -100.f, 100.f, Spot.FloorAt(PlateAt - 80.f), Spot.FloorAt(PlateAt + 80.f), PlateColor));
			break;
		}
		}
	}
	UE_LOG(LogTemp, Display, TEXT("CoopPlayground: %d co-op moments, %d moving pieces"), Spots.Num(), Movers.Num());
}

void ACoopPlayground::UpdateMovers(float DeltaSeconds)
{
	if (Movers.IsEmpty())
	{
		return;
	}
	TArray<ACoopCharacter*, TInlineAllocator<2>> Players;
	for (TActorIterator<ACoopCharacter> It(GetWorld()); It; ++It)
	{
		Players.Add(*It);
	}

	for (FCoopMover& Mover : Movers)
	{
		UStaticMeshComponent* Piece = MoverPieces.IsValidIndex(Mover.Piece) ? MoverPieces[Mover.Piece].Get() : nullptr;
		if (!Piece)
		{
			continue;
		}
		bool bPressed = false;
		bool bBlocked = false;
		for (const ACoopCharacter* Player : Players)
		{
			const FVector Center = Player->GetActorLocation();
			const FVector Feet = Center - FVector(0.f, 0.f, Player->GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
			if (Player->IsGrounded() && (!Mover.bNeedsBrace || Player->IsBraced()))
			{
				for (const FBox& Plate : Mover.Plates)
				{
					bPressed |= Plate.IsInsideOrOn(Feet);
				}
			}
			bBlocked |= Mover.KeepOpen.IsValid && Mover.KeepOpen.IsInsideOrOn(Center);
		}
		const float Target = bPressed ? 1.f : 0.f;
		if (bBlocked && Target < Mover.Alpha)
		{
			continue;   // never shut a gate on someone
		}
		const float Travel = FMath::Max(FVector::Dist(Mover.RestLocation, Mover.ActiveLocation), 1.f);
		const float Speed = Mover.bGate ? CoopTuning::MazeGateSpeed() : CoopTuning::MazeLiftSpeed();
		const float Alpha = FMath::FInterpConstantTo(Mover.Alpha, Target, DeltaSeconds, Speed / Travel);
		if (Alpha != Mover.Alpha)
		{
			Mover.Alpha = Alpha;
			Piece->SetRelativeLocation(FMath::Lerp(Mover.RestLocation, Mover.ActiveLocation, Alpha));
		}
	}
}

void ACoopPlayground::FinishRockGroups()
{
	const TArray<TArray<FVector>> NoHulls;
	for (FCoopRockGroup* Group : { &WallRocks, &CeilingRocks, &Boulders, &SmallRocks, &Pebbles, &FloorStones, &MazeWallRocks, &MazeCeilingRocks })
	{
		if (!Group->Mesh.IsEmpty())
		{
			AddProcMesh(Group->Mesh, MaterialFor(Group->Color), Group->bCollides ? Group->Hulls : NoHulls, Group->bCastShadow);
		}
	}
}

// ---------------------------------------------------------------------------
// Building blocks
// ---------------------------------------------------------------------------

void ACoopPlayground::AddRock(FCoopRockGroup& Group, const FVector& GroundPoint, const FVector& Size, float Yaw,
	int32 Detail, float Jitter, float TopFlat, const FRotator& Tilt)
{
	const FQuat Rotation = FQuat(Tilt) * FQuat(FRotator(0.f, Yaw, 0.f));
	const FTransform Base(Rotation, GroundPoint);
	TArray<FVector> Hull = CoopMeshKit::AddRock(Group.Mesh, Random, Base, Size, Detail, Jitter, TopFlat);
	if (Group.bCollides)
	{
		Group.Hulls.Add(MoveTemp(Hull));
	}
}

UProceduralMeshComponent* ACoopPlayground::AddProcMesh(const FCoopMeshData& Data, UMaterialInterface* Material,
	const TArray<TArray<FVector>>& Hulls, bool bCastShadow, bool bMovable)
{
	if (Data.IsEmpty())
	{
		return nullptr;
	}

	UProceduralMeshComponent* Mesh = NewObject<UProceduralMeshComponent>(this);
	Mesh->SetupAttachment(Root);
	Mesh->SetMobility(bMovable ? EComponentMobility::Movable : EComponentMobility::Static);
	Mesh->bUseAsyncCooking = false;
	Mesh->bUseComplexAsSimpleCollision = false;
	Mesh->SetCastShadow(bCastShadow);
	Mesh->RegisterComponent();

	Mesh->CreateMeshSection(0, Data.Vertices, Data.Triangles, Data.Normals, Data.UVs, Data.Colors, TArray<FProcMeshTangent>(), false);
	if (Material)
	{
		Mesh->SetMaterial(0, Material);
	}

	if (Hulls.Num() > 0)
	{
		Mesh->SetCollisionConvexMeshes(Hulls);
		Mesh->SetCollisionProfileName(UCollisionProfile::BlockAll_ProfileName);
		Mesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	}
	else
	{
		Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}
	return Mesh;
}

UStaticMeshComponent* ACoopPlayground::AddShape(UStaticMesh* Mesh, const FVector& Center, const FVector& SizeCm,
	const FRotator& Rotation, const FLinearColor& Color, bool bCollides)
{
	UStaticMeshComponent* Shape = NewObject<UStaticMeshComponent>(this);
	Shape->SetMobility(EComponentMobility::Static);
	Shape->SetupAttachment(Root);
	Shape->SetStaticMesh(Mesh);

	// Engine shapes are 100 cm across, so scale = size / 100.
	Shape->SetRelativeLocationAndRotation(Center, Rotation);
	Shape->SetRelativeScale3D(SizeCm / 100.f);
	Shape->SetCollisionEnabled(bCollides ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
	Shape->RegisterComponent();

	if (UMaterialInstanceDynamic* Material = MaterialFor(Color))
	{
		Shape->SetMaterial(0, Material);
	}
	return Shape;
}

UStaticMeshComponent* ACoopPlayground::AddBox(const FVector& Center, const FVector& SizeCm, const FLinearColor& Color, bool bCollides)
{
	return AddShape(CubeMesh, Center, SizeCm, FRotator::ZeroRotator, Color, bCollides);
}

UStaticMeshComponent* ACoopPlayground::AddBeam(const FVector& Start, const FVector& End, float Width, float Height,
	const FLinearColor& Color, bool bCollides)
{
	const FVector Span = End - Start;
	const float Length = Span.Size();
	if (Length < 1.f)
	{
		return nullptr;
	}
	return AddShape(CubeMesh, (Start + End) * 0.5f, FVector(Length, Width, Height), Span.Rotation(), Color, bCollides);
}

UMaterialInstanceDynamic* ACoopPlayground::MaterialFor(const FLinearColor& Color)
{
	if (!BaseMaterial)
	{
		return nullptr;
	}

	const uint32 Key = Color.ToFColor(true).ToPackedARGB();
	if (TObjectPtr<UMaterialInstanceDynamic>* Found = MaterialCache.Find(Key))
	{
		return Found->Get();
	}

	UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(BaseMaterial, this);
	Material->SetVectorParameterValue(TEXT("Color"), Color);
	MaterialCache.Add(Key, Material);
	return Material;
}

UMaterialInterface* ACoopPlayground::GlowMaterial() const
{
	// The engine's vertex-color material draws the flame and crystal colors as-is (no lighting needed).
	if (GEngine && GEngine->VertexColorMaterial)
	{
		return GEngine->VertexColorMaterial;
	}
	return BaseMaterial;
}

bool ACoopPlayground::IsKeepClear(const FVector2D& Point, float Radius) const
{
	for (const FBox2D& Box : KeepClearBoxes)
	{
		if (Point.X > Box.Min.X - Radius && Point.X < Box.Max.X + Radius &&
			Point.Y > Box.Min.Y - Radius && Point.Y < Box.Max.Y + Radius)
		{
			return true;
		}
	}
	return false;
}
