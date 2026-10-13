# Original maze obstacle candidate plan

`layout.plan(root)` is pure Python. It reads the immutable PR122 connection capture
with SHA-256 `2008b7a684ba0f82d34b97fe259c20ec7abc46e09d00ead5f9c1dd8c6fcbf0ed`.
It neither opens Unreal nor creates files. Its authored set is finite; it makes no
claim about unlimited generated gameplay or accepted native movement.

The original four colors each retain three separate legs: Fork → HallA → HallB →
Relic. The grid waypoints come from `CoopPlayground.cpp MakePaths`. Strict floor
samples use captured floor records 318–321; room geometry uses original room
specifications and floor record 322. Captured component locations already contain
the X−175 connection shift. World tile centers are `(col−22)*500−175`,
`(41−row)*500`; never apply a second shift to the source actor locations.

The plan supplies original routes, rooms, 36 major clusters, smaller shoulder
rubble, four recoverable gaps, a return route and offline checks. Every major
cluster has a small sequence of choices: low step/jump/step-down, jump/mantle/drop,
boulder weave/jump shortcut, or a gap with recovery. Rounded/faceted rock visuals
should use simple explicit collision consistent with these dimensions. The
`rock` shape is a visual request, not authority to substitute an irregular hull
with an unverified landing. No large plain cube barriers, extra roofs, tube
connectors, outside rooms or new maze footprint are proposed.

Blockers remain outside original rooms. Whole major envelopes keep 10 m of room
mouth approach clear, and keep 5 m around corners, crossed layers and dead-end
junctions. Incidental rubble repeats on the remaining shoulders every 5 m, at
25–39 cm height. Existing captured scenery can still narrow these lanes; native
clearance must check it, rather than trusting a plan against floor meshes alone.

The carrier returns through **Orange leg 3, Yellow leg 2, Yellow leg 1**, in reverse.
Every blocking addition on those legs occupies the opposite shoulder. A continuous
160 cm lane at local across −100…60 remains on untouched source floor, with no new
step, gap or climb. Empty corner tiles connect the offset lane between turns.
Room transitions and the original door connector still require native verification.
The connection capture is clipped below Y3200; preserve and verify the existing
mining-door/mouth floor rather than inventing another cave or return room.

Gaps are limited to four shallow-run candidates, not every corridor. Three are
190 cm walk jumps; one is a 350 cm sprint jump with 600 cm clear approach.
Every gap has a catch floor 250–350 cm below and a 140 cm-wide same-path recovery
channel with nine ≤40 cm steps. Both its visible source floor and collision must
be cut using **both** supplied cut envelopes: the main gap and side stair channel.
Otherwise an intact slab above the stairs would trap the recovering player.
The stair channel occupies one shoulder of the forward landing; the main landing
retains 340 cm width. The pit is nonlethal and contained within the existing
500 cm corridor footprint. Amber marks identify recovery and mantle surfaces;
climbing volumes must use the existing server-validated `Climbable` contract.
Their `collision: false` means nonblocking; the explicit `overlap: true` and
`collision_mode: query_only` require capsule overlaps, not a NoCollision volume.

Primitive sizes are local `(along, across, height)` cm, with numeric world center
and yaw. Floor cuts are world-aligned AABBs; all original runs are axis-aligned.
Primitives declare collision, material category and tags. Parent implementation
owns material/mesh selection, derivative collision generation, editor placement,
compilation, saving and all binary asset changes. Source partner blocks 697–703
must be disabled/excluded by that source bake as agreed.

Run `layout.py` with a Python interpreter to check the source hash, route count,
floor samples, obstacle density, reserved envelopes, carrier lane, gap grade,
stair rises, cross-layer source-floor separation and finite JSON data. The printed
summary is staging evidence only. Required native gates remain: capsule/floor and
ceiling clearance; each jump and mantle using owning input; deliberate missed
jumps and recovery; HallA/HallB puzzle mouths and open-door return; a carried relic
through the entire return route; 2/3/4 joining clients and host split screen;
human readability and fairness at half-screen size. Keep failed placements out
of the accepted build until corrected and rechecked.

The completed offline check reports 12 original legs, 36 major clusters, 31
shoulder rubble groups, four recoverable gaps, 144 cross-layer source-floor
samples and a 160 cm carrier lane. Orange leg 3 has only one large cluster because
its short flat run, side junction and hall mouths leave no safe second full-size
site. Other segments have 2–4 major clusters. This is deliberate finite placement,
not a reason to fill protected transitions with additional blocking rocks.
