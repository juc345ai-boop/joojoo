#!/usr/bin/env python3
"""Build the caption fonts used by render2.py from @fontsource npm packages.

    cd busan-reel/fonts
    npm pack @fontsource/nanum-pen-script @fontsource/dancing-script
    for f in *.tgz; do d=${f%.tgz}; mkdir -p $d && tar xzf $f -C $d --strip-components=1; done
    python3 ../edit/make_fonts.py

fontsource ships Korean fonts as many unicode-range subsets; this merges them
into one TTF so ffmpeg drawtext can use it. Fonts are SIL OFL.
"""
import glob
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import cmap_format_12


def combine(pattern, out):
    files = sorted(glob.glob(pattern))
    base = TTFont(files[0]); base.flavor = None
    glyf, hmtx = base['glyf'], base['hmtx']
    cmap = {}
    for t in base['cmap'].tables:
        if t.isUnicode():
            cmap.update(t.cmap)
    order = list(base.getGlyphOrder())
    for f in files[1:]:
        ft = TTFont(f)
        fc = {}
        for t in ft['cmap'].tables:
            if t.isUnicode():
                fc.update(t.cmap)
        for cp, gn in fc.items():
            if cp in cmap:
                continue
            g = ft['glyf'][gn]
            if g.isComposite():
                continue
            new = f"u{cp:04X}"
            glyf.glyphs[new] = g
            hmtx.metrics[new] = ft['hmtx'].metrics[gn]
            order.append(new)
            cmap[cp] = new
    base.setGlyphOrder(order)
    t = cmap_format_12(12)
    t.platEncID, t.platformID, t.format, t.reserved, t.length, t.language, t.nGroups = 10, 3, 12, 0, 0, 0, 0
    t.cmap = cmap
    base['cmap'].tables = [t]
    base['maxp'].numGlyphs = len(order)
    base['post'].formatType = 3.0
    base.save(out)


combine('fontsource-nanum-pen-script-*/files/nanum-pen-script-*-400-normal.woff2', 'NanumPen.ttf')
f = TTFont(glob.glob('fontsource-dancing-script-*/files/dancing-script-latin-700-normal.woff2')[0])
f.flavor = None
f.save('DancingScript.ttf')
