"""Compose original source previews using Pillow; accepts rebuild.py output folder."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

base=Path(sys.argv[1]); preview=base/'delivery/previews'
board=Image.new('RGB',(832,430),'#1E2433'); d=ImageDraw.Draw(board)
for i,variant in enumerate(['A','B']):
    source=Image.open(base/variant/'studio.png').convert('RGB'); x=16+416*i
    board.paste(source.resize((256,256),Image.Resampling.LANCZOS),(x,44))
    board.paste(source.resize((64,64),Image.Resampling.LANCZOS),(x+284,104))
    d.text((x,16),'A — chosen: wrapped grip / bent flame' if variant=='A' else 'B — rejected: straight collar / narrow tip',fill='#F3E6C8')
    d.text((x+284,84),'64 px',fill='#F3E6C8')
    d.text((x,320),'A retains broad silhouette and medium cloth bands.' if variant=='A' else 'B loses flame shape and grip detail at 64 px.',fill='#F3E6C8')
d.text((16,375),'Original Blender source renders; small-scale comparison, not Unreal split-screen acceptance.',fill='#FFB347')
board.save(preview/'candidate-comparison.png')
board=Image.new('RGB',(768,448),'#1E2433'); d=ImageDraw.Draw(board)
for i,name in enumerate(['studio','cave']):
    source=Image.open(base/'A'/f'{name}.png').convert('RGB'); x=12+384*i
    board.paste(source.resize((256,256),Image.Resampling.LANCZOS),(x,48))
    board.paste(source.resize((64,64),Image.Resampling.LANCZOS),(x+286,112))
    d.text((x,16),f'A / {name}: 256 px and 64 px',fill='#F3E6C8')
d.text((12,344),'6 x 6 x 22 cm. Amber tip remains the brightest shape in the dark source preview.',fill='#FFB347')
d.text((12,384),'No Unreal scene, game camera, split-screen, platform or playtest is represented here.',fill='#F3E6C8')
board.save(preview/'readability.png')
