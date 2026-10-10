#include "CoopCharacter.h"

#include "CoopGameMode.h"
#include "CoopInput.h"
#include "CoopTuning.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace CoopCharacterLook
{
	// Graybox body proportions (engine cylinder/sphere/cube are 100 cm across)
	const FVector BodyScaleStanding(0.75f, 0.75f, 1.3f);
	const FVector BodyOffsetStanding(0.f, 0.f, -25.f);
	const FVector BodyScaleBraced(0.9f, 0.9f, 1.0f);
	const FVector BodyOffsetBraced(0.f, 0.f, -45.f);
	const FVector HeadOffsetStanding(0.f, 0.f, 65.f);
	const FVector HeadOffsetBraced(0.f, 0.f, 35.f);

	const FLinearColor Player1Color(0.95f, 0.35f, 0.20f); // coral
	const FLinearColor Player2Color(0.05f, 0.65f, 0.75f); // teal

	// First person: eye height above the capsule center, and where the hands sit in front of the camera
	constexpr float EyeHeight = 70.f;
	const FVector HandLeftOffset(45.f, -24.f, -26.f);
	const FVector HandRightOffset(45.f, 24.f, -26.f);
	const FVector HandScale(0.16f, 0.14f, 0.12f);

	// Look limits (degrees): first person can look further up and down
	constexpr float MinPitchThirdPerson = -65.f;
	constexpr float MaxPitchThirdPerson = 35.f;
	constexpr float MinPitchFirstPerson = -80.f;
	constexpr float MaxPitchFirstPerson = 80.f;
}

ACoopCharacter::ACoopCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);

	// The character turns toward where it's moving; the camera is controlled separately.
	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 720.f, 0.f);
	Move->MaxWalkSpeed = 500.f;
	Move->BrakingDecelerationWalking = 2000.f;
	Move->BrakingDecelerationFalling = 300.f;
	Move->GravityScale = 1.6f;      // snappier, less floaty jumps
	Move->JumpZVelocity = 760.f;    // ~1.8 m jump height with the gravity above
	Move->AirControl = 0.35f;
	Move->MaxStepHeight = 45.f;               // walk straight over small rocks (coop.StepHeight)
	Move->SetWalkableFloorAngle(50.f);        // a little forgiving on sloped rock tops
	Move->bUseFlatBaseForFloorChecks = true;  // stand steadily on rock edges

	// Camera: over-the-shoulder by default. First person moves it to eye height (see ApplyCameraMode).
	// Distance, shoulder offset, height and FOV come from the coop.Cam.* console variables every frame.
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->TargetArmLength = 380.f;
	CameraBoom->SocketOffset = FVector(0.f, 55.f, 65.f);
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 12.f;
	CameraBoom->CameraLagMaxDistance = 200.f;   // no long camera swoop after station travel

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;

	// Graybox body built from engine shapes
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShapeMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

	BodyMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BodyMesh"));
	BodyMesh->SetupAttachment(GetCapsuleComponent());
	BodyMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	BodyMesh->SetRelativeScale3D(CoopCharacterLook::BodyScaleStanding);
	BodyMesh->SetRelativeLocation(CoopCharacterLook::BodyOffsetStanding);

	HeadMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HeadMesh"));
	HeadMesh->SetupAttachment(GetCapsuleComponent());
	HeadMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	HeadMesh->SetRelativeScale3D(FVector(0.6f));
	HeadMesh->SetRelativeLocation(CoopCharacterLook::HeadOffsetStanding);

	// Small block on the face so you can see which way the character is facing
	NoseMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("NoseMesh"));
	NoseMesh->SetupAttachment(HeadMesh);
	NoseMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	NoseMesh->SetRelativeScale3D(FVector(0.35f, 0.25f, 0.25f));
	NoseMesh->SetRelativeLocation(FVector(45.f, 0.f, 0.f));

	// First-person hands: attached to the camera, only this player ever sees them
	HandLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HandLeft"));
	HandLeft->SetupAttachment(FollowCamera);
	HandRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HandRight"));
	HandRight->SetupAttachment(FollowCamera);
	HandLeft->SetRelativeLocation(CoopCharacterLook::HandLeftOffset);
	HandRight->SetRelativeLocation(CoopCharacterLook::HandRightOffset);
	for (UStaticMeshComponent* Hand : { HandLeft.Get(), HandRight.Get() })
	{
		Hand->SetRelativeScale3D(CoopCharacterLook::HandScale);
		Hand->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Hand->SetOnlyOwnerSee(true);
		Hand->SetCastShadow(false);
		Hand->SetVisibility(false);
	}

	if (CylinderMesh.Succeeded()) { BodyMesh->SetStaticMesh(CylinderMesh.Object); }
	if (SphereMesh.Succeeded())
	{
		HeadMesh->SetStaticMesh(SphereMesh.Object);
		HandLeft->SetStaticMesh(SphereMesh.Object);
		HandRight->SetStaticMesh(SphereMesh.Object);
	}
	if (CubeMesh.Succeeded())     { NoseMesh->SetStaticMesh(CubeMesh.Object); }
	if (ShapeMaterial.Succeeded()) { BaseMaterial = ShapeMaterial.Object; }
}

void ACoopCharacter::BeginPlay()
{
	Super::BeginPlay();
	SetCameraMode(CoopTuning::StartInFirstPerson() ? ECoopCameraMode::FirstPerson : ECoopCameraMode::OverShoulder);
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

void ACoopCharacter::EnsureInputConfig()
{
	if (!CoopInputConfig)
	{
		CoopInputConfig = NewObject<UCoopInput>(this);
		CoopInputConfig->Build();
	}
}

void ACoopCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	EnsureInputConfig();

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!EIC)
	{
		UE_LOG(LogTemp, Error, TEXT("CoopCharacter: Enhanced Input is not the default input component. Check Config/DefaultInput.ini."));
		return;
	}

	UCoopInput* C = CoopInputConfig;

	EIC->BindAction(C->Move,      ETriggerEvent::Triggered, this, &ACoopCharacter::OnMove);
	EIC->BindAction(C->LookStick, ETriggerEvent::Triggered, this, &ACoopCharacter::OnLookStick);
	EIC->BindAction(C->LookMouse, ETriggerEvent::Triggered, this, &ACoopCharacter::OnLookMouse);
	EIC->BindAction(C->Jump,      ETriggerEvent::Started,   this, &ACoopCharacter::OnJumpStarted);
	EIC->BindAction(C->Jump,      ETriggerEvent::Completed, this, &ACoopCharacter::OnJumpCompleted);
	EIC->BindAction(C->Brace,     ETriggerEvent::Started,   this, &ACoopCharacter::OnBraceStarted);
	EIC->BindAction(C->Brace,     ETriggerEvent::Completed, this, &ACoopCharacter::OnBraceCompleted);
	EIC->BindAction(C->Reel,      ETriggerEvent::Started,   this, &ACoopCharacter::OnReelStarted);
	EIC->BindAction(C->Reel,      ETriggerEvent::Completed, this, &ACoopCharacter::OnReelCompleted);
	EIC->BindAction(C->CameraToggle, ETriggerEvent::Started, this, &ACoopCharacter::OnCameraToggle);

	EIC->BindAction(C->StationNext,   ETriggerEvent::Started, this, &ACoopCharacter::OnStationNext);
	EIC->BindAction(C->StationPrev,   ETriggerEvent::Started, this, &ACoopCharacter::OnStationPrev);
	EIC->BindAction(C->StationReset,  ETriggerEvent::Started, this, &ACoopCharacter::OnStationReset);
	EIC->BindAction(C->StationSelect, ETriggerEvent::Started, this, &ACoopCharacter::OnStationSelect);

	// These only fire for Player 1, because only Player 1 gets the shared keyboard context.
	EIC->BindAction(C->P2CameraToggle, ETriggerEvent::Started, this, &ACoopCharacter::OnP2CameraToggle);
	EIC->BindAction(C->P2Move,  ETriggerEvent::Triggered, this, &ACoopCharacter::OnP2Move);
	EIC->BindAction(C->P2Turn,  ETriggerEvent::Triggered, this, &ACoopCharacter::OnP2Turn);
	EIC->BindAction(C->P2Jump,  ETriggerEvent::Started,   this, &ACoopCharacter::OnP2JumpStarted);
	EIC->BindAction(C->P2Jump,  ETriggerEvent::Completed, this, &ACoopCharacter::OnP2JumpCompleted);
	EIC->BindAction(C->P2Brace, ETriggerEvent::Started,   this, &ACoopCharacter::OnP2BraceStarted);
	EIC->BindAction(C->P2Brace, ETriggerEvent::Completed, this, &ACoopCharacter::OnP2BraceCompleted);
	EIC->BindAction(C->P2Reel,  ETriggerEvent::Started,   this, &ACoopCharacter::OnP2ReelStarted);
	EIC->BindAction(C->P2Reel,  ETriggerEvent::Completed, this, &ACoopCharacter::OnP2ReelCompleted);
}

void ACoopCharacter::PawnClientRestart()
{
	// Super creates the input component and calls SetupPlayerInputComponent.
	Super::PawnClientRestart();
	EnsureInputConfig();

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			Subsystem->ClearAllMappings();
			Subsystem->AddMappingContext(CoopInputConfig->PlayerContext, 0);

			if (GetLocalPlayerIndex() == 0)
			{
				Subsystem->AddMappingContext(CoopInputConfig->SharedKeyboardContext, 1);
			}
		}
	}

	ApplyPlayerColor();
}

void ACoopCharacter::PossessedBy(AController* NewController)
{
	Super::PossessedBy(NewController);
	ApplyPlayerColor();
}

// ---------------------------------------------------------------------------
// Tick: brace upkeep
// ---------------------------------------------------------------------------

void ACoopCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Pick up any console changes to speeds, jump, gravity and camera.
	ApplyLiveTuning();

	// Holding brace in the air braces you the moment you land.
	if (bBraceHeld && !bBraced && IsGrounded())
	{
		StartBrace();
	}
	// Knocked into the air while braced: let go.
	else if (bBraced && !IsGrounded())
	{
		EndBrace();
	}
}

// ---------------------------------------------------------------------------
// Input API
// ---------------------------------------------------------------------------

void ACoopCharacter::InputMove(const FVector2D& Axis)
{
	AController* C = GetController();
	if (bBraced || !C)
	{
		return;
	}

	const FRotator YawOnly(0.f, C->GetControlRotation().Yaw, 0.f);
	const FRotationMatrix Basis(YawOnly);
	AddMovementInput(Basis.GetUnitAxis(EAxis::X), static_cast<float>(Axis.Y));
	AddMovementInput(Basis.GetUnitAxis(EAxis::Y), static_cast<float>(Axis.X));
}

void ACoopCharacter::InputLookDegrees(float YawDegrees, float PitchDegrees)
{
	AController* C = GetController();
	if (!C)
	{
		return;
	}

	const bool bFirstPerson = (CameraMode == ECoopCameraMode::FirstPerson);
	const float MinPitch = bFirstPerson ? CoopCharacterLook::MinPitchFirstPerson : CoopCharacterLook::MinPitchThirdPerson;
	const float MaxPitch = bFirstPerson ? CoopCharacterLook::MaxPitchFirstPerson : CoopCharacterLook::MaxPitchThirdPerson;

	FRotator R = C->GetControlRotation();
	R.Yaw += YawDegrees;
	R.Pitch = FMath::Clamp(FRotator::NormalizeAxis(R.Pitch) + PitchDegrees, MinPitch, MaxPitch);
	R.Roll = 0.f;
	C->SetControlRotation(R);
}

void ACoopCharacter::InputJumpPressed()
{
	if (bBraced)
	{
		return;
	}

	// Boost jump: jump next to your braced partner to launch off them.
	ACoopCharacter* Partner = GetPartner();
	if (Partner && Partner->IsBraced() && IsGrounded())
	{
		const FVector ToPartner = Partner->GetActorLocation() - GetActorLocation();
		const bool bCloseEnough = FVector2D(ToPartner.X, ToPartner.Y).Size() <= CoopTuning::BoostRange()
			&& FMath::Abs(ToPartner.Z) < 150.f;

		if (bCloseEnough)
		{
			const FVector Forward = GetActorForwardVector().GetSafeNormal2D();
			LaunchCharacter(Forward * CoopTuning::BoostForward() + FVector(0.f, 0.f, CoopTuning::BoostUp()), true, true);
			return;
		}
	}

	Jump();
}

void ACoopCharacter::InputJumpReleased()
{
	StopJumping();
}

void ACoopCharacter::SetBraceHeld(bool bHeld)
{
	bBraceHeld = bHeld;

	if (bHeld && IsGrounded())
	{
		StartBrace();
	}
	else if (!bHeld)
	{
		EndBrace();
	}
}

void ACoopCharacter::SetReelHeld(bool bHeld)
{
	bReelHeld = bHeld;
}

void ACoopCharacter::StartBrace()
{
	if (bBraced)
	{
		return;
	}
	bBraced = true;
	GetCharacterMovement()->StopMovementImmediately();
	UpdateBraceVisual();
}

void ACoopCharacter::EndBrace()
{
	if (!bBraced)
	{
		return;
	}
	bBraced = false;
	UpdateBraceVisual();
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

bool ACoopCharacter::IsGrounded() const
{
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	return Move && Move->IsMovingOnGround();
}

int32 ACoopCharacter::GetLocalPlayerIndex() const
{
	const APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC)
	{
		return -1;
	}
	for (int32 Index = 0; Index < 2; ++Index)
	{
		if (UGameplayStatics::GetPlayerController(this, Index) == PC)
		{
			return Index;
		}
	}
	return -1;
}

ACoopCharacter* ACoopCharacter::GetPartner() const
{
	const int32 Me = GetLocalPlayerIndex();
	if (Me < 0)
	{
		return nullptr;
	}
	return Cast<ACoopCharacter>(UGameplayStatics::GetPlayerCharacter(this, Me == 0 ? 1 : 0));
}

// ---------------------------------------------------------------------------
// Tether + respawn
// ---------------------------------------------------------------------------

void ACoopCharacter::ApplyTetherPull(const FVector& Offset, const FVector& DirToPartner)
{
	UCharacterMovementComponent* Move = GetCharacterMovement();
	FVector Delta = Offset;

	if (IsGrounded())
	{
		if (DirToPartner.Z > 0.5f)
		{
			// Partner is well above us and pulling: lift off so we can be hauled up a wall.
			Move->SetMovementMode(MOVE_Falling);
		}
		else
		{
			// On the ground, the rope drags us along the floor, never into it.
			Delta.Z = 0.f;
		}
	}

	// Move, and if we hit a wall, slide along it instead of stopping dead.
	FHitResult Hit;
	AddActorWorldOffset(Delta, true, &Hit);
	if (Hit.IsValidBlockingHit())
	{
		const FVector Remaining = Delta * (1.f - Hit.Time);
		AddActorWorldOffset(FVector::VectorPlaneProject(Remaining, Hit.Normal), true);
	}

	// Remove any velocity that would stretch the rope further. What's left is
	// sideways motion, which is what makes a dangling character swing.
	const float Outward = static_cast<float>(FVector::DotProduct(Move->Velocity, -DirToPartner));
	if (Outward > 0.f)
	{
		Move->Velocity += DirToPartner * Outward;
	}
}

void ACoopCharacter::ResetTo(const FVector& Location)
{
	EndBrace();
	SetActorLocation(Location, false, nullptr, ETeleportType::TeleportPhysics);
	GetCharacterMovement()->StopMovementImmediately();
	GetCharacterMovement()->SetMovementMode(MOVE_Falling);
}

// ---------------------------------------------------------------------------
// Visuals
// ---------------------------------------------------------------------------

void ACoopCharacter::ApplyPlayerColor()
{
	if (!BodyMaterial && BaseMaterial)
	{
		BodyMaterial = UMaterialInstanceDynamic::Create(BaseMaterial, this);
		BodyMesh->SetMaterial(0, BodyMaterial);
		HeadMesh->SetMaterial(0, BodyMaterial);
		HandLeft->SetMaterial(0, BodyMaterial);
		HandRight->SetMaterial(0, BodyMaterial);
	}
	if (!BodyMaterial)
	{
		return;
	}

	FLinearColor Color = (GetLocalPlayerIndex() == 1)
		? CoopCharacterLook::Player2Color
		: CoopCharacterLook::Player1Color;

	if (bBraced)
	{
		Color = Color * 0.45f;   // darker while braced
		Color.A = 1.f;
	}

	BodyMaterial->SetVectorParameterValue(TEXT("Color"), Color);
}

void ACoopCharacter::UpdateBraceVisual()
{
	BodyMesh->SetRelativeScale3D(bBraced ? CoopCharacterLook::BodyScaleBraced : CoopCharacterLook::BodyScaleStanding);
	BodyMesh->SetRelativeLocation(bBraced ? CoopCharacterLook::BodyOffsetBraced : CoopCharacterLook::BodyOffsetStanding);
	HeadMesh->SetRelativeLocation(bBraced ? CoopCharacterLook::HeadOffsetBraced : CoopCharacterLook::HeadOffsetStanding);
	ApplyPlayerColor();
}

// ---------------------------------------------------------------------------
// Own controls
// ---------------------------------------------------------------------------

void ACoopCharacter::OnMove(const FInputActionValue& Value)
{
	InputMove(Value.Get<FVector2D>());
}

void ACoopCharacter::OnLookStick(const FInputActionValue& Value)
{
	const FVector2D V = Value.Get<FVector2D>();
	const float Dt = GetWorld()->GetDeltaSeconds();
	InputLookDegrees(static_cast<float>(V.X) * CoopTuning::StickYawRate() * Dt,
		static_cast<float>(V.Y) * CoopTuning::StickPitchRate() * Dt);
}

void ACoopCharacter::OnLookMouse(const FInputActionValue& Value)
{
	const FVector2D V = Value.Get<FVector2D>();
	const float Sensitivity = CoopTuning::MouseSensitivity();
	InputLookDegrees(static_cast<float>(V.X) * Sensitivity, static_cast<float>(V.Y) * Sensitivity);
}

void ACoopCharacter::OnJumpStarted()    { InputJumpPressed(); }
void ACoopCharacter::OnJumpCompleted()  { InputJumpReleased(); }
void ACoopCharacter::OnBraceStarted()   { SetBraceHeld(true); }
void ACoopCharacter::OnBraceCompleted() { SetBraceHeld(false); }
void ACoopCharacter::OnReelStarted()    { SetReelHeld(true); }
void ACoopCharacter::OnReelCompleted()  { SetReelHeld(false); }
void ACoopCharacter::OnCameraToggle()   { ToggleCameraMode(); }

// ---------------------------------------------------------------------------
// Camera modes + live tuning
// ---------------------------------------------------------------------------

void ACoopCharacter::ToggleCameraMode()
{
	SetCameraMode(CameraMode == ECoopCameraMode::FirstPerson ? ECoopCameraMode::OverShoulder : ECoopCameraMode::FirstPerson);

	if (GEngine)
	{
		const int32 PlayerNumber = GetLocalPlayerIndex() + 1;
		const TCHAR* ModeName = (CameraMode == ECoopCameraMode::FirstPerson) ? TEXT("first person") : TEXT("over-the-shoulder");
		GEngine->AddOnScreenDebugMessage(-1, 2.f, FColor::White, FString::Printf(TEXT("P%d camera: %s"), PlayerNumber, ModeName));
	}
}

void ACoopCharacter::SetCameraMode(ECoopCameraMode NewMode)
{
	CameraMode = NewMode;
	ApplyCameraMode();
}

void ACoopCharacter::ApplyCameraMode()
{
	const bool bFirstPerson = (CameraMode == ECoopCameraMode::FirstPerson);

	// First person: the body turns with the camera. Over-the-shoulder: the body turns toward where you move.
	bUseControllerRotationYaw = bFirstPerson;
	GetCharacterMovement()->bOrientRotationToMovement = !bFirstPerson;

	// First person: camera sits at eye height, no lag, no pulling in on walls.
	CameraBoom->SetRelativeLocation(bFirstPerson ? FVector(0.f, 0.f, CoopCharacterLook::EyeHeight) : FVector::ZeroVector);
	CameraBoom->bDoCollisionTest = !bFirstPerson;
	CameraBoom->bEnableCameraLag = !bFirstPerson;

	// Hide your own body from your own camera in first person (your partner still sees it), show your hands.
	BodyMesh->SetOwnerNoSee(bFirstPerson);
	HeadMesh->SetOwnerNoSee(bFirstPerson);
	NoseMesh->SetOwnerNoSee(bFirstPerson);
	HandLeft->SetVisibility(bFirstPerson);
	HandRight->SetVisibility(bFirstPerson);

	ApplyLiveTuning();
}

void ACoopCharacter::ApplyLiveTuning()
{
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = CoopTuning::WalkSpeed();
	Move->JumpZVelocity = CoopTuning::JumpVelocity();
	Move->GravityScale = CoopTuning::GravityScale();
	Move->AirControl = CoopTuning::AirControl();
	Move->MaxStepHeight = CoopTuning::StepHeight();

	if (CameraMode == ECoopCameraMode::FirstPerson)
	{
		CameraBoom->TargetArmLength = 0.f;
		CameraBoom->SocketOffset = FVector::ZeroVector;
		FollowCamera->SetFieldOfView(CoopTuning::FirstPersonFOV());
	}
	else
	{
		CameraBoom->TargetArmLength = CoopTuning::CamDistance();
		CameraBoom->SocketOffset = FVector(0.f, CoopTuning::CamShoulder(), CoopTuning::CamHeight());
		FollowCamera->SetFieldOfView(CoopTuning::CamFOV());
	}
}

// ---------------------------------------------------------------------------
// Playground travel (moves both players)
// ---------------------------------------------------------------------------

ACoopGameMode* ACoopCharacter::GetCoopGameMode() const
{
	UWorld* World = GetWorld();
	return World ? World->GetAuthGameMode<ACoopGameMode>() : nullptr;
}

void ACoopCharacter::OnStationNext()  { if (ACoopGameMode* GM = GetCoopGameMode()) { GM->StepStation(1); } }
void ACoopCharacter::OnStationPrev()  { if (ACoopGameMode* GM = GetCoopGameMode()) { GM->StepStation(-1); } }
void ACoopCharacter::OnStationReset() { if (ACoopGameMode* GM = GetCoopGameMode()) { GM->ResetStation(); } }

void ACoopCharacter::OnStationSelect(const FInputActionValue& Value)
{
	// Number keys arrive as their number (1-6), stations are counted from 0.
	const int32 StationNumber = FMath::RoundToInt(Value.Get<float>());
	if (ACoopGameMode* GM = GetCoopGameMode())
	{
		GM->GoToStation(StationNumber - 1);
	}
}

// ---------------------------------------------------------------------------
// Player 1's keyboard driving Player 2
// ---------------------------------------------------------------------------

void ACoopCharacter::OnP2Move(const FInputActionValue& Value)
{
	if (ACoopCharacter* P2 = GetPartner()) { P2->InputMove(Value.Get<FVector2D>()); }
}

void ACoopCharacter::OnP2Turn(const FInputActionValue& Value)
{
	if (ACoopCharacter* P2 = GetPartner())
	{
		P2->InputLookDegrees(Value.Get<float>() * CoopTuning::StickYawRate() * GetWorld()->GetDeltaSeconds(), 0.f);
	}
}

void ACoopCharacter::OnP2JumpStarted()    { if (ACoopCharacter* P2 = GetPartner()) { P2->InputJumpPressed(); } }
void ACoopCharacter::OnP2JumpCompleted()  { if (ACoopCharacter* P2 = GetPartner()) { P2->InputJumpReleased(); } }
void ACoopCharacter::OnP2BraceStarted()   { if (ACoopCharacter* P2 = GetPartner()) { P2->SetBraceHeld(true); } }
void ACoopCharacter::OnP2BraceCompleted() { if (ACoopCharacter* P2 = GetPartner()) { P2->SetBraceHeld(false); } }
void ACoopCharacter::OnP2ReelStarted()    { if (ACoopCharacter* P2 = GetPartner()) { P2->SetReelHeld(true); } }
void ACoopCharacter::OnP2ReelCompleted()  { if (ACoopCharacter* P2 = GetPartner()) { P2->SetReelHeld(false); } }
void ACoopCharacter::OnP2CameraToggle()   { if (ACoopCharacter* P2 = GetPartner()) { P2->ToggleCameraMode(); } }
