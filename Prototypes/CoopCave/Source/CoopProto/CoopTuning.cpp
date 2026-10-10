#include "CoopTuning.h"

#include "HAL/IConsoleManager.h"

namespace CoopTuningVars
{
	// Movement
	static TAutoConsoleVariable<float> CVarWalkSpeed(TEXT("coop.WalkSpeed"), 500.f, TEXT("Walk speed in cm/s."));
	static TAutoConsoleVariable<float> CVarJumpVelocity(TEXT("coop.JumpVelocity"), 760.f, TEXT("Jump speed upward in cm/s (760 = about 1.8 m jump)."));
	static TAutoConsoleVariable<float> CVarGravity(TEXT("coop.Gravity"), 1.6f, TEXT("Gravity multiplier. Higher = snappier, less floaty."));
	static TAutoConsoleVariable<float> CVarAirControl(TEXT("coop.AirControl"), 0.35f, TEXT("How much you can steer in the air, 0 to 1."));
	static TAutoConsoleVariable<float> CVarStepHeight(TEXT("coop.StepHeight"), 45.f, TEXT("Tallest bump (cm) you walk straight over without jumping. Small rocks are 12-32 cm."));

	// Boost jump
	static TAutoConsoleVariable<float> CVarBoostUp(TEXT("coop.Boost.Up"), 1300.f, TEXT("Boost jump upward speed in cm/s."));
	static TAutoConsoleVariable<float> CVarBoostForward(TEXT("coop.Boost.Forward"), 250.f, TEXT("Boost jump forward speed in cm/s."));
	static TAutoConsoleVariable<float> CVarBoostRange(TEXT("coop.Boost.Range"), 200.f, TEXT("How close (cm) you must be to your braced partner to boost."));

	// Rope
	static TAutoConsoleVariable<int32> CVarTether(TEXT("coop.Tether"), 0, TEXT("1 = tie the players together with the rope. Takes effect the next time you press Play."));
	static TAutoConsoleVariable<float> CVarRopeMax(TEXT("coop.Rope.MaxLength"), 800.f, TEXT("Longest the rope can get, cm."));
	static TAutoConsoleVariable<float> CVarRopeMin(TEXT("coop.Rope.MinLength"), 90.f, TEXT("Shortest you can reel the rope in to, cm."));
	static TAutoConsoleVariable<float> CVarReelSpeed(TEXT("coop.Rope.ReelSpeed"), 300.f, TEXT("Reel speed, cm/s."));
	static TAutoConsoleVariable<float> CVarDragSpeed(TEXT("coop.Rope.DragSpeed"), 250.f, TEXT("How fast a hanging partner drags an unbraced player, cm/s."));
	static TAutoConsoleVariable<float> CVarAirWeight(TEXT("coop.Rope.AirWeight"), 3.f, TEXT("How much harder the rope pulls a player who is in the air."));

	// Camera
	static TAutoConsoleVariable<float> CVarCamDistance(TEXT("coop.Cam.Distance"), 380.f, TEXT("Over-the-shoulder camera distance, cm."));
	static TAutoConsoleVariable<float> CVarCamShoulder(TEXT("coop.Cam.Shoulder"), 55.f, TEXT("Over-the-shoulder sideways offset, cm (negative = left shoulder)."));
	static TAutoConsoleVariable<float> CVarCamHeight(TEXT("coop.Cam.Height"), 65.f, TEXT("Over-the-shoulder height offset, cm."));
	static TAutoConsoleVariable<float> CVarCamFOV(TEXT("coop.Cam.FOV"), 90.f, TEXT("Over-the-shoulder field of view, degrees."));
	static TAutoConsoleVariable<float> CVarFirstPersonFOV(TEXT("coop.Cam.FPFOV"), 95.f, TEXT("First-person field of view, degrees."));
	static TAutoConsoleVariable<int32> CVarStartFirstPerson(TEXT("coop.Cam.StartFirstPerson"), 0, TEXT("1 = players start in first person, 0 = over-the-shoulder."));

	// Cave lighting
	static TAutoConsoleVariable<float> CVarTorch(TEXT("coop.Cave.Torch"), 55.f, TEXT("Torch brightness, candelas."));
	static TAutoConsoleVariable<float> CVarTorchRadius(TEXT("coop.Cave.TorchRadius"), 900.f, TEXT("How far torch light reaches, cm."));
	static TAutoConsoleVariable<int32> CVarTorchShadows(TEXT("coop.Cave.TorchShadows"), 1, TEXT("Torch shadows: 0 = none, 1 = the four torches out in the room (default), 2 = every torch (slow on a Mac)."));
	static TAutoConsoleVariable<float> CVarFlicker(TEXT("coop.Cave.Flicker"), 0.12f, TEXT("Torch flicker: 0 = steady, 0.3 = very flickery."));
	static TAutoConsoleVariable<float> CVarBounce(TEXT("coop.Cave.Bounce"), 0.1f, TEXT("Warm fill light in front of each torch, as a fraction of its brightness."));
	static TAutoConsoleVariable<float> CVarCrystal(TEXT("coop.Cave.Crystal"), 24.f, TEXT("Teal crystal light brightness, candelas."));
	static TAutoConsoleVariable<float> CVarAmbient(TEXT("coop.Cave.Ambient"), 0.55f, TEXT("Cool fill light in the shadows (sky light intensity)."));
	static TAutoConsoleVariable<float> CVarExposure(TEXT("coop.Cave.Exposure"), 0.f, TEXT("Camera exposure in stops: +1 = twice as bright, -1 = half."));
	static TAutoConsoleVariable<float> CVarFog(TEXT("coop.Cave.Fog"), 0.08f, TEXT("Haze density near the floor."));

	// Look
	static TAutoConsoleVariable<float> CVarStickYaw(TEXT("coop.Look.StickYaw"), 170.f, TEXT("Right-stick turn speed, degrees/s."));
	static TAutoConsoleVariable<float> CVarStickPitch(TEXT("coop.Look.StickPitch"), 110.f, TEXT("Right-stick up/down speed, degrees/s."));
	static TAutoConsoleVariable<float> CVarMouse(TEXT("coop.Look.Mouse"), 2.5f, TEXT("Mouse sensitivity, degrees per mouse unit."));
}


float CoopTuning::WalkSpeed()        { return CoopTuningVars::CVarWalkSpeed.GetValueOnGameThread(); }
float CoopTuning::JumpVelocity()     { return CoopTuningVars::CVarJumpVelocity.GetValueOnGameThread(); }
float CoopTuning::GravityScale()     { return CoopTuningVars::CVarGravity.GetValueOnGameThread(); }
float CoopTuning::AirControl()       { return CoopTuningVars::CVarAirControl.GetValueOnGameThread(); }
float CoopTuning::StepHeight()       { return CoopTuningVars::CVarStepHeight.GetValueOnGameThread(); }

float CoopTuning::BoostUp()          { return CoopTuningVars::CVarBoostUp.GetValueOnGameThread(); }
float CoopTuning::BoostForward()     { return CoopTuningVars::CVarBoostForward.GetValueOnGameThread(); }
float CoopTuning::BoostRange()       { return CoopTuningVars::CVarBoostRange.GetValueOnGameThread(); }

bool  CoopTuning::TetherEnabled()    { return CoopTuningVars::CVarTether.GetValueOnGameThread() != 0; }
float CoopTuning::RopeMaxLength()    { return CoopTuningVars::CVarRopeMax.GetValueOnGameThread(); }
float CoopTuning::RopeMinLength()    { return CoopTuningVars::CVarRopeMin.GetValueOnGameThread(); }
float CoopTuning::ReelSpeed()        { return CoopTuningVars::CVarReelSpeed.GetValueOnGameThread(); }
float CoopTuning::DragSpeed()        { return CoopTuningVars::CVarDragSpeed.GetValueOnGameThread(); }
float CoopTuning::AirborneWeight()   { return CoopTuningVars::CVarAirWeight.GetValueOnGameThread(); }

float CoopTuning::CamDistance()      { return CoopTuningVars::CVarCamDistance.GetValueOnGameThread(); }
float CoopTuning::CamShoulder()      { return CoopTuningVars::CVarCamShoulder.GetValueOnGameThread(); }
float CoopTuning::CamHeight()        { return CoopTuningVars::CVarCamHeight.GetValueOnGameThread(); }
float CoopTuning::CamFOV()           { return CoopTuningVars::CVarCamFOV.GetValueOnGameThread(); }
float CoopTuning::FirstPersonFOV()   { return CoopTuningVars::CVarFirstPersonFOV.GetValueOnGameThread(); }
bool  CoopTuning::StartInFirstPerson() { return CoopTuningVars::CVarStartFirstPerson.GetValueOnGameThread() != 0; }

float CoopTuning::TorchBrightness()  { return CoopTuningVars::CVarTorch.GetValueOnGameThread(); }
float CoopTuning::TorchRadius()      { return CoopTuningVars::CVarTorchRadius.GetValueOnGameThread(); }
int32 CoopTuning::TorchShadowMode()  { return CoopTuningVars::CVarTorchShadows.GetValueOnGameThread(); }
float CoopTuning::TorchFlicker()     { return CoopTuningVars::CVarFlicker.GetValueOnGameThread(); }
float CoopTuning::TorchBounce()      { return CoopTuningVars::CVarBounce.GetValueOnGameThread(); }
float CoopTuning::CrystalBrightness(){ return CoopTuningVars::CVarCrystal.GetValueOnGameThread(); }
float CoopTuning::CaveAmbient()      { return CoopTuningVars::CVarAmbient.GetValueOnGameThread(); }
float CoopTuning::CaveExposure()     { return CoopTuningVars::CVarExposure.GetValueOnGameThread(); }
float CoopTuning::CaveFog()          { return CoopTuningVars::CVarFog.GetValueOnGameThread(); }

float CoopTuning::StickYawRate()     { return CoopTuningVars::CVarStickYaw.GetValueOnGameThread(); }
float CoopTuning::StickPitchRate()   { return CoopTuningVars::CVarStickPitch.GetValueOnGameThread(); }
float CoopTuning::MouseSensitivity() { return CoopTuningVars::CVarMouse.GetValueOnGameThread(); }
