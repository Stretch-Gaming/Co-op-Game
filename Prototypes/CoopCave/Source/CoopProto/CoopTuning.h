#pragma once

#include "CoreMinimal.h"

/**
 * Every "feel" number in the game, as live console variables.
 *
 * Change them while playing: press the ` key (left of 1) to open the console,
 * type  coop.  and press Tab to see them all, then e.g.  coop.Boost.Up 1500
 * Typing a name alone prints its current value.
 *
 * To keep a value you like, add it to Config/DefaultEngine.ini under [ConsoleVariables],
 * e.g.  coop.Boost.Up=1500
 */
namespace CoopTuning
{
	// Movement
	float WalkSpeed();        // coop.WalkSpeed       cm/s
	float JumpVelocity();     // coop.JumpVelocity    cm/s upward
	float GravityScale();     // coop.Gravity         1 = normal gravity
	float AirControl();       // coop.AirControl      0..1
	float StepHeight();       // coop.StepHeight      cm, tallest bump you walk straight over

	// Boost jump (jump next to a braced partner)
	float BoostUp();          // coop.Boost.Up        cm/s upward
	float BoostForward();     // coop.Boost.Forward   cm/s forward
	float BoostRange();       // coop.Boost.Range     cm, how close you must be

	// Rope
	bool  TetherEnabled();    // coop.Tether          1 = tie the players together (takes effect on the next Play)
	float RopeMaxLength();    // coop.Rope.MaxLength  cm
	float RopeMinLength();    // coop.Rope.MinLength  cm, shortest you can reel in to
	float ReelSpeed();        // coop.Rope.ReelSpeed  cm/s
	float DragSpeed();        // coop.Rope.DragSpeed  cm/s, a hanging partner dragging you
	float AirborneWeight();   // coop.Rope.AirWeight  how much harder the rope pulls someone in the air

	// Camera
	float CamDistance();      // coop.Cam.Distance    over-the-shoulder distance, cm
	float CamShoulder();      // coop.Cam.Shoulder    sideways offset, cm
	float CamHeight();        // coop.Cam.Height      height offset, cm
	float CamFOV();           // coop.Cam.FOV         over-the-shoulder field of view, degrees
	float FirstPersonFOV();   // coop.Cam.FPFOV       first-person field of view, degrees
	bool  StartInFirstPerson(); // coop.Cam.StartFirstPerson  0 or 1

	// Cave lighting (the work area)
	float TorchBrightness();  // coop.Cave.Torch         candelas per torch
	float TorchRadius();      // coop.Cave.TorchRadius   cm, how far torch light reaches
	int32 TorchShadowMode();  // coop.Cave.TorchShadows  0 = none, 1 = key torches only, 2 = every torch
	float TorchFlicker();     // coop.Cave.Flicker       0 = steady .. 0.3 = very flickery
	float TorchBounce();      // coop.Cave.Bounce        warm fill near each torch, as a fraction of the torch
	float CrystalBrightness();// coop.Cave.Crystal       candelas for the teal crystal light
	float CaveAmbient();      // coop.Cave.Ambient       cool fill light in the shadows
	float CaveExposure();     // coop.Cave.Exposure      camera exposure, in stops (+1 = twice as bright)
	float CaveFog();          // coop.Cave.Fog           haze density near the floor

	// Look
	float StickYawRate();     // coop.Look.StickYaw    degrees/s at full stick
	float StickPitchRate();   // coop.Look.StickPitch  degrees/s at full stick
	float MouseSensitivity(); // coop.Look.Mouse       degrees per mouse unit
}
