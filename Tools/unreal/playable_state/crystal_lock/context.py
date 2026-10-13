"""Repository/editor identity and ignored output paths for HC-A4 replay."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
QUEUE = ROOT / 'Saved/PlayableState/CrystalLock'
assert (ROOT / 'CoopGame.uproject').is_file(), 'Place this bundle in its documented repository location'


def guard(stopped_pie=False):
    import unreal as ue
    assert Path(ue.Paths.project_dir()).resolve() == ROOT, 'Editor must use the same checkout as this helper'
    if stopped_pie:
        assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before inspection/import'
    return ROOT
