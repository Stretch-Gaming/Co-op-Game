"""Persist only the task's new World clone; source map remains read-only."""
import hashlib,unreal as ue
path='/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test'
source=ROOT/'Content/Hazards/L_Site01_HZ.umap'
before=hashlib.sha256(source.read_bytes()).hexdigest()
copy=ue.load_asset(path)
assert copy and copy.get_outermost().get_name()==path
assert ue.EditorLoadingAndSavingUtils.save_packages([copy.get_outermost()],False)
assert (ROOT/'Content/Puzzles/Test/SixRound/L_CaveEnvironment_Test.umap').is_file()
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
RESULT={'copy_saved':path,'source_sha256':before}
