#!/usr/bin/env python3
"""Extract content figures (charts, diagrams, infographic snippets) from the
Eduteria Chem Notes Class Wise.pdf so they can be reused in the consolidated
A4 edition. Decorations (headers, watermarks, cover art) are skipped; each
figure is rendered as a clipped page region so labels baked into the page are
kept. Overlapping/adjacent images on a page are merged into one clip."""
import os
import pymupdf

SRC = "Eduteria Chem Notes Class Wise.pdf"
OUT = "build_consolidated/figures"
DPI = 200

# Page coordinates of the printable content area (A4 595.32 x 841.92)
CONTENT = pymupdf.Rect(8, 40, 587, 812)
DECOR_DIMS = {(1416, 61), (1931, 50), (1070, 1184), (1007, 1478)}

COVER_PAGES = {1, 11, 24, 41, 47, 57, 65, 72, 82, 86, 111, 125, 138}

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
    """Grow rect to include text blocks that intersect it (labels/captions)."""
    r = pymupdf.Rect(rect)
    for _ in range(3):
        grown = pymupdf.Rect(r)
        for b in blocks:
            br = pymupdf.Rect(b[:4])
            if br.intersects(r):
                grown |= br
        if grown == r:
            break
        r = grown
    return r

def main():
    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(SRC)
    manifest = []
    for pno in range(len(doc)):
        pnum = pno + 1
        if pnum in COVER_PAGES:
            continue
        page = doc[pno]
        blocks = page.get_text("blocks")
        items = []
        for img in page.get_images(full=True):
            if is_decor(img, page):
                continue
            if img[2] < 130 or img[3] < 100:      # tiny fragments
                continue
            for r in page.get_image_rects(img[0]):
                items.append(r)
        if not items:
            continue
        # merge overlapping / vertically adjacent image rects
        merged = []
        for r in items:
            r = pymupdf.Rect(r)
            hit = None
            for m in merged:
                probe = pymupdf.Rect(m.x0 - 14, m.y0 - 10, m.x1 + 14, m.y1 + 10)
                if probe.intersects(r):
                    hit = m
                    break
            if hit is not None:
                hit |= r
            else:
                merged.append(r)
        # expand to catch nearby text labels, then re-merge
        expanded = [expand_with_text(page, r, blocks) for r in merged]
        final = []
        for r in expanded:
            hit = None
            for m in final:
                if m.intersects(r):
                    hit = m
                    break
            if hit is not None:
                hit |= r
            else:
                final.append(r)
        for i, r in enumerate(final):
            clip = pymupdf.Rect(r) & CONTENT
            if clip.is_empty or clip.width < 90 or clip.height < 70:
                continue
            if clip.width * clip.height > 0.97 * page.rect.width * page.rect.height:
                clip = pymupdf.Rect(clip) & pymupdf.Rect(8, 40, 587, 806)
            pix = page.get_pixmap(dpi=DPI, clip=clip)
            name = f"p{pnum:03d}_{i}.png"
            pix.save(os.path.join(OUT, name))
            manifest.append((name, pnum, round(clip.width), round(clip.height)))
    with open(os.path.join(OUT, "manifest.tsv"), "w") as f:
        for name, pnum, w, h in manifest:
            f.write(f"{name}\t{pnum}\t{w}\t{h}\n")
    print("figures:", len(manifest))

if __name__ == "__main__":
    main()
