"""Checkout-derived location guard and ignored smoke-report destination.

This new helper does not alter existing machine-specific authoring guards.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
assert (ROOT/'CoopGame.uproject').is_file(), 'Helper must live in this repository'
QUEUE=ROOT/'Saved/PlayableState/Smoke'

def guard():
    import unreal as ue
    actual=Path(ue.Paths.project_dir()).resolve()
    assert actual==ROOT, ('Wrong editor project',str(actual),str(ROOT))
    return ROOT
