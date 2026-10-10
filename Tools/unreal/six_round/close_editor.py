"""Close only this task editor after recording its already saved checkpoint."""
from pathlib import Path
import unreal as ue
assert Path(ue.Paths.project_dir()).resolve() == ROOT.resolve()
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
# Saving is handled by each bounded authoring stage. Do not Save All here.
(QUEUE/'closed-for-ui-recovery.txt').write_text(str(ROOT))
RESULT = {'closing_task_editor': True}
ue.SystemLibrary.quit_editor()
