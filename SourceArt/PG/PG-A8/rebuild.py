"""Build source in a new external staging directory, never in the Unreal project."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    p.add_argument('--blender',default='blender')
    p.add_argument('--compare',action='store_true')
    a=p.parse_args(); out=a.output.resolve()
    here=Path(__file__).resolve().parent; repo=here.parents[2]
    if out == repo or repo in out.parents:
        p.error('Build outside the repository, then copy only delivery/ into SourceArt/PG/PG-A8/.')
    if out.exists() and any(out.iterdir()):
        p.error('Use a new or empty output directory; this script never removes existing files.')
    out.mkdir(parents=True,exist_ok=True)
    cleanup=repo/'Tools/blender/cleanup_export.py'
    def run(script,args,label):
        with (out/(label+'.log')).open('w') as log:
            subprocess.run([a.blender,'-b','--factory-startup','--python-exit-code','1','--python',str(script),'--',*map(str,args)],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
    for candidate in (['A','B'] if a.compare else ['A']):
        run(here/'build_flare.py',['--output',out/candidate,'--candidate',candidate,'--cleanup',cleanup],'build-'+candidate)
    delivery=out/'delivery'; delivery.mkdir()
    run(cleanup,[out/'A/raw.fbx',delivery/'SM_HandFlare.fbx','--name','SM_HandFlare','--target-triangles','1999','--combine'],'cleanup')
    run(here/'validate_flare.py',['--folder',delivery,'--cleanup',cleanup,'--finalize'],'finalize')
    shutil.copy2(out/'A/SFX_Flare_Hiss_Loop.wav',delivery)
    shutil.copy2(out/'A/audio-build.json',delivery)
    preview=delivery/'previews'; preview.mkdir()
    for name in ['studio','cave']: shutil.copy2(out/('A/'+name+'.png'),preview/(name+'.png'))
    run(here/'validate_flare.py',['--folder',delivery,'--cleanup',cleanup],'validate')
    # Exporter's own report records staging paths; make delivery evidence portable.
    report_path=delivery/'SM_HandFlare.validation.json'
    report=json.loads(report_path.read_text()); report['input']='candidate A/raw.fbx'; report['output']='SM_HandFlare.fbx'
    report['scope']='Cleanup visual mesh only, before adding separately validated UCX collision.'
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print('Validated delivery:',delivery)
    if a.compare: print('Unselected candidate B remains outside repo:',out/'B')

if __name__=='__main__': main()
