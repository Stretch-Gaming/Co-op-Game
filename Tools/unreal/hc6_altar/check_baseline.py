import pathlib,json,subprocess,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
files=['Content/Puzzles/BP_Carryable.uasset','Content/Puzzles/BP_KeyRelic.uasset','Content/Puzzles/Carrying/AC_Carrying.uasset','Content/Core/BP_CoopCharacter.uasset','Content/Core/BP_CoopGameMode.uasset','Content/Maps/L_Site01.umap']
rows=[]
for f in files:
 pointer=subprocess.check_output(['git','show','HEAD:'+f],cwd=ROOT,text=True)
 oid=next(l.split('sha256:')[1] for l in pointer.splitlines() if l.startswith('oid sha256:'))
 actual=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
 assert oid==actual,(f,oid,actual)
 rows.append({'path':f,'baseline_oid':oid,'actual_sha256':actual,'unchanged':True})
(ROOT/'Tools/unreal/hc6_altar/baseline-hashes.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'baseline_matches':len(rows)}))
