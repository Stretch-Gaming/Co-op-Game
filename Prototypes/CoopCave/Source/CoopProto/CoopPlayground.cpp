#include "CoopPlayground.h"

#include "CoopTuning.h"
#include "Components/BoxComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
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
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
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
	FinishRockGroups();
}

void ACoopPlayground::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
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
		}
		if (BounceLights.IsValidIndex(i) && BounceLights[i])
		{
			BounceLights[i]->SetIntensity(Base * Bounce * Scale);
		}
		if (TorchFlames.IsValidIndex(i) && TorchFlames[i])
		{
			const float Grow = Scale - 1.f;
			TorchFlames[i]->SetRelativeScale3D(FVector(1.f + 0.4f * Grow, 1.f + 0.4f * Grow, 1.f + 1.1f * Grow));
		}
	}
	LastShadowMode = ShadowMode;

	if (CrystalLight)
	{
		const float Pulse = 1.f + 0.06f * FMath::Sin(TimeSeconds * 1.3f);
		CrystalLight->SetIntensity(CoopTuning::CrystalBrightness() * Pulse);
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
	AddBlocker(FVector(Wall, 0.f, 500.f), FVector(60.f, Half + 200.f, 600.f));
	AddBlocker(FVector(-Wall, 0.f, 500.f), FVector(60.f, Half + 200.f, 600.f));
	AddBlocker(FVector(0.f, Wall, 500.f), FVector(Half + 200.f, 60.f, 600.f));
	AddBlocker(FVector(0.f, -Wall, 500.f), FVector(Half + 200.f, 60.f, 600.f));
	AddBlocker(FVector(0.f, 0.f, BlockerCeilingZ + 50.f), FVector(Half + 200.f, Half + 200.f, 50.f));

	// Dark backstop far behind the rock walls, in case a gap shows through
	auto AddBackstop = [this](const FVector& Center, const FVector& Size)
	{
		if (UStaticMeshComponent* Box = AddBox(Center, Size, Backstop, false))
		{
			Box->SetCastShadow(false);
		}
	};
	AddBackstop(FVector(2000.f, 0.f, 600.f), FVector(100.f, 4200.f, 1600.f));
	AddBackstop(FVector(-2000.f, 0.f, 600.f), FVector(100.f, 4200.f, 1600.f));
	AddBackstop(FVector(0.f, 2000.f, 600.f), FVector(4200.f, 100.f, 1600.f));
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

			AddRock(WallRocks, SidePoint(Side, Along, Out) + FVector(0.f, 0.f, -40.f), FVector(Width, Depth, Height),
				SideYaw + Random.FRandRange(-18.f, 18.f), 1, 0.22f, 0.25f);

			// Upper tier up to the ceiling
			if (Height < 700.f)
			{
				const float UpperHeight = CeilingZ + 220.f - (Height - 140.f);
				AddRock(WallRocks, SidePoint(Side, Along + Random.FRandRange(-80.f, 80.f), Out + 90.f) + FVector(0.f, 0.f, Height - 140.f),
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

void ACoopPlayground::FinishRockGroups()
{
	const TArray<TArray<FVector>> NoHulls;
	for (FCoopRockGroup* Group : { &WallRocks, &CeilingRocks, &Boulders, &SmallRocks, &Pebbles, &FloorStones })
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
