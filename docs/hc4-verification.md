# HC-4 carrying delivery — #10

Owner: Stretch. Blueprint-only implementation, confined to the authorized carrying assets, HC4 fixtures, tools and this document. No hosted subagents were used.

The attached worktree is `C:\Users\Stretch\.codex\worktrees\hc4-carrying\Co op Game`, branch `codex/hc4-carrying`, created from `origin/main` at `dcecbab75999f1cc976d847a24912f4246ddbc8e`. Its editor uses MCP port **8024** and PIE server port **17774**. Authoring and UI requests verify this exact project. Existing editor sessions and the original repository are preserved.

## Runtime API and state

Attach `/Game/Puzzles/Carrying/AC_Carrying` once to each character. Component replication is enabled in the asset. The component has no input or RPC events; it is called by the owning character's server-side interaction and Drop hooks.

| AC_Carrying function | Input / output | Server behavior |
| --- | --- | --- |
| `TryPickup(Item)` | Actor → `Success` bool | Rejects invalid/non-carryable items, an occupied carrying slot, a non-character owner, the `Downed` tag, distance over 250 cm and obstructed line of sight. Claims the item synchronously, then records it and applies speed. |
| `DropCarried()` | No parameters | Detaches the carried item, enables its collision and physics, applies a small forward impulse, clears the slot and restores speed. Empty calls are harmless. |
| `GetCarried()` | → `Item` Actor | Returns the current item. |
| `ReleaseCarried()` | → `Item` Actor | Returns the item after its handoff transition. Empty calls return None. |

These four functions are **server-only**. Client calls to mutating functions do nothing; `TryPickup` returns false and getters/handoff return None on clients. `CarriedItem` is replicated for presentation, but the public getter intentionally retains the server-only contract.

`BP_Carryable` implements `BPI_Interactable` as an instant pickup and `BPI_RoundReset.ResetForRound(Index, Attempt)` as a server reset. Its internal `Claim` has no latent work, so competing requests cannot share one item. `BP_KeyRelic` and `BP_Statue` inherit it and set the `Heavy` boolean (the documented bHeavy behavior).

| CarryState | Carrier / attachment | Collision / physics |
| --- | --- | --- |
| `0` — free | None; detached | PhysicsActor, QueryAndPhysics, simulating |
| `1` — carried | Replicated character; attached to its root at local `(100, 0, 15)` cm | NoCollision, physics off |
| `2` — placed | Carrier cleared; handoff receiver may attach/place it | PhysicsActor, QueryAndPhysics, physics off |

Carrier and CarryState use RepNotify. Both notifications and BeginPlay apply the representation. A 0.1-second reconciliation timer handles replication order and unresolved late-join references. Native attachment and movement replication are enabled. The physics mesh is the root, movable and overlap-enabled. The placed reconciliation path preserves a receiver's attachment.

**BP_Carryable.ReleaseCarried() contract:** server-only, no inputs, returns `Item` (self on successful handoff, otherwise None). It detaches, clears the component's carrying slot, restores movement speed and changes the item to placed **without enabling physics**. It does not implement an altar or round progression. A receiver can take ownership of positioning/attachment after this call. `AC_Carrying.ReleaseCarried()` forwards this contract and returns the same actor.

Heavy pickup captures the character's current walking and crouched maximum speeds, then halves both. RepNotify speed values apply on the server and owning client. Drop, handoff and reset restore the captured values rather than assuming a production speed. The fixtures start at 600/300 cm/s and therefore carry heavy items at 300/150 cm/s. Core/HZ must coordinate any other speed system with this captured baseline.

On the **server only**, heavy free or placed items have actor tag `HC_PlateWeight`. Carried items lose it. Drop/reset restore it. Actor tags are not a client authority source. The HC4 TriggerBox fixture queries overlapping actors and counts this tag only in the server world.

## Exact Core handoff

The Core integration chat owns all of these production changes; none are included here:

1. Add one replicated `AC_Carrying` component to `BP_CoopCharacter`. Its root-relative carry offset needs no saved reference to another actor or sublevel.
2. Retain HC-1's local Interact → owning-character `Server_InteractBegin(Target)` → validated `BPI_Interactable.Interact(Instigator)` path. `BP_Carryable` finds `AC_Carrying` on that instigator and calls `TryPickup(self)`. Interact never calls Drop.
3. Connect the owning local character's existing `IA_Drop.Started` to a **reliable Run on Server character event** such as `Server_DropCarried()`. The server event validates the character's component and calls `DropCarried()`; it takes no client-supplied carrier argument.
4. Forward production `BP_CoopCharacter.GetCarried()` and `ReleaseCarried()` to this component on the server: connect the component's `Item` output to each existing Core return pin named **`CarriedActor`**. Consumers can instead call the component directly. The existing Core stubs were read and preserved.
5. When available, bind `AC_Health.OnDowned` on the server to `DropCarried()` and deny pickup using the authoritative health state. Do not use a client health flag. **Health/downed event integration and its gameplay test are pending.** The current guard understands the `Downed` actor tag; this is not a claim that AC_Health is wired.

Production input assets, HUD, Core, imported art, source art, shared materials and cave maps are untouched. Carrying has no player-count-specific allocation; it uses each owner and supports 2/3/4 players and two local owners. Puzzle population remains the consuming scaling/round work.

## Art handoff

Read published HC-A1 delivery [PR #70](https://github.com/Stretch-Gaming/Co-op-Game/pull/70), head `1e2904c9d42fc6f56c3cb4712441217383d2e247`, and HC-A2 [PR #71](https://github.com/Stretch-Gaming/Co-op-Game/pull/71), head `6bcfe0097a3176aa23c0779fc7ef6d881050cce4`, plus issues #18 and #19. Both deliveries are open and unmerged into this worktree's main baseline. They are preserved.

This PR therefore uses Engine basic geometry. Once those reviewed assets reach the integration branch, assign the existing stone-heart and selected statue meshes to the corresponding carrying Blueprint root. Preserve their source dimensions, material bindings and collision; set the root scale appropriately for the supplied mesh rather than retaining the fixture's 0.5 cube scale. Do not reimport or modify the imported art. Check source-base pivots against the production interaction trace endpoint, carry position and Drop clearance. Site 1 placement, art appearance/fallback review and production camera fit remain integration work.

## Verification

Evidence and independent assertions are under `Tools/unreal/hc4_carrying/evidence/`. `verify_evidence.py` reads captured worlds rather than invoking gameplay functions to manufacture success. Positive pickup/drop/handoff/reset cases inject Enhanced Input in the correct local-player subsystem, exercising character events and server RPCs. Python only arranges fixture positions, aims the fixture camera and observes state. Reconnect uses real network travel to the existing PIE server and loads a new client world while another player carries an item.

The final report records:

- 2/3/4 Play As Client: pickup, Drop, re-pickup, heavy movement values and reset in every server/client world.
- Two players competing for one item: one winner, one occupied slot and consistent carrier identity across peers.
- Late reconnect: carried attachment/collision reconstructed in the new client world; that client subsequently picks up the dropped item.
- Heavy movement samples: continuous expected velocity and no backwards correction in the captured owning-client positions.
- Handoff: placed, detached, physics off, slot cleared and speed restored. Reset from carried and placed states returns initial transforms and clears velocity.
- Two local host players plus two remote clients: independent statue pickup, one-owner Drop/re-pickup, other-owner handoff and reset. `split_screen.png` shows both rendered views.
- Server plate overlap counts across free, carried and placed states; clients do not compute authoritative counts.
- Saved class defaults, RepNotify modes, root mobility/overlap/replication, single fixture component, action links, fresh-load checks and content hashes.

See `final_report.json` for exact acceptance results and remaining limitations. Windows PIE and input injection are covered; physical gamepad and teammate Mac checks are not claimed. Production health/downed integration remains pending. #10 stays open for that and the separate Core integration.

## Reproduction

Open `L_HC4_Carrying` with its `BP_HC4GameMode`. Use Play As Client with 2, 3 or 4 clients. The fixture subclasses inherit HC-1 interaction/movement. Drop uses the existing G/gamepad Drop mapping; H hands off; F8 resets fixture items; F9 adds one second local player on a listen host. These test hooks are outside production input and character assets.

The editor scripts are pinned to this session's exact worktree and ports. See the tooling README for launching, guarded requests and factory/UI prerequisites. All `.uasset`/`.umap` changes were made through the dedicated Unreal editor.
