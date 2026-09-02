#!/usr/bin/env python3
"""Extract the content figures (charts, ray diagrams, infographic snippets)
from the 19 Eduteria physics lecture PDFs in `physic notes eduteria/` so they
can be reused in the consolidated A4 edition.

Decorations (Eduteria header/footer strips, the tree watermark, the lecture
cover art) are skipped; every remaining raster image is rendered as a clipped
*page region* (not the raw embedded bitmap) so the labels typeset around it are
kept. Overlapping/adjacent images are merged into one clip. A handful of
vector-drawn diagrams (which are not embedded images) are clipped from fixed
page coordinates listed in EXTRA_CLIPS.

Output: build_physics/figures/L{nn}_p{page}_{i}.png + manifest.tsv
"""
import json
import os
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "physic notes eduteria")
OUT = os.path.join(ROOT, "build_physics", "figures")
DPI = 150
EXPAND_TEXT = False   # set True to pull adjacent caption text into the clip

# lecture number -> source pdf (numeric file names carry no meaning; the order
# below is the lecture order printed on each cover page)
LECTURES = {
    1: ("306675425537140800.pdf", "Introduction to Physics"),
    2: ("398034991623203260.pdf", "Light Part-01"),
    3: ("293062675426610560.pdf", "Light Part-02"),
    4: ("311443937794482240.pdf", "Light Part-03"),
    5: ("531094603680005700.pdf", "Light Part-04"),
    6: ("286886843631753200.pdf", "Wave"),
    7: ("576259227934578100.pdf", "Sound Wave"),
    8: ("702593218928681700.pdf", "Heat-01"),
    9: ("678976958044898800.pdf", "Temperature"),
    10: ("553551706360511040.pdf", "Heat Part-3"),
    11: ("521558488346541440.pdf", "Kinematics"),
    12: ("835065892002650900.pdf", "Motion Part-02"),
    13: ("193335169739731780.pdf", "Circular Motion & Gravitation"),
    14: ("53632112798045940.pdf", "Gravitation & Mechanical Properties of Fluids"),
    15: ("396793353415595460.pdf", "Electricity Part-01"),
    16: ("231467551622408060.pdf", "Electricity Part-02"),
    17: ("261330855455479360.pdf", "Electricity Part-03"),
    18: ("303047288047826300.pdf", "Magnetism"),
    19: ("88030258169755940.pdf", "Unit & Dimension, Photoelectric Effect, WPE, Nuclear, Measurement"),
}

# Printable content area of the A4 page (595.32 x 841.92): below the header
# strip, above the footer strip.
CONTENT = pymupdf.Rect(8, 50, 587, 786)
# Embedded-image pixel sizes of the page furniture (header, footer, watermark)
DECOR_DIMS = {(1070, 1184), (2126, 92), (1931, 78), (1416, 61), (1931, 50)}

# Vector diagrams that are drawn (not embedded) — clipped from fixed coordinates.
# (lecture, page, name, rect)
EXTRA_CLIPS = [
    (1, 3, "reflection_laws", pymupdf.Rect(330, 640, 590, 775)),
    (3, 2, "sign_convention", pymupdf.Rect(40, 383, 260, 541)),
    (11, 3, "equations_of_motion", pymupdf.Rect(300, 672, 590, 780)),
    (11, 4, "avg_speed_case1", pymupdf.Rect(30, 56, 300, 300)),
    (11, 4, "avg_speed_case2", pymupdf.Rect(30, 300, 300, 578)),
    (9, 2, "state_change_cycle", pymupdf.Rect(300, 329, 590, 410)),
    (15, 2, "charge_forces", pymupdf.Rect(40, 605, 290, 770)),
    (18, 2, "ac_graph", pymupdf.Rect(40, 322, 290, 460)),
    (18, 2, "dc_graph", pymupdf.Rect(40, 531, 290, 645)),
]


def is_decor(img, page):
    w, h = img[2], img[3]
    if (w, h) in DECOR_DIMS:
        return True
    rects = page.get_image_rects(img[0])
    if not rects:
        return True
    r = rects[0]
    if r.width * r.height > 0.92 * page.rect.width * page.rect.height:
        return True
    return False


def expand_with_text(page, rect, blocks):
    """Grow rect to include *caption-like* text blocks: short (<= 2 lines)
    blocks sitting directly above/below the figure and horizontally centred
    on it. Body-text columns are deliberately left out so the clip stays a
    figure, not a page fragment."""
    r = pymupdf.Rect(rect)
    for _ in range(2):
        grown = pymupdf.Rect(r)
        for b in blocks:
            br = pymupdf.Rect(b[:4])
            if br.height > 30 or br.width > r.width * 1.25 + 12:
                continue
            probe = pymupdf.Rect(r.x0 - 6, r.y0 - 18, r.x1 + 6, r.y1 + 18)
            if not br.intersects(probe):
                continue
            cx = (br.x0 + br.x1) / 2
            if not (r.x0 - 10 <= cx <= r.x1 + 10):
                continue
            grown |= br
        if grown == r:
            break
        r = grown
    return r


def strip_watermark(page):
    """Remove the Eduteria tree watermark (1070x1184 px) so it cannot bleed
    through transparent figure regions when the clip is rendered."""
    for img in page.get_images(full=True):
        if (img[2], img[3]) == (1070, 1184):
            try:
                page.delete_image(img[0])
            except Exception:
                pass


def merge_rects(rects, min_overlap=0.2):
    """Union rectangles that genuinely overlap (intersection area at least
    `min_overlap` of the smaller rectangle) until nothing changes. This joins
    a decorative frame with the picture drawn inside it, but leaves merely
    adjacent/touching figures separate.
    Note: pymupdf.Rect `|` returns a new object, so the union is written back."""
    out = [pymupdf.Rect(r) for r in rects]
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = out[i], out[j]
                inter = a & b
                if inter.is_empty:
                    continue
                small = min(a.width * a.height, b.width * b.height)
                if small > 0 and inter.width * inter.height >= min_overlap * small:
                    out[i] = a | b
                    del out[j]
                    changed = True
                    break
            if changed:
                break
    return out


def save_quantized(pix, path):
    """Flatten onto white, palette-quantise and save — keeps flat-colour
    infographics crisp at a fraction of the RGB size."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    im.convert("P", palette=Image.ADAPTIVE, colors=176).save(path, optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for lno in sorted(LECTURES):
        fname, title = LECTURES[lno]
        doc = pymupdf.open(os.path.join(SRC_DIR, fname))
        for pno in range(1, len(doc)):          # page 1 of every lecture is cover art
            page = doc[pno]
            pnum = pno + 1
            strip_watermark(page)
            blocks = page.get_text("blocks")
            items = []
            for img in page.get_images(full=True):
                if is_decor(img, page):
                    continue
                if img[2] < 120 or img[3] < 90:  # tiny fragments / bullets
                    continue
                for r in page.get_image_rects(img[0]):
                    items.append(pymupdf.Rect(r))
            merged = merge_rects(items)
            # Captions are re-typed in the consolidated edition, so keep the
            # clips tight (3 pt pad) instead of pulling in neighbouring body text.
            expanded = [pymupdf.Rect(r.x0 - 3, r.y0 - 3, r.x1 + 3, r.y1 + 3) for r in merged]
            if EXPAND_TEXT:
                expanded = [expand_with_text(page, r, blocks) for r in expanded]
            final = merge_rects(expanded, min_overlap=0.5)
            final.sort(key=lambda r: (round(r.x0 / 200), r.y0))
            for i, r in enumerate(final):
                clip = pymupdf.Rect(r) & CONTENT
                if clip.is_empty or clip.width < 80 or clip.height < 60:
                    continue
                pix = page.get_pixmap(dpi=DPI, clip=clip)
                name = f"L{lno:02d}_p{pnum}_{i}.png"
                save_quantized(pix, os.path.join(OUT, name))
                manifest.append((name, lno, pnum, round(clip.width), round(clip.height)))
        for (l2, p2, nm, rect) in EXTRA_CLIPS:
            if l2 != lno:
                continue
            page = doc[p2 - 1]
            strip_watermark(page)
            pix = page.get_pixmap(dpi=DPI, clip=rect)
            name = f"L{lno:02d}_p{p2}_{nm}.png"
            save_quantized(pix, os.path.join(OUT, name))
            manifest.append((name, lno, p2, round(rect.width), round(rect.height)))
    with open(os.path.join(OUT, "manifest.tsv"), "w") as f:
        f.write("file\tlecture\tpage\twidth_pt\theight_pt\n")
        for name, lno, pnum, w, h in manifest:
            f.write(f"{name}\t{lno}\t{pnum}\t{w}\t{h}\n")
    with open(os.path.join(ROOT, "build_physics", "lectures.json"), "w") as f:
        json.dump({str(k): {"file": v[0], "title": v[1]} for k, v in LECTURES.items()}, f, indent=1)
    print("figures:", len(manifest))


if __name__ == "__main__":
    main()
