"""Close only the primary-owned private QA editor after its PIE gates stop."""
import unreal as ue
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
ue.EditorPythonScripting.set_keep_python_script_alive(False)
ue.SystemLibrary.quit_editor()
RESULT={'closing_private_editor':True}
