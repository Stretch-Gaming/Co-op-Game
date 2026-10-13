"""Location guard and ignored raw-output directory for these new helpers.

Existing authoring helpers and their original checkout guards are unchanged.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
assert (ROOT / 'CoopGame.uproject').is_file(), 'Helper must live in this repository'
QUEUE = ROOT / 'Saved/PlayableState/Ghosts'

def guard(stopped_pie=False):
    import unreal as ue
    actual = Path(ue.Paths.project_dir()).resolve()
    assert actual == ROOT, ('Wrong editor project', str(actual), str(ROOT))
    if stopped_pie:
        assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring'
    return ROOT
