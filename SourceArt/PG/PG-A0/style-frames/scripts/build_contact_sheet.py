"""Build the review sheet from the image table in prompts.md; requires Pillow."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def font(size, bold=False):
    name = 'Arial Bold.ttf' if bold else 'Arial.ttf'
    try:
        return ImageFont.truetype('/System/Library/Fonts/Supplemental/' + name, size)
    except OSError:
        return ImageFont.load_default(size=size)


def main():
    entries = []
    for line in (ROOT / 'prompts.md').read_text(encoding='utf-8').splitlines():
        if line.startswith('| `'):
            _, filename, title, _ = line.split('|')
            entries.append((filename.strip().strip('`'), title.strip()))
    if len(entries) != 12:
        raise ValueError(f'Expected twelve images in the prompt table, found {len(entries)}')

    col_w, row_h, gap, margin, header = 600, 410, 18, 24, 86
    sheet = Image.new('RGB', (1884, 1804), '#171B25')
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 16), 'PG / Shared style anchor — v3', font=font(34, True), fill='#E8ECF1')
    draw.text((margin, 57), 'Corrected reference + selected v1 frames + five isolated Meshy concepts', font=font(16), fill='#AEB8C8')
    for n, (filename, title) in enumerate(entries):
        with Image.open(ROOT / filename) as source:
            thumbnail = source.convert('RGB')
        thumbnail.thumbnail((col_w - 16, 338), Image.Resampling.LANCZOS)
        x = margin + (n % 3) * (col_w + gap)
        y = header + (n // 3) * (row_h + gap)
        draw.rounded_rectangle((x, y, x + col_w, y + row_h), radius=8, fill='#252B38')
        sheet.paste(thumbnail, (x + (col_w - thumbnail.width) // 2, y + 8 + (338 - thumbnail.height) // 2))
        draw.text((x + 12, y + 354), title, font=font(22), fill='#F0F0F0')
        draw.text((x + 12, y + 384), filename, font=font(16), fill='#AFBACD')
    output = ROOT / 'contact-sheet.png'
    sheet.save(output)
    print(f'Wrote {output}: {sheet.width} x {sheet.height}, {len(entries)} images')


if __name__ == '__main__':
    main()
