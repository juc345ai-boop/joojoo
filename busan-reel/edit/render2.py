#!/usr/bin/env python3
"""Busan edit #2: follows the second reference reel (teal night grade,
handwritten captions, white flash / negative / whip effects), 24 fps, 38.03 s.

Usage: render2.py [preview|segments|final]
"""
import os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOOT = os.path.join(ROOT, 'footage')
REEL = os.path.join(ROOT, 'reel2', 'reel.mp4')
FONTS = os.path.join(ROOT, 'fonts')
OUT = os.path.join(ROOT, 'edit2')
SEG = os.path.join(OUT, 'segs')
FPS = 24
TOTAL = 38.03

GRADE = ("eq=contrast=1.12:saturation=0.92:gamma=0.78,"
         "curves=r='0/0 0.25/0.17 0.5/0.45 0.75/0.76 1/0.95'"
         ":g='0/0.035 0.25/0.24 0.5/0.51 0.75/0.79 1/0.97'"
         ":b='0/0.075 0.25/0.28 0.5/0.52 0.75/0.73 1/0.86',"
         "colorbalance=rs=-0.06:gs=0.03:bs=0.07:rm=-0.04:gm=0.02:bm=0.03:rh=0.03:gh=0.01:bh=-0.03")
BLOOM = "split[m][h];[h]curves=all='0/0 0.72/0 1/1',gblur=sigma=18[g];[m][g]blend=all_mode=screen:all_opacity=0.22"

CUTS = [0.0, 3.875, 4.417, 4.667, 6.042, 7.25, 9.292, 9.958, 10.792, 11.208,
        12.542, 12.667, 13.833, 14.75, 15.0, 15.583, 16.167, 16.292, 16.625,
        17.458, 17.792, 18.333, 20.5, 22.0, 22.5, 23.458, 24.292, 25.5, 26.0,
        27.458, 27.833, 28.708, 30.25, 31.083, 31.292, 31.417, 32.292, 33.0,
        34.125, 34.292, 34.542, 35.083, TOTAL]

# (source, t_in, speed, zoom_start, zoom_end, pan_x, pan_y, fx)
# fx: '' | 'flash' (white blow-out) | 'neg' (negative) | 'whip' (horizontal
#     streak blur) | 'punch' (fast zoom over the first 8 frames)
S = [
    ('0063', 2.00, 1, 1.0, 1.05, 0.5, 0.5, ''),      # title over night window
    ('0016', 1.00, 1, 2.6, 2.6, 0.62, 0.33, ''),     # 돼지국밥 sign
    ('p20',  0.00, 1, 1.6, 1.6, 0.50, 0.15, ''),     # menu board
    ('0071', 0.00, 1, 1.0, 1.08, 0.5, 0.5, ''),      # harbour wide
    ('0071', 1.40, 1, 1.0, 2.2, 0.55, 0.42, 'punch'),# punch into the hill city
    ('0087', 0.00, 1, 1.0, 1.05, 0.5, 0.5, ''),      # station hall
    ('0087', 5.50, 1, 1.4, 1.4, 0.30, 0.60, ''),
    ('0056', 5.00, 1, 1.6, 1.6, 0.50, 0.10, ''),     # night lights
    ('0008', 15.0, 1, 1.1, 1.1, 0.5, 0.5, 'flash'),
    ('0008', 15.4, 1, 1.1, 1.1, 0.5, 0.5, ''),       # crowd walking
    ('0008', 3.00, 1, 1.1, 1.1, 0.5, 0.5, 'flash'),
    ('0008', 6.50, 1, 1.2, 1.2, 0.5, 0.45, ''),
    ('0071', 3.60, 1, 1.0, 1.0, 0.5, 0.5, ''),       # street pan
    ('0016', 6.00, 1, 1.3, 1.3, 0.5, 0.5, ''),
    ('0007', 1.00, 1, 1.3, 1.3, 0.5, 0.5, ''),       # market entrance
    ('0008', 11.3, 1, 1.3, 1.3, 0.5, 0.45, ''),      # food stall
    ('0008', 11.9, 1, 1.3, 1.3, 0.5, 0.45, ''),
    ('0056', 3.00, 1, 1.4, 1.4, 0.5, 0.3, 'flash'),
    ('0056', 3.40, 1, 1.4, 1.4, 0.5, 0.3, ''),       # colourful lights
    ('p18',  0.00, 1, 1.2, 1.25, 0.60, 0.55, ''),    # sign photo
    ('0007', 3.00, 1, 1.6, 1.6, 0.95, 0.35, ''),     # 떡갈비 sign
    ('0016', 2.00, 1, 1.0, 1.1, 0.62, 0.40, ''),     # food court + "돼지국밥???"
    ('0007', 12.0, 1, 1.0, 1.04, 0.5, 0.5, ''),      # corridor
    ('0056', 1.30, 1, 1.1, 1.1, 0.5, 0.5, ''),
    ('0087', 8.00, 1, 1.1, 1.1, 0.5, 0.5, ''),
    ('0087', 2.20, 1, 2.0, 2.0, 0.55, 0.20, 'whipin'),# departure board
    ('0056', 0.00, 1, 1.0, 1.04, 0.5, 0.5, ''),      # night stairs
    ('0008', 17.0, 1, 1.1, 1.1, 0.5, 0.5, ''),
    ('0071', 0.20, 0.8, 1.5, 1.55, 0.30, 0.62, ''),  # harbour + typed caption
    ('0056', 4.50, 1, 1.2, 1.2, 0.5, 0.4, 'whip'),   # light streak
    ('0007', 10.0, 1, 1.0, 1.0, 0.5, 0.5, ''),       # corridor
    ('0008', 13.0, 1, 1.1, 1.1, 0.5, 0.5, ''),       # stall crowd
    ('0016', 4.50, 1, 1.2, 1.2, 0.5, 0.5, ''),
    ('0007', 14.0, 1, 1.3, 1.3, 0.5, 0.5, ''),
    ('0056', 2.00, 1, 1.3, 1.3, 0.5, 0.5, 'neg'),
    ('0056', 2.10, 1, 1.3, 1.3, 0.5, 0.5, ''),
    ('0071', 4.80, 1, 1.0, 1.0, 0.5, 0.5, ''),
    ('0008', 1.00, 1, 1.0, 1.1, 0.5, 0.5, ''),       # market wide
    ('0087', 6.50, 1, 1.2, 1.2, 0.5, 0.5, ''),
    ('0087', 6.70, 1, 1.2, 1.2, 0.5, 0.5, 'flash'),
    ('0087', 6.95, 1, 1.2, 1.2, 0.5, 0.5, ''),
    ('0063', 0.00, 0.7, 1.0, 1.06, 0.5, 0.5, ''),    # ending window
]
assert len(S) == len(CUTS) - 1, (len(S), len(CUTS))
FR = [round(c * FPS) for c in CUTS]


def src_path(src):
    return os.path.join(FOOT, src + ('.jpg' if src.startswith('p') else '.mp4'))


def zoom_expr(z0, z1, n, fx):
    if z0 == z1:
        return f"{z0}"
    if fx == 'punch':  # ease-out over 8 frames, then hold
        p = "min(t/0.333,1)"
        return f"({z0}+({z1}-{z0})*(1-pow(1-{p},3)))"
    return f"({z0}+({z1}-{z0})*min(t/{max(n / FPS, 1e-3):.4f},1))"


def fx_chain(fx):
    if fx == 'flash':
        return ",hue=s=0,curves=all='0/0 0.16/0.04 0.30/1 1/1'"
    if fx == 'neg':
        return ",negate"
    if fx == 'whip':
        return ",avgblur=sizeX=140:sizeY=1,eq=brightness=0.06:saturation=1.4"
    return ""


def vf(seg, n):
    src, tin, speed, z0, z1, px, py, fx = seg
    z = zoom_expr(z0, z1, n, fx)
    chain = (f"scale=w='2*trunc(960*{z}+0.5)':h=-2:eval=frame:flags=bicubic,"
             f"crop=1920:1080:x='(iw-1920)*{px}':y='(ih-1080)*{py}',setsar=1,"
             f"{GRADE},{BLOOM}{fx_chain(fx)}")
    if fx == 'whipin':
        # first 5 frames streaked, then sharp
        chain += ",split[s0][s1];[s1]avgblur=sizeX=120:sizeY=1[sb];[s0][sb]overlay=enable='lt(n,5)'"
    return chain + ",format=yuv420p"


def cmd_for(i, still=None):
    seg = S[i]
    src, tin, speed = seg[0], seg[1], seg[2]
    n = FR[i + 1] - FR[i]
    base = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
    if src.startswith('p'):
        inp = ['-loop', '1', '-framerate', str(FPS), '-i', src_path(src)]
        chain = vf(seg, n)
    else:
        need = n / FPS * speed + 0.3
        inp = ['-ss', f'{tin:.3f}', '-t', f'{need:.3f}', '-i', src_path(src)]
        chain = f"setpts=(PTS-STARTPTS)/{speed},fps={FPS}," + vf(seg, n)
    if still:
        return base + inp + ['-vf', chain + ',scale=384:216,'
                             f"drawtext=text='{i} {src}':x=4:y=4:fontsize=16:"
                             "fontcolor=yellow:box=1:boxcolor=black",
                             '-frames:v', '1', still]
    return base + inp + ['-vf', chain, '-an', '-frames:v', str(n), '-r', str(FPS),
                         '-c:v', 'libx264', '-preset', 'fast', '-crf', '12',
                         '-pix_fmt', 'yuv420p', os.path.join(SEG, f'{i:03d}.mp4')]


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print('FAIL', c[-1], r.stderr[-800:])
    return r.returncode


def frames_of(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                        '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p],
                       capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


# ---------------- captions (global timeline) ----------------
F_SCRIPT = os.path.join(FONTS, 'DancingScript.ttf')
F_PEN = os.path.join(FONTS, 'NanumPen.ttf')
F_SANS = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
F_LIGHT = '/usr/share/fonts/opentype/inter/Inter-Light.otf'


def esc(t):
    return t.replace('\\', '\\\\').replace(':', '\\:').replace("'", "’").replace('%', '\\%')


def dt(font, text, size, color, x, y, t0, t1, fade=0.0, extra=''):
    alpha = '1'
    if fade:
        alpha = (f"if(lt(t,{t0}+{fade}),(t-{t0})/{fade},"
                 f"if(gt(t,{t1}-{fade}),({t1}-t)/{fade},1))")
    return (f"drawtext=fontfile='{font}':text='{esc(text)}':fontsize={size}:"
            f"fontcolor={color}:x={x}:y={y}:alpha='{alpha}':"
            f"enable='between(t,{t0},{t1})'{extra}")


def typed(font, text, size, color, y, t0, step, t1, spacing=''):
    """Reveal text letter by letter, left edge fixed at the full text's centred x."""
    f = ImageFont.truetype(font, size)
    full_w = f.getlength(text)
    x = f"(w-{full_w:.0f})/2"
    out = []
    visible = [i for i, ch in enumerate(text) if ch != ' ']
    for k, idx in enumerate(visible):
        a = t0 + k * step
        b = t0 + (k + 1) * step if k + 1 < len(visible) else t1
        out.append(dt(font, text[:idx + 1], size, color, x, y, round(a, 3), round(b, 3)))
    return out


def captions():
    gold, red, white = '0xE9C46A', '0xE0342C', '0xF2F2F2'
    sh = ':shadowcolor=black@0.45:shadowx=3:shadowy=3'
    c = []
    # title: script "Busan" grows in, then small red "2026" / "september"
    c.append("drawtext=fontfile='%s':text='Busan':fontsize='min(90+260*t,330)':"
             "fontcolor=%s:x=(w-tw)/2:y=(h-th)/2-40:alpha='if(gt(t,1.95),max(0,(2.25-t)/0.3),min(1,t/0.25))':"
             "enable='between(t,0,2.25)'%s" % (F_SCRIPT, gold, sh))
    c.append(dt(F_SCRIPT, '2026', 96, red, '(w/2)-420', '(h/2)-200', 1.25, 2.25, 0.15, sh))
    c.append(dt(F_SCRIPT, 'in september', 88, red, '(w/2)+60', '(h/2)+120', 0.9, 2.25, 0.15, sh))
    # "shot on" card
    c.append(dt(F_SANS, 'SHOT ON', 70, white, 'w*0.06', '(h-th)/2', 2.45, 3.42, 0.08))
    c.append(dt(F_SANS, 'DJI', 84, white, '(w-tw)/2', '(h/2)-70', 2.45, 3.42, 0.08))
    c.append(dt(F_LIGHT, 'Osmo Pocket 4', 50, white, '(w-tw)/2', '(h/2)+28', 2.45, 3.42, 0.08))
    # big red city name
    c.append(dt(F_SANS, 'BUSAN', 340, red, '(w-tw)/2', '(h-th)/2', 3.45, 3.875))
    # "돼지국밥???" handwritten
    c.append(dt(F_PEN, '돼지국밥???', 300, red, 'w*0.06', 'h*0.06', 18.95, 20.5, 0.0, sh))
    # typed spaced caption on the harbour
    c += typed(F_LIGHT, 'B   U   S   A   N', 96, white, 'h*0.74', 26.05, 0.07, 27.45)
    c += typed(F_LIGHT, '3 5 . 1 °  N      1 2 9 . 0 °  E', 50, white, 'h*0.74+120', 26.45, 0.035, 27.45)
    # ending
    c.append(dt(F_PEN, '끝.', 380, red, 'w*0.32', '(h-th)/2', 35.45, 36.35, 0.12, sh))
    c.append(dt(F_PEN, 'The End...', 300, red, '(w-tw)/2', '(h-th)/2', 36.45, TOTAL, 0.12, sh))
    return ','.join(c)


def main(mode):
    os.makedirs(SEG, exist_ok=True)
    if mode == 'preview':
        pv = os.path.join(OUT, 'pv')
        os.makedirs(pv, exist_ok=True)
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(run, [cmd_for(i, os.path.join(pv, f'{i:03d}.jpg')) for i in range(len(S))]))
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-pattern_type', 'glob',
             '-i', os.path.join(pv, '*.jpg'), '-vf', 'tile=7x6', '-frames:v', '1',
             os.path.join(OUT, 'preview.jpg')])
    elif mode == 'segments':
        only = [int(x) for x in sys.argv[2:]] or range(len(S))
        with ThreadPoolExecutor(3) as ex:
            list(ex.map(run, [cmd_for(i) for i in only]))
        bad = [(i, FR[i + 1] - FR[i], frames_of(os.path.join(SEG, f'{i:03d}.mp4')))
               for i in range(len(S))]
        print('frame mismatches:', [b for b in bad if b[1] != b[2]])
    elif mode == 'final':
        lst = os.path.join(OUT, 'list.txt')
        with open(lst, 'w') as f:
            for i in range(len(S)):
                f.write(f"file '{os.path.join(SEG, f'{i:03d}.mp4')}'\n")
        out = os.path.join(OUT, 'busan_style2.mp4')
        vfx = (f"vignette=angle=PI/4.5,{captions()},noise=alls=4:allf=t,"
               f"fade=t=in:st=0:d=0.25,fade=t=out:st={TOTAL-0.4:.2f}:d=0.4,format=yuv420p")
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
             '-f', 'concat', '-safe', '0', '-i', lst, '-i', REEL,
             '-map', '0:v', '-map', '1:a', '-vf', vfx,
             '-af', f"afade=t=out:st={TOTAL-0.5:.2f}:d=0.5",
             '-c:v', 'libx264', '-preset', 'slow', '-b:v', '7M', '-maxrate', '9M',
             '-bufsize', '14M', '-x264-params', 'aq-mode=3', '-profile:v', 'high',
             '-level', '4.1', '-pix_fmt', 'yuv420p', '-r', str(FPS),
             '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
             '-movflags', '+faststart', '-t', f'{TOTAL:.3f}', out])
        print(out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'preview')
