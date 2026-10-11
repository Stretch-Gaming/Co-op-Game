"""Fixed test package contract. No production map is a writable target."""
from pathlib import Path
TEST_ROOT='/Game/Puzzles/Test/SixRound/'
PERSISTENT=TEST_ROOT+'L_SixRound_Test'
HC_LEVEL=TEST_ROOT+'L_SixRound_HC_Test'
CAVE_COPY=TEST_ROOT+'L_CaveEnvironment_Test'
TEST_MODE=TEST_ROOT+'BP_SixRoundTestGameMode'
DOOR=TEST_ROOT+'BP_PuzzleConnectionDoor'
WORLD_ROUTE='/Game/Hazards/Test/SixRound/L_WorldRoute_Test'
CAVE_SOURCE='/Game/Hazards/L_Site01_HZ'
DEFAULT_PLAYER_LEVEL='/Game/Player/Test/SixRound/L_SixRound_PG_Test'
WRITE_MAPS={PERSISTENT,HC_LEVEL,CAVE_COPY}

def writable_package(package):
    name=package.get_name() if hasattr(package,'get_name') else str(package)
    assert name in WRITE_MAPS,f'Unapproved level save/mutation: {name}'
    return name

def player_level(args):
    path=args.get('player_level',DEFAULT_PLAYER_LEVEL)
    assert path.startswith('/Game/Player/Test/SixRound/') and path.rsplit('/',1)[-1].startswith('L_')
    return path

def validate_args(args):
    assert args.get('target_map',PERSISTENT)==PERSISTENT
    assert args.get('hc_level',HC_LEVEL)==HC_LEVEL
    assert args.get('cave_level',CAVE_COPY)==CAVE_COPY
    assert args.get('world_level',WORLD_ROUTE)==WORLD_ROUTE
    return player_level(args)

def save_exact(ue,packages):
    names=[writable_package(p) for p in packages]
    assert len(names)==len(set(names))
    assert ue.EditorLoadingAndSavingUtils.save_packages(packages,False)
    return names

def safe_actor(actor,package):
    name=writable_package(package)
    assert actor.get_level().get_outermost().get_name()==name
    return actor
